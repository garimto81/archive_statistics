# Archive Statistics Dashboard - Installation Script for Windows Server
# Server IP: 221.149.191.199
# Run as Administrator

param(
    [switch]$SkipDockerInstall
)

$ErrorActionPreference = "Stop"

Write-Host "========================================"
Write-Host " Archive Statistics Dashboard Installer"
Write-Host " Target Server: 221.149.191.199"
Write-Host "========================================"
Write-Host ""

# Check Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[!] Please run as Administrator" -ForegroundColor Red
    exit 1
}

# Check Docker
Write-Host "[*] Checking Docker..."
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerInstalled -and -not $SkipDockerInstall) {
    Write-Host "[*] Docker not found. Please install Docker Desktop from:"
    Write-Host "    https://www.docker.com/products/docker-desktop/"
    Write-Host ""
    Write-Host "After installing Docker Desktop, run this script again."
    exit 1
}
Write-Host "[OK] Docker found"

# Create directories
Write-Host "[*] Creating directories..."
$installPath = "C:\archive-stats"
New-Item -ItemType Directory -Force -Path "$installPath\data" | Out-Null

# Copy files
Write-Host "[*] Copying application files..."
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Copy-Item -Path "$scriptDir\..\*" -Destination $installPath -Recurse -Force

# Setup environment
Write-Host "[*] Setting up environment..."
if (-not (Test-Path "$installPath\deploy\.env")) {
    Copy-Item "$installPath\deploy\.env.example" "$installPath\deploy\.env"
}

# Mount NAS
Write-Host "[*] Mounting NAS share..."
$nasPath = "\\10.10.100.122\docker\GGPNAs\ARCHIVE"
$driveLetter = "Z:"

# Remove existing mapping if exists
if (Test-Path $driveLetter) {
    net use $driveLetter /delete /y 2>$null
}

# Map network drive
$password = "!@QW12qw"
net use $driveLetter $nasPath /user:GGP $password /persistent:yes

if (Test-Path $driveLetter) {
    Write-Host "[OK] NAS mounted as $driveLetter"
} else {
    Write-Host "[!] NAS mount failed - check credentials" -ForegroundColor Yellow
}

# Build and start containers
Write-Host "[*] Building Docker containers..."
Set-Location $installPath
docker-compose -f deploy/docker-compose.prod.yml build

Write-Host "[*] Starting services..."
docker-compose -f deploy/docker-compose.prod.yml up -d

# Wait for services
Write-Host "[*] Waiting for services to start..."
Start-Sleep -Seconds 10

# Health check
Write-Host "[*] Checking service health..."
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    if ($health.status -eq "healthy") {
        Write-Host "[OK] Backend is healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "[!] Backend health check failed" -ForegroundColor Yellow
}

try {
    $frontend = Invoke-WebRequest -Uri "http://localhost:80" -UseBasicParsing
    if ($frontend.StatusCode -eq 200) {
        Write-Host "[OK] Frontend is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "[!] Frontend check failed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================"
Write-Host " Installation Complete!"
Write-Host "========================================"
Write-Host ""
Write-Host " Access the dashboard at:"
Write-Host "   http://221.149.191.199" -ForegroundColor Cyan
Write-Host ""
Write-Host " Useful commands:"
Write-Host "   View logs:    docker-compose -f $installPath\deploy\docker-compose.prod.yml logs -f"
Write-Host "   Stop:         docker-compose -f $installPath\deploy\docker-compose.prod.yml down"
Write-Host "   Restart:      docker-compose -f $installPath\deploy\docker-compose.prod.yml restart"
Write-Host ""
