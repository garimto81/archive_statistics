"""
폴더-작업 연결 관리 API

폴더와 WorkStatus를 명시적으로 연결/해제하는 엔드포인트
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.file_stats import FolderStats
from app.models.work_status import WorkStatus

router = APIRouter()


# ==================== Schemas ====================


class FolderMappingCreate(BaseModel):
    """폴더-작업 연결 요청"""

    folder_path: str
    work_status_id: int


class FolderMappingBulk(BaseModel):
    """대량 연결 요청"""

    mappings: List[FolderMappingCreate]


class FolderMappingResponse(BaseModel):
    """연결 결과"""

    folder_id: int
    folder_path: str
    folder_name: str
    work_status_id: Optional[int]
    work_status_category: Optional[str]


class UnmappedFolderResponse(BaseModel):
    """연결되지 않은 폴더"""

    id: int
    path: str
    name: str
    depth: int
    file_count: int


class WorkStatusOption(BaseModel):
    """작업 선택 옵션"""

    id: int
    category: str
    archive_name: Optional[str]
    total_videos: int
    excel_done: int


# ==================== Endpoints ====================


@router.get("/unmapped", response_model=List[UnmappedFolderResponse])
async def get_unmapped_folders(
    min_depth: int = Query(default=1, ge=0, le=10),
    max_depth: int = Query(default=3, ge=0, le=10),
    min_files: int = Query(default=1, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    WorkStatus에 연결되지 않은 폴더 목록 조회

    폴더-작업 매핑 UI에서 사용
    """
    query = (
        select(FolderStats)
        .where(
            FolderStats.work_status_id.is_(None),
            FolderStats.depth >= min_depth,
            FolderStats.depth <= max_depth,
            FolderStats.file_count >= min_files,
        )
        .order_by(FolderStats.depth, FolderStats.path)
        .limit(limit)
    )

    result = await db.execute(query)
    folders = result.scalars().all()

    return [
        UnmappedFolderResponse(
            id=f.id,
            path=f.path,
            name=f.name,
            depth=f.depth,
            file_count=f.file_count,
        )
        for f in folders
    ]


@router.get("/mapped", response_model=List[FolderMappingResponse])
async def get_mapped_folders(
    work_status_id: Optional[int] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    WorkStatus에 연결된 폴더 목록 조회
    """
    query = (
        select(FolderStats, WorkStatus)
        .outerjoin(WorkStatus, FolderStats.work_status_id == WorkStatus.id)
        .where(FolderStats.work_status_id.isnot(None))
    )

    if work_status_id:
        query = query.where(FolderStats.work_status_id == work_status_id)

    query = query.order_by(FolderStats.path).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    return [
        FolderMappingResponse(
            folder_id=folder.id,
            folder_path=folder.path,
            folder_name=folder.name,
            work_status_id=folder.work_status_id,
            work_status_category=ws.category if ws else None,
        )
        for folder, ws in rows
    ]


@router.get("/work-status-options", response_model=List[WorkStatusOption])
async def get_work_status_options(
    db: AsyncSession = Depends(get_db),
):
    """
    연결 가능한 WorkStatus 목록

    폴더 매핑 드롭다운에서 사용
    """
    from app.models.work_status import Archive

    query = (
        select(WorkStatus, Archive.name)
        .outerjoin(Archive, WorkStatus.archive_id == Archive.id)
        .order_by(Archive.name, WorkStatus.category)
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        WorkStatusOption(
            id=ws.id,
            category=ws.category,
            archive_name=archive_name,
            total_videos=ws.total_videos,
            excel_done=ws.excel_done,
        )
        for ws, archive_name in rows
    ]


@router.post("/connect", response_model=FolderMappingResponse)
async def connect_folder_to_work_status(
    mapping: FolderMappingCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    폴더를 WorkStatus에 연결
    """
    # 폴더 확인
    folder_result = await db.execute(
        select(FolderStats).where(FolderStats.path == mapping.folder_path)
    )
    folder = folder_result.scalar_one_or_none()

    if not folder:
        raise HTTPException(
            status_code=404, detail=f"폴더를 찾을 수 없습니다: {mapping.folder_path}"
        )

    # WorkStatus 확인
    ws_result = await db.execute(
        select(WorkStatus).where(WorkStatus.id == mapping.work_status_id)
    )
    ws = ws_result.scalar_one_or_none()

    if not ws:
        raise HTTPException(
            status_code=404,
            detail=f"WorkStatus를 찾을 수 없습니다: {mapping.work_status_id}",
        )

    # 연결
    folder.work_status_id = mapping.work_status_id
    await db.commit()
    await db.refresh(folder)

    return FolderMappingResponse(
        folder_id=folder.id,
        folder_path=folder.path,
        folder_name=folder.name,
        work_status_id=folder.work_status_id,
        work_status_category=ws.category,
    )


@router.post("/connect-bulk")
async def connect_folders_bulk(
    bulk: FolderMappingBulk,
    db: AsyncSession = Depends(get_db),
):
    """
    여러 폴더를 한 번에 연결
    """
    success_count = 0
    errors = []

    for mapping in bulk.mappings:
        try:
            folder_result = await db.execute(
                select(FolderStats).where(FolderStats.path == mapping.folder_path)
            )
            folder = folder_result.scalar_one_or_none()

            if folder:
                folder.work_status_id = mapping.work_status_id
                success_count += 1
            else:
                errors.append(f"폴더 없음: {mapping.folder_path}")
        except Exception as e:
            errors.append(f"{mapping.folder_path}: {str(e)}")

    await db.commit()

    return {
        "success_count": success_count,
        "error_count": len(errors),
        "errors": errors[:10],  # 최대 10개만 반환
    }


@router.delete("/disconnect/{folder_id}")
async def disconnect_folder(
    folder_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    폴더와 WorkStatus 연결 해제
    """
    folder_result = await db.execute(
        select(FolderStats).where(FolderStats.id == folder_id)
    )
    folder = folder_result.scalar_one_or_none()

    if not folder:
        raise HTTPException(
            status_code=404, detail=f"폴더를 찾을 수 없습니다: {folder_id}"
        )

    folder.work_status_id = None
    await db.commit()

    return {"message": "연결 해제됨", "folder_id": folder_id}


@router.post("/auto-match")
async def auto_match_folders(
    dry_run: bool = Query(default=True, description="True면 실제 변경 없이 미리보기만"),
    db: AsyncSession = Depends(get_db),
):
    """
    기존 fuzzy matching 로직으로 자동 매칭 수행

    dry_run=True: 매칭 결과만 반환 (실제 DB 변경 없음)
    dry_run=False: 실제 DB에 work_status_id 업데이트
    """
    from app.services.progress_service import ProgressService

    service = ProgressService()

    # WorkStatus 로드
    ws_result = await db.execute(select(WorkStatus))
    work_statuses = {}
    for ws in ws_result.scalars().all():
        work_statuses[ws.category] = {
            "id": ws.id,
            "category": ws.category,
            "total_videos": ws.total_videos,
            "excel_done": ws.excel_done,
        }

    # 연결되지 않은 폴더 조회
    folder_result = await db.execute(
        select(FolderStats)
        .where(FolderStats.work_status_id.is_(None))
        .order_by(FolderStats.depth)
    )
    folders = folder_result.scalars().all()

    matches = []
    for folder in folders:
        matched = service._match_work_statuses(folder.name, folder.path, work_statuses)
        if matched:
            # 가장 좋은 매칭만 사용
            best_match = matched[0]
            matches.append(
                {
                    "folder_id": folder.id,
                    "folder_path": folder.path,
                    "folder_name": folder.name,
                    "work_status_id": best_match["id"],
                    "work_status_category": best_match["category"],
                }
            )

            if not dry_run:
                folder.work_status_id = best_match["id"]

    if not dry_run:
        await db.commit()

    return {
        "dry_run": dry_run,
        "total_unmatched": len(folders),
        "matched_count": len(matches),
        "matches": matches[:50],  # 최대 50개만 반환
    }
