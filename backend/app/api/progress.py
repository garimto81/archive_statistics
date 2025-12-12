"""
Progress API - 폴더/파일별 통합 진행률 조회

Folder Tree와 Work Progress를 통합한 간트차트 형태 데이터 제공.
metadata db(핸드 분석)와 archive db(작업 현황)를 NAS 폴더 구조와 매칭.

Block: api.progress
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.services.progress_service import progress_service

router = APIRouter()


# ==================== Schemas ====================

class WorkStatusInfo(BaseModel):
    """Work Status 정보 (archive db) - 구글 시트 원본 행 전체"""
    id: int
    category: str
    pic: Optional[str]
    status: str
    total_videos: int
    excel_done: int
    progress_percent: float
    notes1: Optional[str] = None
    notes2: Optional[str] = None


class WorkStatusSummary(BaseModel):
    """Work Status 요약 (상위 폴더용)

    여러 work_status를 합산한 요약 정보.
    트리 뷰에서 상위 폴더에 표시할 때 사용.

    주의:
    - total_files는 NAS 스캔 결과 (진행률 계산 기준)
    - sheets_total_videos는 구글 시트 원본 값 (검증용)
    - 90% 이상 진행률은 100%로 표시
    """
    task_count: int = 0           # 매칭된 작업 수
    total_files: int = 0          # NAS 파일 수 (스캔 결과, 진행률 계산 기준)
    total_done: int = 0           # 완료 파일 수 (excel_done 합산)
    combined_progress: float = 0  # 전체 진행률 (90% 이상은 100%)
    # 구글 시트 원본 값 (검증용)
    sheets_total_videos: int = 0  # 구글 시트 total_videos 합계
    sheets_excel_done: int = 0    # 구글 시트 excel_done 합계


class HandAnalysisInfo(BaseModel):
    """Hand Analysis 정보 (파일 기반 집계) - 상세 패널용"""
    total_files: int = 0  # 전체 파일 수 (하위 폴더 포함)
    files_matched: int = 0  # 매칭된 파일 수
    match_rate: float = 0.0  # 매칭 비율 (%)
    hand_count: int = 0
    max_timecode_sec: float = 0
    max_timecode_formatted: str = "00:00:00"
    avg_progress: float = 0
    completed_files: int = 0


class MetadataProgress(BaseModel):
    """파일별 metadata 진행률"""
    hand_count: int
    max_timecode_sec: float
    max_timecode_formatted: str
    progress_percent: float
    is_complete: bool


class FolderCodecSummary(BaseModel):
    """폴더별 코덱 요약 통계"""
    total_files: int = 0
    files_with_codec: int = 0
    video_codecs: dict = {}  # {"h264": 10, "hevc": 5}
    audio_codecs: dict = {}  # {"aac": 12, "ac3": 3}
    top_video_codec: Optional[str] = None
    top_audio_codec: Optional[str] = None


class FileWithProgress(BaseModel):
    """파일 + 진행률"""
    id: int
    name: str
    path: str
    size: int
    size_formatted: str
    duration: float
    duration_formatted: str
    extension: Optional[str]
    metadata_progress: Optional[MetadataProgress] = None
    # 코덱 정보
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None


class FolderRootStats(BaseModel):
    """폴더의 루트 전체 대비 비율 (Issue #29)"""
    total_files: int = 0
    total_size: int = 0
    total_size_formatted: str = "0 B"
    file_ratio: float = 0.0  # 현재 폴더 파일 수 / 전체 파일 수 * 100
    size_ratio: float = 0.0  # 현재 폴더 용량 / 전체 용량 * 100


class FolderWithProgress(BaseModel):
    """폴더 + 진행률 (재귀 구조)"""
    id: int
    name: str
    path: str
    size: int
    size_formatted: str
    file_count: int
    folder_count: int
    duration: float
    duration_formatted: str
    depth: int

    # 작업 현황 (work_status)
    work_summary: Optional[WorkStatusSummary] = None  # 트리 뷰용 요약
    work_statuses: Optional[List[WorkStatusInfo]] = None  # 상세 패널용 목록

    # 분석 현황 (hand_analysis) - 상세 패널에서만 사용
    hand_analysis: Optional[HandAnalysisInfo] = None

    # 코덱 정보 (Codec Explorer용)
    codec_summary: Optional[FolderCodecSummary] = None

    # Issue #29: 루트 전체 대비 비율 (NAS/Sheets 데이터 분리 표시용)
    root_stats: Optional[FolderRootStats] = None

    # 하위 호환성
    work_status: Optional[WorkStatusInfo] = None  # deprecated

    children: List["FolderWithProgress"] = []
    files: Optional[List[FileWithProgress]] = None

    class Config:
        from_attributes = True


class RootStats(BaseModel):
    """전체 아카이브 통계 (Issue #29)"""
    total_files: int = 0
    total_size: int = 0
    total_size_formatted: str = "0 B"
    total_duration: float = 0
    total_duration_formatted: str = "00:00:00"
    sheets_total_videos: int = 0
    sheets_total_done: int = 0


class TreeWithRootStats(BaseModel):
    """폴더 트리 + 루트 통계 (Issue #29)"""
    tree: List[FolderWithProgress] = []
    root_stats: RootStats


# Forward reference 해결
FolderWithProgress.model_rebuild()


# ==================== Endpoints ====================

@router.get("/tree", response_model=TreeWithRootStats)
async def get_folder_tree_with_progress(
    path: Optional[str] = Query(None, description="시작 경로 (None=루트)"),
    depth: int = Query(2, ge=1, le=10, description="탐색 깊이 (1-10)"),
    include_files: bool = Query(False, description="파일 목록 포함"),
    include_codecs: bool = Query(False, description="코덱 정보 포함 (Codec Explorer용)"),
    extensions: Optional[str] = Query(None, description="쉼표로 구분된 확장자 필터 (예: mp4,mkv)"),
    db: AsyncSession = Depends(get_db),
):
    """
    폴더 트리 + 진행률 통합 조회 (간트차트용)

    - 각 폴더에 Work Status (archive db) 매칭
    - 각 폴더에 Hand Analysis (metadata db) 집계
    - include_files=true 시 파일별 진행률 포함
    - include_codecs=true 시 폴더/파일별 코덱 정보 포함
    - extensions 필터로 특정 확장자만 포함
    - Issue #29: root_stats로 전체 통계 반환 (NAS/Sheets 데이터 분리 표시용)

    Returns:
        {tree: 폴더 트리, root_stats: 전체 통계}
    """
    # Parse extensions filter
    ext_list = None
    if extensions:
        ext_list = [f".{e.strip().lower().lstrip('.')}" for e in extensions.split(",")]

    result = await progress_service.get_folder_with_progress(
        db, path, depth, include_files, ext_list, include_codecs
    )
    return result


@router.get("/folder/{folder_path:path}")
async def get_folder_progress_detail(
    folder_path: str,
    include_files: bool = Query(True, description="파일 목록 포함"),
    db: AsyncSession = Depends(get_db),
):
    """
    특정 폴더의 상세 진행률

    Args:
        folder_path: 폴더 경로
        include_files: 파일 목록 포함 여부
    """
    result = await progress_service.get_folder_detail(
        db, folder_path, include_files=include_files
    )

    if not result:
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder_path}")

    return result


@router.get("/file/{file_path:path}")
async def get_file_progress_detail(
    file_path: str,
    db: AsyncSession = Depends(get_db),
):
    """
    특정 파일의 상세 진행률

    - 해당 파일의 모든 핸드 분석 데이터
    - 타임코드별 진행 상태

    Args:
        file_path: 파일 경로
    """
    result = await progress_service.get_file_progress_detail(db, file_path)

    if not result:
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    return result


@router.get("/summary")
async def get_progress_summary(
    path: Optional[str] = Query(None, description="폴더 경로 필터 (None=전체)"),
    extensions: Optional[str] = Query(None, description="쉼표로 구분된 확장자 필터 (예: mp4,mkv)"),
    db: AsyncSession = Depends(get_db),
):
    """
    전체 진행률 요약 (폴더 필터 지원)

    - 전체 폴더/파일 수
    - Work Status 요약 (archive db)
    - Hand Analysis 요약 (metadata db)
    - 매칭률 통계
    - path 필터로 특정 폴더 하위만 집계
    - extensions 필터로 특정 확장자만 집계
    """
    from sqlalchemy import func
    from app.models.file_stats import FolderStats, FileStats
    from app.models.hand_analysis import HandAnalysis
    from app.models.work_status import WorkStatus

    # Parse extensions filter
    ext_list = None
    if extensions:
        ext_list = [f".{e.strip().lower().lstrip('.')}" for e in extensions.split(",")]

    # 폴더 경로 필터 조건
    path_filter = path + "%" if path else None

    # 폴더 통계 (경로 필터 적용)
    folder_query = select(func.count(FolderStats.id))
    if path_filter:
        folder_query = folder_query.where(FolderStats.path.like(path_filter))
    folder_count = await db.scalar(folder_query) or 0

    # 파일 수 (경로 및 확장자 필터 적용)
    file_query = select(func.count(FileStats.id))
    if path_filter:
        file_query = file_query.where(FileStats.folder_path.like(path_filter))
    if ext_list:
        file_query = file_query.where(FileStats.extension.in_(ext_list))
    file_count = await db.scalar(file_query) or 0

    # Work Status 통계 (경로 필터 - 카테고리 매칭 기반)
    # 폴더 경로가 있으면 해당 폴더와 매칭되는 Work Status만 카운트
    if path_filter:
        # 폴더명 추출 (경로의 마지막 부분)
        folder_name = path.split("/")[-1] if path else None
        if folder_name:
            # 카테고리에 폴더명이 포함된 Work Status 검색
            ws_query = select(func.count(WorkStatus.id)).where(
                WorkStatus.category.ilike(f"%{folder_name}%")
            )
            ws_total = await db.scalar(ws_query) or 0
            ws_completed = await db.scalar(
                select(func.count(WorkStatus.id)).where(
                    WorkStatus.category.ilike(f"%{folder_name}%"),
                    WorkStatus.status == "completed"
                )
            ) or 0
        else:
            ws_total = 0
            ws_completed = 0
    else:
        ws_total = await db.scalar(select(func.count(WorkStatus.id))) or 0
        ws_completed = await db.scalar(
            select(func.count(WorkStatus.id)).where(WorkStatus.status == "completed")
        ) or 0

    # Hand Analysis 통계 (파일명 기반 필터링)
    if path_filter:
        # 해당 경로의 파일명 목록 조회
        file_names_query = select(FileStats.name).where(FileStats.folder_path.like(path_filter))
        file_names_result = await db.execute(file_names_query)
        file_names = [r[0] for r in file_names_result.fetchall()]

        if file_names:
            hand_total = await db.scalar(
                select(func.count(HandAnalysis.id)).where(HandAnalysis.file_name.in_(file_names))
            ) or 0
            worksheet_count = await db.scalar(
                select(func.count(func.distinct(HandAnalysis.source_worksheet))).where(
                    HandAnalysis.file_name.in_(file_names)
                )
            ) or 0
            matched_files = await db.scalar(
                select(func.count(func.distinct(HandAnalysis.file_name))).where(
                    HandAnalysis.file_name.in_(file_names)
                )
            ) or 0
        else:
            hand_total = 0
            worksheet_count = 0
            matched_files = 0
    else:
        hand_total = await db.scalar(select(func.count(HandAnalysis.id))) or 0
        worksheet_count = await db.scalar(
            select(func.count(func.distinct(HandAnalysis.source_worksheet)))
        ) or 0
        matched_files = await db.scalar(
            select(func.count(func.distinct(HandAnalysis.file_name)))
        ) or 0

    return {
        "nas": {
            "total_folders": folder_count,
            "total_files": file_count,
        },
        "archive_db": {
            "total_tasks": ws_total,
            "completed": ws_completed,
            "in_progress": ws_total - ws_completed,
        },
        "metadata_db": {
            "total_hands": hand_total,
            "worksheets": worksheet_count,
            "matched_files": matched_files,
        },
        "matching": {
            "files_with_hands": matched_files,
            "match_rate": round((matched_files / file_count * 100), 1) if file_count > 0 else 0,
        },
        "filter": {
            "path": path,
            "extensions": ext_list,
        }
    }


# SQL select import
from sqlalchemy import select
