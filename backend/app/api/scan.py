from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.file_stats import ScanHistory
from app.schemas.scan import (
    ScanStatus,
    ScanHistoryResponse,
    ScanStartRequest,
    ScanStartResponse,
)
from app.services.scanner import ArchiveScanner

router = APIRouter()

# Global scan state (shared across all clients)
_scan_state = {
    "is_scanning": False,
    "scan_id": None,
    "progress": 0.0,
    "current_folder": None,
    "files_scanned": 0,
    "total_files_estimated": 0,
    "started_at": None,
    "logs": [],
    "media_files_processed": 0,
    "total_duration_found": 0.0,
}

# Track active viewers (simple heartbeat-based tracking)
_active_viewers = {}  # {client_id: last_seen_timestamp}


@router.get("/status", response_model=ScanStatus)
async def get_scan_status(client_id: Optional[str] = None):
    """Get current scan status (shared across all clients)"""
    # Update viewer tracking
    if client_id:
        _active_viewers[client_id] = datetime.utcnow()

    # Clean up stale viewers (not seen in 30 seconds)
    stale_threshold = datetime.utcnow() - timedelta(seconds=30)
    stale_clients = [k for k, v in _active_viewers.items() if v < stale_threshold]
    for client in stale_clients:
        del _active_viewers[client]

    elapsed = None
    estimated_remaining = None

    if _scan_state["started_at"]:
        elapsed = (datetime.utcnow() - _scan_state["started_at"]).total_seconds()

        # Estimate remaining time based on progress
        if _scan_state["progress"] > 0:
            total_estimated = elapsed / (_scan_state["progress"] / 100)
            estimated_remaining = max(0, total_estimated - elapsed)

    return ScanStatus(
        is_scanning=_scan_state["is_scanning"],
        scan_id=_scan_state["scan_id"],
        progress=_scan_state["progress"],
        current_folder=_scan_state["current_folder"],
        files_scanned=_scan_state["files_scanned"],
        total_files_estimated=_scan_state["total_files_estimated"],
        started_at=_scan_state["started_at"],
        elapsed_seconds=elapsed,
        estimated_remaining_seconds=estimated_remaining,
        logs=_scan_state.get("logs", [])[-20:],  # Last 20 logs
        media_files_processed=_scan_state.get("media_files_processed", 0),
        total_duration_found=_scan_state.get("total_duration_found", 0.0),
        active_viewers=len(_active_viewers),
    )


@router.post("/start", response_model=ScanStartResponse)
async def start_scan(
    request: ScanStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start a new archive scan"""
    if _scan_state["is_scanning"]:
        raise HTTPException(
            status_code=409,
            detail="A scan is already in progress"
        )

    # Create scan history record
    scan_history = ScanHistory(
        scan_type=request.scan_type,
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(scan_history)
    await db.commit()
    await db.refresh(scan_history)

    # Update global state
    _scan_state["is_scanning"] = True
    _scan_state["scan_id"] = scan_history.id
    _scan_state["progress"] = 0.0
    _scan_state["current_folder"] = None
    _scan_state["files_scanned"] = 0
    _scan_state["started_at"] = datetime.utcnow()
    _scan_state["logs"] = [f"[{datetime.utcnow().strftime('%H:%M:%S')}] 🚀 Scan started"]
    _scan_state["media_files_processed"] = 0
    _scan_state["total_duration_found"] = 0.0

    # Start background scan
    background_tasks.add_task(
        run_scan,
        scan_history.id,
        request.path,
    )

    return ScanStartResponse(
        scan_id=scan_history.id,
        message="Scan started",
        status="running",
    )


async def run_scan(scan_id: int, path: Optional[str] = None):
    """Background scan task"""
    from app.core.database import async_session_maker

    async with async_session_maker() as db:
        try:
            scanner = ArchiveScanner(db, _scan_state)
            await scanner.scan(path)

            # Update scan history
            scan_history = await db.get(ScanHistory, scan_id)
            if scan_history:
                scan_history.status = "completed"
                scan_history.completed_at = datetime.utcnow()
                scan_history.total_files = _scan_state["files_scanned"]
                await db.commit()

        except Exception as e:
            # Update scan history with error
            scan_history = await db.get(ScanHistory, scan_id)
            if scan_history:
                scan_history.status = "failed"
                scan_history.completed_at = datetime.utcnow()
                scan_history.error_message = str(e)
                await db.commit()

        finally:
            # Reset global state
            _scan_state["is_scanning"] = False
            _scan_state["scan_id"] = None


@router.post("/stop")
async def stop_scan():
    """Stop current scan"""
    if not _scan_state["is_scanning"]:
        raise HTTPException(
            status_code=400,
            detail="No scan is currently running"
        )

    # Set flag to stop scan (scanner should check this)
    _scan_state["is_scanning"] = False
    return {"message": "Scan stop requested"}


@router.get("/history", response_model=List[ScanHistoryResponse])
async def get_scan_history(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Get scan history"""
    result = await db.execute(
        select(ScanHistory)
        .order_by(ScanHistory.started_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
