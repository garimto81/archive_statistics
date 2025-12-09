# 영상 분석 완료 기준 설계 명세서

**버전**: 1.0.0
**작성일**: 2025-12-09
**상태**: Approved (데이터 검증 완료)

---

## 1. 개요

### 1.1 목적

NAS 아카이브 영상의 핸드 분석 작업 완료 여부를 **영상 길이 기반 90%** 기준으로 판정하는 시스템 설계.

### 1.2 핵심 원칙

```
하나의 영상 = 수백 개의 핸드
완료 기준 = 영상 길이의 90% 지점까지 분석 완료
```

### 1.3 데이터 검증 결과 (2025-12-09)

| 항목 | 값 |
|------|-----|
| 분석 데이터 | WSOP HAND SELECTION - 2025 WSOP Clip Tracker.csv |
| 총 핸드 레코드 | 314개 |
| 고유 영상(이벤트) | 62개 |
| 평균 핸드/영상 | 5.1개 |
| 다중 핸드 영상 (2개+) | 54개 (87%) |

**검증 결론**: ✅ 90% 완료 기준은 실제 데이터에서 합리적으로 적용 가능

---

## 2. 완료 판정 공식

### 2.1 기본 공식

```
완료 = MAX(time_end) ≥ video_duration × 0.9
```

| 변수 | 설명 | 단위 |
|------|------|------|
| `video_duration` | 영상 전체 길이 | 초 |
| `MAX(time_end)` | 분석된 핸드 중 가장 늦은 종료 타임코드 | 초 |
| `0.9` | 완료 기준 (90%) | - |

### 2.2 판정 예시

```
영상: WSOP_2024_Main_Event_Day2.mp4
├── 영상 길이 (D): 7,200초 (2시간)
├── 90% 기준점: 6,480초 (1시간 48분)
│
├── 케이스 A: MAX(time_end) = 6,500초
│   └── 6,500 ≥ 6,480 → ✅ 완료 (90.3%)
│
└── 케이스 B: MAX(time_end) = 5,000초
    └── 5,000 < 6,480 → 🔄 진행중 (69.4%)
```

### 2.3 완료 상태 분류

| 상태 | 조건 | 아이콘 | 설명 |
|------|------|--------|------|
| **COMPLETE** | progress ≥ 90% | ✅ | 분석 완료 |
| **IN_PROGRESS** | 10% ≤ progress < 90% | 🔄 | 진행 중 |
| **STARTED** | 0% < progress < 10% | 🔸 | 시작됨 |
| **NOT_STARTED** | progress = 0% 또는 핸드 없음 | ⏳ | 미시작 |

---

## 3. 데이터베이스 스키마

### 3.1 테이블 설계

```sql
-- ============================================
-- 1. 영상 파일 테이블 (NAS 스캔 결과)
-- ============================================
CREATE TABLE video_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 파일 식별
    file_path TEXT NOT NULL UNIQUE,       -- NAS 전체 경로
    file_name TEXT NOT NULL,               -- 파일명
    file_hash TEXT,                        -- MD5 해시 (중복 방지)

    -- 영상 메타데이터 (ffprobe)
    duration_sec REAL NOT NULL,            -- 영상 길이 (초)
    duration_formatted TEXT,               -- "HH:MM:SS" 형식

    -- 계층 구조
    archive TEXT NOT NULL,                 -- L1: WSOP, HCL, MPP
    category TEXT,                         -- L2: Bracelet Event
    subcategory TEXT,                      -- L3: WSOP-LAS VEGAS
    year INTEGER,                          -- L4: 2024

    -- 파일 정보
    file_size_bytes INTEGER,
    codec TEXT,
    resolution TEXT,                       -- "1920x1080"

    -- 메타
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_video_archive ON video_files(archive);
CREATE INDEX idx_video_year ON video_files(year);

-- ============================================
-- 2. 핸드 분석 테이블 (Google Sheets 데이터)
-- ============================================
CREATE TABLE hand_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 영상 연결
    video_file_id INTEGER REFERENCES video_files(id),

    -- 타임코드
    timecode_in_sec REAL NOT NULL,         -- 핸드 시작 (초)
    timecode_out_sec REAL NOT NULL,        -- 핸드 종료 (초)
    timecode_in_formatted TEXT,            -- "HH:MM:SS"
    timecode_out_formatted TEXT,           -- "HH:MM:SS"

    -- 핸드 메타데이터
    players TEXT,                          -- "IVEY vs DWAN"
    hands TEXT,                            -- "AA vs KK"
    hand_grade TEXT,                       -- "★", "★★", "★★★"

    -- 태그
    poker_play_tags TEXT,                  -- JSON: ["bluff", "cooler"]
    emotion_tags TEXT,                     -- JSON: ["dramatic"]

    -- 원본 참조
    source_sheet TEXT,                     -- 시트 이름
    source_row TEXT,                       -- 시트 행 번호

    -- 메타
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hand_video ON hand_analysis(video_file_id);
CREATE INDEX idx_hand_timecode ON hand_analysis(timecode_out_sec);

-- ============================================
-- 3. 진행률 계산 뷰
-- ============================================
CREATE VIEW video_progress AS
SELECT
    vf.id,
    vf.file_name,
    vf.file_path,
    vf.archive,
    vf.category,
    vf.year,
    vf.duration_sec,
    vf.duration_formatted,

    -- 핸드 집계
    COUNT(ha.id) AS hand_count,
    MAX(ha.timecode_out_sec) AS max_timecode_sec,

    -- 진행률 계산
    CASE
        WHEN vf.duration_sec > 0 AND MAX(ha.timecode_out_sec) IS NOT NULL
        THEN ROUND(MAX(ha.timecode_out_sec) / vf.duration_sec * 100, 1)
        ELSE 0
    END AS progress_percent,

    -- 90% 기준점
    vf.duration_sec * 0.9 AS threshold_sec,

    -- 완료 상태
    CASE
        WHEN MAX(ha.timecode_out_sec) >= vf.duration_sec * 0.9 THEN 'COMPLETE'
        WHEN MAX(ha.timecode_out_sec) >= vf.duration_sec * 0.1 THEN 'IN_PROGRESS'
        WHEN MAX(ha.timecode_out_sec) > 0 THEN 'STARTED'
        ELSE 'NOT_STARTED'
    END AS status

FROM video_files vf
LEFT JOIN hand_analysis ha ON vf.id = ha.video_file_id
GROUP BY vf.id;

-- ============================================
-- 4. Archive별 집계 뷰
-- ============================================
CREATE VIEW archive_summary AS
SELECT
    archive,
    COUNT(*) AS total_files,
    SUM(CASE WHEN status = 'COMPLETE' THEN 1 ELSE 0 END) AS completed,
    SUM(CASE WHEN status = 'IN_PROGRESS' THEN 1 ELSE 0 END) AS in_progress,
    SUM(CASE WHEN status = 'STARTED' THEN 1 ELSE 0 END) AS started,
    SUM(CASE WHEN status = 'NOT_STARTED' THEN 1 ELSE 0 END) AS not_started,
    ROUND(SUM(CASE WHEN status = 'COMPLETE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS completion_rate
FROM video_progress
GROUP BY archive;
```

### 3.2 ERD

```
┌─────────────────┐       ┌─────────────────┐
│  video_files    │       │  hand_analysis  │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │───┐   │ id (PK)         │
│ file_path       │   │   │ video_file_id(FK)│──┘
│ file_name       │   └──>│ timecode_in_sec │
│ duration_sec    │       │ timecode_out_sec│
│ archive         │       │ players         │
│ category        │       │ hands           │
│ year            │       │ hand_grade      │
└─────────────────┘       └─────────────────┘
         │
         ▼
┌─────────────────┐
│ video_progress  │ (VIEW)
├─────────────────┤
│ progress_percent│
│ max_timecode_sec│
│ status          │
└─────────────────┘
```

---

## 4. API 설계

### 4.1 엔드포인트 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/progress/summary` | 전체 진행률 요약 |
| GET | `/api/progress/by-archive` | Archive별 진행률 |
| GET | `/api/progress/by-category/{archive}` | Category별 진행률 |
| GET | `/api/progress/files` | 파일 목록 (필터/페이징) |
| GET | `/api/progress/files/{id}` | 개별 파일 상세 |
| POST | `/api/progress/sync` | Google Sheets CSV 동기화 |

### 4.2 응답 스키마

#### GET /api/progress/summary

```json
{
  "total_files": 1902,
  "total_duration_hours": 8500,
  "by_status": {
    "complete": 150,
    "in_progress": 200,
    "started": 50,
    "not_started": 1502
  },
  "overall_progress_percent": 7.9,
  "last_synced_at": "2025-12-09T10:30:00Z"
}
```

#### GET /api/progress/by-archive

```json
{
  "archives": [
    {
      "name": "WSOP",
      "total_files": 1802,
      "complete": 140,
      "in_progress": 180,
      "started": 45,
      "not_started": 1437,
      "completion_rate": 7.8
    },
    {
      "name": "HCL",
      "total_files": 45,
      "complete": 5,
      "in_progress": 10,
      "started": 3,
      "not_started": 27,
      "completion_rate": 11.1
    }
  ]
}
```

#### GET /api/progress/files/{id}

```json
{
  "id": 123,
  "file_name": "WSOP_2024_Main_Event_Day2.mp4",
  "file_path": "\\\\10.10.100.122\\...",
  "archive": "WSOP",
  "category": "Main Event",
  "year": 2024,

  "duration": {
    "seconds": 25200,
    "formatted": "07:00:00"
  },

  "progress": {
    "max_timecode_sec": 23400,
    "max_timecode_formatted": "06:30:00",
    "threshold_sec": 22680,
    "threshold_formatted": "06:18:00",
    "percent": 92.9,
    "status": "COMPLETE"
  },

  "hands": {
    "count": 45,
    "items": [
      {
        "id": 1,
        "in": "00:12:30",
        "out": "00:15:45",
        "players": "IVEY vs DWAN",
        "hands": "AA vs KK",
        "grade": "★★★"
      }
    ]
  }
}
```

---

## 5. 프론트엔드 UI 설계

### 5.1 진행률 대시보드

```
┌─────────────────────────────────────────────────────────────────────┐
│                     📊 작업 진행률 대시보드                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │  1,902   │  │   150    │  │   250    │  │  7.9%    │            │
│  │ 총 영상  │  │ ✅ 완료  │  │ 🔄 진행  │  │ 완료율   │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Archive별 진행률                                             │    │
│  │                                                              │    │
│  │ WSOP      ████████░░░░░░░░░░░░░░░░░░░░░░░  7.8% (140/1802)  │    │
│  │ HCL       ██████████░░░░░░░░░░░░░░░░░░░░░ 11.1% (5/45)      │    │
│  │ MPP       ████████████░░░░░░░░░░░░░░░░░░░ 18.2% (2/11)      │    │
│  │ GOG 최종  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  0.0% (0/30)      │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 파일별 상세 진행률

```
┌─────────────────────────────────────────────────────────────────────┐
│ 📁 WSOP_2024_Main_Event_Day2.mp4                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  영상 타임라인:                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ 0:00                    3:30                    7:00           │ │
│  │ |─────────|─────────|─────────|─────────|─────────|─────────|  │ │
│  │ ▲    ▲       ▲     ▲    ▲      ▲  ▲        ▲                  │ │
│  │ H1   H2      H5    H10  H15    H20 H25     H45                 │ │
│  │                                        │                       │ │
│  │                                   90% 기준점 (6:18)            │ │
│  │                                        │    ▼                  │ │
│  │ ████████████████████████████████████████████░░░  92.9%        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  📊 통계:                                                            │
│  ├── 영상 길이: 7:00:00 (25,200초)                                   │
│  ├── 90% 기준: 6:18:00 (22,680초)                                    │
│  ├── 마지막 분석: 6:30:00 (23,400초)                                 │
│  ├── 진행률: 92.9%                                                   │
│  ├── 상태: ✅ 완료                                                   │
│  └── 분석 핸드: 45개                                                 │
│                                                                      │
│  📋 핸드 목록:                                                        │
│  ┌─────┬──────────────┬─────────────────┬────────────┬──────────┐  │
│  │ No. │ 타임코드     │ 플레이어        │ 핸드       │ 등급     │  │
│  ├─────┼──────────────┼─────────────────┼────────────┼──────────┤  │
│  │  1  │ 0:12:30-0:15 │ IVEY vs DWAN    │ AA vs KK   │ ★★★      │  │
│  │  2  │ 0:45:20-0:48 │ NEGREANU vs... │ QQ vs AK   │ ★★       │  │
│  │ ... │ ...          │ ...             │ ...        │ ...      │  │
│  │ 45  │ 6:25:00-6:30 │ FOXEN vs...    │ JJ vs TT   │ ★★★      │  │
│  └─────┴──────────────┴─────────────────┴────────────┴──────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. 동기화 프로세스

### 6.1 데이터 흐름

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Google Sheets │     │     Backend     │     │     SQLite      │
│  (Hand 분석)    │     │    (FastAPI)    │     │   (Archive DB)  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │  1. CSV Export        │                       │
         │─────────────────────>│                       │
         │                       │  2. Parse & Validate │
         │                       │─────────────────────>│
         │                       │                       │
         │                       │  3. Match Video File │
         │                       │<─────────────────────│
         │                       │                       │
         │                       │  4. Insert Hands     │
         │                       │─────────────────────>│
         │                       │                       │
         │                       │  5. Update Progress  │
         │                       │─────────────────────>│
         │                       │                       │

┌─────────────────┐     ┌─────────────────┐
│      NAS        │     │     Backend     │
│  (Video Files)  │     │    (ffprobe)    │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │  A. Scan Files        │
         │<─────────────────────│
         │                       │
         │  B. Get Duration      │
         │<─────────────────────│
         │                       │
         │  C. Store Metadata    │
         │─────────────────────>│ (video_files 테이블)
```

### 6.2 매칭 로직

```python
def match_hand_to_video(hand_record: dict, video_files: list) -> int | None:
    """
    Google Sheets 핸드 레코드를 NAS 영상 파일과 매칭

    매칭 우선순위:
    1. 정확한 파일명 매칭
    2. 프로젝트 + 연도 + 이벤트 매칭
    3. 퍼지 매칭 (유사도 80% 이상)
    """
    event_name = hand_record.get('event_name', '')

    # Step 1: 키워드 추출
    keywords = extract_keywords(event_name)
    # {"project": "WSOP", "event_num": 46, "event_type": "Super High Roller", "day": "Final Table"}

    # Step 2: 후보 필터링
    candidates = []
    for video in video_files:
        score = calculate_match_score(video, keywords)
        if score > 0.8:
            candidates.append((video, score))

    # Step 3: 최고 점수 반환
    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]['id']

    return None
```

---

## 7. 구현 체크리스트

### Phase 1: 백엔드 기반 (High Priority)

- [ ] DB 스키마 생성 (`video_files`, `hand_analysis`, 뷰)
- [ ] NAS 스캔 + ffprobe 영상 길이 추출
- [ ] CSV Import API (`/api/progress/sync`)
- [ ] 진행률 계산 로직

### Phase 2: API 개발

- [ ] GET `/api/progress/summary`
- [ ] GET `/api/progress/by-archive`
- [ ] GET `/api/progress/files`
- [ ] GET `/api/progress/files/{id}`

### Phase 3: 프론트엔드

- [ ] 진행률 대시보드 컴포넌트
- [ ] Archive별 진행률 차트
- [ ] 파일별 상세 뷰 (타임라인)
- [ ] CSV 업로드 UI

### Phase 4: 자동화

- [ ] 주기적 NAS 스캔 (크론)
- [ ] Google Sheets API 연동 (선택)

---

## 8. 관련 문서

| 문서 | 설명 |
|------|------|
| [WORK_PROGRESS_TRACKING_REPORT.md](./WORK_PROGRESS_TRACKING_REPORT.md) | 작업량 산출 보고서 |
| [RATIONALITY_VERIFICATION_REPORT.md](./RATIONALITY_VERIFICATION_REPORT.md) | 90% 기준 합리성 검증 |
| [REAL_DATA_ANALYSIS_RESULT.md](./REAL_DATA_ANALYSIS_RESULT.md) | 실제 데이터 분석 결과 |
| [GOOGLE_SHEETS_INTEGRATION_PROPOSAL.md](./GOOGLE_SHEETS_INTEGRATION_PROPOSAL.md) | Sheets 연동 제안 |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0.0 | 2025-12-09 | 최초 작성, 데이터 검증 완료 |

---

*이 문서는 실제 Google Sheets 데이터 분석 결과를 기반으로 작성되었습니다.*
