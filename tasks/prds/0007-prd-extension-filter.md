# PRD: 전체 파일 스캔 + 확장자 필터 GUI

**Version**: 1.0.0 | **Date**: 2025-12-10 | **Status**: In Progress
**Issue**: #7 | **Branch**: `feat/issue-7-extension-filter`

---

## 1. 개요

### 1.1 배경

- 현재 Scanner가 `.mp4` 파일만 처리 (하드코딩)
- 아카이브에는 다양한 파일 타입 존재 (mkv, avi, mov, mp3 등)
- 사용자가 전체 파일 통계를 확인하고 필터링할 수 없음

### 1.2 목표

| 목표 | 측정 지표 |
|------|----------|
| 전체 파일 스캔 | 모든 확장자 수집 |
| 확장자 필터 GUI | Dashboard에서 다중 선택 가능 |
| API 필터링 | `?extensions=mp4,mkv` 파라미터 지원 |

### 1.3 영향 블럭

| Block | 역할 | 변경사항 |
|-------|------|----------|
| `scanner.discovery` | 파일 스캔 | 확장자 제한 해제 |
| `progress.dashboard` | 대시보드 | 필터 GUI 추가 |
| `stats.api` | 통계 API | 필터 파라미터 추가 |

---

## 2. 기능 상세

### 2.1 Scanner 변경

```python
# 현재 (하드코딩)
VIDEO_EXTENSIONS = {'.mp4'}

# 변경 (설정 기반)
class Settings:
    SCAN_ALL_FILES: bool = True
    EXCLUDED_EXTENSIONS: set = {'.tmp', '.bak', '.log'}
```

### 2.2 확장자 필터 GUI

```
┌─────────────────────────────────────────────────────────────┐
│  Archive Statistics                    v1.10.0              │
├─────────────────────────────────────────────────────────────┤
│  Filter by Extension:                                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ [✓] All  [✓] mp4  [✓] mkv  [ ] avi  [ ] mov  [+3 more] ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│  Stats Cards (필터 적용된 통계)                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Files   │ │ Size    │ │ Duration│ │ Types   │           │
│  │ 12,345  │ │ 500 TB  │ │ 1,234h  │ │ 15      │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
├─────────────────────────────────────────────────────────────┤
│  Folder Tree (필터 적용)                                     │
│  📁 ARCHIVE                                                  │
│    📁 WSOP (mp4: 500, mkv: 100)                             │
│    📁 HCL (mp4: 300, mkv: 50)                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 API 변경

| Endpoint | 변경 | 예시 |
|----------|------|------|
| `GET /api/stats` | extensions 파라미터 | `?extensions=mp4,mkv` |
| `GET /api/stats/file-types` | extensions 파라미터 | `?extensions=mp4` |
| `GET /api/folders/tree` | extensions 파라미터 | `?extensions=mp4,mkv` |
| `GET /api/progress/tree` | extensions 파라미터 | `?extensions=mp4` |

---

## 3. 기술 사양

### 3.1 Backend 변경

**config.py**:
```python
SCAN_ALL_FILES: bool = True
EXCLUDED_EXTENSIONS: List[str] = ['.tmp', '.bak', '.log', '.DS_Store']
```

**scanner.py**:
```python
def should_include_file(filename: str, extension: str) -> bool:
    # 제외 확장자만 체크 (전체 파일 스캔)
    if extension.lower() in settings.EXCLUDED_EXTENSIONS:
        return False
    # 제외 키워드 체크
    # ...
    return True
```

**stats.py** (필터 파라미터):
```python
@router.get("")
async def get_stats(
    extensions: Optional[str] = Query(None, description="Comma-separated extensions"),
    db: AsyncSession = Depends(get_db)
):
    ext_list = extensions.split(",") if extensions else None
    # 필터 적용 쿼리
```

### 3.2 Frontend 변경

**ExtensionFilter.tsx** (신규):
```typescript
interface ExtensionFilterProps {
  availableExtensions: string[];
  selectedExtensions: Set<string>;
  onChange: (selected: Set<string>) => void;
}

export function ExtensionFilter({ ... }: ExtensionFilterProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {availableExtensions.map(ext => (
        <button
          key={ext}
          className={clsx(
            'px-3 py-1 rounded-full text-sm',
            selectedExtensions.has(ext)
              ? 'bg-primary-500 text-white'
              : 'bg-gray-100 text-gray-600'
          )}
          onClick={() => toggleExtension(ext)}
        >
          {ext}
        </button>
      ))}
    </div>
  );
}
```

**api.ts** (수정):
```typescript
export const statsApi = {
  getSummary: (extensions?: string[]) =>
    api.get('/stats', {
      params: { extensions: extensions?.join(',') }
    }),
  // ...
};
```

---

## 4. 체크리스트

### Phase 1: Backend 스캔 확장
- [ ] `config.py`: SCAN_ALL_FILES, EXCLUDED_EXTENSIONS 설정
- [ ] `scanner.py`: should_include_file() 수정
- [ ] 재스캔 테스트

### Phase 2: API 필터 파라미터
- [ ] `stats.py`: extensions 파라미터 추가
- [ ] `folders.py`: extensions 파라미터 추가
- [ ] `progress.py`: extensions 파라미터 추가

### Phase 3: Frontend 필터 GUI
- [ ] `ExtensionFilter.tsx` 컴포넌트 생성
- [ ] `Dashboard.tsx`: 필터 통합
- [ ] `api.ts`: extensions 파라미터 추가
- [ ] `Statistics.tsx`: 필터 연동

### Phase 4: 테스트 및 검증
- [ ] E2E 테스트: 필터 선택/해제
- [ ] API 테스트: 필터 파라미터 검증
- [ ] Docker 재빌드 및 검증

---

## 5. 참조

| 문서 | 설명 |
|------|------|
| `docs/DESIGN_CODEC_FILETYPE.md` | 코덱/파일타입 설계 |
| Issue #7 | GitHub 이슈 |
