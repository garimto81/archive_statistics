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
        # No filter - get totals from folder stats (root folder)
        result = await db.execute(
            select(
                func.sum(FolderStats.total_size).label("total_size"),
                func.sum(FolderStats.file_count).label("total_files"),
                func.count(FolderStats.id).label("total_folders"),
                func.sum(FolderStats.total_duration).label("total_duration"),
            ).where(FolderStats.depth == 0)
        )
        stats = result.first()

        total_files = stats.total_files or 0
        total_size = stats.total_size or 0
        total_duration = stats.total_duration or 0.0
        total_folders = stats.total_folders or 0

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
