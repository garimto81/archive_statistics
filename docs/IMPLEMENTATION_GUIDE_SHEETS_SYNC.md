# Google Sheets 동기화 구현 가이드

**작성일**: 2025-12-09
**버전**: 1.0
**관련 문서**: [GOOGLE_SHEETS_INTEGRATION_PROPOSAL.md](./GOOGLE_SHEETS_INTEGRATION_PROPOSAL.md)

---

## 1. 현재 상태 분석

### 1.1 기존 구현 (유지)

| 파일 | 설명 | 변경 필요 |
|------|------|----------|
| `backend/app/api/worker_stats.py` | 작업자별 통계 API | ❌ 유지 |
| `backend/app/schemas/worker_stats.py` | Pydantic 스키마 | ❌ 유지 |
| `backend/app/models/work_status.py` | WorkStatus 모델 | ⚠️ 필드 추가 가능 |
| `frontend/src/pages/WorkStatus.tsx` | Workers 탭 UI | ⚠️ 동기화 상태 추가 |
| `frontend/src/services/api.ts` | API 클라이언트 | ⚠️ sync API 추가 |

### 1.2 신규 구현 필요

| 파일 | 설명 |
|------|------|
| `backend/app/services/sheets_sync.py` | Google Sheets 동기화 서비스 |
| `backend/app/api/sync.py` | 동기화 상태/트리거 API |
| `backend/credentials/service_account.json` | Service Account 키 파일 |

---

## 2. 아키텍처 결정

### 2.1 데이터 소스 전략

```
[기존] CSV Import → DB → worker_stats API → Frontend
                    ↓
[변경] Google Sheets → sheets_sync → DB → worker_stats API → Frontend
```

**핵심 포인트**: `worker_stats.py` API는 그대로 유지하고, 데이터 입력 부분만 Google Sheets에서 자동으로 가져오도록 변경

### 2.2 동기화 방식

- **주기**: 30분 (설정 가능)
- **방식**: 전체 교체 (Full Replace) - 시트 데이터가 Source of Truth
- **트리거**: 서버 시작 시 + 주기적 + 수동

---

## 3. 단계별 구현

### Phase 1: 의존성 추가

```bash
cd backend
pip install gspread google-auth apscheduler
```

`requirements.txt` 추가:
```
gspread>=6.0.0
google-auth>=2.0.0
apscheduler>=3.10.0
```

### Phase 2: 설정 파일 업데이트

**`backend/app/core/config.py`** 수정:

```python
class Settings(BaseSettings):
    # ... 기존 설정 ...

    # Google Sheets 설정
    google_service_account_file: str = "credentials/service_account.json"
    google_sheets_url: str = ""  # 사용자가 제공할 URL
    sheets_sync_interval_minutes: int = 30
    sheets_sync_enabled: bool = False  # URL 제공 전까지 비활성화
```

**`backend/.env`** 추가:
```env
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/service_account.json
GOOGLE_SHEETS_URL=
SHEETS_SYNC_INTERVAL_MINUTES=30
SHEETS_SYNC_ENABLED=false
```

### Phase 3: SheetsSync 서비스 구현

**`backend/app/services/sheets_sync.py`**:

```python
"""
Google Sheets 자동 동기화 서비스

Source of Truth: Google Sheets
Target: work_status 테이블
"""
import logging
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass

import gspread
from google.oauth2.service_account import Credentials
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.core.config import settings
from app.core.database import async_session_maker
from app.models.work_status import WorkStatus, Archive

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    success: bool
    synced_at: datetime
    total_records: int
    synced_count: int
    error: Optional[str] = None


class SheetsSyncService:
    """Google Sheets 자동 동기화 서비스"""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._client: Optional[gspread.Client] = None
        self.last_sync_time: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.status: str = "idle"

    @property
    def next_sync_time(self) -> Optional[datetime]:
        """다음 동기화 예정 시간"""
        job = self.scheduler.get_job('sheets_sync')
        return job.next_run_time if job else None

    async def start(self):
        """동기화 서비스 시작"""
        if not settings.sheets_sync_enabled:
            logger.info("Sheets sync disabled - skipping startup")
            return

        if not settings.google_sheets_url:
            logger.warning("Sheets URL not configured - skipping sync")
            return

        self.scheduler.add_job(
            self._sync_wrapper,
            'interval',
            minutes=settings.sheets_sync_interval_minutes,
            id='sheets_sync',
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info(f"Sheets sync scheduler started (interval: {settings.sheets_sync_interval_minutes}m)")

        # 시작 시 즉시 1회 동기화
        await self._sync_wrapper()

    async def stop(self):
        """동기화 서비스 중지"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Sheets sync scheduler stopped")

    def _get_client(self) -> gspread.Client:
        """Google Sheets 클라이언트 획득 (lazy initialization)"""
        if self._client is None:
            creds = Credentials.from_service_account_file(
                settings.google_service_account_file,
                scopes=self.SCOPES,
            )
            self._client = gspread.authorize(creds)
        return self._client

    async def _sync_wrapper(self):
        """비동기 래퍼 (스케줄러 호환)"""
        try:
            await self.sync()
        except Exception as e:
            logger.exception(f"Sync failed: {e}")
            self.last_error = str(e)
            self.status = "error"

    async def sync(self) -> SyncResult:
        """Google Sheets에서 데이터 동기화"""
        self.status = "syncing"
        logger.info("Starting sheets sync...")

        try:
            # 1. Sheets 데이터 fetch
            client = self._get_client()
            sheet = client.open_by_url(settings.google_sheets_url)
            worksheet = sheet.get_worksheet(0)
            records = worksheet.get_all_records()

            logger.info(f"Fetched {len(records)} records from sheets")

            # 2. DB 동기화
            async with async_session_maker() as db:
                synced_count = await self._sync_to_db(db, records)
                await db.commit()

            # 3. 결과 기록
            result = SyncResult(
                success=True,
                synced_at=datetime.now(),
                total_records=len(records),
                synced_count=synced_count,
            )

            self.last_sync_time = result.synced_at
            self.last_error = None
            self.status = "idle"

            logger.info(f"Sync completed: {synced_count}/{len(records)} records")
            return result

        except Exception as e:
            logger.exception(f"Sync error: {e}")
            self.last_error = str(e)
            self.status = "error"
            return SyncResult(
                success=False,
                synced_at=datetime.now(),
                total_records=0,
                synced_count=0,
                error=str(e),
            )

    async def _sync_to_db(
        self,
        db: AsyncSession,
        records: List[dict],
    ) -> int:
        """DB에 데이터 동기화 (Full Replace 방식)"""
        # 기존 데이터 삭제 (sheets 동기화 데이터만)
        # source='sheets'인 레코드만 삭제하거나 전체 교체
        # 여기서는 전체 교체 방식 사용

        # 아카이브 캐시 (이름 → ID 매핑)
        archive_cache = {}

        synced_count = 0
        for record in records:
            try:
                # Archive 처리
                archive_name = record.get('Archive', '')
                if archive_name and archive_name not in archive_cache:
                    archive = await self._get_or_create_archive(db, archive_name)
                    archive_cache[archive_name] = archive.id

                # WorkStatus 생성 또는 업데이트
                work_status = WorkStatus(
                    archive_id=archive_cache.get(archive_name),
                    category=record.get('Category', ''),
                    pic=record.get('PIC', ''),
                    status=self._normalize_status(record.get('Status', '대기')),
                    total_videos=int(record.get('Total Videos', 0) or 0),
                    excel_done=int(record.get('Done Videos', 0) or 0),
                    notes1=record.get('Notes', ''),
                    notes2=record.get('Notes2', ''),
                )

                # Upsert 로직 (category + archive_id로 unique 판단)
                await self._upsert_work_status(db, work_status)
                synced_count += 1

            except Exception as e:
                logger.warning(f"Failed to sync record: {record}, error: {e}")

        return synced_count

    async def _get_or_create_archive(
        self,
        db: AsyncSession,
        name: str,
    ) -> Archive:
        """Archive 조회 또는 생성"""
        from sqlalchemy import select

        result = await db.execute(
            select(Archive).where(Archive.name == name)
        )
        archive = result.scalar_one_or_none()

        if not archive:
            archive = Archive(name=name)
            db.add(archive)
            await db.flush()

        return archive

    async def _upsert_work_status(
        self,
        db: AsyncSession,
        work_status: WorkStatus,
    ):
        """WorkStatus upsert (archive_id + category로 매칭)"""
        from sqlalchemy import select

        result = await db.execute(
            select(WorkStatus).where(
                WorkStatus.archive_id == work_status.archive_id,
                WorkStatus.category == work_status.category,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # 업데이트
            existing.pic = work_status.pic
            existing.status = work_status.status
            existing.total_videos = work_status.total_videos
            existing.excel_done = work_status.excel_done
            existing.notes1 = work_status.notes1
            existing.notes2 = work_status.notes2
        else:
            # 신규 추가
            db.add(work_status)

    def _normalize_status(self, status: str) -> str:
        """상태 값 정규화"""
        status_map = {
            '대기': '대기',
            'waiting': '대기',
            'pending': '대기',
            '작업 중': '작업 중',
            'in progress': '작업 중',
            'working': '작업 중',
            '검토': '검토',
            'review': '검토',
            '완료': '완료',
            'done': '완료',
            'complete': '완료',
            'completed': '완료',
        }
        return status_map.get(status.lower().strip(), status)


# 싱글톤 인스턴스
sheets_sync_service = SheetsSyncService()
```

### Phase 4: Sync API 엔드포인트

**`backend/app/api/sync.py`**:

```python
"""
Sync API - Google Sheets 동기화 상태 및 트리거
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.services.sheets_sync import sheets_sync_service
from app.core.config import settings

router = APIRouter()


class SyncStatusResponse(BaseModel):
    enabled: bool
    status: str
    last_sync: Optional[datetime]
    next_sync: Optional[datetime]
    error: Optional[str]
    interval_minutes: int


class SyncTriggerResponse(BaseModel):
    success: bool
    synced_at: datetime
    total_records: int
    synced_count: int
    error: Optional[str]


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status():
    """동기화 상태 조회"""
    return SyncStatusResponse(
        enabled=settings.sheets_sync_enabled,
        status=sheets_sync_service.status,
        last_sync=sheets_sync_service.last_sync_time,
        next_sync=sheets_sync_service.next_sync_time,
        error=sheets_sync_service.last_error,
        interval_minutes=settings.sheets_sync_interval_minutes,
    )


@router.post("/trigger", response_model=SyncTriggerResponse)
async def trigger_sync():
    """수동으로 동기화 트리거"""
    if not settings.sheets_sync_enabled:
        raise HTTPException(
            status_code=400,
            detail="Sheets sync is not enabled. Set SHEETS_SYNC_ENABLED=true and provide GOOGLE_SHEETS_URL",
        )

    result = await sheets_sync_service.sync()

    return SyncTriggerResponse(
        success=result.success,
        synced_at=result.synced_at,
        total_records=result.total_records,
        synced_count=result.synced_count,
        error=result.error,
    )
```

### Phase 5: 라우터 등록

**`backend/app/main.py`** 수정:

```python
from app.api import sync
from app.services.sheets_sync import sheets_sync_service

# ... 기존 코드 ...

# 라우터 등록
app.include_router(sync.router, prefix="/api/sync", tags=["sync"])

# lifespan에 sheets sync 추가
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await sheets_sync_service.start()
    yield
    # Shutdown
    await sheets_sync_service.stop()
```

### Phase 6: Frontend 업데이트

**`frontend/src/services/api.ts`** 추가:

```typescript
// Sync API
export interface SyncStatus {
  enabled: boolean;
  status: string;
  last_sync: string | null;
  next_sync: string | null;
  error: string | null;
  interval_minutes: number;
}

export interface SyncTriggerResponse {
  success: boolean;
  synced_at: string;
  total_records: number;
  synced_count: number;
  error: string | null;
}

export const syncApi = {
  getStatus: async (): Promise<SyncStatus> => {
    const { data } = await api.get('/sync/status');
    return data;
  },

  trigger: async (): Promise<SyncTriggerResponse> => {
    const { data } = await api.post('/sync/trigger');
    return data;
  },
};
```

**WorkStatus.tsx** - 동기화 상태 표시 컴포넌트 추가:

```tsx
// 동기화 상태 표시 (헤더에 추가)
const SyncStatusIndicator = () => {
  const { data: syncStatus, refetch } = useQuery({
    queryKey: ['syncStatus'],
    queryFn: syncApi.getStatus,
    refetchInterval: 60000, // 1분마다 갱신
  });

  const triggerMutation = useMutation({
    mutationFn: syncApi.trigger,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workerStats'] });
      refetch();
    },
  });

  if (!syncStatus?.enabled) return null;

  const lastSyncText = syncStatus.last_sync
    ? `Last sync: ${formatDistanceToNow(new Date(syncStatus.last_sync))} ago`
    : 'Never synced';

  return (
    <div className="flex items-center gap-2 text-sm text-gray-500">
      <span>{lastSyncText}</span>
      <button
        onClick={() => triggerMutation.mutate()}
        disabled={triggerMutation.isPending || syncStatus.status === 'syncing'}
        className="p-1 hover:bg-gray-100 rounded"
        title="Sync now"
      >
        <RefreshCw
          className={`w-4 h-4 ${syncStatus.status === 'syncing' ? 'animate-spin' : ''}`}
        />
      </button>
      {syncStatus.error && (
        <span className="text-red-500" title={syncStatus.error}>⚠️</span>
      )}
    </div>
  );
};
```

---

## 4. 테스트

### 4.1 단위 테스트

```python
# backend/tests/test_sheets_sync.py

import pytest
from unittest.mock import MagicMock, patch
from app.services.sheets_sync import SheetsSyncService

@pytest.fixture
def mock_gspread():
    with patch('app.services.sheets_sync.gspread') as mock:
        yield mock

def test_parse_record():
    service = SheetsSyncService()
    record = {
        'Archive': 'WSOP',
        'Category': 'Main Event',
        'PIC': 'John',
        'Status': 'working',
        'Total Videos': 100,
        'Done Videos': 50,
    }
    # ... 테스트 로직
```

### 4.2 E2E 테스트

```typescript
// frontend/tests/e2e/functional/sync-status.spec.ts

test('should display sync status when enabled', async ({ page }) => {
  await page.goto('/work-status');

  // Workers 탭으로 이동
  await page.getByRole('button', { name: /Workers/i }).click();

  // 동기화 상태가 표시되는지 확인 (enabled일 때)
  // ...
});
```

---

## 5. 배포 체크리스트

- [ ] Google Cloud 프로젝트에서 Sheets API 활성화
- [ ] Service Account 생성 및 JSON 키 다운로드
- [ ] 대상 Google Sheet에 Service Account 이메일 공유
- [ ] `backend/credentials/service_account.json` 배치
- [ ] `.env`에 `GOOGLE_SHEETS_URL` 설정
- [ ] `.env`에 `SHEETS_SYNC_ENABLED=true` 설정
- [ ] Docker 볼륨 마운트 설정 (credentials 폴더)
- [ ] 로그 확인: 첫 동기화 성공 여부

---

## 6. 기존 기능과의 호환성

### CSV Import/Export
- **유지**: 수동 CSV import/export 기능은 그대로 유지
- **용도**: 백업, 오프라인 데이터 이동, 디버깅
- **우선순위**: Google Sheets 동기화가 Source of Truth

### Worker Stats API
- **변경 없음**: 기존 API 엔드포인트 그대로 유지
- **데이터 소스**: 동일한 `work_status` 테이블
- **차이점**: 데이터 입력 방식만 CSV → Sheets로 변경

---

## 7. 롤백 계획

문제 발생 시:
1. `.env`에서 `SHEETS_SYNC_ENABLED=false` 설정
2. Docker 재시작
3. 기존 CSV import로 데이터 복구

---

## 8. 다음 단계

이 가이드를 기반으로 구현을 시작하기 전에:

1. **Google Sheet URL 제공** - 사용자로부터 대상 시트 URL 수신
2. **Service Account 설정** - Google Cloud Console에서 설정
3. **시트 스키마 확인** - 실제 컬럼 이름 확인 및 매핑 조정
