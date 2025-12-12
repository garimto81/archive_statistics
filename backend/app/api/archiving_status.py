"""
Archiving Status API - 아카이빙 작업 현황 조회 및 관리

Block: api.archiving
Note: This is an alias module for backward compatibility (Issue #37)
      The actual implementation is in work_status.py
      Use /api/archiving-status as the preferred endpoint in new code
"""

# Re-export everything from work_status.py
from app.api.work_status import router

# Schema re-exports for convenience
from app.schemas.work_status import (
    WorkStatusCreate as ArchivingStatusCreate,
    WorkStatusUpdate as ArchivingStatusUpdate,
    WorkStatusResponse as ArchivingStatusResponse,
    WorkStatusListResponse as ArchivingStatusListResponse,
    WorkStatusImportResult as ArchivingStatusImportResult,
    ArchiveResponse,
    ArchiveCreate,
)

__all__ = [
    "router",
    "ArchivingStatusCreate",
    "ArchivingStatusUpdate",
    "ArchivingStatusResponse",
    "ArchivingStatusListResponse",
    "ArchivingStatusImportResult",
    "ArchiveResponse",
    "ArchiveCreate",
]
