"""
Progress Service - 통합 진행률 계산

핵심 원칙:
1. archive db (work_status): 폴더-카테고리 매칭 유지
2. metadata db (hand_analysis): 파일 기반 매칭 → 폴더로 집계
3. 하이어라키: 모든 폴더 + 파일 출력
4. 진행률 바: 최상위부터 모든 레벨에서 표시

Block: progress.service
"""
import re
import logging
from typing import Optional, List, Dict, Any, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.file_stats import FolderStats, FileStats
from app.models.hand_analysis import HandAnalysis
from app.models.work_status import WorkStatus

logger = logging.getLogger(__name__)


# ==================== Helper Functions ====================

def format_duration(seconds: float) -> str:
    """초를 HH:MM:SS 형식으로 변환"""
    if not seconds or seconds <= 0:
        return "00:00:00"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_size(size_bytes: int) -> str:
    """바이트를 읽기 쉬운 형식으로 변환"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    elif size_bytes < 1024 * 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024 * 1024):.2f} TB"


def normalize_name(name: str) -> str:
    """파일명/비디오제목 정규화"""
    if not name:
        return ""
    name = re.sub(r'\.[a-zA-Z0-9]{2,4}$', '', name)
    name = name.lower()
    name = re.sub(r'[^a-z0-9가-힣\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def extract_keywords(text: str) -> Set[str]:
    """텍스트에서 키워드 추출"""
    stopwords = {'the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for'}
    normalized = normalize_name(text)
    words = set(normalized.split())
    return words - stopwords


def calculate_similarity(name1: str, name2: str) -> float:
    """두 이름의 키워드 유사도 계산"""
    kw1 = extract_keywords(name1)
    kw2 = extract_keywords(name2)
    if not kw1 or not kw2:
        return 0.0
    intersection = kw1 & kw2
    return len(intersection) / min(len(kw1), len(kw2))


# ==================== Main Service ====================

class ProgressService:
    """
    통합 진행률 서비스

    - archive db: 폴더-카테고리 매칭
    - metadata db: 파일 기반 매칭 → 폴더 집계
    """

    SIMILARITY_THRESHOLD = 0.5

    async def get_folder_with_progress(
        self,
        db: AsyncSession,
        path: Optional[str] = None,
        depth: int = 2,
        include_files: bool = False,
        extensions: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        폴더 트리와 진행률 정보를 함께 반환

        Args:
            db: 데이터베이스 세션
            path: 시작 경로 (None이면 루트)
            depth: 탐색 깊이
            include_files: 파일 목록 포함 여부
            extensions: 확장자 필터 목록 (예: ['.mp4', '.mkv'])
        """
        # Step 1: Work Status 전체 로드 (archive db)
        work_statuses = await self._load_work_statuses(db)
        logger.info(f"Loaded {len(work_statuses)} work statuses from archive db")

        # Step 2: Hand Analysis 전체 로드 (metadata db)
        hand_data = await self._load_hand_analysis_data(db)
        logger.info(f"Loaded {len(hand_data)} unique file titles from metadata db")

        # Step 3: 폴더 트리 구축
        if path:
            query = select(FolderStats).where(FolderStats.parent_path == path)
        else:
            query = select(FolderStats).where(FolderStats.depth == 0)

        result = await db.execute(query.order_by(FolderStats.total_size.desc()))
        folders = result.scalars().all()

        tree = []
        for folder in folders:
            folder_data = await self._build_folder_progress(
                db, folder, work_statuses, hand_data, depth, 0, include_files, extensions
            )
            tree.append(folder_data)

        return tree

    async def _load_work_statuses(self, db: AsyncSession) -> Dict[str, Any]:
        """Work Status (archive db) 로드 - 카테고리 기준"""
        result = await db.execute(select(WorkStatus))
        work_statuses = {}
        for ws in result.scalars().all():
            # progress_percent 계산: excel_done / total_videos * 100
            # DB에 저장된 값 대신 동적으로 계산 (calculate_progress와 동일 로직)
            progress_percent = 0.0
            if ws.total_videos and ws.total_videos > 0:
                progress_percent = (ws.excel_done / ws.total_videos) * 100

            work_statuses[ws.category] = {
                "id": ws.id,
                "category": ws.category,
                "pic": ws.pic,
                "status": ws.status,
                "total_videos": ws.total_videos,
                "excel_done": ws.excel_done,
                "progress_percent": progress_percent,  # 동적 계산
                "notes1": ws.notes1,
                "notes2": ws.notes2,
            }
        return work_statuses

    async def _load_hand_analysis_data(self, db: AsyncSession) -> Dict[str, Dict]:
        """Hand Analysis (metadata db) 로드 - file_name 기준"""
        query = select(
            HandAnalysis.file_name,
            func.count(HandAnalysis.id).label('hand_count'),
            func.max(HandAnalysis.timecode_out_sec).label('max_timecode'),
        ).where(
            HandAnalysis.file_name.isnot(None),
            HandAnalysis.file_name != ''
        ).group_by(HandAnalysis.file_name)

        result = await db.execute(query)

        hand_data = {}
        for row in result.fetchall():
            file_name = row[0]
            hand_data[file_name] = {
                'hand_count': row[1],
                'max_timecode_sec': row[2] or 0,
                'max_timecode_formatted': format_duration(row[2] or 0),
            }

        return hand_data

    def _match_work_statuses(
        self,
        folder_name: str,
        folder_path: str,
        work_statuses: Dict[str, Dict]
    ) -> List[Dict]:
        """폴더명과 Work Status 카테고리 매칭 (여러 개 반환)

        매칭 전략 (우선순위):
        1. 정확히 일치 (카테고리 == 폴더명)
        2. 카테고리가 폴더명으로 시작 (예: "PAD S12" starts with "PAD")
        3. 폴더명이 카테고리에 독립 단어로 포함 (공백으로 분리된 단어)

        주의: 부분 문자열 매칭(substring)은 의도하지 않은 매칭을 유발하므로 제외
        - 예: "WSOP" in "WSOP Europe" → 허용 (독립 단어)
        - 예: "WSOP" in "WSOPE" → 제외 (부분 문자열)

        Returns:
            매칭된 work_status 목록 (progress_percent 내림차순 정렬)
        """
        matched = []
        folder_lower = folder_name.lower()

        for category, ws in work_statuses.items():
            category_lower = category.lower()

            # 1. 정확히 일치
            if folder_lower == category_lower:
                matched.append((ws, 1.0, 'exact'))
                continue

            # 2. 카테고리가 폴더명으로 시작 (예: "PAD S12" → "PAD")
            # 폴더명 뒤에 공백이 와야 함 (WSOPE 폴더가 WSOP로 매칭되는 것 방지)
            if category_lower.startswith(folder_lower + ' '):
                matched.append((ws, 0.9, 'prefix'))
                continue

            # 2.5. 폴더명이 카테고리로 시작 (예: "GOG 최종" → "GOG")
            # 카테고리 뒤에 공백 또는 언더스코어가 와야 함
            if folder_lower.startswith(category_lower + ' ') or folder_lower.startswith(category_lower + '_'):
                matched.append((ws, 0.85, 'folder_prefix'))
                continue

            # 3. 폴더명이 카테고리에 독립 단어로 포함 (공백으로 분리된 단어)
            # 예: "2023 WSOP Paradise"에서 "WSOP"는 독립 단어로 매칭됨
            category_words = category_lower.split()
            if folder_lower in category_words:
                matched.append((ws, 0.8, 'word'))
                continue

            # 4. 연도 매칭: 폴더명이 4자리 숫자(연도)인 경우 카테고리에 해당 연도가 있으면 매칭
            if folder_lower.isdigit() and len(folder_lower) == 4:
                # 연도도 독립 단어로만 매칭 (1973이 19730에 매칭되는 것 방지)
                if folder_lower in category_words:
                    matched.append((ws, 0.7, 'year'))

            # 부분 문자열 매칭(substring)은 제외 - 의도하지 않은 매칭 방지
            # 예: "WSOP" in "WSOPE" → 제외

        # 정렬: 우선순위 점수 > progress_percent
        matched.sort(key=lambda x: (x[1], x[0].get('progress_percent', 0)), reverse=True)

        # 상위 매칭만 반환 (같은 점수 그룹)
        if not matched:
            return []

        top_score = matched[0][1]
        result = [m[0] for m in matched if m[1] >= top_score - 0.1]

        return result

    def _match_file_to_hand(
        self,
        file_name: str,
        hand_data: Dict[str, Dict]
    ) -> Tuple[Optional[str], Dict]:
        """NAS 파일명과 Hand Analysis file_name 매칭"""
        if not file_name or not hand_data:
            return None, {}

        file_normalized = normalize_name(file_name)
        best_match = None
        best_score = 0.0

        for hand_title, hand_info in hand_data.items():
            hand_normalized = normalize_name(hand_title)

            # 1. 정확 일치
            if file_normalized == hand_normalized:
                return hand_title, hand_info

            # 2. 포함 관계
            if file_normalized in hand_normalized or hand_normalized in file_normalized:
                score = 0.8
                if score > best_score:
                    best_score = score
                    best_match = hand_title

            # 3. 키워드 유사도
            similarity = calculate_similarity(file_name, hand_title)
            if similarity > best_score and similarity >= self.SIMILARITY_THRESHOLD:
                best_score = similarity
                best_match = hand_title

        if best_match:
            return best_match, hand_data[best_match]

        return None, {}

    async def _build_folder_progress(
        self,
        db: AsyncSession,
        folder: FolderStats,
        work_statuses: Dict[str, Dict],
        hand_data: Dict[str, Dict],
        max_depth: int,
        current_depth: int,
        include_files: bool,
        extensions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """폴더 데이터 구축 (archive db + metadata db 통합)"""

        # 기본 폴더 정보
        folder_dict = {
            "id": folder.id,
            "name": folder.name,
            "path": folder.path,
            "size": folder.total_size,
            "size_formatted": format_size(folder.total_size),
            "file_count": folder.file_count,
            "folder_count": folder.folder_count,
            "duration": folder.total_duration,
            "duration_formatted": format_duration(folder.total_duration),
            "depth": folder.depth,
        }

        # === archive db: Work Status 매칭 ===
        # 우선순위: 1. FK 기반 (명시적 연결) > 2. Fuzzy matching (fallback)
        work_statuses_matched = []
        matching_method = "none"

        # 1. FK 기반 조회 (folder.work_status_id가 있으면)
        if hasattr(folder, 'work_status_id') and folder.work_status_id:
            # work_statuses dict에서 해당 ID 찾기
            for category, ws in work_statuses.items():
                if ws.get("id") == folder.work_status_id:
                    work_statuses_matched = [ws]
                    matching_method = "fk"
                    break

        # 2. Fuzzy matching fallback (FK가 없는 경우)
        if not work_statuses_matched:
            work_statuses_matched = self._match_work_statuses(folder.name, folder.path, work_statuses)
            if work_statuses_matched:
                matching_method = "fuzzy"

        folder_dict["work_statuses"] = work_statuses_matched  # 상세 패널용 목록
        folder_dict["matching_method"] = matching_method  # 디버깅용

        # 디버깅: 폴더 매칭 결과 로그
        if current_depth <= 2:
            logger.info(f"[DEBUG] 폴더 매칭: {folder.name} (depth={current_depth}, method={matching_method})")
            logger.info(f"  - 매칭된 work_status 수: {len(work_statuses_matched)}")
            if work_statuses_matched:
                for ws in work_statuses_matched[:3]:  # 최대 3개만 표시
                    logger.info(f"    - 카테고리: {ws.get('category')}, done: {ws.get('excel_done')}/{ws.get('total_videos')}")

        # work_summary 계산 (트리 뷰용 요약)
        # 주의: 진행률은 file_count (NAS 스캔 결과) 기준
        # 단, 구글 시트 원본값(sheets_total_videos, sheets_excel_done)도 함께 표시 (검증용)
        if work_statuses_matched:
            total_done = sum(ws.get("excel_done", 0) for ws in work_statuses_matched)
            # 구글 시트 원본 값 합산 (검증용)
            sheets_total = sum(ws.get("total_videos", 0) for ws in work_statuses_matched)

            # file_count 기준 진행률 계산 (NAS 실제 파일 수)
            combined_progress = (total_done / folder.file_count * 100) if folder.file_count > 0 else 0

            # 90% 이상은 100%로 처리
            if combined_progress >= 90:
                combined_progress = 100.0

            # 구글 시트 기준 진행률 계산 (실제 작업 진행률)
            actual_progress = (total_done / sheets_total * 100) if sheets_total > 0 else 0
            if actual_progress >= 90:
                actual_progress = 100.0

            # 데이터 출처 불일치 감지
            data_mismatch = abs(folder.file_count - sheets_total) > max(folder.file_count, sheets_total) * 0.1  # 10% 이상 차이

            folder_dict["work_summary"] = {
                "task_count": len(work_statuses_matched),
                "total_files": folder.file_count,  # NAS 스캔 결과
                "total_done": total_done,  # 구글 시트 excel_done 합계
                "combined_progress": round(combined_progress, 1),  # NAS 기준 (참고용)
                # 구글 시트 원본 값
                "sheets_total_videos": sheets_total,  # 구글 시트 total_videos 합계
                "sheets_excel_done": total_done,  # 동일 값이지만 명시적으로 표시
                "actual_progress": round(actual_progress, 1),  # 시트 기준 (실제 진행률)
                # 데이터 불일치 정보
                "data_source_mismatch": data_mismatch,
                "mismatch_count": sheets_total - folder.file_count,  # 양수: 시트가 더 많음, 음수: NAS가 더 많음
            }
        else:
            folder_dict["work_summary"] = None
            # 디버깅: 매칭 실패 시 로그
            if current_depth <= 2:
                logger.warning(f"[DEBUG] ⚠️ {folder.name}: 직접 매칭 없음 → work_summary=None (자식 합산 대기)")

        # 하위 호환성: 첫 번째 매칭만 work_status로 유지
        folder_dict["work_status"] = work_statuses_matched[0] if work_statuses_matched else None

        # === metadata db: 파일 기반 Hand Analysis 집계 ===
        files_progress = await self._get_files_with_matching(db, folder.path, hand_data, extensions)

        # 현재 폴더의 직접 파일 통계
        direct_files_count = len(files_progress)
        files_with_hands = sum(1 for f in files_progress if f.get('matched_title'))
        total_hands = sum(f.get('hand_count', 0) for f in files_progress)
        completed_files = sum(1 for f in files_progress if f.get('is_complete', False))
        progress_values = [f['progress_percent'] for f in files_progress if f.get('matched_title')]
        avg_progress = sum(progress_values) / len(progress_values) if progress_values else 0
        progress_sum = sum(progress_values)  # 가중 평균 계산용

        # hand_analysis 초기화 (자식 합산을 위해 항상 생성)
        # total_files: 폴더의 전체 파일 수 (FolderStats.file_count 사용)
        folder_dict["hand_analysis"] = {
            "total_files": folder.file_count,  # 폴더의 전체 파일 수 (하위 포함)
            "files_matched": files_with_hands,
            "hand_count": total_hands,
            "max_timecode_sec": max((f.get('max_timecode_sec', 0) for f in files_progress), default=0),
            "max_timecode_formatted": "00:00:00",
            "avg_progress": round(avg_progress, 1),
            "completed_files": completed_files,
            "match_rate": 0.0,  # 매칭 비율
        }

        # === 자식 폴더 (재귀) ===
        children = []
        # work_summary 합산용 변수 (file_count 기준)
        child_total_files = 0
        child_total_done = 0
        child_task_count = 0
        child_sheets_total = 0  # 구글 시트 원본 값 합산

        if current_depth < max_depth:
            child_result = await db.execute(
                select(FolderStats)
                .where(FolderStats.parent_path == folder.path)
                .order_by(FolderStats.total_size.desc())
            )
            child_folders = child_result.scalars().all()

            for child in child_folders:
                child_data = await self._build_folder_progress(
                    db, child, work_statuses, hand_data,
                    max_depth, current_depth + 1, include_files, extensions
                )
                children.append(child_data)

                # 자식 폴더의 work_summary 합산 (file_count 기준)
                if child_data.get("work_summary"):
                    child_ws = child_data["work_summary"]
                    child_total_files += child_ws.get("total_files", 0)
                    child_total_done += child_ws.get("total_done", 0)
                    child_task_count += child_ws.get("task_count", 0)
                    child_sheets_total += child_ws.get("sheets_total_videos", 0)

                # 자식 폴더의 hand_analysis 합산 (files_matched, hand_count만 합산)
                # total_files는 folder.file_count에 이미 하위 폴더 포함되어 있으므로 합산하지 않음
                if child_data.get("hand_analysis"):
                    child_ha = child_data["hand_analysis"]
                    # total_files는 합산하지 않음 (중복 방지)
                    folder_dict["hand_analysis"]["files_matched"] += child_ha.get("files_matched", 0)
                    folder_dict["hand_analysis"]["hand_count"] += child_ha.get("hand_count", 0)
                    folder_dict["hand_analysis"]["completed_files"] += child_ha.get("completed_files", 0)
                    # 가중 평균을 위한 합산
                    child_matched = child_ha.get("files_matched", 0)
                    child_avg = child_ha.get("avg_progress", 0)
                    progress_sum += child_avg * child_matched

        folder_dict["children"] = children

        # work_summary에 자식 폴더 합산 (file_count 기준)
        if folder_dict["work_summary"]:
            ws = folder_dict["work_summary"]
            ws["total_files"] += child_total_files
            ws["total_done"] += child_total_done
            ws["task_count"] += child_task_count
            ws["sheets_total_videos"] += child_sheets_total
            ws["sheets_excel_done"] = ws["total_done"]  # 동기화
            # combined_progress 재계산 (file_count 기준)
            if ws["total_files"] > 0:
                combined_progress = ws["total_done"] / ws["total_files"] * 100
                # 90% 이상은 100%로 처리
                if combined_progress >= 90:
                    combined_progress = 100.0
                ws["combined_progress"] = round(combined_progress, 1)

            # actual_progress 재계산 (시트 기준)
            if ws["sheets_total_videos"] > 0:
                actual_progress = ws["total_done"] / ws["sheets_total_videos"] * 100
                if actual_progress >= 90:
                    actual_progress = 100.0
                ws["actual_progress"] = round(actual_progress, 1)

            # 데이터 불일치 감지
            ws["data_source_mismatch"] = abs(ws["total_files"] - ws["sheets_total_videos"]) > max(ws["total_files"], ws["sheets_total_videos"]) * 0.1
            ws["mismatch_count"] = ws["sheets_total_videos"] - ws["total_files"]
        elif child_total_files > 0:
            # 현재 폴더에 매칭이 없지만 자식에 있는 경우 → 자식 합산으로 work_summary 생성
            # 디버깅: 자식 합산 로그
            if current_depth <= 2:
                logger.info(f"[DEBUG] ✅ {folder.name}: 자식 합산으로 work_summary 생성!")
                logger.info(f"  - child_total_files: {child_total_files}, child_total_done: {child_total_done}")

            combined_progress = (child_total_done / child_total_files * 100) if child_total_files > 0 else 0
            # 90% 이상은 100%로 처리
            if combined_progress >= 90:
                combined_progress = 100.0

            # actual_progress 계산
            actual_progress = (child_total_done / child_sheets_total * 100) if child_sheets_total > 0 else 0
            if actual_progress >= 90:
                actual_progress = 100.0

            # 데이터 불일치 감지
            data_mismatch = abs(child_total_files - child_sheets_total) > max(child_total_files, child_sheets_total) * 0.1

            folder_dict["work_summary"] = {
                "task_count": child_task_count,
                "total_files": child_total_files,
                "total_done": child_total_done,
                "combined_progress": round(combined_progress, 1),
                "sheets_total_videos": child_sheets_total,
                "sheets_excel_done": child_total_done,
                "actual_progress": round(actual_progress, 1),
                "data_source_mismatch": data_mismatch,
                "mismatch_count": child_sheets_total - child_total_files,
            }

        # 최종 통계 계산
        ha = folder_dict["hand_analysis"]
        total_matched = ha["files_matched"]
        total_files = ha["total_files"]

        # 매칭 비율 계산 (전체 파일 대비 매칭된 파일)
        ha["match_rate"] = round((total_matched / total_files * 100), 1) if total_files > 0 else 0.0

        # 가중 평균 진행률 재계산 (자식 폴더 포함)
        if total_matched > 0:
            ha["avg_progress"] = round(progress_sum / total_matched, 1)

        # max_timecode 포맷
        ha["max_timecode_formatted"] = format_duration(ha["max_timecode_sec"])

        # 매칭된 파일이 없으면 null 반환 (기존 동작 유지 - 선택적)
        # if ha["files_matched"] == 0 and ha["total_files"] == 0:
        #     folder_dict["hand_analysis"] = None

        # === 파일 목록 ===
        if include_files:
            folder_dict["files"] = files_progress
        else:
            folder_dict["files"] = None

        return folder_dict

    async def _get_files_with_matching(
        self,
        db: AsyncSession,
        folder_path: str,
        hand_data: Dict[str, Dict],
        extensions: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """폴더 내 파일들과 Hand Analysis 매칭"""
        query = select(FileStats).where(FileStats.folder_path == folder_path)

        # 확장자 필터 적용
        if extensions:
            query = query.where(FileStats.extension.in_(extensions))

        file_result = await db.execute(
            query.order_by(FileStats.name).limit(200)
        )
        files = file_result.scalars().all()

        result = []
        for file in files:
            matched_title, hand_info = self._match_file_to_hand(file.name, hand_data)

            file_dict = {
                "id": file.id,
                "name": file.name,
                "path": file.path,
                "size": file.size,
                "size_formatted": format_size(file.size),
                "duration": file.duration or 0,
                "duration_formatted": format_duration(file.duration or 0),
                "extension": file.extension,
                "matched_title": matched_title,
                "hand_count": hand_info.get('hand_count', 0),
                "max_timecode_sec": hand_info.get('max_timecode_sec', 0),
                "max_timecode_formatted": hand_info.get('max_timecode_formatted', '00:00:00'),
            }

            # 진행률 계산
            if matched_title and file.duration and file.duration > 0:
                progress = (hand_info.get('max_timecode_sec', 0) / file.duration) * 100
                file_dict["progress_percent"] = min(progress, 100)
                file_dict["is_complete"] = progress >= 90
            else:
                file_dict["progress_percent"] = 0
                file_dict["is_complete"] = False

            # metadata_progress 포맷 (프론트엔드 호환)
            if matched_title:
                file_dict["metadata_progress"] = {
                    "hand_count": file_dict["hand_count"],
                    "max_timecode_sec": file_dict["max_timecode_sec"],
                    "max_timecode_formatted": file_dict["max_timecode_formatted"],
                    "progress_percent": file_dict["progress_percent"],
                    "is_complete": file_dict["is_complete"],
                }
            else:
                file_dict["metadata_progress"] = None

            result.append(file_dict)

        return result

    async def get_folder_detail(
        self,
        db: AsyncSession,
        folder_path: str,
        include_files: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """특정 폴더의 상세 정보"""
        folder_result = await db.execute(
            select(FolderStats).where(FolderStats.path == folder_path)
        )
        folder = folder_result.scalar_one_or_none()

        if not folder:
            return None

        work_statuses = await self._load_work_statuses(db)
        hand_data = await self._load_hand_analysis_data(db)

        folder_dict = {
            "id": folder.id,
            "name": folder.name,
            "path": folder.path,
            "size": folder.total_size,
            "size_formatted": format_size(folder.total_size),
            "file_count": folder.file_count,
            "folder_count": folder.folder_count,
            "duration": folder.total_duration,
            "duration_formatted": format_duration(folder.total_duration),
            "depth": folder.depth,
        }

        # Work Status (여러 개 가능)
        work_statuses_matched = self._match_work_statuses(folder.name, folder.path, work_statuses)
        folder_dict["work_statuses"] = work_statuses_matched
        folder_dict["work_status"] = work_statuses_matched[0] if work_statuses_matched else None

        # work_summary 계산
        if work_statuses_matched:
            total_done = sum(ws.get("excel_done", 0) for ws in work_statuses_matched)
            sheets_total = sum(ws.get("total_videos", 0) for ws in work_statuses_matched)
            combined_progress = (total_done / folder.file_count * 100) if folder.file_count > 0 else 0
            if combined_progress >= 90:
                combined_progress = 100.0

            # actual_progress 계산
            actual_progress = (total_done / sheets_total * 100) if sheets_total > 0 else 0
            if actual_progress >= 90:
                actual_progress = 100.0

            # 데이터 불일치 감지
            data_mismatch = abs(folder.file_count - sheets_total) > max(folder.file_count, sheets_total) * 0.1

            folder_dict["work_summary"] = {
                "task_count": len(work_statuses_matched),
                "total_files": folder.file_count,
                "total_done": total_done,
                "combined_progress": round(combined_progress, 1),
                "sheets_total_videos": sheets_total,
                "sheets_excel_done": total_done,
                "actual_progress": round(actual_progress, 1),
                "data_source_mismatch": data_mismatch,
                "mismatch_count": sheets_total - folder.file_count,
            }
        else:
            folder_dict["work_summary"] = None

        # 파일 매칭
        if include_files:
            files_progress = await self._get_files_with_matching(db, folder.path, hand_data)
            folder_dict["files"] = files_progress

            files_with_hands = sum(1 for f in files_progress if f['matched_title'])
            total_hands = sum(f.get('hand_count', 0) for f in files_progress)
            completed_files = sum(1 for f in files_progress if f.get('is_complete', False))
            progress_values = [f['progress_percent'] for f in files_progress if f.get('matched_title')]
            avg_progress = sum(progress_values) / len(progress_values) if progress_values else 0

            if files_with_hands > 0:
                max_timecode = max((f.get('max_timecode_sec', 0) for f in files_progress), default=0)
                folder_dict["hand_analysis"] = {
                    "files_matched": files_with_hands,
                    "hand_count": total_hands,
                    "max_timecode_sec": max_timecode,
                    "max_timecode_formatted": format_duration(max_timecode),
                    "avg_progress": round(avg_progress, 1),
                    "completed_files": completed_files,
                }
            else:
                folder_dict["hand_analysis"] = None
        else:
            folder_dict["files"] = None
            folder_dict["hand_analysis"] = None

        folder_dict["children"] = []

        return folder_dict

    async def get_file_progress_detail(
        self,
        db: AsyncSession,
        file_path: str,
    ) -> Optional[Dict[str, Any]]:
        """특정 파일의 상세 진행률"""
        file_result = await db.execute(
            select(FileStats).where(FileStats.path == file_path)
        )
        file = file_result.scalar_one_or_none()

        if not file:
            return None

        hand_data = await self._load_hand_analysis_data(db)
        matched_title, hand_info = self._match_file_to_hand(file.name, hand_data)

        hands = []
        if matched_title:
            hand_result = await db.execute(
                select(HandAnalysis)
                .where(HandAnalysis.file_name == matched_title)
                .order_by(HandAnalysis.timecode_out_sec)
            )
            hands = [
                {
                    "id": h.id,
                    "timecode_in": h.timecode_in,
                    "timecode_out": h.timecode_out,
                    "timecode_in_sec": h.timecode_in_sec,
                    "timecode_out_sec": h.timecode_out_sec,
                    "hand_grade": h.hand_grade,
                    "winner": h.winner,
                    "hands": h.hands,
                }
                for h in hand_result.scalars().all()
            ]

        progress_percent = 0
        if matched_title and file.duration and file.duration > 0:
            progress_percent = min(
                (hand_info.get('max_timecode_sec', 0) / file.duration) * 100,
                100
            )

        return {
            "file": {
                "id": file.id,
                "name": file.name,
                "path": file.path,
                "duration": file.duration or 0,
                "duration_formatted": format_duration(file.duration or 0),
            },
            "matched_title": matched_title,
            "hands": hands,
            "summary": {
                "hand_count": len(hands),
                "max_timecode_sec": hand_info.get('max_timecode_sec', 0),
                "max_timecode_formatted": hand_info.get('max_timecode_formatted', '00:00:00'),
                "progress_percent": progress_percent,
                "is_complete": progress_percent >= 90,
            }
        }


# 싱글톤 인스턴스
progress_service = ProgressService()
