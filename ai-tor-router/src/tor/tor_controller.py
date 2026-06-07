"""
Tor Controller — wraps Stem library to control the Tor daemon.
"""

import requests
import logging
from stem import Signal
from stem.control import Controller

logger = logging.getLogger("tor_controller")


class TorController:
    def __init__(self, port: int = 9051, password: str = ""):
        self.port = port
        self.password = password
        self.controller: Controller = None

    def connect(self):
        """Authenticate and connect to the Tor control port."""
        try:
            self.controller = Controller.from_port(port=self.port)
            self.controller.authenticate(password=self.password)
            logger.info(f"Connected to Tor control port {self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Tor: {e}")
            raise

    def is_connected(self) -> bool:
        try:
            return self.controller is not None and self.controller.is_alive()
        except Exception:
            return False

    def new_circuit(self):
        """Signal Tor to create a new circuit (new identity)."""
        try:
            self.controller.signal(Signal.NEWNYM)
            logger.info("New Tor circuit requested (NEWNYM signal sent)")
        except Exception as e:
            logger.error(f"Failed to signal new circuit: {e}")

    def get_exit_ip(self) -> str:
        """Return current exit node IP via check.torproject.org."""
        try:
            proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
            r = requests.get("https://check.torproject.org/api/ip", proxies=proxies, timeout=10)
            return r.json().get("IP", "Unknown")
        except Exception as e:
            logger.warning(f"Could not fetch exit IP: {e}")
            return "Unknown"

    def get_circuits(self) -> list:
        """Return list of active circuits."""
        try:
            return list(self.controller.get_circuits())
        except Exception as e:
            logger.error(f"Could not fetch circuits: {e}")
            return []

    def get_info(self, key: str) -> str:
        """Get Tor GETINFO values."""
        try:
            return self.controller.get_info(key)
        except Exception:
            return ""

    def close(self):
        if self.controller:
            self.controller.close()
