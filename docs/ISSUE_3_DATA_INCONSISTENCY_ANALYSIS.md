# Issue 3: 폴더 하이어라키별 데이터 불일치 분석 리포트

**작성일**: 2025-12-09
**이슈**: #3 폴더별 데이터 불일치
**블럭**: data.consistency

---

## 1. 문제 요약

폴더 하이어라키에서 상위 폴더와 하위 폴더의 `work_summary` 데이터가 일관되지 않음. 특히 WSOP 폴더에서 다음과 같은 문제 발견:

- **NAS file_count**: 860개 (실제 스캔 결과)
- **매칭된 work_status total_videos 합산**: 110개 (구글 시트)
- **차이**: -750개 (87% 불일치)

---

## 2. 근본 원인 분석

### 2.1 중복 매칭 문제

**현상**:
- "WSOP" 폴더가 5개의 work_status에 매칭됨:
  - `2023 WSOP Paradise` (word match)
  - `2025 WSOP` (word match)
  - `WSOP Cyprus` (prefix match)
  - `WSOP Europe` (prefix match)
  - `WSOP LA` (prefix match)

**원인**:
- `_match_work_statuses()` 메서드가 **여러 개의 work_status를 반환**
- 각 work_status의 `total_videos`를 단순 합산
- 실제로 WSOP 폴더의 860개 파일은 하위 폴더에 분산되어 있음:
  - `WSOP ARCHIVE (PRE-2016)`: 326개
  - `WSOP Bracelet Event`: 486개
  - `WSOP Circuit Event`: 48개

**코드 위치**:
```python
# backend/app/services/progress_service.py:318-338
if work_statuses_matched:
    total_done = sum(ws.get("excel_done", 0) for ws in work_statuses_matched)
    sheets_total = sum(ws.get("total_videos", 0) for ws in work_statuses_matched)

    combined_progress = (total_done / folder.file_count * 100) if folder.file_count > 0 else 0
```

### 2.2 하이어라키 집계 이중 카운팅

**현상**:
- 상위 폴더(WSOP)와 하위 폴더(WSOP-PARADISE)가 같은 work_status에 매칭
- 상위 폴더의 `work_summary` 계산 시 하위 폴더 데이터를 합산하면 이중 카운팅

**코드 위치**:
```python
# backend/app/services/progress_service.py:416-444
# 자식 폴더의 work_summary 합산
if child_data.get("work_summary"):
    child_ws = child_data["work_summary"]
    child_total_files += child_ws.get("total_files", 0)
    child_total_done += child_ws.get("total_done", 0)
    # ...

# 현재 폴더의 work_summary에 더함
if folder_dict["work_summary"]:
    ws = folder_dict["work_summary"]
    ws["total_files"] += child_total_files
    ws["total_done"] += child_total_done
```

**시나리오**:
1. "WSOP" 폴더가 "2023 WSOP Paradise" work_status와 매칭 → `excel_done: 9`
2. 하위 "WSOP-PARADISE" 폴더도 같은 work_status와 매칭 → `excel_done: 9`
3. 상위 폴더 집계 시 `9 + 9 = 18`로 이중 카운팅

### 2.3 데이터 출처 불일치

**NAS file_count vs 구글 시트 total_videos**:

| 항목 | 출처 | 의미 | 예시 |
|------|------|------|------|
| `file_count` | NAS 스캔 | 실제 파일 개수 | 860 |
| `total_videos` | 구글 시트 | 작업 대상 수량 | 110 |

**불일치 원인**:
1. 파일 분할: 1개 원본 → 여러 개 파일로 분할
2. 파일 병합: 여러 에피소드 → 1개 파일로 병합
3. 폴더 재구성: 파일 이동 후 구글 시트 미반영
4. 하위 폴더 포함: 상위 폴더 file_count는 하위 포함, work_status는 최종 작업물만

### 2.4 진행률 계산 기준 불일치

**현재 로직**:
```python
# progress_service.py:324
combined_progress = (total_done / folder.file_count * 100)
```

- 분자: `total_done` (구글 시트 `excel_done` 합산)
- 분모: `folder.file_count` (NAS 스캔 결과)
- **문제**: 서로 다른 출처의 데이터를 사용하여 진행률 계산

---

## 3. 실제 데이터 예시

### WSOP 폴더 매칭 결과

```
폴더: WSOP (depth 1)
  file_count (NAS): 860

매칭된 work_status:
  1. 2023 WSOP Paradise (word)
     total_videos: 9, excel_done: 9
  2. 2025 WSOP (word)
     total_videos: 43, excel_done: 6
  3. WSOP Cyprus (prefix)
     total_videos: 6, excel_done: 6
  4. WSOP Europe (prefix)
     total_videos: 41, excel_done: 22
  5. WSOP LA (prefix)
     total_videos: 11, excel_done: 11

합산:
  total_videos: 110 (구글 시트)
  excel_done: 54
  file_count: 860 (NAS)
  차이: -750 (-87%)

진행률:
  현재 계산: 54 / 860 * 100 = 6.3%
  실제 의도: 54 / 110 * 100 = 49.1%
```

### 하위 폴더 분석

| 폴더명 | file_count (NAS) | 매칭된 work_status |
|--------|------------------|-------------------|
| WSOP ARCHIVE (PRE-2016) | 326 | 없음 |
| WSOP Bracelet Event | 486 | 없음 |
| WSOP Circuit Event | 48 | 없음 |
| WSOP 1973 | 2 | 없음 |
| WSOP-PARADISE | 196 | "2023 WSOP Paradise" (가능성) |
| WSOP-LAS VEGAS | 203 | "WSOP LA" (가능성) |
| WSOP-EUROPE | 87 | "WSOP Europe" (가능성) |

**관찰**:
- 상위 폴더(WSOP)에 매칭된 work_status는 실제로 하위 폴더(WSOP-PARADISE, WSOP-EUROPE 등)의 작업을 의미
- 상위 폴더의 file_count는 하위 포함 전체 파일 수이므로 분모가 과대 계상

---

## 4. 해결 방안

### 옵션 A: 매칭 로직 개선 (권장)

**목표**: 상위 폴더에서 하위 폴더의 work_status를 제외

**구현**:
```python
def _match_work_statuses(
    self,
    folder_name: str,
    folder_path: str,
    work_statuses: Dict[str, Dict],
    children_matched_categories: Set[str] = None  # 추가
) -> List[Dict]:
    """폴더명과 Work Status 카테고리 매칭

    Args:
        children_matched_categories: 하위 폴더에 이미 매칭된 카테고리 집합
    """
    matched = []
    folder_lower = folder_name.lower()

    for category, ws in work_statuses.items():
        # 하위 폴더에 이미 매칭된 카테고리는 제외
        if children_matched_categories and category in children_matched_categories:
            continue

        # 기존 매칭 로직...
```

**호출**:
```python
# _build_folder_progress에서
# 1. 하위 폴더 먼저 처리
children_matched_categories = set()
for child in child_folders:
    child_data = await self._build_folder_progress(...)
    if child_data.get("work_statuses"):
        for ws in child_data["work_statuses"]:
            children_matched_categories.add(ws["category"])

# 2. 현재 폴더 매칭 시 하위 매칭 제외
work_statuses_matched = self._match_work_statuses(
    folder.name,
    folder.path,
    work_statuses,
    children_matched_categories  # 전달
)
```

**장점**:
- 이중 카운팅 방지
- 상위 폴더는 직속 파일의 work_status만 매칭

**단점**:
- 로직 복잡도 증가
- 하위 폴더 순회 순서에 의존

### 옵션 B: 진행률 계산 기준 통일

**목표**: file_count 대신 total_videos를 진행률 분모로 사용

**구현**:
```python
# progress_service.py:324
if work_statuses_matched:
    total_done = sum(ws.get("excel_done", 0) for ws in work_statuses_matched)
    sheets_total = sum(ws.get("total_videos", 0) for ws in work_statuses_matched)

    # 변경: sheets_total을 분모로 사용
    combined_progress = (total_done / sheets_total * 100) if sheets_total > 0 else 0
```

**장점**:
- 간단한 수정
- 구글 시트 기준으로 일관된 진행률

**단점**:
- NAS 실제 파일 수와 괴리
- total_videos가 0인 경우 진행률 계산 불가

### 옵션 C: 매칭 정확도 향상

**목표**: 폴더명과 카테고리의 매칭 정확도를 높여 상위 폴더에 하위 work_status가 매칭되지 않도록 함

**구현**:
```python
# 매칭 우선순위 조정
def _match_work_statuses(self, folder_name, folder_path, work_statuses):
    matched = []
    folder_lower = folder_name.lower()

    for category, ws in work_statuses.items():
        category_lower = category.lower()

        # 1. 정확 일치 (exact match) - 우선순위 1.0
        if folder_lower == category_lower:
            matched.append((ws, 1.0, 'exact'))
            continue

        # 2. 카테고리가 폴더명으로 시작 (prefix) - 우선순위 0.9
        # 단, 카테고리가 폴더명보다 훨씬 길면 제외 (예: "WSOP" vs "2023 WSOP Paradise")
        if category_lower.startswith(folder_lower + ' '):
            # 길이 비율 체크: 카테고리가 폴더명의 2배 이상이면 하위 항목으로 간주
            if len(category_lower) < len(folder_lower) * 2:
                matched.append((ws, 0.9, 'prefix'))
            continue

        # 3. 폴더명이 카테고리로 시작 (reverse prefix) - 우선순위 0.8
        # 예: "WSOP Paradise" 폴더 vs "WSOP" 카테고리 → 매칭하지 않음
        if folder_lower.startswith(category_lower + ' '):
            continue  # 하위 폴더이므로 제외

        # 4. 독립 단어 매칭 (word) - 우선순위 0.7
        # 단, 전체 단어 수 대비 매칭 비율 확인
        category_words = set(category_lower.split())
        folder_words = set(folder_lower.split())

        if folder_lower in category_words:
            # 폴더명이 1단어이고 카테고리가 3단어 이상이면 제외
            if len(folder_words) == 1 and len(category_words) >= 3:
                continue  # 너무 포괄적인 매칭
            matched.append((ws, 0.7, 'word'))

    # 정렬 및 최상위 매칭만 반환
    matched.sort(key=lambda x: x[1], reverse=True)
    if not matched:
        return []

    top_score = matched[0][1]
    result = [m[0] for m in matched if m[1] >= top_score]

    return result
```

**장점**:
- 근본적인 매칭 품질 개선
- 폴더 하이어라키 관계 고려

**단점**:
- 매칭 로직이 더 복잡해짐
- 모든 경우를 커버하는 규칙 정의 어려움

### 옵션 D: UI에서 데이터 투명하게 표시

**목표**: 데이터 불일치를 수정하지 않고, UI에서 명확히 표시

**구현**:
```json
{
  "work_summary": {
    "task_count": 5,
    "total_files": 860,           // NAS 스캔 결과
    "total_done": 54,              // 구글 시트 합산
    "sheets_total_videos": 110,    // 구글 시트 원본
    "combined_progress": 6.3,      // 54 / 860 (참고용)
    "actual_progress": 49.1,       // 54 / 110 (실제 진행률)
    "data_source_mismatch": true,  // 불일치 플래그
    "mismatch_ratio": -750         // file_count - sheets_total
  }
}
```

**프론트엔드**:
```tsx
{workSummary.data_source_mismatch && (
  <Alert severity="warning">
    NAS 파일 수({workSummary.total_files})와
    작업 대상 수({workSummary.sheets_total_videos})가 다릅니다.
    실제 진행률: {workSummary.actual_progress}%
  </Alert>
)}
```

**장점**:
- 백엔드 로직 변경 최소화
- 사용자가 데이터 출처를 명확히 인지

**단점**:
- 근본 원인 해결 아님
- UI가 복잡해짐

---

## 5. 권장 솔루션

### 단계적 접근

**Phase 1: 즉시 적용 (옵션 D)**
- `work_summary`에 `sheets_total_videos`, `actual_progress` 필드 추가
- 프론트엔드에서 두 진행률 모두 표시
- 불일치 경고 메시지 표시

**Phase 2: 단기 개선 (옵션 C)**
- 매칭 로직 개선:
  - 폴더명과 카테고리 길이 비율 체크
  - 단어 수 기반 포괄성 필터링
  - 하위 폴더 패턴 제외

**Phase 3: 장기 개선 (옵션 A)**
- 하이어라키 기반 매칭:
  - 하위 폴더 우선 매칭
  - 상위 폴더는 하위 매칭 제외
  - work_status에 `folder_path` 명시적 매핑 추가

**Phase 4: 데이터 정규화**
- 구글 시트와 NAS 데이터 동기화:
  - 폴더 구조 변경 시 work_status 자동 업데이트
  - `total_videos` 자동 계산 (file_count 기반)
  - 수동 조정이 필요한 경우 플래그 표시

---

## 6. 구현 우선순위

| 작업 | 우선순위 | 난이도 | 예상 시간 |
|------|----------|--------|----------|
| 옵션 D: UI 투명화 | P0 (최우선) | 낮음 | 2시간 |
| 옵션 C: 매칭 개선 | P1 (단기) | 중간 | 4시간 |
| 옵션 A: 하이어라키 개선 | P2 (중기) | 높음 | 8시간 |
| Phase 4: 데이터 정규화 | P3 (장기) | 높음 | 16시간 |

---

## 7. 테스트 케이스

### TC1: WSOP 폴더 진행률 표시
- **Given**: WSOP 폴더 (file_count: 860, matched total_videos: 110, excel_done: 54)
- **When**: `/api/folders?path=/mnt/nas/WSOP` 호출
- **Then**:
  - `combined_progress`: 6.3% (54/860)
  - `actual_progress`: 49.1% (54/110)
  - `data_source_mismatch`: true

### TC2: 하위 폴더 매칭 제외
- **Given**: "2023 WSOP Paradise" work_status가 "WSOP-PARADISE" 폴더에 매칭
- **When**: "WSOP" 폴더 매칭 실행
- **Then**: "2023 WSOP Paradise"는 WSOP 폴더에 매칭되지 않음

### TC3: 매칭 길이 비율 체크
- **Given**: 폴더명 "WSOP" (4자), 카테고리 "2023 WSOP Paradise" (20자)
- **When**: prefix 매칭 시도
- **Then**: 길이 비율 5배 → 매칭 제외

---

## 8. 참조

- **코드**: `D:\AI\claude01\archive-statistics\backend\app\services\progress_service.py`
- **디버깅 스크립트**: `D:\AI\claude01\archive-statistics\scripts\debug_hierarchy.py`
- **상세 분석**: `D:\AI\claude01\archive-statistics\scripts\analyze_wsop_mismatch.py`
- **데이터베이스**: `D:\AI\claude01\archive-statistics\data\archive_stats.db`

---

## 9. 결론

폴더 하이어라키 데이터 불일치의 근본 원인은 **매칭 로직의 과도한 포괄성**과 **데이터 출처 차이**입니다.

**즉시 적용 가능한 해결책**:
1. UI에서 NAS 기준/시트 기준 진행률 모두 표시
2. 매칭 로직에 길이 비율 체크 추가
3. 하위 폴더 패턴 명시적 제외

**장기적 해결책**:
1. work_status에 `folder_path` 명시적 매핑
2. 구글 시트 ↔ NAS 데이터 동기화 자동화
3. 파일 수 불일치 알림 시스템
