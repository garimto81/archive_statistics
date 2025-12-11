"""
Progress Service - 통합 진행률 계산

핵심 원칙:
1. archive db (work_status): 폴더-카테고리 매칭 유지
2. metadata db (hand_analysis): 파일 기반 매칭 → 폴더로 집계
3. 하이어라키: 모든 폴더 + 파일 출력
4. 진행률 바: 최상위부터 모든 레벨에서 표시

=== BLOCK INDEX ===
| Block ID                | Lines     | Description              |
|-------------------------|-----------|--------------------------|
| progress.utils          | 25-55     | 정규화/유사도 헬퍼 함수  |
| progress.data_loader    | 105-160   | DB 데이터 로드           |
| progress.matcher        | 162-285   | 폴더-카테고리 매칭       |
| progress.file_matcher   | 287-323   | 파일-핸드 매칭           |
| progress.aggregator     | 325-642   | 하이어라키 합산/코덱집계 |
| progress.file_query     | 644-708   | 파일 목록 조회           |
| progress.folder_detail  | 710-854   | 폴더 상세 조회           |
| progress.file_detail    | 856-918   | 파일 상세 조회           |
===================
"""
import re
import logging
from typing import Optional, List, Dict, Any, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.file_stats import FolderStats, FileStats
from app.models.hand_analysis import HandAnalysis
from app.models.work_status import WorkStatus
# 중복 제거: format_size, format_duration을 공통 utils에서 import
from app.services.utils import format_size, format_duration

logger = logging.getLogger(__name__)


# === BLOCK: progress.utils ===
# Description: 문자열 정규화 및 유사도 계산 헬퍼 함수
# Dependencies: None
# AI Context: 매칭 로직 디버깅 시 이 블록만 읽으면 됨

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

# === END BLOCK: progress.utils ===


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
        include_codecs: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        폴더 트리와 진행률 정보를 함께 반환

        Args:
            db: 데이터베이스 세션
            path: 시작 경로 (None이면 루트)
            depth: 탐색 깊이
            include_files: 파일 목록 포함 여부
            extensions: 확장자 필터 목록 (예: ['.mp4', '.mkv'])
            include_codecs: 코덱 정보 포함 여부
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

        # ⚠️ Lazy Loading 시 Cascading Match 방지 (Issue #24 확장)
        # path가 있으면 → 상위 폴더들에서 이미 매칭된 work_status_ids 계산
        ancestor_work_status_ids: Set[int] = set()
        if path:
            ancestor_work_status_ids = await self._get_ancestor_work_status_ids(
                db, path, work_statuses
            )
            if ancestor_work_status_ids:
                logger.info(f"[Lazy Load] path={path}, ancestor_ids={ancestor_work_status_ids}")

        tree = []
        # ⚠️ 루트 레벨 폴더들 간에도 형제 중복 매칭 방지
        # ancestor_ids와 sibling_ids 모두 포함
        root_sibling_used_ids: Set[int] = ancestor_work_status_ids.copy()

        for folder in folders:
            folder_data, folder_used_ids = await self._build_folder_progress(
                db, folder, work_statuses, hand_data, depth, 0, include_files, extensions, include_codecs,
                parent_work_status_ids=root_sibling_used_ids.copy()  # 조상+이전형제 ID 전달
            )
            tree.append(folder_data)
            # 이 폴더와 하위에서 사용된 ID를 다음 형제에게 전파
            root_sibling_used_ids.update(folder_used_ids)

        return tree

    # === BLOCK: progress.data_loader ===
    # Description: Work Status 및 Hand Analysis 데이터 로드
    # Dependencies: WorkStatus, HandAnalysis models
    # AI Context: 데이터 로딩 문제 디버깅 시

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

    # === END BLOCK: progress.data_loader ===

    # === BLOCK: progress.ancestor_matcher ===
    # Description: 상위 폴더들의 매칭된 work_status_ids 계산 (Cascading 방지용)
    # Dependencies: _match_work_statuses
    # AI Context: /progress/folder API에서 Cascading 방지 시 사용

    async def _get_ancestor_work_status_ids(
        self,
        db: AsyncSession,
        folder_path: str,
        work_statuses: Dict[str, Dict]
    ) -> Set[int]:
        """상위 폴더들에서 매칭된 work_status_ids를 계산

        Args:
            folder_path: 현재 폴더 경로
            work_statuses: 전체 work_status 데이터

        Returns:
            상위 폴더들에서 매칭된 work_status_id 집합
        """
        ancestor_ids: Set[int] = set()

        # 경로를 분해하여 상위 폴더들 추출 (현재 폴더 포함!)
        # 예: /mnt/nas/WSOP/Bracelet/Europe → [/mnt/nas, /mnt/nas/WSOP, /mnt/nas/WSOP/Bracelet, /mnt/nas/WSOP/Bracelet/Europe]
        # ⚠️ Lazy Loading 시 path는 부모 폴더이므로, 이 폴더 자체의 매칭도 포함해야 함
        path_parts = folder_path.split('/')
        current_path = ""

        for i, part in enumerate(path_parts):  # 모든 경로 포함 (현재 폴더까지)
            if not part:
                continue
            current_path = current_path + "/" + part if current_path else "/" + part

            # 상위 폴더 조회
            ancestor_result = await db.execute(
                select(FolderStats).where(FolderStats.path == current_path)
            )
            ancestor = ancestor_result.scalar_one_or_none()

            if ancestor:
                # 상위 폴더에서 매칭되는 work_status 찾기
                # ancestor_ids에 있는 것은 제외 (더 상위에서 이미 매칭됨)
                available_ws = {
                    cat: ws for cat, ws in work_statuses.items()
                    if ws.get("id") not in ancestor_ids
                }
                matched = self._match_work_statuses(ancestor.name, ancestor.path, available_ws)
                if matched:
                    # 최상위 매칭만 사용 (Single Match Policy)
                    ancestor_ids.add(matched[0].get("id"))

        return ancestor_ids

    # === END BLOCK: progress.ancestor_matcher ===

    # === BLOCK: progress.matcher ===
    # Description: 폴더명-카테고리 매칭 로직 (핵심!)
    # Dependencies: WorkStatus data
    # AI Context: 매칭 버그 수정 시 이 블록만 읽으면 됨
    # Known Issues: #3 해결됨 (folder_prefix 전략 추가)

    def _normalize_folder_name(self, name: str) -> str:
        """폴더명 정규화: 하이픈/밑줄을 공백으로 변환"""
        # 하이픈, 밑줄 → 공백으로 변환
        normalized = re.sub(r'[-_]', ' ', name.lower())
        # 연속 공백 제거
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

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
        3. 폴더명이 카테고리로 시작 (예: "GOG 최종" → "GOG")
        4. 연도+키워드 조합 매칭 (예: "2025 WSOP-LAS VEGAS" → "2025 WSOP")
        5. 폴더명이 카테고리에 독립 단어로 포함 (공백으로 분리된 단어)
        6. 연도 매칭

        주의: 부분 문자열 매칭(substring)은 의도하지 않은 매칭을 유발하므로 제외
        - 예: "WSOP" in "WSOP Europe" → 허용 (독립 단어)
        - 예: "WSOP" in "WSOPE" → 제외 (부분 문자열)

        Returns:
            매칭된 work_status 목록 (progress_percent 내림차순 정렬)
        """
        matched = []
        folder_lower = folder_name.lower()
        # 하이픈/밑줄을 공백으로 변환한 정규화 버전
        folder_normalized = self._normalize_folder_name(folder_name)
        folder_words = set(folder_normalized.split())

        for category, ws in work_statuses.items():
            category_lower = category.lower()
            category_normalized = self._normalize_folder_name(category)
            category_words = set(category_normalized.split())

            # 1. 정확히 일치
            if folder_lower == category_lower:
                matched.append((ws, 1.0, 'exact'))
                continue

            # 1.5. 정규화 후 정확히 일치 (하이픈/밑줄 차이만 있는 경우)
            if folder_normalized == category_normalized:
                matched.append((ws, 0.98, 'exact_normalized'))
                continue

            # 2. 카테고리가 폴더명으로 시작 (예: "PAD S12" → "PAD")
            # 폴더명 뒤에 공백이 와야 함 (WSOPE 폴더가 WSOP로 매칭되는 것 방지)
            # ⚠️ 핵심 수정 (Issue #24 재발 방지):
            #   - 단일 단어 상위 폴더(WSOP)가 다단어 하위 카테고리(WSOP LA)와 매칭되면 안됨
            #   - 이 전략은 "PAD" 폴더 → "PAD S12" 같은 시리즈 매칭용
            #   - 단, 폴더가 1단어이고 카테고리가 2단어 이상이면 스킵 (상위 폴더 보호)
            if category_lower.startswith(folder_lower + ' '):
                # 단일 단어 폴더는 다단어 카테고리와 prefix 매칭 금지
                # 예: "WSOP" (1단어) → "WSOP LA" (2단어) 매칭 금지
                if len(folder_words) == 1 and len(category_words) >= 2:
                    continue  # 매칭 스킵
                matched.append((ws, 0.9, 'prefix'))
                continue

            # 2.5. 폴더명이 카테고리로 시작 (예: "GOG 최종" → "GOG")
            # 카테고리 뒤에 공백 또는 언더스코어가 와야 함
            if folder_lower.startswith(category_lower + ' ') or folder_lower.startswith(category_lower + '_'):
                matched.append((ws, 0.85, 'folder_prefix'))
                continue

            # 3. 연도+키워드 조합 매칭 (핵심 개선!)
            # 예: 폴더 "2025 WSOP-LAS VEGAS" → 카테고리 "2025 WSOP"
            # 카테고리의 모든 단어가 폴더에 포함되어야 함
            if len(category_words) >= 2 and category_words.issubset(folder_words):
                # 카테고리 단어 수가 많을수록 더 정확한 매칭
                score = 0.88 + (len(category_words) * 0.01)  # 2단어: 0.90, 3단어: 0.91 등
                matched.append((ws, min(score, 0.94), 'subset'))
                continue

            # 4. 폴더명이 카테고리에 독립 단어로 포함 (공백으로 분리된 단어)
            # 예: "2023 WSOP Paradise"에서 "WSOP"는 독립 단어로 매칭됨
            # ⚠️ 핵심 수정 (Issue #24 재발 방지):
            #   - 단일 단어 폴더(WSOP)가 다단어 카테고리(WSOP LA)와 매칭되면 안됨
            #   - 폴더 단어 수 <= 카테고리 단어 수일 때만 허용
            #   - 예: "WSOP" 폴더 → "WSOP LA" 매칭 금지 (1단어 < 2단어)
            #   - 예: "WSOP" 폴더 → "WSOP" 카테고리는 exact match로 처리됨
            if folder_lower in category_words and len(folder_words) >= len(category_words):
                matched.append((ws, 0.8, 'word'))
                continue

            # 5. 연도 매칭: 폴더명이 4자리 숫자(연도)인 경우 카테고리에 해당 연도가 있으면 매칭
            if folder_lower.isdigit() and len(folder_lower) == 4:
                # 연도도 독립 단어로만 매칭 (1973이 19730에 매칭되는 것 방지)
                if folder_lower in category_words:
                    matched.append((ws, 0.7, 'year'))

            # 부분 문자열 매칭(substring)은 제외 - 의도하지 않은 매칭 방지
            # 예: "WSOP" in "WSOPE" → 제외

        # 정렬: 우선순위 점수 > progress_percent
        matched.sort(key=lambda x: (x[1], x[0].get('progress_percent', 0)), reverse=True)

        # ⚠️ 핵심 수정: 최고 점수 매칭 하나만 반환 (중복 합산 방지)
        # 이전: 비슷한 점수(top_score - 0.1) 모두 반환 → excel_done 중복 합산 문제
        # 현재: 가장 정확한 매칭 하나만 선택
        # 중기 해결책: folder_work_mapping 테이블로 명시적 매핑 (Issue 생성 필요)
        if not matched:
            return []

        # 최고 점수 매칭만 반환 (1개)
        return [matched[0][0]]

    # === END BLOCK: progress.matcher ===

    # === BLOCK: progress.file_matcher ===
    # Description: NAS 파일명과 Hand Analysis 매칭
    # Dependencies: hand_data, normalize_name, calculate_similarity
    # AI Context: 파일 진행률 표시 문제 시

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

    # === END BLOCK: progress.file_matcher ===

    # === BLOCK: progress.aggregator ===
    # Description: 폴더 트리 구축 및 하이어라키 합산 (가장 복잡!)
    # Dependencies: progress.matcher, progress.file_matcher, progress.data_loader
    # AI Context: 진행률 계산/합산 문제, 코덱 집계 문제 시
    # Warning: 300줄 이상의 대형 함수 - 분할 고려 필요

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
        include_codecs: bool = False,
        parent_work_status_ids: Optional[Set[int]] = None,  # 상위 폴더에서 매칭된 work_status ID들
    ) -> Tuple[Dict[str, Any], Set[int]]:
        """폴더 데이터 구축 (archive db + metadata db + codecs 통합)

        Args:
            parent_work_status_ids: 상위 폴더에서 이미 매칭된 work_status ID 집합.
                                    Cascading Match 방지: 동일 work_status가 부모-자식에 중복 매칭되지 않도록 함.

        Returns:
            Tuple[폴더 데이터 dict, 이 폴더와 하위 폴더에서 사용된 work_status_id 집합]
        """
        # 초기화: parent_work_status_ids가 None이면 빈 Set 생성
        if parent_work_status_ids is None:
            parent_work_status_ids = set()

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
        # ⚠️ Cascading Match 방지: 상위에서 이미 매칭된 work_status는 제외
        work_statuses_matched = []
        matching_method = "none"
        current_work_status_id = None  # 현재 폴더에서 매칭된 work_status ID (자식에게 전파용)

        # 1. FK 기반 조회 (folder.work_status_id가 있으면)
        if hasattr(folder, 'work_status_id') and folder.work_status_id:
            # FK가 있으면 무조건 사용 (parent_work_status_ids에 있어도 FK 우선)
            for category, ws in work_statuses.items():
                if ws.get("id") == folder.work_status_id:
                    work_statuses_matched = [ws]
                    matching_method = "fk"
                    current_work_status_id = folder.work_status_id
                    break

        # 2. Fuzzy matching fallback (FK가 없는 경우)
        # ⚠️ 핵심: 상위에서 이미 매칭된 work_status_id는 제외
        if not work_statuses_matched:
            # 상위에서 사용되지 않은 work_statuses만 필터링
            available_work_statuses = {
                cat: ws for cat, ws in work_statuses.items()
                if ws.get("id") not in parent_work_status_ids
            }

            if available_work_statuses:
                work_statuses_matched = self._match_work_statuses(folder.name, folder.path, available_work_statuses)
                if work_statuses_matched:
                    matching_method = "fuzzy"
                    current_work_status_id = work_statuses_matched[0].get("id")
            else:
                # 모든 work_status가 상위에서 사용됨 → 매칭 스킵
                if current_depth <= 2:
                    logger.info(f"[DEBUG] {folder.name}: 상위 폴더에서 모든 work_status 사용됨 → fuzzy matching 스킵")

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

            # ⚠️ 검증: total_done > total_files 이면 잘못된 매칭 (무효화)
            # 예: 파일 1개 폴더가 done=27인 작업에 매칭된 경우
            if total_done > folder.file_count:
                logger.warning(
                    f"[MISMATCH] {folder.name}: total_done({total_done}) > file_count({folder.file_count}) - 매칭 무효화"
                )
                work_statuses_matched = []
                folder_dict["work_statuses"] = []
                folder_dict["matching_method"] = "invalidated"
                folder_dict["work_summary"] = None  # 무효화된 매칭은 work_summary 없음
            else:
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

        # === 코덱 정보 조회 (include_codecs=true일 때만) ===
        video_codecs: Dict[str, int] = {}
        audio_codecs: Dict[str, int] = {}
        files_with_codec = 0

        if include_codecs:
            # 현재 폴더의 직접 파일들의 코덱 정보 조회
            codec_query = select(
                FileStats.video_codec,
                FileStats.audio_codec,
                func.count(FileStats.id).label("count"),
            ).where(
                FileStats.folder_path == folder.path
            ).group_by(
                FileStats.video_codec,
                FileStats.audio_codec,
            )
            codec_result = await db.execute(codec_query)
            codec_rows = codec_result.fetchall()

            for row in codec_rows:
                if row.video_codec:
                    video_codecs[row.video_codec] = video_codecs.get(row.video_codec, 0) + row.count
                    files_with_codec += row.count
                if row.audio_codec:
                    audio_codecs[row.audio_codec] = audio_codecs.get(row.audio_codec, 0) + row.count

        # === 자식 폴더 (재귀) ===
        children = []
        # ⚠️ 형제+사촌 폴더 간 중복 매칭 방지 (Issue #24 확장)
        # 형제 폴더를 순회하면서 이미 매칭된 work_status_id를 누적
        # 먼저 매칭된 폴더가 해당 카테고리를 "점유"
        # 참고: if 블록 밖에서 초기화해야 함수 끝에서 참조 가능
        sibling_used_ids: Set[int] = set()

        if current_depth < max_depth:
            child_result = await db.execute(
                select(FolderStats)
                .where(FolderStats.parent_path == folder.path)
                .order_by(FolderStats.total_size.desc())
            )
            child_folders = child_result.scalars().all()

            for child in child_folders:
                # ⚠️ Cascading Match 방지:
                # 1. 부모에서 매칭된 ID (parent_work_status_ids)
                # 2. 현재 폴더에서 매칭된 ID (current_work_status_id)
                # 3. 형제+사촌에서 이미 매칭된 ID (sibling_used_ids) ← 확장!
                child_parent_ids = parent_work_status_ids.copy()
                if current_work_status_id:
                    child_parent_ids.add(current_work_status_id)
                # 형제+사촌에서 사용된 ID도 제외
                child_parent_ids.update(sibling_used_ids)

                child_data, child_used_ids = await self._build_folder_progress(
                    db, child, work_statuses, hand_data,
                    max_depth, current_depth + 1, include_files, extensions, include_codecs,
                    parent_work_status_ids=child_parent_ids  # 상위+형제 매칭 ID 전파
                )
                children.append(child_data)

                # ⚠️ 핵심 수정: 이 자식과 그 하위 폴더에서 사용된 모든 ID를 형제에게 전파
                # 이렇게 하면 사촌 폴더(다른 부모의 자식)도 중복 사용 방지됨
                sibling_used_ids.update(child_used_ids)

                # 참고: work_summary 자식 합산 제거됨 (Issue #24)
                # 각 폴더는 자신의 직접 매칭만 표시 (Cascading Match 방지)

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

                # 자식 폴더의 codec_summary 합산 (include_codecs=true일 때만)
                if include_codecs and child_data.get("codec_summary"):
                    child_codec = child_data["codec_summary"]
                    for codec, count in (child_codec.get("video_codecs") or {}).items():
                        video_codecs[codec] = video_codecs.get(codec, 0) + count
                    for codec, count in (child_codec.get("audio_codecs") or {}).items():
                        audio_codecs[codec] = audio_codecs.get(codec, 0) + count
                    files_with_codec += child_codec.get("files_with_codec", 0)

        folder_dict["children"] = children

        # work_summary 로직 (Cascading Match Prevention)
        # ⚠️ 핵심 수정 (Issue #24): 직접 매칭이 있는 폴더만 work_summary 표시
        # 자식 합산 로직 제거 - 중복 집계 원인 (WSOP Bracelet Event 버그)
        #
        # 이전 동작 (버그):
        #   - 직접 매칭 없는 부모가 자식의 total_done을 합산하여 중복 표시
        #   - 예: WSOP Bracelet Event (45/744) = WSOP-EUROPE(27) + LAS VEGAS(9) + PARADISE(9)
        #
        # 수정 후:
        #   - 직접 매칭이 있는 폴더만 work_summary 표시
        #   - 직접 매칭 없는 폴더는 work_summary = None (진행률 바 없음)
        #   - 자식 폴더들은 각자 자신의 work_summary만 표시
        if folder_dict["work_summary"]:
            # 직접 매칭이 있는 경우만 work_summary 유지
            # total_files는 NAS 실제 파일 수 (folder.file_count)
            ws = folder_dict["work_summary"]
            ws["total_files"] = folder.file_count

            # combined_progress 재계산 (NAS file_count 기준)
            if ws["total_files"] > 0:
                combined_progress = min(ws["total_done"] / ws["total_files"] * 100, 100.0)
                if combined_progress >= 90:
                    combined_progress = 100.0
                ws["combined_progress"] = round(combined_progress, 1)

            # actual_progress 계산 (시트 기준 - 실제 진행률)
            if ws["sheets_total_videos"] > 0:
                actual_progress = ws["total_done"] / ws["sheets_total_videos"] * 100
                if actual_progress >= 90:
                    actual_progress = 100.0
                ws["actual_progress"] = round(actual_progress, 1)
            else:
                ws["actual_progress"] = 0.0

            # 데이터 불일치 감지
            ws["data_source_mismatch"] = abs(ws["total_files"] - ws["sheets_total_videos"]) > max(ws["total_files"], ws["sheets_total_videos"], 1) * 0.1
            ws["mismatch_count"] = ws["sheets_total_videos"] - ws["total_files"]
        # else: 직접 매칭 없음 → work_summary = None 유지 (자식 합산 제거)

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

        # === 코덱 요약 생성 (include_codecs=true일 때만) ===
        if include_codecs:
            if video_codecs or audio_codecs:
                top_video = max(video_codecs.items(), key=lambda x: x[1])[0] if video_codecs else None
                top_audio = max(audio_codecs.items(), key=lambda x: x[1])[0] if audio_codecs else None
                folder_dict["codec_summary"] = {
                    "total_files": folder.file_count,
                    "files_with_codec": files_with_codec,
                    "video_codecs": video_codecs,
                    "audio_codecs": audio_codecs,
                    "top_video_codec": top_video,
                    "top_audio_codec": top_audio,
                }
            else:
                folder_dict["codec_summary"] = None
        else:
            folder_dict["codec_summary"] = None

        # === 파일 목록 ===
        if include_files:
            # 파일에 코덱 정보 추가 (include_codecs=true일 때)
            if include_codecs:
                for f in files_progress:
                    # 파일의 코덱 정보는 이미 _get_files_with_matching에서 가져옴
                    pass  # video_codec, audio_codec은 별도로 조회 필요
            folder_dict["files"] = files_progress
        else:
            folder_dict["files"] = None

        # ⚠️ 이 폴더와 모든 하위 폴더에서 사용된 work_status_id 수집
        # 호출자에게 반환하여 형제/사촌 폴더에서 중복 사용 방지
        all_used_ids: Set[int] = set()
        if current_work_status_id:
            all_used_ids.add(current_work_status_id)
        # sibling_used_ids는 자식들과 그 하위 폴더에서 사용한 모든 ID
        all_used_ids.update(sibling_used_ids)

        return folder_dict, all_used_ids

    # === END BLOCK: progress.aggregator ===

    # === BLOCK: progress.file_query ===
    # Description: 폴더 내 파일 목록 조회 및 매칭
    # Dependencies: progress.file_matcher
    # AI Context: 파일 목록 표시 문제 시

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
                # 코덱 정보 (Codec Explorer용)
                "video_codec": file.video_codec,
                "audio_codec": file.audio_codec,
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

    # === END BLOCK: progress.file_query ===

    # === BLOCK: progress.folder_detail ===
    # Description: 특정 폴더 상세 정보 조회 (폴더 클릭 시)
    # Dependencies: progress.matcher, progress.file_query
    # AI Context: 상세 패널 표시 문제 시

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

        # ⚠️ Cascading Match 방지: 상위 폴더에서 매칭된 work_status_ids 계산
        ancestor_work_status_ids = await self._get_ancestor_work_status_ids(db, folder_path, work_statuses)

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
        # ⚠️ Cascading 방지: 상위에서 매칭된 work_status는 제외
        available_work_statuses = {
            cat: ws for cat, ws in work_statuses.items()
            if ws.get("id") not in ancestor_work_status_ids
        }
        work_statuses_matched = self._match_work_statuses(folder.name, folder.path, available_work_statuses)
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

        # === 자식 폴더 조회 ===
        child_result = await db.execute(
            select(FolderStats)
            .where(FolderStats.parent_path == folder_path)
            .order_by(FolderStats.total_size.desc())
        )
        child_folders = child_result.scalars().all()

        # ⚠️ Cascading Match 방지: 자식 폴더 매칭 시 조상 + 현재 폴더의 매칭된 ID 제외
        parent_work_status_ids = ancestor_work_status_ids.copy()
        if work_statuses_matched:
            # 현재 폴더에서 매칭된 work_status의 id들을 추가
            for matched_ws in work_statuses_matched:
                if matched_ws.get("id"):
                    parent_work_status_ids.add(matched_ws["id"])

        # 자식 폴더용 available_work_statuses (조상+현재 제외)
        child_available_work_statuses = {
            cat: ws for cat, ws in work_statuses.items()
            if ws.get("id") not in parent_work_status_ids
        }

        children = []
        for child in child_folders:
            # 자식 폴더 기본 정보 (재귀 호출 없이 1단계만)
            # ⚠️ Cascading 방지: 필터링된 work_statuses 사용
            child_work_statuses = self._match_work_statuses(child.name, child.path, child_available_work_statuses)

            child_summary = None
            if child_work_statuses:
                child_total_done = sum(ws.get("excel_done", 0) for ws in child_work_statuses)
                child_sheets_total = sum(ws.get("total_videos", 0) for ws in child_work_statuses)
                child_progress = (child_total_done / child.file_count * 100) if child.file_count > 0 else 0
                if child_progress >= 90:
                    child_progress = 100.0

                child_summary = {
                    "task_count": len(child_work_statuses),
                    "total_files": child.file_count,
                    "total_done": child_total_done,
                    "combined_progress": round(child_progress, 1),
                    "sheets_total_videos": child_sheets_total,
                    "sheets_excel_done": child_total_done,
                }

            children.append({
                "id": child.id,
                "name": child.name,
                "path": child.path,
                "size": child.total_size,
                "size_formatted": format_size(child.total_size),
                "file_count": child.file_count,
                "folder_count": child.folder_count,
                "duration": child.total_duration,
                "duration_formatted": format_duration(child.total_duration),
                "depth": child.depth,
                "work_summary": child_summary,
                "work_statuses": child_work_statuses,
                "work_status": child_work_statuses[0] if child_work_statuses else None,
                "hand_analysis": None,  # 상세 조회 시만 계산
                "children": [],  # 손자 폴더는 추가 조회 필요
                "files": None,
            })

        folder_dict["children"] = children

        return folder_dict

    # === END BLOCK: progress.folder_detail ===

    # === BLOCK: progress.file_detail ===
    # Description: 특정 파일의 상세 진행률 조회
    # Dependencies: progress.file_matcher, HandAnalysis model
    # AI Context: 개별 파일 진행률 표시 문제 시

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

    # === END BLOCK: progress.file_detail ===


# 싱글톤 인스턴스
progress_service = ProgressService()
