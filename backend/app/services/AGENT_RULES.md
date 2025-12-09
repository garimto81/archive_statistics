# Services Block Agent Rules

## Identity
- **Role**: 비즈니스 로직 처리 전문가
- **Domain**: Scanner (primary)
- **Scope**: `backend/app/services/` 내부만

## Files in Scope

| File | Block | 책임 |
|------|-------|------|
| `scanner.py` | scanner.metadata | NAS 스캔 및 메타데이터 추출 |
| `utils.py` | scanner.metadata | MIME 타입 분석, 유틸리티 |

## Core Class: ArchiveScanner

```python
class ArchiveScanner:
    """
    책임:
    1. NAS 디렉토리 재귀 탐색
    2. ffprobe로 미디어 메타데이터 추출
    3. DB 저장 (배치 커밋)
    """

    def __init__(self, db: AsyncSession, state: Dict):
        self.db = db
        self.state = state  # 공유 상태 (진행률, 로그)

    async def scan(self, subpath: Optional[str] = None):
        """메인 스캔 진입점"""

    async def _scan_directory(self, path: str, depth: int):
        """재귀 디렉토리 탐색"""

    def _get_media_duration(self, file_path: str) -> float:
        """ffprobe로 duration 추출"""

    async def _process_file(self, entry: DirEntry, folder_path: str):
        """개별 파일 처리"""

    async def _save_folder_stats(self, path: str, stats: Dict):
        """폴더 통계 저장"""
```

## Constraints

### DO
- ffprobe 호출 시 timeout 10초 설정
- 500건마다 batch commit
- asyncio.sleep(0)으로 이벤트 루프 양보
- state["is_scanning"] 확인하여 취소 지원
- 에러 시에도 스캔 계속 (개별 파일 스킵)

### DON'T
- `api/` 폴더 직접 수정 금지
- 동기 blocking 호출 금지
- 설정값 하드코딩 금지 (settings 사용)
- 직접 print 대신 _add_log 사용

## ffprobe Optimization

```python
# 최적화된 ffprobe 호출
result = subprocess.run(
    [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',         # 첫 번째 비디오 스트림만
        '-show_entries', 'format=duration',
        '-of', 'json',
        '-probesize', '5000000',          # 5MB로 제한
        '-analyzeduration', '5000000',    # 분석 시간 제한
        file_path
    ],
    capture_output=True,
    text=True,
    timeout=10                            # 10초 타임아웃
)
```

## State Management

```python
# 공유 상태 구조
state = {
    "is_scanning": True,           # 스캔 진행 중 여부
    "current_folder": "",          # 현재 스캔 중인 폴더
    "files_scanned": 0,            # 스캔된 파일 수
    "media_files_processed": 0,    # 처리된 미디어 파일 수
    "total_duration_found": 0.0,   # 총 duration (초)
    "progress": 0.0,               # 진행률 (%)
    "logs": []                     # 최근 로그 (100개 유지)
}
```

## Dependencies

### Internal
- `app.core.config`: NAS 설정
- `app.models.file_stats`: FileStats, FolderStats 모델

### External
- `ffprobe`: 미디어 메타데이터 (시스템 설치 필요)
- `sqlalchemy`: 비동기 DB 접근
- `asyncio`: 비동기 처리

## Error Handling

| Error | Handling |
|-------|----------|
| `PermissionError` | 로그 후 스킵 |
| `TimeoutExpired` | 로그 후 duration=0 |
| `JSONDecodeError` | duration=0 반환 |
| `Exception` | 로그 후 계속 |

## Testing
- Unit: `tests/test_scanner.py`
- Mock: `os.scandir`, `subprocess.run`
- Fixture: 임시 디렉토리 구조
