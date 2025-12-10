# Sync Domain Agent Rules

## Identity
- **Role**: Google Sheets 동기화 전문가
- **Level**: 1 (Domain)
- **Scope**: `backend/app/` 내 동기화 관련 모듈 (구현 예정)

## Managed Blocks

| Block ID | 파일 | 책임 |
|----------|------|------|
| `sync.sheets` | `services/sheets.py` (예정) | Google Sheets API 연동 |
| `sync.matching` | `services/matching.py` (예정) | NAS 파일 매칭 |
| `sync.import` | `services/import.py` (예정) | DB Import |

## Capabilities

### fetch_sheet_data
- **Description**: Google Sheets 데이터 가져오기
- **Input**: `SheetConfig { sheet_id: str, range: str }`
- **Output**: `RawSheetData { rows: List[Dict] }`

### match_files
- **Description**: 시트 데이터와 NAS 파일 매칭
- **Input**: `MatchRequest { sheet_data: RawSheetData }`
- **Output**: `MatchResult { matched: int, unmatched: List[str] }`

### import_hands
- **Description**: 핸드 분석 결과 가져오기
- **Input**: `ImportRequest { matched_records: MatchedRecords }`
- **Output**: `ImportResult { imported: int, skipped: int }`

## Data Flow

```
Google Sheets
    │
    ▼
┌─────────────────┐
│   sync.sheets   │
│   CSV 파싱       │
│   정규화         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  sync.matching  │
│  파일명 매칭     │
│  Fuzzy 매칭      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   sync.import   │
│  DB 저장        │
│  중복 처리       │
└─────────────────┘
```

## Constraints

### DO
- Timecode 파싱은 표준 형식 지원 (HH:MM:SS, MM:SS)
- 파일 매칭 시 대소문자 무시
- 중복 레코드는 최신 데이터로 업데이트
- 매칭 실패 건은 로그로 기록

### DON'T
- Google API 키 하드코딩 금지
- 원본 시트 데이터 수정 금지
- scanner-domain 직접 호출 금지

## Matching Strategy

```python
# 매칭 우선순위
def match_file(sheet_row: dict, nas_files: List[str]) -> Optional[str]:
    """
    1. 정확한 파일명 매칭
    2. 경로 포함 매칭
    3. Fuzzy 매칭 (유사도 80% 이상)
    """
    filename = sheet_row.get("filename", "")

    # 1. Exact match
    exact = [f for f in nas_files if f.endswith(filename)]
    if exact:
        return exact[0]

    # 2. Path contains
    path_hint = sheet_row.get("path", "")
    if path_hint:
        partial = [f for f in nas_files if path_hint in f]
        if partial:
            return partial[0]

    # 3. Fuzzy match
    from rapidfuzz import fuzz
    best_match = max(nas_files, key=lambda f: fuzz.ratio(filename, os.path.basename(f)))
    if fuzz.ratio(filename, os.path.basename(best_match)) >= 80:
        return best_match

    return None
```

## Sheet Data Schema

```python
# Expected sheet columns
@dataclass
class SheetRow:
    video_id: str              # 비디오 ID
    filename: str              # 파일명
    event_name: str            # 이벤트명
    timecode_in: str           # 시작 시간 (HH:MM:SS)
    timecode_out: str          # 종료 시간 (HH:MM:SS)
    hand_number: Optional[int] # 핸드 번호
    player_name: Optional[str] # 플레이어명
    notes: Optional[str]       # 메모
```

## Error Codes

| Code | Description | Recovery |
|------|-------------|----------|
| `SHEETS_AUTH_FAILED` | Sheets API 인증 실패 | 자격 증명 확인 |
| `SHEETS_NOT_FOUND` | 시트 없음 | 시트 ID 확인 |
| `MATCH_FAILED` | 파일 매칭 실패 | 수동 매칭 필요 |
| `IMPORT_DUPLICATE` | 중복 레코드 | 업데이트 또는 스킵 |
| `TIMECODE_PARSE_ERROR` | 타임코드 파싱 실패 | 형식 확인 |

## Testing
- Unit: `tests/test_sync.py`
- Integration: `tests/test_sheets_api.py`
- Mock: Google Sheets API, NAS 파일 목록
