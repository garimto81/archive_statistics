# 작업량 산출 및 진행률 추적 보고서

**작성일**: 2025-12-09
**버전**: 2.0
**변경사항**: 영상 길이 기반 완료 판정 기준으로 수정

---

## 1. 개요

NAS 아카이브 영상 파일과 Google Sheets 핸드 분석 데이터를 연동하여 **영상 길이 기반** 작업 진행률을 추적합니다.

### 1.1 핵심 개념

```
하나의 영상 = 수백 개의 핸드 포함
작업 완료 = 영상 길이의 90% 구간까지 분석 완료
```

### 1.2 완료 판정 공식

```
영상 길이: D (초)
분석된 마지막 타임코드: T_max (초)

완료 조건: T_max ≥ D × 0.9

예시:
- 영상 길이: 7200초 (2시간)
- 90% 지점: 6480초 (1시간 48분)
- 마지막 분석 타임코드: 6500초 → 완료 ✅
- 마지막 분석 타임코드: 5000초 → 미완료 ❌ (69.4%)
```

---

## 2. 데이터 구조 분석

### 2.1 NAS 파일 (영상)

| 항목 | 값 |
|------|------|
| 총 파일 수 | 1,902개 |
| 주요 형식 | .mp4, .mov, .mkv |
| 평균 길이 | 2-7시간 (추정) |

**폴더별 현황:**

| Archive | 파일 수 | 비율 |
|---------|--------|------|
| WSOP | 1,802 | 94.7% |
| PAD | 45 | 2.4% |
| GOG 최종 | 30 | 1.6% |
| GGMillions | 13 | 0.7% |
| MPP | 11 | 0.6% |
| HCL | 1 | 0.1% |

### 2.2 Google Sheets (핸드 분석)

**1영상 = N개 핸드:**

| 파일명 | 핸드 수 | 타임코드 범위 |
|--------|--------|--------------|
| House Warming Day 2 | 8개 | 0:45:59 ~ 6:58:55 |
| Main Event Final Table | 4개 | 분산 |
| Tournament of Champions Final | 6개 | 분산 |

**핸드 레코드 구조:**
```
File Name: "2024 WSOP Circuit LA - Main Event [Day 2]"
├── Hand 1: In=0:12:30, Out=0:15:45
├── Hand 2: In=0:45:20, Out=0:48:10
├── Hand 3: In=1:23:00, Out=1:26:30
├── ...
└── Hand N: In=6:45:00, Out=6:48:30  ← 마지막 분석 지점
```

---

## 3. 작업 완료 판정 기준

### 3.1 영상별 진행률 계산

```python
def calculate_file_progress(file_duration_sec, analyzed_hands):
    """
    영상별 진행률 계산

    Args:
        file_duration_sec: 영상 전체 길이 (초)
        analyzed_hands: 분석된 핸드 목록 [{in_sec, out_sec}, ...]

    Returns:
        progress_rate: 0.0 ~ 1.0
        is_completed: True if progress >= 0.9
    """
    if not analyzed_hands:
        return 0.0, False

    # 마지막 분석 지점 (가장 늦은 타임코드)
    max_timecode = max(hand['out_sec'] for hand in analyzed_hands)

    # 진행률 = 마지막 분석 지점 / 영상 길이
    progress_rate = max_timecode / file_duration_sec

    # 90% 이상이면 완료
    is_completed = progress_rate >= 0.9

    return progress_rate, is_completed
```

### 3.2 완료 상태 분류

| 상태 | 조건 | 표시 |
|------|------|------|
| **완료** | 진행률 ≥ 90% | ✅ |
| **진행중** | 10% ≤ 진행률 < 90% | 🔶 |
| **시작됨** | 0% < 진행률 < 10% | 🔸 |
| **미시작** | 진행률 = 0% (핸드 없음) | ❌ |

### 3.3 예시

```
파일: WSOP_2024_Main_Event_Day2.mp4
├── 영상 길이: 25,200초 (7시간)
├── 90% 지점: 22,680초 (6시간 18분)
│
├── 분석된 핸드: 45개
│   ├── Hand 1:  In=720s,   Out=900s
│   ├── Hand 2:  In=1800s,  Out=2100s
│   ├── ...
│   └── Hand 45: In=23000s, Out=23400s  ← 최대값
│
├── 마지막 분석 지점: 23,400초
├── 진행률: 23400/25200 = 92.9%
└── 상태: 완료 ✅ (≥90%)
```

---

## 4. 계층별 진행률 집계

### 4.1 집계 구조

```
전체 진행률
│
├── Archive별 (L1)
│   ├── WSOP: 완료 파일 / 전체 파일
│   ├── HCL: 완료 파일 / 전체 파일
│   └── ...
│
├── Category별 (L2)
│   ├── WSOP Bracelet Event
│   │   └── 완료 파일 / 전체 파일
│   └── WSOP Circuit Event
│       └── 완료 파일 / 전체 파일
│
└── 폴더별 (L3, L4)
    └── 개별 폴더 진행률
```

### 4.2 집계 공식

```python
# 폴더별 진행률
folder_progress = completed_files / total_files

# Archive별 진행률 (하위 폴더 합산)
archive_progress = sum(folder_completed) / sum(folder_total)

# 전체 진행률
total_progress = sum(archive_completed) / sum(archive_total)
```

---

## 5. 데이터베이스 스키마

### 5.1 파일 진행률 테이블

```sql
CREATE TABLE file_progress (
    id INTEGER PRIMARY KEY,

    -- NAS 파일 정보
    nas_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_duration_sec REAL,           -- ffprobe로 측정된 영상 길이

    -- 계층 정보
    archive TEXT NOT NULL,            -- L1: WSOP, HCL, MPP
    category TEXT,                    -- L2: WSOP Bracelet Event
    subcategory TEXT,                 -- L3: WSOP-LAS VEGAS
    year INTEGER,                     -- L4: 2024

    -- 진행률
    analyzed_hand_count INTEGER DEFAULT 0,  -- 분석된 핸드 수
    max_timecode_sec REAL DEFAULT 0,        -- 마지막 분석 타임코드
    progress_rate REAL DEFAULT 0,           -- 0.0 ~ 1.0

    -- 완료 상태
    completion_status TEXT DEFAULT 'not_started',
    -- 'completed', 'in_progress', 'started', 'not_started'

    -- 메타
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_file_progress_archive ON file_progress(archive);
CREATE INDEX idx_file_progress_status ON file_progress(completion_status);
```

### 5.2 핸드 분석 테이블

```sql
CREATE TABLE hand_analysis (
    id INTEGER PRIMARY KEY,

    -- 파일 연결
    file_progress_id INTEGER REFERENCES file_progress(id),

    -- 타임코드
    timecode_in_sec REAL NOT NULL,    -- 핸드 시작 (초)
    timecode_out_sec REAL NOT NULL,   -- 핸드 종료 (초)

    -- 핸드 정보 (Google Sheets에서)
    hand_grade TEXT,                  -- ★, ★★, ★★★
    winner TEXT,
    players TEXT,                     -- JSON array
    poker_play_tags TEXT,             -- JSON array
    emotion_tags TEXT,                -- JSON array

    -- 원본 시트 참조
    sheets_source TEXT,
    sheets_row_id TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hand_file ON hand_analysis(file_progress_id);
CREATE INDEX idx_hand_timecode ON hand_analysis(timecode_out_sec);
```

---

## 6. 매칭 로직

### 6.1 NAS 파일 ↔ Google Sheets 매칭

```python
def match_file_to_sheets(nas_file_name, sheets_records):
    """
    NAS 파일명과 Google Sheets 레코드 매칭

    매칭 전략:
    1. 정확한 파일명 매칭
    2. 프로젝트 + 연도 + 이벤트명 매칭
    3. 퍼지 매칭 (유사도 80% 이상)
    """

    # 1. 정확한 매칭
    for record in sheets_records:
        if record['file_name'] == nas_file_name:
            return record

    # 2. 메타데이터 매칭
    nas_meta = parse_file_name(nas_file_name)
    # {"project": "WSOP", "year": 2024, "event": "Main Event", "day": "Day 2"}

    for record in sheets_records:
        sheet_meta = parse_sheet_record(record)
        if (nas_meta['project'] == sheet_meta['project'] and
            nas_meta['year'] == sheet_meta['year'] and
            nas_meta['event'] == sheet_meta['event']):
            return record

    return None
```

### 6.2 타임코드 파싱

```python
def parse_timecode(timecode_str):
    """
    타임코드 문자열 → 초 변환

    지원 형식:
    - "1:23:45" → 5025초
    - "0:45:30" → 2730초
    - "6:58:55" → 25135초
    """
    parts = timecode_str.split(':')
    if len(parts) == 3:
        h, m, s = map(int, parts)
        return h * 3600 + m * 60 + s
    return 0
```

---

## 7. API 엔드포인트

```python
# backend/app/api/progress.py

@router.get("/summary")
async def get_progress_summary():
    """전체 진행률 요약"""
    return {
        "total_files": 1902,
        "total_duration_hours": 8500,  # 추정
        "completed_files": 150,
        "in_progress_files": 200,
        "not_started_files": 1552,
        "overall_progress": 0.079  # 7.9%
    }

@router.get("/by-archive")
async def get_progress_by_archive():
    """Archive별 진행률"""
    return [
        {
            "archive": "WSOP",
            "total_files": 1802,
            "completed_files": 140,
            "in_progress_files": 180,
            "progress_rate": 0.078
        },
        ...
    ]

@router.get("/file/{file_id}")
async def get_file_progress(file_id: int):
    """개별 파일 진행률 상세"""
    return {
        "file_name": "WSOP_2024_Main_Event_Day2.mp4",
        "duration_sec": 25200,
        "duration_formatted": "7:00:00",
        "completion_threshold_sec": 22680,  # 90%
        "max_analyzed_sec": 23400,
        "progress_rate": 0.929,
        "status": "completed",
        "hand_count": 45,
        "hands": [
            {"in": "0:12:30", "out": "0:15:45", "grade": "★★"},
            ...
        ]
    }

@router.post("/sync")
async def sync_from_sheets(file: UploadFile):
    """Google Sheets CSV 업로드 → 진행률 업데이트"""
    pass
```

---

## 8. Dashboard UI

```
┌─────────────────────────────────────────────────────────────────┐
│                    작업 진행률 대시보드                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  1,902   │  │   150    │  │   200    │  │  7.9%    │        │
│  │ 총 영상  │  │  완료    │  │  진행중  │  │ 진행률   │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 파일별 진행률 (영상 길이 대비)                           │    │
│  │                                                          │    │
│  │ WSOP_2024_Main_Day2.mp4                                 │    │
│  │ ████████████████████████████████████░░░░  92.9% ✅      │    │
│  │ |-------- 7시간 --------|← 90% →|                       │    │
│  │                         6:18    마지막분석: 6:30         │    │
│  │                                                          │    │
│  │ WSOP_2024_Main_Day1.mp4                                 │    │
│  │ ████████████████████░░░░░░░░░░░░░░░░░░░░  45.2% 🔶      │    │
│  │ |-------- 6시간 --------|← 90% →|                       │    │
│  │                         5:24    마지막분석: 2:43         │    │
│  │                                                          │    │
│  │ WSOP_2024_Circuit_Day3.mp4                              │    │
│  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   0.0% ❌      │    │
│  │ (미분석)                                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. 구현 우선순위

| 순서 | 기능 | 설명 |
|------|------|------|
| 1 | DB 스키마 생성 | file_progress, hand_analysis 테이블 |
| 2 | NAS 스캔 + ffprobe | 영상 길이 측정하여 file_progress 생성 |
| 3 | CSV Import | Google Sheets → hand_analysis 테이블 |
| 4 | 진행률 계산 | max_timecode / duration 계산 |
| 5 | API 엔드포인트 | summary, by-archive, file detail |
| 6 | Dashboard UI | 진행률 바, 파일 목록 |

---

## 10. 결론

### 10.1 핵심 정의

| 항목 | 정의 |
|------|------|
| **총 작업량** | NAS 영상 파일의 총 재생 시간 |
| **파일 완료 기준** | 영상 길이의 90% 지점까지 핸드 분석 완료 |
| **진행률** | 마지막 분석 타임코드 / 영상 전체 길이 |

### 10.2 장점

- **객관적 기준**: 영상 길이라는 명확한 기준
- **자동 계산**: 타임코드만 있으면 자동으로 진행률 산출
- **세밀한 추적**: 파일별, 폴더별, Archive별 진행률 확인

---

## 부록

### A. Google Sheets URL

- Sheet 1: `https://docs.google.com/spreadsheets/d/1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk`
- Sheet 2: `https://docs.google.com/spreadsheets/d/1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4`

### B. 타임코드 필드

- Sheet 1: `time_start_ms`, `time_end_ms`, `time_start_S`, `time_end_S` (대부분 비어있음)
- Sheet 2: `In`, `Out` (HH:MM:SS 형식, 데이터 존재)

### C. NAS 경로

- 기본 경로: `\\10.10.100.122\docker\GGPNAs\ARCHIVE`
- Docker 마운트: `/mnt/nas`
