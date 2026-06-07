"""
REST API routes for the dashboard.
"""

import time
from flask import jsonify, request
from ai.threat_scorer import ThreatScorer

_threat_scorer = ThreatScorer()


def register_routes(app, tor, circuit_mgr, monitor, detector, health):

    @app.route("/api/status")
    def status():
        # Current traffic stats
        stats = monitor.current_stats

        # Threat score
        anomaly_score = detector.score(stats) if stats else 0.0
        threat = _threat_scorer.compute(
            anomaly_score=anomaly_score,
            latency_ms=stats.get("latency_ms", 500),
            connection_count=stats.get("connection_count", 0),
            dns_rate=stats.get("dns_query_rate", 0)
        )

        return jsonify({
            "health": health.check(),
            "circuit": {
                "current_ip": circuit_mgr.current_ip,
                "rotation_count": circuit_mgr.rotation_count,
                "last_rotation": circuit_mgr.last_rotation,
                "history": circuit_mgr.get_history()[:10]
            },
            "threat": threat,
            "bandwidth": monitor.get_bandwidth_history(),
            "anomaly_scores": monitor.get_anomaly_history(),
            "alerts": detector.get_alerts(limit=10),
            "incidents": health.get_incidents()
        })

    @app.route("/api/rotate", methods=["POST"])
    def rotate():
        event = circuit_mgr.rotate(reason="manual")
        return jsonify({
            "success": True,
            "new_ip": event.new_ip,
            "latency_ms": event.latency_ms
        })

    @app.route("/api/health")
    def health_check():
        return jsonify(health.check())

    @app.route("/api/alerts")
    def alerts():
        limit = int(request.args.get("limit", 20))
        return jsonify(detector.get_alerts(limit=limit))

    @app.route("/api/circuits")
    def circuits():
        return jsonify(circuit_mgr.get_history())

    @app.route("/api/retrain", methods=["POST"])
    def retrain():
        detector.retrain()
        return jsonify({"success": True, "message": "Model retrained."})
