"""
Archiving Status Sync Service

아카이빙 작업 현황 동기화 서비스
Google Sheets에서 동기화

Block: sync.status
Note: This is an alias module for backward compatibility (Issue #37)
      The actual service is in sheets_sync.py
      Use ArchivingStatusSyncService as the preferred name in new code
"""

# Re-export from sheets_sync.py with new names
from app.services.sheets_sync import SheetsSyncService as ArchivingStatusSyncService
from app.services.sheets_sync import sheets_sync_service as archiving_status_sync_service
from app.services.sheets_sync import SyncResult as ArchivingStatusSyncResult

__all__ = [
    "ArchivingStatusSyncService",
    "archiving_status_sync_service",
    "ArchivingStatusSyncResult",
]
