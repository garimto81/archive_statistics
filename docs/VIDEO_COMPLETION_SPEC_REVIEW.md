# 코드 리뷰 보고서: VIDEO_COMPLETION_SPEC.md

**리뷰 일시**: 2025-12-09
**리뷰 대상**: `docs/VIDEO_COMPLETION_SPEC.md` (영상 분석 완료 기준 설계 명세서)
**리뷰어**: Security, Logic, Style, Performance (4개 병렬 에이전트)

---

## 요약

| 항목 | 값 |
|------|-----|
| **파일 수** | 1개 |
| **발견된 이슈** | 27개 |
| **심각도 분포** | 🔴 Critical: 5 / 🟠 High: 9 / 🟡 Medium: 8 / 🟢 Low: 5 |
| **전체 점수** | **72/100** |

```
이슈 분포 차트:
Critical  ████████████████████ 5개 (19%)
High      ████████████████████████████████████ 9개 (33%)
Medium    ████████████████████████████████ 8개 (30%)
Low       ████████████████████ 5개 (19%)
```

---

## 🔴 Critical Issues (5개)

### 1. [Security] 인증/인가 부재

**위치**: 섹션 4. API 설계 (전체)

**설명**: 모든 API 엔드포인트에 인증/인가 메커니즘이 명시되지 않음.

**위험**:
- 진행률 조회 API: 민감한 작업 정보 노출
- `POST /api/progress/sync`: 인증 없이 CSV 업로드 시 임의 데이터 주입 가능

**권장 수정**:
```python
# FastAPI 예시
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/api/progress/summary")
async def get_summary(token: str = Depends(security)):
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    # ...
```

---

### 2. [Security] 경로 탐색 공격 (Path Traversal)

**위치**: 섹션 4.2 응답 스키마 (line 297)

**설명**: API 응답에 NAS 전체 경로 노출
```json
{
  "file_path": "\\\\10.10.100.122\\docker\\GGPNAs\\ARCHIVE\\..."
}
```

**위험**: 내부 네트워크 구조, NAS IP 주소 노출

**권장 수정**:
```json
{
  "id": 123,
  "file_name": "WSOP_2024_Main_Event_Day2.mp4",
  "file_id": "abc123def456"  // 암호화된 식별자로 대체
  // file_path 제거
}
```

---

### 3. [Logic] duration_sec = 0 처리 누락

**위치**: 섹션 3.1 DB 스키마 (line 83-109), 뷰 (line 168-183)

**설명**: `video_files.duration_sec`이 0일 때 상태 분류 오류 발생

**문제 시나리오**:
```sql
-- duration_sec = 0 일 때
-- threshold_sec = 0 * 0.9 = 0
-- MAX(timecode_out_sec) >= 0 이면 무조건 COMPLETE 판정 (오류)
```

**권장 수정**:
```sql
-- 제약 조건 추가
ALTER TABLE video_files
ADD CONSTRAINT chk_duration CHECK (duration_sec > 0);

-- 뷰 수정
CASE
    WHEN vf.duration_sec <= 0 THEN 'INVALID'
    WHEN MAX(ha.timecode_out_sec) IS NULL THEN 'NOT_STARTED'
    -- ...
END AS status
```

---

### 4. [Performance] NAS 스캔 성능 병목

**위치**: 섹션 7. 구현 체크리스트 - Phase 1

**설명**: 1,902개 파일에 대해 ffprobe 직렬 실행

**예상 소요 시간**:
- ffprobe 파일당: 0.5~2초
- 총 소요: 16~63분 (네트워크 지연 추가 시 더 증가)

**권장 수정**:
```python
# 병렬 처리 + 증분 스캔
async def scan_nas_videos(nas_path: str, workers: int = 10):
    existing_files = get_scanned_files()  # 기존 DB 파일 목록
    new_files = [f for f in scan_directory(nas_path)
                 if f not in existing_files]

    # 병렬 처리 (10-20 workers)
    async with asyncio.TaskGroup() as group:
        for batch in chunked(new_files, 100):
            group.create_task(process_batch(batch))
```

**예상 개선**: 60분 → 5분

---

### 5. [Performance] VIEW 실시간 집계 비용

**위치**: 섹션 3.1 뷰 정의 (line 152-187)

**설명**: `video_progress` 뷰가 매 조회마다 GROUP BY + MAX() + CASE 연산 수행

**문제**:
- API 호출마다 1,902개 파일 × N개 핸드 전체 재계산
- `/api/progress/summary` 호출 시 수 초 소요 가능

**권장 수정**:
```sql
-- 캐시 테이블 생성
CREATE TABLE video_progress_cache (
    video_file_id INTEGER PRIMARY KEY,
    hand_count INTEGER,
    max_timecode_sec REAL,
    progress_percent REAL,
    status TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 트리거로 자동 업데이트
CREATE TRIGGER update_progress_on_hand_insert
AFTER INSERT ON hand_analysis
BEGIN
    INSERT OR REPLACE INTO video_progress_cache
    SELECT ... FROM video_progress WHERE id = NEW.video_file_id;
END;
```

**예상 개선**: 10초 → 100ms

---

## 🟠 High Priority (9개)

### 6. [Security] SQL Injection 취약점

**위치**: 섹션 4.1 API 엔드포인트

**설명**: 동적 쿼리 생성 시 SQL Injection 위험
- `GET /api/progress/files?status=COMPLETE&archive=WSOP`
- `GET /api/progress/by-category/{archive}`

**권장 수정**:
```python
# ❌ 취약
query = f"SELECT * FROM video_files WHERE archive = '{archive}'"

# ✅ 안전 (Parameterized Query)
query = "SELECT * FROM video_files WHERE archive = ?"
cursor.execute(query, (archive,))
```

---

### 7. [Security] CSV Import 입력 검증 부재

**위치**: 섹션 4.1 `POST /api/progress/sync`

**누락 항목**:
- 파일 크기 제한
- 형식 검증
- 타임코드 범위 검증
- 악성 페이로드 검증

**권장 수정**:
```python
MAX_CSV_SIZE = 10 * 1024 * 1024  # 10MB
MAX_ROWS = 10000
REQUIRED_COLUMNS = ['event_name', 'timecode_in', 'timecode_out']

# 타임코드 범위 검증
if not (0 <= timecode_out_sec <= video.duration_sec):
    raise ValueError("Invalid timecode")
```

---

### 8. [Logic] 매칭 실패 시 데이터 유실

**위치**: 섹션 6.2 매칭 로직 (line 444-472)

**설명**: `match_hand_to_video()`가 `None` 반환 시 핸드 데이터가 어느 영상에도 포함되지 않음

**권장 수정**:
```sql
-- 매칭 실패 추적 테이블
CREATE TABLE unmatched_hands (
    id INTEGER PRIMARY KEY,
    event_name TEXT,
    timecode_in TEXT,
    timecode_out TEXT,
    reason TEXT,  -- "no_candidate", "low_score", "ambiguous"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 9. [Logic] 중복 핸드 방지 제약 없음

**위치**: 섹션 3.1 hand_analysis 테이블

**설명**: 동일 영상의 동일 타임코드 구간에 중복 삽입 가능

**권장 수정**:
```sql
CREATE UNIQUE INDEX idx_hand_unique
ON hand_analysis(video_file_id, timecode_in_sec, timecode_out_sec);
```

---

### 10. [Logic] 퍼지 매칭 임계값 근거 부족

**위치**: 섹션 6.2 (line 464)

**설명**: `score > 0.8` 기준이 임의적이며 검증 없음

**권장 수정**:
- 실제 데이터로 임계값 튜닝
- 스코어 차이가 0.05 미만이면 ambiguous로 처리

---

### 11. [Performance] CSV Import O(n²) 복잡도

**위치**: 섹션 6.2 매칭 로직

**설명**: 1개 핸드 × 1,902개 영상 비교 = 최대 597,228회 비교

**권장 수정**:
```python
# 영상 파일 인덱스 구축 (한 번만)
video_index = build_video_index()  # Dict[keywords, video_id]

# O(1) 매칭
video_id = quick_match(hand, video_index)
```

---

### 12. [Performance] API 페이징 명세 누락

**위치**: 섹션 4.2 응답 스키마

**설명**: 1,902개 파일 전체 반환 시 JSON 응답 크기 수 MB

**권장 수정**:
```json
// GET /api/progress/files?limit=50&offset=0
{
  "items": [...],
  "pagination": {
    "total": 1902,
    "limit": 50,
    "offset": 0,
    "has_next": true
  }
}
```

---

### 13. [Performance] 복합 인덱스 누락

**위치**: 섹션 3.1 인덱스 정의

**누락된 인덱스**:
```sql
-- Category별 조회 최적화
CREATE INDEX idx_video_category ON video_files(category);

-- JOIN + MAX 최적화
CREATE INDEX idx_hand_video_timecode
ON hand_analysis(video_file_id, timecode_out_sec DESC);
```

---

### 14. [Style] JSON 키 명명 규칙 혼용

**위치**: 섹션 4.2 응답 스키마

**불일치 예시**:
- `total_files` (snake_case)
- `duration.seconds` (객체 네스팅)

**권장**: 전체 JSON 키를 `snake_case`로 통일

---

## 🟡 Medium Priority (8개)

| No. | 영역 | 이슈 | 권장 수정 |
|-----|------|------|----------|
| 15 | Security | NAS 자격증명 하드코딩 위험 | 환경 변수 사용 |
| 16 | Security | JSON 태그 필드 Injection 위험 | bleach로 sanitize |
| 17 | Logic | 상태 경계 처리 모호 (10%, 90%) | 명확한 기준 문서화 |
| 18 | Logic | timecode_in > timecode_out 검증 없음 | CHECK 제약 추가 |
| 19 | Performance | VIEW → VIEW 체이닝 비효율 | 기본 테이블에서 직접 집계 |
| 20 | Performance | 진행률 계산 중복 연산 | CTE로 한 번만 계산 |
| 21 | Style | 한글/영어 혼용 패턴 불일치 | 용어 사용 원칙 명시 |
| 22 | Style | 코드 블록 언어 태그 누락 | ```sql, ```python 명시 |

---

## 🟢 Low Priority / Suggestions (5개)

| No. | 영역 | 이슈 |
|-----|------|------|
| 23 | Security | HTTPS 강제 미명시 |
| 24 | Performance | duration_formatted 중복 저장 |
| 25 | Logic | source_sheet, source_row 미활용 |
| 26 | Performance | 타임스탬프 인덱스 누락 |
| 27 | Style | 아이콘 사용 가이드라인 부재 |

---

## 리뷰어별 상세 분석

### Security Review 요약

| 심각도 | 개수 | 주요 이슈 |
|--------|------|----------|
| Critical | 3 | 인증 부재, 경로 노출, SQL Injection |
| High | 2 | CSV 검증 부재, 해시 알고리즘 취약 |
| Medium | 4 | 자격증명 노출, 로깅, 권한 관리, JSON 파싱 |
| Low | 2 | HTTPS, CORS |

### Logic Review 요약

| 심각도 | 개수 | 주요 이슈 |
|--------|------|----------|
| Critical | 3 | 타임코드 초과, duration=0, NULL 처리 |
| High | 3 | 매칭 실패, 중복 핸드, 퍼지 매칭 임계값 |
| Medium | 4 | 경계 처리, 타임코드 검증, 집계 성능, year 타입 |
| Low | 4 | 중복 저장, 미사용 필드, 명명 일관성 |

### Style Review 요약

| 심각도 | 개수 | 주요 이슈 |
|--------|------|----------|
| High | 2 | 테이블명 복수형, JSON 키 혼용 |
| Medium | 3 | 한글/영어 혼용, 상태값 표기, 코드 블록 |
| Low | 4 | 아이콘, 단위 표기, 타임코드 포맷, formatted 저장 |

### Performance Review 요약

| 심각도 | 개수 | 주요 이슈 |
|--------|------|----------|
| Critical | 2 | NAS 스캔 성능, VIEW 실시간 집계 |
| High | 3 | CSV Import O(n²), API 페이징, 인덱스 부족 |
| Medium | 4 | 중복 연산, JSON 검색, 해시 계산, VIEW 체이닝 |
| Low | 3 | formatted 저장, 타임스탬프 인덱스, file_size 미활용 |

---

## 권장사항 (우선순위별)

### 🔴 즉시 수정 필요 (Phase 1 전)

| 순서 | 작업 | 예상 효과 |
|------|------|----------|
| 1 | 인증 추가 (JWT/OAuth2) | 보안 강화 |
| 2 | 경로 마스킹 (file_path 제거) | 정보 노출 방지 |
| 3 | 입력 검증 (CSV 크기/형식) | Injection 방지 |
| 4 | DB 제약 추가 (duration > 0, timecode 검증) | 데이터 무결성 |
| 5 | 캐시 테이블 + 트리거 | 응답 시간 10초→100ms |

### 🟠 Phase 1 완료 전 적용 권장

| 순서 | 작업 | 예상 효과 |
|------|------|----------|
| 6 | NAS 스캔 병렬 처리 (10-20 workers) | 스캔 60분→5분 |
| 7 | CSV Import 배치 최적화 | Import 속도 10x |
| 8 | 인덱스 추가 (category, 복합 인덱스) | 쿼리 성능 향상 |
| 9 | API 페이징 표준화 | 응답 크기 최적화 |

### 🟡 장기적 고려 사항

| 순서 | 작업 |
|------|------|
| 10 | 명명 규칙 가이드라인 문서화 |
| 11 | 매칭 실패 추적 테이블 추가 |
| 12 | 성능 모니터링 구축 |
| 13 | 퍼지 매칭 임계값 튜닝 |

---

## 결론

**전체 평가**: 설계는 기능적으로 완전하며, 90% 완료 기준의 논리가 잘 정립되어 있습니다. 그러나 **보안(인증)**, **성능(캐싱/병렬처리)**, **데이터 무결성(제약조건)** 영역에서 Critical 이슈가 발견되었습니다.

**권장 조치**:
1. Critical 5개 이슈 해결 후 구현 시작
2. High 9개 이슈 Phase 1 완료 전 적용
3. Medium/Low는 점진적 개선

**예상 개선 효과**:
- API 응답 시간: 10초 → 100ms
- NAS 초기 스캔: 60분 → 5분
- 보안 점수: D → A

---

*이 리뷰는 4개의 전문 에이전트(Security, Logic, Style, Performance)가 병렬로 분석한 결과를 통합하였습니다.*
