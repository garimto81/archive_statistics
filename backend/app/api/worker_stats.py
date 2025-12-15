"""
Worker Statistics API
Aggregates work status data by PIC (Person In Charge)
"""

from collections import defaultdict
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.work_status import Archive, WorkStatus
from app.schemas.worker_stats import (
    WorkerDetailResponse,
    WorkerStatsListResponse,
    WorkerStatsResponse,
    WorkerStatsSummary,
    WorkerTaskResponse,
)

router = APIRouter()


def calculate_progress(total: int, done: int) -> float:
    """Calculate progress percentage"""
    return round((done / total * 100), 2) if total > 0 else 0.0


@router.get("", response_model=WorkerStatsListResponse)
async def get_worker_stats(db: AsyncSession = Depends(get_db)):
    """
    Get aggregated statistics for all workers (PICs)

    Returns:
        - workers: List of worker statistics
        - summary: Overall summary including totals
    """
    # Fetch all work statuses with archive info
    result = await db.execute(
        select(WorkStatus, Archive.name.label("archive_name"))
        .outerjoin(Archive)
        .order_by(WorkStatus.pic)
    )
    rows = result.all()

    # Aggregate by PIC
    workers_data: Dict[str, dict] = defaultdict(
        lambda: {
            "task_count": 0,
            "total_videos": 0,
            "total_done": 0,
            "archives": set(),
            "status_breakdown": defaultdict(int),
        }
    )

    # Summary counters
    total_videos = 0
    total_done = 0
    status_counts: Dict[str, int] = defaultdict(int)
    archive_counts: Dict[str, int] = defaultdict(int)

    for row in rows:
        ws = row[0]
        archive_name = row[1] or "Unknown"

        # Use "Unassigned" for null PIC
        pic = ws.pic if ws.pic else "Unassigned"

        # Aggregate worker data
        workers_data[pic]["task_count"] += 1
        workers_data[pic]["total_videos"] += ws.total_videos
        workers_data[pic]["total_done"] += ws.excel_done
        workers_data[pic]["archives"].add(archive_name)
        workers_data[pic]["status_breakdown"][ws.status] += 1

        # Summary aggregation
        total_videos += ws.total_videos
        total_done += ws.excel_done
        status_counts[ws.status] += 1
        archive_counts[archive_name] += ws.total_videos

    # Build worker responses
    workers: List[WorkerStatsResponse] = []
    for pic, data in sorted(workers_data.items()):
        workers.append(
            WorkerStatsResponse(
                pic=pic,
                task_count=data["task_count"],
                total_videos=data["total_videos"],
                total_done=data["total_done"],
                progress_percent=calculate_progress(
                    data["total_videos"], data["total_done"]
                ),
                archives=sorted(list(data["archives"])),
                status_breakdown=dict(data["status_breakdown"]),
            )
        )

    # Build summary
    summary = WorkerStatsSummary(
        total_workers=len(workers),
        total_videos=total_videos,
        total_done=total_done,
        overall_progress=calculate_progress(total_videos, total_done),
        by_status=dict(status_counts),
        by_archive=dict(archive_counts),
    )

    return WorkerStatsListResponse(workers=workers, summary=summary)


@router.get("/summary", response_model=WorkerStatsSummary)
async def get_worker_stats_summary(db: AsyncSession = Depends(get_db)):
    """
    Get overall summary statistics only

    Returns summary with:
        - total_workers: Number of unique PICs
        - total_videos: Sum of all videos
        - total_done: Sum of completed videos
        - overall_progress: Percentage complete
        - by_status: Count by status
        - by_archive: Video count by archive
    """
    # Count unique workers
    worker_count_result = await db.execute(
        select(func.count(func.distinct(WorkStatus.pic)))
    )
    unique_pics = worker_count_result.scalar() or 0

    # Check if there are any null PICs (add 1 for "Unassigned")
    null_pic_result = await db.execute(
        select(func.count()).where(WorkStatus.pic.is_(None))
    )
    has_unassigned = (null_pic_result.scalar() or 0) > 0

    total_workers = unique_pics + (1 if has_unassigned else 0)

    # Aggregate totals
    totals_result = await db.execute(
        select(
            func.sum(WorkStatus.total_videos),
            func.sum(WorkStatus.excel_done),
        )
    )
    totals = totals_result.first()
    total_videos = totals[0] or 0
    total_done = totals[1] or 0

    # Status breakdown
    status_result = await db.execute(
        select(WorkStatus.status, func.count()).group_by(WorkStatus.status)
    )
    by_status = {row[0]: row[1] for row in status_result.all()}

    # Archive breakdown
    archive_result = await db.execute(
        select(Archive.name, func.sum(WorkStatus.total_videos))
        .join(WorkStatus)
        .group_by(Archive.name)
    )
    by_archive = {row[0]: row[1] for row in archive_result.all()}

    return WorkerStatsSummary(
        total_workers=total_workers,
        total_videos=total_videos,
        total_done=total_done,
        overall_progress=calculate_progress(total_videos, total_done),
        by_status=by_status,
        by_archive=by_archive,
    )


@router.get("/{pic}", response_model=WorkerDetailResponse)
async def get_worker_detail(
    pic: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed statistics for a specific worker (PIC)

    Args:
        pic: Worker name (use "Unassigned" for tasks without PIC)

    Returns:
        - Worker aggregated stats
        - List of all tasks assigned to this worker
    """
    # Handle "Unassigned" special case
    if pic.lower() == "unassigned":
        query = (
            select(WorkStatus, Archive.name.label("archive_name"))
            .outerjoin(Archive)
            .where(WorkStatus.pic.is_(None))
        )
    else:
        query = (
            select(WorkStatus, Archive.name.label("archive_name"))
            .outerjoin(Archive)
            .where(WorkStatus.pic == pic)
        )

    result = await db.execute(query.order_by(WorkStatus.category))
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"Worker '{pic}' not found")

    # Build task list
    tasks: List[WorkerTaskResponse] = []
    total_videos = 0
    total_done = 0
    archives = set()
    status_breakdown: Dict[str, int] = defaultdict(int)

    for row in rows:
        ws = row[0]
        archive_name = row[1] or "Unknown"

        progress = calculate_progress(ws.total_videos, ws.excel_done)

        tasks.append(
            WorkerTaskResponse(
                id=ws.id,
                archive_id=ws.archive_id,
                archive_name=archive_name,
                category=ws.category,
                status=ws.status,
                total_videos=ws.total_videos,
                excel_done=ws.excel_done,
                progress_percent=progress,
                notes1=ws.notes1,
                notes2=ws.notes2,
            )
        )

        total_videos += ws.total_videos
        total_done += ws.excel_done
        archives.add(archive_name)
        status_breakdown[ws.status] += 1

    return WorkerDetailResponse(
        pic=pic,
        task_count=len(tasks),
        total_videos=total_videos,
        total_done=total_done,
        progress_percent=calculate_progress(total_videos, total_done),
        archives=sorted(list(archives)),
        status_breakdown=dict(status_breakdown),
        tasks=tasks,
    )
