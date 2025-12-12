# PRD-0040: Archiving Status UI 개선

**Version**: 1.1.0
**Created**: 2025-12-12
**Issue**: #40
**Status**: Draft

---

## 1. Overview

### 1.1 Background

Issue #37에서 `WorkStatus` → `ArchivingStatus` 이름 변경이 완료되었습니다. 이제 UI에서 **작업자 표기** 및 **작업 상태**를 더 직관적으로 확인할 수 있도록 개선합니다.

### 1.2 Goals

1. **Work Status 탭 강화**: 핵심 작업 현황 뷰
2. **대시보드 통합**: 메인 대시보드에서 작업 현황 요약 확인
3. **Block Agent 설계**: AI 컨텍스트 최적화를 위한 도메인 분리
4. **API 마이그레이션**: deprecated API → 새 API 적용

---

## 2. UI Mockup Design

### 2.1 전체 페이지 레이아웃

```mermaid
graph TB
    subgraph App["🏠 Archive Statistics App"]
        direction TB

        subgraph NavBar["Navigation Bar"]
            N1["🏠 Dashboard"]
            N2["📁 Folders"]
            N3["📋 Work Status ⭐"]
            N4["📊 Statistics"]
        end

        subgraph MainContent["Main Content Area"]
            direction TB
            Dashboard["Dashboard Page"]
            WorkStatus["Work Status Page"]
        end
    end

    NavBar --> MainContent
```

### 2.2 Work Status Page - 전체 구조

```mermaid
graph TB
    subgraph WorkStatusPage["📋 Work Status Page"]
        direction TB

        subgraph Header["🔝 Header Section"]
            direction TB
            H1["🔄 Sync Status"]
            H2["Last sync: 5 minutes ago"]
            H3["[🔄 Sync Now Button]"]
        end

        subgraph Summary["📊 Summary Bar"]
            direction LR
            S1["📋 Total Tasks: 58"]
            S2["👥 Workers: 4"]
            S3["📈 Overall: 45%"]
            S4["🎬 Videos: 1,234 / 2,741"]
        end

        subgraph TabNav["🗂️ Tab Navigation"]
            direction LR
            T1["📋 Tasks"]
            T2["👥 Workers ⭐ Default"]
            T3["📈 Analytics"]
        end

        subgraph Content["📄 Tab Content"]
            direction TB
            WorkersTab["Workers Tab Content"]
        end
    end

    Header --> Summary
    Summary --> TabNav
    TabNav --> Content
```

### 2.3 Workers Tab - 작업자 카드 그리드

```mermaid
graph TB
    subgraph WorkersTab["👥 Workers Tab"]
        direction TB

        subgraph FilterBar["🔍 Filter & Sort"]
            F1["Sort: Progress ▼"]
            F2["Filter: All Status"]
        end

        subgraph CardGrid["📇 Worker Cards Grid"]
            direction TB

            subgraph Row1["Row 1"]
                direction LR

                subgraph Card1["👤 이영희"]
                    C1_1["━━━━━━━━━━━━━━"]
                    C1_2["📋 Tasks: 8"]
                    C1_3["📈 Progress: 82%"]
                    C1_4["████████░░"]
                    C1_5["━━━━━━━━━━━━━━"]
                    C1_6["🎬 320 / 390 videos"]
                    C1_7["━━━━━━━━━━━━━━"]
                    C1_8["🟢 완료: 6"]
                    C1_9["🔵 작업중: 2"]
                    C1_10["🟡 검토: 0"]
                    C1_11["⚪ 대기: 0"]
                end

                subgraph Card2["👤 김철수"]
                    C2_1["━━━━━━━━━━━━━━"]
                    C2_2["📋 Tasks: 12"]
                    C2_3["📈 Progress: 67%"]
                    C2_4["██████░░░░"]
                    C2_5["━━━━━━━━━━━━━━"]
                    C2_6["🎬 456 / 680 videos"]
                    C2_7["━━━━━━━━━━━━━━"]
                    C2_8["🟢 완료: 5"]
                    C2_9["🔵 작업중: 4"]
                    C2_10["🟡 검토: 2"]
                    C2_11["⚪ 대기: 1"]
                end
            end

            subgraph Row2["Row 2"]
                direction LR

                subgraph Card3["👤 박민수"]
                    C3_1["━━━━━━━━━━━━━━"]
                    C3_2["📋 Tasks: 15"]
                    C3_3["📈 Progress: 45%"]
                    C3_4["████░░░░░░"]
                    C3_5["━━━━━━━━━━━━━━"]
                    C3_6["🎬 280 / 620 videos"]
                    C3_7["━━━━━━━━━━━━━━"]
                    C3_8["🟢 완료: 3"]
                    C3_9["🔵 작업중: 8"]
                    C3_10["🟡 검토: 2"]
                    C3_11["⚪ 대기: 2"]
                end

                subgraph Card4["👤 Unassigned"]
                    C4_1["━━━━━━━━━━━━━━"]
                    C4_2["📋 Tasks: 23"]
                    C4_3["📈 Progress: 12%"]
                    C4_4["█░░░░░░░░░"]
                    C4_5["━━━━━━━━━━━━━━"]
                    C4_6["🎬 178 / 1,051 videos"]
                    C4_7["━━━━━━━━━━━━━━"]
                    C4_8["🟢 완료: 0"]
                    C4_9["🔵 작업중: 3"]
                    C4_10["🟡 검토: 0"]
                    C4_11["⚪ 대기: 20"]
                end
            end
        end
    end

    FilterBar --> CardGrid
    Row1 --> Row2
```

### 2.4 Worker Detail Modal

```mermaid
graph TB
    subgraph Modal["👤 Worker Detail Modal"]
        direction TB

        subgraph ModalHeader["🔝 Modal Header"]
            direction TB
            MH1["👤 김철수"]
            MH2["━━━━━━━━━━━━━━━━━━━━"]
            MH3["📈 Progress: 67%"]
            MH4["██████████████░░░░░░"]
            MH5["🎬 456 / 680 videos completed"]
        end

        subgraph StatusSummary["📊 Status Summary"]
            direction LR
            SS1["🟢 완료<br/>5 tasks"]
            SS2["🔵 작업중<br/>4 tasks"]
            SS3["🟡 검토<br/>2 tasks"]
            SS4["⚪ 대기<br/>1 task"]
        end

        subgraph TaskTable["📋 Task List Table"]
            direction TB
            TH["| Archive | Category | Status | Progress |"]
            T1["| WSOP 2024 | Paradise | 🟢 완료 | 120/120 |"]
            T2["| WSOP 2024 | LA Main | 🔵 작업중 | 85/150 |"]
            T3["| GG Millions | 2024 | 🔵 작업중 | 45/80 |"]
            T4["| WSOP Circuit | LA Clip | 🟡 검토 | 45/50 |"]
            T5["| GOG | Season 12 | ⚪ 대기 | 0/80 |"]
        end

        subgraph ModalFooter["🔽 Modal Footer"]
            MF1["[Close Button]"]
        end
    end

    ModalHeader --> StatusSummary
    StatusSummary --> TaskTable
    TaskTable --> ModalFooter
```

### 2.5 Dashboard - Work Status Summary Card

```mermaid
graph TB
    subgraph Dashboard["🏠 Dashboard Page"]
        direction TB

        subgraph StatsRow["📊 Overview Stats Row"]
            direction LR
            ST1["📁 Files<br/>12,345"]
            ST2["💾 Storage<br/>1.2 TB"]
            ST3["⏱️ Duration<br/>2,450 hrs"]
            ST4["📈 Progress<br/>45%"]
        end

        subgraph WorkStatusSection["📋 Work Status Section ⭐ NEW"]
            direction TB

            subgraph WSHeader["Section Header"]
                WSH1["📋 Work Status"]
                WSH2["[View All →]"]
            end

            subgraph WSContent["Section Content"]
                direction LR

                subgraph SummaryCard["📊 Summary Card"]
                    direction TB
                    SC1["👥 Active Workers"]
                    SC2["4"]
                    SC3["━━━━━━━━━━"]
                    SC4["📋 Total Tasks"]
                    SC5["58"]
                    SC6["━━━━━━━━━━"]
                    SC7["🟢 완료: 14 (24%)"]
                    SC8["🔵 작업중: 17 (29%)"]
                    SC9["🟡 검토: 4 (7%)"]
                    SC10["⚪ 대기: 23 (40%)"]
                end

                subgraph TopWorkersCard["🏆 Top Workers Card"]
                    direction TB
                    TW1["🏆 Top Workers"]
                    TW2["━━━━━━━━━━━━━━"]
                    TW3["1. 🥇 이영희"]
                    TW4["   82% ████████░░"]
                    TW5["━━━━━━━━━━━━━━"]
                    TW6["2. 🥈 김철수"]
                    TW7["   67% ██████░░░░"]
                    TW8["━━━━━━━━━━━━━━"]
                    TW9["3. 🥉 박민수"]
                    TW10["   45% ████░░░░░░"]
                end
            end
        end

        subgraph ActivityRow["📜 Recent Activity Row"]
            direction TB
            AR1["Recent scans and syncs..."]
        end
    end

    StatsRow --> WorkStatusSection
    WSHeader --> WSContent
    WorkStatusSection --> ActivityRow
```

---

## 3. Workflow Design (세로)

### 3.1 Task Status Workflow

```mermaid
graph TB
    subgraph TaskWorkflow["📋 Task Status Workflow"]
        direction TB

        Start(["🆕 Task Created"])

        subgraph Pending["⚪ PENDING"]
            P1["대기 상태"]
            P2["담당자 미배정 가능"]
        end

        subgraph InProgress["🔵 IN PROGRESS"]
            IP1["작업 진행 중"]
            IP2["담당자가 작업 수행"]
            IP3["진행률 업데이트"]
        end

        subgraph Review["🟡 REVIEW"]
            R1["검토 대기"]
            R2["QA/검수 진행"]
        end

        subgraph Completed["🟢 COMPLETED"]
            C1["작업 완료"]
            C2["100% 달성"]
        end

        End(["✅ Done"])

        Start --> Pending
        Pending -->|"작업 시작"| InProgress
        InProgress -->|"검토 요청"| Review
        Review -->|"승인"| Completed
        Review -->|"수정 필요"| InProgress
        Completed --> End
    end
```

### 3.2 Data Sync Workflow

```mermaid
graph TB
    subgraph SyncWorkflow["🔄 Data Sync Workflow"]
        direction TB

        subgraph Trigger["1️⃣ Trigger"]
            TR1["⏰ 30분 자동 동기화"]
            TR2["👆 수동 Sync 버튼"]
        end

        subgraph FetchData["2️⃣ Fetch Data"]
            FD1["Google Sheets API 호출"]
            FD2["Work Status Sheet 읽기"]
            FD3["Raw 데이터 파싱"]
        end

        subgraph ProcessData["3️⃣ Process Data"]
            PD1["헤더 정규화"]
            PD2["상태값 매핑"]
            PD3["숫자 파싱"]
        end

        subgraph SaveData["4️⃣ Save to DB"]
            SD1["기존 레코드 조회"]
            SD2["Upsert 수행"]
            SD3["트랜잭션 커밋"]
        end

        subgraph UpdateUI["5️⃣ Update UI"]
            UI1["Frontend 알림"]
            UI2["데이터 리페치"]
            UI3["UI 갱신"]
        end

        Trigger --> FetchData
        FetchData --> ProcessData
        ProcessData --> SaveData
        SaveData --> UpdateUI
    end
```

### 3.3 User Interaction Workflow

```mermaid
graph TB
    subgraph UserFlow["👤 User Interaction Flow"]
        direction TB

        subgraph Entry["1️⃣ Entry Point"]
            E1["🏠 Dashboard 접속"]
            E2["Work Status 카드 확인"]
        end

        subgraph Navigate["2️⃣ Navigation"]
            N1["'View All' 클릭"]
            N2["또는 Nav에서 Work Status 클릭"]
        end

        subgraph WorkStatusView["3️⃣ Work Status Page"]
            WS1["Workers 탭 (기본)"]
            WS2["작업자 카드 목록 확인"]
        end

        subgraph SelectWorker["4️⃣ Worker Selection"]
            SW1["작업자 카드 클릭"]
            SW2["상세 모달 오픈"]
        end

        subgraph ViewDetails["5️⃣ View Details"]
            VD1["작업자 전체 진행률"]
            VD2["담당 Task 목록"]
            VD3["상태별 breakdown"]
        end

        subgraph Actions["6️⃣ Actions"]
            A1["🔄 Sync 트리거"]
            A2["📤 CSV Export"]
            A3["🔍 필터/정렬"]
        end

        Entry --> Navigate
        Navigate --> WorkStatusView
        WorkStatusView --> SelectWorker
        SelectWorker --> ViewDetails
        ViewDetails --> Actions
    end
```

---

## 4. Component Architecture (세로)

### 4.1 Component Hierarchy

```mermaid
graph TB
    subgraph ComponentTree["🌳 Component Hierarchy"]
        direction TB

        subgraph AppLevel["App Level"]
            App["App.tsx"]
        end

        subgraph RouterLevel["Router Level"]
            Router["React Router"]
        end

        subgraph PageLevel["Page Level"]
            Dashboard["Dashboard.tsx"]
            WorkStatus["WorkStatus.tsx"]
        end

        subgraph DashboardComponents["Dashboard Components"]
            direction TB
            StatCards["StatCards"]
            WSS["WorkStatusSummary ⭐"]
            TopWorkers["TopWorkers ⭐"]
            RecentActivity["RecentActivity"]
        end

        subgraph WorkStatusComponents["WorkStatus Components"]
            direction TB
            SyncIndicator["SyncStatusIndicator"]
            TabNav["TabNavigation"]
            WorkerCards["WorkerCard[]"]
            TasksTable["TasksTable"]
            WorkerModal["WorkerDetailModal"]
        end

        subgraph SharedComponents["Shared Components"]
            direction TB
            ProgressBar["ProgressBar"]
            StatusBadge["StatusBadge"]
            LoadingSpinner["LoadingSpinner"]
        end

        App --> Router
        Router --> PageLevel
        Dashboard --> DashboardComponents
        WorkStatus --> WorkStatusComponents
        DashboardComponents --> SharedComponents
        WorkStatusComponents --> SharedComponents
    end
```

### 4.2 Data Flow Architecture

```mermaid
graph TB
    subgraph DataFlow["📊 Data Flow"]
        direction TB

        subgraph ExternalSources["External Sources"]
            GS["📗 Google Sheets"]
        end

        subgraph Backend["Backend (FastAPI)"]
            direction TB

            subgraph SyncService["Sync Service"]
                SS1["archiving_status_sync.py"]
                SS2["30분 주기 동기화"]
            end

            subgraph Database["SQLite Database"]
                DB1["work_statuses table"]
                DB2["archives table"]
            end

            subgraph APIRoutes["API Routes"]
                AR1["/api/archiving-status"]
                AR2["/api/worker-stats"]
                AR3["/api/sync"]
            end
        end

        subgraph Frontend["Frontend (React)"]
            direction TB

            subgraph APIClient["API Client"]
                AC1["api.ts"]
                AC2["React Query"]
            end

            subgraph State["State Management"]
                ST1["Query Cache"]
                ST2["Local State"]
            end

            subgraph UI["UI Components"]
                UI1["Dashboard"]
                UI2["WorkStatus"]
            end
        end

        GS -->|"Fetch"| SyncService
        SyncService -->|"Upsert"| Database
        Database -->|"Query"| APIRoutes
        APIRoutes -->|"JSON"| APIClient
        APIClient -->|"Cache"| State
        State -->|"Render"| UI
    end
```

---

## 5. Block Agent Design

### 5.1 Domain Separation

```mermaid
graph TB
    subgraph BlockSystem["🧱 Block Agent System"]
        direction TB

        subgraph ArchivingBlock["Block: archiving.status"]
            direction TB

            subgraph BackendFiles["Backend Files"]
                B1["api/archiving_status.py"]
                B2["api/worker_stats.py"]
                B3["services/archiving_status_sync.py"]
                B4["models/archiving_status.py"]
                B5["schemas/work_status.py"]
            end

            subgraph FrontendFiles["Frontend Files"]
                F1["pages/WorkStatus.tsx"]
                F2["components/WorkerCard.tsx"]
                F3["components/WorkerDetailModal.tsx"]
                F4["components/WorkStatusSummary.tsx"]
                F5["components/TopWorkers.tsx"]
            end

            subgraph SharedFiles["Shared Files"]
                S1["types/archiving.ts"]
                S2["api.ts (archiving section)"]
            end
        end

        subgraph RelatedBlocks["Related Blocks"]
            RB1["sync.sheets"]
            RB2["progress"]
            RB3["scanner"]
        end

        BackendFiles --> SharedFiles
        FrontendFiles --> SharedFiles
        ArchivingBlock -.->|"depends on"| RelatedBlocks
    end
```

### 5.2 Agent Specification

```yaml
# .claude/agents/archiving-status.md

name: archiving-status
description: 아카이빙 작업 현황 관리 전담 에이전트

responsibilities:
  - Work Status UI 구현 및 유지보수
  - Worker Stats 집계 및 표시
  - Google Sheets 동기화 상태 관리
  - Dashboard Work Status 카드

files:
  backend:
    - backend/app/api/archiving_status.py
    - backend/app/api/worker_stats.py
    - backend/app/services/archiving_status_sync.py
    - backend/app/models/archiving_status.py
    - backend/app/schemas/work_status.py
  frontend:
    - frontend/src/pages/WorkStatus.tsx
    - frontend/src/components/WorkerCard.tsx
    - frontend/src/components/WorkStatusSummary.tsx
    - frontend/src/types/archiving.ts

api_endpoints:
  - GET /api/archiving-status
  - GET /api/worker-stats
  - GET /api/worker-stats/{pic}
  - GET /api/sync/status
  - POST /api/sync/trigger

related_blocks:
  - sync.sheets (동기화 서비스)
  - progress (진행률 계산)
```

---

## 6. Implementation Plan

### 6.1 Phase Overview

```mermaid
graph TB
    subgraph ImplementationPhases["📅 Implementation Phases"]
        direction TB

        subgraph Phase1["Phase 1: API Migration"]
            P1_1["Config 업데이트"]
            P1_2["API 라우터 등록"]
            P1_3["Frontend API 클라이언트"]
        end

        subgraph Phase2["Phase 2: Dashboard Integration"]
            P2_1["WorkStatusSummary 컴포넌트"]
            P2_2["TopWorkers 컴포넌트"]
            P2_3["Dashboard 통합"]
        end

        subgraph Phase3["Phase 3: Work Status Enhancement"]
            P3_1["Workers 탭 기본 설정"]
            P3_2["WorkerCard 개선"]
            P3_3["상태별 breakdown 강조"]
        end

        subgraph Phase4["Phase 4: Testing & Polish"]
            P4_1["E2E 테스트"]
            P4_2["반응형 디자인"]
            P4_3["성능 최적화"]
        end

        Phase1 --> Phase2
        Phase2 --> Phase3
        Phase3 --> Phase4
    end
```

### 6.2 Detailed Tasks

| Phase | Task | File | Description |
|-------|------|------|-------------|
| 1 | Config | `config.py` | `ARCHIVING_STATUS_SHEET_URL` 추가 |
| 1 | API Route | `api/__init__.py` | `/archiving-status` 라우터 등록 |
| 1 | Frontend API | `api.ts` | `archivingStatusApi` 추가 |
| 2 | Summary Card | `WorkStatusSummary.tsx` | 대시보드용 요약 카드 |
| 2 | Top Workers | `TopWorkers.tsx` | 상위 작업자 랭킹 |
| 2 | Dashboard | `Dashboard.tsx` | 새 컴포넌트 통합 |
| 3 | Default Tab | `WorkStatus.tsx` | Workers 탭 기본 |
| 3 | Worker Card | `WorkerCard.tsx` | 상태 breakdown 개선 |

---

## 7. API Specification

### 7.1 Archiving Status API

```typescript
// GET /api/archiving-status
interface ArchivingStatusListResponse {
  items: ArchivingStatus[];
  total_count: number;
  total_videos: number;
  total_done: number;
  overall_progress: number;
}

interface ArchivingStatus {
  id: number;
  archive_id: number;
  archive_name: string | null;
  category: string;
  pic: string | null;           // Person In Charge
  status: 'pending' | 'in_progress' | 'review' | 'completed';
  total_videos: number;
  excel_done: number;
  progress_percent: number;
  notes1: string | null;
  notes2: string | null;
}
```

### 7.2 Worker Stats API

```typescript
// GET /api/worker-stats
interface WorkerStatsResponse {
  workers: WorkerStats[];
  summary: {
    total_workers: number;
    active_workers: number;
    total_tasks: number;
    status_breakdown: Record<string, number>;
  };
}

interface WorkerStats {
  pic: string;
  task_count: number;
  total_videos: number;
  total_done: number;
  progress_percent: number;
  archives: string[];
  status_breakdown: {
    pending: number;
    in_progress: number;
    review: number;
    completed: number;
  };
}
```

---

## 8. File Changes Summary

### 8.1 New Files

| File | Description |
|------|-------------|
| `frontend/src/components/WorkStatusSummary.tsx` | 대시보드용 작업 현황 요약 |
| `frontend/src/components/TopWorkers.tsx` | 상위 작업자 랭킹 |
| `frontend/src/types/archiving.ts` | Archiving 관련 타입 정의 |
| `.claude/agents/archiving-status.md` | 전담 에이전트 정의 |

### 8.2 Modified Files

| File | Change |
|------|--------|
| `frontend/src/services/api.ts` | `archivingStatusApi` 추가 |
| `frontend/src/pages/Dashboard.tsx` | WorkStatusSummary 통합 |
| `frontend/src/pages/WorkStatus.tsx` | Workers 탭 기본 설정 |
| `backend/app/api/__init__.py` | archiving_status 라우터 |

---

## 9. Success Metrics

| Metric | Target |
|--------|--------|
| API Migration | 100% deprecated API 제거 |
| Dashboard Integration | Work Status 카드 표시 |
| Workers View | 기본 탭으로 설정 |
| Block Agent | archiving-status 에이전트 정의 완료 |

---

## 10. Related Documents

- [Issue #37](https://github.com/garimto81/archive_statistics/issues/37) - 이름 변경
- [Issue #40](https://github.com/garimto81/archive_statistics/issues/40) - 본 이슈
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 시스템 구조
- [BLOCK_AGENT_SYSTEM.md](./BLOCK_AGENT_SYSTEM.md) - Block Agent 시스템
