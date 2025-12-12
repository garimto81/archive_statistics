# Architecture

시스템 구조 및 도메인 로직 상세

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React 18 + TypeScript)        │
│  pages/: Dashboard, Folders, WorkStatus, Statistics          │
│  components/: FolderTreeWithProgress, ProgressBar            │
│  services/api.ts → Axios + React Query                       │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API (http://localhost:8000)
┌──────────────────────────▼──────────────────────────────────┐
│                    Backend (FastAPI + SQLAlchemy)            │
│  app/api/                                                    │
│    ├── progress.py   → /api/progress/tree (핵심 API) ⭐      │
│    ├── stats.py      → /api/stats                           │
│    ├── folders.py    → /api/folders                         │
│    ├── work_status.py → /api/work-status                    │
│    ├── sync.py       → /api/sync                            │
│    └── scan.py       → /api/scan                            │
│  app/services/                                               │
│    ├── progress_service.py → 폴더-카테고리 매칭 (핵심) ⭐     │
│    ├── scanner.py         → NAS 파일 스캔 + ffprobe          │
│    └── sheets_sync.py     → Google Sheets 동기화             │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        ▼                                      ▼
┌───────────────────┐               ┌──────────────────────┐
│  SQLite           │               │  NAS (SMB/CIFS)      │
│  - FolderStats    │               │  - 비디오 파일       │
│  - FileStats      │               │  - ffprobe 메타데이터│
│  - WorkStatus     │               └──────────────────────┘
│  - HandAnalysis   │
└───────────────────┘
```

---

## Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | 헬스체크 |
| `/api/stats` | GET | 전체 통계 (파일 수, 용량, 재생시간) |
| `/api/folders` | GET | 폴더 트리 구조 |
| `/api/progress/tree` | GET | 진행률 포함 폴더 트리 ⭐ |
| `/api/scan` | POST | NAS 스캔 시작 |
| `/api/work-status` | GET | 아카이빙 작업 현황 |
| `/api/sync/status` | GET | Google Sheets 동기화 상태 |
| `/api/sync/trigger` | POST | 수동 동기화 트리거 |
| `/api/hands` | GET | Hand Analysis 데이터 |
| `/api/data-sources` | GET | 데이터 소스 상태 |
| `/api/worker-stats` | GET | 작업자별 통계 |

---

## Core Domain Logic ⭐

### 1. 폴더-카테고리 매칭 (`progress_service.py`)

NAS 폴더명과 Google Sheets 카테고리를 매칭하여 작업 진행률 계산:

| 전략 | 점수 | 예시 |
|------|------|------|
| `exact` | 1.0 | "GOG" == "GOG" |
| `prefix` | 0.9 | 카테고리 "PAD S12"가 폴더명 "PAD"로 시작 |
| `folder_prefix` | 0.85 | 폴더명 "GOG 최종"이 카테고리 "GOG"로 시작 |
| `word` | 0.8 | "wsop" in ["2023", "wsop", "paradise"] |
| `year` | 0.7 | 폴더 "2023"이 카테고리에 포함 |

**매칭 흐름**:
```
1. NAS 폴더 이름 정규화 (대소문자, 공백 처리)
2. Google Sheets 카테고리와 6가지 전략으로 매칭 시도
3. 최고 점수 매칭 결과 반환 (0.7 미만은 무시)
4. 매칭된 카테고리의 excel_done, total_videos로 진행률 계산
```

### 2. 90% 완료 기준

```python
# MAX(time_end) >= video_duration * 0.9 → COMPLETE
def calculate_completion_status(video_duration: float, hands: List[Hand]) -> str:
    if not hands:
        return "NOT_STARTED"

    max_time_end = max(h.timecode_out_sec for h in hands)
    progress = max_time_end / video_duration if video_duration > 0 else 0

    if progress >= 0.9:
        return "COMPLETE"
    elif progress >= 0.1:
        return "IN_PROGRESS"
    else:
        return "STARTED"
```

### 3. 하이어라키 합산 원칙

부모 폴더는 자식 폴더들의 `total_done`, `total_files`를 합산:

```
ARCHIVE/
├── 2023/                    # total_done: 150, total_files: 200 (합산)
│   ├── WSOP/               # total_done: 100, total_files: 120
│   └── GGMillions/         # total_done: 50,  total_files: 80
```

---

## File Structure

### Backend

```
backend/app/
├── api/
│   ├── __init__.py
│   ├── progress.py        # Progress API (핵심)
│   ├── stats.py           # 통계 API
│   ├── folders.py         # 폴더 트리 API
│   ├── work_status.py     # 작업 현황 API
│   ├── sync.py            # Google Sheets 동기화
│   ├── scan.py            # NAS 스캔
│   ├── hands.py           # Hand Analysis
│   ├── data_sources.py    # 데이터 소스
│   └── worker_stats.py    # 작업자 통계
├── services/
│   ├── progress_service.py  # 매칭 로직 (핵심)
│   ├── scanner.py           # NAS 스캔 + ffprobe
│   ├── sheets_sync.py       # Sheets API 연동
│   └── hand_analysis_sync.py
├── models/
│   ├── file_stats.py        # FileStats, FolderStats
│   ├── work_status.py       # WorkStatus
│   └── hand_analysis.py     # HandAnalysis
├── schemas/
│   ├── stats.py
│   ├── work_status.py
│   └── worker_stats.py
├── core/
│   ├── config.py            # Settings
│   └── database.py          # SQLAlchemy
└── main.py                  # FastAPI app
```

### Frontend

```
frontend/src/
├── pages/
│   ├── Dashboard.tsx        # 대시보드
│   ├── Folders.tsx          # 폴더 트리
│   ├── WorkStatus.tsx       # 작업 현황
│   ├── Statistics.tsx       # 통계
│   └── Settings.tsx         # 설정
├── components/
│   ├── FolderTreeWithProgress.tsx  # 트리 + 진행률 (핵심)
│   ├── ProgressBar.tsx
│   ├── StatCard.tsx
│   ├── CodecStats.tsx
│   └── Layout.tsx
├── services/
│   └── api.ts               # Axios + React Query
└── types/
    └── index.ts
```

---

## Block Agent System

AI 컨텍스트 최적화를 위한 도메인 분리. 상세: [BLOCK_AGENT_SYSTEM.md](BLOCK_AGENT_SYSTEM.md)

| Domain | 핵심 파일 | 책임 |
|--------|----------|------|
| Scanner | `scanner.py`, `file_stats.py` | NAS 스캔, 메타데이터 |
| Progress | `progress_service.py`, `FolderTreeWithProgress.tsx` | 작업 진행률 |
| Sync | `sheets_sync.py`, `hand_analysis.py` | Sheets 동기화 |
| Reconciliation | `progress_service.py:202-665` | NAS-Sheets 일관성 |
