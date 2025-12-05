from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Archive(Base):
    """Archive category model (WSOP, HCL, etc.)"""

    __tablename__ = "archives"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # WSOP, HCL
    description = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    work_statuses = relationship("WorkStatus", back_populates="archive")


class WorkStatus(Base):
    """Work status tracking model"""

    __tablename__ = "work_statuses"

    id = Column(Integer, primary_key=True, index=True)
    archive_id = Column(Integer, ForeignKey("archives.id"), nullable=False)
    category = Column(String, nullable=False)  # WSOP Paradise, Clip 2023

    # Assignment
    pic = Column(String, nullable=True)  # Person In Charge (담당자)
    status = Column(String, default="pending")  # pending, in_progress, review, completed

    # Progress
    total_videos = Column(Integer, default=0)
    excel_done = Column(Integer, default=0)
    progress_percent = Column(Float, default=0.0)

    # Notes
    notes1 = Column(Text, nullable=True)
    notes2 = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    archive = relationship("Archive", back_populates="work_statuses")

    def calculate_progress(self):
        """Calculate progress percentage"""
        if self.total_videos > 0:
            self.progress_percent = (self.excel_done / self.total_videos) * 100
        else:
            self.progress_percent = 0.0
        return self.progress_percent
