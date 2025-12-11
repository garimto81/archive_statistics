# Reconciliation Domain Agent Rules

**Version**: 1.1.0 | **Updated**: 2025-12-11

## Identity

- **Role**: NAS-Sheets 데이터 일관성 보장 전문가
- **Level**: 1 (Domain)
- **Scope**: NAS 파일 데이터와 Google Sheets 작업 현황의 조정(Reconciliation)

---

## 🎯 실행 계획: 누가 어떻게 개선하는가?

### 역할 정의

| 역할 | 담당 | 책임 |
|------|------|------|
| **사용자** | Human | 문제 보고, 최종 승인 |
| **Orchestrator** | Claude AI | 문제 분류, 도메인 라우팅 |
| **Reconciliation Agent** | Claude AI (도메인 전문가) | 매칭/합산/검증 로직 개선 |
| **Reviewer** | Claude AI | 변경사항 검증, 회귀 테스트 |

### 트리거 조건: 언제 개선이 시작되는가?

| 트리거 | 감지 방법 | 담당 블럭 |
|--------|----------|----------|
| `total_done > total_files` | API 응답 검증 | `recon.validator` |
| `work_summary: null` (예상치 못한) | 로그 분석 | `recon.aggregator` |
| 매칭 실패 (Orphan 폴더) | 매칭률 < 90% | `recon.matcher` |
| NAS-Sheets 10%+ 불일치 | `data_source_mismatch: true` | `recon.validator` |

### 자동 진단 흐름

```
문제 발생
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Step 1: 증상 분류 (Orchestrator)                       │
│  • total_done > total_files → recon.aggregator 문제    │
│  • 매칭 없음 → recon.matcher 문제                       │
│  • 데이터 불일치 → recon.validator 검토                 │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Step 2: 블럭 진단 (Reconciliation Agent)               │
│  • 해당 블럭의 Agent Rules 로드                         │
│  • 과거 Known Issues 검색                               │
│  • 유사 패턴 매칭                                       │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Step 3: 수정 제안 (Reconciliation Agent)               │
│  • 코드 변경 위치 특정                                  │
│  • 테스트 케이스 작성                                   │
│  • 사용자 승인 요청                                     │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Step 4: 검증 (Reviewer)                                │
│  • 회귀 테스트 실행                                     │
│  • 다른 블럭 영향 확인                                  │
│  • Known Issues 업데이트                                │
└─────────────────────────────────────────────────────────┘
```

---

## Problem Statement

이 도메인이 해결하는 핵심 문제:

| 문제 유형 | 증상 | 원인 |
|-----------|------|------|
| **NAS 분석 결과 불일치** | `nas: (26/1897)` vs 실제 `1912` 파일 | work_summary 없는 자식 file_count 누락 |
| **Sheets 분석 결과 불일치** | 중복 카운팅, Cascading Match | 폴더-카테고리 매칭 오류 |
| **합산 초과** | `total_done > total_files` | 동일 work_status가 부모+자식에서 중복 매칭 |

---

## Managed Blocks

| Block ID | 파일 | 책임 | 테스트 |
|----------|------|------|--------|
| `recon.matcher` | `services/reconciliation/matcher.py` | 폴더-카테고리 매칭 (6가지 전략) | `test_recon_matcher.py` |
| `recon.aggregator` | `services/reconciliation/aggregator.py` | 계층 합산, Cascading 방지 | `test_recon_aggregator.py` |
| `recon.validator` | `services/reconciliation/validator.py` | 불일치 감지, 경고 생성 | `test_recon_validator.py` |

---

## Critical Files (현재 위치)

리팩토링 전까지 아래 파일들이 Reconciliation 로직을 담고 있음:

| 파일 | 해당 블럭 | 줄 번호 | 개선 담당 |
|------|----------|---------|----------|
| `backend/app/services/progress_service.py` | `recon.matcher` | 202-293 | Reconciliation Agent |
| `backend/app/services/progress_service.py` | `recon.aggregator` | 569-665 | Reconciliation Agent |
| `backend/app/services/progress_service.py` | `recon.validator` | 628-630 | Reconciliation Agent |

---

## Block 1: recon.matcher

### 개선 책임자: Reconciliation Agent

### 개선 시점
- 새로운 폴더명 패턴이 매칭 실패할 때
- 기존 전략의 점수 조정이 필요할 때

### 개선 절차

```
1. 매칭 실패 케이스 수집
   └─ 로그: "[RECON.MATCHER] ⚠️ {folder} 매칭 실패"

2. 전략 분석
   └─ 기존 6가지 전략 중 해당하는 것 검토

3. 해결 방안 선택
   ├─ A) 기존 전략 점수 조정
   ├─ B) 새 전략 추가 (score 정의 필수)
   └─ C) 정규화 로직 수정

4. 테스트 작성 (반드시 먼저)
   └─ tests/test_recon_matcher.py에 케이스 추가

5. 구현 및 검증
   └─ pytest tests/test_recon_matcher.py -v

6. Known Issues 업데이트
   └─ 이 문서의 "Known Issues" 섹션에 기록
```

### Core Logic: 6가지 매칭 전략

```python
MATCHING_STRATEGIES = {
    "exact": {
        "score": 1.0,
        "description": "정확히 일치",
        "example": '"GOG" == "GOG"'
    },
    "exact_normalized": {
        "score": 0.98,
        "description": "하이픈/밑줄 정규화 후 일치",
        "example": '"WSOP-Europe" → "WSOP Europe"'
    },
    "prefix": {
        "score": 0.9,
        "description": "카테고리가 폴더명으로 시작",
        "example": '"PAD S12" starts with "PAD "'
    },
    "folder_prefix": {
        "score": 0.85,
        "description": "폴더명이 카테고리로 시작",
        "example": '"GOG 최종" starts with "GOG "'
    },
    "subset": {
        "score": "0.88 + 0.01 * word_count (max 0.94)",
        "description": "카테고리 단어가 폴더명에 모두 포함",
        "example": '"2025 WSOP" ⊆ "2025 WSOP-LAS VEGAS"'
    },
    "word": {
        "score": 0.8,
        "description": "독립 단어로 포함",
        "example": '"WSOP" in ["2023", "WSOP", "Paradise"]'
    },
    "year": {
        "score": 0.7,
        "description": "연도만 매칭",
        "example": '"2023" in category'
    }
}
```

### Critical Rule: 단일 매칭 정책

```python
# ⚠️ 핵심: 여러 매칭 후보 중 최고 점수 1개만 반환
def match(self, folder_name: str, work_statuses: Dict) -> Optional[MatchResult]:
    candidates = self._find_all_candidates(folder_name, work_statuses)
    if not candidates:
        return None

    # 점수 내림차순 정렬 → 최고 점수 1개만
    candidates.sort(key=lambda x: x.score, reverse=True)
    return candidates[0]  # 단일 반환!
```

**위반 시 증상**: `excel_done` 중복 합산 → `total_done > total_files`

### Constraints

#### DO
- 모든 비교는 case-insensitive (`.lower()`)
- 정규화 시 하이픈, 밑줄을 공백으로 변환
- 새 전략 추가 시 반드시 단위 테스트 작성

#### DON'T
- 여러 매칭 결과 반환 금지 (반드시 1개 또는 0개)
- substring 매칭 사용 금지 ("WSOPE" != "WSOP")
- 점수 하드코딩 금지 (상수로 정의)

---

## Block 2: recon.aggregator

### 개선 책임자: Reconciliation Agent

### 개선 시점
- `total_files` 합산이 실제 NAS 파일 수와 불일치할 때
- Cascading Match가 감지될 때

### 개선 절차

```
1. 불일치 케이스 특정
   └─ API 응답: work_summary.total_files vs file_count 비교

2. 원인 분석
   ├─ A) work_summary 없는 자식 누락? → else 절 확인
   ├─ B) Cascading Match? → parent_work_status_ids 전파 확인
   └─ C) 직접 매칭과 자식 합산 중복? → 조건문 확인

3. 테스트 작성 (반드시 먼저)
   └─ tests/test_recon_aggregator.py에 케이스 추가

4. 구현 및 검증
   └─ pytest tests/test_recon_aggregator.py -v

5. 전체 회귀 테스트
   └─ pytest tests/test_progress_matching.py -v
```

### Core Logic: 계층 합산 원칙

```
ARCHIVE/
├── WSOP/                      ← sum(children.total_files) = 100
│   ├── Main Event/            ← total_files: 40
│   ├── Bracelet/              ← total_files: 35
│   └── GGMillions/            ← file_count: 25 (work_summary 없음!)
```

### Critical Rule: 모든 자식 합산

```python
# ⚠️ 핵심: work_summary 유무와 관계없이 모든 자식 파일 수 합산
def aggregate_children(self, children: List[FolderData]) -> AggregatedSummary:
    child_total_files = 0
    child_total_done = 0

    for child in children:
        if child.work_summary:
            child_total_files += child.work_summary.total_files
            child_total_done += child.work_summary.total_done
        else:
            # ⚠️ 이 else 절이 없으면 file_count 누락!
            child_total_files += child.file_count

    return AggregatedSummary(total_files=child_total_files, total_done=child_total_done)
```

**위반 시 증상**: `nas: (26/1897)` (실제 1912 중 15개 누락)

### Critical Rule: Cascading Match 방지

```python
# ⚠️ 핵심: 상위 폴더에서 사용된 work_status는 하위에서 제외
def aggregate_with_cascading_prevention(
    self,
    children: List[FolderData],
    parent_work_status_ids: Set[int]  # 상위에서 이미 사용된 ID
) -> AggregatedSummary:

    for child in children:
        # 자식에게 parent_ids 전파
        child_available_statuses = {
            ws for ws in all_work_statuses
            if ws.id not in parent_work_status_ids
        }
        ...
```

**위반 시 증상**: WSOP-Europe(27개) + 2025 WSOP(6개) = 33개 중복 카운팅

### Constraints

#### DO
- `parent_work_status_ids` 파라미터 필수 전파
- 재귀 호출 시 현재 매칭 ID를 set에 추가 후 전달
- 합산 후 검증 (`total_done <= total_files`)

#### DON'T
- 직접 매칭이 있는 폴더는 자식 합산하지 않음 (중복 방지)
- `parent_work_status_ids` 생략 금지

---

## Block 3: recon.validator

### 개선 책임자: Reconciliation Agent

### 개선 시점
- 새로운 검증 규칙이 필요할 때
- 기존 임계값 조정이 필요할 때

### 개선 절차

```
1. 검증 실패 케이스 분석
   └─ 로그: "[RECON.VALIDATOR] V00X: ..."

2. 규칙 검토
   ├─ A) 기존 규칙 임계값 조정
   └─ B) 새 규칙 추가 (V005, V006...)

3. 테스트 작성 (반드시 먼저)
   └─ tests/test_recon_validator.py에 케이스 추가

4. 구현 및 검증
```

### Validation Rules

| Rule ID | 조건 | 심각도 | 조치 |
|---------|------|--------|------|
| `V001` | `total_done > total_files` | ERROR | 매칭 무효화 |
| `V002` | `\|nas_count - sheets_count\| > 10%` | WARNING | 데이터 불일치 표시 |
| `V003` | Orphan 폴더 (매칭 없음) | INFO | 수동 매핑 권장 |
| `V004` | Orphan 카테고리 (사용 안 됨) | INFO | Sheets 검토 권장 |

### Implementation

```python
class ReconciliationValidator:
    MISMATCH_THRESHOLD = 0.1  # 10%

    def validate(self, folder: FolderData) -> ValidationResult:
        issues = []

        # V001: 합산 초과 검사
        if folder.total_done > folder.total_files:
            issues.append(Issue(
                code="V001",
                severity="ERROR",
                message=f"Overcounting: {folder.total_done} > {folder.total_files}"
            ))

        # V002: 데이터 소스 불일치
        if folder.work_summary:
            ws = folder.work_summary
            diff_ratio = abs(ws.total_files - ws.sheets_total_videos) / max(ws.total_files, ws.sheets_total_videos, 1)
            if diff_ratio > self.MISMATCH_THRESHOLD:
                issues.append(Issue(
                    code="V002",
                    severity="WARNING",
                    message=f"Data mismatch: NAS={ws.total_files}, Sheets={ws.sheets_total_videos}"
                ))

        return ValidationResult(
            valid=all(i.severity != "ERROR" for i in issues),
            issues=issues
        )
```

### Constraints

#### DO
- 모든 검증 규칙에 고유 코드 부여 (V001, V002...)
- 검증 실패 시 로그 기록
- UI에 불일치 경고 표시 (`data_source_mismatch` 플래그)

#### DON'T
- ERROR 심각도의 문제를 무시하고 진행
- 검증 로직 인라인 작성 (반드시 Validator 클래스 사용)

---

## Dependencies

### Internal
- `scanner.storage`: FolderStats, FileStats 데이터
- `sync.import`: WorkStatus, HandAnalysis 데이터

### External
- `sqlalchemy`: DB 접근

---

## Error Codes

| Code | Description | Recovery |
|------|-------------|----------|
| `MATCH_NOT_FOUND` | 매칭되는 카테고리 없음 | 수동 매핑 필요 |
| `CASCADING_DETECTED` | 부모-자식 중복 매칭 | parent_ids 확인 |
| `OVERCOUNTING` | total_done > total_files | 매칭 로직 검토 |
| `DATA_MISMATCH` | NAS-Sheets 10%+ 차이 | 데이터 소스 확인 |
| `AGGREGATION_FAILED` | 합산 계산 오류 | 재귀 로직 검토 |

---

## Testing Strategy

### Unit Tests (각 블럭 독립 테스트)

```python
# tests/test_recon_matcher.py
class TestReconMatcher:
    def test_exact_match(self): ...
    def test_folder_prefix_match(self): ...
    def test_single_match_only(self): ...
    def test_no_false_positive(self): ...

# tests/test_recon_aggregator.py
class TestReconAggregator:
    def test_includes_children_without_work_summary(self): ...
    def test_cascading_prevention(self): ...
    def test_no_double_counting(self): ...

# tests/test_recon_validator.py
class TestReconValidator:
    def test_overcounting_detection(self): ...
    def test_data_mismatch_warning(self): ...
```

### Integration Tests (블럭 간 연동)

```python
# tests/integration/test_reconciliation_flow.py
async def test_full_reconciliation_flow():
    """matcher → aggregator → validator 전체 흐름"""
    ...
```

---

## 🐛 Known Issues & Solutions

### Issue #1: file_count 합산 누락 (2025-12-11 해결)

**증상**: `nas: (26/1897)` (실제 1912개)

**담당 블럭**: `recon.aggregator`

**원인**: work_summary 없는 자식의 file_count 미합산

**해결**: else 절 추가
```python
else:
    child_total_files += child_data.get("file_count", 0)
```

**파일**: `progress_service.py:576-579`

**개선 담당**: Reconciliation Agent

---

### Issue #2: Cascading Match (Issue #24, 2025-12-10 해결)

**증상**: WSOP-Europe과 2025 WSOP-Europe 모두 "WSOP Europe" 카테고리에 매칭

**담당 블럭**: `recon.aggregator`

**원인**: 상위 매칭 ID가 하위로 전파되지 않음

**해결**: `parent_work_status_ids` 파라미터 추가 및 전파

**파일**: `progress_service.py:557-565`

**개선 담당**: Reconciliation Agent

---

### Issue #3: 중복 excel_done 카운팅 (Issue #18, 2025-12-07 해결)

**증상**: 하나의 폴더에 여러 카테고리 매칭 → done 합산 폭증

**담당 블럭**: `recon.matcher`

**원인**: `recon.matcher`가 여러 결과 반환

**해결**: 최고 점수 1개만 반환하도록 수정

**파일**: `progress_service.py:280-293`

**개선 담당**: Reconciliation Agent

---

## Debugging Strategy

### 디버그 로그 패턴

```python
# recon.matcher
logger.info(f"[RECON.MATCHER] {folder_name} → {category} (strategy={strategy}, score={score})")

# recon.aggregator
logger.info(f"[RECON.AGGREGATOR] {folder_name}: children={len(children)}, total_files={total_files}")
logger.info(f"[RECON.AGGREGATOR] ⚠️ {child_name}: work_summary 없음, file_count={file_count} 합산")

# recon.validator
logger.warning(f"[RECON.VALIDATOR] V001: {folder_name} overcounting detected")
logger.warning(f"[RECON.VALIDATOR] V002: {folder_name} data mismatch NAS={nas} Sheets={sheets}")
```

### API 검증

```bash
# 불일치 확인
curl http://localhost:8000/api/progress/tree?include_files=false | \
  jq '.children[] | select(.work_summary.data_source_mismatch == true) | .name'

# 합산 초과 확인
curl http://localhost:8000/api/progress/tree | \
  jq '.. | select(.work_summary.total_done > .file_count?) | .name'
```

---

## Migration Plan

### Phase 1: 현재 상태 (완료)
- ✅ Agent Rules 파일로 도메인 경계 명확화
- ✅ 기존 `progress_service.py`에서 해당 로직 위치 식별

### Phase 2: 테스트 강화 (권장)
- [ ] `test_recon_aggregator.py` 신규 작성
- [ ] 현재 버그 회귀 테스트 추가

### Phase 3: 블럭 분리 (선택적)
- [ ] `services/reconciliation/` 디렉토리 생성
- [ ] matcher.py, aggregator.py, validator.py 분리
- [ ] progress_service.py에서 import하여 사용

---

## References

| 문서 | 설명 |
|------|------|
| `progress-domain.md` | Progress 도메인 (이 도메인의 소비자) |
| `sync-domain.md` | Sync 도메인 (WorkStatus 데이터 제공) |
| `docs/PRD_CASCADING_MATCH.md` | Cascading Match 문제 상세 분석 |
| `tests/test_progress_matching.py` | 현재 매칭 테스트 |
