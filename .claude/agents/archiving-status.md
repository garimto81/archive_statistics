# Archiving Status Agent

아카이빙 작업 현황 관리 전담 에이전트

## Block: archiving.status

### Responsibilities

1. **Work Status UI** - 작업 현황 페이지 구현 및 유지보수
2. **Worker Stats** - 작업자별 통계 집계 및 표시
3. **Dashboard Integration** - 대시보드에 작업 현황 요약 카드 제공
4. **Google Sheets Sync** - 동기화 상태 관리 및 트리거

---

## Domain Files

### Backend

```
backend/app/
├── api/
│   ├── archiving_status.py    # /api/archiving-status 엔드포인트
│   └── worker_stats.py        # /api/worker-stats 엔드포인트
├── services/
│   └── archiving_status_sync.py  # Google Sheets 동기화
├── models/
│   ├── archiving_status.py    # ArchivingStatus alias
│   └── work_status.py         # WorkStatus 기본 모델
└── schemas/
    └── work_status.py         # Pydantic 스키마
```

### Frontend

```
frontend/src/
├── pages/
│   └── WorkStatus.tsx         # 작업 현황 페이지
├── components/
│   ├── WorkerCard.tsx         # 작업자 카드
│   ├── WorkerDetailModal.tsx  # 작업자 상세 모달
│   ├── WorkStatusSummary.tsx  # 대시보드용 요약 카드
│   ├── TopWorkers.tsx         # 상위 작업자 랭킹
│   └── SyncStatusIndicator.tsx # 동기화 상태 표시
├── services/
│   └── api.ts                 # archivingStatusApi, workerStatsApi
└── types/
    └── archiving.ts           # Archiving 관련 타입
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/archiving-status` | 작업 목록 (필터: archive_id, status, pic) |
| GET | `/api/archiving-status/{id}` | 개별 작업 조회 |
| POST | `/api/archiving-status` | 작업 생성 |
| PUT | `/api/archiving-status/{id}` | 작업 수정 |
| DELETE | `/api/archiving-status/{id}` | 작업 삭제 |
| GET | `/api/worker-stats` | 전체 작업자 통계 |
| GET | `/api/worker-stats/{pic}` | 특정 작업자 상세 |
| GET | `/api/sync/status` | 동기화 상태 |
| POST | `/api/sync/trigger` | 수동 동기화 |

---

## Data Models

### ArchivingStatus (WorkStatus)

```python
class ArchivingStatus:
    id: int
    archive_id: int           # Archive FK
    category: str             # 작업 카테고리명
    pic: str | None           # Person In Charge (담당자)
    status: str               # pending | in_progress | review | completed
    total_videos: int         # 전체 비디오 수
    excel_done: int           # 완료된 수
    progress_percent: float   # 진행률 (%)
    notes1: str | None
    notes2: str | None
```

### WorkerStats

```python
class WorkerStats:
    pic: str                  # 작업자명
    task_count: int           # 할당된 작업 수
    total_videos: int         # 전체 비디오 수
    total_done: int           # 완료된 비디오 수
    progress_percent: float   # 진행률 (%)
    archives: list[str]       # 담당 아카이브 목록
    status_breakdown: dict    # 상태별 작업 수
```

---

## Status Definitions

| Status | Label | Color | Description |
|--------|-------|-------|-------------|
| `pending` | 대기 | Gray ⚪ | 작업 대기 중 |
| `in_progress` | 작업 중 | Blue 🔵 | 작업 진행 중 |
| `review` | 검토 | Yellow 🟡 | 검토 대기 |
| `completed` | 완료 | Green 🟢 | 작업 완료 |

---

## Related Blocks

| Block | Relationship |
|-------|-------------|
| `sync.sheets` | Google Sheets 데이터 소스 |
| `progress` | 진행률 계산 연동 |
| `scanner` | 파일 스캔 데이터 |

---

## Usage Examples

### 작업 현황 조회
```typescript
const { data } = await archivingStatusApi.getAll({
  status: 'in_progress',
  pic: '김철수'
});
```

### 작업자 통계 조회
```typescript
const { workers, summary } = await workerStatsApi.getAll();
```

### 동기화 트리거
```typescript
await syncApi.trigger();
```

---

## Debugging

### 동기화 문제
1. `/api/sync/status` 확인 - error 필드
2. Backend 로그 확인 - `sheets_sync` 관련
3. Google Sheets API 할당량 확인

### 진행률 불일치
1. `excel_done` vs `total_videos` 값 확인
2. Google Sheets 원본 데이터 확인
3. 수동 동기화 트리거 후 재확인

---

## PRD Reference

- [PRD-0040-ARCHIVING-STATUS-UI.md](../../docs/PRD-0040-ARCHIVING-STATUS-UI.md)
