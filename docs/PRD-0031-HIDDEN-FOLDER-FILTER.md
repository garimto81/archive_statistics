# PRD-0031: 숨김 폴더 필터링 지원

**Status**: Draft
**Issue**: [#31](https://github.com/garimto81/archive_statistics/issues/31)
**Version**: 1.30.0
**Created**: 2025-12-12

---

## 1. 개요

### 1.1 배경
v1.29.0에서 숨김 파일 필터링이 구현되었으나, 폴더는 필터링되지 않음.
NAS 환경에서 `.git`, `@eaDir`, `#recycle` 등 시스템 폴더가 트리에 노출되어 사용자 경험 저하.

### 1.2 목표
- 숨김 폴더를 기본적으로 트리에서 제외
- 기존 `include_hidden` 파라미터로 파일/폴더 통합 제어
- 스캔 시 숨김 폴더 내 파일은 DB에 저장하되, UI에서 필터링

---

## 2. 숨김 폴더 정의

### 2.1 판별 기준

| 우선순위 | 조건 | 예시 |
|----------|------|------|
| 1 | `.`으로 시작 | `.git`, `.cache`, `.svn` |
| 2 | NAS 시스템 폴더 | `@eaDir`, `#recycle`, `@tmp` |
| 3 | 개발 도구 폴더 | `__pycache__`, `node_modules` |

### 2.2 숨김 폴더 목록

```python
HIDDEN_FOLDER_PREFIXES = ('.', '@', '#')

HIDDEN_FOLDER_NAMES = {
    # 버전 관리
    '.git', '.svn', '.hg', '.bzr',
    # 캐시/임시
    '.cache', '.tmp', '.temp',
    # NAS 시스템 (Synology)
    '@eaDir', '@tmp', '#recycle', '#snapshot',
    # 개발 도구
    '__pycache__', 'node_modules', '.venv', 'venv',
    # IDE
    '.idea', '.vscode',
}
```

---

## 3. 구현 설계

### 3.1 DB 모델 변경

**파일:** `backend/app/models/folder_stats.py`

```python
class FolderStats(Base):
    # 기존 필드...
    is_hidden = Column(Boolean, default=False, index=True)  # 추가
```

### 3.2 스캐너 변경

**파일:** `backend/app/services/scanner.py`

```python
def _is_hidden_folder(self, folder_name: str) -> bool:
    """폴더가 숨김 대상인지 판별"""
    # 접두사 검사
    if folder_name.startswith(('.', '@', '#')):
        return True
    # 이름 검사
    if folder_name.lower() in HIDDEN_FOLDER_NAMES:
        return True
    return False
```

**스캔 시 적용:**
```python
# _scan_folder() 내
is_hidden = self._is_hidden_folder(entry.name)
folder_info = {
    ...
    "is_hidden": is_hidden,
}
```

### 3.3 Progress Service 변경

**파일:** `backend/app/services/progress_service.py`

```python
async def _build_folder_progress(
    self, ..., include_hidden: bool = False
) -> Dict[str, Any]:
    # 폴더 쿼리에 숨김 필터 추가
    query = select(FolderStats).where(...)

    if not include_hidden:
        query = query.where(FolderStats.is_hidden == False)
```

### 3.4 API 변경 없음

기존 `include_hidden` 파라미터가 파일 + 폴더 모두 제어하므로 API 변경 불필요.

---

## 4. 마이그레이션

### 4.1 DB 마이그레이션

```sql
-- folder_stats 테이블에 is_hidden 컬럼 추가
ALTER TABLE folder_stats ADD COLUMN is_hidden BOOLEAN DEFAULT 0;
CREATE INDEX ix_folder_stats_is_hidden ON folder_stats(is_hidden);

-- 기존 데이터 업데이트 (이름 기반)
UPDATE folder_stats SET is_hidden = 1
WHERE name LIKE '.%'
   OR name LIKE '@%'
   OR name LIKE '#%'
   OR name IN ('__pycache__', 'node_modules', 'venv', '.venv');
```

### 4.2 재스캔 권장

마이그레이션 후 전체 스캔 실행하여 `is_hidden` 플래그 정확히 설정.

---

## 5. 테스트 계획

### 5.1 단위 테스트

```python
# tests/test_hidden_folder.py
def test_hidden_folder_detection():
    """숨김 폴더 판별 테스트"""
    assert _is_hidden_folder('.git') == True
    assert _is_hidden_folder('@eaDir') == True
    assert _is_hidden_folder('normal_folder') == False

def test_hidden_folder_filter():
    """API 필터링 테스트"""
    # include_hidden=false: 숨김 폴더 제외
    # include_hidden=true: 숨김 폴더 포함
```

### 5.2 E2E 테스트

```typescript
// tests/e2e/test_hidden_folder.spec.ts
test('숨김 폴더가 기본적으로 숨겨짐', async ({ page }) => {
  // 토글 OFF 상태에서 @eaDir 폴더가 보이지 않아야 함
});

test('토글 ON 시 숨김 폴더 표시', async ({ page }) => {
  // 토글 클릭 후 @eaDir 폴더가 보여야 함
});
```

---

## 6. 작업 체크리스트

- [ ] **Backend**
  - [ ] `FolderStats` 모델에 `is_hidden` 컬럼 추가
  - [ ] `scanner.py`에 `_is_hidden_folder()` 함수 추가
  - [ ] 스캔 로직에서 폴더 숨김 플래그 설정
  - [ ] `progress_service.py` 폴더 쿼리에 필터 추가

- [ ] **Database**
  - [ ] ALTER TABLE 마이그레이션
  - [ ] 기존 데이터 UPDATE

- [ ] **Testing**
  - [ ] 단위 테스트 작성
  - [ ] E2E 테스트 작성

- [ ] **Documentation**
  - [ ] CLAUDE.md 버전 업데이트
  - [ ] CHANGELOG 작성

---

## 7. 영향 범위

| 영역 | 영향 |
|------|------|
| DB 스키마 | `folder_stats` 테이블 컬럼 추가 |
| 스캐너 | 폴더 스캔 시 `is_hidden` 설정 |
| API | 변경 없음 (기존 파라미터 활용) |
| Frontend | 변경 없음 (기존 토글 활용) |

---

## 8. 롤백 계획

1. 컬럼 삭제: `ALTER TABLE folder_stats DROP COLUMN is_hidden`
2. 이전 버전 코드 배포
3. Docker 재빌드

---

## 9. 일정

| 단계 | 예상 |
|------|------|
| 구현 | 1시간 |
| 테스트 | 30분 |
| 배포 | 15분 |
| **총계** | **~2시간** |
