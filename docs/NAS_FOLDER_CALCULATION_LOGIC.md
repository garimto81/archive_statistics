# NAS 폴더 계산 로직 분석

**Version**: 1.0.0 | **Date**: 2025-12-13 | **Status**: Issue Analysis

이 문서는 NAS 폴더 통계 계산 로직을 분석하고, 현재 발견된 문제점과 개선 방안을 제시합니다.

---

## 1. 전체 아키텍처

```mermaid
flowchart TB
    subgraph API["API Layer"]
        endpoint["/api/progress/tree"]
    end

    subgraph Service["Progress Service"]
        main["get_folder_with_progress()"]
        rootStats["_calculate_root_stats()"]
        buildFolder["_build_folder_progress()"]
        loadWS["_load_work_statuses()"]
        loadHA["_load_hand_analysis_data()"]
        matchWS["_match_work_statuses()"]
        validate["validate_match()"]
        getFiles["_get_files_with_matching()"]
    end

    subgraph DB["Database"]
        folderStats[(FolderStats)]
        fileStats[(FileStats)]
        workStatus[(WorkStatus)]
        handAnalysis[(HandAnalysis)]
    end

    endpoint --> main
    main --> rootStats
    main --> loadWS
    main --> loadHA
    main --> buildFolder

    rootStats --> folderStats
    rootStats --> workStatus
    loadWS --> workStatus
    loadHA --> handAnalysis

    buildFolder --> matchWS
    buildFolder --> validate
    buildFolder --> getFiles
    buildFolder -->|재귀| buildFolder

    getFiles --> fileStats
```

---

## 2. 데이터 소스별 통계 계산 방식

### 2.1 데이터 소스 개요

```mermaid
flowchart LR
    subgraph Sources["데이터 소스"]
        NAS["NAS 스캔<br/>(FolderStats/FileStats)"]
        Sheets["Google Sheets<br/>(WorkStatus)"]
        Meta["Hand Analysis<br/>(HandAnalysis)"]
    end

    subgraph Values["계산되는 값들"]
        fileCount["file_count<br/>folder_count"]
        filtered["filtered_file_count<br/>filtered_size"]
        workSummary["work_summary<br/>(task_count, progress)"]
        handSummary["hand_analysis<br/>(files_matched, hand_count)"]
    end

    NAS --> fileCount
    NAS --> filtered
    Sheets --> workSummary
    Meta --> handSummary
```

### 2.2 각 통계 값의 계산 방식

| 값 | 소스 | 계산 방식 | 하위 폴더 포함 |
|----|------|----------|---------------|
| `file_count` | FolderStats | DB에 저장된 값 | ✅ 포함 (스캔 시 계산) |
| `folder_count` | FolderStats | DB에 저장된 값 | ✅ 포함 |
| `filtered_file_count` | FileStats | DB 쿼리로 집계 | ✅ `startswith(folder.path)` |
| `filtered_size` | FileStats | DB 쿼리로 집계 | ✅ `startswith(folder.path)` |
| `work_summary.total_done` | WorkStatus | 직접 매칭만 합산 | ❌ 자식 합산 안함 |
| `hand_analysis.files_matched` | HandAnalysis | 직접 + 자식 합산 | ✅ 재귀 합산 |
| `hand_analysis.hand_count` | HandAnalysis | 직접 + 자식 합산 | ✅ 재귀 합산 |

---

## 3. filtered_file_count 계산 흐름

```mermaid
sequenceDiagram
    participant API as API
    participant Service as ProgressService
    participant DB as Database

    API->>Service: get_folder_with_progress(path, include_hidden=false)

    loop 각 폴더에 대해
        Service->>Service: _build_folder_progress(folder)

        alt extensions 또는 include_hidden=false
            Service->>DB: SELECT COUNT(*), SUM(size), SUM(duration)<br/>FROM FileStats<br/>WHERE folder_path LIKE 'folder.path%'<br/>AND NOT name LIKE '.%'
            DB-->>Service: filtered_count, filtered_size, filtered_duration
            Service->>Service: folder_dict["filtered_file_count"] = filtered_count
        else include_hidden=true AND extensions=None
            Service->>Service: folder_dict["filtered_file_count"] = folder.file_count
        end

        Note over Service: 자식 폴더 재귀 처리 시<br/>합산하지 않음 (v1.35.1 수정)
    end
```

### 3.1 현재 로직 (v1.35.1)

```python
# progress_service.py:697-729
if extensions or not include_hidden:
    filtered_query = (
        select(
            func.count(FileStats.id).label("count"),
            func.coalesce(func.sum(FileStats.size), 0).label("total_size"),
            func.coalesce(func.sum(FileStats.duration), 0).label("total_duration"),
        )
        .where(FileStats.folder_path.startswith(folder.path))  # ⚠️ 하위 폴더 포함
    )
    if extensions:
        filtered_query = filtered_query.where(FileStats.extension.in_(extensions))
    if not include_hidden:
        filtered_query = filtered_query.where(~FileStats.name.startswith('.'))
```

**핵심 포인트**:
- `folder_path.startswith(folder.path)`로 **하위 폴더의 모든 파일 포함**
- 자식 폴더에서 다시 집계하면 **중복 집계 발생**

---

## 4. 문제 분석: 서브 폴더마다 합산 값이 다른 현상

### 4.1 문제 시나리오

```mermaid
flowchart TB
    subgraph Problem["문제 상황"]
        nas["nas<br/>filtered: 1,444<br/>total: 1,912"]
        wsop["WSOP<br/>filtered: 1,348<br/>total: 1,912 ❓"]
        archive["WSOP ARCHIVE<br/>filtered: 545<br/>total: 1,912 ❓"]
        y2010["WSOP 2010<br/>filtered: 36<br/>total: 1,912 ❓"]
    end

    nas --> wsop
    wsop --> archive
    archive --> y2010

    note1[/"total이 모든 폴더에서<br/>루트 전체값(1,912)으로 표시됨"/]
```

### 4.2 근본 원인

```mermaid
flowchart LR
    subgraph Issue["문제 원인"]
        A["root_stats.total_files<br/>= 전체 파일 수"]
        B["모든 폴더에<br/>동일한 root_stats 전달"]
        C["UI에서 'filtered/total' 형식으로<br/>표시"]
    end

    A --> B --> C

    D["결과: 모든 폴더가<br/>36/1,912 형식으로 표시"]
```

**문제 코드 위치**:

1. **root_stats 계산** (`progress_service.py:190-260`):
   - 전체 ARCHIVE의 파일 수를 계산
   - 모든 폴더에 동일한 값 전달

2. **folder_dict에 root_stats 설정** (`progress_service.py:731-752`):
   ```python
   folder_dict["root_stats"] = {
       "total_files": root_total_files,  # 전체 루트 파일 수
       "total_size": root_total_size,
       ...
   }
   ```

3. **프론트엔드 표시** (`MasterFolderTree/index.tsx:331-341`):
   ```jsx
   {folder.root_stats ? (
       <>
           <span>{folder.filtered_file_count}</span>
           /{folder.root_stats.total_files}  // ← 모든 폴더에서 동일한 값
       </>
   )}
   ```

---

## 5. 통계 값들의 관계 다이어그램

```mermaid
erDiagram
    FolderStats {
        int id PK
        string path
        int file_count "하위 폴더 포함 파일 수"
        int folder_count "하위 폴더 수"
        bigint total_size "하위 폴더 포함 용량"
        float total_duration "하위 폴더 포함 재생시간"
        int depth "폴더 깊이"
    }

    FileStats {
        int id PK
        string name
        string folder_path FK "직접 부모 폴더 경로"
        bigint size
        float duration
        string extension
        string video_codec
        string audio_codec
    }

    WorkStatus {
        int id PK
        string category "매칭 기준 키워드"
        int total_videos "시트 기준 총 비디오"
        int excel_done "시트 기준 완료 수"
    }

    FolderStats ||--o{ FileStats : "folder_path"
    FolderStats ||--o| WorkStatus : "fuzzy matching"
```

---

## 6. 계산 흐름 상세

### 6.1 filtered_* 계산

```mermaid
stateDiagram-v2
    [*] --> CheckFilter: _build_folder_progress 시작

    CheckFilter --> DBQuery: extensions 또는 include_hidden=false
    CheckFilter --> UseStored: include_hidden=true AND extensions=None

    DBQuery --> SetFiltered: 쿼리 결과 저장
    UseStored --> SetFiltered: folder.file_count 사용

    SetFiltered --> ProcessChildren: 자식 폴더 처리
    ProcessChildren --> ProcessChildren: 재귀 호출
    ProcessChildren --> [*]: 완료

    note right of DBQuery
        SELECT COUNT(*), SUM(size)
        FROM FileStats
        WHERE folder_path LIKE 'path%'
        AND NOT name LIKE '.%'
    end note

    note right of ProcessChildren
        v1.35.1: 자식 합산 제거
        (중복 집계 방지)
    end note
```

### 6.2 work_summary 계산

```mermaid
stateDiagram-v2
    [*] --> CheckFK: work_status 매칭 시작

    CheckFK --> UseFK: folder.work_status_id 있음
    CheckFK --> FuzzyMatch: FK 없음

    UseFK --> SetMatched: work_statuses_matched = [ws]

    FuzzyMatch --> FilterAvailable: 상위에서 사용된 ID 제외
    FilterAvailable --> MatchCategory: 카테고리 매칭
    MatchCategory --> SetMatched: 매칭 성공
    MatchCategory --> NoMatch: 매칭 실패

    SetMatched --> Validate: validate_match()
    Validate --> CalcSummary: 유효한 매칭
    Validate --> Invalidate: 불일치 > 30%

    CalcSummary --> [*]: work_summary 설정
    Invalidate --> [*]: work_summary = None
    NoMatch --> [*]: work_summary = None

    note right of FilterAvailable
        Cascading Match 방지:
        parent_work_status_ids에서
        이미 사용된 ID 제외
    end note
```

---

## 7. 문제점 및 개선 방안

### 7.1 현재 문제점

```mermaid
flowchart TB
    subgraph Problems["발견된 문제점"]
        P1["1. Lazy Load마다<br/>root_stats가 재계산됨"]
        P2["2. 각 레벨마다<br/>다른 total 값 표시"]
        P3["3. UI에서 의미 불명확한<br/>숫자 표시"]
    end

    subgraph Causes["원인"]
        C1["_calculate_root_stats(path)가<br/>path 기준으로 계산"]
        C2["Lazy Load 요청마다<br/>다른 path 전달"]
        C3["프론트엔드에서<br/>root_stats를 덮어쓰지 않음"]
    end

    P1 --> C1
    P1 --> C2
    P2 --> C1
    P3 --> C3
```

### 7.2 Lazy Load와 root_stats 불일치 분석

```mermaid
sequenceDiagram
    participant UI as Frontend
    participant API as Backend API
    participant Service as ProgressService

    Note over UI: 초기 로드
    UI->>API: GET /tree?depth=1 (path=None)
    API->>Service: _calculate_root_stats(path=None)
    Service-->>API: root_stats = {total_files: 1912}
    API-->>UI: 모든 폴더에 1912 전달

    Note over UI: WSOP 확장 (Lazy Load)
    UI->>API: GET /tree?path=/mnt/nas/WSOP&depth=1
    API->>Service: _calculate_root_stats(path=WSOP)
    Service-->>API: root_stats = {total_files: 1811}
    API-->>UI: WSOP 하위 폴더에 1811 전달

    Note over UI: WSOP ARCHIVE 확장 (Lazy Load)
    UI->>API: GET /tree?path=WSOP ARCHIVE&depth=1
    API->>Service: _calculate_root_stats(path=WSOP ARCHIVE)
    Service-->>API: root_stats = {total_files: 1017}
    API-->>UI: ARCHIVE 하위 폴더에 1017 전달
```

### 7.3 실제 데이터 예시

| 로드 단계 | API path | root_stats.total_files | UI 표시 |
|----------|----------|------------------------|---------|
| 초기 | None | **1912** | nas: 1,444/1,912 |
| Lazy 1 | /mnt/nas/WSOP | **1811** | WSOP: 1,348/1,811 |
| Lazy 2 | WSOP ARCHIVE | **1017** | ARCHIVE: 545/1,017 |
| Lazy 3 | WSOP 2010 | **72** | 2010: 36/72 |

### 7.4 개선 방안

```mermaid
flowchart LR
    subgraph Solutions["개선 방안"]
        S1["방안 A: UI 수정<br/>root_stats 대신<br/>folder.file_count 사용"]
        S2["방안 B: 프론트엔드에서<br/>초기 root_stats 캐싱"]
        S3["방안 C: API 수정<br/>항상 전체 root_stats 반환"]
    end

    S1 --> Result1["빠른 수정<br/>가장 간단"]
    S2 --> Result2["일관된 비율 표시<br/>프론트 변경만 필요"]
    S3 --> Result3["정확한 데이터<br/>API 변경 필요"]
```

### 7.5 방안별 상세 설명

#### 방안 A: UI에서 folder.file_count 사용 (권장)
- **변경**: `root_stats.total_files` 대신 `folder.file_count` 사용
- **장점**: 즉시 적용 가능, 각 폴더의 실제 파일 수 표시
- **단점**: 전체 대비 비율 표시 불가

#### 방안 B: 프론트엔드에서 초기 root_stats 캐싱
- **변경**: 초기 로드 시 root_stats를 상태로 저장, lazy load 결과에 적용
- **장점**: 일관된 비율 표시
- **단점**: 상태 관리 복잡도 증가

#### 방안 C: API에서 항상 전체 root_stats 반환
- **변경**: `_calculate_root_stats(path=None)` 항상 사용
- **장점**: 모든 폴더에서 일관된 전체 대비 비율
- **단점**: API 응답 의미 변경, 기존 동작 변경

---

## 8. 권장 해결 방안

### 8.1 즉시 적용 가능한 수정 (방안 A)

**위치**: `frontend/src/components/MasterFolderTree/index.tsx:331-355`

**현재 코드**:
```jsx
{folder.root_stats ? (
    <>
        <span>{folder.filtered_file_count}</span>
        /{folder.root_stats.total_files}  // ← 문제: 루트 전체 파일 수
    </>
) : (
    <>
        <span>{folder.filtered_file_count}</span>
        {' files'}
    </>
)}
```

**수정 제안**:
```jsx
{folder.root_stats ? (
    <>
        <span className={folder.filtered_file_count !== folder.file_count ? 'text-blue-600' : ''}>
            {folder.filtered_file_count?.toLocaleString()}
        </span>
        /{folder.file_count.toLocaleString()}  // ← 수정: 폴더 자체 파일 수
        <span className="text-gray-300 mx-1">·</span>
        <span className="text-gray-400">
            ({((folder.file_count / folder.root_stats.total_files) * 100).toFixed(1)}%)
        </span>
    </>
)}
```

### 8.2 표시 형식 예시

| 현재 | 개선 후 |
|------|---------|
| 36/1,912 또는 36/1,017 또는 36/72 (불일치) | 36/72 files (필터링/폴더전체) |
| 1,348/1,811 (lazy load 기준) | 1,348/1,912 files (70.4% of archive) |

---

## 9. 문제 요약

### 두 가지 문제점

1. **Lazy Load마다 root_stats 재계산**
   - 초기: 1912 (전체)
   - WSOP: 1811 (WSOP 기준)
   - ARCHIVE: 1017 (ARCHIVE 기준)
   - 결과: 같은 트리에서 다른 total 표시

2. **root_stats.total_files의 의미 혼란**
   - 설계 의도: 전체 대비 비율 표시
   - 실제 사용: filtered/total 형식 표시
   - 결과: 의미 불명확한 숫자

### 핵심 코드 위치

| 파일 | 라인 | 설명 |
|------|------|------|
| `progress_service.py` | 128 | root_stats 계산 호출 |
| `progress_service.py` | 190-260 | `_calculate_root_stats()` - path별 계산 |
| `progress_service.py` | 731-752 | folder_dict에 root_stats 설정 |
| `MasterFolderTree/index.tsx` | 331-355 | UI 표시 로직 |

---

## 10. 참조

- **핵심 파일**: `backend/app/services/progress_service.py`
- **Block Index**: 파일 상단 주석 참조
- **관련 Issue**: #29 (NAS/Sheets 데이터 분리 표시)
- **관련 PRD**: PRD-0041 (매칭 검증)

---

## 변경 이력

| 버전 | 날짜 | 변경 |
|------|------|------|
| 1.1.0 | 2025-12-13 | Lazy Load root_stats 불일치 문제 분석 추가 |
| 1.0.0 | 2025-12-13 | 초기 문서 작성 (Issue 분석용) |
