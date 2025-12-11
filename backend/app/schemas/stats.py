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


class CodecStats(BaseModel):
    """Codec statistics"""

    codec_name: str
    codec_type: str  # "video" or "audio"
    file_count: int
    total_size: int
    total_size_formatted: str
    total_duration: float
    total_duration_formatted: str
    percentage: float


class CodecSummary(BaseModel):
    """Codec summary response"""

    video_codecs: List[CodecStats]
    audio_codecs: List[CodecStats]
    total_video_files: int
    total_audio_analyzed: int


class CodecCount(BaseModel):
    """Simple codec count for by-extension view"""

    codec_name: str
    file_count: int
    percentage: float


class ExtensionCodecStats(BaseModel):
    """Codec distribution for a single extension"""

    extension: str
    total_files: int
    video_codecs: List[CodecCount]
    audio_codecs: List[CodecCount]


class CodecsByExtensionResponse(BaseModel):
    """Codec distribution grouped by file extension"""

    extensions: List[ExtensionCodecStats]
    total_extensions: int


# === Codec Tree (폴더별 코덱 정보) ===

class FileCodecInfo(BaseModel):
    """파일별 코덱 정보"""

    id: int
    name: str
    path: str
    size: int
    size_formatted: str
    duration: float
    duration_formatted: str
    extension: Optional[str] = None
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None


class FolderCodecSummary(BaseModel):
    """폴더별 코덱 요약 통계"""

    total_files: int
    files_with_codec: int
    video_codecs: dict  # {"h264": 10, "hevc": 5}
    audio_codecs: dict  # {"aac": 12, "ac3": 3}
    top_video_codec: Optional[str] = None
    top_audio_codec: Optional[str] = None


class CodecTreeNode(BaseModel):
    """코덱 트리 노드 (폴더 + 코덱 정보)"""

    id: int
    name: str
    path: str
    size: int
    size_formatted: str
    file_count: int
    folder_count: int
    duration: float
    duration_formatted: str
    depth: int
    codec_summary: Optional[FolderCodecSummary] = None
    children: List["CodecTreeNode"] = []
    files: Optional[List[FileCodecInfo]] = None

    class Config:
        from_attributes = True


# Allow self-referential model
CodecTreeNode.model_rebuild()
