import csv
import io
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.work_status import Archive, WorkStatus
from app.schemas.work_status import (
    ArchiveCreate,
    ArchiveResponse,
    WorkStatusCreate,
    WorkStatusImportResult,
    WorkStatusListResponse,
    WorkStatusResponse,
    WorkStatusUpdate,
)

router = APIRouter()


# ===== Archive Endpoints =====


@router.get("/archives", response_model=List[ArchiveResponse])
async def get_archives(db: AsyncSession = Depends(get_db)):
    """Get all archives"""
    result = await db.execute(select(Archive).order_by(Archive.name))
    return result.scalars().all()


@router.post("/archives", response_model=ArchiveResponse)
async def create_archive(
    archive: ArchiveCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new archive"""
    db_archive = Archive(**archive.model_dump())
    db.add(db_archive)
    await db.commit()
    await db.refresh(db_archive)
    return db_archive


# ===== Work Status Endpoints =====


@router.get("", response_model=WorkStatusListResponse)
async def get_work_statuses(
    archive_id: Optional[int] = None,
    status: Optional[str] = None,
    pic: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get all work statuses with optional filters"""

    query = select(WorkStatus, Archive.name.label("archive_name")).join(Archive)

    if archive_id:
        query = query.where(WorkStatus.archive_id == archive_id)
    if status:
        query = query.where(WorkStatus.status == status)
    if pic:
        query = query.where(WorkStatus.pic.contains(pic))

    result = await db.execute(query.order_by(Archive.name, WorkStatus.category))
    rows = result.all()

    items = []
    total_videos = 0
    total_done = 0

    for row in rows:
        ws = row[0]
        archive_name = row[1]
        ws.calculate_progress()

        items.append(
            WorkStatusResponse(
                id=ws.id,
                archive_id=ws.archive_id,
                archive_name=archive_name,
                category=ws.category,
                pic=ws.pic,
                status=ws.status,
                total_videos=ws.total_videos,
                excel_done=ws.excel_done,
                progress_percent=ws.progress_percent,
                notes1=ws.notes1,
                notes2=ws.notes2,
                created_at=ws.created_at,
                updated_at=ws.updated_at,
            )
        )
        total_videos += ws.total_videos
        total_done += ws.excel_done

    overall_progress = (total_done / total_videos * 100) if total_videos > 0 else 0

    return WorkStatusListResponse(
        items=items,
        total_count=len(items),
        total_videos=total_videos,
        total_done=total_done,
        overall_progress=overall_progress,
    )


@router.get("/{work_status_id}", response_model=WorkStatusResponse)
async def get_work_status(
    work_status_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific work status"""
    result = await db.execute(
        select(WorkStatus, Archive.name.label("archive_name"))
        .join(Archive)
        .where(WorkStatus.id == work_status_id)
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Work status not found")

    ws = row[0]
    ws.calculate_progress()

    return WorkStatusResponse(
        id=ws.id,
        archive_id=ws.archive_id,
        archive_name=row[1],
        category=ws.category,
        pic=ws.pic,
        status=ws.status,
        total_videos=ws.total_videos,
        excel_done=ws.excel_done,
        progress_percent=ws.progress_percent,
        notes1=ws.notes1,
        notes2=ws.notes2,
        created_at=ws.created_at,
        updated_at=ws.updated_at,
    )


@router.post("", response_model=WorkStatusResponse)
async def create_work_status(
    work_status: WorkStatusCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new work status"""
    db_ws = WorkStatus(**work_status.model_dump())
    db_ws.calculate_progress()
    db.add(db_ws)
    await db.commit()
    await db.refresh(db_ws)

    # Get archive name
    archive = await db.get(Archive, db_ws.archive_id)

    return WorkStatusResponse(
        id=db_ws.id,
        archive_id=db_ws.archive_id,
        archive_name=archive.name if archive else None,
        category=db_ws.category,
        pic=db_ws.pic,
        status=db_ws.status,
        total_videos=db_ws.total_videos,
        excel_done=db_ws.excel_done,
        progress_percent=db_ws.progress_percent,
        notes1=db_ws.notes1,
        notes2=db_ws.notes2,
        created_at=db_ws.created_at,
        updated_at=db_ws.updated_at,
    )


@router.put("/{work_status_id}", response_model=WorkStatusResponse)
async def update_work_status(
    work_status_id: int,
    work_status: WorkStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a work status"""
    db_ws = await db.get(WorkStatus, work_status_id)
    if not db_ws:
        raise HTTPException(status_code=404, detail="Work status not found")

    update_data = work_status.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ws, field, value)

    db_ws.calculate_progress()
    await db.commit()
    await db.refresh(db_ws)

    archive = await db.get(Archive, db_ws.archive_id)

    return WorkStatusResponse(
        id=db_ws.id,
        archive_id=db_ws.archive_id,
        archive_name=archive.name if archive else None,
        category=db_ws.category,
        pic=db_ws.pic,
        status=db_ws.status,
        total_videos=db_ws.total_videos,
        excel_done=db_ws.excel_done,
        progress_percent=db_ws.progress_percent,
        notes1=db_ws.notes1,
        notes2=db_ws.notes2,
        created_at=db_ws.created_at,
        updated_at=db_ws.updated_at,
    )


@router.delete("/{work_status_id}")
async def delete_work_status(
    work_status_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a work status"""
    db_ws = await db.get(WorkStatus, work_status_id)
    if not db_ws:
        raise HTTPException(status_code=404, detail="Work status not found")

    await db.delete(db_ws)
    await db.commit()
    return {"message": "Work status deleted successfully"}


# ===== Import/Export =====


@router.post("/import", response_model=WorkStatusImportResult)
async def import_csv(
    file: UploadFile = File(...),
    replace: bool = Query(default=False, description="Replace existing data"),
    db: AsyncSession = Depends(get_db),
):
    """Import work statuses from CSV"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    text = content.decode("utf-8-sig")  # Handle BOM
    reader = csv.DictReader(io.StringIO(text))

    if replace:
        # Delete all existing work statuses
        await db.execute(WorkStatus.__table__.delete())

    imported = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
        try:
            archive_name = row.get("Archive", "").strip()
            if not archive_name:
                skipped += 1
                continue

            # Find or create archive
            result = await db.execute(
                select(Archive).where(Archive.name == archive_name)
            )
            archive = result.scalar_one_or_none()
            if not archive:
                archive = Archive(name=archive_name)
                db.add(archive)
                await db.flush()

            # Parse values
            total_videos = 0
            try:
                total_str = row.get("Total\n(# of videos)", row.get("Total", "0"))
                total_videos = int(total_str) if total_str else 0
            except ValueError:
                pass

            excel_done = 0
            try:
                done_str = row.get(
                    "Excel Done\n(# of videos)", row.get("Excel Done", "0")
                )
                excel_done = int(done_str) if done_str else 0
            except ValueError:
                pass

            ws = WorkStatus(
                archive_id=archive.id,
                category=row.get("Category", "").strip(),
                pic=row.get("PIC", "").strip() or None,
                status=row.get("Status", "pending").strip() or "pending",
                total_videos=total_videos,
                excel_done=excel_done,
                notes1=row.get("Notes 1", "").strip() or None,
                notes2=row.get("Notes 2", "").strip() or None,
            )
            ws.calculate_progress()
            db.add(ws)
            imported += 1

        except Exception as e:
            errors.append(f"Row {i}: {str(e)}")
            skipped += 1

    await db.commit()

    return WorkStatusImportResult(
        success=len(errors) == 0,
        total_rows=imported + skipped,
        imported_rows=imported,
        skipped_rows=skipped,
        errors=errors,
    )


@router.get("/export/csv")
async def export_csv(db: AsyncSession = Depends(get_db)):
    """Export work statuses to CSV"""
    result = await db.execute(
        select(WorkStatus, Archive.name.label("archive_name"))
        .join(Archive)
        .order_by(Archive.name, WorkStatus.category)
    )
    rows = result.all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "Archive",
            "Category",
            "PIC",
            "Status",
            "Total (# of videos)",
            "Excel Done (# of videos)",
            "Progress %",
            "Notes 1",
            "Notes 2",
        ]
    )

    # Data
    for row in rows:
        ws = row[0]
        ws.calculate_progress()
        writer.writerow(
            [
                row[1],  # archive_name
                ws.category,
                ws.pic or "",
                ws.status,
                ws.total_videos,
                ws.excel_done,
                f"{ws.progress_percent:.2f}%",
                ws.notes1 or "",
                ws.notes2 or "",
            ]
        )

    output.seek(0)
    filename = f"work_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
