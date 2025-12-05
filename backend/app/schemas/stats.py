from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class StatsSummary(BaseModel):
    """Overall statistics summary"""

    total_files: int
    total_size: int  # bytes
    total_size_formatted: str  # "856.3 TB"
    total_duration: float  # seconds
    total_duration_formatted: str  # "45,230 hrs"
    total_folders: int
    file_type_count: int
    last_scan_at: Optional[datetime] = None


class FileTypeStats(BaseModel):
    """File type statistics"""

    extension: str
    mime_type: Optional[str] = None
    file_count: int
    total_size: int
    total_size_formatted: str
    percentage: float


class FolderTreeNode(BaseModel):
    """Folder tree node for hierarchical view"""

    id: int
    name: str
    path: str
    size: int
    size_formatted: str
    file_count: int
    folder_count: int
    duration: float
    depth: int
    children: List["FolderTreeNode"] = []

    class Config:
        from_attributes = True


# Allow self-referential model
FolderTreeNode.model_rebuild()


class FolderDetails(BaseModel):
    """Folder detailed information"""

    path: str
    name: str
    size: int
    size_formatted: str
    file_count: int
    folder_count: int
    duration: float
    duration_formatted: str
    file_types: List[FileTypeStats]
    last_scanned_at: Optional[datetime] = None


class HistoryData(BaseModel):
    """Historical data point"""

    date: datetime
    total_size: int
    total_files: int
    total_folders: int
    total_duration: float
    size_change: Optional[int] = None


class HistoryResponse(BaseModel):
    """History response with list of data points"""

    data: List[HistoryData]
    period: str  # "daily", "weekly", "monthly"
    start_date: datetime
    end_date: datetime
