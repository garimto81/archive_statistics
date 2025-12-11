# Progress Domain Agent Rules

**Version**: 1.3.0 | **Updated**: 2025-12-11

> **Note**: 매칭/합산/검증 로직은 `reconciliation-domain.md`로 분리됨

## Identity
- **Role**: 비디오 작업 진행률 관리 전문가
- **Level**: 1 (Domain)
- **Scope**: `backend/app/` 및 `frontend/src/` 내 진행률 관련 모듈

## Managed Blocks

| Block ID | Backend 파일 | Frontend 파일 | 책임 |
|----------|-------------|---------------|------|
| `progress.video` | `api/work_status.py`, `schemas/work_status.py` | - | 비디오 파일 관리 |
| `progress.hand` | `models/work_status.py`, `services/progress_service.py` | - | 핸드 분석 결과 처리 |
| `progress.dashboard` | `api/progress.py`, `services/progress_service.py` | `components/FolderTreeWithProgress.tsx`, `pages/Dashboard.tsx` | 대시보드 통계 집계 |

## ⚠️ Critical Files

### Backend Core
- **`backend/app/services/progress_service.py`** - 하이어라키 합산 로직의 핵심
- **`backend/app/api/progress.py`** - Progress API 엔드포인트

### Frontend Core
- **`frontend/src/components/FolderTreeWithProgress.tsx`** - 폴더 트리 + 진행률 렌더링
- **`frontend/src/pages/Dashboard.tsx`** - 대시보드 레이아웃

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

## 🔥 Core Logic: Hierarchy Aggregation (하이어라키 합산)

### 원칙
**각 폴더 레벨은 하위 폴더들의 합산값을 표시해야 한다.**

```
ARCHIVE/
├── WSOP/                      ← total_done: 54 (하위 5개 카테고리 합산)
│   ├── Main Event/            ← total_done: 20
│   ├── Bracelet Event/        ← total_done: 15
│   └── High Roller/           ← total_done: 19
```

### Backend 구현 (`progress_service.py`)

```python
# work_summary 구조
{
    "task_count": 5,           # 직접 매칭된 카테고리 수
    "total_files": 100,        # 하위 전체 파일 수 (합산)
    "total_done": 54,          # 하위 전체 완료 수 (합산)
    "progress_percent": 54.0,  # total_done / total_files * 100
    "work_statuses": [...]     # 매칭된 카테고리 목록
}
```

**핵심**: `task_count`가 0이어도 `total_done`이나 `total_files`가 있으면 표시해야 함!

### Frontend 구현 (`FolderTreeWithProgress.tsx`)

```typescript
// ⚠️ CRITICAL: 하위 합산값 표시를 위한 조건
function getWorkSummary(folder: FolderWithProgress): WorkSummary | null {
  const summary = (folder as any).work_summary as WorkSummary | undefined;

  // 1. summary가 없으면 null
  if (!summary) return null;

  // 2. task_count가 0이어도 total_done이나 total_files가 있으면 표시
  //    (하위 폴더 합산값일 수 있음)
  if (summary.task_count === 0 && summary.total_done === 0 && summary.total_files === 0) {
    return null;
  }

  return summary;
}
```

### ❌ 과거 버그 패턴

```typescript
// 이 코드는 버그입니다! 하위 합산값을 숨김
if (!summary || summary.task_count === 0) return null;  // ❌ WRONG
```

### ✅ 올바른 패턴

```typescript
// 하위 합산값도 표시
if (!summary) return null;
if (summary.task_count === 0 && summary.total_done === 0 && summary.total_files === 0) {
  return null;
}
return summary;  // ✅ CORRECT
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
- `reconciliation.*`: 매칭/합산/검증 로직 (핵심!)

### External
- `sqlalchemy`: DB 접근

---

## Reconciliation 도메인과의 관계

Progress 도메인은 Reconciliation 도메인의 **소비자**입니다.

```
┌─────────────────────────────────────────────────────────────┐
│  Progress Domain                                             │
│  (작업 진행률 표시)                                          │
│         │                                                    │
│         │ uses                                               │
│         ▼                                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Reconciliation Domain                               │    │
│  │  • recon.matcher    → 폴더-카테고리 매칭            │    │
│  │  • recon.aggregator → 계층 합산 (Cascading 방지)    │    │
│  │  • recon.validator  → 불일치 감지                   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**참조**: `.claude/agents/reconciliation-domain.md`

## Error Codes

| Code | Description | Recovery |
|------|-------------|----------|
| `VIDEO_NOT_FOUND` | 비디오 파일 없음 | 스캔 재실행 |
| `DURATION_ZERO` | duration 0 | 메타데이터 재추출 |
| `STATS_CALCULATION_FAILED` | 통계 집계 실패 | 캐시 초기화 후 재시도 |

## Testing
- Unit: `tests/test_progress.py`
- Integration: `tests/test_work_status_api.py`

---

## 📐 Layout Rules (Dashboard.tsx)

### Flex 레이아웃 (권장)

```tsx
// ✅ 올바른 패턴: 독립 스크롤 영역
<div className="flex flex-col lg:flex-row gap-6" style={{ height: 'calc(100vh - 280px)' }}>
  {/* Left: 폴더 트리 - 독립 스크롤 */}
  <div className="flex-[2] min-h-0 overflow-y-auto">
    <FolderTreeWithProgress />
  </div>

  {/* Right: 상세 패널 - 독립 스크롤 */}
  <div className="flex-1 min-h-0 overflow-y-auto space-y-4">
    <FolderProgressDetail />
    <DataSourceStatus />
  </div>
</div>
```

### ❌ 피해야 할 패턴

```tsx
// Grid + sticky 조합은 overflow-hidden과 충돌
<div className="grid grid-cols-1 lg:grid-cols-3">
  <div className="lg:col-span-2 overflow-hidden">  // ❌ sticky 무효화
    ...
  </div>
  <div className="lg:sticky lg:top-4">  // ❌ 작동 안 함
    ...
  </div>
</div>
```

---

## 🐛 Known Issues & Solutions

### Issue #1: 하이어라키 합산값 미표시 (2025-12-09 해결)

**증상**: 부모 폴더에 프로그레스바가 표시되지 않음 (하위 폴더에만 데이터 있음)

**원인**: `getWorkSummary()` 함수가 `task_count === 0`일 때 무조건 `null` 반환

**해결**: `total_done`이나 `total_files`가 있으면 표시하도록 조건 수정

**파일**: `FolderTreeWithProgress.tsx:71-77`

---

### Issue #2: 좌우 패널 스크롤 연동 문제 (2025-12-09 해결)

**증상**: 좌측 스크롤 시 우측 패널이 "대기 상태"로 보임

**원인**: CSS Grid + sticky 조합이 `overflow-hidden` 부모와 충돌

**해결**: Flex 레이아웃 + 독립 스크롤 영역으로 변경

**파일**: `Dashboard.tsx:92-104`

---

### Issue #3: 폴더명 변형 매칭 실패 (2025-12-10 해결)

**증상**: "GOG 최종", "GGMillions", "HCL" 폴더에 `work_summary=null` 표시

**원인**: `_match_work_statuses()` 함수의 4가지 매칭 전략이 "폴더명이 카테고리로 시작"하는 패턴을 처리하지 못함
- 예: "GOG 최종" 폴더와 "GOG" 카테고리가 매칭되지 않음

**분석**:
```
기존 매칭 전략:
1. exact: "GOG 최종" == "GOG" → ❌
2. prefix: "GOG".startswith("GOG 최종 ") → ❌
3. word: "GOG 최종" in ["GOG"] → ❌
4. year: 연도 아님 → ❌
```

**해결**: 전략 2.5 `folder_prefix` 추가 (우선순위 0.85)
```python
# 2.5. 폴더명이 카테고리로 시작 (예: "GOG 최종" → "GOG")
if folder_lower.startswith(category_lower + ' ') or folder_lower.startswith(category_lower + '_'):
    matched.append((ws, 0.85, 'folder_prefix'))
    continue
```

**파일**: `progress_service.py:219-223`

---

## 📋 Matching Strategy Reference

| 전략 | 점수 | 예시 | 설명 |
|------|------|------|------|
| `exact` | 1.0 | "GOG" == "GOG" | 정확히 일치 |
| `prefix` | 0.9 | "PAD S12" starts with "PAD " | 카테고리가 폴더명으로 시작 |
| `folder_prefix` | 0.85 | "GOG 최종" starts with "GOG " | 폴더명이 카테고리로 시작 |
| `word` | 0.8 | "WSOP" in "2023 WSOP Paradise" | 독립 단어로 포함 |
| `year` | 0.7 | "2023" in category_words | 연도 매칭 |

---

## 🔍 Debugging Strategy

### 디버깅 플래그

**Frontend** (`FolderTreeWithProgress.tsx`):
```typescript
const DEBUG_WORK_SUMMARY = true;  // 콘솔 로그 활성화
```

**Backend** (`progress_service.py`):
```python
logger.info(f"[DEBUG] 폴더 매칭: {folder.name}")  # depth <= 2 폴더만
```

### 콘솔 로그 패턴

| 로그 | 의미 |
|------|------|
| `[FolderTreeWithProgress] API 응답:` | API에서 받은 전체 데이터 |
| `[getWorkSummary] 폴더: {name}` | 각 폴더의 work_summary 상태 |
| `[getWorkSummary] ⚠️ {name}: work_summary가 없음!` | 데이터 누락 |
| `[DEBUG] 폴더 매칭: {name}` | Backend 매칭 결과 |
| `[DEBUG] ⚠️ {name}: 직접 매칭 없음` | 카테고리 매칭 실패 |
| `[DEBUG] ✅ {name}: 자식 합산으로 work_summary 생성!` | 자식 데이터 합산 성공 |

### API 응답 확인

```bash
# work_summary 데이터 확인
curl http://localhost:8000/api/progress/tree?include_files=false

# 특정 폴더 확인 (jq 필요)
curl ... | jq '.children[] | select(.name == "WSOP") | .work_summary'
```

### 예상 응답

```json
{
  "task_count": 5,
  "total_files": 100,
  "total_done": 54,
  "combined_progress": 54.0,
  "sheets_total_videos": 120,
  "sheets_excel_done": 54,
  "actual_progress": 45.0,
  "data_source_mismatch": true,
  "mismatch_count": 20
}
```

### 문제 확인 체크리스트

1. [ ] 브라우저 DevTools > Console에서 `[FolderTreeWithProgress]` 로그 확인
2. [ ] 각 폴더의 `hasWorkSummary: true/false` 확인
3. [ ] Backend 로그에서 `[DEBUG]` 패턴 확인
4. [ ] 직접 매칭 실패 → 자식 합산 성공 흐름 확인
