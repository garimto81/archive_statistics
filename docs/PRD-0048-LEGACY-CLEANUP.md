# PRD-0048: FolderTreeWithProgress 레거시 정리

**Status**: Draft
**Created**: 2025-12-12
**Author**: Claude Code
**Related Issues**: #48, #34 (PRD-0033)

---

## 1. Executive Summary

레거시 `FolderTreeWithProgress` 컴포넌트를 삭제하고, Dashboard를 포함한 모든 페이지에서 통합 `MasterFolderTree` 컴포넌트를 사용하도록 마이그레이션합니다.

### 목표
- 코드 중복 제거 (~836줄 삭제)
- 단일 소스 원칙(Single Source of Truth) 복원
- 향후 유지보수 부담 감소

---

## 2. Background

### 2.1 현재 문제점

```
┌─────────────────────────────────────────────────────────────────┐
│                    이중 구현 문제 (블록화 원칙 위반)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FolderTreeWithProgress.tsx (656줄)  ←──┐                       │
│  └── Dashboard.tsx 사용                  │  중복 로직            │
│  └── ExtensionFilter.tsx (180줄) 의존   │                       │
│                                         │                       │
│  MasterFolderTree/index.tsx (692줄)  ←──┘                       │
│  └── Folders.tsx 사용                                           │
│  └── Statistics.tsx 사용                                        │
│  └── CompactFilterBar.tsx 내장                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 발생한 버그

- **증상**: 필터 옵션 사라지고, 필터 클릭해도 수치값 미변경
- **원인**: PRD-0041 변경 시 레거시 컴포넌트 미반영
- **근본 원인**: 동일 기능의 이중 구현

### 2.3 PRD-0033 미완성 사항

PRD-0033에서 MasterFolderTree 통합 컴포넌트를 구현했으나, Dashboard 마이그레이션이 누락됨:

| 페이지 | PRD-0033 이전 | PRD-0033 이후 |
|--------|--------------|---------------|
| Folders | FolderTree | MasterFolderTree ✅ |
| Statistics | CodecTree | MasterFolderTree ✅ |
| **Dashboard** | FolderTreeWithProgress | FolderTreeWithProgress ❌ |

---

## 3. Scope

### 3.1 In Scope

| 작업 | 파일 | 설명 |
|------|------|------|
| Dashboard 마이그레이션 | `Dashboard.tsx` | MasterFolderTree 사용으로 변경 |
| 레거시 삭제 | `FolderTreeWithProgress.tsx` | 656줄 삭제 |
| 외부 필터 삭제 | `ExtensionFilter.tsx` | 180줄 삭제 |
| 타입 정리 | `types/index.ts` | 미사용 타입 제거 (있다면) |

### 3.2 Out of Scope

- MasterFolderTree 기능 확장
- 새 필터 옵션 추가
- Backend API 변경
- 다른 페이지 변경

---

## 4. Technical Design

### 4.1 현재 Dashboard 구조

```tsx
// Dashboard.tsx (현재)
import FolderTreeWithProgress, { FolderProgressDetail } from '../components/FolderTreeWithProgress';
import ExtensionFilter from '../components/ExtensionFilter';

export default function Dashboard() {
  const [selectedExtensions, setSelectedExtensions] = useState<Set<string>>(new Set());

  return (
    <div>
      {/* 외부 필터 컴포넌트 */}
      <ExtensionFilter
        selectedExtensions={selectedExtensions}
        onChange={setSelectedExtensions}
      />

      {/* 레거시 폴더 트리 */}
      <FolderTreeWithProgress
        selectedExtensions={Array.from(selectedExtensions)}
        displayMode="progress"
        onFolderSelect={handleFolderSelect}
      />

      {/* 상세 패널 */}
      <FolderProgressDetail folder={selectedFolder} />
    </div>
  );
}
```

### 4.2 변경 후 Dashboard 구조

```tsx
// Dashboard.tsx (변경 후)
import MasterFolderTree from '../components/MasterFolderTree';
import MasterFolderDetail from '../components/MasterFolderDetail';

export default function Dashboard() {
  const [selectedFolder, setSelectedFolder] = useState<FolderWithProgress | null>(null);

  return (
    <div>
      {/* Stats Cards (유지) */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard ... />
      </div>

      {/* 통합 폴더 트리 (필터 내장) */}
      <MasterFolderTree
        // 기본 설정
        initialDepth={2}
        enableLazyLoading={true}
        enableAutoRefresh={true}
        autoRefreshInterval={60000}

        // 표시 옵션 (Dashboard = Progress 모드)
        showProgressBar={true}
        showWorkBadge={true}
        showCodecBadge={false}

        // 필터바 설정
        showFilterBar={true}
        filterBarTitle="Progress Overview"
        enableExtensionFilter={true}
        enableHiddenFilter={true}
        enableDisplayToggles={true}
        enableSearch={true}

        // 이벤트
        onFolderSelect={setSelectedFolder}
        selectedPath={selectedFolder?.path}

        // 스타일
        className="h-[500px]"
      />

      {/* 통합 상세 패널 */}
      <MasterFolderDetail
        folder={selectedFolder}
        mode="progress"
      />
    </div>
  );
}
```

### 4.3 Props 매핑

| FolderTreeWithProgress | MasterFolderTree | 비고 |
|------------------------|------------------|------|
| `selectedExtensions` | (내부 관리) | CompactFilterBar에서 처리 |
| `displayMode="progress"` | `showProgressBar={true}` | |
| `displayMode="codec"` | `showCodecBadge={true}` | |
| `onFolderSelect` | `onFolderSelect` | 동일 |
| `onFileSelect` | `onFileSelect` | 동일 |
| `initialPath` | `initialPath` | 동일 |
| `initialDepth` | `initialDepth` | 동일 |
| `showFiles` | `showFiles` | 동일 |
| `enableLazyLoading` | `enableLazyLoading` | 동일 |

### 4.4 삭제 파일 목록

```
frontend/src/components/
├── FolderTreeWithProgress.tsx     ← 삭제
├── ExtensionFilter.tsx            ← 삭제
└── MasterFolderTree/              ← 유지
    ├── index.tsx
    └── CompactFilterBar.tsx
```

---

## 5. Implementation Plan

### Phase 1: Dashboard 마이그레이션 (30분)

1. **import 변경**
   ```diff
   - import FolderTreeWithProgress, { FolderProgressDetail } from '../components/FolderTreeWithProgress';
   - import ExtensionFilter from '../components/ExtensionFilter';
   + import MasterFolderTree from '../components/MasterFolderTree';
   + import MasterFolderDetail from '../components/MasterFolderDetail';
   ```

2. **상태 관리 단순화**
   ```diff
   - const [selectedExtensions, setSelectedExtensions] = useState<Set<string>>(new Set());
   - const extensionsArray = useMemo(() => ..., [selectedExtensions]);
   // 필터 상태는 MasterFolderTree 내부에서 관리
   ```

3. **컴포넌트 교체**
   - `ExtensionFilter` 제거
   - `FolderTreeWithProgress` → `MasterFolderTree`
   - `FolderProgressDetail` → `MasterFolderDetail`

### Phase 2: 레거시 파일 삭제 (10분)

1. `FolderTreeWithProgress.tsx` 삭제
2. `ExtensionFilter.tsx` 삭제
3. ESLint/TypeScript 오류 확인

### Phase 3: 테스트 및 검증 (20분)

1. Dashboard 필터 동작 확인
2. 진행률 바 표시 확인
3. 폴더 선택 → 상세 패널 연동 확인
4. 반응형 레이아웃 확인
5. Folders, Statistics 페이지 영향 없음 확인

---

## 6. Block Index

### 6.1 Dashboard.tsx 블록 구조 (변경 후)

```
| Block ID              | Lines       | Description              |
|-----------------------|-------------|--------------------------|
| dashboard.imports     | 1-30        | import 및 타입 정의       |
| dashboard.hooks       | 32-60       | useQuery, useState        |
| dashboard.stats       | 62-120      | StatCard 섹션             |
| dashboard.tree        | 122-180     | MasterFolderTree 섹션     |
| dashboard.detail      | 182-220     | MasterFolderDetail 섹션   |
| dashboard.sources     | 222-280     | DataSourceStatus 등       |
```

### 6.2 삭제되는 블록

```
FolderTreeWithProgress.tsx 전체:
| Block ID              | Lines       | Description              |
|-----------------------|-------------|--------------------------|
| tree.types            | 44-79       | 타입 정의 (삭제)          |
| tree.helpers          | 81-154      | 헬퍼 함수 (삭제)          |
| tree.file_node        | 156-237     | FileNode (삭제)           |
| tree.folder_node      | 239-444     | FolderNode (삭제)         |
| tree.legend           | 446-490     | ProgressLegend (삭제)     |
| tree.main             | 492-658     | 메인 컴포넌트 (삭제)      |
| tree.detail_panel     | 660-916     | FolderProgressDetail (삭제)|
```

---

## 7. Risk Assessment

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| Dashboard 레이아웃 깨짐 | 낮음 | 중간 | CSS 클래스 조정 |
| Stats 쿼리 연동 실패 | 낮음 | 중간 | 기존 쿼리 로직 유지 |
| MasterFolderTree Props 누락 | 낮음 | 높음 | Props 매핑 테이블 확인 |

---

## 8. Success Criteria

- [ ] Dashboard에서 필터 정상 동작
- [ ] 진행률 바 정상 표시
- [ ] 폴더 선택 → 상세 패널 연동
- [ ] FolderTreeWithProgress.tsx 삭제됨
- [ ] ExtensionFilter.tsx 삭제됨
- [ ] TypeScript 컴파일 오류 없음
- [ ] Folders, Statistics 페이지 영향 없음

---

## 9. References

- PRD-0033: MasterFolderTree 통합 컴포넌트 구현
- PRD-0041: Archiving Progress Matching 개선
- Issue #48: FolderTreeWithProgress 삭제 및 MasterFolderTree 마이그레이션
- 근본 원인 분석 보고서 (2025-12-12)
