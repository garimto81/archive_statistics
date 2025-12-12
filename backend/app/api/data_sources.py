"""
Data Sources API - 통합 데이터 소스 상태 조회

모든 Google Sheets 데이터 소스의 상태를 통합하여 제공합니다.
- archive db (Work Status)
- metadata db (Archive Metadata)
- iconik db (MAM Metadata - 미구현)

Block: api.data_sources
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.services.sheets_sync import sheets_sync_service
from app.services.archive_metadata_sync import archive_metadata_sync_service
from app.models.work_status import WorkStatus
from app.models.archive_metadata import ArchiveMetadata

router = APIRouter()


# ==================== Schemas ====================

class DataSourceStatus(BaseModel):
    """단일 데이터 소스 상태"""
    name: str
    type: str
    enabled: bool
    status: str
    last_sync: Optional[str]
    next_sync: Optional[str]
    record_count: int
    details: Optional[dict] = None


class AllDataSourcesResponse(BaseModel):
    """모든 데이터 소스 상태 응답"""
    archive_db: DataSourceStatus
    metadata_db: DataSourceStatus
    iconik_db: DataSourceStatus


class WorkStatusSummary(BaseModel):
    """Work Status 요약"""
    total_tasks: int
    completed: int
    in_progress: int
    pending: int
    overall_progress: float
    last_sync: Optional[str]


class ArchiveMetadataSummary(BaseModel):
    """Archive Metadata 요약"""
    total_entries: int
    worksheets_count: int
    by_worksheet: List[dict]
    last_sync: Optional[str]


# ==================== Endpoints ====================

@router.get("/status", response_model=AllDataSourcesResponse)
async def get_all_data_sources():
    """
    모든 데이터 소스 상태 조회

    - archive_db: Work Status 시트 (아카이빙 작업 현황)
    - metadata_db: Hand Analysis 시트 (핸드 분석 데이터)
    - iconik_db: iconik MAM 메타데이터 (미구현)
    """
    # archive_db (Work Status)
    sheets_result = sheets_sync_service.last_sync_result
    archive_db = DataSourceStatus(
        name="archive db",
        type="Work Status",
        enabled=sheets_sync_service.is_enabled,
        status=sheets_sync_service.status,
        last_sync=sheets_sync_service.last_sync_time.isoformat() if sheets_sync_service.last_sync_time else None,
        next_sync=sheets_sync_service.next_sync_time.isoformat() if sheets_sync_service.next_sync_time else None,
        record_count=sheets_result.synced_count if sheets_result else 0,
        details={
            "created": sheets_result.created_count if sheets_result else 0,
            "updated": sheets_result.updated_count if sheets_result else 0,
        } if sheets_result else None,
    )

    # metadata_db (Archive Metadata)
    metadata_result = archive_metadata_sync_service.last_sync_result
    metadata_db = DataSourceStatus(
        name="metadata db",
        type="Archive Metadata",
        enabled=archive_metadata_sync_service.is_enabled,
        status=archive_metadata_sync_service.status,
        last_sync=archive_metadata_sync_service.last_sync_time.isoformat() if archive_metadata_sync_service.last_sync_time else None,
        next_sync=archive_metadata_sync_service.next_sync_time.isoformat() if archive_metadata_sync_service.next_sync_time else None,
        record_count=metadata_result.synced_count if metadata_result else 0,
        details={
            "created": metadata_result.created_count if metadata_result else 0,
            "updated": metadata_result.updated_count if metadata_result else 0,
            "worksheets": metadata_result.worksheets_processed if metadata_result else 0,
        } if metadata_result else None,
    )

    # iconik_db (미구현)
    iconik_db = DataSourceStatus(
        name="iconik db",
        type="MAM Metadata",
        enabled=False,
        status="disabled",
        last_sync=None,
        next_sync=None,
        record_count=0,
        details={"note": "Not implemented"},
    )

    return AllDataSourcesResponse(
        archive_db=archive_db,
        metadata_db=metadata_db,
        iconik_db=iconik_db,
    )


@router.get("/work-status/summary", response_model=WorkStatusSummary)
async def get_work_status_summary(
    db: AsyncSession = Depends(get_db),
):
    """
    Work Status 요약 (Dashboard용)

    - 총 작업 수, 완료/진행중/대기 상태별 집계
    - 전체 진행률 계산
    """
    # 전체 작업 수
    total_query = select(func.count(WorkStatus.id))
    total_tasks = await db.scalar(total_query) or 0

    # 상태별 집계
    completed_query = select(func.count(WorkStatus.id)).where(WorkStatus.status == "completed")
    completed = await db.scalar(completed_query) or 0

    in_progress_query = select(func.count(WorkStatus.id)).where(WorkStatus.status == "in_progress")
    in_progress = await db.scalar(in_progress_query) or 0

    pending = total_tasks - completed - in_progress

    # 전체 진행률 (progress_percent 평균)
    progress_query = select(func.avg(WorkStatus.progress_percent))
    overall_progress = await db.scalar(progress_query) or 0.0

    return WorkStatusSummary(
        total_tasks=total_tasks,
        completed=completed,
        in_progress=in_progress,
        pending=pending,
        overall_progress=round(float(overall_progress), 1),
        last_sync=sheets_sync_service.last_sync_time.isoformat() if sheets_sync_service.last_sync_time else None,
    )


@router.get("/archive-metadata/summary", response_model=ArchiveMetadataSummary)
async def get_archive_metadata_summary(
    db: AsyncSession = Depends(get_db),
):
    """
    Archive Metadata 요약 (Dashboard용)

    - 총 엔트리 수
    - 워크시트별 엔트리 수 분포
    """
    # 총 엔트리 수
    total_query = select(func.count(ArchiveMetadata.id))
    total_entries = await db.scalar(total_query) or 0

    # 워크시트별 집계
    ws_query = select(
        ArchiveMetadata.source_worksheet,
        func.count(ArchiveMetadata.id).label('count')
    ).group_by(ArchiveMetadata.source_worksheet).order_by(func.count(ArchiveMetadata.id).desc())

    ws_result = await db.execute(ws_query)
    by_worksheet = [
        {"worksheet": row[0] or "Unknown", "count": row[1]}
        for row in ws_result.fetchall()
    ]

    return ArchiveMetadataSummary(
        total_entries=total_entries,
        worksheets_count=len(by_worksheet),
        by_worksheet=by_worksheet,
        last_sync=archive_metadata_sync_service.last_sync_time.isoformat() if archive_metadata_sync_service.last_sync_time else None,
    )
