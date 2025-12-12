"""
Archive Metadata Model

Google Sheets에서 동기화된 아카이브 메타데이터
타임코드 기반 영상 진행률 추적에 사용

Block: sync.metadata
Note: Renamed from HandAnalysis (Issue #36)
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index
from datetime import datetime
from app.core.database import Base


class ArchiveMetadata(Base):
    """
    아카이브 메타데이터 테이블

    Google Sheets의 각 워크시트(2024 WSOPC LA, WSOPE 2008-2013 등)에서
    동기화된 타임코드 데이터
    """

    # Note: Using legacy table name for backward compatibility
    # A future migration can rename this to "archive_metadata"
    __tablename__ = "hand_analyses"

    id = Column(Integer, primary_key=True, index=True)

    # 파일 정보
    file_name = Column(String, nullable=False, index=True)
    nas_path = Column(String, nullable=True)  # NAS 전체 경로 (매칭용)

    # 타임코드
    timecode_in = Column(String, nullable=True)      # 원본 (HH:MM:SS)
    timecode_out = Column(String, nullable=True)     # 원본 (HH:MM:SS)
    timecode_in_sec = Column(Float, default=0.0)     # 초 변환
    timecode_out_sec = Column(Float, default=0.0)    # 초 변환

    # 엔트리 정보 (컬럼명은 레거시 호환성 유지)
    file_no = Column(Integer, nullable=True)         # 엔트리 순번
    hand_grade = Column(String, nullable=True)       # ★, ★★, ★★★ (legacy: entry_grade)
    winner = Column(String, nullable=True)
    hands = Column(String, nullable=True)            # 설명 (legacy: description)

    # 태그 (JSON string, 컬럼명은 레거시 호환성 유지)
    player_tags = Column(Text, nullable=True)        # ["player1", "player2"]
    poker_play_tags = Column(Text, nullable=True)    # ["tag1", "tag2"] (legacy: action_tags)

    # 출처
    source_worksheet = Column(String, nullable=True)  # "2024 WSOPC LA"
    source_row = Column(Integer, nullable=True)

    # 메타
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 복합 인덱스 (레거시 호환성 유지)
    __table_args__ = (
        Index('idx_hand_file_worksheet', 'file_name', 'source_worksheet'),
        Index('idx_hand_timecode_out', 'timecode_out_sec'),
    )

    def __repr__(self):
        return f"<ArchiveMetadata {self.file_name} [{self.timecode_in}-{self.timecode_out}]>"
