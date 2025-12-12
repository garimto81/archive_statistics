"""
Archiving Status Model

아카이빙 작업 현황 추적 모델
Google Sheets에서 동기화

Block: sync.status
Note: This is an alias module for backward compatibility (Issue #37)
      The actual model is in work_status.py with class name WorkStatus
      Use ArchivingStatus as the preferred name in new code
"""

# Re-export from work_status.py with new names
from app.models.work_status import WorkStatus as ArchivingStatus
from app.models.work_status import Archive

__all__ = ["ArchivingStatus", "Archive"]
