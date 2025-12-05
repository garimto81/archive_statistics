from fastapi import APIRouter
from app.api import stats, folders, work_status, scan

api_router = APIRouter()

api_router.include_router(stats.router, prefix="/stats", tags=["Statistics"])
api_router.include_router(folders.router, prefix="/folders", tags=["Folders"])
api_router.include_router(work_status.router, prefix="/work-status", tags=["Work Status"])
api_router.include_router(scan.router, prefix="/scan", tags=["Scan"])
