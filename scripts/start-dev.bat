@echo off
REM Start development servers

echo ========================================
echo  Archive Statistics Dashboard - Dev Mode
echo ========================================
echo.

REM Check if Z: drive is mounted
if exist Z:\ (
    echo [OK] NAS mounted at Z:
) else (
    echo [!] NAS not mounted. Run mount-nas.bat first
    echo.
)

echo.
echo Starting Backend (port 8000)...
start "Backend" cmd /k "cd /d %~dp0\..\backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo Starting Frontend (port 3000)...
start "Frontend" cmd /k "cd /d %~dp0\..\frontend && npm run dev -- --host 0.0.0.0"

echo.
echo ========================================
echo  Servers starting...
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:3000
echo  LAN:      http://10.10.100.87:3000
echo ========================================
echo.
echo Press any key to exit (servers will keep running)
pause >nul
