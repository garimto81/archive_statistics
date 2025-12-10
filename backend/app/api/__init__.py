from fastapi import APIRouter
from app.api import stats, folders, work_status, scan, worker_stats, sync, hands, data_sources, progress, folder_mapping

api_router = APIRouter()

api_router.include_router(stats.router, prefix="/stats", tags=["Statistics"])
api_router.include_router(folders.router, prefix="/folders", tags=["Folders"])
api_router.include_router(work_status.router, prefix="/work-status", tags=["Work Status"])
api_router.include_router(worker_stats.router, prefix="/worker-stats", tags=["Worker Stats"])
api_router.include_router(scan.router, prefix="/scan", tags=["Scan"])
api_router.include_router(sync.router, prefix="/sync", tags=["Sync"])
api_router.include_router(hands.router, prefix="/hands", tags=["Hand Analysis"])
api_router.include_router(data_sources.router, prefix="/data-sources", tags=["Data Sources"])
api_router.include_router(progress.router, prefix="/progress", tags=["Progress"])
api_router.include_router(folder_mapping.router, prefix="/folder-mapping", tags=["Folder Mapping"])
