"""
Threat Scorer — combines multiple signals into a composite threat level.
"""

import logging

logger = logging.getLogger("threat_scorer")

LEVELS = {
    (0.0, 0.3): ("LOW", "green"),
    (0.3, 0.6): ("MEDIUM", "orange"),
    (0.6, 0.85): ("HIGH", "red"),
    (0.85, 1.0): ("CRITICAL", "darkred"),
}


class ThreatScorer:
    def __init__(self):
        self.current_score = 0.0
        self.current_level = "LOW"

    def compute(
        self,
        anomaly_score: float,
        latency_ms: float,
        connection_count: int,
        dns_rate: float
    ) -> dict:
        # Normalize inputs
        latency_norm = min(latency_ms / 5000.0, 1.0)
        conn_norm = min(connection_count / 100.0, 1.0)
        dns_norm = min(dns_rate / 50.0, 1.0)

        # Weighted composite score
        composite = (
            0.5 * anomaly_score +
            0.2 * latency_norm +
            0.2 * conn_norm +
            0.1 * dns_norm
        )
        composite = round(min(composite, 1.0), 3)
        self.current_score = composite

        # Determine level
        level = "LOW"
        color = "green"
        for (low, high), (lvl, clr) in LEVELS.items():
            if low <= composite <= high:
                level = lvl
                color = clr
                break

        self.current_level = level

        result = {
            "score": composite,
            "level": level,
            "color": color,
            "components": {
                "anomaly": round(anomaly_score, 3),
                "latency": round(latency_norm, 3),
                "connections": round(conn_norm, 3),
                "dns_rate": round(dns_norm, 3)
            }
        }
        logger.debug(f"Threat: {level} ({composite})")
        return result
