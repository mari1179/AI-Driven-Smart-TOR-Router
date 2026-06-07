"""
Circuit Optimizer — AI-driven circuit rotation logic.
Scores circuits and rotates when anomaly threshold exceeded or interval elapsed.
"""

import time
import requests
import logging

logger = logging.getLogger("circuit_optimizer")


class CircuitOptimizer:
    def __init__(
        self,
        tor_controller,
        circuit_manager,
        anomaly_detector,
        rotation_interval: int = 600,
        preferred_countries: list = None,
        blocked_countries: list = None
    ):
        self.tor = tor_controller
        self.circuit_mgr = circuit_manager
        self.detector = anomaly_detector
        self.rotation_interval = rotation_interval
        self.preferred_countries = preferred_countries or []
        self.blocked_countries = blocked_countries or []
        self.running = False

    def measure_latency(self) -> float:
        """Measure latency through current Tor circuit in ms."""
        try:
            proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
            t0 = time.time()
            requests.get("http://check.torproject.org", proxies=proxies, timeout=10)
            return (time.time() - t0) * 1000
        except Exception:
            return 9999.0

    def circuit_score(self) -> float:
        """
        Score the current circuit. Lower is better.
        Combines latency and recent anomaly scores.
        """
        latency = self.measure_latency()
        # Get average anomaly score from last 10 buffer samples
        buf = list(self.detector.training_buffer)[-10:]
        avg_anomaly = 0.0
        if buf:
            scores = [self.detector.score(s) for s in buf]
            avg_anomaly = sum(scores) / len(scores)

        # Weighted score: latency (normalized to 0-1 assuming max 5000ms) + anomaly
        latency_norm = min(latency / 5000.0, 1.0)
        score = 0.6 * latency_norm + 0.4 * avg_anomaly
        logger.debug(f"Circuit score: {score:.3f} (latency={latency:.0f}ms, anomaly={avg_anomaly:.3f})")
        return score

    def should_rotate(self, current_score: float) -> tuple:
        """Return (should_rotate: bool, reason: str)."""
        elapsed = self.circuit_mgr.seconds_since_rotation()

        # Anomaly-triggered rotation
        if current_score > 0.7:
            return True, "high_anomaly_score"

        # Scheduled rotation
        if elapsed >= self.rotation_interval:
            return True, "scheduled"

        # Exit node in blocked country
        exit_ip = self.circuit_mgr.current_ip
        # (Country check would require GeoIP — skipped for simplicity)

        return False, ""

    def run(self):
        """Main optimizer loop — runs in a background thread."""
        self.running = True
        logger.info(f"Circuit optimizer started. Rotation interval: {self.rotation_interval}s")

        # Wait for initial traffic samples
        time.sleep(30)

        while self.running:
            try:
                score = self.circuit_score()
                rotate, reason = self.should_rotate(score)

                if rotate:
                    logger.info(f"Rotating circuit: {reason} (score={score:.3f})")
                    self.circuit_mgr.rotate(reason=reason)
                else:
                    logger.debug(f"Circuit OK (score={score:.3f})")

            except Exception as e:
                logger.error(f"Optimizer error: {e}")

            time.sleep(60)  # Check every minute

    def stop(self):
        self.running = False
