from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class FolderStats(Base):
    """Folder statistics model"""

    __tablename__ = "folder_stats"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    parent_path = Column(String, index=True, nullable=True)
    depth = Column(Integer, default=0)

    # Statistics
    total_size = Column(BigInteger, default=0)  # bytes
    file_count = Column(Integer, default=0)
    folder_count = Column(Integer, default=0)
    total_duration = Column(Float, default=0.0)  # seconds

    # Work Status 연결 (명시적 FK - fuzzy matching 대체)
    work_status_id = Column(Integer, ForeignKey("work_statuses.id"), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scanned_at = Column(DateTime, nullable=True)

    # Relationships
    work_status = relationship("WorkStatus", back_populates="folders")


class FileStats(Base):
    """File statistics model"""

    __tablename__ = "file_stats"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    folder_path = Column(String, index=True, nullable=False)

    # File info
    extension = Column(String, index=True, nullable=True)
    mime_type = Column(String, nullable=True)
    size = Column(BigInteger, default=0)  # bytes
    duration = Column(Float, nullable=True)  # seconds (for media files)

    # Codec info (extracted via ffprobe)
    video_codec = Column(String, nullable=True)  # e.g., h264, hevc, vp9
    audio_codec = Column(String, nullable=True)  # e.g., aac, mp3, opus

    # Hidden file flag (파일명이 .으로 시작하거나 시스템 파일)
    is_hidden = Column(Boolean, default=False, index=True)

    # Timestamps
    file_created_at = Column(DateTime, nullable=True)
    file_modified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScanHistory(Base):
    """Scan history model"""

    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, index=True)
    scan_type = Column(String, default="manual")  # manual, scheduled
    status = Column(String, default="running")  # running, completed, failed

    # Statistics at scan time
    total_size = Column(BigInteger, default=0)
    total_files = Column(Integer, default=0)
    total_folders = Column(Integer, default=0)
    total_duration = Column(Float, default=0.0)

    # Changes
    new_files = Column(Integer, default=0)
    deleted_files = Column(Integer, default=0)
    size_change = Column(BigInteger, default=0)

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)


class DailySnapshot(Base):
    """Daily snapshot for historical tracking"""

    __tablename__ = "daily_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, unique=True, index=True, nullable=False)

    # Statistics
    total_size = Column(BigInteger, default=0)
    total_files = Column(Integer, default=0)
    total_folders = Column(Integer, default=0)
    total_duration = Column(Float, default=0.0)

    # File type breakdown (JSON stored as string)
    file_type_stats = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
