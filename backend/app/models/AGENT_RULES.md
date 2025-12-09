# Models Block Agent Rules

## Identity
- **Role**: 데이터 모델 및 스키마 전문가
- **Domain**: Scanner (storage), Progress (hand)
- **Scope**: `backend/app/models/` 내부만

## Files in Scope

| File | Block | 책임 |
|------|-------|------|
| `file_stats.py` | scanner.storage | 파일/폴더 통계 모델 |
| `work_status.py` | progress.hand | 작업 상태, 핸드 분석 모델 |

## Core Models

### FileStats (scanner.storage)

```python
class FileStats(Base):
    """파일 통계 모델"""
    __tablename__ = "file_stats"

    id: int                    # PK
    path: str                  # 파일 전체 경로 (UNIQUE)
    name: str                  # 파일명
    folder_path: str           # 폴더 경로
    extension: str             # 확장자
    mime_type: str             # MIME 타입
    size: int                  # 파일 크기 (bytes)
    duration: float            # 재생 시간 (초) - 미디어만
    file_created_at: datetime  # 파일 생성일
    file_modified_at: datetime # 파일 수정일
    created_at: datetime       # 레코드 생성일
    updated_at: datetime       # 레코드 수정일
```

### FolderStats (scanner.storage)

```python
class FolderStats(Base):
    """폴더 통계 모델"""
    __tablename__ = "folder_stats"

    id: int                    # PK
    path: str                  # 폴더 전체 경로 (UNIQUE)
    name: str                  # 폴더명
    parent_path: str           # 상위 폴더 경로
    depth: int                 # 깊이 (루트=0)
    total_size: int            # 총 크기 (bytes)
    file_count: int            # 파일 수
    folder_count: int          # 하위 폴더 수
    total_duration: float      # 총 재생 시간 (초)
    last_scanned_at: datetime  # 마지막 스캔 일시
```

### WorkStatus / HandAnalysis (progress.hand)

```python
class WorkStatus(Base):
    """비디오 작업 상태"""
    __tablename__ = "work_status"

    id: int
    video_file_id: int         # FK -> file_stats.id
    status: str                # COMPLETE, IN_PROGRESS, STARTED, NOT_STARTED
    progress: float            # 진행률 (0.0 ~ 1.0)
    hands_count: int           # 핸드 수
    last_updated: datetime


class HandAnalysis(Base):
    """핸드 분석 결과"""
    __tablename__ = "hand_analysis"

    id: int
    video_file_id: int         # FK -> file_stats.id
    hand_number: int           # 핸드 번호
    timecode_in_sec: float     # 시작 시간 (초)
    timecode_out_sec: float    # 종료 시간 (초)
    player_name: str           # 플레이어명
    notes: str                 # 메모
    created_at: datetime
```

## Constraints

### DO
- SQLAlchemy 2.0 스타일 사용
- 모든 테이블에 created_at, updated_at 포함
- 인덱스 적절히 설정 (path, video_file_id)
- relationship 설정으로 조인 최적화

### DON'T
- 비즈니스 로직 포함 금지 (모델만)
- 직접 쿼리 실행 금지 (services에서 실행)
- 스키마 변경 시 마이그레이션 필수
- `pokervod.db` 스키마 수정 금지 (외부 DB)

## Relationships

```
FileStats (1) ──────▶ (N) FolderStats
    │
    └─────▶ (1) WorkStatus
    │
    └─────▶ (N) HandAnalysis
```

## Index Strategy

```python
# 권장 인덱스
Index("idx_file_stats_path", FileStats.path)
Index("idx_file_stats_folder", FileStats.folder_path)
Index("idx_file_stats_extension", FileStats.extension)
Index("idx_folder_stats_path", FolderStats.path)
Index("idx_folder_stats_parent", FolderStats.parent_path)
Index("idx_hand_analysis_video", HandAnalysis.video_file_id)
```

## Dependencies

### External
- `sqlalchemy`: ORM
- `alembic`: 마이그레이션 (필요 시)

## Testing
- Unit: `tests/test_models.py`
- Fixture: in-memory SQLite
