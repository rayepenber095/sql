#!/usr/bin/env bash
# SQLi Engine — Kali Linux Installer
# Usage: sudo bash install.sh

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "============================================="
echo "   SQLi Engine Installer — Kali Linux"
echo "============================================="

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[ERROR] Please run as root: sudo bash install.sh${NC}"
  exit 1
fi

INSTALL_DIR="/opt/sqli-engine"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[1/6] Installing system dependencies..."
apt-get update -q
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libxcb1 \
    libx11-6 \
    libgl1 \
    2>/dev/null

echo "[2/6] Copying project to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cp -r "$SOURCE_DIR"/. "$INSTALL_DIR/"
cd "$INSTALL_DIR"

echo "[3/6] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo "[4/6] Creating required directories..."
mkdir -p db exports wordlists

echo "[5/6] Creating CLI launcher at /usr/local/bin/sqli-engine..."
cat > /usr/local/bin/sqli-engine <<'LAUNCHER'
#!/bin/bash
source /opt/sqli-engine/venv/bin/activate
cd /opt/sqli-engine
python3 main.py "$@"
LAUNCHER
chmod +x /usr/local/bin/sqli-engine

echo "[6/6] Creating desktop shortcut..."
cat > /usr/share/applications/sqli-engine.desktop <<'DESKTOP'
[Desktop Entry]
Name=SQLi Engine
Comment=Graphical SQL Injection Testing Tool (Authorized Testing Only)
Exec=/usr/local/bin/sqli-engine
Terminal=false
Type=Application
Categories=Security;
DESKTOP

echo ""
echo -e "${GREEN}============================================="
echo "   Installation Complete!"
echo "============================================="
echo "  Run with:  sqli-engine"
echo "  Or:        python3 /opt/sqli-engine/main.py"
echo -e "=============================================${NC}"
