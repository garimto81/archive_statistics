# Task List: Google Sheets 자동 동기화 (PRD-0002)

**Created**: 2025-12-09
**PRD**: `docs/GOOGLE_SHEETS_INTEGRATION_PROPOSAL.md`
**Implementation Guide**: `docs/IMPLEMENTATION_GUIDE_SHEETS_SYNC.md`
**Status**: Planning
**Related Issue**: GitHub #2

---

## 개요

Google Sheets에 저장된 작업자별 작업 현황 데이터를 자동으로 동기화하여
Archive Statistics Dashboard의 Workers 탭에서 실시간으로 확인할 수 있도록 구현.

### 핵심 요구사항

| 요구사항 | 설명 |
|----------|------|
| 자동 동기화 | CSV import 없이 백그라운드에서 자동 연동 |
| Service Account | Google Service Account API 인증 |
| 주기적 갱신 | 30분 간격 자동 데이터 갱신 |

---

## Phase 0: 사전 준비 (Blocked - 사용자 입력 대기)

### Task 0.1: Google Cloud 설정 ⏸️
- [ ] Google Cloud Console 프로젝트 생성/선택
- [ ] Google Sheets API 활성화
- [ ] Service Account 생성
- [ ] JSON 키 파일 다운로드

**Priority**: High
**Estimate**: 30m
**Status**: Blocked (사용자 필요)

### Task 0.2: Google Sheet URL 수집 ⏸️
- [ ] 작업 현황 Google Sheet URL 수집
- [ ] Sheet 컬럼 구조 확인
- [ ] Service Account 이메일에 뷰어 권한 공유

**Priority**: High
**Estimate**: 15m
**Status**: Blocked (사용자 필요)
**Blocker**: 사용자가 Sheet URL 제공 필요

---

## Phase 1: Backend 의존성 및 설정

### Task 1.1: 의존성 추가
- [ ] `gspread>=6.0.0` 추가
- [ ] `google-auth>=2.0.0` 추가
- [ ] `apscheduler>=3.10.0` 추가
- [ ] `pip install` 및 requirements.txt 업데이트

**Priority**: High
**Estimate**: 15m
**Files**: `backend/requirements.txt`

### Task 1.2: 설정 파일 업데이트
- [ ] `config.py`에 Sheets 설정 추가
- [ ] `.env.example` 업데이트
- [ ] `.gitignore`에 credentials 폴더 추가

**Priority**: High
**Estimate**: 30m
**Files**:
- `backend/app/core/config.py`
- `backend/.env.example`
- `backend/.gitignore`

---

## Phase 2: SheetsSync 서비스 구현

### Task 2.1: SheetsSyncService 클래스 구현
- [ ] `sheets_sync.py` 파일 생성
- [ ] gspread 인증 로직 구현
- [ ] APScheduler 연동
- [ ] sync() 메서드 구현
- [ ] _parse_record() 메서드 구현
- [ ] _upsert_work_status() 메서드 구현

**Priority**: High
**Estimate**: 2h
**Files**: `backend/app/services/sheets_sync.py`
**Block**: `sync.sheets`

### Task 2.2: Sync API 엔드포인트
- [ ] `/api/sync/status` GET 엔드포인트
- [ ] `/api/sync/trigger` POST 엔드포인트
- [ ] Pydantic 스키마 정의
- [ ] main.py에 라우터 등록

**Priority**: High
**Estimate**: 1h
**Files**:
- `backend/app/api/sync.py`
- `backend/app/schemas/sync.py`
- `backend/app/main.py`

### Task 2.3: Lifespan 통합
- [ ] FastAPI lifespan에 sheets_sync 시작/종료 추가
- [ ] 서버 시작 시 첫 동기화 실행

**Priority**: High
**Estimate**: 30m
**Files**: `backend/app/main.py`

---

## Phase 3: Frontend 업데이트

### Task 3.1: Sync API 클라이언트 추가
- [ ] `syncApi` 함수 추가 (getStatus, trigger)
- [ ] TypeScript 타입 정의

**Priority**: Medium
**Estimate**: 30m
**Files**: `frontend/src/services/api.ts`

### Task 3.2: 동기화 상태 표시 컴포넌트
- [ ] SyncStatusIndicator 컴포넌트 구현
- [ ] 마지막 동기화 시간 표시
- [ ] 수동 동기화 버튼
- [ ] 에러 상태 표시

**Priority**: Medium
**Estimate**: 1h
**Files**: `frontend/src/pages/WorkStatus.tsx`

---

## Phase 4: AGENT_RULES 업데이트

### Task 4.1: Services AGENT_RULES 업데이트
- [ ] sync.sheets 블럭 규칙 추가
- [ ] 의존성 및 제약사항 문서화

**Priority**: Low
**Estimate**: 30m
**Files**: `backend/app/services/AGENT_RULES.md`

### Task 4.2: API AGENT_RULES 업데이트
- [ ] sync API 규칙 추가

**Priority**: Low
**Estimate**: 15m
**Files**: `backend/app/api/AGENT_RULES.md`

---

## Phase 5: 테스트

### Task 5.1: 단위 테스트
- [ ] SheetsSyncService 테스트 (Mock gspread)
- [ ] Sync API 엔드포인트 테스트
- [ ] 스키마 유효성 테스트

**Priority**: Medium
**Estimate**: 1.5h
**Files**: `backend/tests/test_sheets_sync.py`

### Task 5.2: E2E 테스트 업데이트
- [ ] 동기화 상태 표시 테스트
- [ ] 수동 동기화 버튼 테스트

**Priority**: Low
**Estimate**: 1h
**Files**: `frontend/tests/e2e/functional/sync-status.spec.ts`

---

## Phase 6: 배포

### Task 6.1: Docker 설정
- [ ] credentials 볼륨 마운트 설정
- [ ] 환경변수 설정 확인

**Priority**: High
**Estimate**: 30m
**Files**: `docker-compose.yml`

### Task 6.2: 문서 업데이트
- [ ] README에 Sheets 설정 가이드 추가
- [ ] CLAUDE.md 업데이트

**Priority**: Low
**Estimate**: 30m
**Files**: `README.md`, `CLAUDE.md`

---

## 진행률 요약

| Phase | 태스크 수 | 완료 | 진행률 | 상태 |
|-------|----------|------|--------|------|
| Phase 0: 사전 준비 | 2 | 0 | 0% | ⏸️ Blocked |
| Phase 1: 의존성/설정 | 2 | 0 | 0% | Pending |
| Phase 2: Backend 구현 | 3 | 0 | 0% | Pending |
| Phase 3: Frontend 업데이트 | 2 | 0 | 0% | Pending |
| Phase 4: AGENT_RULES | 2 | 0 | 0% | Pending |
| Phase 5: 테스트 | 2 | 0 | 0% | Pending |
| Phase 6: 배포 | 2 | 0 | 0% | Pending |
| **Total** | **15** | **0** | **0%** | - |

---

## 의존성 그래프

```
Phase 0 (Blocked) ─────┐
                       ▼
                 Phase 1 (의존성/설정)
                       │
                       ▼
                 Phase 2 (Backend)
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
     Phase 3      Phase 4      Phase 5
     (Frontend)  (AGENT_RULES) (테스트)
          │            │            │
          └────────────┴────────────┘
                       │
                       ▼
                 Phase 6 (배포)
```

---

## Blockers

| Blocker | 설명 | 해결 방법 |
|---------|------|----------|
| **Google Sheet URL** | 작업 현황 시트 URL 필요 | 사용자가 제공 |
| **Service Account JSON** | GCP 인증 키 필요 | 사용자가 GCP Console에서 생성 |

---

## 예상 총 작업 시간

| Category | 시간 |
|----------|------|
| Phase 0: 사전 준비 | 45m (사용자) |
| Phase 1: 의존성/설정 | 45m |
| Phase 2: Backend 구현 | 3.5h |
| Phase 3: Frontend 업데이트 | 1.5h |
| Phase 4: AGENT_RULES | 45m |
| Phase 5: 테스트 | 2.5h |
| Phase 6: 배포 | 1h |
| **Total** | **~11h** |

---

## 다음 단계

1. **⏸️ Phase 0 해제 대기**: 사용자로부터 Google Sheet URL 및 Service Account 정보 필요
2. Phase 0 완료 후 Phase 1부터 순차 진행
3. TDD 방식으로 구현 (테스트 먼저 작성)
