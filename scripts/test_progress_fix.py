"""
Phase 1 수정 사항 검증: work_summary에 actual_progress 추가
"""
import sys
import asyncio
import os
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# 데이터베이스 경로 환경변수 설정
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///D:/AI/claude01/archive-statistics/data/archive_stats.db"

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_maker
from app.services.progress_service import progress_service


async def test_wsop_folder():
    """WSOP 폴더의 work_summary 검증"""
    print("=" * 80)
    print("  WSOP 폴더 work_summary 검증")
    print("=" * 80)

    async with async_session_maker() as session:
        # WSOP 폴더 상세 정보 조회
        folder_data = await progress_service.get_folder_detail(
            session,
            "/mnt/nas/WSOP",
            include_files=False
        )

        if not folder_data:
            print("\n❌ WSOP 폴더를 찾을 수 없습니다.")
            return

        print(f"\n폴더명: {folder_data['name']}")
        print(f"경로: {folder_data['path']}")
        print(f"file_count (NAS): {folder_data['file_count']}")

        if folder_data.get("work_summary"):
            ws = folder_data["work_summary"]
            print("\n[work_summary]")
            print(f"  task_count: {ws.get('task_count')}")
            print(f"  total_files (NAS): {ws.get('total_files')}")
            print(f"  sheets_total_videos (구글 시트): {ws.get('sheets_total_videos')}")
            print(f"  total_done: {ws.get('total_done')}")
            print(f"  combined_progress (NAS 기준): {ws.get('combined_progress')}%")
            print(f"  actual_progress (시트 기준): {ws.get('actual_progress')}%")
            print(f"  data_source_mismatch: {ws.get('data_source_mismatch')}")
            print(f"  mismatch_count: {ws.get('mismatch_count')}")

            # 검증
            print("\n[검증]")
            expected_combined = round(ws['total_done'] / ws['total_files'] * 100, 1) if ws['total_files'] > 0 else 0
            expected_actual = round(ws['total_done'] / ws['sheets_total_videos'] * 100, 1) if ws['sheets_total_videos'] > 0 else 0

            print(f"  combined_progress 예상값: {expected_combined}%")
            print(f"  combined_progress 실제값: {ws.get('combined_progress')}%")
            match_str = "[OK] Match" if abs(ws.get('combined_progress', 0) - expected_combined) < 0.2 else "[FAIL] Mismatch"
            print(f"  {match_str}")

            print(f"\n  actual_progress 예상값: {expected_actual}%")
            print(f"  actual_progress 실제값: {ws.get('actual_progress')}%")
            match_str = "[OK] Match" if abs(ws.get('actual_progress', 0) - expected_actual) < 0.2 else "[FAIL] Mismatch"
            print(f"  {match_str}")

            # 불일치 플래그 검증
            expected_mismatch = abs(ws['total_files'] - ws['sheets_total_videos']) > max(ws['total_files'], ws['sheets_total_videos']) * 0.1
            print(f"\n  data_source_mismatch 예상값: {expected_mismatch}")
            print(f"  data_source_mismatch 실제값: {ws.get('data_source_mismatch')}")
            match_str = "[OK] Match" if ws.get('data_source_mismatch') == expected_mismatch else "[FAIL] Mismatch"
            print(f"  {match_str}")

        if folder_data.get("work_statuses"):
            print("\n[매칭된 work_statuses]")
            for ws in folder_data["work_statuses"]:
                print(f"  - {ws['category']}: {ws['excel_done']}/{ws['total_videos']} ({ws.get('progress_percent', 0):.1f}%)")


async def test_folder_tree():
    """폴더 트리의 work_summary 검증"""
    print("\n" + "=" * 80)
    print("  폴더 트리 work_summary 검증 (depth=2)")
    print("=" * 80)

    async with async_session_maker() as session:
        tree = await progress_service.get_folder_with_progress(
            session,
            path=None,  # 루트부터
            depth=2,
            include_files=False
        )

        for root_folder in tree:
            if root_folder['name'] == 'nas':
                for child in root_folder.get('children', []):
                    if child['name'] in ['WSOP', 'PAD', 'MPP']:
                        print(f"\n[{child['name']}]")
                        print(f"  file_count: {child['file_count']}")

                        if child.get('work_summary'):
                            ws = child['work_summary']
                            print(f"  total_files: {ws.get('total_files')}")
                            print(f"  sheets_total_videos: {ws.get('sheets_total_videos')}")
                            print(f"  combined_progress: {ws.get('combined_progress')}%")
                            print(f"  actual_progress: {ws.get('actual_progress')}%")
                            print(f"  data_source_mismatch: {ws.get('data_source_mismatch')}")

                            # actual_progress 필드 존재 확인
                            if 'actual_progress' in ws:
                                print("  [OK] actual_progress field exists")
                            else:
                                print("  [FAIL] actual_progress field missing")

                            if 'data_source_mismatch' in ws:
                                print("  [OK] data_source_mismatch field exists")
                            else:
                                print("  [FAIL] data_source_mismatch field missing")
                        else:
                            print("  work_summary: None")


async def main():
    print("=" * 80)
    print("  Phase 1 수정 검증: work_summary 필드 추가")
    print("=" * 80)

    try:
        await test_wsop_folder()
        await test_folder_tree()

        print("\n" + "=" * 80)
        print("  검증 완료")
        print("=" * 80)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
