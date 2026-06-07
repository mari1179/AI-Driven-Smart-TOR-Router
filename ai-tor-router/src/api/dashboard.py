"""
Flask Web Dashboard — real-time monitoring UI.
"""

import time
from flask import Flask, render_template_string, jsonify
from .routes import register_routes

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Tor Router — Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #0a0e1a;
    --card: #111827;
    --border: #1e293b;
    --accent: #7c3aed;
    --green: #10b981;
    --red: #ef4444;
    --orange: #f59e0b;
    --text: #e2e8f0;
    --muted: #64748b;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'Courier New', monospace; min-height: 100vh; }
  header { background: var(--card); border-bottom: 1px solid var(--border); padding: 1rem 2rem;
           display: flex; align-items: center; gap: 1rem; }
  header h1 { font-size: 1.25rem; color: var(--accent); letter-spacing: 2px; text-transform: uppercase; }
  .badge { padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.75rem; font-weight: bold; }
  .badge.healthy { background: #065f46; color: var(--green); }
  .badge.down { background: #7f1d1d; color: var(--red); }
  .badge.degraded { background: #78350f; color: var(--orange); }
  main { padding: 1.5rem 2rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.25rem; }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; }
  .card h2 { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.75rem; }
  .stat { font-size: 1.75rem; font-weight: bold; color: var(--accent); }
  .sub { font-size: 0.8rem; color: var(--muted); margin-top: 0.25rem; }
  .wide { grid-column: 1 / -1; }
  canvas { max-height: 180px; }
  button.rotate-btn {
    background: var(--accent); color: white; border: none; padding: 0.6rem 1.25rem;
    border-radius: 8px; cursor: pointer; font-family: inherit; font-size: 0.85rem;
    letter-spacing: 1px; text-transform: uppercase; transition: opacity 0.2s;
  }
  button.rotate-btn:hover { opacity: 0.8; }
  .alert-item { padding: 0.5rem; border-left: 3px solid var(--red); margin-bottom: 0.5rem;
                background: #1c0a0a; border-radius: 0 6px 6px 0; font-size: 0.78rem; }
  .alert-item .score { color: var(--red); font-weight: bold; }
  .log-box { background: #070b14; border: 1px solid var(--border); border-radius: 8px;
             padding: 0.75rem; height: 160px; overflow-y: auto; font-size: 0.75rem; color: #94a3b8; }
  .threat { font-size: 2rem; font-weight: bold; }
  .threat.LOW { color: var(--green); }
  .threat.MEDIUM { color: var(--orange); }
  .threat.HIGH, .threat.CRITICAL { color: var(--red); }
  footer { text-align: center; padding: 1rem; color: var(--muted); font-size: 0.7rem; }
</style>
</head>
<body>
<header>
  <h1>🧅 AI Tor Router</h1>
  <span class="badge" id="status-badge">loading...</span>
  <span style="margin-left:auto; color:var(--muted); font-size:0.8rem;" id="clock"></span>
</header>

<main>
  <!-- Exit IP -->
  <div class="card">
    <h2>Current Exit Node</h2>
    <div class="stat" id="exit-ip">—</div>
    <div class="sub" id="exit-country">Fetching...</div>
  </div>

  <!-- Circuits rotated -->
  <div class="card">
    <h2>Circuits Rotated</h2>
    <div class="stat" id="rotation-count">0</div>
    <div class="sub" id="last-rotation">Last: —</div>
  </div>

  <!-- Threat level -->
  <div class="card">
    <h2>Threat Level</h2>
    <div class="threat LOW" id="threat-level">LOW</div>
    <div class="sub" id="threat-score">Score: 0.000</div>
  </div>

  <!-- Manual rotate -->
  <div class="card">
    <h2>Manual Control</h2>
    <button class="rotate-btn" onclick="rotateNow()">⟳ Rotate Circuit</button>
    <div class="sub" style="margin-top:0.5rem;" id="rotate-msg"></div>
  </div>

  <!-- Bandwidth chart -->
  <div class="card wide">
    <h2>Bandwidth (KB/s)</h2>
    <canvas id="bwChart"></canvas>
  </div>

  <!-- Anomaly score chart -->
  <div class="card wide">
    <h2>Anomaly Score History</h2>
    <canvas id="anomalyChart"></canvas>
  </div>

  <!-- Alerts -->
  <div class="card">
    <h2>Anomaly Alerts</h2>
    <div id="alerts-feed">No alerts.</div>
  </div>

  <!-- Health / incidents -->
  <div class="card">
    <h2>Auto-Heal Log</h2>
    <div class="log-box" id="heal-log">No incidents.</div>
  </div>
</main>

<footer>AI-Driven Smart Tor Router — Raspberry Pi Project</footer>

<script>
const bwCtx = document.getElementById('bwChart').getContext('2d');
const anomalyCtx = document.getElementById('anomalyChart').getContext('2d');

const bwChart = new Chart(bwCtx, {
  type: 'line',
  data: { labels: [], datasets: [
    { label: 'Download KB/s', data: [], borderColor: '#7c3aed', fill: true, backgroundColor: 'rgba(124,58,237,0.1)', tension: 0.4, pointRadius: 0 },
    { label: 'Upload KB/s', data: [], borderColor: '#10b981', fill: true, backgroundColor: 'rgba(16,185,129,0.1)', tension: 0.4, pointRadius: 0 }
  ]},
  options: { animation: false, scales: { x: { display: false }, y: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' } } }, plugins: { legend: { labels: { color: '#94a3b8', boxWidth: 12 } } } }
});

const anomalyChart = new Chart(anomalyCtx, {
  type: 'line',
  data: { labels: [], datasets: [
    { label: 'Anomaly Score', data: [], borderColor: '#ef4444', fill: true, backgroundColor: 'rgba(239,68,68,0.1)', tension: 0.4, pointRadius: 0 },
  ]},
  options: { animation: false, scales: { x: { display: false }, y: { min: 0, max: 1, ticks: { color: '#64748b' }, grid: { color: '#1e293b' } } }, plugins: { legend: { labels: { color: '#94a3b8', boxWidth: 12 } } } }
});

function fmt(ts) {
  return new Date(ts * 1000).toLocaleTimeString();
}

async function refresh() {
  const res = await fetch('/api/status');
  const d = await res.json();

  // Status badge
  const badge = document.getElementById('status-badge');
  badge.textContent = d.health.status;
  badge.className = 'badge ' + d.health.status;

  // Exit IP
  document.getElementById('exit-ip').textContent = d.circuit.current_ip || '—';
  document.getElementById('rotation-count').textContent = d.circuit.rotation_count;
  document.getElementById('last-rotation').textContent = 'Last: ' + (d.circuit.last_rotation ? new Date(d.circuit.last_rotation * 1000).toLocaleTimeString() : '—');

  // Threat
  const tl = d.threat.level;
  const tlEl = document.getElementById('threat-level');
  tlEl.textContent = tl;
  tlEl.className = 'threat ' + tl;
  document.getElementById('threat-score').textContent = 'Score: ' + d.threat.score.toFixed(3);

  // Bandwidth chart
  const bw = d.bandwidth.slice(-40);
  bwChart.data.labels = bw.map(x => fmt(x.t));
  bwChart.data.datasets[0].data = bw.map(x => x.down);
  bwChart.data.datasets[1].data = bw.map(x => x.up);
  bwChart.update();

  // Anomaly chart
  const an = d.anomaly_scores.slice(-40);
  anomalyChart.data.labels = an.map(x => fmt(x.t));
  anomalyChart.data.datasets[0].data = an.map(x => x.score);
  anomalyChart.update();

  // Alerts
  const alertsEl = document.getElementById('alerts-feed');
  if (d.alerts.length === 0) {
    alertsEl.innerHTML = '<div style="color:var(--green);font-size:0.8rem;">✓ No anomalies detected</div>';
  } else {
    alertsEl.innerHTML = d.alerts.slice(0, 5).map(a =>
      `<div class="alert-item"><span class="score">⚠ ${a.score}</span> — ${new Date(a.timestamp).toLocaleTimeString()}</div>`
    ).join('');
  }

  // Heal log
  const healEl = document.getElementById('heal-log');
  if (d.incidents.length === 0) {
    healEl.textContent = 'No incidents.';
  } else {
    healEl.innerHTML = d.incidents.map(i =>
      `[${i.timestamp}] ${i.reason} → ${i.resolved ? '✓ resolved' : '✗ unresolved'}`
    ).join('<br>');
  }
}

async function rotateNow() {
  document.getElementById('rotate-msg').textContent = 'Rotating...';
  await fetch('/api/rotate', { method: 'POST' });
  document.getElementById('rotate-msg').textContent = 'Done! New circuit active.';
  setTimeout(() => { document.getElementById('rotate-msg').textContent = ''; }, 4000);
  refresh();
}

// Clock
setInterval(() => {
  document.getElementById('clock').textContent = new Date().toLocaleString();
}, 1000);

// Refresh every 5s
setInterval(refresh, 5000);
refresh();
</script>
</body>
</html>
"""


def create_app(tor_controller, circuit_manager, traffic_monitor, anomaly_detector, health_checker):
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template_string(DASHBOARD_HTML)

    register_routes(app, tor_controller, circuit_manager, traffic_monitor, anomaly_detector, health_checker)
    return app
