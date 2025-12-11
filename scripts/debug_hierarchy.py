"""
이슈 3 디버깅: 폴더 하이어라키별 데이터 불일치 분석
"""
import sqlite3
import json
from pathlib import Path

# 데이터베이스 경로
DB_PATH = Path(__file__).parent.parent / "data" / "archive_stats.db"

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print('='*80)

def analyze_folder_hierarchy():
    """폴더 하이어라키 분석"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print_section("1. 폴더 하이어라키 (depth 0-2)")
    cursor.execute("""
        SELECT path, name, parent_path, depth, file_count, folder_count, total_size
        FROM folder_stats
        WHERE depth <= 2
        ORDER BY depth, path
        LIMIT 30
    """)

    folders = {}
    for row in cursor.fetchall():
        path = row['path']
        folders[path] = dict(row)
        print(f"\n[Depth {row['depth']}] {row['name']}")
        print(f"  Path: {path}")
        print(f"  Parent: {row['parent_path']}")
        print(f"  Files: {row['file_count']:,} | Folders: {row['folder_count']}")

    print_section("2. Work Status 데이터")
    cursor.execute("""
        SELECT category, total_videos, excel_done, progress_percent
        FROM work_statuses
        ORDER BY category
        LIMIT 30
    """)

    work_statuses = {}
    for row in cursor.fetchall():
        category = row['category']
        work_statuses[category] = dict(row)
        print(f"\n{category}")
        print(f"  Total Videos: {row['total_videos']}")
        print(f"  Excel Done: {row['excel_done']}")
        print(f"  Progress: {row['progress_percent']:.2f}%")

    print_section("3. 매칭 시뮬레이션")

    # progress_service의 _match_work_statuses 로직 재현
    def match_folder_to_work_status(folder_name):
        """폴더명과 Work Status 매칭"""
        matched = []
        folder_lower = folder_name.lower()

        for category, ws in work_statuses.items():
            category_lower = category.lower()

            # 1. 정확 일치
            if folder_lower == category_lower:
                matched.append((category, 'exact', ws))
                continue

            # 2. 카테고리가 폴더명으로 시작
            if category_lower.startswith(folder_lower + ' '):
                matched.append((category, 'prefix', ws))
                continue

            # 3. 독립 단어 매칭
            category_words = category_lower.split()
            if folder_lower in category_words:
                matched.append((category, 'word', ws))
                continue

            # 4. 연도 매칭
            if folder_lower.isdigit() and len(folder_lower) == 4:
                if folder_lower in category_words:
                    matched.append((category, 'year', ws))

        return matched

    # 샘플 폴더들에 대해 매칭 시뮬레이션
    test_folders = [
        "WSOP", "2023", "PAD", "TPC", "WSOPE",
        "WSOP Paradise", "2023 WSOP Paradise"
    ]

    for folder_name in test_folders:
        matches = match_folder_to_work_status(folder_name)
        print(f"\n폴더: '{folder_name}'")
        if matches:
            for cat, match_type, ws in matches:
                print(f"  → {cat} ({match_type}) | {ws['excel_done']}/{ws['total_videos']} ({ws['progress_percent']:.1f}%)")
        else:
            print("  → 매칭 없음")

    print_section("4. 중복 매칭 검증")

    # 특정 work_status가 여러 폴더에 매칭되는지 확인
    for category, ws in work_statuses.items():
        matched_folders = []
        for path, folder in folders.items():
            matches = match_folder_to_work_status(folder['name'])
            if any(cat == category for cat, _, _ in matches):
                matched_folders.append(folder['name'])

        if len(matched_folders) > 1:
            print(f"\n[WARN] '{category}' -> multiple folders:")
            for fname in matched_folders:
                print(f"    - {fname}")

    print_section("5. 상위 폴더 집계 검증")

    # 특정 상위 폴더의 하위 폴더 file_count 합산 검증
    cursor.execute("""
        SELECT
            parent_path,
            SUM(file_count) as child_file_sum,
            COUNT(*) as child_count
        FROM folder_stats
        WHERE parent_path IS NOT NULL AND depth = 1
        GROUP BY parent_path
    """)

    print("\n부모 폴더의 하위 파일 수 합산:")
    for row in cursor.fetchall():
        parent_path = row['parent_path']
        child_sum = row['child_file_sum']

        # 부모 폴더의 실제 file_count
        cursor.execute("SELECT file_count, name FROM folder_stats WHERE path = ?", (parent_path,))
        parent = cursor.fetchone()

        if parent:
            parent_count = parent['file_count']
            parent_name = parent['name']
            diff = parent_count - child_sum
            status = "[OK]" if abs(diff) < 10 else "[WARN]"

            print(f"\n{status} {parent_name} (depth 0)")
            print(f"  부모 file_count: {parent_count:,}")
            print(f"  자식 합산: {child_sum:,}")
            print(f"  차이: {diff:,} (부모 직속 파일 or 불일치)")

    conn.close()

if __name__ == "__main__":
    print("=" * 80)
    print("  이슈 3: 폴더 하이어라키별 데이터 불일치 분석")
    print("=" * 80)

    try:
        analyze_folder_hierarchy()

        print("\n" + "=" * 80)
        print("  분석 완료")
        print("=" * 80)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
