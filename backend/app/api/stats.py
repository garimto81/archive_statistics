from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.file_stats import FileStats, FolderStats, ScanHistory, DailySnapshot
from app.schemas.stats import (
    StatsSummary,
    FileTypeStats,
    HistoryData,
    HistoryResponse,
    CodecStats,
    CodecSummary,
    CodecCount,
    ExtensionCodecStats,
    CodecsByExtensionResponse,
    CodecTreeNode,
    FolderCodecSummary,
    FileCodecInfo,
)
from app.services.utils import format_size, format_duration

router = APIRouter()


@router.get("/summary", response_model=StatsSummary)
async def get_stats_summary(
    extensions: Optional[str] = Query(None, description="Comma-separated extensions filter (e.g., mp4,mkv,avi)"),
    db: AsyncSession = Depends(get_db),
):
    """Get overall archive statistics summary with optional extension filter"""

    # Parse extensions filter
    ext_list = None
    if extensions:
        ext_list = [f".{e.strip().lower().lstrip('.')}" for e in extensions.split(",") if e.strip()]

    # If filtering by extensions, get stats directly from FileStats
    if ext_list:
        query = select(
            func.count(FileStats.id).label("total_files"),
            func.sum(FileStats.size).label("total_size"),
            func.sum(FileStats.duration).label("total_duration"),
        ).where(FileStats.extension.in_(ext_list))

        result = await db.execute(query)
        stats = result.first()

        total_files = stats.total_files or 0
        total_size = stats.total_size or 0
        total_duration = stats.total_duration or 0.0

        # Count folders containing these files
        folder_result = await db.execute(
            select(func.count(func.distinct(FileStats.folder_path)))
            .where(FileStats.extension.in_(ext_list))
        )
        total_folders = folder_result.scalar() or 0
        file_type_count = len(ext_list)
    else:
        # No filter - get totals from root folder (depth == 0) for size/files/duration
        result = await db.execute(
            select(
                func.sum(FolderStats.total_size).label("total_size"),
                func.sum(FolderStats.file_count).label("total_files"),
                func.sum(FolderStats.total_duration).label("total_duration"),
            ).where(FolderStats.depth == 0)
        )
        stats = result.first()

        total_files = stats.total_files or 0
        total_size = stats.total_size or 0
        total_duration = stats.total_duration or 0.0

        # Get total folder count (all folders including root)
        folder_count_result = await db.execute(
            select(func.count(FolderStats.id))
        )
        total_folders = folder_count_result.scalar() or 0

        # If folder duration is 0, get it directly from files (fallback)
        if total_duration == 0:
            duration_result = await db.execute(
                select(func.sum(FileStats.duration))
            )
            total_duration = duration_result.scalar() or 0.0

        # Get unique file type count
        type_result = await db.execute(
            select(func.count(func.distinct(FileStats.extension)))
        )
        file_type_count = type_result.scalar() or 0

    # Get last scan time
    scan_result = await db.execute(
        select(ScanHistory.completed_at)
        .where(ScanHistory.status == "completed")
        .order_by(ScanHistory.completed_at.desc())
        .limit(1)
    )
    last_scan = scan_result.scalar()

    return StatsSummary(
        total_files=total_files,
        total_size=total_size,
        total_size_formatted=format_size(total_size),
        total_duration=total_duration,
        total_duration_formatted=format_duration(total_duration),
        total_folders=total_folders,
        file_type_count=file_type_count,
        last_scan_at=last_scan,
    )


@router.get("/file-types", response_model=List[FileTypeStats])
async def get_file_type_stats(
    limit: int = Query(default=20, ge=1, le=100),
    extensions: Optional[str] = Query(None, description="Comma-separated extensions filter"),
    db: AsyncSession = Depends(get_db),
):
    """Get file statistics by extension/type with optional filter"""

    # Parse extensions filter
    ext_list = None
    if extensions:
        ext_list = [f".{e.strip().lower().lstrip('.')}" for e in extensions.split(",") if e.strip()]

    query = select(
        FileStats.extension,
        func.count(FileStats.id).label("file_count"),
        func.sum(FileStats.size).label("total_size"),
    )

    if ext_list:
        query = query.where(FileStats.extension.in_(ext_list))

    query = query.group_by(FileStats.extension).order_by(func.sum(FileStats.size).desc()).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    # Calculate total for percentage
    total_size = sum(row.total_size or 0 for row in rows)

    return [
        FileTypeStats(
            extension=row.extension or "unknown",
            file_count=row.file_count,
            total_size=row.total_size or 0,
            total_size_formatted=format_size(row.total_size or 0),
            percentage=(row.total_size / total_size * 100) if total_size > 0 else 0,
        )
        for row in rows
    ]


@router.get("/available-extensions", response_model=List[str])
async def get_available_extensions(db: AsyncSession = Depends(get_db)):
    """Get list of all available file extensions in the archive"""

    result = await db.execute(
        select(FileStats.extension)
        .where(FileStats.extension.isnot(None))
        .group_by(FileStats.extension)
        .order_by(func.count(FileStats.id).desc())
    )
    extensions = [row[0] for row in result.all() if row[0]]

    # Remove the leading dot for cleaner display
    return [ext.lstrip('.') for ext in extensions]


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    period: str = Query(default="daily", regex="^(daily|weekly|monthly)$"),
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get historical statistics data"""

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    result = await db.execute(
        select(DailySnapshot)
        .where(DailySnapshot.date >= start_date)
        .where(DailySnapshot.date <= end_date)
        .order_by(DailySnapshot.date.asc())
    )
    snapshots = result.scalars().all()

    data = []
    prev_size = None
    for snapshot in snapshots:
        size_change = None
        if prev_size is not None:
            size_change = snapshot.total_size - prev_size
        prev_size = snapshot.total_size

        data.append(
            HistoryData(
                date=snapshot.date,
                total_size=snapshot.total_size,
                total_files=snapshot.total_files,
                total_folders=snapshot.total_folders,
                total_duration=snapshot.total_duration,
                size_change=size_change,
            )
        )

    return HistoryResponse(
        data=data,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/codecs", response_model=CodecSummary)
async def get_codec_stats(
    limit: int = Query(default=10, ge=1, le=50),
    extensions: Optional[str] = Query(None, description="Comma-separated extensions filter"),
    db: AsyncSession = Depends(get_db),
):
    """Get codec statistics for video and audio files"""

    # Parse extensions filter
    ext_list = None
    if extensions:
        ext_list = [f".{e.strip().lower().lstrip('.')}" for e in extensions.split(",") if e.strip()]

    # Query video codecs
    video_query = select(
        FileStats.video_codec,
        func.count(FileStats.id).label("file_count"),
        func.sum(FileStats.size).label("total_size"),
        func.sum(FileStats.duration).label("total_duration"),
    ).where(FileStats.video_codec.isnot(None))

    if ext_list:
        video_query = video_query.where(FileStats.extension.in_(ext_list))

    video_query = video_query.group_by(FileStats.video_codec).order_by(
        func.count(FileStats.id).desc()
    ).limit(limit)

    video_result = await db.execute(video_query)
    video_rows = video_result.all()

    # Query audio codecs
    audio_query = select(
        FileStats.audio_codec,
        func.count(FileStats.id).label("file_count"),
        func.sum(FileStats.size).label("total_size"),
        func.sum(FileStats.duration).label("total_duration"),
    ).where(FileStats.audio_codec.isnot(None))

    if ext_list:
        audio_query = audio_query.where(FileStats.extension.in_(ext_list))

    audio_query = audio_query.group_by(FileStats.audio_codec).order_by(
        func.count(FileStats.id).desc()
    ).limit(limit)

    audio_result = await db.execute(audio_query)
    audio_rows = audio_result.all()

    # Calculate totals for percentages
    total_video_size = sum(row.total_size or 0 for row in video_rows)
    total_audio_size = sum(row.total_size or 0 for row in audio_rows)

    # Count total files with codec info
    video_count_query = select(func.count(FileStats.id)).where(FileStats.video_codec.isnot(None))
    audio_count_query = select(func.count(FileStats.id)).where(FileStats.audio_codec.isnot(None))

    if ext_list:
        video_count_query = video_count_query.where(FileStats.extension.in_(ext_list))
        audio_count_query = audio_count_query.where(FileStats.extension.in_(ext_list))

    total_video_files = (await db.execute(video_count_query)).scalar() or 0
    total_audio_analyzed = (await db.execute(audio_count_query)).scalar() or 0

    # Build response
    video_codecs = [
        CodecStats(
            codec_name=row.video_codec,
            codec_type="video",
            file_count=row.file_count,
            total_size=row.total_size or 0,
            total_size_formatted=format_size(row.total_size or 0),
            total_duration=row.total_duration or 0.0,
            total_duration_formatted=format_duration(row.total_duration or 0.0),
            percentage=(row.total_size / total_video_size * 100) if total_video_size > 0 else 0,
        )
        for row in video_rows
    ]

    audio_codecs = [
        CodecStats(
            codec_name=row.audio_codec,
            codec_type="audio",
            file_count=row.file_count,
            total_size=row.total_size or 0,
            total_size_formatted=format_size(row.total_size or 0),
            total_duration=row.total_duration or 0.0,
            total_duration_formatted=format_duration(row.total_duration or 0.0),
            percentage=(row.total_size / total_audio_size * 100) if total_audio_size > 0 else 0,
        )
        for row in audio_rows
    ]

    return CodecSummary(
        video_codecs=video_codecs,
        audio_codecs=audio_codecs,
        total_video_files=total_video_files,
        total_audio_analyzed=total_audio_analyzed,
    )


@router.get("/codecs-by-extension", response_model=CodecsByExtensionResponse)
async def get_codecs_by_extension(
    limit: int = Query(default=10, ge=1, le=50, description="Max extensions to return"),
    codec_limit: int = Query(default=5, ge=1, le=20, description="Max codecs per extension"),
    db: AsyncSession = Depends(get_db),
):
    """Get codec distribution grouped by file extension.

    Returns the top N extensions with their video/audio codec breakdown.
    """

    # Step 1: Get top extensions by file count (only those with codec info)
    ext_query = select(
        FileStats.extension,
        func.count(FileStats.id).label("file_count"),
    ).where(
        FileStats.video_codec.isnot(None)
    ).group_by(
        FileStats.extension
    ).order_by(
        func.count(FileStats.id).desc()
    ).limit(limit)

    ext_result = await db.execute(ext_query)
    top_extensions = ext_result.all()

    extensions_data = []

    for ext_row in top_extensions:
        extension = ext_row.extension or "unknown"
        total_files = ext_row.file_count

        # Step 2: Get video codec distribution for this extension
        video_query = select(
            FileStats.video_codec,
            func.count(FileStats.id).label("count"),
        ).where(
            FileStats.extension == ext_row.extension,
            FileStats.video_codec.isnot(None),
        ).group_by(
            FileStats.video_codec
        ).order_by(
            func.count(FileStats.id).desc()
        ).limit(codec_limit)

        video_result = await db.execute(video_query)
        video_rows = video_result.all()
        video_total = sum(r.count for r in video_rows)

        video_codecs = [
            CodecCount(
                codec_name=row.video_codec,
                file_count=row.count,
                percentage=(row.count / video_total * 100) if video_total > 0 else 0,
            )
            for row in video_rows
        ]

        # Step 3: Get audio codec distribution for this extension
        audio_query = select(
            FileStats.audio_codec,
            func.count(FileStats.id).label("count"),
        ).where(
            FileStats.extension == ext_row.extension,
            FileStats.audio_codec.isnot(None),
        ).group_by(
            FileStats.audio_codec
        ).order_by(
            func.count(FileStats.id).desc()
        ).limit(codec_limit)

        audio_result = await db.execute(audio_query)
        audio_rows = audio_result.all()
        audio_total = sum(r.count for r in audio_rows)

        audio_codecs = [
            CodecCount(
                codec_name=row.audio_codec,
                file_count=row.count,
                percentage=(row.count / audio_total * 100) if audio_total > 0 else 0,
            )
            for row in audio_rows
        ]

        extensions_data.append(
            ExtensionCodecStats(
                extension=extension,
                total_files=total_files,
                video_codecs=video_codecs,
                audio_codecs=audio_codecs,
            )
        )

    return CodecsByExtensionResponse(
        extensions=extensions_data,
        total_extensions=len(extensions_data),
    )


@router.get("/codecs/tree", response_model=List[CodecTreeNode])
async def get_codec_tree(
    path: Optional[str] = Query(None, description="Starting folder path"),
    depth: int = Query(default=2, ge=1, le=5, description="Tree depth"),
    include_files: bool = Query(default=False, description="Include file list"),
    db: AsyncSession = Depends(get_db),
):
    """Get codec information in folder tree structure.

    폴더 트리 구조로 코덱 정보를 반환합니다.
    Progress Overview와 유사한 구조로 lazy loading을 지원합니다.
    """

    async def build_codec_tree(
        folder: FolderStats,
        current_depth: int,
        max_depth: int,
        include_files: bool,
    ) -> dict:
        """재귀적으로 코덱 트리 구축"""

        # 폴더 내 파일들의 코덱 정보 집계
        file_query = select(
            FileStats.video_codec,
            FileStats.audio_codec,
            func.count(FileStats.id).label("count"),
        ).where(
            FileStats.folder_path == folder.path
        ).group_by(
            FileStats.video_codec,
            FileStats.audio_codec,
        )

        file_result = await db.execute(file_query)
        codec_rows = file_result.fetchall()

        # 코덱 통계 집계
        video_codecs = {}
        audio_codecs = {}
        files_with_codec = 0

        for row in codec_rows:
            if row.video_codec:
                video_codecs[row.video_codec] = video_codecs.get(row.video_codec, 0) + row.count
                files_with_codec += row.count
            if row.audio_codec:
                audio_codecs[row.audio_codec] = audio_codecs.get(row.audio_codec, 0) + row.count

        # 최다 코덱 찾기
        top_video = max(video_codecs.items(), key=lambda x: x[1])[0] if video_codecs else None
        top_audio = max(audio_codecs.items(), key=lambda x: x[1])[0] if audio_codecs else None

        codec_summary = FolderCodecSummary(
            total_files=folder.file_count,
            files_with_codec=files_with_codec,
            video_codecs=video_codecs,
            audio_codecs=audio_codecs,
            top_video_codec=top_video,
            top_audio_codec=top_audio,
        ) if video_codecs or audio_codecs else None

        # 파일 목록 (옵션)
        files = None
        if include_files:
            files_query = select(FileStats).where(
                FileStats.folder_path == folder.path,
                FileStats.video_codec.isnot(None),
            ).order_by(FileStats.name).limit(100)

            files_result = await db.execute(files_query)
            file_list = files_result.scalars().all()

            files = [
                FileCodecInfo(
                    id=f.id,
                    name=f.name,
                    path=f.path,
                    size=f.size,
                    size_formatted=format_size(f.size),
                    duration=f.duration or 0,
                    duration_formatted=format_duration(f.duration or 0),
                    extension=f.extension,
                    video_codec=f.video_codec,
                    audio_codec=f.audio_codec,
                )
                for f in file_list
            ]

        # 자식 폴더 (재귀)
        children = []
        if current_depth < max_depth:
            child_result = await db.execute(
                select(FolderStats)
                .where(FolderStats.parent_path == folder.path)
                .order_by(FolderStats.total_size.desc())
            )
            child_folders = child_result.scalars().all()

            for child in child_folders:
                child_data = await build_codec_tree(
                    child, current_depth + 1, max_depth, include_files
                )
                children.append(child_data)

                # 자식 폴더의 코덱 정보를 부모에 합산
                child_cs = child_data.get("codec_summary")
                if child_cs:
                    # Pydantic 객체의 속성에 직접 접근
                    for codec, count in (child_cs.video_codecs or {}).items():
                        video_codecs[codec] = video_codecs.get(codec, 0) + count
                    for codec, count in (child_cs.audio_codecs or {}).items():
                        audio_codecs[codec] = audio_codecs.get(codec, 0) + count
                    files_with_codec += child_cs.files_with_codec or 0

            # 합산 후 codec_summary 업데이트
            if video_codecs or audio_codecs:
                top_video = max(video_codecs.items(), key=lambda x: x[1])[0] if video_codecs else None
                top_audio = max(audio_codecs.items(), key=lambda x: x[1])[0] if audio_codecs else None
                codec_summary = FolderCodecSummary(
                    total_files=folder.file_count,
                    files_with_codec=files_with_codec,
                    video_codecs=video_codecs,
                    audio_codecs=audio_codecs,
                    top_video_codec=top_video,
                    top_audio_codec=top_audio,
                )

        return {
            "id": folder.id,
            "name": folder.name,
            "path": folder.path,
            "size": folder.total_size,
            "size_formatted": format_size(folder.total_size),
            "file_count": folder.file_count,
            "folder_count": folder.folder_count,
            "duration": folder.total_duration,
            "duration_formatted": format_duration(folder.total_duration),
            "depth": folder.depth,
            "codec_summary": codec_summary,
            "children": children,
            "files": files,
        }

    # 시작 폴더 조회
    if path:
        query = select(FolderStats).where(FolderStats.parent_path == path)
    else:
        query = select(FolderStats).where(FolderStats.depth == 0)

    result = await db.execute(query.order_by(FolderStats.total_size.desc()))
    folders = result.scalars().all()

    tree = []
    for folder in folders:
        folder_data = await build_codec_tree(folder, 0, depth, include_files)
        tree.append(folder_data)

    return tree


@router.get("/codecs/folder/{folder_path:path}", response_model=CodecTreeNode)
async def get_codec_folder_detail(
    folder_path: str,
    include_files: bool = Query(default=True, description="Include file list"),
    db: AsyncSession = Depends(get_db),
):
    """Get codec information for a specific folder.

    특정 폴더의 코덱 정보와 자식 폴더 목록을 반환합니다.
    """
    from urllib.parse import unquote

    decoded_path = unquote(folder_path)
    if not decoded_path.startswith("/"):
        decoded_path = "/" + decoded_path

    # 폴더 조회
    folder_result = await db.execute(
        select(FolderStats).where(FolderStats.path == decoded_path)
    )
    folder = folder_result.scalar_one_or_none()

    if not folder:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Folder not found: {decoded_path}")

    # 현재 폴더의 코덱 통계
    file_query = select(
        FileStats.video_codec,
        FileStats.audio_codec,
        func.count(FileStats.id).label("count"),
    ).where(
        FileStats.folder_path == decoded_path
    ).group_by(
        FileStats.video_codec,
        FileStats.audio_codec,
    )

    file_result = await db.execute(file_query)
    codec_rows = file_result.fetchall()

    video_codecs = {}
    audio_codecs = {}
    files_with_codec = 0

    for row in codec_rows:
        if row.video_codec:
            video_codecs[row.video_codec] = video_codecs.get(row.video_codec, 0) + row.count
            files_with_codec += row.count
        if row.audio_codec:
            audio_codecs[row.audio_codec] = audio_codecs.get(row.audio_codec, 0) + row.count

    top_video = max(video_codecs.items(), key=lambda x: x[1])[0] if video_codecs else None
    top_audio = max(audio_codecs.items(), key=lambda x: x[1])[0] if audio_codecs else None

    codec_summary = FolderCodecSummary(
        total_files=folder.file_count,
        files_with_codec=files_with_codec,
        video_codecs=video_codecs,
        audio_codecs=audio_codecs,
        top_video_codec=top_video,
        top_audio_codec=top_audio,
    ) if video_codecs or audio_codecs else None

    # 파일 목록
    files = None
    if include_files:
        files_query = select(FileStats).where(
            FileStats.folder_path == decoded_path,
        ).order_by(FileStats.name).limit(200)

        files_result = await db.execute(files_query)
        file_list = files_result.scalars().all()

        files = [
            FileCodecInfo(
                id=f.id,
                name=f.name,
                path=f.path,
                size=f.size,
                size_formatted=format_size(f.size),
                duration=f.duration or 0,
                duration_formatted=format_duration(f.duration or 0),
                extension=f.extension,
                video_codec=f.video_codec,
                audio_codec=f.audio_codec,
            )
            for f in file_list
        ]

    # 자식 폴더
    child_result = await db.execute(
        select(FolderStats)
        .where(FolderStats.parent_path == decoded_path)
        .order_by(FolderStats.total_size.desc())
    )
    child_folders = child_result.scalars().all()

    children = []
    for child in child_folders:
        # 자식 폴더의 코덱 통계도 간략히 조회
        child_codec_query = select(
            FileStats.video_codec,
            func.count(FileStats.id).label("count"),
        ).where(
            FileStats.folder_path == child.path,
            FileStats.video_codec.isnot(None),
        ).group_by(FileStats.video_codec)

        child_codec_result = await db.execute(child_codec_query)
        child_codec_rows = child_codec_result.fetchall()

        child_video_codecs = {row.video_codec: row.count for row in child_codec_rows}
        child_top_video = max(child_video_codecs.items(), key=lambda x: x[1])[0] if child_video_codecs else None

        child_codec_summary = FolderCodecSummary(
            total_files=child.file_count,
            files_with_codec=sum(child_video_codecs.values()),
            video_codecs=child_video_codecs,
            audio_codecs={},
            top_video_codec=child_top_video,
            top_audio_codec=None,
        ) if child_video_codecs else None

        children.append(CodecTreeNode(
            id=child.id,
            name=child.name,
            path=child.path,
            size=child.total_size,
            size_formatted=format_size(child.total_size),
            file_count=child.file_count,
            folder_count=child.folder_count,
            duration=child.total_duration,
            duration_formatted=format_duration(child.total_duration),
            depth=child.depth,
            codec_summary=child_codec_summary,
            children=[],
            files=None,
        ))

    return CodecTreeNode(
        id=folder.id,
        name=folder.name,
        path=folder.path,
        size=folder.total_size,
        size_formatted=format_size(folder.total_size),
        file_count=folder.file_count,
        folder_count=folder.folder_count,
        duration=folder.total_duration,
        duration_formatted=format_duration(folder.total_duration),
        depth=folder.depth,
        codec_summary=codec_summary,
        children=children,
        files=files,
    )
