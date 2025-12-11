"""
WSOP 폴더 데이터 불일치 상세 분석
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "archive_stats.db"

def main():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 80)
    print("  WSOP 폴더 하이어라키 상세 분석")
    print("=" * 80)

    # 1. WSOP 관련 폴더 트리 (depth 1-3)
    print("\n[1] WSOP 폴더 트리 (depth 1-3)")
    cursor.execute("""
        SELECT path, name, depth, file_count, folder_count, parent_path
        FROM folder_stats
        WHERE path LIKE '/mnt/nas/WSOP%'
        ORDER BY depth, path
        LIMIT 50
    """)

    wsop_folders = {}
    for row in cursor.fetchall():
        path = row['path']
        wsop_folders[path] = dict(row)
        indent = "  " * row['depth']
        print(f"{indent}[D{row['depth']}] {row['name']}: {row['file_count']} files")

    # 2. WSOP 관련 Work Status
    print("\n" + "=" * 80)
    print("[2] WSOP 관련 Work Status")
    print("=" * 80)

    cursor.execute("""
        SELECT category, total_videos, excel_done, progress_percent
        FROM work_statuses
        WHERE category LIKE '%WSOP%'
        ORDER BY category
    """)

    wsop_work_statuses = []
    for row in cursor.fetchall():
        ws = dict(row)
        wsop_work_statuses.append(ws)
        print(f"\n{ws['category']}")
        print(f"  total_videos: {ws['total_videos']}")
        print(f"  excel_done: {ws['excel_done']}")
        print(f"  progress: {ws['progress_percent']:.1f}%")

    # 3. 매칭 시뮬레이션: WSOP 폴더에 매칭되는 work_status 찾기
    print("\n" + "=" * 80)
    print("[3] 매칭 시뮬레이션: progress_service 로직 재현")
    print("=" * 80)

    def match_work_statuses(folder_name, work_statuses):
        """폴더명과 Work Status 카테고리 매칭"""
        matched = []
        folder_lower = folder_name.lower()

        for ws in work_statuses:
            category = ws['category']
            category_lower = category.lower()

            # 1. 정확히 일치
            if folder_lower == category_lower:
                matched.append((ws, 'exact'))
                continue

            # 2. 카테고리가 폴더명으로 시작
            if category_lower.startswith(folder_lower + ' '):
                matched.append((ws, 'prefix'))
                continue

            # 3. 독립 단어 매칭
            category_words = category_lower.split()
            if folder_lower in category_words:
                matched.append((ws, 'word'))
                continue

            # 4. 연도 매칭
            if folder_lower.isdigit() and len(folder_lower) == 4:
                if folder_lower in category_words:
                    matched.append((ws, 'year'))

        return matched

    # WSOP 최상위 폴더
    print("\n--- WSOP (depth 1) ---")
    print(f"실제 file_count: 860")

    matches = match_work_statuses("WSOP", wsop_work_statuses)
    total_matched_videos = sum(ws['total_videos'] for ws, _ in matches)
    total_matched_done = sum(ws['excel_done'] for ws, _ in matches)

    print(f"\n매칭된 work_status: {len(matches)}개")
    for ws, match_type in matches:
        print(f"  - {ws['category']} ({match_type})")
        print(f"    total_videos: {ws['total_videos']}, excel_done: {ws['excel_done']}")

    print(f"\n합산:")
    print(f"  total_videos (구글 시트): {total_matched_videos}")
    print(f"  excel_done: {total_matched_done}")
    print(f"  file_count (NAS): 860")
    print(f"  차이: {total_matched_videos - 860}")

    # 4. 하위 폴더 검증
    print("\n" + "=" * 80)
    print("[4] 하위 폴더별 매칭 검증")
    print("=" * 80)

    cursor.execute("""
        SELECT path, name, file_count
        FROM folder_stats
        WHERE parent_path = '/mnt/nas/WSOP' AND depth = 2
        ORDER BY name
    """)

    child_sum = 0
    for row in cursor.fetchall():
        folder_name = row['name']
        file_count = row['file_count']
        child_sum += file_count

        matches = match_work_statuses(folder_name, wsop_work_statuses)

        print(f"\n{folder_name}")
        print(f"  file_count (NAS): {file_count}")

        if matches:
            matched_total = sum(ws['total_videos'] for ws, _ in matches)
            matched_done = sum(ws['excel_done'] for ws, _ in matches)
            print(f"  매칭된 work_status: {len(matches)}개")
            for ws, match_type in matches:
                print(f"    - {ws['category']} ({match_type}): {ws['excel_done']}/{ws['total_videos']}")
            print(f"  합산: {matched_done}/{matched_total}")
            print(f"  차이: {matched_total - file_count}")
        else:
            print(f"  매칭: 없음")

    print(f"\n하위 폴더 file_count 합계: {child_sum}")
    print(f"부모 폴더 file_count: 860")
    print(f"차이: {860 - child_sum} (부모 직속 파일)")

    # 5. 문제점 요약
    print("\n" + "=" * 80)
    print("[5] 발견된 문제점")
    print("=" * 80)

    print("""
1. 중복 매칭 문제:
   - "WSOP" 폴더는 5개의 work_status에 매칭됨
     (2023 WSOP Paradise, 2025 WSOP, WSOP Cyprus, WSOP Europe, WSOP LA)
   - 각 work_status의 total_videos를 합산하면 NAS file_count와 불일치

2. 하이어라키 집계 문제:
   - 상위 폴더(WSOP)의 work_summary.combined_progress 계산 시
   - 하위 폴더(WSOP Bracelet Event, WSOP Circuit Event 등)의 work_summary도 합산
   - 같은 work_status가 상위/하위 폴더에서 중복 매칭되면 이중 카운팅

3. 진행률 계산 기준 불일치:
   - progress_service는 file_count (NAS 기준) 사용
   - work_status.progress_percent는 total_videos (구글 시트) 기준
   - 두 값이 다르면 진행률이 100% 초과 또는 비정상적으로 낮아짐

4. 데이터 출처 차이:
   - file_count: NAS 스캔 결과 (실제 파일 개수)
   - total_videos: 구글 시트 수동 입력 (작업 대상 수량)
   - 파일 분할/병합 시 개수 불일치 발생 가능
""")

    conn.close()

if __name__ == "__main__":
    main()
