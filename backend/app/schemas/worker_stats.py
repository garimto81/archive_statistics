"""
Worker Statistics Schemas
Pydantic models for worker (PIC) statistics aggregation
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, computed_field


class WorkerTaskResponse(BaseModel):
    """Individual task assigned to a worker"""

    id: int
    archive_id: int
    archive_name: Optional[str] = None
    category: str
    status: str
    total_videos: int
    excel_done: int
    progress_percent: float
    notes1: Optional[str] = None
    notes2: Optional[str] = None

    class Config:
        from_attributes = True


class WorkerStatsResponse(BaseModel):
    """Aggregated statistics for a single worker (PIC)"""

    pic: str
    task_count: int
    total_videos: int
    total_done: int
    progress_percent: float
    archives: List[str]  # List of archive names
    status_breakdown: Dict[str, int]  # {"completed": 2, "in_progress": 1, ...}


class WorkerDetailResponse(BaseModel):
    """Detailed worker statistics with task list"""

    pic: str
    task_count: int
    total_videos: int
    total_done: int
    progress_percent: float
    archives: List[str]
    status_breakdown: Dict[str, int]
    tasks: List[WorkerTaskResponse]


class WorkerStatsSummary(BaseModel):
    """Overall summary statistics"""

    total_workers: int
    total_videos: int
    total_done: int
    overall_progress: float
    by_status: Dict[str, int]
    by_archive: Dict[str, int]  # Videos per archive


class WorkerStatsListResponse(BaseModel):
    """Worker statistics list with summary"""

    workers: List[WorkerStatsResponse]
    summary: WorkerStatsSummary
