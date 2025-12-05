#!/bin/bash
# Archive Statistics Dashboard - Installation Script for Linux Server
# Server IP: 221.149.191.199

set -e

echo "========================================"
echo " Archive Statistics Dashboard Installer"
echo " Target Server: 221.149.191.199"
echo "========================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "[!] Please run as root (sudo ./install.sh)"
    exit 1
fi

# Check Docker
echo "[*] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "[*] Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
    rm get-docker.sh
fi
echo "[OK] Docker installed"

# Check Docker Compose
echo "[*] Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "[*] Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi
echo "[OK] Docker Compose installed"

# Install CIFS utils for NAS mounting
echo "[*] Installing CIFS utilities..."
apt-get update
apt-get install -y cifs-utils curl
echo "[OK] CIFS utilities installed"

# Create directories
echo "[*] Creating directories..."
mkdir -p /opt/archive-stats/data
mkdir -p /mnt/nas

# Copy files
echo "[*] Copying application files..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -r "$SCRIPT_DIR"/../* /opt/archive-stats/

# Setup environment
echo "[*] Setting up environment..."
if [ ! -f /opt/archive-stats/deploy/.env ]; then
    cp /opt/archive-stats/deploy/.env.example /opt/archive-stats/deploy/.env
fi

# Mount NAS
echo "[*] Mounting NAS share..."
source /opt/archive-stats/deploy/.env

# Add to fstab for persistent mount
FSTAB_ENTRY="//${NAS_HOST}/${NAS_SHARE}/${NAS_PATH} /mnt/nas cifs username=${NAS_USERNAME},password=${NAS_PASSWORD},uid=1000,gid=1000,file_mode=0755,dir_mode=0755,_netdev 0 0"
if ! grep -q "${NAS_HOST}" /etc/fstab; then
    echo "$FSTAB_ENTRY" >> /etc/fstab
fi
mount -a || echo "[!] NAS mount failed - check credentials"

# Build and start containers
echo "[*] Building Docker containers..."
cd /opt/archive-stats
docker-compose -f deploy/docker-compose.prod.yml build

echo "[*] Starting services..."
docker-compose -f deploy/docker-compose.prod.yml up -d

# Wait for services
echo "[*] Waiting for services to start..."
sleep 10

# Health check
echo "[*] Checking service health..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "[OK] Backend is healthy"
else
    echo "[!] Backend health check failed"
fi

if curl -s http://localhost:80 | grep -q "html"; then
    echo "[OK] Frontend is accessible"
else
    echo "[!] Frontend check failed"
fi

echo ""
echo "========================================"
echo " Installation Complete!"
echo "========================================"
echo ""
echo " Access the dashboard at:"
echo "   http://221.149.191.199"
echo ""
echo " Useful commands:"
echo "   View logs:    docker-compose -f /opt/archive-stats/deploy/docker-compose.prod.yml logs -f"
echo "   Stop:         docker-compose -f /opt/archive-stats/deploy/docker-compose.prod.yml down"
echo "   Restart:      docker-compose -f /opt/archive-stats/deploy/docker-compose.prod.yml restart"
echo ""
