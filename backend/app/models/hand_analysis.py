"""
Hand Analysis Model

Google Sheets (WSOP Circuit LA)에서 동기화된 핸드 분석 데이터
타임코드 기반 영상 진행률 추적에 사용

Block: sync.hands
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index
from datetime import datetime
from app.core.database import Base


class HandAnalysis(Base):
    """
    핸드 분석 테이블

    Google Sheets의 각 워크시트(2024 WSOPC LA, WSOPE 2008-2013 등)에서
    동기화된 핸드 타임코드 데이터
    """

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

    # 핸드 정보
    file_no = Column(Integer, nullable=True)         # 핸드 순번
    hand_grade = Column(String, nullable=True)       # ★, ★★, ★★★
    winner = Column(String, nullable=True)
    hands = Column(String, nullable=True)            # "88 vs JJ"

    # 태그 (JSON string)
    player_tags = Column(Text, nullable=True)        # ["baby shark", "ivey"]
    poker_play_tags = Column(Text, nullable=True)    # ["bluff", "fold"]

    # 출처
    source_worksheet = Column(String, nullable=True)  # "2024 WSOPC LA"
    source_row = Column(Integer, nullable=True)

    # 메타
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 복합 인덱스
    __table_args__ = (
        Index('idx_hand_file_worksheet', 'file_name', 'source_worksheet'),
        Index('idx_hand_timecode_out', 'timecode_out_sec'),
    )

    def __repr__(self):
        return f"<HandAnalysis {self.file_name} [{self.timecode_in}-{self.timecode_out}]>"
