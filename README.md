# 🧅 AI-Driven Smart Tor Router on Raspberry Pi

> An intelligent, self-managing anonymous routing system powered by AI — built on a Raspberry Pi. Routes all connected device traffic securely through the Tor network with AI-based anomaly detection, automatic circuit management, DNS leak prevention, and a live monitoring dashboard.

# 📸 Project Overview

This project transforms a Raspberry Pi into an intelligent Tor gateway router.

Any device connected to the Raspberry Pi hotspot automatically routes its traffic through the Tor network using transparent proxying and DNS redirection.

An AI engine continuously monitors traffic statistics, detects anomalies, optimizes Tor circuit usage, and performs self-healing when failures occur.

```text
[ Devices ]
     │
     ▼
[ Raspberry Pi Hotspot ]
     │
     ▼
[ iptables Transparent Proxy ]
     │
     ▼
[ Tor TransPort + DNSPort ]
     │
     ▼
[ AI Monitoring Engine ]
     │
     ▼
[ Tor Network ]
     │
     ▼
[ Anonymous Internet ]
```

---

# ✨ Features

| Feature                  | Description                                                |
| ------------------------ | ---------------------------------------------------------- |
| 🔁 Auto Circuit Rotation | Automatically rotates Tor circuits based on AI scoring     |
| 🧠 AI Anomaly Detection  | Isolation Forest model detects suspicious traffic patterns |
| 📊 Live Dashboard        | Real-time Flask dashboard with metrics and alerts          |
| 🔧 Auto-Healing          | Automatically restarts Tor and rebuilds firewall rules     |
| 🌍 Country Filtering     | Prefer or block Tor exit nodes by country                  |
| 📡 Hotspot Mode          | Raspberry Pi acts as a secure Wi-Fi hotspot                |
| 🔐 DNS Leak Prevention   | Forces all DNS traffic through Tor DNSPort                 |
| 📈 Traffic Analytics     | Collects anonymized metrics for AI learning                |
| 🚨 Threat Alerts         | Generates alerts on abnormal traffic behavior              |
| 🛡 Transparent Proxying  | Redirects all TCP traffic through Tor automatically        |

---

# 🛒 Hardware Requirements

| Component         | Recommended                         |
| ----------------- | ----------------------------------- |
| Raspberry Pi      | Raspberry Pi 4 (2GB+ RAM) or Pi 3B+ |
| MicroSD Card      | 16GB+ Class 10                      |
| USB Wi-Fi Adapter | TP-Link TL-WN725N or compatible     |
| Ethernet Cable    | Upstream internet connection        |
| Power Supply      | Official Pi 4 USB-C (5V/3A)         |

---

# 🧰 Software Stack

* Raspberry Pi OS Lite (64-bit)
* Python 3.9+
* Tor (`tor`)
* Flask
* Stem (Tor Controller API)
* Scikit-learn
* psutil
* hostapd
* dnsmasq
* iptables / netfilter-persistent

---

# 📁 Project Structure

```text
ai-tor-router/
├── src/
│   ├── ai/
│   │   ├── anomaly_detector.py
│   │   ├── circuit_optimizer.py
│   │   └── threat_scorer.py
│   ├── tor/
│   │   ├── tor_controller.py
│   │   ├── circuit_manager.py
│   │   └── dns_guard.py
│   ├── monitor/
│   │   ├── traffic_monitor.py
│   │   ├── health_checker.py
│   │   └── logger.py
│   └── api/
│       ├── dashboard.py
│       └── routes.py
│
├── config/
│   ├── torrc
│   ├── hostapd.conf
│   ├── dnsmasq.conf
│   └── settings.yaml
│
├── scripts/
│   ├── install.sh
│   ├── setup_hotspot.sh
│   ├── setup_iptables.sh
│   └── start.sh
│
├── tests/
│   ├── test_anomaly.py
│   ├── test_circuit.py
│   └── test_api.py
│
├── .github/workflows/
│   └── ci.yml
│
├── requirements.txt
├── main.py
└── README.md
```

---

# 🚀 Installation

## Step 1 — Flash Raspberry Pi OS

Flash Raspberry Pi OS Lite (64-bit) using Raspberry Pi Imager.

Enable:

* SSH
* Wi-Fi (optional)
* Username/password

---

## Step 2 — SSH into the Raspberry Pi

```bash
ssh pi@raspberrypi.local
```

---

## Step 3 — Clone Repository

```bash
https://github.com/mari1179/AI-Driven-Smart-TOR-Router.git
cd ai-tor-router
```

---

## Step 4 — Run Installer

```bash
chmod +x scripts/install.sh
sudo bash scripts/install.sh
```

The installer automatically:

* Updates packages
* Installs Tor
* Installs hostapd + dnsmasq
* Configures hotspot
* Enables IP forwarding
* Configures transparent proxy firewall rules
* Installs Python dependencies
* Enables required services

---

## Step 5 — Start Router

```bash
chmod +x scripts/start.sh
sudo bash scripts/start.sh
```

Dashboard:

```text
http://raspberrypi.local:5000
```

---

# ⚙️ Configuration

Edit:

```text
config/settings.yaml
```

Example:

```yaml
tor:
  socks_port: 9050
  control_port: 9051
  transparent_port: 9040
  dns_port: 5353
  circuit_rotation_interval: 600

  preferred_countries: []
  blocked_countries:
    - "CN"
    - "RU"

ai:
  anomaly_threshold: 0.75
  model_retrain_interval: 3600
  alert_on_anomaly: true

hotspot:
  ssid: "SecureNet"
  password: "changeme123"
  interface: "wlan1"
  channel: 6

alerts:
  telegram_token: ""
  telegram_chat_id: ""
  email: ""
```

---

# 🧠 AI Engine

## Anomaly Detection

Uses an Isolation Forest machine learning model trained on:

* Bytes per second
* Packets per second
* Connection count
* DNS request rate
* Circuit age
* Upload/download ratio

Traffic outside the learned baseline is flagged as anomalous.

---

## Circuit Optimization

The optimizer scores Tor circuits using:

* Exit node latency
* Circuit age
* Network performance
* Anomaly score
* Historical stability

Automatically rotates to better-performing circuits.

---

## Auto-Healing

Health checker continuously:

1. Tests Tor control connectivity
2. Verifies outbound Tor traffic
3. Restarts Tor on failure
4. Rebuilds firewall rules
5. Logs incidents to dashboard

---

# 📊 Dashboard Features

The Flask dashboard provides:

* Tor connection status
* Exit node IP
* Threat level scoring
* Live bandwidth graphs
* Circuit rotation history
* AI anomaly alerts
* Auto-healing logs
* Manual circuit rotation
* Connected device monitoring

---

# 🔒 Security Notes

* Change default hotspot credentials before deployment
* Never expose dashboard port `5000` publicly
* Tor does not guarantee perfect anonymity
* Avoid logging into personal accounts while using Tor
* Some UDP applications may not function correctly through Tor
* Use responsibly and comply with local laws

---

# 🧪 Running Tests

```bash
pip3 install pytest
pytest tests/
```

---

# 🤝 Contributing

Contributions are welcome.

Please open an issue before submitting major changes.

---

# 📄 License

MIT License © 2026

Copyright (c) 2026 Mari Ganesh


# ⚠️ Disclaimer

This project is intended strictly for educational, privacy, and cybersecurity research purposes.

The authors are not responsible for misuse, illegal activities, or damages caused by improper usage.

Always comply with local laws and regulations.
