# Progress Domain Agent Rules

## Identity
- **Role**: 비디오 작업 진행률 관리 전문가
- **Level**: 1 (Domain)
- **Scope**: `backend/app/` 내 진행률 관련 모듈

## Managed Blocks

| Block ID | 파일 | 책임 |
|----------|------|------|
| `progress.video` | `api/work_status.py`, `schemas/work_status.py` | 비디오 파일 관리 |
| `progress.hand` | `models/work_status.py` | 핸드 분석 결과 처리 |
| `progress.dashboard` | `api/stats.py`, `schemas/stats.py` | 대시보드 통계 집계 |

## Core Logic: 90% Completion Criterion

```python
# 핵심 완료 기준
def calculate_status(video_duration: float, hands: List[Hand]) -> str:
    """
    90% 완료 기준:
    MAX(time_end) >= video_duration * 0.9
    """
    if not hands:
        return "NOT_STARTED"

    max_time_end = max(h.timecode_out_sec for h in hands)
    progress = max_time_end / video_duration if video_duration > 0 else 0

    if progress >= 0.9:
        return "COMPLETE"       # 90% 이상
    elif progress >= 0.1:
        return "IN_PROGRESS"    # 10% ~ 90%
    elif progress > 0:
        return "STARTED"        # 0% ~ 10%
    else:
        return "NOT_STARTED"    # 0%
```

## Capabilities

### get_video_progress
- **Description**: 비디오 작업 진행률 조회
- **Input**: `VideoQuery { archive?: str, category?: str }`
- **Output**: `VideoProgress { total: int, complete: int, in_progress: int }`

### calculate_completion
- **Description**: 90% 완료 상태 계산
- **Input**: `VideoFileId`
- **Output**: `CompletionStatus { status: str, progress: float }`

### get_dashboard_stats
- **Description**: 대시보드 통계 집계
- **Input**: `DashboardQuery { group_by?: str }`
- **Output**: `DashboardStats`

## Constraints

### DO
- duration이 0인 비디오는 "NOT_STARTED"로 분류
- 통계 집계 시 캐싱 고려
- 진행률은 소수점 2자리까지

### DON'T
- 완료 기준 90% 값 하드코딩 금지 (설정값 사용)
- scanner-domain 직접 호출 금지
- 원시 SQL 쿼리 사용 자제 (ORM 우선)

## Status Classification

```
Video Status Flow:

NOT_STARTED ──▶ STARTED ──▶ IN_PROGRESS ──▶ COMPLETE
    │              │              │              │
    ▼              ▼              ▼              ▼
  0 hands      progress      10% ≤ p       p ≥ 90%
              0% < p < 10%     < 90%
```

## Dependencies

### Internal
- `scanner.storage`: FileStats 데이터
- `sync.import`: HandAnalysis 데이터

### External
- `sqlalchemy`: DB 접근

## Error Codes

| Code | Description | Recovery |
|------|-------------|----------|
| `VIDEO_NOT_FOUND` | 비디오 파일 없음 | 스캔 재실행 |
| `DURATION_ZERO` | duration 0 | 메타데이터 재추출 |
| `STATS_CALCULATION_FAILED` | 통계 집계 실패 | 캐시 초기화 후 재시도 |

## Testing
- Unit: `tests/test_progress.py`
- Integration: `tests/test_work_status_api.py`
