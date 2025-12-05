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
)
from app.services.utils import format_size, format_duration

router = APIRouter()


@router.get("/summary", response_model=StatsSummary)
async def get_stats_summary(db: AsyncSession = Depends(get_db)):
    """Get overall archive statistics summary"""

    # Get totals from folder stats (root folder)
    result = await db.execute(
        select(
            func.sum(FolderStats.total_size).label("total_size"),
            func.sum(FolderStats.file_count).label("total_files"),
            func.count(FolderStats.id).label("total_folders"),
            func.sum(FolderStats.total_duration).label("total_duration"),
        ).where(FolderStats.depth == 0)
    )
    stats = result.first()

    # If folder duration is 0, get it directly from files (fallback)
    total_duration = stats.total_duration or 0.0
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

    total_size = stats.total_size or 0

    return StatsSummary(
        total_files=stats.total_files or 0,
        total_size=total_size,
        total_size_formatted=format_size(total_size),
        total_duration=total_duration,
        total_duration_formatted=format_duration(total_duration),
        total_folders=stats.total_folders or 0,
        file_type_count=file_type_count,
        last_scan_at=last_scan,
    )


@router.get("/file-types", response_model=List[FileTypeStats])
async def get_file_type_stats(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get file statistics by extension/type"""

    result = await db.execute(
        select(
            FileStats.extension,
            func.count(FileStats.id).label("file_count"),
            func.sum(FileStats.size).label("total_size"),
        )
        .group_by(FileStats.extension)
        .order_by(func.sum(FileStats.size).desc())
        .limit(limit)
    )
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
