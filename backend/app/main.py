"""Archive Statistics Dashboard - FastAPI Application"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.database import create_tables
from app.services.hand_analysis_sync import hand_analysis_sync_service
from app.services.sheets_sync import sheets_sync_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    await create_tables()
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started")

    # Start Google Sheets sync service (Work Status)
    if settings.SHEETS_SYNC_ENABLED:
        print("📊 Starting Google Sheets sync service...")
        await sheets_sync_service.start()

    # Start Hand Analysis sync service
    if settings.HAND_ANALYSIS_SYNC_ENABLED:
        print("🃏 Starting Hand Analysis sync service...")
        await hand_analysis_sync_service.start()

    yield

    # Shutdown
    if settings.SHEETS_SYNC_ENABLED:
        await sheets_sync_service.stop()
        print("📊 Google Sheets sync service stopped")
    if settings.HAND_ANALYSIS_SYNC_ENABLED:
        await hand_analysis_sync_service.stop()
        print("🃏 Hand Analysis sync service stopped")
    print("👋 Application shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Archive Statistics Dashboard API",
    lifespan=lifespan,
)

# CORS - Allow LAN access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.CORS_ALLOW_ALL else settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
