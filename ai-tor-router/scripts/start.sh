#!/bin/bash

echo "=================================="
echo " Starting AI Smart Tor Router"
echo "=================================="

sudo systemctl start tor
sudo systemctl start hostapd
sudo systemctl start dnsmasq

sudo bash scripts/setup_iptables.sh

python3 main.py