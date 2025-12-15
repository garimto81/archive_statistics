"""
Hands API - 핸드 분석 데이터 조회 및 동기화

Block: api.hands
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.hand_analysis import HandAnalysis
from app.services.hand_analysis_sync import hand_analysis_sync_service

router = APIRouter()


# ==================== Schemas ====================


class HandAnalysisResponse(BaseModel):
    """핸드 분석 응답"""

    id: int
    file_name: str
    nas_path: Optional[str]
    timecode_in: Optional[str]
    timecode_out: Optional[str]
    timecode_in_sec: float
    timecode_out_sec: float
    file_no: Optional[int]
    hand_grade: Optional[str]
    winner: Optional[str]
    hands: Optional[str]
    player_tags: Optional[str]
    poker_play_tags: Optional[str]
    source_worksheet: Optional[str]

    class Config:
        from_attributes = True


class HandListResponse(BaseModel):
    """핸드 목록 응답"""

    items: List[HandAnalysisResponse]
    total_count: int
    worksheets: List[str]


class FileProgressResponse(BaseModel):
    """파일별 진행률 응답"""

    file_name: str
    hand_count: int
    max_timecode_sec: float
    max_timecode: str
    hands: List[HandAnalysisResponse]


class HandSyncStatusResponse(BaseModel):
    """동기화 상태 응답"""

    enabled: bool
    status: str
    last_sync: Optional[str]
    next_sync: Optional[str]
    error: Optional[str]
    interval_minutes: int
    last_result: Optional[dict]


class HandSyncTriggerResponse(BaseModel):
    """동기화 트리거 응답"""

    success: bool
    synced_at: str
    total_records: int
    synced_count: int
    created_count: int
    updated_count: int
    worksheets_processed: int
    error: Optional[str]
    message: str


# ==================== Endpoints ====================


@router.get("", response_model=HandListResponse)
async def get_hands(
    worksheet: Optional[str] = Query(None, description="Filter by worksheet name"),
    file_name: Optional[str] = Query(
        None, description="Filter by file name (partial match)"
    ),
    grade: Optional[str] = Query(None, description="Filter by hand grade (★, ★★, ★★★)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    핸드 분석 목록 조회

    - worksheet: 워크시트명 필터 (예: "2024 WSOPC LA")
    - file_name: 파일명 부분 검색
    - grade: 핸드 등급 필터
    """
    query = select(HandAnalysis)

    if worksheet:
        query = query.where(HandAnalysis.source_worksheet == worksheet)
    if file_name:
        query = query.where(HandAnalysis.file_name.ilike(f"%{file_name}%"))
    if grade:
        query = query.where(HandAnalysis.hand_grade == grade)

    # 총 개수
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query)

    # 워크시트 목록
    ws_query = select(HandAnalysis.source_worksheet).distinct()
    ws_result = await db.execute(ws_query)
    worksheets = [row[0] for row in ws_result.fetchall() if row[0]]

    # 데이터 조회
    query = (
        query.order_by(
            HandAnalysis.source_worksheet,
            HandAnalysis.file_name,
            HandAnalysis.timecode_in_sec,
        )
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(query)
    items = result.scalars().all()

    return HandListResponse(
        items=[HandAnalysisResponse.model_validate(item) for item in items],
        total_count=total_count or 0,
        worksheets=worksheets,
    )


@router.get("/by-file/{file_name:path}", response_model=FileProgressResponse)
async def get_hands_by_file(
    file_name: str,
    db: AsyncSession = Depends(get_db),
):
    """
    특정 파일의 핸드 목록 및 진행률 조회

    - file_name: 파일명
    - 반환: 핸드 목록, 최대 타임코드, 핸드 수
    """
    query = (
        select(HandAnalysis)
        .where(HandAnalysis.file_name.ilike(f"%{file_name}%"))
        .order_by(HandAnalysis.timecode_out_sec.desc())
    )

    result = await db.execute(query)
    hands = result.scalars().all()

    if not hands:
        raise HTTPException(
            status_code=404, detail=f"No hands found for file: {file_name}"
        )

    max_timecode_sec = max(h.timecode_out_sec for h in hands)

    # 초를 HH:MM:SS로 변환
    hours = int(max_timecode_sec // 3600)
    minutes = int((max_timecode_sec % 3600) // 60)
    seconds = int(max_timecode_sec % 60)
    max_timecode = f"{hours}:{minutes:02d}:{seconds:02d}"

    return FileProgressResponse(
        file_name=hands[0].file_name,
        hand_count=len(hands),
        max_timecode_sec=max_timecode_sec,
        max_timecode=max_timecode,
        hands=[HandAnalysisResponse.model_validate(h) for h in hands],
    )


@router.get("/summary")
async def get_hands_summary(
    db: AsyncSession = Depends(get_db),
):
    """
    핸드 분석 요약 통계

    - 총 핸드 수
    - 워크시트별 핸드 수
    - 파일별 핸드 수 (상위 10개)
    """
    # 총 핸드 수
    total_query = select(func.count(HandAnalysis.id))
    total_count = await db.scalar(total_query) or 0

    # 워크시트별 핸드 수
    ws_query = select(
        HandAnalysis.source_worksheet, func.count(HandAnalysis.id).label("count")
    ).group_by(HandAnalysis.source_worksheet)
    ws_result = await db.execute(ws_query)
    by_worksheet = [
        {"worksheet": row[0], "count": row[1]} for row in ws_result.fetchall()
    ]

    # 파일별 핸드 수 (상위 10개)
    file_query = (
        select(
            HandAnalysis.file_name,
            func.count(HandAnalysis.id).label("hand_count"),
            func.max(HandAnalysis.timecode_out_sec).label("max_timecode"),
        )
        .group_by(HandAnalysis.file_name)
        .order_by(desc("hand_count"))
        .limit(10)
    )
    file_result = await db.execute(file_query)
    top_files = [
        {
            "file_name": row[0],
            "hand_count": row[1],
            "max_timecode_sec": row[2] or 0,
        }
        for row in file_result.fetchall()
    ]

    return {
        "total_hands": total_count,
        "by_worksheet": by_worksheet,
        "top_files": top_files,
    }


@router.get("/sync/status", response_model=HandSyncStatusResponse)
async def get_hand_sync_status():
    """핸드 분석 동기화 상태 조회"""
    status = hand_analysis_sync_service.get_status_dict()
    return HandSyncStatusResponse(**status)


@router.post("/sync/trigger", response_model=HandSyncTriggerResponse)
async def trigger_hand_sync():
    """
    핸드 분석 수동 동기화 트리거

    Google Sheets의 8개 워크시트에서 핸드 데이터를 동기화합니다.
    """
    if not hand_analysis_sync_service.is_enabled:
        raise HTTPException(
            status_code=400,
            detail="Hand analysis sync is not enabled. Set HAND_ANALYSIS_SYNC_ENABLED=true",
        )

    result = await hand_analysis_sync_service.sync()

    return HandSyncTriggerResponse(
        success=result.success,
        synced_at=result.synced_at.isoformat(),
        total_records=result.total_records,
        synced_count=result.synced_count,
        created_count=result.created_count,
        updated_count=result.updated_count,
        worksheets_processed=result.worksheets_processed,
        error=result.error,
        message=(
            f"Successfully synced {result.synced_count} hands from {result.worksheets_processed} worksheets"
            if result.success
            else f"Sync failed: {result.error}"
        ),
    )
