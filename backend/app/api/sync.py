"""
Sync API - Google Sheets 동기화 상태 및 트리거

Block: sync.sheets
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from app.services.sheets_sync import sheets_sync_service
from app.core.config import settings

router = APIRouter()


class SyncStatusResponse(BaseModel):
    """동기화 상태 응답"""
    enabled: bool
    status: str
    last_sync: Optional[str]
    next_sync: Optional[str]
    error: Optional[str]
    interval_minutes: int
    last_result: Optional[Dict[str, Any]] = None


class SyncTriggerResponse(BaseModel):
    """동기화 트리거 응답"""
    success: bool
    synced_at: str
    total_records: int
    synced_count: int
    created_count: int
    updated_count: int
    error: Optional[str] = None
    message: str


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status():
    """
    동기화 상태 조회

    Returns:
        - enabled: 동기화 활성화 여부
        - status: 현재 상태 (idle, syncing, error)
        - last_sync: 마지막 동기화 시간
        - next_sync: 다음 예정 동기화 시간
        - error: 마지막 에러 메시지
        - interval_minutes: 동기화 간격 (분)
        - last_result: 마지막 동기화 결과 상세
    """
    status_dict = sheets_sync_service.get_status_dict()

    return SyncStatusResponse(
        enabled=status_dict["enabled"],
        status=status_dict["status"],
        last_sync=status_dict["last_sync"],
        next_sync=status_dict["next_sync"],
        error=status_dict["error"],
        interval_minutes=status_dict["interval_minutes"],
        last_result=status_dict["last_result"],
    )


@router.post("/trigger", response_model=SyncTriggerResponse)
async def trigger_sync():
    """
    수동으로 동기화 트리거

    Google Sheets에서 데이터를 즉시 가져와 DB에 동기화합니다.

    Returns:
        - success: 성공 여부
        - synced_at: 동기화 시간
        - total_records: 시트의 총 레코드 수
        - synced_count: 동기화된 레코드 수
        - created_count: 신규 생성된 레코드 수
        - updated_count: 업데이트된 레코드 수
        - error: 에러 메시지 (실패 시)
        - message: 결과 메시지
    """
    if not sheets_sync_service.is_enabled:
        raise HTTPException(
            status_code=400,
            detail="Sheets sync is not enabled. Check SHEETS_SYNC_ENABLED and WORK_STATUS_SHEET_URL settings.",
        )

    if sheets_sync_service.status == "syncing":
        raise HTTPException(
            status_code=409,
            detail="Sync is already in progress. Please wait.",
        )

    result = await sheets_sync_service.sync()

    if result.success:
        message = (
            f"Successfully synced {result.synced_count} records "
            f"({result.created_count} created, {result.updated_count} updated)"
        )
    else:
        message = f"Sync failed: {result.error}"

    return SyncTriggerResponse(
        success=result.success,
        synced_at=result.synced_at.isoformat(),
        total_records=result.total_records,
        synced_count=result.synced_count,
        created_count=result.created_count,
        updated_count=result.updated_count,
        error=result.error,
        message=message,
    )


@router.get("/config")
async def get_sync_config():
    """
    동기화 설정 조회 (디버깅용)

    Returns:
        - sheet_url: 연동된 Google Sheet URL
        - interval_minutes: 동기화 간격
        - service_account_email: Service Account 이메일 (마스킹)
    """
    # Service Account 이메일 마스킹
    sa_email = None
    try:
        from pathlib import Path
        import json
        sa_path = Path(settings.GOOGLE_SERVICE_ACCOUNT_FILE)
        if not sa_path.exists():
            sa_path = Path("backend") / settings.GOOGLE_SERVICE_ACCOUNT_FILE
        if sa_path.exists():
            with open(sa_path) as f:
                sa_data = json.load(f)
                email = sa_data.get("client_email", "")
                # 이메일 앞 10자만 표시
                if len(email) > 15:
                    sa_email = email[:10] + "***@***"
                else:
                    sa_email = "***"
    except Exception:
        sa_email = "Error reading"

    return {
        "sheet_url": settings.WORK_STATUS_SHEET_URL if settings.SHEETS_SYNC_ENABLED else None,
        "interval_minutes": settings.SHEETS_SYNC_INTERVAL_MINUTES,
        "service_account_email": sa_email,
        "enabled": settings.SHEETS_SYNC_ENABLED,
    }
