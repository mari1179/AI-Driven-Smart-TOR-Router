"""
AI Anomaly Detector — Isolation Forest model for traffic anomaly detection.
Features: bytes/s, packets/s, connections, DNS rate, circuit age.
"""

import os
import pickle
import logging
import numpy as np
from collections import deque
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger("anomaly_detector")

MODEL_PATH = "data/anomaly_model.pkl"
SCALER_PATH = "data/anomaly_scaler.pkl"


class AnomalyDetector:
    def __init__(self, threshold: float = 0.75, window: int = 100):
        self.threshold = threshold
        self.window = window
        self.model: IsolationForest = None
        self.scaler: StandardScaler = None
        self.training_buffer = deque(maxlen=500)
        self.alert_history = deque(maxlen=200)
        self.is_trained = False

    # ── Feature vector ────────────────────────────────────────────────────────

    def _feature_vector(self, sample: dict) -> list:
        return [
            sample.get("bytes_per_sec", 0),
            sample.get("packets_per_sec", 0),
            sample.get("connection_count", 0),
            sample.get("dns_query_rate", 0),
            sample.get("circuit_age_sec", 0),
            sample.get("upload_ratio", 0.5),
        ]

    # ── Model lifecycle ───────────────────────────────────────────────────────

    def load_or_train(self):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            with open(MODEL_PATH, "rb") as f:
                self.model = pickle.load(f)
            with open(SCALER_PATH, "rb") as f:
                self.scaler = pickle.load(f)
            self.is_trained = True
            logger.info("Loaded existing anomaly model from disk.")
        else:
            logger.info("No existing model found. Will train after 50 samples.")
            self._bootstrap_model()

    def _bootstrap_model(self):
        """Create a model with synthetic normal-traffic baseline data."""
        np.random.seed(42)
        normal_data = np.column_stack([
            np.random.exponential(50000, 300),   # bytes/s
            np.random.exponential(100, 300),      # packets/s
            np.random.randint(1, 20, 300),        # connections
            np.random.exponential(5, 300),        # dns rate
            np.random.uniform(0, 600, 300),       # circuit age
            np.random.uniform(0.1, 0.9, 300),     # upload ratio
        ])
        self._fit(normal_data)
        logger.info("Bootstrap model trained on synthetic baseline data.")

    def _fit(self, X: np.ndarray):
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X_scaled)
        self.is_trained = True
        self._save()

    def _save(self):
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(self.model, f)
        with open(SCALER_PATH, "wb") as f:
            pickle.dump(self.scaler, f)
        logger.info("Anomaly model saved.")

    def retrain(self):
        if len(self.training_buffer) < 50:
            logger.warning("Not enough samples to retrain.")
            return
        X = np.array([self._feature_vector(s) for s in self.training_buffer])
        self._fit(X)
        logger.info(f"Model retrained on {len(X)} samples.")

    # ── Scoring ───────────────────────────────────────────────────────────────

    def score(self, sample: dict) -> float:
        """
        Returns anomaly score in [0, 1].
        Higher = more anomalous.
        """
        self.training_buffer.append(sample)

        if not self.is_trained:
            return 0.0

        x = np.array([self._feature_vector(sample)])
        x_scaled = self.scaler.transform(x)
        # score_samples returns negative values; more negative = more anomalous
        raw = self.model.score_samples(x_scaled)[0]
        # Normalize to [0, 1]: typical range is [-0.5, 0.5]
        score = float(np.clip((-raw + 0.5) / 1.0, 0, 1))
        return score

    def is_anomalous(self, sample: dict) -> tuple:
        """Returns (is_anomaly: bool, score: float)."""
        score = self.score(sample)
        anomalous = score >= self.threshold
        if anomalous:
            alert = {
                "timestamp": datetime.now().isoformat(),
                "score": round(score, 3),
                "sample": sample
            }
            self.alert_history.appendleft(alert)
            logger.warning(f"ANOMALY DETECTED — score={score:.3f} sample={sample}")
        return anomalous, score

    def get_alerts(self, limit: int = 20) -> list:
        return list(self.alert_history)[:limit]
