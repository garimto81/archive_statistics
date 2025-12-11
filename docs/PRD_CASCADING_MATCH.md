# PRD: 상위 폴더 매칭 전파 (Cascading Match)

**Version**: 1.0.0
**Date**: 2025-12-11
**Status**: Draft
**Related Issue**: N/A (신규)

---

## 1. 문제 정의

### 1.1 현재 상황

동일한 `work_status`가 부모 폴더와 자식 폴더에 **중복 매칭**됨:

```
WSOP-EUROPE (156개)        → "WSOP Europe" (done=27) 매칭
└── 2025 WSOP-Europe (58개)   → "WSOP Europe" (done=27) 매칭 ⚠️ 중복
    └── MAIN EVENT (31개)     → "WSOP Europe" (done=27) 매칭 ⚠️ 중복
```

### 1.2 예상 동작

```
WSOP-EUROPE (156개)        → "WSOP Europe" 매칭 ✅
└── 2025 WSOP-Europe (58개)   → 상위에서 처리됨 (매칭 없음)
    └── MAIN EVENT (31개)     → 상위에서 처리됨 (매칭 없음)
```

### 1.3 영향

- 진행률 표시 왜곡 (상위: 17%, 하위: 87%)
- 사용자 혼란 (같은 작업이 여러 번 표시됨)
- 데이터 중복 카운트 위험

---

## 2. 목표

1. **상위 폴더 매칭 전파**: FK로 매칭된 상위 폴더의 하위 폴더는 동일 work_status에 매칭되지 않음
2. **FK 우선 매칭 강화**: FK가 있으면 fuzzy matching 완전 비활성화
3. **명시적 매핑 활용**: 기존 folder_mapping API를 통한 1:1 명시적 연결 활용

---

## 3. 해결 방안

### 3.1 접근법 1: 상위 매칭 ID 전파 (선택)

`_build_folder_progress` 함수에 `parent_work_status_ids` 파라미터 추가:

```python
async def _build_folder_progress(
    self,
    db: AsyncSession,
    folder: FolderStats,
    work_statuses: Dict[str, Dict],
    hand_data: Dict[str, Dict],
    max_depth: int,
    current_depth: int,
    include_files: bool,
    extensions: Optional[List[str]] = None,
    include_codecs: bool = False,
    parent_work_status_ids: Set[int] = None,  # 추가
) -> Dict[str, Any]:
```

**매칭 로직**:
1. FK 존재 → FK 사용, `parent_work_status_ids`에 추가
2. FK 없음 + `work_status_id`가 `parent_work_status_ids`에 없음 → fuzzy matching
3. FK 없음 + `work_status_id`가 `parent_work_status_ids`에 있음 → 매칭 스킵

### 3.2 접근법 2: 하위 폴더 완전 제외

상위 폴더에 FK가 있으면, 해당 폴더의 **모든 하위 폴더**는:
- `work_summary = None`
- 상위 폴더에서 통합 관리

### 3.3 권장: 접근법 1 (유연성 유지)

- 하위 폴더가 **다른** work_status에 매칭될 수 있음
- 같은 work_status에만 중복 매칭 방지

---

## 4. 구현 계획

### Phase 1: FK 우선 매칭 강화

```python
# 현재 (문제)
if hasattr(folder, 'work_status_id') and folder.work_status_id:
    # FK 매칭
    ...
if not work_statuses_matched:
    # Fuzzy matching fallback (항상 실행됨)
    work_statuses_matched = self._match_work_statuses(...)

# 수정 (해결)
if hasattr(folder, 'work_status_id') and folder.work_status_id:
    # FK 매칭
    ...
    matching_method = "fk"
elif current_work_status_id not in parent_work_status_ids:
    # Fuzzy matching (상위에서 사용된 work_status 제외)
    work_statuses_matched = self._match_work_statuses(...)
```

### Phase 2: 상위 매칭 ID 전파

```python
# 자식 폴더 처리 시
child_parent_ids = parent_work_status_ids.copy()
if folder_work_status_id:
    child_parent_ids.add(folder_work_status_id)

child_data = await self._build_folder_progress(
    ...,
    parent_work_status_ids=child_parent_ids,
)
```

### Phase 3: UI 표시 개선

- 상위에서 매칭된 폴더는 "상위 폴더에서 관리됨" 표시
- 또는 진행률 바 숨김

---

## 5. 테스트 케이스

### 5.1 단위 테스트

```python
def test_cascading_match_prevents_duplicate():
    """상위 폴더 매칭 시 하위 폴더 중복 매칭 방지"""
    # WSOP-EUROPE에 FK로 "WSOP Europe" 연결
    # 2025 WSOP-Europe은 같은 work_status에 매칭되지 않아야 함
    pass

def test_different_work_status_still_matches():
    """다른 work_status는 하위 폴더에서 매칭 가능"""
    # WSOP-EUROPE → "WSOP Europe"
    # 2025 WSOP-Europe → "2025 WSOP" (다른 작업)은 허용
    pass
```

### 5.2 통합 테스트

```python
def test_progress_tree_no_duplicate_done():
    """트리 전체에서 done 값 중복 없음"""
    # API 호출 후 같은 work_status가 여러 폴더에 매칭되지 않음 확인
    pass
```

---

## 6. 마이그레이션

### 6.1 데이터 마이그레이션 불필요

- 기존 FK 구조 그대로 사용
- 코드 로직만 수정

### 6.2 배포 순서

1. Backend 코드 수정
2. 테스트 통과 확인
3. Docker 재배포
4. Frontend 캐시 클리어 (필요 시)

---

## 7. 성공 기준

| 기준 | 측정 방법 |
|------|----------|
| 중복 매칭 제거 | 같은 work_status가 2개 이상 폴더에 표시되지 않음 |
| 기존 기능 유지 | 10개 단위 테스트 통과 |
| 진행률 정확성 | WSOP-EUROPE: 17.3% (27/156) 단일 표시 |

---

## 8. 리스크

| 리스크 | 영향 | 완화 방안 |
|--------|------|----------|
| 하위 폴더 진행률 누락 | 중간 | 상위 폴더에서 통합 표시 |
| 성능 저하 | 낮음 | Set 자료구조로 O(1) 조회 |
| FK 미설정 폴더 | 중간 | Fuzzy matching fallback 유지 |
