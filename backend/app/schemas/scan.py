from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ScanStatus(BaseModel):
    """Current scan status"""

    is_scanning: bool
    scan_id: Optional[int] = None
    progress: float = 0.0  # 0-100
    current_folder: Optional[str] = None
    files_scanned: int = 0
    total_files_estimated: int = 0
    started_at: Optional[datetime] = None
    elapsed_seconds: Optional[float] = None
    estimated_remaining_seconds: Optional[float] = None
    logs: List[str] = []  # Recent log messages
    media_files_processed: int = 0
    total_duration_found: float = 0.0
    active_viewers: int = 0  # Number of active clients viewing the dashboard


class ScanHistoryResponse(BaseModel):
    """Scan history entry"""

    id: int
    scan_type: str
    status: str
    total_size: int
    total_files: int
    total_folders: int
    total_duration: float
    new_files: int
    deleted_files: int
    size_change: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class ScanStartRequest(BaseModel):
    """Scan start request"""

    scan_type: str = "manual"
    path: Optional[str] = None  # Optional subfolder path


class ScanStartResponse(BaseModel):
    """Scan start response"""

    scan_id: int
    message: str
    status: str
