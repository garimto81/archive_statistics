"""
Archive Metadata API - 아카이브 메타데이터 조회 및 동기화

Block: api.metadata
Note: Renamed from hands.py (Issue #36)
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.archive_metadata import ArchiveMetadata
from app.services.archive_metadata_sync import archive_metadata_sync_service

router = APIRouter()


# ==================== Schemas ====================

class MetadataResponse(BaseModel):
    """메타데이터 응답"""
    id: int
    file_name: str
    nas_path: Optional[str]
    timecode_in: Optional[str]
    timecode_out: Optional[str]
    timecode_in_sec: float
    timecode_out_sec: float
    file_no: Optional[int]
    hand_grade: Optional[str]  # legacy field name
    winner: Optional[str]
    hands: Optional[str]  # legacy field name
    player_tags: Optional[str]
    poker_play_tags: Optional[str]  # legacy field name
    source_worksheet: Optional[str]

    class Config:
        from_attributes = True


class MetadataListResponse(BaseModel):
    """메타데이터 목록 응답"""
    items: List[MetadataResponse]
    total_count: int
    worksheets: List[str]


class FileMetadataResponse(BaseModel):
    """파일별 메타데이터 응답"""
    file_name: str
    entry_count: int
    max_timecode_sec: float
    max_timecode: str
    entries: List[MetadataResponse]


class MetadataSyncStatusResponse(BaseModel):
    """동기화 상태 응답"""
    enabled: bool
    status: str
    last_sync: Optional[str]
    next_sync: Optional[str]
    error: Optional[str]
    interval_minutes: int
    last_result: Optional[dict]


class MetadataSyncTriggerResponse(BaseModel):
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

@router.get("", response_model=MetadataListResponse)
async def get_metadata(
    worksheet: Optional[str] = Query(None, description="Filter by worksheet name"),
    file_name: Optional[str] = Query(None, description="Filter by file name (partial match)"),
    grade: Optional[str] = Query(None, description="Filter by entry grade"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    아카이브 메타데이터 목록 조회

    - worksheet: 워크시트명 필터
    - file_name: 파일명 부분 검색
    - grade: 등급 필터
    """
    query = select(ArchiveMetadata)

    if worksheet:
        query = query.where(ArchiveMetadata.source_worksheet == worksheet)
    if file_name:
        query = query.where(ArchiveMetadata.file_name.ilike(f"%{file_name}%"))
    if grade:
        query = query.where(ArchiveMetadata.hand_grade == grade)

    # 총 개수
    count_query = select(func.count()).select_from(query.subquery())
    total_count = await db.scalar(count_query)

    # 워크시트 목록
    ws_query = select(ArchiveMetadata.source_worksheet).distinct()
    ws_result = await db.execute(ws_query)
    worksheets = [row[0] for row in ws_result.fetchall() if row[0]]

    # 데이터 조회
    query = query.order_by(
        ArchiveMetadata.source_worksheet,
        ArchiveMetadata.file_name,
        ArchiveMetadata.timecode_in_sec,
    ).offset(offset).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    return MetadataListResponse(
        items=[MetadataResponse.model_validate(item) for item in items],
        total_count=total_count or 0,
        worksheets=worksheets,
    )


@router.get("/by-file/{file_name:path}", response_model=FileMetadataResponse)
async def get_metadata_by_file(
    file_name: str,
    db: AsyncSession = Depends(get_db),
):
    """
    특정 파일의 메타데이터 목록 및 진행률 조회

    - file_name: 파일명
    - 반환: 엔트리 목록, 최대 타임코드, 엔트리 수
    """
    query = select(ArchiveMetadata).where(
        ArchiveMetadata.file_name.ilike(f"%{file_name}%")
    ).order_by(ArchiveMetadata.timecode_out_sec.desc())

    result = await db.execute(query)
    entries = result.scalars().all()

    if not entries:
        raise HTTPException(status_code=404, detail=f"No metadata found for file: {file_name}")

    max_timecode_sec = max(e.timecode_out_sec for e in entries)

    # 초를 HH:MM:SS로 변환
    hours = int(max_timecode_sec // 3600)
    minutes = int((max_timecode_sec % 3600) // 60)
    seconds = int(max_timecode_sec % 60)
    max_timecode = f"{hours}:{minutes:02d}:{seconds:02d}"

    return FileMetadataResponse(
        file_name=entries[0].file_name,
        entry_count=len(entries),
        max_timecode_sec=max_timecode_sec,
        max_timecode=max_timecode,
        entries=[MetadataResponse.model_validate(e) for e in entries],
    )


@router.get("/summary")
async def get_metadata_summary(
    db: AsyncSession = Depends(get_db),
):
    """
    아카이브 메타데이터 요약 통계

    - 총 엔트리 수
    - 워크시트별 엔트리 수
    - 파일별 엔트리 수 (상위 10개)
    """
    # 총 엔트리 수
    total_query = select(func.count(ArchiveMetadata.id))
    total_count = await db.scalar(total_query) or 0

    # 워크시트별 엔트리 수
    ws_query = select(
        ArchiveMetadata.source_worksheet,
        func.count(ArchiveMetadata.id).label('count')
    ).group_by(ArchiveMetadata.source_worksheet)
    ws_result = await db.execute(ws_query)
    by_worksheet = [{"worksheet": row[0], "count": row[1]} for row in ws_result.fetchall()]

    # 파일별 엔트리 수 (상위 10개)
    file_query = select(
        ArchiveMetadata.file_name,
        func.count(ArchiveMetadata.id).label('entry_count'),
        func.max(ArchiveMetadata.timecode_out_sec).label('max_timecode')
    ).group_by(ArchiveMetadata.file_name).order_by(desc('entry_count')).limit(10)
    file_result = await db.execute(file_query)
    top_files = [
        {
            "file_name": row[0],
            "entry_count": row[1],
            "max_timecode_sec": row[2] or 0,
        }
        for row in file_result.fetchall()
    ]

    return {
        "total_entries": total_count,
        "by_worksheet": by_worksheet,
        "top_files": top_files,
    }


@router.get("/sync/status", response_model=MetadataSyncStatusResponse)
async def get_metadata_sync_status():
    """아카이브 메타데이터 동기화 상태 조회"""
    status = archive_metadata_sync_service.get_status_dict()
    return MetadataSyncStatusResponse(**status)


@router.post("/sync/trigger", response_model=MetadataSyncTriggerResponse)
async def trigger_metadata_sync():
    """
    아카이브 메타데이터 수동 동기화 트리거

    Google Sheets의 워크시트에서 메타데이터를 동기화합니다.
    """
    if not archive_metadata_sync_service.is_enabled:
        raise HTTPException(
            status_code=400,
            detail="Archive metadata sync is not enabled. Set ARCHIVE_METADATA_SYNC_ENABLED=true",
        )

    result = await archive_metadata_sync_service.sync()

    return MetadataSyncTriggerResponse(
        success=result.success,
        synced_at=result.synced_at.isoformat(),
        total_records=result.total_records,
        synced_count=result.synced_count,
        created_count=result.created_count,
        updated_count=result.updated_count,
        worksheets_processed=result.worksheets_processed,
        error=result.error,
        message=f"Successfully synced {result.synced_count} entries from {result.worksheets_processed} worksheets"
        if result.success else f"Sync failed: {result.error}",
    )
