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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
