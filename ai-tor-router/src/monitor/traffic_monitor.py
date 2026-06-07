"""
Traffic Monitor — measures bandwidth and feeds samples to anomaly detector.
"""

import time
import psutil
import logging
from collections import deque

logger = logging.getLogger("traffic_monitor")


class TrafficMonitor:
    def __init__(self, detector, interface: str = "eth0", sample_interval: float = 5.0):
        self.detector = detector
        self.interface = interface
        self.sample_interval = sample_interval
        self.running = False

        # Rolling history for dashboard
        self.bandwidth_history = deque(maxlen=120)   # 10 min at 5s intervals
        self.anomaly_scores = deque(maxlen=120)

        self._prev_bytes_sent = 0
        self._prev_bytes_recv = 0
        self._prev_packets_sent = 0
        self._prev_packets_recv = 0
        self._prev_time = time.time()

        self.current_stats = {}

    def _read_net_io(self):
        counters = psutil.net_io_counters(pernic=True)
        # Fall back to total if interface not found
        if self.interface in counters:
            c = counters[self.interface]
        else:
            c = psutil.net_io_counters()
        return c.bytes_sent, c.bytes_recv, c.packets_sent, c.packets_recv

    def _sample(self) -> dict:
        now = time.time()
        bs, br, ps, pr = self._read_net_io()
        dt = now - self._prev_time

        bytes_out = (bs - self._prev_bytes_sent) / dt
        bytes_in = (br - self._prev_bytes_recv) / dt
        pkts_out = (ps - self._prev_packets_sent) / dt
        pkts_in = (pr - self._prev_packets_recv) / dt

        self._prev_bytes_sent = bs
        self._prev_bytes_recv = br
        self._prev_packets_sent = ps
        self._prev_packets_recv = pr
        self._prev_time = now

        total_bytes = bytes_out + bytes_in
        upload_ratio = (bytes_out / total_bytes) if total_bytes > 0 else 0.5

        connections = len(psutil.net_connections())

        sample = {
            "timestamp": now,
            "bytes_per_sec": total_bytes,
            "upload_bytes_per_sec": bytes_out,
            "download_bytes_per_sec": bytes_in,
            "packets_per_sec": pkts_out + pkts_in,
            "connection_count": connections,
            "dns_query_rate": 0,       # Placeholder (would need pcap for real value)
            "circuit_age_sec": 0,       # Filled by optimizer
            "upload_ratio": upload_ratio,
        }
        return sample

    def run(self):
        self.running = True
        logger.info(f"Traffic monitor started on interface '{self.interface}'")

        # Init baseline
        self._prev_bytes_sent, self._prev_bytes_recv, \
            self._prev_packets_sent, self._prev_packets_recv = self._read_net_io()
        self._prev_time = time.time()

        while self.running:
            try:
                time.sleep(self.sample_interval)
                sample = self._sample()
                self.current_stats = sample

                # Feed to AI detector
                is_anom, score = self.detector.is_anomalous(sample)

                self.bandwidth_history.append({
                    "t": sample["timestamp"],
                    "up": round(sample["upload_bytes_per_sec"] / 1024, 2),    # KB/s
                    "down": round(sample["download_bytes_per_sec"] / 1024, 2)
                })
                self.anomaly_scores.append({"t": sample["timestamp"], "score": round(score, 3)})

            except Exception as e:
                logger.error(f"Monitor error: {e}")

    def stop(self):
        self.running = False

    def get_bandwidth_history(self) -> list:
        return list(self.bandwidth_history)

    def get_anomaly_history(self) -> list:
        return list(self.anomaly_scores)
