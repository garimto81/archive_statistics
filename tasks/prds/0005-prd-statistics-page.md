# PRD: Statistics 페이지 구현

**Version**: 1.0.0 | **Date**: 2025-12-10 | **Status**: In Progress
**Issue**: #5 | **Branch**: `feat/issue-5-statistics-page`

---

## 1. 개요

### 1.1 배경

- 기존 Dashboard에서 파일 타입/용량 차트가 Progress Overview로 대체되면서 제거됨
- `/statistics` 라우트가 Placeholder로 존재
- 사용자가 파일 분석 통계를 확인할 수 있는 전용 페이지 필요

### 1.2 목표

| 목표 | 측정 지표 |
|------|----------|
| 파일 타입 분포 시각화 | 파이 차트로 Top 5 확장자 표시 |
| 저장 용량 추이 확인 | 30일간 라인 차트 |
| 폴더별 용량 비교 | Top 5 폴더 바 차트 |

### 1.3 영향 블럭

| Block | 역할 | 변경사항 |
|-------|------|----------|
| `progress.dashboard` | 통계 API | 기존 API 활용 (변경 없음) |
| Frontend Pages | UI | `Statistics.tsx` 신규 생성 |

---

## 2. 기능 상세

### 2.1 Statistics 페이지 레이아웃

```
┌─────────────────────────────────────────────────────────────────┐
│  Statistics                                                      │
├─────────────────────────────────────────────────────────────────┤
│  Stats Cards (4개)                                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │ Total   │ │ Total   │ │ Media   │ │ File    │               │
│  │ Files   │ │ Size    │ │ Duration│ │ Types   │               │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────┐  ┌─────────────────────────────┐ │
│  │ File Type Distribution    │  │ Top Folders by Size         │ │
│  │ (Pie Chart)               │  │ (Horizontal Bar)            │ │
│  │                           │  │                             │ │
│  │   .mp4  45%               │  │ WSOP    ████████████  45TB  │ │
│  │   .mkv  30%               │  │ HCL     ████████     30TB   │ │
│  │   .mov  15%               │  │ GOG     ██████       20TB   │ │
│  │   other 10%               │  │ PAD     ████         15TB   │ │
│  │                           │  │ Other   ███          10TB   │ │
│  └───────────────────────────┘  └─────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Storage Growth Trend (30 days)                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                                                    ___------ ││
│  │                                              __---           ││
│  │                                        __---                 ││
│  │                                  __---                       ││
│  │                            __---                             ││
│  │  ──────────────────────────                                  ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 사용 API

| API | 용도 | 응답 |
|-----|------|------|
| `GET /api/stats` | 전체 통계 | `StatsSummary` |
| `GET /api/stats/file-types?limit=10` | 파일 타입별 | `FileTypeStats[]` |
| `GET /api/stats/history?period=daily&days=30` | 히스토리 | `HistoryData[]` |
| `GET /api/folders/tree?depth=3` | 폴더 트리 | `FolderTreeNode[]` |

### 2.3 컴포넌트 구조

```
Statistics.tsx
├── StatCard (x4) - 기존 컴포넌트 재사용
├── FileTypeDistribution (Pie Chart)
│   └── Recharts PieChart
├── TopFoldersBySize (Bar Chart)
│   └── 직접 구현 (div + CSS width)
└── StorageGrowthTrend (Line Chart)
    └── Recharts LineChart
```

---

## 3. 기술 사양

### 3.1 프론트엔드

**파일 생성**:
- `frontend/src/pages/Statistics.tsx`

**수정 파일**:
- `frontend/src/App.tsx` - PlaceholderPage → Statistics

**의존성** (기존):
- `recharts` - 차트 라이브러리
- `@tanstack/react-query` - 데이터 페칭
- `lucide-react` - 아이콘

### 3.2 타입 정의 (기존)

```typescript
// frontend/src/types/index.ts (이미 존재)
export interface StatsSummary { ... }
export interface FileTypeStats { ... }
export interface HistoryData { ... }
export interface FolderTreeNode { ... }
```

---

## 4. 체크리스트

### Phase 1: 기본 구현

- [ ] `Statistics.tsx` 페이지 생성
- [ ] Stats Cards 섹션
- [ ] File Type Distribution (Pie Chart)
- [ ] Top Folders by Size
- [ ] Storage Growth Trend (Line Chart)
- [ ] `App.tsx` 라우터 연결

### Phase 2: E2E 테스트

- [ ] Statistics 페이지 렌더링 테스트
- [ ] 차트 컴포넌트 표시 테스트

---

## 5. 참조

| 문서 | 설명 |
|------|------|
| `docs/DESIGN_CODEC_FILETYPE.md` | 코덱 기능 설계 (미래 확장) |
| Git `01fcb30` | 원본 Dashboard.tsx (차트 코드) |
