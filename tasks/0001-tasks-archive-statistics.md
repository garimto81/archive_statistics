# Task List: Archive Statistics Dashboard (PRD-0001)

**Created**: 2025-12-05
**PRD**: `tasks/prds/0001-prd-archive-statistics.md`
**Status**: In Progress

---

## Phase 0: 프로젝트 설정

### Task 0.1: 프로젝트 초기화
- [ ] Git 저장소 초기화
- [ ] `.gitignore` 설정
- [ ] `README.md` 작성
- [ ] 프로젝트 구조 생성

**Priority**: High
**Estimate**: 1h

### Task 0.2: 개발 환경 설정
- [ ] Python 가상환경 생성 (venv)
- [ ] Node.js/npm 설정
- [ ] Docker 설정 (선택)
- [ ] VS Code 설정 (.vscode/)

**Priority**: High
**Estimate**: 2h

---

## Phase 1: Backend 개발

### Task 1.1: FastAPI 서버 기본 구조
- [ ] FastAPI 프로젝트 생성
- [ ] 기본 라우터 설정
- [ ] CORS 설정
- [ ] 환경변수 설정 (.env)

**Priority**: High
**Estimate**: 2h

### Task 1.2: 데이터베이스 모델 설계
- [ ] SQLite/PostgreSQL 연결
- [ ] 파일 메타데이터 테이블
- [ ] 스캔 히스토리 테이블
- [ ] 작업 현황 테이블 (Work Status)
- [ ] Alembic 마이그레이션 설정

**Priority**: High
**Estimate**: 3h

### Task 1.3: NAS 연결 모듈
- [ ] SMB/CIFS 연결 구현
- [ ] 인증 처리 (GGP/!@QW12qw)
- [ ] 연결 상태 확인 API
- [ ] 에러 핸들링

**Priority**: High
**Estimate**: 4h
**Path**: `\\10.10.100.122\docker\GGPNAs\ARCHIVE`

### Task 1.4: 아카이브 스캐너 개발
- [ ] 디렉토리 트리 스캔 로직
- [ ] 파일 메타데이터 수집 (크기, 형식, 수정일)
- [ ] 미디어 재생시간 추출 (ffprobe)
- [ ] 점진적 스캔 구현
- [ ] 백그라운드 작업 (Celery/BackgroundTasks)
- [ ] 스캔 진행률 API

**Priority**: High
**Estimate**: 8h

### Task 1.5: 통계 API 개발
- [ ] GET /api/stats/summary - 전체 통계
- [ ] GET /api/stats/file-types - 파일 형식별 통계
- [ ] GET /api/stats/folders - 폴더별 통계
- [ ] GET /api/stats/history - 히스토리 데이터
- [ ] GET /api/folders/tree - 폴더 트리 구조

**Priority**: High
**Estimate**: 4h

### Task 1.6: 작업 현황 API 개발
- [ ] GET /api/work-status - 전체 작업 목록
- [ ] POST /api/work-status - 작업 추가
- [ ] PUT /api/work-status/{id} - 작업 수정
- [ ] DELETE /api/work-status/{id} - 작업 삭제
- [ ] POST /api/work-status/import - CSV Import
- [ ] GET /api/work-status/export - Excel Export

**Priority**: High
**Estimate**: 4h

### Task 1.7: 알림 시스템
- [ ] 알림 규칙 설정 API
- [ ] 임계치 모니터링
- [ ] 이메일 알림 (SMTP)
- [ ] 웹 알림 (WebSocket)

**Priority**: Medium
**Estimate**: 4h

---

## Phase 2: Frontend 개발

### Task 2.1: React 프로젝트 설정
- [ ] Vite + React + TypeScript
- [ ] TailwindCSS 설정
- [ ] React Router 설정
- [ ] Axios/React Query 설정

**Priority**: High
**Estimate**: 2h

### Task 2.2: 공통 컴포넌트 개발
- [ ] Layout (Header, Sidebar, Footer)
- [ ] StatCard 컴포넌트
- [ ] LoadingSpinner
- [ ] ErrorBoundary
- [ ] Modal 컴포넌트

**Priority**: High
**Estimate**: 4h

### Task 2.3: 대시보드 페이지
- [ ] 통계 카드 4개 (파일 수, 용량, 재생시간, 형식 수)
- [ ] 파일 형식별 분포 Pie Chart
- [ ] 용량 추이 Line Chart
- [ ] 마지막 스캔 정보

**Priority**: High
**Estimate**: 6h

### Task 2.4: 폴더 트리 뷰 페이지
- [ ] 인터랙티브 폴더 트리 컴포넌트
- [ ] 트리맵 시각화 (react-d3-treemap)
- [ ] 폴더 클릭 시 드릴다운
- [ ] 폴더 상세 정보 패널
- [ ] 검색 및 필터링

**Priority**: High
**Estimate**: 8h

### Task 2.5: 통계 페이지
- [ ] 파일 형식별 상세 테이블
- [ ] 폴더별 용량 Top 10 Bar Chart
- [ ] 필터링 (날짜, 형식)
- [ ] 데이터 Export (CSV)

**Priority**: Medium
**Estimate**: 4h

### Task 2.6: 히스토리 페이지
- [ ] 날짜 범위 필터
- [ ] 용량 추이 그래프
- [ ] 히스토리 테이블
- [ ] Export 기능

**Priority**: Medium
**Estimate**: 4h

### Task 2.7: 작업 현황 페이지 (Work Status)
- [ ] 작업 현황 테이블 뷰
- [ ] 칸반 보드 뷰
- [ ] 작업 추가/수정 모달
- [ ] CSV Import 기능
- [ ] Excel Export 기능
- [ ] 담당자별 필터링
- [ ] 진행률 차트

**Priority**: High
**Estimate**: 8h

### Task 2.8: 스캔 기능 UI
- [ ] 스캔 시작 버튼
- [ ] 스캔 진행률 모달
- [ ] 스캔 히스토리 표시

**Priority**: High
**Estimate**: 3h

### Task 2.9: 알림 설정 페이지
- [ ] 알림 규칙 목록
- [ ] 알림 추가/수정 폼
- [ ] 알림 테스트 기능

**Priority**: Medium
**Estimate**: 3h

### Task 2.10: 설정 페이지
- [ ] NAS 연결 설정
- [ ] 스캔 스케줄 설정
- [ ] 알림 설정

**Priority**: Low
**Estimate**: 2h

---

## Phase 3: 통합 및 테스트

### Task 3.1: API 연동 테스트
- [ ] Backend-Frontend 연동 확인
- [ ] CORS 이슈 해결
- [ ] 에러 핸들링 검증

**Priority**: High
**Estimate**: 2h

### Task 3.2: 성능 최적화
- [ ] 대용량 폴더 트리 렌더링 최적화
- [ ] API 응답 캐싱
- [ ] 지연 로딩 구현

**Priority**: Medium
**Estimate**: 4h

### Task 3.3: 단위 테스트
- [ ] Backend API 테스트 (pytest)
- [ ] Frontend 컴포넌트 테스트 (Jest)

**Priority**: Medium
**Estimate**: 4h

### Task 3.4: E2E 테스트
- [ ] 주요 사용자 시나리오 테스트
- [ ] 스캔 기능 테스트
- [ ] 작업 현황 CRUD 테스트

**Priority**: Low
**Estimate**: 4h

---

## Phase 4: 배포

### Task 4.1: Docker 컨테이너화
- [ ] Backend Dockerfile
- [ ] Frontend Dockerfile
- [ ] docker-compose.yml

**Priority**: High
**Estimate**: 3h

### Task 4.2: 배포 환경 설정
- [ ] 환경변수 설정
- [ ] 리버스 프록시 (Nginx)
- [ ] SSL 설정

**Priority**: High
**Estimate**: 3h

### Task 4.3: 모니터링 설정
- [ ] 로깅 설정
- [ ] 헬스 체크 API
- [ ] 에러 알림

**Priority**: Medium
**Estimate**: 2h

---

## 진행률 요약

| Phase | 태스크 수 | 완료 | 진행률 |
|-------|----------|------|--------|
| Phase 0: 설정 | 2 | 0 | 0% |
| Phase 1: Backend | 7 | 0 | 0% |
| Phase 2: Frontend | 10 | 0 | 0% |
| Phase 3: 테스트 | 4 | 0 | 0% |
| Phase 4: 배포 | 3 | 0 | 0% |
| **Total** | **26** | **0** | **0%** |

---

## 우선순위별 태스크

### 🔴 High Priority (15)
- Task 0.1, 0.2: 프로젝트 설정
- Task 1.1-1.6: Backend 핵심 기능
- Task 2.1-2.4, 2.7, 2.8: Frontend 핵심 기능
- Task 3.1: API 연동
- Task 4.1, 4.2: 배포

### 🟡 Medium Priority (8)
- Task 1.7: 알림 시스템
- Task 2.5, 2.6, 2.9: 통계/히스토리/알림 페이지
- Task 3.2, 3.3: 최적화/단위테스트
- Task 4.3: 모니터링

### 🟢 Low Priority (3)
- Task 2.10: 설정 페이지
- Task 3.4: E2E 테스트

---

## 예상 총 작업 시간

| Category | 시간 |
|----------|------|
| Phase 0: 설정 | 3h |
| Phase 1: Backend | 29h |
| Phase 2: Frontend | 44h |
| Phase 3: 테스트 | 14h |
| Phase 4: 배포 | 8h |
| **Total** | **98h** |

---

## 다음 단계

1. Task 0.1: 프로젝트 초기화 시작
2. 개발 환경 선택 확정 (커스텀 개발 vs 오픈소스 조합)
3. 기술 스택 최종 확정
