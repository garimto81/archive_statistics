# Archive Statistics Dashboard

1 PB 규모의 아카이브 저장소를 모니터링하고 관리하는 웹 기반 대시보드 솔루션

## 주요 기능

- **파일 통계 대시보드**: 파일 수, 용량, 재생시간, 형식별 분포
- **폴더 트리 뷰**: 인터랙티브 폴더 구조 시각화 (트리맵 포함)
- **아카이빙 작업 현황**: CSV Import/Export, 칸반 보드, 진행률 추적
- **히스토리 추적**: 용량 변화 추이 그래프
- **알림 시스템**: 용량 임계치 도달 시 알림

## 기술 스택

### Backend
- Python 3.11+
- FastAPI
- SQLite / PostgreSQL
- SMB/CIFS (NAS 연결)

### Frontend
- React 18 + TypeScript
- Vite
- TailwindCSS
- Recharts / Chart.js
- React Query

### Infrastructure
- Docker & Docker Compose
- Nginx (Reverse Proxy)

## 설치 및 실행

### 요구사항
- Python 3.11+
- Node.js 18+
- Docker (선택)

### 개발 환경 설정

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Docker로 실행

```bash
docker-compose up -d
```

## 프로젝트 구조

```
Archive_Statistics/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── main.py         # FastAPI 앱 진입점
│   │   ├── api/            # API 라우터
│   │   ├── models/         # DB 모델
│   │   ├── schemas/        # Pydantic 스키마
│   │   ├── services/       # 비즈니스 로직
│   │   └── core/           # 설정, 유틸리티
│   ├── tests/
│   └── requirements.txt
├── frontend/                # React Frontend
│   ├── src/
│   │   ├── components/     # React 컴포넌트
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── hooks/          # Custom Hooks
│   │   ├── services/       # API 서비스
│   │   └── types/          # TypeScript 타입
│   ├── public/
│   └── package.json
├── docker/                  # Docker 설정
├── docs/                    # 문서
│   └── UI_MOCKUP.md        # UI 목업
├── tasks/                   # PRD 및 태스크
│   ├── prds/
│   └── 0001-tasks-*.md
└── README.md
```

## NAS 연결 정보

- **경로**: `\\10.10.100.122\docker\GGPNAs\ARCHIVE`
- **프로토콜**: SMB/CIFS

## 라이선스

Private - GGP Team Internal Use Only

## 문서

- [PRD](tasks/prds/0001-prd-archive-statistics.md)
- [UI Mockup](docs/UI_MOCKUP.md)
- [Task List](tasks/0001-tasks-archive-statistics.md)
