#!/bin/bash
# ══════════════════════════════════════════════════════════════════
#  AI-Driven Smart Tor Router — Full Installer for Raspberry Pi
#  Run as: sudo bash scripts/install.sh
# ══════════════════════════════════════════════════════════════════

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; exit 1; }
section() { echo -e "\n${GREEN}══ $1 ══${NC}"; }

# ── Check root ──────────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then error "Please run as root: sudo bash scripts/install.sh"; fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
info "Project directory: $PROJECT_DIR"

# ── 1. System update ────────────────────────────────────────────
section "System Update"
apt-get update -y && apt-get upgrade -y
info "System updated."

# ── 2. Install system packages ──────────────────────────────────
section "Installing Packages"
apt-get install -y \
  tor \
  hostapd \
  dnsmasq \
  iptables \
  iptables-persistent \
  python3 \
  python3-pip \
  python3-venv \
  net-tools \
  curl \
  git \
  rfkill
info "System packages installed."

# ── 3. Python dependencies ──────────────────────────────────────
section "Python Dependencies"
cd "$PROJECT_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
info "Python packages installed."

# ── 4. Configure Tor ────────────────────────────────────────────
section "Configuring Tor"
cp config/torrc /etc/tor/torrc
systemctl enable tor
systemctl restart tor
sleep 5
if systemctl is-active --quiet tor; then
  info "Tor is running."
else
  warn "Tor failed to start. Check: sudo journalctl -u tor"
fi

# ── 5. Configure Hotspot ────────────────────────────────────────
section "Setting Up Wi-Fi Hotspot"
bash "$PROJECT_DIR/scripts/setup_hotspot.sh"

# ── 6. Configure iptables ───────────────────────────────────────
section "Setting Up Firewall Rules"
bash "$PROJECT_DIR/scripts/setup_iptables.sh"
netfilter-persistent save
info "iptables rules saved."

# ── 7. Create systemd service ───────────────────────────────────
section "Creating Systemd Service"
cat > /etc/systemd/system/ai-tor-router.service << EOF
[Unit]
Description=AI-Driven Smart Tor Router
After=network.target tor.service
Requires=tor.service

[Service]
Type=simple
User=pi
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ai-tor-router
info "Systemd service created and enabled."

# ── 8. Create data directories ──────────────────────────────────
mkdir -p "$PROJECT_DIR/data" "$PROJECT_DIR/logs"
chown -R pi:pi "$PROJECT_DIR/data" "$PROJECT_DIR/logs"

# ── Done ────────────────────────────────────────────────────────
section "Installation Complete"
echo ""
echo "  ┌─────────────────────────────────────────────────┐"
echo "  │  AI Tor Router installed successfully!           │"
echo "  │                                                   │"
echo "  │  Start:    sudo systemctl start ai-tor-router    │"
echo "  │  Status:   sudo systemctl status ai-tor-router   │"
echo "  │  Logs:     journalctl -u ai-tor-router -f        │"
echo "  │  Dashboard: http://raspberrypi.local:5000        │"
echo "  │                                                   │"
echo "  │  ⚠  Change the hotspot password in:             │"
echo "  │     config/settings.yaml & config/hostapd.conf  │"
echo "  └─────────────────────────────────────────────────┘"
echo ""
