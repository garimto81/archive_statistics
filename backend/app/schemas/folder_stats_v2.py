"""
Folder Stats V2 Schemas

Issue #49: NAS 폴더 통계 계산 로직 리팩토링
설계 문서: docs/REFACTORING_FOLDER_STATS.md (v1.2.0)

새로운 데이터 구조:
- FileCountInfo: 파일 수 통합 정보 (stored, actual, visible, is_stale)
- SizeInfo: 용량 통합 정보
- ArchiveStats: 전체 아카이브 통계 (항상 동일한 값)
"""

from typing import Optional

from pydantic import BaseModel, Field


class FileCountInfo(BaseModel):
    """파일 수 통합 정보

    용어 정의:
    - stored: FolderStats.file_count (DB 저장값, 스캔 시점 고정)
    - actual: FileStats COUNT(*) 실시간 계산 (필터 무관)
    - visible: 필터 적용 후 표시할 파일 수
    - is_stale: 데이터 신선도 (stored != actual이면 True)
    """

    stored: int = Field(description="DB에 저장된 파일 수 (스캔 시점)")
    actual: int = Field(description="FileStats에서 실시간 계산된 파일 수")
    visible: int = Field(description="필터 적용 후 표시할 파일 수")
    is_stale: bool = Field(description="데이터 신선도 (stored != actual)")

    class Config:
        json_schema_extra = {
            "example": {
                "stored": 745,
                "actual": 755,
                "visible": 720,
                "is_stale": True,
            }
        }


class SizeInfo(BaseModel):
    """용량 통합 정보

    용어 정의:
    - stored: FolderStats.total_size (DB 저장값)
    - actual: FileStats SUM(size) 실시간 계산
    - visible: 필터 적용 후 용량
    """

    stored: int = Field(description="DB에 저장된 용량 (bytes)")
    actual: int = Field(description="FileStats에서 실시간 계산된 용량 (bytes)")
    visible: int = Field(description="필터 적용 후 용량 (bytes)")
    stored_formatted: str = Field(description="포맷된 저장 용량")
    actual_formatted: str = Field(description="포맷된 실제 용량")
    visible_formatted: str = Field(description="포맷된 표시 용량")
    is_stale: bool = Field(description="데이터 신선도")

    class Config:
        json_schema_extra = {
            "example": {
                "stored": 1099511627776,
                "actual": 1199511627776,
                "visible": 1050511627776,
                "stored_formatted": "1.00 TB",
                "actual_formatted": "1.09 TB",
                "visible_formatted": "0.95 TB",
                "is_stale": True,
            }
        }


class DurationInfo(BaseModel):
    """재생시간 통합 정보"""

    stored: float = Field(description="DB에 저장된 재생시간 (초)")
    actual: float = Field(description="FileStats에서 실시간 계산된 재생시간 (초)")
    visible: float = Field(description="필터 적용 후 재생시간 (초)")
    stored_formatted: str = Field(description="포맷된 저장 재생시간")
    actual_formatted: str = Field(description="포맷된 실제 재생시간")
    visible_formatted: str = Field(description="포맷된 표시 재생시간")


class ArchiveStats(BaseModel):
    """전체 아카이브 통계

    핵심 특징:
    - path 파라미터와 무관하게 항상 동일한 값 반환
    - Lazy Load 시에도 일관성 보장
    - 캐싱 가능 (5분 TTL)

    이전 root_stats와의 차이:
    - root_stats: path에 따라 값이 달라짐 (버그)
    - archive_stats: 항상 전체 아카이브 기준 (수정)
    """

    total_files: int = Field(description="전체 아카이브 파일 수 (항상 고정)")
    total_size: int = Field(description="전체 아카이브 용량 (bytes)")
    total_size_formatted: str = Field(description="포맷된 전체 용량")
    total_duration: float = Field(default=0, description="전체 재생시간 (초)")
    total_duration_formatted: str = Field(
        default="0:00:00", description="포맷된 전체 재생시간"
    )

    # Sheets 통계 (참조용)
    sheets_total_videos: int = Field(
        default=0, description="Google Sheets 전체 비디오 수"
    )
    sheets_total_done: int = Field(
        default=0, description="Google Sheets 완료된 비디오 수"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_files": 1912,
                "total_size": 1099511627776000,
                "total_size_formatted": "1.00 PB",
                "total_duration": 3600000,
                "total_duration_formatted": "1,000 hrs",
                "sheets_total_videos": 2000,
                "sheets_total_done": 1500,
            }
        }


class FolderRatioInfo(BaseModel):
    """폴더의 전체 대비 비율 정보"""

    file_ratio: float = Field(description="전체 대비 파일 수 비율 (%)")
    size_ratio: float = Field(description="전체 대비 용량 비율 (%)")
    duration_ratio: float = Field(default=0, description="전체 대비 재생시간 비율 (%)")


class FolderStatsV2(BaseModel):
    """폴더 통계 V2 응답

    V1과의 차이:
    - file_count → file_counts (통합 정보)
    - filtered_file_count → file_counts.visible
    - root_stats → archive_stats (일관된 값)
    """

    # 기본 정보
    id: int
    name: str
    path: str
    depth: int

    # V2 통합 정보 (권장)
    file_counts: FileCountInfo
    sizes: SizeInfo
    durations: Optional[DurationInfo] = None
    archive_stats: ArchiveStats
    ratios: FolderRatioInfo

    # V1 호환 필드 (deprecated, 마이그레이션 기간 동안 유지)
    file_count: int = Field(deprecated=True, description="Use file_counts.stored")
    filtered_file_count: int = Field(
        deprecated=True, description="Use file_counts.visible"
    )
    size: int = Field(deprecated=True, description="Use sizes.stored")
    filtered_size: int = Field(deprecated=True, description="Use sizes.visible")
    size_formatted: str = Field(
        deprecated=True, description="Use sizes.stored_formatted"
    )
    filtered_size_formatted: str = Field(
        deprecated=True, description="Use sizes.visible_formatted"
    )

    class Config:
        from_attributes = True
