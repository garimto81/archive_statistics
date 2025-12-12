"""
Google Sheets 자동 동기화 서비스

Source of Truth: Google Sheets (Work Status)
Target: work_status 테이블

Block: sync.sheets
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session_maker
from app.models.work_status import WorkStatus, Archive

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """동기화 결과"""
    success: bool
    synced_at: datetime
    total_records: int
    synced_count: int
    created_count: int = 0
    updated_count: int = 0
    error: Optional[str] = None
    details: List[str] = field(default_factory=list)


class SheetsSyncService:
    """
    Google Sheets 자동 동기화 서비스

    - Service Account 인증
    - 주기적 백그라운드 동기화 (APScheduler)
    - Work Status 시트 → work_status 테이블 동기화
    """

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._client: Optional[gspread.Client] = None
        self.last_sync_time: Optional[datetime] = None
        self.last_sync_result: Optional[SyncResult] = None
        self.last_error: Optional[str] = None
        self.status: str = "idle"
        self._is_started: bool = False

    @property
    def next_sync_time(self) -> Optional[datetime]:
        """다음 동기화 예정 시간"""
        job = self.scheduler.get_job('sheets_sync')
        return job.next_run_time if job else None

    @property
    def is_enabled(self) -> bool:
        """동기화 활성화 여부"""
        return settings.SHEETS_SYNC_ENABLED and bool(settings.WORK_STATUS_SHEET_URL)

    async def start(self):
        """동기화 서비스 시작"""
        if self._is_started:
            logger.warning("Sheets sync service already started")
            return

        if not self.is_enabled:
            logger.info("Sheets sync disabled - skipping startup")
            return

        # Service Account 파일 존재 확인
        sa_path = Path(settings.GOOGLE_SERVICE_ACCOUNT_FILE)
        if not sa_path.exists():
            # backend 폴더 기준으로도 확인
            sa_path = Path("backend") / settings.GOOGLE_SERVICE_ACCOUNT_FILE
            if not sa_path.exists():
                logger.error(f"Service account file not found: {settings.GOOGLE_SERVICE_ACCOUNT_FILE}")
                self.status = "error"
                self.last_error = "Service account file not found"
                return

        try:
            self.scheduler.add_job(
                self._sync_wrapper,
                'interval',
                minutes=settings.SHEETS_SYNC_INTERVAL_MINUTES,
                id='sheets_sync',
                replace_existing=True,
            )
            self.scheduler.start()
            self._is_started = True
            logger.info(
                f"Sheets sync scheduler started "
                f"(interval: {settings.SHEETS_SYNC_INTERVAL_MINUTES}m)"
            )

            # 시작 시 즉시 1회 동기화
            await self._sync_wrapper()

        except Exception as e:
            logger.exception(f"Failed to start sheets sync service: {e}")
            self.status = "error"
            self.last_error = str(e)

    async def stop(self):
        """동기화 서비스 중지"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self._is_started = False
            logger.info("Sheets sync scheduler stopped")

    def _get_client(self) -> gspread.Client:
        """Google Sheets 클라이언트 획득 (lazy initialization)"""
        if self._client is None:
            # Service Account 파일 경로 확인 (여러 위치 시도)
            possible_paths = [
                Path(settings.GOOGLE_SERVICE_ACCOUNT_FILE),  # 환경변수 경로 (Docker: /app/credentials/...)
                Path("..") / settings.GOOGLE_SERVICE_ACCOUNT_FILE,  # 상위 디렉토리
                Path("backend") / settings.GOOGLE_SERVICE_ACCOUNT_FILE,  # backend 하위
                Path(__file__).parent.parent.parent.parent / settings.GOOGLE_SERVICE_ACCOUNT_FILE,  # 프로젝트 루트
                Path("/app/credentials/service_account_key.json"),  # Docker 컨테이너 내 절대 경로
            ]

            sa_path = None
            for p in possible_paths:
                if p.exists():
                    sa_path = p
                    break

            if sa_path is None:
                raise FileNotFoundError(
                    f"Service account file not found. Tried: {[str(p) for p in possible_paths]}"
                )

            creds = Credentials.from_service_account_file(
                str(sa_path),
                scopes=self.SCOPES,
            )
            self._client = gspread.authorize(creds)
            logger.info(f"Google Sheets client initialized (using: {sa_path})")
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
            sheet = client.open_by_url(settings.WORK_STATUS_SHEET_URL)
            worksheet = sheet.get_worksheet(0)

            # 시트 구조: Row 1 = 제목, Row 2 = 헤더, Row 3+ = 데이터
            # get_all_values()로 raw 데이터를 가져와서 직접 파싱
            all_values = worksheet.get_all_values()

            if len(all_values) < 3:
                logger.warning("Sheet has insufficient rows")
                result = SyncResult(
                    success=True,
                    synced_at=datetime.now(),
                    total_records=0,
                    synced_count=0,
                    error="Sheet has insufficient rows",
                )
                # 상태 업데이트 (early return 케이스)
                self.last_sync_time = result.synced_at
                self.last_sync_result = result
                self.status = "idle"
                return result

            # Row 2를 헤더로 사용 (index 1)
            headers = [self._normalize_header(h) for h in all_values[1]]
            data_rows = all_values[2:]  # Row 3부터 데이터

            # 딕셔너리 리스트로 변환 (병합 셀 처리)
            records = []
            last_archive = ""  # 병합 셀: 빈 Archive는 이전 값 상속

            for row in data_rows:
                if len(row) >= len(headers):
                    record = {headers[i]: row[i] for i in range(len(headers))}

                    # 병합 셀 처리: Archive가 비어있으면 이전 값 사용
                    current_archive = str(record.get('Archive', '')).strip()
                    if current_archive:
                        last_archive = current_archive
                    else:
                        record['Archive'] = last_archive

                    records.append(record)

            logger.info(f"Fetched {len(records)} records from sheets (headers: {headers})")

            # 2. DB 동기화
            async with async_session_maker() as db:
                result = await self._sync_to_db(db, records)
                await db.commit()

            # 3. 결과 기록
            self.last_sync_time = result.synced_at
            self.last_sync_result = result
            self.last_error = None
            self.status = "idle"

            logger.info(
                f"Sync completed: {result.synced_count}/{result.total_records} records "
                f"(created: {result.created_count}, updated: {result.updated_count})"
            )
            return result

        except gspread.exceptions.APIError as e:
            error_msg = f"Google Sheets API error: {e}"
            logger.error(error_msg)
            result = SyncResult(
                success=False,
                synced_at=datetime.now(),
                total_records=0,
                synced_count=0,
                error=error_msg,
            )
            # 에러 시에도 last_sync_time 업데이트 (시도 시간 기록)
            self.last_sync_time = result.synced_at
            self.last_sync_result = result
            self.last_error = error_msg
            self.status = "error"
            return result

        except Exception as e:
            error_msg = f"Sync error: {e}"
            logger.exception(error_msg)
            result = SyncResult(
                success=False,
                synced_at=datetime.now(),
                total_records=0,
                synced_count=0,
                error=str(e),
            )
            # 에러 시에도 last_sync_time 업데이트 (시도 시간 기록)
            self.last_sync_time = result.synced_at
            self.last_sync_result = result
            self.last_error = str(e)
            self.status = "error"
            return result

    async def _sync_to_db(
        self,
        db: AsyncSession,
        records: List[Dict[str, Any]],
    ) -> SyncResult:
        """DB에 데이터 동기화 (Upsert 방식)"""
        synced_count = 0
        created_count = 0
        updated_count = 0
        details: List[str] = []

        # 아카이브 캐시 (이름 → ID 매핑)
        archive_cache: Dict[str, int] = {}

        for record in records:
            try:
                # 빈 행 스킵 (Archive 또는 Category가 비어있으면 스킵)
                archive_name = str(record.get('Archive', '')).strip()
                category = str(record.get('Category', '')).strip()
                if not archive_name or not category:
                    continue

                # Archive 처리
                if archive_name not in archive_cache:
                    archive = await self._get_or_create_archive(db, archive_name)
                    archive_cache[archive_name] = archive.id

                archive_id = archive_cache[archive_name]
                # category는 이미 위에서 추출됨

                # 기존 레코드 조회 (archive_id + category로 unique 판단)
                result = await db.execute(
                    select(WorkStatus).where(
                        WorkStatus.archive_id == archive_id,
                        WorkStatus.category == category,
                    )
                )
                existing = result.scalar_one_or_none()

                # 데이터 파싱 (정규화된 헤더 이름 사용)
                # PIC에 줄바꿈이 있을 수 있으므로 정리
                pic_raw = str(record.get('PIC', '')).strip()
                pic = ' '.join(pic_raw.split()) if pic_raw else None

                status = self._normalize_status(str(record.get('Status', '대기')))
                total_videos = self._parse_int(record.get('Total', 0))
                excel_done = self._parse_int(record.get('Excel Done', 0))
                notes1 = str(record.get('Notes 1', '')).strip() or None
                notes2 = str(record.get('Notes 2', '')).strip() or None

                if existing:
                    # 업데이트
                    existing.pic = pic
                    existing.status = status
                    existing.total_videos = total_videos
                    existing.excel_done = excel_done
                    existing.notes1 = notes1
                    existing.notes2 = notes2
                    updated_count += 1
                else:
                    # 신규 추가
                    new_work_status = WorkStatus(
                        archive_id=archive_id,
                        category=category,
                        pic=pic,
                        status=status,
                        total_videos=total_videos,
                        excel_done=excel_done,
                        notes1=notes1,
                        notes2=notes2,
                    )
                    db.add(new_work_status)
                    created_count += 1
                    details.append(f"Created: {archive_name}/{category}")

                synced_count += 1

            except Exception as e:
                logger.warning(f"Failed to sync record: {record}, error: {e}")
                details.append(f"Error: {record.get('Archive', 'Unknown')} - {e}")

        return SyncResult(
            success=True,
            synced_at=datetime.now(),
            total_records=len(records),
            synced_count=synced_count,
            created_count=created_count,
            updated_count=updated_count,
            details=details,
        )

    async def _get_or_create_archive(
        self,
        db: AsyncSession,
        name: str,
    ) -> Archive:
        """Archive 조회 또는 생성"""
        result = await db.execute(
            select(Archive).where(Archive.name == name)
        )
        archive = result.scalar_one_or_none()

        if not archive:
            archive = Archive(name=name)
            db.add(archive)
            await db.flush()
            logger.info(f"Created new archive: {name}")

        return archive

    def _normalize_header(self, header: str) -> str:
        """헤더 이름 정규화 (줄바꿈 제거, 공백 정리)"""
        # 줄바꿈을 공백으로 변환 후 정리
        normalized = ' '.join(header.split())
        # 괄호 내용 제거 (예: "Total (# of videos)" → "Total")
        if '(' in normalized:
            normalized = normalized.split('(')[0].strip()
        return normalized

    def _normalize_status(self, status: str) -> str:
        """
        상태 값 정규화

        Google Sheets에서 Status 필드가 복합 문자열일 수 있음:
        예: "WSOP Paradise, WSOP LA \n작업 중" → "작업 중"

        처리 전략:
        1. 줄바꿈으로 분리하여 각 부분에서 상태 키워드 찾기
        2. 키워드 매칭 실패 시 원본 반환
        """
        if not status:
            return '대기'

        status_map = {
            '대기': '대기',
            'waiting': '대기',
            'pending': '대기',
            '작업 중': '작업 중',
            '작업중': '작업 중',
            '진행 중': '작업 중',
            '진행중': '작업 중',
            '작업 中': '작업 중',
            '작업中': '작업 중',
            'in progress': '작업 중',
            'working': '작업 중',
            '검토': '검토',
            'review': '검토',
            '완료': '완료',
            'done': '완료',
            'complete': '완료',
            'completed': '완료',
        }

        # 줄바꿈으로 분리하여 각 부분 검사
        parts = status.replace('\n', ' ').split()

        # 전체 문자열에서 키워드 매칭 시도
        status_lower = status.lower().strip()
        if status_lower in status_map:
            return status_map[status_lower]

        # 부분 문자열에서 키워드 검색
        for key, value in status_map.items():
            if key in status_lower:
                return value

        # 매칭 실패 시 빈 값이면 기본값, 아니면 원본 유지
        return status.strip() if status.strip() else '대기'

    def _parse_int(self, value: Any) -> int:
        """정수 파싱 (빈 값, 문자열 처리)"""
        if value is None or value == '':
            return 0
        try:
            # 콤마 제거 후 파싱
            if isinstance(value, str):
                value = value.replace(',', '').strip()
            return int(float(value))
        except (ValueError, TypeError):
            return 0

    def get_status_dict(self) -> Dict[str, Any]:
        """현재 상태를 딕셔너리로 반환"""
        return {
            "enabled": self.is_enabled,
            "status": self.status,
            "last_sync": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "next_sync": self.next_sync_time.isoformat() if self.next_sync_time else None,
            "error": self.last_error,
            "interval_minutes": settings.SHEETS_SYNC_INTERVAL_MINUTES,
            "last_result": {
                "total_records": self.last_sync_result.total_records,
                "synced_count": self.last_sync_result.synced_count,
                "created_count": self.last_sync_result.created_count,
                "updated_count": self.last_sync_result.updated_count,
            } if self.last_sync_result else None,
        }


# 싱글톤 인스턴스
sheets_sync_service = SheetsSyncService()
