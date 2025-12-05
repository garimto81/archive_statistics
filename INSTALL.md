# Archive Statistics Dashboard - 설치 가이드

## 서버 정보
- **서버 IP**: 221.149.191.199
- **서브넷 마스크**: 255.255.255.224
- **게이트웨이**: 221.149.191.222
- **DNS**: 168.126.63.1 / 168.126.63.2

## 시스템 요구사항
- Docker 20.10+
- Docker Compose 2.0+
- 최소 4GB RAM
- 10GB 디스크 공간

---

## 빠른 설치 (Linux)

```bash
# 1. 패키지 압축 해제
unzip archive-stats-deploy.zip -d /opt/
cd /opt/Archive_Statistics

# 2. 설치 스크립트 실행 (root 권한)
sudo chmod +x deploy/install.sh
sudo ./deploy/install.sh
```

## 빠른 설치 (Windows)

```powershell
# 1. 패키지 압축 해제
Expand-Archive archive-stats-deploy.zip -DestinationPath C:\

# 2. PowerShell (관리자 권한)에서 실행
cd C:\Archive_Statistics
.\deploy\install.ps1
```

---

## 수동 설치

### 1. NAS 마운트

**Linux:**
```bash
# CIFS 유틸리티 설치
sudo apt-get install cifs-utils

# 마운트 디렉토리 생성
sudo mkdir -p /mnt/nas

# NAS 마운트
sudo mount -t cifs //10.10.100.122/docker/GGPNAs/ARCHIVE /mnt/nas \
  -o username=GGP,password='!@QW12qw',uid=1000,gid=1000

# 부팅 시 자동 마운트 (fstab 추가)
echo "//10.10.100.122/docker/GGPNAs/ARCHIVE /mnt/nas cifs username=GGP,password=!@QW12qw,uid=1000,gid=1000,_netdev 0 0" | sudo tee -a /etc/fstab
```

**Windows:**
```cmd
# 네트워크 드라이브 연결
net use Z: \\10.10.100.122\docker\GGPNAs\ARCHIVE /user:GGP "!@QW12qw" /persistent:yes
```

### 2. Docker 컨테이너 빌드 및 실행

```bash
cd /opt/Archive_Statistics

# 환경설정 파일 복사
cp deploy/.env.example deploy/.env

# Docker 이미지 빌드
docker-compose -f deploy/docker-compose.prod.yml build

# 서비스 시작
docker-compose -f deploy/docker-compose.prod.yml up -d
```

### 3. 상태 확인

```bash
# 컨테이너 상태
docker-compose -f deploy/docker-compose.prod.yml ps

# 헬스체크
curl http://localhost:8000/health
```

---

## 접속 정보

설치 완료 후 브라우저에서 접속:
- **대시보드**: http://221.149.191.199

---

## 관리 명령어

```bash
# 로그 확인
docker-compose -f deploy/docker-compose.prod.yml logs -f

# 서비스 중지
docker-compose -f deploy/docker-compose.prod.yml down

# 서비스 재시작
docker-compose -f deploy/docker-compose.prod.yml restart

# 이미지 재빌드 후 시작
docker-compose -f deploy/docker-compose.prod.yml up -d --build
```

---

## 문제 해결

### NAS 연결 실패
1. 네트워크 연결 확인: `ping 10.10.100.122`
2. SMB 포트 확인: `telnet 10.10.100.122 445`
3. 자격증명 확인: ID=GGP, 비밀번호 확인

### Docker 컨테이너 오류
```bash
# 로그 확인
docker logs archive-stats-backend
docker logs archive-stats-frontend
```

### 포트 충돌
- 80 포트 사용 중: nginx.conf에서 포트 변경
- 8000 포트 사용 중: docker-compose.prod.yml에서 포트 변경

---

## 파일 구조

```
Archive_Statistics/
├── backend/           # FastAPI 백엔드
│   ├── app/
│   │   ├── api/       # API 엔드포인트
│   │   ├── core/      # 설정
│   │   ├── models/    # DB 모델
│   │   └── services/  # 비즈니스 로직
│   └── requirements.txt
├── frontend/          # React 프론트엔드
│   ├── src/
│   └── package.json
├── docker/            # Docker 설정
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
├── deploy/            # 배포 스크립트
│   ├── docker-compose.prod.yml
│   ├── install.sh
│   ├── install.ps1
│   └── .env.example
└── data/              # 데이터 (SQLite DB)
```
