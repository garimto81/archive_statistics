# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Version**: 1.14.0 | **Last Updated**: 2025-12-10

## Project Overview

1PB 규모의 NAS 아카이브 저장소를 모니터링하는 웹 기반 대시보드. 파일 통계, 폴더 트리 시각화, 아카이빙 작업 현황 추적 기능 제공.

**NAS 경로**: `\\10.10.100.122\docker\GGPNAs\ARCHIVE`

---

## 핵심 규칙

> **전역 규칙 적용**: [상위 CLAUDE.md](../CLAUDE.md) 참조

---

## 버전 관리 및 태깅 규칙 ⚠️

> **상세 규칙**: [상위 CLAUDE.md - 버전 관리](../CLAUDE.md#버전-관리-필수) 참조

### 필수 체크리스트 (PR/Issue)

| 항목 | 필수 | 예시 |
|------|:----:|------|
| CLAUDE.md 버전 업데이트 | ✅ | `1.7.0` → `1.8.0` |
| 커밋 해시 참조 | ✅ | `abc1234` |
| 이슈 번호 연결 | ✅ | `Fixes #3`, `Refs: #5` |
| 테스트 통과 확인 | ✅ | `pytest`, `npm run lint` |
| **Docker 재배포** | ✅ | PR 머지 후 반드시 실행 |

### 작업 완료 후 Docker 재배포 (필수) ⚠️

**PR 머지 후 반드시 Docker 재배포를 실행해야 변경사항이 프로덕션에 반영됩니다.**

```powershell
# 프로젝트 루트에서 실행
cd D:\AI\claude01\archive-statistics

# Backend 재빌드 및 재배포 (Python 코드 변경 시)
docker-compose down && docker-compose build --no-cache backend && docker-compose up -d

# 전체 재빌드 (Frontend 포함)
docker-compose down && docker-compose build --no-cache && docker-compose up -d

# 배포 확인
docker-compose ps
curl http://localhost:8002/health
```

**DB 마이그레이션이 필요한 경우** (새 컬럼 추가 등):
```powershell
# 로컬 DB 파일에 직접 마이그레이션 적용
python -c "
import sqlite3
conn = sqlite3.connect('data/archive_stats.db')
cursor = conn.cursor()
# ALTER TABLE 실행
cursor.execute('ALTER TABLE table_name ADD COLUMN new_column TEXT')
conn.commit()
conn.close()
"
```

### 버전 업데이트 예시

```markdown
# 변경 전
**Version**: 1.7.0 | **Last Updated**: 2025-12-10

# 변경 후 (버전 증가 + 날짜 갱신)
**Version**: 1.8.0 | **Last Updated**: 2025-12-11
```

---

## Build & Run Commands

### Backend (FastAPI)

```powershell
cd backend

# 초기 설정 (1회)
python -m venv venv
venv\Scripts\activate           # Windows (Linux: source venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env            # 환경변수 설정

# 개발 서버
uvicorn app.main:app --reload --port 8000

# 테스트
pytest tests/test_scanner.py -v           # 단일 테스트
pytest tests/ -v --tb=short               # 전체 테스트 (간략 출력)
pytest tests/test_api.py -v -k "test_stats"  # 특정 테스트만

# 린트 (개별)
black --check app/
isort --check app/
flake8 app/

# 린트 (자동 수정)
black app/ && isort app/
```

### Frontend (React/Vite)

```powershell
cd frontend
npm install

# 개발 서버 (port 5173)
npm run dev

# 빌드
npm run build

# 린트
npm run lint

# E2E 테스트 (Playwright)
npm run test:e2e                 # 전체 실행
npm run test:e2e:ui              # UI 모드
npm run test:e2e:chromium        # Chromium만
```

### Docker (프로덕션)

```powershell
# 전체 스택 실행 (NAS 마운트 필요)
docker-compose up -d

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend

# Backend만 재빌드 (Python 코드 변경 시)
docker-compose build --no-cache backend && docker-compose up -d backend

# 전체 재빌드
docker-compose down && docker-compose build --no-cache && docker-compose up -d
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React 18 + TypeScript)        │
│  pages/: Dashboard, Folders, WorkStatus                      │
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

## Core Domain Logic ⭐

### 폴더-카테고리 매칭 (`progress_service.py`)

NAS 폴더명과 Google Sheets 카테고리를 매칭하여 작업 진행률 계산:

| 전략 | 점수 | 예시 |
|------|------|------|
| `exact` | 1.0 | "GOG" == "GOG" |
| `prefix` | 0.9 | 카테고리 "PAD S12"가 폴더명 "PAD"로 시작 |
| `folder_prefix` | 0.85 | 폴더명 "GOG 최종"이 카테고리 "GOG"로 시작 |
| `word` | 0.8 | "wsop" in ["2023", "wsop", "paradise"] |
| `year` | 0.7 | 폴더 "2023"이 카테고리에 포함 |

### 90% 완료 기준 (`progress-domain.md`)

```python
# MAX(time_end) >= video_duration * 0.9 → COMPLETE
if progress >= 0.9:
    return "COMPLETE"
```

### 하이어라키 합산 원칙

부모 폴더는 자식 폴더들의 `total_done`, `total_files`를 합산하여 진행률 표시.

---

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | 헬스체크 |
| `GET /api/stats` | 전체 통계 (파일 수, 용량, 재생시간) |
| `GET /api/folders` | 폴더 트리 구조 |
| `GET /api/progress/tree` | 진행률 포함 폴더 트리 ⭐ |
| `POST /api/scan` | NAS 스캔 시작 |
| `GET /api/work-status` | 아카이빙 작업 현황 |

---

## Configuration

환경변수 (`backend/.env`):
```bash
NAS_LOCAL_PATH=Z:/GGPNAs/ARCHIVE  # Windows (Linux: /mnt/nas)
DATABASE_URL=sqlite+aiosqlite:///./archive_stats.db
CORS_ALLOW_ALL=true               # LAN 배포 시
GOOGLE_SHEETS_ID=1abc...          # Google Sheets 연동 시
```

---

## Key Files Reference

| 파일 | 역할 |
|------|------|
| `backend/app/services/progress_service.py` | 폴더-카테고리 매칭 로직 (핵심) |
| `backend/app/api/progress.py` | Progress API 엔드포인트 |
| `frontend/src/components/FolderTreeWithProgress.tsx` | 트리 렌더링 + 진행률 표시 |
| `frontend/src/pages/Dashboard.tsx` | 대시보드 레이아웃 |
| `.claude/agents/progress-domain.md` | 도메인 규칙 상세 문서 |

---

## Block Agent System

AI 컨텍스트 최적화를 위한 도메인 분리:

| Domain | 핵심 파일 | 책임 |
|--------|----------|------|
| Scanner | `scanner.py`, `file_stats.py` | NAS 스캔 |
| Progress | `progress_service.py`, `FolderTreeWithProgress.tsx` | 작업 진행률 ⭐ |
| Sync | `sheets_sync.py`, `hand_analysis.py` | Sheets 동기화 |

상세: [docs/BLOCK_AGENT_SYSTEM.md](docs/BLOCK_AGENT_SYSTEM.md)

---

## Debugging

### Frontend 디버그 로그 확인

```javascript
// 브라우저 DevTools > Console
[FolderTreeWithProgress] API 응답: {...}
[getWorkSummary] 폴더: WSOP {depth: 1, hasWorkSummary: true, ...}
[getWorkSummary] ⚠️ GGMillions: work_summary가 없음!
```

### Backend 디버그 로그 확인

```bash
docker-compose logs -f backend | grep "\[DEBUG\]"
```

### DB 카테고리 확인

```bash
docker exec archive-stats-backend python -c "
from app.core.database import SessionLocal
from app.models.work_status import WorkStatus
db = SessionLocal()
for ws in db.query(WorkStatus).all():
    print(f'{ws.category}: total={ws.total_videos}, done={ws.excel_done}')
"
```
