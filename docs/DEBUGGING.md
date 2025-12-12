# Debugging Guide

디버깅 가이드 및 문제 해결

---

## Frontend 디버그

### Console 로그 확인

브라우저 DevTools > Console에서 확인:

```javascript
// 정상 로그
[FolderTreeWithProgress] API 응답: {...}
[getWorkSummary] 폴더: WSOP {depth: 1, hasWorkSummary: true, ...}

// 경고 로그
[getWorkSummary] ⚠️ GGMillions: work_summary가 없음!
```

### React Query DevTools

개발 모드에서 React Query DevTools로 캐시 상태 확인 가능.

### Network 탭

1. DevTools > Network 탭 열기
2. `/api/progress/tree` 요청 확인
3. Response 데이터에서 `work_summary` 필드 확인

---

## Backend 디버그

### 로그 확인

```powershell
# Docker 로그
docker-compose logs -f backend

# DEBUG 레벨만 필터
docker-compose logs -f backend | grep "\[DEBUG\]"

# ERROR 레벨만 필터
docker-compose logs -f backend | grep "\[ERROR\]"
```

### 로컬 개발 서버 로그

```powershell
# uvicorn 실행 시 --log-level debug
uvicorn app.main:app --reload --port 8000 --log-level debug
```

---

## DB 디버깅

### WorkStatus 카테고리 확인

```powershell
docker exec archive-stats-backend python -c "
from app.core.database import SessionLocal
from app.models.work_status import WorkStatus

db = SessionLocal()
for ws in db.query(WorkStatus).all():
    print(f'{ws.category}: total={ws.total_videos}, done={ws.excel_done}')
db.close()
"
```

### FolderStats 확인

```powershell
docker exec archive-stats-backend python -c "
from app.core.database import SessionLocal
from app.models.file_stats import FolderStats

db = SessionLocal()
for fs in db.query(FolderStats).limit(10).all():
    print(f'{fs.path}: files={fs.file_count}, size={fs.total_size}')
db.close()
"
```

### SQLite 직접 쿼리

```powershell
# 컨테이너 내부에서
docker exec -it archive-stats-backend sqlite3 /app/data/archive_stats.db

# 테이블 목록
.tables

# WorkStatus 조회
SELECT category, total_videos, excel_done FROM work_status LIMIT 10;

# FolderStats 조회
SELECT path, file_count, total_size FROM folder_stats LIMIT 10;
```

---

## 일반적인 문제 해결

### 1. 진행률이 표시되지 않음

**증상**: 폴더 트리에 진행률 바가 없음

**원인 확인**:
1. `/api/progress/tree` 응답에서 `work_summary` 필드 확인
2. WorkStatus 테이블에 해당 카테고리 데이터 있는지 확인

**해결**:
```powershell
# Google Sheets 동기화 수동 트리거
curl -X POST http://localhost:8002/api/sync/trigger
```

### 2. Cascading Match 문제

**증상**: 부모 폴더와 자식 폴더가 동일 카테고리에 매칭됨

**원인**: 매칭 전략 점수가 비슷할 때 발생

**해결**: `progress_service.py`에서 `parent_work_status_ids` 전파 로직 확인

### 3. NAS 연결 오류

**증상**: `/api/scan` 실패, 파일 통계 0

**원인 확인**:
```powershell
# NAS 마운트 확인
ls Z:\GGPNAs\ARCHIVE

# Docker 볼륨 마운트 확인
docker exec archive-stats-backend ls /mnt/nas
```

**해결**:
1. NAS SMB 연결 확인
2. `docker-compose.yml`에서 볼륨 마운트 경로 확인
3. `.env`의 `NAS_LOCAL_PATH` 확인

### 4. Docker 컨테이너 시작 실패

**증상**: `docker-compose up` 후 컨테이너 재시작 반복

**원인 확인**:
```powershell
docker-compose logs backend
```

**일반적인 원인**:
- `.env` 파일 누락
- DB 파일 권한 문제
- 포트 충돌 (8000, 8002)

### 5. API 응답 느림

**증상**: `/api/progress/tree` 응답 5초 이상

**원인**: NAS 스캔 또는 대용량 데이터 처리

**해결**:
1. NAS 네트워크 연결 확인
2. DB 인덱스 확인
3. 캐싱 적용 여부 확인

---

## 로그 레벨 설정

### Backend (FastAPI)

`app/core/config.py`:
```python
LOG_LEVEL: str = "DEBUG"  # DEBUG, INFO, WARNING, ERROR
```

### uvicorn

```powershell
uvicorn app.main:app --log-level debug
```

---

## 유용한 curl 명령어

```powershell
# 헬스체크
curl http://localhost:8002/health

# 전체 통계
curl http://localhost:8002/api/stats

# 진행률 트리
curl http://localhost:8002/api/progress/tree

# 작업 현황
curl http://localhost:8002/api/work-status

# 동기화 상태
curl http://localhost:8002/api/sync/status

# 수동 동기화
curl -X POST http://localhost:8002/api/sync/trigger
```
