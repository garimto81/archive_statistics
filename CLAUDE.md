# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Version**: 1.33.0 | **Last Updated**: 2025-12-12

## Project Overview

1PB 규모의 NAS 아카이브 저장소 모니터링 대시보드 (FastAPI + React)

**NAS 경로**: `\\10.10.100.122\docker\GGPNAs\ARCHIVE`

---

## Quick Reference

| 작업 | 명령어 |
|------|--------|
| Backend 실행 | `cd backend && uvicorn app.main:app --reload --port 8000` |
| Frontend 실행 | `cd frontend && npm run dev` |
| 테스트 (단일) | `cd backend && pytest tests/test_api.py -v` |
| 린트 자동수정 | `cd backend && black app/ && isort app/` |
| Frontend 린트 | `cd frontend && npm run lint` |
| E2E 테스트 | `cd frontend && npm run test:e2e` |
| Docker 재배포 | `docker-compose down && docker-compose build --no-cache && docker-compose up -d` |

---

## 핵심 규칙

> **전역 규칙**: [상위 CLAUDE.md](../CLAUDE.md) 참조

| 규칙 | 내용 |
|------|------|
| PR 후 Docker 재배포 | 필수 ⚠️ |
| 테스트 통과 | `pytest`, `npm run lint` |
| 버전 업데이트 | CLAUDE.md 버전 + 날짜 갱신 |

---

## 핵심 API

| Endpoint | Description |
|----------|-------------|
| `GET /api/progress/tree` | 진행률 포함 폴더 트리 ⭐ |
| `GET /api/stats` | 전체 통계 |
| `GET /api/work-status` | 작업 현황 |
| `POST /api/scan` | NAS 스캔 |
| `GET /api/sync/status` | Sheets 동기화 상태 |

---

## 핵심 도메인 로직 ⭐

### 폴더-카테고리 매칭 점수

| 전략 | 점수 | 예시 |
|------|------|------|
| `exact` | 1.0 | "GOG" == "GOG" |
| `prefix` | 0.9 | 카테고리가 폴더명으로 시작 |
| `folder_prefix` | 0.85 | 폴더명이 카테고리로 시작 |
| `word` | 0.8 | 단어 포함 |

### 90% 완료 기준

```python
# MAX(time_end) >= video_duration * 0.9 → COMPLETE
```

---

## 핵심 파일

| 파일 | 역할 |
|------|------|
| `backend/app/services/progress_service.py` | 매칭 로직 (핵심) ⭐ |
| `backend/app/api/progress.py` | Progress API |
| `frontend/src/components/MasterFolderTree/index.tsx` | 통합 트리 UI (Dashboard/Folders/Statistics 공용) ⭐ |
| `frontend/src/components/MasterFolderDetail/index.tsx` | 폴더 상세 패널 |
| `backend/app/services/sheets_sync.py` | Google Sheets 동기화 |

### Block Agent System

`progress_service.py`는 Block Index로 구조화됨. 특정 기능 수정 시 해당 블록만 참조:

| Block ID | Lines | Description |
|----------|-------|-------------|
| `progress.utils` | 25-55 | 정규화/유사도 헬퍼 |
| `progress.matcher` | 162-285 | 폴더-카테고리 매칭 |
| `progress.aggregator` | 325-642 | 하이어라키 합산 |

---

## 상세 문서

| 문서 | 내용 |
|------|------|
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | 빌드, 테스트, Docker 명령어 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 시스템 구조, 도메인 로직 |
| [docs/DEBUGGING.md](docs/DEBUGGING.md) | 디버깅 가이드 |
| [docs/BLOCK_AGENT_SYSTEM.md](docs/BLOCK_AGENT_SYSTEM.md) | AI 컨텍스트 최적화 |

---

## 환경변수

```bash
# backend/.env
NAS_LOCAL_PATH=Z:/GGPNAs/ARCHIVE
DATABASE_URL=sqlite+aiosqlite:///./archive_stats.db
GOOGLE_SHEETS_ID=1abc...
```

---

## 아키텍처 개요

```
Frontend (React 18 + Vite + TailwindCSS)
    │ REST API
Backend (FastAPI + SQLAlchemy + aiosqlite)
    ├── SQLite (FolderStats, FileStats, WorkStatus)
    └── NAS (SMB/CIFS, 비디오 파일, ffprobe 메타데이터)
```

**데이터 흐름**: NAS 스캔 → DB 저장 → Google Sheets 동기화 → 진행률 계산 → 프론트엔드 표시

---

## 변경 이력

| 버전 | 날짜 | 변경 |
|------|------|------|
| 1.33.0 | 2025-12-12 | progress.validator 블록 추가 (PRD-0041 Phase 1, #42) |
| 1.32.0 | 2025-12-12 | WorkStatus 기본 탭 Workers로 변경 (#40) |
| 1.31.0 | 2025-12-12 | CLAUDE.md 개선: Quick Reference 확장, Block Agent System 추가 |
| 1.30.0 | 2025-12-12 | MasterFolderTree 통합 컴포넌트 (#34), 레거시 정리 |
| 1.29.0 | 2025-12-12 | 숨긴 항목 필터 기능 (is_hidden, include_hidden API) |
| 1.28.0 | 2025-12-12 | NAS/Sheets 데이터 분리 표시 (#29), 파일 메타데이터 표시 개선 |
| 1.27.0 | 2025-12-12 | 문서 분리 (DEVELOPMENT, ARCHITECTURE, DEBUGGING) |
| 1.26.0 | 2025-12-11 | Google Sheets 동기화 기능 |
