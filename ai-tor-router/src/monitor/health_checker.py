"""
Health Checker — monitors Tor service health and auto-heals on failure.
"""

import time
import subprocess
import requests
import logging
from datetime import datetime
from collections import deque

logger = logging.getLogger("health_checker")

PROXIES = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
TEST_URL = "https://check.torproject.org/api/ip"


class HealthChecker:
    def __init__(self, tor_controller, check_interval: int = 30):
        self.tor = tor_controller
        self.check_interval = check_interval
        self.running = False
        self.status = "unknown"
        self.last_check = None
        self.heal_count = 0
        self.incident_log = deque(maxlen=100)

    def _test_tor(self) -> bool:
        """Returns True if Tor is working correctly."""
        try:
            r = requests.get(TEST_URL, proxies=PROXIES, timeout=15)
            data = r.json()
            return data.get("IsTor", False)
        except Exception:
            return False

    def _restart_tor(self):
        """Restart the Tor system service."""
        logger.warning("Restarting Tor service...")
        try:
            subprocess.run(["sudo", "systemctl", "restart", "tor"], check=True, timeout=30)
            time.sleep(15)
            # Reconnect controller
            self.tor.connect()
            logger.info("Tor service restarted successfully.")
        except Exception as e:
            logger.error(f"Failed to restart Tor: {e}")

    def _restore_iptables(self):
        """Re-apply iptables rules after restart."""
        try:
            subprocess.run(["sudo", "bash", "scripts/setup_iptables.sh"], check=True, timeout=15)
            logger.info("iptables rules restored.")
        except Exception as e:
            logger.warning(f"Could not restore iptables: {e}")

    def heal(self, reason: str = "auto"):
        """Perform full healing sequence."""
        incident = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "action": "restart_tor"
        }
        self._restart_tor()
        self._restore_iptables()
        self.heal_count += 1
        incident["resolved"] = self._test_tor()
        self.incident_log.appendleft(incident)
        logger.info(f"Heal #{self.heal_count} complete. Resolved: {incident['resolved']}")

    def check(self) -> dict:
        """Run a single health check and return status dict."""
        self.last_check = datetime.now().isoformat()
        tor_ok = self._test_tor()
        ctrl_ok = self.tor.is_connected()

        if tor_ok and ctrl_ok:
            self.status = "healthy"
        elif ctrl_ok and not tor_ok:
            self.status = "degraded"
        else:
            self.status = "down"

        return {
            "status": self.status,
            "tor_circuit_ok": tor_ok,
            "control_connected": ctrl_ok,
            "last_check": self.last_check,
            "heal_count": self.heal_count
        }

    def run(self):
        """Main health loop — runs in background thread."""
        self.running = True
        logger.info(f"Health checker started. Interval: {self.check_interval}s")
        consecutive_failures = 0

        while self.running:
            result = self.check()
            logger.debug(f"Health: {result['status']}")

            if result["status"] == "down":
                consecutive_failures += 1
                logger.error(f"Tor is DOWN! Consecutive failures: {consecutive_failures}")
                if consecutive_failures >= 2:
                    self.heal(reason="tor_down")
                    consecutive_failures = 0
            elif result["status"] == "degraded":
                consecutive_failures += 1
                logger.warning("Tor circuit degraded.")
            else:
                consecutive_failures = 0

            time.sleep(self.check_interval)

    def stop(self):
        self.running = False

    def get_incidents(self) -> list:
        return list(self.incident_log)
