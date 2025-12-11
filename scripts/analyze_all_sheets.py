"""
3개 Google Sheets 구조 분석 스크립트
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
import json

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

SHEETS = {
    "Work Status": "https://docs.google.com/spreadsheets/d/1xuN4_1mQME_SVwnI7445JuLd8K7tRS9HDNYYJi2fm2k",
    "WSOP Hand Database": "https://docs.google.com/spreadsheets/d/1pUMPKe-OsKc-Xd8lH1cP9ctJO4hj3keXY5RwNFp2Mtk",
    "WSOP Circuit LA": "https://docs.google.com/spreadsheets/d/1_RN_W_ZQclSZA0Iez6XniCXVtjkkd5HNZwiT6l-z6d4",
}

def main():
    # Service Account 파일 찾기
    possible_paths = [
        Path("service_account_key.json"),
        Path("../service_account_key.json"),
        Path("D:/AI/claude01/archive-statistics/service_account_key.json"),
    ]

    sa_path = None
    for p in possible_paths:
        if p.exists():
            sa_path = p
            break

    if not sa_path:
        print("❌ Service Account 파일을 찾을 수 없습니다.")
        return

    print(f"✅ Service Account 파일: {sa_path}")

    # Google Sheets 연결
    creds = Credentials.from_service_account_file(str(sa_path), scopes=SCOPES)
    client = gspread.authorize(creds)

    for sheet_name, sheet_url in SHEETS.items():
        print(f"\n{'='*80}")
        print(f"📊 {sheet_name}")
        print(f"   URL: {sheet_url}")
        print("="*80)

        try:
            sheet = client.open_by_url(sheet_url)

            # 모든 워크시트 분석
            for ws in sheet.worksheets():
                print(f"\n📑 워크시트: {ws.title}")

                all_values = ws.get_all_values()
                print(f"   총 행 수: {len(all_values)}")

                if len(all_values) == 0:
                    print("   (빈 시트)")
                    continue

                # 헤더 찾기 (첫 번째 비어있지 않은 행)
                header_row = None
                header_idx = 0
                for i, row in enumerate(all_values[:5]):
                    # 최소 3개 이상의 컬럼이 있는 행을 헤더로 간주
                    non_empty = [c for c in row if c.strip()]
                    if len(non_empty) >= 3:
                        header_row = row
                        header_idx = i
                        break

                if header_row:
                    print(f"   헤더 위치: Row {header_idx + 1}")
                    print(f"   컬럼 수: {len(header_row)}")
                    print(f"   컬럼 목록:")
                    for j, col in enumerate(header_row[:15]):  # 최대 15개만
                        col_clean = col.replace('\n', ' ').strip()[:40]
                        if col_clean:
                            print(f"      {j}: {col_clean}")

                    # 샘플 데이터 (헤더 다음 3행)
                    print(f"\n   샘플 데이터 (최대 3행):")
                    data_rows = all_values[header_idx + 1:header_idx + 4]
                    for i, row in enumerate(data_rows):
                        # 비어있지 않은 값만 표시
                        sample = {}
                        for j, val in enumerate(row[:10]):
                            if val.strip() and j < len(header_row):
                                key = header_row[j].replace('\n', ' ').strip()[:20]
                                sample[key] = val.strip()[:30]
                        if sample:
                            print(f"      Row {header_idx + 2 + i}: {json.dumps(sample, ensure_ascii=False)}")

        except Exception as e:
            print(f"   ❌ 에러: {e}")

if __name__ == "__main__":
    main()
