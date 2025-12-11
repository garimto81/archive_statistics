# Components Block Agent Rules

AI 에이전트를 위한 Frontend Components 도메인 가이드.

## Identity
- **Role**: React 컴포넌트 개발 전문가
- **Domain**: Progress, Codec, UI
- **Scope**: `frontend/src/components/` 내부만

## Files in Scope

| File | Block ID | 책임 |
|------|----------|------|
| `FolderTreeWithProgress.tsx` | `tree.*` | 폴더 트리 + 진행률 표시 (핵심) |
| `CodecFolderDetail.tsx` | `components.codec-detail` | 코덱 상세 정보 패널 |
| `ProgressBar.tsx` | `components.progress-bar` | 진행률 바 컴포넌트 |
| `FolderTree.tsx` | - | 기본 폴더 트리 (레거시) |
| `StatCard.tsx` | - | 통계 카드 UI |

---

## 핵심 파일: FolderTreeWithProgress.tsx (946 lines)

### Block Index

| Block ID | Lines | Description | When to Read |
|----------|-------|-------------|--------------|
| `tree.types` | 44-79 | Props 및 내부 타입 정의 | 컴포넌트 구조 이해 |
| `tree.helpers` | 81-154 | getWorkSummary 등 유틸리티 | work_summary 계산 디버깅 |
| `tree.file_node` | 156-237 | FileNode 컴포넌트 | 파일 표시 UI 수정 |
| `tree.folder_node` | 239-444 | FolderNode 컴포넌트 | 폴더 트리 UI, Lazy Loading |
| `tree.legend` | 446-490 | ProgressLegend 컴포넌트 | 범례 UI 수정 |
| `tree.main` | 492-658 | 메인 export 컴포넌트 | API 호출, 상태관리 |
| `tree.detail_panel` | 660-916 | FolderProgressDetail | 상세 패널 UI |

### Display Modes

```typescript
type DisplayMode = 'progress' | 'codec';
```

- `progress`: 작업 진행률 표시 (기본값)
- `codec`: 코덱 정보 표시 (Codec Explorer)

### 주요 Props

```typescript
interface FolderTreeWithProgressProps {
  initialPath?: string;        // 시작 경로
  initialDepth?: number;       // 초기 깊이 (기본: 2)
  showFiles?: boolean;         // 파일 표시 여부
  displayMode?: DisplayMode;   // progress | codec
  enableLazyLoading?: boolean; // Lazy Loading 활성화
  onFolderSelect?: (folder: FolderWithProgress) => void;
  onFileSelect?: (file: FileWithProgress) => void;
}
```

---

## 타입 의존성

```
types/index.ts
├── FolderWithProgress
│   ├── work_summary?: WorkSummary    // 진행률 데이터
│   ├── codec_summary?: FolderCodecSummary  // 코덱 데이터
│   └── children: FolderWithProgress[]
├── FileWithProgress
│   ├── metadata_progress?: MetadataProgress
│   ├── video_codec?: string
│   └── audio_codec?: string
└── WorkSummary
    ├── task_count, total_files, total_done
    ├── combined_progress
    └── sheets_total_videos, sheets_excel_done
```

---

## API 의존성

```typescript
// services/api.ts - progressApi
progressApi.getTreeWithProgress(
  path?,           // 시작 경로
  depth?,          // 깊이
  includeFiles?,   // 파일 포함
  extensions?,     // 확장자 필터
  includeCodecs?   // 코덱 정보 포함
)

progressApi.getFolderDetail(path, includeFiles?)
```

---

## Constraints

### DO
- Block 마커 유지 (`// === BLOCK: xxx ===`)
- TypeScript 타입 명시
- React Query 캐시 활용
- Tailwind CSS 클래스 사용

### DON'T
- `any` 타입 사용 최소화
- 직접 API fetch 금지 (progressApi 사용)
- 인라인 스타일 금지
- console.log 프로덕션에서 제거 (DEBUG_WORK_SUMMARY 플래그로 제어)

---

## 디버깅 가이드

1. **work_summary 누락**: `tree.helpers` 블록의 `getWorkSummary()` 확인
2. **Lazy Loading 오류**: `tree.folder_node`의 `handleClick` 확인
3. **코덱 정보 미표시**: `displayMode === 'codec'` 분기 확인
4. **API 응답 오류**: `tree.main`의 useQuery 확인

---

## 컴포넌트 관계도

```
Statistics.tsx (page)
├── FolderTreeWithProgress (displayMode="codec")
└── CodecFolderDetail (선택된 폴더)

Dashboard.tsx (page)
├── FolderTreeWithProgress (displayMode="progress")
└── FolderProgressDetail (선택된 폴더)
```
