# Scanner Domain Agent Rules

## Identity
- **Role**: NAS 스캔 및 메타데이터 추출 전문가
- **Level**: 1 (Domain)
- **Scope**: `backend/app/` 내 스캔 관련 모듈

## Managed Blocks

| Block ID | 파일 | 책임 |
|----------|------|------|
| `scanner.discovery` | `api/scan.py`, `api/folders.py` | NAS 디렉토리 탐색 |
| `scanner.metadata` | `services/scanner.py`, `services/utils.py` | 미디어 메타데이터 추출 |
| `scanner.storage` | `models/file_stats.py` | DB 저장 및 캐시 |

## Capabilities

### scan_directory
- **Description**: NAS 디렉토리 스캔
- **Input**: `ScanRequest { path: str, subpath?: str }`
- **Output**: `ScanResult { files_scanned: int, duration: float }`

### get_file_stats
- **Description**: 파일 통계 조회
- **Input**: `FileQuery { folder_path?: str, extension?: str }`
- **Output**: `FileStats[]`

### get_folder_stats
- **Description**: 폴더 통계 조회
- **Input**: `FolderQuery { path: str, depth?: int }`
- **Output**: `FolderStats`

## Constraints

### DO
- ffprobe 호출 시 timeout 10초 설정 필수
- 대용량 스캔 시 500건마다 commit
- asyncio.sleep(0)으로 이벤트 루프 양보
- 스캔 취소 요청 시 즉시 중단

### DON'T
- 동기 blocking 호출 금지
- NAS 경로 하드코딩 금지 (settings 사용)
- progress-domain, sync-domain 직접 호출 금지

## Dependencies

### Internal
- `app.core.config`: NAS 설정
- `app.core.database`: DB 세션

### External
- `ffprobe`: 미디어 메타데이터
- `sqlalchemy`: DB 접근
- `asyncio`: 비동기 처리

## Error Codes

| Code | Description | Recovery |
|------|-------------|----------|
| `SCAN_PERMISSION_DENIED` | NAS 접근 권한 없음 | 관리자 확인 요청 |
| `SCAN_PATH_NOT_FOUND` | 경로 없음 | 경로 확인 |
| `METADATA_TIMEOUT` | ffprobe 시간 초과 | 스킵 후 계속 |
| `STORAGE_COMMIT_FAILED` | DB 저장 실패 | 재시도 |

## Performance Guidelines

```
NAS 스캔 최적화:
┌─────────────────────────────────────┐
│  1. 증분 스캔 우선                   │
│     - 기존 파일은 duration > 0 스킵  │
│                                      │
│  2. 배치 커밋                        │
│     - 500건마다 commit               │
│                                      │
│  3. 병렬 메타데이터 추출             │
│     - run_in_executor 사용           │
│                                      │
│  4. 로그 제한                        │
│     - 최근 100건만 유지              │
└─────────────────────────────────────┘
```

## Testing
- Unit: `tests/test_scanner.py`
- Integration: `tests/test_scan_api.py`
- Mock: NAS 접근, ffprobe 호출
