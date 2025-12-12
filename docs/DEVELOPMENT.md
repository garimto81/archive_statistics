# Development Guide

빌드, 테스트, Docker 명령어 상세 가이드

---

## Backend (FastAPI)

### 초기 설정 (1회)

```powershell
cd D:\AI\claude01\archive-statistics\backend

python -m venv venv
venv\Scripts\activate           # Windows
# source venv/bin/activate      # Linux/Mac

pip install -r requirements.txt
cp .env.example .env            # 환경변수 설정
```

### 개발 서버

```powershell
cd D:\AI\claude01\archive-statistics\backend
uvicorn app.main:app --reload --port 8000
```

### 테스트

```powershell
# 단일 테스트 (권장)
pytest tests/test_scanner.py -v

# 전체 테스트 (간략 출력)
pytest tests/ -v --tb=short

# 특정 테스트 함수만
pytest tests/test_api.py -v -k "test_stats"

# 특정 테스트 클래스::함수
pytest tests/test_api.py::test_get_stats -v

# 커버리지 리포트 (주의: 120초 타임아웃)
# run_in_background: true 권장
pytest tests/ --cov=app --cov-report=term-missing
```

### 린트

```powershell
# 검사만
black --check app/
isort --check app/
flake8 app/

# 자동 수정
black app/ && isort app/
```

---

## Frontend (React/Vite)

### 초기 설정

```powershell
cd D:\AI\claude01\archive-statistics\frontend
npm install
```

### 개발 서버

```powershell
npm run dev    # http://localhost:5173
```

### 빌드

```powershell
npm run build
```

### 린트

```powershell
npm run lint
```

### E2E 테스트 (Playwright)

```powershell
npm run test:e2e              # 전체 실행
npm run test:e2e:ui           # UI 모드 (디버깅용)
npm run test:e2e:chromium     # Chromium만
```

---

## Docker (프로덕션)

### 전체 스택 실행

```powershell
cd D:\AI\claude01\archive-statistics
docker-compose up -d
```

### 로그 확인

```powershell
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 재빌드

```powershell
# Backend만 (Python 코드 변경 시)
docker-compose build --no-cache backend && docker-compose up -d backend

# 전체 재빌드
docker-compose down && docker-compose build --no-cache && docker-compose up -d
```

### 배포 확인

```powershell
docker-compose ps
curl http://localhost:8002/health
```

---

## PR 머지 후 필수 작업 ⚠️

**변경사항이 프로덕션에 반영되려면 Docker 재배포 필수!**

```powershell
cd D:\AI\claude01\archive-statistics
docker-compose down && docker-compose build --no-cache && docker-compose up -d
```

---

## DB 마이그레이션

새 컬럼 추가 등 스키마 변경 시:

```powershell
python -c "
import sqlite3
conn = sqlite3.connect('data/archive_stats.db')
cursor = conn.cursor()
cursor.execute('ALTER TABLE table_name ADD COLUMN new_column TEXT')
conn.commit()
conn.close()
"
```

---

## 환경변수

`backend/.env`:

```bash
NAS_LOCAL_PATH=Z:/GGPNAs/ARCHIVE      # Windows
# NAS_LOCAL_PATH=/mnt/nas              # Linux

DATABASE_URL=sqlite+aiosqlite:///./archive_stats.db
CORS_ALLOW_ALL=true                    # LAN 배포 시
GOOGLE_SHEETS_ID=1abc...               # Google Sheets 연동 시
```
