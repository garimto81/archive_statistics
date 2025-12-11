# Dashboard 리팩토링 개발 계획서

**작성일**: 2025-12-09
**버전**: 2.0
**상태**: 🔄 Planning (Phase 2 - Folder Tree + Progress Integration)

---

## 1. 목표

### 1.1 요구사항

| 항목 | 설명 |
|------|------|
| **archive db** (Work Status) | 데이터 그대로 표시 |
| **metadata db** (Hand Analysis) | 마킹하여 구분 표시 (데이터 소스 식별) |
| **목적** | 각 데이터 소스별 수집 현황 확인 가능 |

### 1.2 UI 변경사항

| 현재 | 변경 후 |
|------|---------|
| File Type Distribution (Pie Chart) | ❌ 삭제 |
| Top Folders by Size | ❌ 삭제 |
| Storage Growth Trend (Line Chart) | ❌ 삭제 |
| Folder Tree (1/3) | ✅ 유지 |
| Stats Cards (4개) | ✅ 유지 |
| - | ✅ Data Source Status Panel 추가 |
| - | ✅ Work Status Summary 추가 |

---

## 2. 데이터 소스별 표시 방안

### 2.1 archive db (Work Status)

```
┌─────────────────────────────────────────────────────────────┐
│  📊 Work Status                             [archive db]    │
├─────────────────────────────────────────────────────────────┤
│  Overall Progress: ████████████░░░░░░░░ 63.5%               │
│                                                             │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │ Total       │ Completed   │ In Progress │ Pending     │  │
│  │ 11 tasks    │ 4           │ 5           │ 2           │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
│                                                             │
│  Last Sync: 08:03:01  |  11 records synced                  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 metadata db (Hand Analysis) - 마킹 표시

```
┌─────────────────────────────────────────────────────────────┐
│  🃏 Hand Analysis                          [metadata db]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ Worksheet Breakdown ────────────────────────────────┐   │
│  │                                                      │   │
│  │  2023 WSOP Paradise     ████████████████████░ 44     │   │
│  │  2024 WSOPC LA          ███████████████░░░░░░ 38     │   │
│  │  2025 WSOPSC CYPRUS     ████████████░░░░░░░░░ 30     │   │
│  │  2025 WSOP Las Vegas    ████████░░░░░░░░░░░░░ 21     │   │
│  │  MPP                    ██████░░░░░░░░░░░░░░░ 17     │   │
│  │  PAD S12,13             ███░░░░░░░░░░░░░░░░░░  8     │   │
│  │  WSOPE 2008-2013        ███░░░░░░░░░░░░░░░░░░  8     │   │
│  │  WSOPE 2024             █░░░░░░░░░░░░░░░░░░░░  1     │   │
│  │                                                      │   │
│  │  Total: 167 hands  |  8 worksheets                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Last Sync: 08:03:05  |  167 created, 22 updated            │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Data Source Status Panel

```
┌─────────────────────────────────────────────────────────────┐
│  📡 Data Sources                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ archive db ─────────────────────────────────────────┐   │
│  │  ✅ Connected   |  Work Status                        │   │
│  │  Last: 08:03:01  |  Next: 08:33:01  |  11 records     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─ metadata db ────────────────────────────────────────┐   │
│  │  ✅ Connected   |  Hand Analysis                      │   │
│  │  Last: 08:03:05  |  Next: 08:33:01  |  167 records    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─ iconik db ──────────────────────────────────────────┐   │
│  │  ⏸️ Disabled    |  MAM Metadata                       │   │
│  │  Not implemented                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 코드 구조 분석

### 3.1 현재 블럭화 상태

| 블럭 | 서비스 파일 | API 파일 | 모델 파일 |
|------|-------------|----------|-----------|
| `sync.sheets` | sheets_sync.py | sync.py | work_status.py |
| `sync.hands` | hand_analysis_sync.py | hands.py | hand_analysis.py |

### 3.2 중복 코드 분석

#### 🔄 추출 가능한 공통 코드

```python
# 제안: backend/app/services/base_sync.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class BaseSyncResult:
    """동기화 결과 기본 클래스"""
    success: bool
    synced_at: datetime
    total_records: int
    synced_count: int
    created_count: int = 0
    updated_count: int = 0
    error: Optional[str] = None
    details: List[str] = field(default_factory=list)


class BaseSyncService:
    """동기화 서비스 기본 클래스"""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._client: Optional[gspread.Client] = None
        self.last_sync_time: Optional[datetime] = None
        self.last_sync_result: Optional[BaseSyncResult] = None
        self.last_error: Optional[str] = None
        self.status: str = "idle"
        self._is_started: bool = False

    def _get_client(self) -> gspread.Client:
        """Google Sheets 클라이언트 (공통)"""
        # ... 공통 로직 ...

    def get_status_dict(self) -> Dict[str, Any]:
        """상태 딕셔너리 (공통)"""
        # ... 공통 로직 ...
```

#### ❌ 현재 결정: 리팩토링 보류

**이유**:
1. 두 서비스가 이미 안정적으로 동작 중
2. 파싱 로직이 각각 고유함 (Work Status vs Hand Analysis)
3. 과도한 추상화는 유지보수 복잡도 증가
4. 현재 중복 코드량이 크리티컬하지 않음 (~50줄)

**향후**: 3번째 시트 추가 시 리팩토링 고려

### 3.3 재사용 가능한 컴포넌트 (Frontend)

| 컴포넌트 | 위치 | 재사용 가능 |
|----------|------|-------------|
| `SyncStatusIndicator` | WorkStatus.tsx | ✅ 추출 → 공통 컴포넌트 |
| `StatCard` | components/StatCard.tsx | ✅ 이미 공통 |
| `FolderTree` | components/FolderTree.tsx | ✅ 이미 공통 |
| Progress Bar | WorkStatus.tsx 내부 | ✅ 추출 가능 |

---

## 4. 구현 계획

### 4.1 Phase 1: Backend API 확장 (0.5일)

#### 4.1.1 통합 데이터 소스 상태 API

```python
# backend/app/api/data_sources.py

@router.get("/status")
async def get_all_data_sources():
    """모든 데이터 소스 상태 조회"""
    return {
        "archive_db": {
            "name": "archive db",
            "type": "Work Status",
            "enabled": sheets_sync_service.is_enabled,
            "status": sheets_sync_service.status,
            "last_sync": sheets_sync_service.last_sync_time,
            "record_count": sheets_sync_service.last_sync_result.synced_count if sheets_sync_service.last_sync_result else 0,
        },
        "metadata_db": {
            "name": "metadata db",
            "type": "Hand Analysis",
            "enabled": hand_analysis_sync_service.is_enabled,
            "status": hand_analysis_sync_service.status,
            "last_sync": hand_analysis_sync_service.last_sync_time,
            "record_count": hand_analysis_sync_service.last_sync_result.synced_count if hand_analysis_sync_service.last_sync_result else 0,
            "worksheets": hand_analysis_sync_service.last_sync_result.worksheets_processed if hand_analysis_sync_service.last_sync_result else 0,
        },
        "iconik_db": {
            "name": "iconik db",
            "type": "MAM Metadata",
            "enabled": False,
            "status": "disabled",
            "last_sync": None,
            "record_count": 0,
        }
    }
```

### 4.2 Phase 2: Frontend 컴포넌트 개발 (1일)

#### 4.2.1 새 컴포넌트 목록

| 컴포넌트 | 파일 | 역할 |
|----------|------|------|
| `DataSourceStatus` | components/DataSourceStatus.tsx | 데이터 소스 연결 상태 표시 |
| `WorkStatusSummary` | components/WorkStatusSummary.tsx | Work Status 요약 (Dashboard용) |
| `HandAnalysisSummary` | components/HandAnalysisSummary.tsx | Hand Analysis 요약 + 마킹 |
| `SyncStatusBadge` | components/SyncStatusBadge.tsx | 동기화 상태 배지 (공통) |

#### 4.2.2 SyncStatusBadge (공통 컴포넌트)

```tsx
// components/SyncStatusBadge.tsx

interface SyncStatusBadgeProps {
  source: 'archive_db' | 'metadata_db' | 'iconik_db';
  label: string;
  enabled: boolean;
  status: string;
  lastSync?: string;
  recordCount?: number;
}

export function SyncStatusBadge({ source, label, enabled, status, lastSync, recordCount }: SyncStatusBadgeProps) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-lg border">
      {/* Status Icon */}
      {enabled ? (
        status === 'syncing' ? <Spinner /> : <CheckCircle className="text-green-500" />
      ) : (
        <PauseCircle className="text-gray-400" />
      )}

      {/* Label with Source Badge */}
      <span className="text-sm font-medium">{label}</span>
      <span className={`text-xs px-1.5 py-0.5 rounded ${
        source === 'archive_db' ? 'bg-blue-100 text-blue-700' :
        source === 'metadata_db' ? 'bg-purple-100 text-purple-700' :
        'bg-gray-100 text-gray-500'
      }`}>
        {source}
      </span>

      {/* Record Count */}
      {recordCount !== undefined && (
        <span className="text-xs text-gray-500">{recordCount} records</span>
      )}
    </div>
  );
}
```

### 4.3 Phase 3: Dashboard 수정 (0.5일)

#### 4.3.1 Dashboard.tsx 변경사항

```tsx
// 삭제할 섹션
- File Type Distribution (Pie Chart)
- Top Folders by Size
- Storage Growth Trend (Line Chart)

// 추가할 섹션
+ DataSourceStatus panel
+ WorkStatusSummary
+ HandAnalysisSummary (with worksheet breakdown)
```

#### 4.3.2 새 레이아웃

```
┌─────────────────────────────────────────────────────────────────┐
│                    Stats Cards (4개) - 유지                      │
├─────────────────┬───────────────────────────────────────────────┤
│                 │                                               │
│  Folder Tree    │  ┌─ Data Sources ──────────────────────────┐  │
│  (폴더 탐색)    │  │  ✅ archive db  |  ✅ metadata db  |  ⏸️  │  │
│                 │  └─────────────────────────────────────────┘  │
│                 │                                               │
│                 │  ┌─ Work Status Summary ────────────────────┐  │
│                 │  │  [archive db] 11 tasks | 63.5% complete  │  │
│                 │  └─────────────────────────────────────────┘  │
│                 │                                               │
│                 │  ┌─ Hand Analysis ─────────────────────────┐  │
│                 │  │  [metadata db] 167 hands | 8 worksheets │  │
│                 │  │  - 2023 WSOP Paradise: 44               │  │
│                 │  │  - 2024 WSOPC LA: 38                    │  │
│                 │  │  - ...                                  │  │
│                 │  └─────────────────────────────────────────┘  │
│                 │                                               │
└─────────────────┴───────────────────────────────────────────────┘
```

---

## 5. 파일 변경 목록

### 5.1 Backend (신규/수정)

| 파일 | 작업 | 설명 |
|------|------|------|
| `api/data_sources.py` | 신규 | 통합 데이터 소스 API |
| `api/__init__.py` | 수정 | 라우터 등록 |

### 5.2 Frontend (신규/수정)

| 파일 | 작업 | 설명 |
|------|------|------|
| `components/DataSourceStatus.tsx` | 신규 | 데이터 소스 상태 패널 |
| `components/WorkStatusSummary.tsx` | 신규 | Work Status 요약 |
| `components/HandAnalysisSummary.tsx` | 신규 | Hand Analysis 요약 |
| `components/SyncStatusBadge.tsx` | 신규 | 동기화 상태 배지 |
| `pages/Dashboard.tsx` | 수정 | 레이아웃 변경 |
| `services/api.ts` | 수정 | 신규 API 연동 |

### 5.3 문서

| 파일 | 작업 |
|------|------|
| `docs/SHEETS_SOLUTION_DESIGN.md` | 업데이트 완료 |
| `docs/DASHBOARD_REFACTOR_PLAN.md` | 신규 (본 문서) |

---

## 6. 예상 일정

| Phase | 작업 | 예상 시간 |
|-------|------|----------|
| 1 | Backend API 확장 | 0.5일 |
| 2 | Frontend 컴포넌트 개발 | 1일 |
| 3 | Dashboard 수정 | 0.5일 |
| 4 | 테스트 및 검증 | 0.5일 |
| **총계** | | **2.5일** |

---

## 7. 리스크 및 완화 방안

| 리스크 | 영향 | 완화 방안 |
|--------|------|----------|
| API 응답 속도 | Medium | 캐싱 적용 (React Query) |
| 동시 동기화 충돌 | Low | status 체크 로직 이미 있음 |
| 컴포넌트 재사용성 | Low | props 인터페이스 설계 주의 |

---

## 8. 체크리스트

### 8.1 코드 품질

- [x] 중복 코드 최소화
- [x] 컴포넌트 재사용성 확보
- [x] TypeScript 타입 정의
- [x] 에러 처리

### 8.2 블럭화 규칙 준수

- [x] 블럭 헤더 주석 추가
- [x] 단일 책임 원칙
- [x] 의존성 명시

### 8.3 테스트

- [x] API 엔드포인트 테스트
- [ ] 컴포넌트 렌더링 테스트
- [ ] 동기화 상태 시나리오 테스트

---

## 9. 구현 결과

### 9.1 생성된 파일

| 파일 | 역할 |
|------|------|
| `backend/app/api/data_sources.py` | 통합 Data Sources API |
| `frontend/src/components/SyncStatusBadge.tsx` | 동기화 상태 배지 (공통) |
| `frontend/src/components/DataSourceStatus.tsx` | Data Sources 패널 |
| `frontend/src/components/WorkStatusSummary.tsx` | Work Status 요약 |
| `frontend/src/components/HandAnalysisSummary.tsx` | Hand Analysis 요약 |

### 9.2 수정된 파일

| 파일 | 변경 내용 |
|------|----------|
| `backend/app/api/__init__.py` | data_sources 라우터 등록 |
| `frontend/src/types/index.ts` | Data Sources 타입 추가 |
| `frontend/src/services/api.ts` | dataSourcesApi 추가 |
| `frontend/src/pages/Dashboard.tsx` | 차트 제거, Data Sources 패널 추가 |

### 9.3 API 엔드포인트

| Endpoint | 응답 |
|----------|------|
| `GET /api/data-sources/status` | 모든 데이터 소스 상태 (archive_db, metadata_db, iconik_db) |
| `GET /api/data-sources/work-status/summary` | Work Status 요약 (11 tasks) |
| `GET /api/data-sources/hand-analysis/summary` | Hand Analysis 요약 (176 hands, 8 worksheets) |

### 9.4 접속 주소

- Frontend: http://localhost:8082
- Backend API: http://localhost:8002/api

---

## 10. Phase 2: Folder Tree + Progress Integration (간트차트 형태)

### 10.1 새로운 요구사항

| 항목 | 설명 |
|------|------|
| **통합 뷰** | metadata db와 archive db를 Folder Tree 내에 통합 표시 |
| **간트차트 형태** | 각 폴더/파일별 작업 진행률을 타임라인 바로 표시 |
| **직관적 이해** | 관리자가 폴더를 보면서 각 프로젝트 작업 현황을 한눈에 파악 |
| **중복 작업 표시** | 동일 파일에 metadata db와 archive db 작업이 중복될 수 있음 |

### 10.2 데이터 매칭 로직 (Bottom-Up, 파일 기반)

> **핵심 원칙**: 폴더 매칭 삭제. 반드시 **파일 단위 매칭** 후 상위 폴더로 집계.

#### 10.2.1 데이터 소스별 매칭 키

| 데이터 소스 | 매칭 키 | 설명 |
|------------|---------|------|
| **NAS (file_stats)** | `name` (파일명) | NAS 스캔 결과, `duration` 포함 |
| **metadata db (hand_analyses)** | `file_name` (비디오 제목) | 파일명과 유사도 매칭 필요 |
| **archive db (work_statuses)** | - | 폴더 단위 매칭 삭제, 직접 사용 안함 |

#### 10.2.2 매칭 관계 (Bottom-Up)

```
Step 1: 파일 단위 매칭 (핵심)
────────────────────────────────────────────────────────────
file_stats.name (실제 파일명)
    ↓ FUZZY MATCH
hand_analyses.file_name (비디오 제목)
    ↓
progress = max(timecode_out_sec) / file_stats.duration * 100

예시:
- NAS 파일: "WSOP_Paradise_Final_Table.mp4"
- Hand Analysis: "WSOP Paradise $1,500 Mystery Millions (Final Table)"
- 매칭 로직: 키워드 추출 → "WSOP", "Paradise", "Final", "Table" 공통

Step 2: 폴더로 집계 (Aggregation)
────────────────────────────────────────────────────────────
folder_stats
    ↓ GROUP BY folder_path
    ├── 매칭된 파일 수 (files_with_hands)
    ├── 총 핸드 수 (sum of hand_count)
    ├── 평균 진행률 (avg of progress_percent)
    └── 완료 파일 수 (progress >= 90%)

Step 3: 계층 구조로 전파 (Propagation)
────────────────────────────────────────────────────────────
/ARCHIVE/WSOP/2024_WSOPC_LA/
    ↓ 하위 파일들의 집계 결과
    └── 진행률, 핸드 수, 완료율 표시
```

#### 10.2.3 파일명-비디오제목 매칭 알고리즘

```python
def match_file_to_hand_analysis(file_name: str, hand_file_names: List[str]) -> Optional[str]:
    """
    NAS 파일명과 Hand Analysis의 file_name(비디오 제목) 매칭

    매칭 전략 (우선순위):
    1. 정확 일치 (확장자 제외)
    2. 정규화 후 일치 (특수문자, 공백 제거)
    3. 키워드 유사도 매칭 (70% 이상)
    """
    # 1. 확장자 제거
    base_name = os.path.splitext(file_name)[0]

    # 2. 정규화: 소문자, 특수문자→공백, 연속 공백 제거
    normalized = normalize(base_name)

    # 3. 각 hand file_name과 비교
    for hand_title in hand_file_names:
        hand_normalized = normalize(hand_title)

        # 정확 일치
        if normalized == hand_normalized:
            return hand_title

        # 키워드 교집합 비율
        file_keywords = set(normalized.split())
        hand_keywords = set(hand_normalized.split())

        if len(file_keywords) > 0 and len(hand_keywords) > 0:
            intersection = file_keywords & hand_keywords
            similarity = len(intersection) / min(len(file_keywords), len(hand_keywords))
            if similarity >= 0.7:
                return hand_title

    return None
```

#### 10.2.4 매칭 예시

| NAS 파일명 | Hand Analysis file_name | 매칭 결과 |
|-----------|-------------------------|----------|
| `WSOP_Paradise_Final_Table.mp4` | `WSOP Paradise $1,500 Mystery Millions (Final Table)` | ✅ 키워드: Paradise, Final, Table |
| `MPP_Cyprus_Day1.mov` | `MPP` | ✅ 키워드: MPP |
| `PAD_S12_E01.mp4` | `PAD S12,13` | ✅ 키워드: PAD, S12 |
| `random_video.mp4` | - | ❌ 매칭 없음 |

### 10.3 UI 목업: 간트차트 형태 Folder Tree

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  📁 Folder Structure + Work Progress                                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ▼ 📁 WSOP                                              [archive] 63.5%         │
│  │   Progress: ██████████████░░░░░░░░░░░░░░░░░░░ 63.5%                          │
│  │   ├─ Total: 11 tasks | Done: 7 | In Progress: 4                              │
│  │                                                                               │
│  │   ▼ 📁 2024 WSOPC LA                                 [metadata] 38 hands     │
│  │   │   Duration: 45:30:00 total                                               │
│  │   │                                                                           │
│  │   │   📄 WSOP_LA_Day1_01.mp4                         02:15:30                │
│  │   │   ├─ [metadata] ████████████████████░░░░░░░░░░  85%  (01:55:00)         │
│  │   │   └─ [archive]  ──────────────|──────────────   @ 85% marker             │
│  │   │                                                                           │
│  │   │   📄 WSOP_LA_Day1_02.mp4                         01:45:20                │
│  │   │   ├─ [metadata] ██████████████░░░░░░░░░░░░░░░░  60%  (01:02:00)         │
│  │   │   └─ [archive]  ────────|─────────────────────   @ 60% marker             │
│  │   │                                                                           │
│  │   │   📄 WSOP_LA_Day2_01.mp4                         02:30:00                │
│  │   │   └─ [metadata] ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  0%   (no data)          │
│  │   │                                                                           │
│  │   └─ 📁 Clips                                                                 │
│  │       └─ 📄 highlight_01.mp4                         00:05:30                │
│  │           └─ [metadata] ████████████████████████████ 100% ✓                  │
│  │                                                                               │
│  │   ▶ 📁 2023 WSOP Paradise                           [metadata] 44 hands      │
│  │   ▶ 📁 WSOPE 2024                                   [metadata] 1 hand        │
│  │                                                                               │
│  └─ ▶ 📁 HCL                                           [archive] 45.2%          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 10.4 진행률 표시 방식

#### 10.4.1 metadata db (Hand Analysis)

```
[metadata] ██████████████░░░░░░░░░░░░░░░░░░  60%  (01:02:00)
           ▲                                       ▲
           │                                       │
           채워진 바 (max(timecode_out_sec) / file_duration * 100)
                                                   │
                                        마지막 타임코드 위치
```

- **계산식**: `progress = max(timecode_out_sec) / file_duration * 100`
- **완료 조건**: `progress >= 90%` → 작업 완료로 판단

#### 10.4.2 archive db (Work Status)

```
[archive]  ────────────────|──────────────────────  @ 60% marker
                           ▲
                           │
                 timecode_out 위치를 세로선(|)으로 표시
```

- **표시 방식**: metadata db와 같은 파일에서, archive db의 out_time 위치를 세로 마커로 표시
- **의미**: 동일 파일에서 두 데이터 소스의 작업 진행 상태를 동시 확인 가능

### 10.5 데이터 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│                      Backend API                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  GET /api/folders/tree-with-progress                             │
│                                                                  │
│  Response:                                                       │
│  {                                                               │
│    "folders": [{                                                 │
│      "id": 1,                                                    │
│      "name": "WSOP",                                             │
│      "path": "/ARCHIVE/WSOP",                                    │
│      "size_formatted": "1.2 TB",                                 │
│      "duration": 163800,  // 45:30:00 in seconds                 │
│                                                                  │
│      // Work Status (archive db)                                 │
│      "work_status": {                                            │
│        "total_tasks": 11,                                        │
│        "completed": 7,                                           │
│        "progress_percent": 63.5                                  │
│      },                                                          │
│                                                                  │
│      // Hand Analysis (metadata db)                              │
│      "hand_analysis": {                                          │
│        "total_hands": 38,                                        │
│        "max_timecode_sec": 5700,  // 01:35:00                    │
│        "progress_percent": 85                                    │
│      },                                                          │
│                                                                  │
│      "children": [...]                                           │
│    }]                                                            │
│  }                                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.6 블록화 설계

#### 10.6.1 도메인 블록 구조

| Domain | Block | 책임 |
|--------|-------|------|
| **Progress** | `progress.folder` | 폴더별 통합 진행률 조회 |
| **Progress** | `progress.file` | 파일별 진행률 계산 |
| **Progress** | `progress.matching` | NAS ↔ metadata/archive 매칭 |

#### 10.6.2 신규 파일 구조

```
backend/app/
├── api/
│   └── progress.py          # Block: api.progress
├── services/
│   └── progress_service.py  # Block: progress.service
└── schemas/
    └── progress.py          # Block: schemas.progress

frontend/src/
├── components/
│   ├── FolderTreeWithProgress.tsx   # Block: components.folder-progress
│   └── ProgressBar.tsx              # Block: components.progress-bar
└── pages/
    └── Dashboard.tsx                # 수정
```

#### 10.6.3 Agent Rules

```markdown
# backend/app/services/AGENT_RULES.md (추가)

## Block: progress.service

### 책임
- NAS 파일과 metadata db/archive db 매칭
- 폴더/파일별 진행률 계산
- 캐싱 및 성능 최적화

### 의존성
- file_stats (NAS 스캔 결과)
- hand_analyses (metadata db)
- work_statuses (archive db)

### 매칭 로직
1. file_stats.name ↔ hand_analyses.file_name (파일명 매칭)
2. folder_stats.name ↔ work_statuses.category (폴더/카테고리 매칭)

### 진행률 계산
- metadata: max(timecode_out_sec) / file_duration * 100
- archive: work_status.progress_percent (시트에서 직접 가져옴)
```

### 10.7 구현 계획 (Phase 2)

| Step | 작업 | 상세 |
|------|------|------|
| 2.1 | Backend: Progress API | `/api/folders/tree-with-progress` 엔드포인트 |
| 2.2 | Backend: Matching Service | NAS ↔ metadata/archive 매칭 로직 |
| 2.3 | Frontend: FolderTreeWithProgress | 간트차트 형태 트리 컴포넌트 |
| 2.4 | Frontend: ProgressBar | metadata/archive 이중 진행률 표시 |
| 2.5 | Dashboard 통합 | 기존 FolderTree → FolderTreeWithProgress 교체 |
| 2.6 | 테스트 및 검증 | 매칭 정확도, UI 렌더링 테스트 |

### 10.8 예상 일정 (Phase 2)

| Step | 예상 시간 |
|------|----------|
| 2.1 Backend API | 0.5일 |
| 2.2 Matching Service | 0.5일 |
| 2.3 FolderTreeWithProgress | 1일 |
| 2.4 ProgressBar | 0.5일 |
| 2.5 Dashboard 통합 | 0.25일 |
| 2.6 테스트 | 0.25일 |
| **총계** | **3일** |

### 10.9 리스크 및 완화

| 리스크 | 영향 | 완화 방안 |
|--------|------|----------|
| 파일명 매칭 실패 | High | fuzzy matching, 정규화 로직 추가 |
| 대용량 폴더 성능 | Medium | 페이징, 가상화, 캐싱 |
| 중복 데이터 처리 | Low | metadata 우선, archive 마커 표시 |
