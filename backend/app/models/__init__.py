from app.models.file_stats import FileStats, FolderStats, ScanHistory
from app.models.work_status import WorkStatus, Archive
from app.models.archive_metadata import ArchiveMetadata
from app.models.archiving_status import ArchivingStatus

# Backward compatibility aliases (deprecated)
HandAnalysis = ArchiveMetadata  # Use ArchiveMetadata

__all__ = [
    "FileStats", "FolderStats", "ScanHistory",
    "WorkStatus", "ArchivingStatus", "Archive",  # ArchivingStatus is preferred
    "ArchiveMetadata", "HandAnalysis"
]
