"""
Circuit Manager — tracks circuit history and rotation events.
"""

import time
import logging
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger("circuit_manager")


@dataclass
class CircuitEvent:
    timestamp: float
    reason: str
    old_ip: str
    new_ip: str
    latency_ms: float


class CircuitManager:
    def __init__(self, tor_controller, max_history: int = 50):
        self.tor = tor_controller
        self.history: deque = deque(maxlen=max_history)
        self.current_ip: str = "Unknown"
        self.rotation_count: int = 0
        self.last_rotation: float = time.time()

    def rotate(self, reason: str = "scheduled") -> CircuitEvent:
        """Rotate to a new Tor circuit and log the event."""
        old_ip = self.current_ip
        t0 = time.time()

        self.tor.new_circuit()
        # Wait for NEWNYM cooldown (Tor enforces 10s minimum)
        time.sleep(10)

        new_ip = self.tor.get_exit_ip()
        latency_ms = (time.time() - t0) * 1000

        event = CircuitEvent(
            timestamp=time.time(),
            reason=reason,
            old_ip=old_ip,
            new_ip=new_ip,
            latency_ms=latency_ms
        )
        self.history.appendleft(event)
        self.current_ip = new_ip
        self.rotation_count += 1
        self.last_rotation = time.time()

        logger.info(f"Circuit rotated [{reason}]: {old_ip} → {new_ip} ({latency_ms:.0f}ms)")
        return event

    def get_history(self) -> list:
        return [
            {
                "timestamp": e.timestamp,
                "reason": e.reason,
                "old_ip": e.old_ip,
                "new_ip": e.new_ip,
                "latency_ms": round(e.latency_ms, 1)
            }
            for e in self.history
        ]

    def seconds_since_rotation(self) -> float:
        return time.time() - self.last_rotation
