from app.models.file_stats import FileStats, FolderStats, ScanHistory
from app.models.work_status import WorkStatus, Archive
from app.models.archive_metadata import ArchiveMetadata

# Backward compatibility alias (deprecated, use ArchiveMetadata)
HandAnalysis = ArchiveMetadata

__all__ = ["FileStats", "FolderStats", "ScanHistory", "WorkStatus", "Archive", "ArchiveMetadata", "HandAnalysis"]
