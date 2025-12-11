"""
Google Sheets 구조 디버그 스크립트
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
import json

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SHEET_URL = "https://docs.google.com/spreadsheets/d/1xuN4_1mQME_SVwnI7445JuLd8K7tRS9HDNYYJi2fm2k"

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

    print(f"📊 Opening sheet: {SHEET_URL}")
    sheet = client.open_by_url(SHEET_URL)

    # 모든 워크시트 목록
    print(f"\n📑 워크시트 목록:")
    for i, ws in enumerate(sheet.worksheets()):
        print(f"  {i}: {ws.title}")

    # 첫 번째 워크시트 분석
    worksheet = sheet.get_worksheet(0)
    print(f"\n📄 분석 대상: {worksheet.title}")

    # 전체 데이터 가져오기
    all_values = worksheet.get_all_values()
    print(f"\n📊 총 행 수: {len(all_values)}")

    # 처음 5행 출력
    print("\n--- 처음 5행 ---")
    for i, row in enumerate(all_values[:5]):
        print(f"Row {i}: {row}")

    # 헤더 분석 (Row 2를 헤더로 가정)
    if len(all_values) >= 2:
        headers = all_values[1]
        print(f"\n--- 헤더 (Row 2) ---")
        for i, h in enumerate(headers):
            print(f"  Col {i}: '{h}'")

    # get_all_records() 결과 확인
    print("\n--- get_all_records() 결과 (첫 3개) ---")
    try:
        records = worksheet.get_all_records()
        for i, record in enumerate(records[:3]):
            print(f"Record {i}: {json.dumps(record, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"❌ get_all_records() 에러: {e}")

        # 수동 파싱 시도
        print("\n--- 수동 파싱 ---")
        headers = [h.strip() for h in all_values[1]]
        print(f"Headers: {headers}")

        for i, row in enumerate(all_values[2:5]):  # Row 3-5
            record = {}
            for j, val in enumerate(row):
                if j < len(headers):
                    record[headers[j]] = val
            print(f"Record {i}: {json.dumps(record, ensure_ascii=False, indent=2)}")

if __name__ == "__main__":
    main()
