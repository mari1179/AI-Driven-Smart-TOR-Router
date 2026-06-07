#!/bin/bash

set -e

echo "[+] Installing hotspot packages..."

sudo apt update
sudo apt install -y hostapd dnsmasq iptables-persistent

echo "[+] Stopping services..."

sudo systemctl stop hostapd
sudo systemctl stop dnsmasq

echo "[+] Configuring static IP for wlan1..."

sudo tee -a /etc/dhcpcd.conf > /dev/null <<EOF

interface wlan1
static ip_address=192.168.50.1/24
nohook wpa_supplicant
EOF

echo "[+] Creating hostapd config..."

sudo tee /etc/hostapd/hostapd.conf > /dev/null <<EOF
interface=wlan1
driver=nl80211
ssid=SecureNet
hw_mode=g
channel=6
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=changeme123
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

echo '[+] Linking hostapd config...'

sudo sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd

echo "[+] Configuring dnsmasq..."

sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.bak 2>/dev/null || true

sudo tee /etc/dnsmasq.conf > /dev/null <<EOF
interface=wlan1
dhcp-range=192.168.50.10,192.168.50.100,255.255.255.0,24h
domain-needed
bogus-priv
EOF

echo "[+] Enabling IP forwarding..."

sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf

sudo sysctl -p

echo "[+] Enabling services..."

sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

echo "[+] Restarting services..."

sudo systemctl restart dhcpcd
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq

echo "[✓] Hotspot setup complete!"
echo "[✓] SSID: SecureNet"
echo "[✓] Password: changeme123"