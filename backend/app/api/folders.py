from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.core.database import get_db
from app.models.file_stats import FolderStats, FileStats
from app.schemas.stats import FolderTreeNode, FolderDetails, FileTypeStats
from app.services.utils import format_size, format_duration


def parse_extensions(extensions: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated extensions into list with leading dots"""
    if not extensions:
        return None
    return [f".{e.strip().lower().lstrip('.')}" for e in extensions.split(",") if e.strip()]


router = APIRouter()


@router.get("/tree", response_model=List[FolderTreeNode])
async def get_folder_tree(
    path: Optional[str] = Query(default=None, description="Parent path to start from"),
    depth: int = Query(default=2, ge=1, le=10, description="Depth of tree to return"),
    extensions: Optional[str] = Query(default=None, description="Comma-separated extensions filter"),
    db: AsyncSession = Depends(get_db),
):
    """Get folder tree structure with optional extension filter"""

    ext_list = parse_extensions(extensions)

    # Build query based on path
    if path:
        query = select(FolderStats).where(
            FolderStats.parent_path == path,
            FolderStats.depth <= depth,
        )
    else:
        # Get root level folders
        query = select(FolderStats).where(
            FolderStats.depth == 0,
        )

    result = await db.execute(query.order_by(FolderStats.total_size.desc()))
    folders = result.scalars().all()

    async def get_filtered_stats(folder_path: str) -> dict:
        """Get file stats filtered by extensions for a folder"""
        if not ext_list:
            return None

        stats_result = await db.execute(
            select(
                func.count(FileStats.id).label("file_count"),
                func.sum(FileStats.size).label("total_size"),
                func.sum(FileStats.duration).label("total_duration"),
            )
            .where(FileStats.folder_path.like(f"{folder_path}%"))
            .where(FileStats.extension.in_(ext_list))
        )
        row = stats_result.first()
        return {
            "file_count": row.file_count or 0,
            "total_size": row.total_size or 0,
            "total_duration": row.total_duration or 0.0,
        }

    async def build_tree(folder: FolderStats, current_depth: int) -> FolderTreeNode:
        children = []
        if current_depth < depth:
            child_result = await db.execute(
                select(FolderStats)
                .where(FolderStats.parent_path == folder.path)
                .order_by(FolderStats.total_size.desc())
                .limit(20)  # Limit children for performance
            )
            child_folders = child_result.scalars().all()
            children = [
                await build_tree(child, current_depth + 1) for child in child_folders
            ]

        # Apply extension filter if specified
        if ext_list:
            filtered = await get_filtered_stats(folder.path)
            return FolderTreeNode(
                id=folder.id,
                name=folder.name,
                path=folder.path,
                size=filtered["total_size"],
                size_formatted=format_size(filtered["total_size"]),
                file_count=filtered["file_count"],
                folder_count=folder.folder_count,
                duration=filtered["total_duration"],
                depth=folder.depth,
                children=children,
            )

        return FolderTreeNode(
            id=folder.id,
            name=folder.name,
            path=folder.path,
            size=folder.total_size,
            size_formatted=format_size(folder.total_size),
            file_count=folder.file_count,
            folder_count=folder.folder_count,
            duration=folder.total_duration,
            depth=folder.depth,
            children=children,
        )

    tree = [await build_tree(folder, 0) for folder in folders]
    return tree


@router.get("/details", response_model=FolderDetails)
async def get_folder_details(
    path: str = Query(..., description="Folder path"),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information for a specific folder"""

    # Get folder
    result = await db.execute(
        select(FolderStats).where(FolderStats.path == path)
    )
    folder = result.scalar_one_or_none()

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    # Get file type breakdown for this folder
    type_result = await db.execute(
        select(
            FileStats.extension,
            FileStats.mime_type,
            func.count(FileStats.id).label("file_count"),
            func.sum(FileStats.size).label("total_size"),
        )
        .where(FileStats.folder_path.like(f"{path}%"))
        .group_by(FileStats.extension, FileStats.mime_type)
        .order_by(func.sum(FileStats.size).desc())
        .limit(20)
    )
    type_rows = type_result.all()

    total_size = sum(row.total_size or 0 for row in type_rows)
    file_types = [
        FileTypeStats(
            extension=row.extension or "unknown",
            mime_type=row.mime_type,
            file_count=row.file_count,
            total_size=row.total_size or 0,
            total_size_formatted=format_size(row.total_size or 0),
            percentage=(row.total_size / total_size * 100) if total_size > 0 else 0,
        )
        for row in type_rows
    ]

    return FolderDetails(
        path=folder.path,
        name=folder.name,
        size=folder.total_size,
        size_formatted=format_size(folder.total_size),
        file_count=folder.file_count,
        folder_count=folder.folder_count,
        duration=folder.total_duration,
        duration_formatted=format_duration(folder.total_duration),
        file_types=file_types,
        last_scanned_at=folder.last_scanned_at,
    )


@router.get("/top", response_model=List[FolderTreeNode])
async def get_top_folders(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get top folders by size"""

    result = await db.execute(
        select(FolderStats)
        .order_by(FolderStats.total_size.desc())
        .limit(limit)
    )
    folders = result.scalars().all()

    return [
        FolderTreeNode(
            id=folder.id,
            name=folder.name,
            path=folder.path,
            size=folder.total_size,
            size_formatted=format_size(folder.total_size),
            file_count=folder.file_count,
            folder_count=folder.folder_count,
            duration=folder.total_duration,
            depth=folder.depth,
            children=[],
        )
        for folder in folders
    ]
