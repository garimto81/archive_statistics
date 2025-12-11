# Progress Overview 이슈 히스토리

**Version**: 1.1.0 | **Last Updated**: 2025-12-11

> Progress Overview 컴포넌트 관련 버그 및 수정 이력을 추적합니다.

---

## 현재 상태: ✅ 모든 버그 해결 완료

**Issue #24, #26**: Cascading Match 문제가 모든 API 엔드포인트에서 해결됨

---

## 버그 히스토리

### Bug #1: 하이어라키 합산값 미표시 (2025-12-09 해결)

**증상**: 부모 폴더에 프로그레스바가 표시되지 않음

**원인**: `getWorkSummary()` 함수가 `task_count === 0`일 때 무조건 `null` 반환

**해결**: `total_done`이나 `total_files`가 있으면 표시하도록 조건 수정

**파일**: `FolderTreeWithProgress.tsx:71-77`

---

### Bug #2: 좌우 패널 스크롤 연동 문제 (2025-12-09 해결)

**증상**: 좌측 스크롤 시 우측 패널이 "대기 상태"로 보임

**원인**: CSS Grid + sticky 조합이 `overflow-hidden` 부모와 충돌

**해결**: Flex 레이아웃 + 독립 스크롤 영역으로 변경

**파일**: `Dashboard.tsx:92-104`

---

### Bug #3: 폴더명 변형 매칭 실패 (2025-12-10 해결)

**증상**: "GOG 최종", "GGMillions", "HCL" 폴더에 `work_summary=null` 표시

**원인**: 매칭 전략이 "폴더명이 카테고리로 시작"하는 패턴을 처리하지 못함

**해결**: 전략 2.5 `folder_prefix` 추가 (우선순위 0.85)

**파일**: `progress_service.py:219-223`

---

### Bug #4: 파일 카운트 합산 누락 (2025-12-11 해결)

**증상**: `nas: 1% (26/1897)` - 15개 파일 누락

**원인**: `work_summary`가 없는 자식 폴더의 `file_count`가 합산에서 제외됨

**해결**: `else` 절 추가하여 매칭 없는 폴더도 `file_count` 합산

**파일**: `progress_service.py:576-579`

```python
else:
    # work_summary가 없는 자식도 file_count는 합산해야 함
    child_total_files += child_data.get("file_count", 0)
```

---

### Bug #5: Cascading Match - `/progress/tree` API (2025-12-11 해결)

**증상**: "WSOP Europe" 카테고리가 WSOP-EUROPE, 2025 WSOP-Europe 등에 중복 매칭

**원인**: 부모에서 매칭된 work_status가 자식에게 전파되지 않음

**해결**: `parent_work_status_ids` 파라미터로 상위 매칭 ID 전파

**파일**: `progress_service.py:359, 558-565`

```python
# 자식에게 전파
child_parent_ids = parent_work_status_ids.copy()
if current_work_status_id:
    child_parent_ids.add(current_work_status_id)
```

---

### Bug #6: Cascading Match - `/progress/folder/{path}` API (2025-12-11 해결)

**증상**: 폴더 클릭 시 여전히 중복 매칭 발생
- `/progress/tree`: WSOP Bracelet Event → `-` (정상)
- `/progress/folder/{path}`: WSOP Bracelet Event → `4% (27/744)` (버그)

**원인**: `get_folder_detail()` 함수는 독립적으로 매칭하여 `parent_work_status_ids` 없음

**해결**:
1. `_get_ancestor_work_status_ids()` 헬퍼 함수 추가
2. `get_folder_detail()`에서 조상 폴더 매칭 ID 계산 후 제외
3. 자식 폴더 매칭 시 조상 + 현재 폴더 매칭 ID 제외

**파일**: `progress_service.py:188-240, 870, 960-978`

```python
# 조상 매칭 ID 계산
ancestor_work_status_ids = await self._get_ancestor_work_status_ids(db, folder_path, work_statuses)

# 현재 폴더 매칭 시 조상 제외
available_work_statuses = {
    cat: ws for cat, ws in work_statuses.items()
    if ws.get("id") not in ancestor_work_status_ids
}

# 자식 폴더 매칭 시 조상 + 현재 제외
parent_work_status_ids = ancestor_work_status_ids.copy()
if work_statuses_matched:
    for matched_ws in work_statuses_matched:
        if matched_ws.get("id"):
            parent_work_status_ids.add(matched_ws["id"])
```

**Issue**: #26

**상태**: ✅ RESOLVED

---

## API 엔드포인트별 Cascading 방지 상태

| API | Cascading 방지 | 상태 |
|-----|----------------|------|
| `/progress/tree` | ✅ 적용됨 | 정상 |
| `/progress/folder/{path}` | ✅ 적용됨 | 정상 (Issue #26) |
| `/progress/file/{path}` | N/A | - |

---

## 관련 파일

| 파일 | 역할 |
|------|------|
| `backend/app/services/progress_service.py` | 핵심 매칭/합산 로직 |
| `backend/app/api/progress.py` | API 엔드포인트 |
| `frontend/src/components/FolderTreeWithProgress.tsx` | 트리 렌더링 |
| `.claude/agents/progress-domain.md` | 도메인 규칙 |
| `.claude/agents/reconciliation-domain.md` | 데이터 일관성 규칙 |

---

## 테스트 커버리지

| 테스트 | 파일 | 상태 |
|--------|------|------|
| `test_cascading_match_excludes_parent_work_status` | `test_progress_matching.py` | ✅ |
| `test_cascading_match_allows_different_work_status` | `test_progress_matching.py` | ✅ |
| `test_cascading_match_empty_parent_ids` | `test_progress_matching.py` | ✅ |
| `Issue #26: Cascading Match Prevention` | `cascading-verify.spec.ts` | ✅ (E2E) |

---

## 디버깅 가이드

### Frontend 콘솔 로그
```javascript
[FolderTreeWithProgress] API 응답: {...}
[getWorkSummary] 폴더: {name} {hasWorkSummary: true/false}
```

### Backend 로그
```bash
docker-compose logs -f backend | grep "\[DEBUG\]"
```

### API 직접 호출
```bash
# 트리 API (Cascading 방지 O)
curl "http://localhost:8003/api/progress/tree?include_files=false"

# 폴더 상세 API (Cascading 방지 O) ✅
curl "http://localhost:8003/api/progress/folder/{path}?include_files=false"
```

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2025-12-11 | 1.0.0 | 문서 생성, Bug #1-#6 기록 |
| 2025-12-11 | 1.1.0 | Bug #6 해결 (Issue #26), E2E 테스트 추가 |
