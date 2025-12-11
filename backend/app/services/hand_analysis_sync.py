"""
Hand Analysis Google Sheets 동기화 서비스

Source of Truth: Google Sheets (WSOP Circuit LA - 8개 워크시트)
Target: hand_analyses 테이블

Block: sync.hands
"""
import logging
import json
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.config import settings
from app.core.database import async_session_maker
from app.models.hand_analysis import HandAnalysis

logger = logging.getLogger(__name__)


@dataclass
class HandSyncResult:
    """동기화 결과"""
    success: bool
    synced_at: datetime
    total_records: int
    synced_count: int
    created_count: int = 0
    updated_count: int = 0
    worksheets_processed: int = 0
    error: Optional[str] = None
    details: List[str] = field(default_factory=list)


class HandAnalysisSyncService:
    """
    Hand Analysis Google Sheets 동기화 서비스

    - 8개 워크시트 순회
    - 헤더 위치 자동 감지 (Row 1 or Row 3)
    - 타임코드 파싱 (HH:MM:SS → 초)
    - 태그 JSON 변환
    """

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    # 표준 헤더 매핑 (다양한 컬럼명 정규화)
    HEADER_MAP = {
        'file no.': 'file_no',
        'file no': 'file_no',
        'file name': 'file_name',
        'filename': 'file_name',
        'nas folder link': 'nas_path',
        'nas path': 'nas_path',
        'in': 'timecode_in',
        'out': 'timecode_out',
        'hand grade': 'hand_grade',
        'grade': 'hand_grade',
        'winner': 'winner',
        'hands': 'hands',
        'hand': 'hands',
    }

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._client: Optional[gspread.Client] = None
        self.last_sync_time: Optional[datetime] = None
        self.last_sync_result: Optional[HandSyncResult] = None
        self.last_error: Optional[str] = None
        self.status: str = "idle"
        self._is_started: bool = False

    @property
    def next_sync_time(self) -> Optional[datetime]:
        """다음 동기화 예정 시간"""
        job = self.scheduler.get_job('hand_analysis_sync')
        return job.next_run_time if job else None

    @property
    def is_enabled(self) -> bool:
        """동기화 활성화 여부"""
        return settings.HAND_ANALYSIS_SYNC_ENABLED and bool(settings.HAND_ANALYSIS_SHEET_URL)

    async def start(self):
        """동기화 서비스 시작"""
        if self._is_started:
            logger.warning("Hand analysis sync service already started")
            return

        if not self.is_enabled:
            logger.info("Hand analysis sync disabled - skipping startup")
            return

        try:
            self.scheduler.add_job(
                self._sync_wrapper,
                'interval',
                minutes=settings.SHEETS_SYNC_INTERVAL_MINUTES,
                id='hand_analysis_sync',
                replace_existing=True,
            )
            self.scheduler.start()
            self._is_started = True
            logger.info(
                f"Hand analysis sync scheduler started "
                f"(interval: {settings.SHEETS_SYNC_INTERVAL_MINUTES}m)"
            )

            # 시작 시 즉시 1회 동기화
            await self._sync_wrapper()

        except Exception as e:
            logger.exception(f"Failed to start hand analysis sync service: {e}")
            self.status = "error"
            self.last_error = str(e)

    async def stop(self):
        """동기화 서비스 중지"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self._is_started = False
            logger.info("Hand analysis sync scheduler stopped")

    def _get_client(self) -> gspread.Client:
        """Google Sheets 클라이언트 획득 (lazy initialization)"""
        if self._client is None:
            possible_paths = [
                Path(settings.GOOGLE_SERVICE_ACCOUNT_FILE),
                Path("..") / settings.GOOGLE_SERVICE_ACCOUNT_FILE,
                Path("backend") / settings.GOOGLE_SERVICE_ACCOUNT_FILE,
                Path(__file__).parent.parent.parent.parent / settings.GOOGLE_SERVICE_ACCOUNT_FILE,
                Path("/app/credentials/service_account_key.json"),
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
            logger.exception(f"Hand analysis sync failed: {e}")
            self.last_error = str(e)
            self.status = "error"

    async def sync(self) -> HandSyncResult:
        """Google Sheets에서 핸드 데이터 동기화"""
        self.status = "syncing"
        logger.info("Starting hand analysis sync...")

        try:
            client = self._get_client()
            sheet = client.open_by_url(settings.HAND_ANALYSIS_SHEET_URL)
            worksheets = sheet.worksheets()

            logger.info(f"Found {len(worksheets)} worksheets")

            total_records = 0
            synced_count = 0
            created_count = 0
            updated_count = 0
            details = []

            async with async_session_maker() as db:
                for ws in worksheets:
                    ws_result = await self._sync_worksheet(db, ws)
                    total_records += ws_result['total']
                    synced_count += ws_result['synced']
                    created_count += ws_result['created']
                    updated_count += ws_result['updated']
                    if ws_result['synced'] > 0:
                        details.append(f"{ws.title}: {ws_result['synced']} records")

                await db.commit()

            result = HandSyncResult(
                success=True,
                synced_at=datetime.now(),
                total_records=total_records,
                synced_count=synced_count,
                created_count=created_count,
                updated_count=updated_count,
                worksheets_processed=len(worksheets),
                details=details,
            )

            self.last_sync_time = result.synced_at
            self.last_sync_result = result
            self.last_error = None
            self.status = "idle"

            logger.info(
                f"Hand analysis sync completed: {synced_count}/{total_records} records "
                f"from {len(worksheets)} worksheets "
                f"(created: {created_count}, updated: {updated_count})"
            )
            return result

        except gspread.exceptions.APIError as e:
            error_msg = f"Google Sheets API error: {e}"
            logger.error(error_msg)
            self.last_error = error_msg
            self.status = "error"
            return HandSyncResult(
                success=False,
                synced_at=datetime.now(),
                total_records=0,
                synced_count=0,
                error=error_msg,
            )

        except Exception as e:
            error_msg = f"Hand analysis sync error: {e}"
            logger.exception(error_msg)
            self.last_error = str(e)
            self.status = "error"
            return HandSyncResult(
                success=False,
                synced_at=datetime.now(),
                total_records=0,
                synced_count=0,
                error=str(e),
            )

    async def _sync_worksheet(
        self,
        db: AsyncSession,
        worksheet: gspread.Worksheet,
    ) -> Dict[str, int]:
        """개별 워크시트 동기화"""
        ws_title = worksheet.title
        logger.info(f"Processing worksheet: {ws_title}")

        try:
            all_values = worksheet.get_all_values()

            if len(all_values) < 2:
                logger.warning(f"Worksheet {ws_title} has insufficient rows")
                return {'total': 0, 'synced': 0, 'created': 0, 'updated': 0}

            # 헤더 찾기 (Row 1 또는 Row 3)
            header_idx, headers = self._find_headers(all_values)
            if header_idx is None:
                logger.warning(f"No valid headers found in {ws_title}")
                return {'total': 0, 'synced': 0, 'created': 0, 'updated': 0}

            data_rows = all_values[header_idx + 1:]
            logger.info(f"  Headers at row {header_idx + 1}: {headers[:8]}")
            logger.info(f"  Data rows: {len(data_rows)}")

            synced = 0
            created = 0
            updated = 0

            for row_idx, row in enumerate(data_rows):
                try:
                    record = self._parse_row(headers, row, ws_title, header_idx + row_idx + 2)
                    if record is None:
                        continue

                    # Upsert (file_name + source_worksheet + file_no로 unique 판단)
                    result = await db.execute(
                        select(HandAnalysis).where(
                            HandAnalysis.file_name == record['file_name'],
                            HandAnalysis.source_worksheet == ws_title,
                            HandAnalysis.file_no == record.get('file_no'),
                        )
                    )
                    existing = result.scalar_one_or_none()

                    if existing:
                        # 업데이트
                        for key, value in record.items():
                            setattr(existing, key, value)
                        updated += 1
                    else:
                        # 신규 추가
                        new_hand = HandAnalysis(**record)
                        db.add(new_hand)
                        created += 1

                    synced += 1

                except Exception as e:
                    logger.warning(f"Failed to sync row {row_idx} in {ws_title}: {e}")

            return {'total': len(data_rows), 'synced': synced, 'created': created, 'updated': updated}

        except Exception as e:
            logger.error(f"Error processing worksheet {ws_title}: {e}")
            return {'total': 0, 'synced': 0, 'created': 0, 'updated': 0}

    def _find_headers(self, all_values: List[List[str]]) -> tuple:
        """헤더 행 찾기 (Row 1 또는 Row 3)"""
        for idx in [0, 2]:  # Row 1, Row 3 시도
            if idx >= len(all_values):
                continue

            row = all_values[idx]
            # 필수 컬럼 확인
            row_lower = [c.lower().strip() for c in row]

            has_file = any('file' in c for c in row_lower)
            has_in_out = 'in' in row_lower or 'out' in row_lower

            if has_file and has_in_out:
                headers = [self._normalize_header(h) for h in row]
                return idx, headers

        return None, []

    def _normalize_header(self, header: str) -> str:
        """헤더 정규화"""
        normalized = ' '.join(header.lower().strip().split())

        # 매핑 테이블에서 찾기
        for key, value in self.HEADER_MAP.items():
            if key in normalized:
                return value

        # Tag 컬럼 처리
        if 'tag' in normalized and 'player' in normalized:
            return 'player_tag'
        if 'tag' in normalized and 'poker' in normalized:
            return 'poker_play_tag'
        if 'tag' in normalized:
            return 'tag'

        return normalized

    def _parse_row(
        self,
        headers: List[str],
        row: List[str],
        worksheet_name: str,
        row_number: int,
    ) -> Optional[Dict[str, Any]]:
        """행 데이터 파싱"""
        if len(row) < len(headers):
            row = row + [''] * (len(headers) - len(row))

        record = {headers[i]: row[i] for i in range(len(headers))}

        # 필수 필드 확인
        file_name = str(record.get('file_name', '')).strip()
        if not file_name:
            return None

        # 타임코드 파싱
        timecode_in = str(record.get('timecode_in', '')).strip()
        timecode_out = str(record.get('timecode_out', '')).strip()

        if not timecode_in and not timecode_out:
            return None  # 타임코드 없으면 스킵

        # 플레이어 태그 수집
        player_tags = []
        poker_play_tags = []

        for key, value in record.items():
            if key == 'player_tag' and value:
                player_tags.append(value.strip())
            elif key == 'poker_play_tag' and value:
                poker_play_tags.append(value.strip())
            elif key == 'tag' and value:
                # 일반 태그는 플레이어 태그로 분류
                player_tags.append(value.strip())

        return {
            'file_name': file_name,
            'nas_path': str(record.get('nas_path', '')).strip() or None,
            'timecode_in': timecode_in or None,
            'timecode_out': timecode_out or None,
            'timecode_in_sec': self._parse_timecode(timecode_in),
            'timecode_out_sec': self._parse_timecode(timecode_out),
            'file_no': self._parse_int(record.get('file_no')),
            'hand_grade': str(record.get('hand_grade', '')).strip() or None,
            'winner': str(record.get('winner', '')).strip() or None,
            'hands': str(record.get('hands', '')).strip() or None,
            'player_tags': json.dumps(player_tags, ensure_ascii=False) if player_tags else None,
            'poker_play_tags': json.dumps(poker_play_tags, ensure_ascii=False) if poker_play_tags else None,
            'source_worksheet': worksheet_name,
            'source_row': row_number,
        }

    def _parse_timecode(self, timecode_str: str) -> float:
        """
        타임코드 문자열 → 초 변환

        지원 형식:
        - "1:23:45" → 5025초
        - "6:58:55" → 25135초
        - "45:30" → 2730초
        """
        if not timecode_str or not timecode_str.strip():
            return 0.0

        timecode_str = timecode_str.strip()

        try:
            parts = timecode_str.split(':')

            if len(parts) == 3:
                h, m, s = map(float, parts)
                return h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m, s = map(float, parts)
                return m * 60 + s
            else:
                return 0.0

        except (ValueError, TypeError):
            return 0.0

    def _parse_int(self, value: Any) -> Optional[int]:
        """정수 파싱"""
        if value is None or value == '':
            return None
        try:
            return int(float(str(value).strip()))
        except (ValueError, TypeError):
            return None

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
                "worksheets_processed": self.last_sync_result.worksheets_processed,
            } if self.last_sync_result else None,
        }


# 싱글톤 인스턴스
hand_analysis_sync_service = HandAnalysisSyncService()
