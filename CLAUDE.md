# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

1PB 규모의 NAS 아카이브 저장소를 모니터링하는 웹 기반 대시보드. 파일 통계, 폴더 트리 시각화, 아카이빙 작업 현황 추적 기능 제공.

**NAS 경로**: `\\10.10.100.122\docker\GGPNAs\ARCHIVE`

## Build & Run Commands

### Backend (FastAPI)

```powershell
cd backend
python -m venv venv
venv\Scripts\activate           # Windows
pip install -r requirements.txt
cp .env.example .env            # 환경변수 설정

# 개발 서버
uvicorn app.main:app --reload --port 8000

# 단일 테스트
pytest tests/test_scanner.py -v

# 린트
black --check app/ && isort --check app/ && flake8 app/
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
```

### Docker (프로덕션)

```powershell
# NAS 마운트 필요 (호스트에서 /mnt/nas 또는 Z:)
docker-compose up -d

# 로그 확인
docker-compose logs -f backend
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  pages/: Dashboard, Folders, WorkStatus                      │
│  components/: Layout, StatCard, FolderTree                   │
│  services/api.ts → Axios HTTP client                         │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  app/main.py → Entry point, CORS, lifespan                   │
│  app/api/                                                    │
│    ├── stats.py      → /api/stats (통계 조회)                │
│    ├── folders.py    → /api/folders (폴더 트리)              │
│    ├── work_status.py → /api/work-status (작업 현황)         │
│    └── scan.py       → /api/scan (스캔 트리거)               │
│  app/services/scanner.py → NAS 파일 스캔 로직                │
│  app/models/ → SQLAlchemy 모델                               │
│  app/schemas/ → Pydantic 스키마                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  SQLite (archive_stats.db)    NAS (SMB/CIFS, Read-only)     │
│  - 스캔 결과 캐싱              - 실제 파일 메타데이터 수집    │
│  - 작업 현황 저장              - ffprobe로 미디어 재생시간    │
└─────────────────────────────────────────────────────────────┘
```

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | 헬스체크 |
| `GET /api/stats` | 전체 통계 (파일 수, 용량, 재생시간) |
| `GET /api/folders` | 폴더 트리 구조 |
| `POST /api/scan` | 스캔 시작 |
| `GET /api/work-status` | 아카이빙 작업 현황 |

## Configuration

환경변수 (`backend/.env`):
- `NAS_LOCAL_PATH`: 마운트된 NAS 경로 (Windows: `Z:/GGPNAs/ARCHIVE`, Linux: `/mnt/nas`)
- `DATABASE_URL`: SQLite 경로
- `CORS_ALLOW_ALL`: LAN 배포 시 `true`

## Project Structure

```
archive-statistics/
├── backend/app/          # FastAPI 앱
│   ├── api/              # 라우터 (stats, folders, work_status, scan)
│   ├── core/             # config, database
│   ├── models/           # SQLAlchemy 모델
│   ├── schemas/          # Pydantic 스키마
│   └── services/         # 비즈니스 로직 (scanner)
├── frontend/src/         # React 앱
│   ├── pages/            # 페이지 컴포넌트
│   ├── components/       # 공통 컴포넌트
│   └── services/         # API 클라이언트
├── docker/               # Dockerfile
├── deploy/               # 배포 스크립트
├── docs/                 # UI 목업, 설계 문서
├── tasks/prds/           # PRD 문서
└── .claude/agents/       # AI 에이전트 규칙
```

## Block Agent System

AI 컨텍스트 최적화를 위한 블럭화 에이전트 시스템 적용.

### Domain Structure

| Domain | Blocks | 책임 |
|--------|--------|------|
| Scanner | discovery, metadata, storage | NAS 스캔 |
| Progress | video, hand, dashboard | 작업 진행률 |
| Sync | sheets, matching, import | Sheets 동기화 |

### Agent Rules Files

```
.claude/agents/           # 도메인 에이전트 규칙
backend/app/api/AGENT_RULES.md
backend/app/services/AGENT_RULES.md
backend/app/models/AGENT_RULES.md
```

자세한 내용: [docs/BLOCK_AGENT_SYSTEM.md](docs/BLOCK_AGENT_SYSTEM.md)
