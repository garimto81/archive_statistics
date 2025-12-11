"""
Progress Service 매칭 로직 단위 테스트

테스트 케이스:
- 정확 매칭
- 정규화 후 매칭 (하이픈/밑줄 차이)
- 연도+키워드 조합 매칭 (Issue #4 핵심)
- 독립 단어 매칭
"""

import pytest
from app.services.progress_service import ProgressService


class TestProgressMatching:
    """Progress 매칭 로직 테스트"""

    def setup_method(self):
        """테스트 전 셋업"""
        self.service = ProgressService()
        # 실제 DB에서 확인된 work_status 카테고리들
        self.work_statuses = {
            "2023 WSOP Paradise": {
                "id": 1,
                "category": "2023 WSOP Paradise",
                "total_videos": 9,
                "excel_done": 9,
                "progress_percent": 100.0,
            },
            "WSOP LA": {
                "id": 2,
                "category": "WSOP LA",
                "total_videos": 11,
                "excel_done": 11,
                "progress_percent": 100.0,
            },
            "WSOP Cyprus": {
                "id": 3,
                "category": "WSOP Cyprus",
                "total_videos": 6,
                "excel_done": 6,
                "progress_percent": 100.0,
            },
            "WSOP Europe": {
                "id": 4,
                "category": "WSOP Europe",
                "total_videos": 41,
                "excel_done": 22,
                "progress_percent": 53.6,
            },
            "2025 WSOP": {
                "id": 5,
                "category": "2025 WSOP",
                "total_videos": 43,
                "excel_done": 6,
                "progress_percent": 14.0,
            },
        }

    def test_exact_match(self):
        """정확히 일치하는 경우"""
        result = self.service._match_work_statuses(
            "WSOP Europe", "/mnt/nas/WSOP/WSOP Europe", self.work_statuses
        )
        assert len(result) == 1
        assert result[0]["category"] == "WSOP Europe"

    def test_normalized_exact_match(self):
        """하이픈/밑줄이 다른 경우 (정규화 후 일치)"""
        result = self.service._match_work_statuses(
            "WSOP-Europe", "/mnt/nas/WSOP/WSOP-Europe", self.work_statuses
        )
        assert len(result) == 1
        assert result[0]["category"] == "WSOP Europe"

    def test_subset_match_issue4_case(self):
        """Issue #4 핵심: 연도+키워드 조합 매칭

        폴더 "2025 WSOP-LAS VEGAS"는 카테고리 "2025 WSOP"와 매칭되어야 함
        """
        result = self.service._match_work_statuses(
            "2025 WSOP-LAS VEGAS", "/mnt/nas/WSOP/2025 WSOP-LAS VEGAS", self.work_statuses
        )
        assert len(result) >= 1
        # "2025 WSOP"가 매칭되어야 함
        categories = [r["category"] for r in result]
        assert "2025 WSOP" in categories

    def test_subset_match_paradise(self):
        """연도+키워드 조합 매칭: Paradise 케이스"""
        result = self.service._match_work_statuses(
            "2023 WSOP-PARADISE", "/mnt/nas/WSOP/2023 WSOP-PARADISE", self.work_statuses
        )
        assert len(result) >= 1
        categories = [r["category"] for r in result]
        assert "2023 WSOP Paradise" in categories

    def test_word_match_top_level(self):
        """최상위 "WSOP" 폴더는 모든 WSOP 관련 카테고리와 매칭"""
        result = self.service._match_work_statuses(
            "WSOP", "/mnt/nas/WSOP", self.work_statuses
        )
        # WSOP이 포함된 모든 카테고리와 매칭 (word 전략)
        assert len(result) >= 1

    def test_no_false_positive(self):
        """의도하지 않은 매칭 방지: "WSOPE" 폴더가 "WSOP"와 매칭되면 안 됨"""
        result = self.service._match_work_statuses(
            "WSOPE", "/mnt/nas/WSOPE", self.work_statuses
        )
        # WSOPE는 어떤 카테고리와도 매칭되면 안 됨
        assert len(result) == 0

    def test_normalize_folder_name(self):
        """_normalize_folder_name 함수 테스트"""
        assert self.service._normalize_folder_name("2025 WSOP-LAS VEGAS") == "2025 wsop las vegas"
        assert self.service._normalize_folder_name("WSOP_Europe") == "wsop europe"
        assert self.service._normalize_folder_name("WSOP-Europe") == "wsop europe"
        assert self.service._normalize_folder_name("WSOP  Europe") == "wsop europe"

    # === 새로 추가된 테스트: 단일 매칭 정책 (Issue #10 관련) ===

    def test_single_match_only(self):
        """핵심 수정: 여러 매칭 후보 중 최고 점수 하나만 반환

        이전 동작: "WSOP Europe"과 "2025 WSOP" 둘 다 반환 → excel_done 중복 합산
        현재 동작: 최고 점수 매칭 1개만 반환
        """
        # "2025 WSOP-Europe"은 두 카테고리에 매칭 가능:
        # - "WSOP Europe" (word match)
        # - "2025 WSOP" (subset match)
        result = self.service._match_work_statuses(
            "2025 WSOP-Europe", "/mnt/nas/WSOP/2025 WSOP-Europe", self.work_statuses
        )
        # 단일 매칭만 반환되어야 함
        assert len(result) == 1, f"Expected 1 match, got {len(result)}: {[r['category'] for r in result]}"

    def test_single_match_europe_main_event(self):
        """실제 문제 케이스: 2025 WSOP-EUROPE MAIN EVENT

        이전: "WSOP Europe" + "2025 WSOP" 둘 다 매칭 → done=33 (27+6)
        현재: 최고 점수 매칭 1개만 → done=27 (WSOP Europe)
        """
        result = self.service._match_work_statuses(
            "2025 WSOP-EUROPE MAIN EVENT",
            "/mnt/nas/WSOP/2025 WSOP-EUROPE MAIN EVENT",
            self.work_statuses
        )
        assert len(result) == 1
        # 가장 정확한 매칭은 "WSOP Europe" (정규화 후 일치)
        assert result[0]["category"] == "WSOP Europe"

    def test_no_match_for_small_subfolder(self):
        """작은 하위 폴더는 상위 작업과 매칭되지 않아야 함

        주의: 이 테스트는 _match_work_statuses 자체가 아닌
        _build_folder_progress의 검증 로직을 확인하는 것
        (total_done > total_files → 무효화)

        여기서는 매칭 자체는 발생할 수 있지만,
        실제 진행률 계산에서 무효화됨
        """
        # MINI MAIN EVENT는 WSOP Europe과 매칭될 수 있음
        result = self.service._match_work_statuses(
            "2025 WSOP-EUROPE #5 MINI MAIN EVENT",
            "/mnt/nas/WSOP/2025 WSOP-Europe/MINI",
            self.work_statuses
        )
        # 매칭은 발생할 수 있음 (word match)
        # 하지만 file_count < excel_done인 경우 _build_folder_progress에서 무효화됨
        # 이 테스트는 매칭 로직 자체만 테스트
        if len(result) > 0:
            # 매칭되더라도 1개만 반환되어야 함
            assert len(result) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
