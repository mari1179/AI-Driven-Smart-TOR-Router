#!/bin/bash

set -e

echo "[+] Applying Tor transparent proxy firewall rules..."

# Interfaces
LAN_IF="wlan1"
WAN_IF="eth0"

# Tor ports
TRANS_PORT="9040"
DNS_PORT="5353"

# Flush existing rules
sudo iptables -F
sudo iptables -t nat -F

# Default policies
sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD ACCEPT
sudo iptables -P OUTPUT ACCEPT

# Enable masquerading
sudo iptables -t nat -A POSTROUTING -o $WAN_IF -j MASQUERADE

# Redirect DNS queries through Tor
sudo iptables -t nat -A PREROUTING -i $LAN_IF -p udp --dport 53 \
-j REDIRECT --to-ports $DNS_PORT

# Redirect all TCP traffic through Tor transparent proxy
sudo iptables -t nat -A PREROUTING -i $LAN_IF -p tcp --syn \
-j REDIRECT --to-ports $TRANS_PORT

# Allow forwarding
sudo iptables -A FORWARD -i $LAN_IF -o $WAN_IF -j ACCEPT
sudo iptables -A FORWARD -i $WAN_IF -o $LAN_IF \
-m state --state RELATED,ESTABLISHED -j ACCEPT

# Save rules
sudo netfilter-persistent save

echo "[✓] Tor transparent proxy firewall active!"