#!/usr/bin/env python3
"""
AI-Driven Smart Tor Router
Entry point — starts all subsystems.
"""

import time
import threading
import logging
import yaml
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from tor.tor_controller import TorController
from tor.circuit_manager import CircuitManager
from tor.dns_guard import DNSGuard
from ai.anomaly_detector import AnomalyDetector
from ai.circuit_optimizer import CircuitOptimizer
from monitor.traffic_monitor import TrafficMonitor
from monitor.health_checker import HealthChecker
from monitor.logger import setup_logger
from api.dashboard import create_app

# ── Load config ──────────────────────────────────────────────────────────────
with open("config/settings.yaml", "r") as f:
    config = yaml.safe_load(f)

logger = setup_logger("main")


def main():
    logger.info("=" * 60)
    logger.info("  AI-Driven Smart Tor Router — Starting Up")
    logger.info("=" * 60)

    # 1. Start Tor controller
    logger.info("[1/6] Connecting to Tor control port...")
    tor = TorController(
        port=config["tor"]["control_port"],
        password=config["tor"].get("control_password", "")
    )
    tor.connect()
    logger.info(f"      Tor connected. Exit IP: {tor.get_exit_ip()}")

    # 2. DNS Guard
    logger.info("[2/6] Starting DNS leak guard...")
    dns_guard = DNSGuard()
    dns_guard.apply_rules()

    # 3. AI Anomaly Detector
    logger.info("[3/6] Initialising AI anomaly detector...")
    detector = AnomalyDetector(
        threshold=config["ai"]["anomaly_threshold"]
    )
    detector.load_or_train()

    # 4. Circuit Manager + Optimizer
    logger.info("[4/6] Starting circuit manager & optimizer...")
    circuit_mgr = CircuitManager(tor_controller=tor)
    optimizer = CircuitOptimizer(
        tor_controller=tor,
        circuit_manager=circuit_mgr,
        anomaly_detector=detector,
        rotation_interval=config["tor"]["circuit_rotation_interval"],
        preferred_countries=config["tor"].get("preferred_countries", []),
        blocked_countries=config["tor"].get("blocked_countries", [])
    )
    optimizer_thread = threading.Thread(target=optimizer.run, daemon=True)
    optimizer_thread.start()

    # 5. Traffic Monitor
    logger.info("[5/6] Starting traffic monitor...")
    monitor = TrafficMonitor(detector=detector)
    monitor_thread = threading.Thread(target=monitor.run, daemon=True)
    monitor_thread.start()

    # 6. Health Checker
    logger.info("[6/6] Starting health checker & auto-heal...")
    health = HealthChecker(
        tor_controller=tor,
        check_interval=30
    )
    health_thread = threading.Thread(target=health.run, daemon=True)
    health_thread.start()

    # Dashboard
    logger.info("Starting web dashboard on port 5000...")
    app = create_app(
        tor_controller=tor,
        circuit_manager=circuit_mgr,
        traffic_monitor=monitor,
        anomaly_detector=detector,
        health_checker=health
    )

    logger.info("=" * 60)
    logger.info("  Router is LIVE. Dashboard: http://0.0.0.0:5000")
    logger.info("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down AI Tor Router. Goodbye.")
        sys.exit(0)
