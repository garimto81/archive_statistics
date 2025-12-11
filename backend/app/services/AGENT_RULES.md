# Services Block Agent Rules

## Identity
- **Role**: 비즈니스 로직 처리 전문가
- **Domain**: Scanner, Progress, Sync
- **Scope**: `backend/app/services/` 내부만

## Files in Scope

| File | Block Prefix | 책임 |
|------|--------------|------|
| `progress_service.py` | `progress.*` | 폴더-카테고리 매칭, 진행률 계산 (핵심) |
| `scanner.py` | `scanner.*` | NAS 스캔 및 메타데이터 추출 |
| `sheets_sync.py` | `sync.*` | Google Sheets 동기화 |
| `utils.py` | - | 공통 유틸리티 (format_size, format_duration) |

---

## 핵심 파일: progress_service.py (921 lines)

### Block Index

| Block ID | Lines | Description | When to Read |
|----------|-------|-------------|--------------|
| `progress.utils` | 25-55 | 문자열 정규화, 유사도 계산 | 매칭 로직 디버깅 |
| `progress.data_loader` | 105-160 | DB 데이터 로드 | 데이터 소스 문제 |
| `progress.matcher` | 162-285 | 폴더-카테고리 매칭 | 매칭 오류 수정 |
| `progress.file_matcher` | 287-323 | 파일-핸드 매칭 | 파일 레벨 진행률 |
| `progress.aggregator` | 325-642 | 하이어라키 합산, 코덱 집계 | 진행률 계산 오류 |
| `progress.file_query` | 644-708 | 파일 목록 조회 | 파일 리스트 API |
| `progress.folder_detail` | 710-854 | 폴더 상세 조회 | 상세 패널 API |
| `progress.file_detail` | 856-918 | 파일 상세 조회 | 개별 파일 API |

### 매칭 전략 우선순위

```
1. exact (1.0)         - "GOG" == "GOG"
2. prefix (0.9)        - 카테고리가 폴더명으로 시작
3. folder_prefix (0.85) - 폴더명이 카테고리로 시작
4. word (0.8)          - 단어 포함
5. year (0.7)          - 연도 매칭
```

### 진행률 계산 규칙

- 90% 이상 = 100% (완료 처리)
- 하이어라키 합산: `부모 = sum(자식.total_done) / sum(자식.total_files)`

### 공통 함수 Import 규칙

```python
# ✅ 올바른 사용
from app.services.utils import format_size, format_duration

# ❌ 금지: 중복 정의
def format_size(size):  # 절대 금지!
    ...
```

---

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
