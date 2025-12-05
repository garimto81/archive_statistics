from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime


class ArchiveBase(BaseModel):
    """Archive base schema"""

    name: str
    description: Optional[str] = None


class ArchiveCreate(ArchiveBase):
    pass


class ArchiveResponse(ArchiveBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkStatusBase(BaseModel):
    """Work status base schema"""

    category: str
    pic: Optional[str] = None
    status: str = "pending"
    total_videos: int = 0
    excel_done: int = 0
    notes1: Optional[str] = None
    notes2: Optional[str] = None


class WorkStatusCreate(WorkStatusBase):
    """Create work status"""

    archive_id: int


class WorkStatusUpdate(BaseModel):
    """Update work status"""

    category: Optional[str] = None
    pic: Optional[str] = None
    status: Optional[str] = None
    total_videos: Optional[int] = None
    excel_done: Optional[int] = None
    notes1: Optional[str] = None
    notes2: Optional[str] = None


class WorkStatusResponse(WorkStatusBase):
    """Work status response"""

    id: int
    archive_id: int
    archive_name: Optional[str] = None
    progress_percent: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkStatusListResponse(BaseModel):
    """List of work statuses with summary"""

    items: List[WorkStatusResponse]
    total_count: int
    total_videos: int
    total_done: int
    overall_progress: float


class WorkStatusCSVRow(BaseModel):
    """CSV import row schema"""

    archive: str
    category: str
    pic: Optional[str] = None
    status: Optional[str] = None
    total_videos: int = 0
    excel_done: int = 0
    notes1: Optional[str] = None
    notes2: Optional[str] = None


class WorkStatusImportResult(BaseModel):
    """CSV import result"""

    success: bool
    total_rows: int
    imported_rows: int
    skipped_rows: int
    errors: List[str] = []
