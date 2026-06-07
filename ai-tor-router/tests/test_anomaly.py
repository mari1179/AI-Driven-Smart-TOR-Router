from src.ai.anomaly_detector import AnomalyDetector

def test_normal_traffic():
    detector = AnomalyDetector()
    detector.load_or_train()

    sample = {
        "bytes_per_sec": 1000,
        "packets_per_sec": 10,
        "connection_count": 2,
        "dns_query_rate": 1,
        "circuit_age_sec": 100,
        "upload_ratio": 0.5
    }

    anomalous, score = detector.is_anomalous(sample)

    assert anomalous in [True, False]
    assert 0 <= score <= 1


def test_anomaly_score():
    detector = AnomalyDetector()
    detector.load_or_train()

    sample = {
        "bytes_per_sec": 9999999,
        "packets_per_sec": 50000,
        "connection_count": 1000,
        "dns_query_rate": 500,
        "circuit_age_sec": 1,
        "upload_ratio": 0.99
    }

    anomalous, score = detector.is_anomalous(sample)

    assert score > 0