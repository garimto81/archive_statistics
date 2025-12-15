"""
Data Sources API - 통합 데이터 소스 상태 조회

모든 Google Sheets 데이터 소스의 상태를 통합하여 제공합니다.
- archive db (Work Status)
- metadata db (Hand Analysis)
- iconik db (MAM Metadata - 미구현)

Block: api.data_sources
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.hand_analysis import HandAnalysis
from app.models.work_status import WorkStatus
from app.services.hand_analysis_sync import hand_analysis_sync_service
from app.services.sheets_sync import sheets_sync_service

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


class HandAnalysisSummary(BaseModel):
    """Hand Analysis 요약"""

    total_hands: int
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
        last_sync=(
            sheets_sync_service.last_sync_time.isoformat()
            if sheets_sync_service.last_sync_time
            else None
        ),
        next_sync=(
            sheets_sync_service.next_sync_time.isoformat()
            if sheets_sync_service.next_sync_time
            else None
        ),
        record_count=sheets_result.synced_count if sheets_result else 0,
        details=(
            {
                "created": sheets_result.created_count if sheets_result else 0,
                "updated": sheets_result.updated_count if sheets_result else 0,
            }
            if sheets_result
            else None
        ),
    )

    # metadata_db (Hand Analysis)
    hand_result = hand_analysis_sync_service.last_sync_result
    metadata_db = DataSourceStatus(
        name="metadata db",
        type="Hand Analysis",
        enabled=hand_analysis_sync_service.is_enabled,
        status=hand_analysis_sync_service.status,
        last_sync=(
            hand_analysis_sync_service.last_sync_time.isoformat()
            if hand_analysis_sync_service.last_sync_time
            else None
        ),
        next_sync=(
            hand_analysis_sync_service.next_sync_time.isoformat()
            if hand_analysis_sync_service.next_sync_time
            else None
        ),
        record_count=hand_result.synced_count if hand_result else 0,
        details=(
            {
                "created": hand_result.created_count if hand_result else 0,
                "updated": hand_result.updated_count if hand_result else 0,
                "worksheets": hand_result.worksheets_processed if hand_result else 0,
            }
            if hand_result
            else None
        ),
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
    completed_query = select(func.count(WorkStatus.id)).where(
        WorkStatus.status == "completed"
    )
    completed = await db.scalar(completed_query) or 0

    in_progress_query = select(func.count(WorkStatus.id)).where(
        WorkStatus.status == "in_progress"
    )
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
        last_sync=(
            sheets_sync_service.last_sync_time.isoformat()
            if sheets_sync_service.last_sync_time
            else None
        ),
    )


@router.get("/hand-analysis/summary", response_model=HandAnalysisSummary)
async def get_hand_analysis_summary(
    db: AsyncSession = Depends(get_db),
):
    """
    Hand Analysis 요약 (Dashboard용)

    - 총 핸드 수
    - 워크시트별 핸드 수 분포
    """
    # 총 핸드 수
    total_query = select(func.count(HandAnalysis.id))
    total_hands = await db.scalar(total_query) or 0

    # 워크시트별 집계
    ws_query = (
        select(
            HandAnalysis.source_worksheet, func.count(HandAnalysis.id).label("count")
        )
        .group_by(HandAnalysis.source_worksheet)
        .order_by(func.count(HandAnalysis.id).desc())
    )

    ws_result = await db.execute(ws_query)
    by_worksheet = [
        {"worksheet": row[0] or "Unknown", "count": row[1]}
        for row in ws_result.fetchall()
    ]

    return HandAnalysisSummary(
        total_hands=total_hands,
        worksheets_count=len(by_worksheet),
        by_worksheet=by_worksheet,
        last_sync=(
            hand_analysis_sync_service.last_sync_time.isoformat()
            if hand_analysis_sync_service.last_sync_time
            else None
        ),
    )
