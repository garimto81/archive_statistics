"""
DB Migration: FolderStats에 work_status_id FK 컬럼 추가

실행 방법:
  docker exec archive-stats-backend python /app/scripts/migrate_add_work_status_fk.py

또는 로컬:
  cd backend
  python ../scripts/migrate_add_work_status_fk.py
"""

import sqlite3
import os
import sys

# DB 경로 설정
DB_PATHS = [
    "/app/data/archive_stats.db",  # Docker 컨테이너 내부
    "data/archive_stats.db",        # 로컬 backend 디렉토리에서 실행 시
    "../data/archive_stats.db",     # scripts 디렉토리에서 실행 시
]

def find_db():
    """DB 파일 찾기"""
    for path in DB_PATHS:
        if os.path.exists(path):
            return path
    return None

def migrate():
    """work_status_id 컬럼 추가 마이그레이션"""
    db_path = find_db()
    if not db_path:
        print("ERROR: DB 파일을 찾을 수 없습니다.")
        print(f"검색 경로: {DB_PATHS}")
        sys.exit(1)

    print(f"DB 경로: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. 현재 스키마 확인
    cursor.execute("PRAGMA table_info(folder_stats)")
    columns = {row[1] for row in cursor.fetchall()}
    print(f"현재 folder_stats 컬럼: {columns}")

    # 2. work_status_id 컬럼이 이미 있는지 확인
    if "work_status_id" in columns:
        print("INFO: work_status_id 컬럼이 이미 존재합니다. 마이그레이션 생략.")
        conn.close()
        return

    # 3. 컬럼 추가
    print("work_status_id 컬럼 추가 중...")
    cursor.execute("""
        ALTER TABLE folder_stats
        ADD COLUMN work_status_id INTEGER
        REFERENCES work_statuses(id)
    """)

    # 4. 인덱스 생성
    print("인덱스 생성 중...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS ix_folder_stats_work_status_id
        ON folder_stats(work_status_id)
    """)

    conn.commit()
    print("마이그레이션 완료!")

    # 5. 결과 확인
    cursor.execute("PRAGMA table_info(folder_stats)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"업데이트된 folder_stats 컬럼: {columns}")

    conn.close()

if __name__ == "__main__":
    migrate()
