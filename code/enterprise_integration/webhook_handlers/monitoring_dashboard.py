"""
Monitoring Dashboard

Real-time monitoring dashboard for webhook handlers using Flask and Chart.js.
"""

from flask import Flask, render_template, jsonify, request
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List
import requests
from dataclasses import dataclass, asdict
import queue
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Individual metric data point"""
    timestamp: float
    value: float
    label: str = ""


class MetricsCollector:
    """Collects and stores metrics from webhook system"""
    
    def __init__(self, webhook_url: str = "http://localhost:5000", 
                 collection_interval: int = 30):
        """
        Initialize metrics collector
        
        Args:
            webhook_url: URL of webhook service
            collection_interval: Collection interval in seconds
        """
        self.webhook_url = webhook_url
        self.collection_interval = collection_interval
        self.metrics_data = {
            'requests_per_minute': [],
            'success_rate': [],
            'response_time': [],
            'rate_limit_hits': [],
            'signature_failures': [],
            'queue_size': []
        }
        self.max_data_points = 100
        self.running = False
        self.collection_thread = None
        self._lock = threading.Lock()
    
    def start(self) -> None:
        """Start metrics collection"""
        if not self.running:
            self.running = True
            self.collection_thread = threading.Thread(target=self._collect_metrics_loop, daemon=True)
            self.collection_thread.start()
            logger.info("Metrics collector started")
    
    def stop(self) -> None:
        """Stop metrics collection"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info("Metrics collector stopped")
    
    def _collect_metrics_loop(self) -> None:
        """Main metrics collection loop"""
        while self.running:
            try:
                self._collect_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                time.sleep(self.collection_interval)
    
    def _collect_metrics(self) -> None:
        """Collect metrics from webhook service"""
        try:
            response = requests.get(f"{self.webhook_url}/metrics", timeout=10)
            if response.status_code == 200:
                metrics = response.json()
                self._process_metrics(metrics)
            else:
                logger.warning(f"Failed to get metrics: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching metrics: {e}")
    
    def _process_metrics(self, metrics: Dict[str, Any]) -> None:
        """Process and store metrics"""
        timestamp = time.time()
        requests_data = metrics.get('requests', {})
        
        # Collect metrics
        self._add_metric('requests_per_minute', timestamp, requests_data.get('total', 0))
        self._add_metric('success_rate', timestamp, requests_data.get('success_rate', 0))
        self._add_metric('response_time', timestamp, requests_data.get('avg_response_time', 0))
        self._add_metric('rate_limit_hits', timestamp, requests_data.get('rate_limit_hits', 0))
        self._add_metric('signature_failures', timestamp, requests_data.get('signature_failures', 0))
        
        # Queue size
        router_stats = metrics.get('system', {}).get('router_stats', {})
        self._add_metric('queue_size', timestamp, router_stats.get('queue_size', 0))
    
    def _add_metric(self, metric_name: str, timestamp: float, value: float) -> None:
        """Add metric data point"""
        with self._lock:
            if metric_name not in self.metrics_data:
                self.metrics_data[metric_name] = []
            
            self.metrics_data[metric_name].append(MetricPoint(timestamp, value))
            
            # Limit data points
            if len(self.metrics_data[metric_name]) > self.max_data_points:
                self.metrics_data[metric_name] = self.metrics_data[metric_name][-self.max_data_points:]
    
    def get_metrics(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get collected metrics"""
        with self._lock:
            return {
                name: [
                    {
                        'timestamp': point.timestamp,
                        'value': point.value,
                        'label': point.label
                    }
                    for point in points
                ]
                for name, points in self.metrics_data.items()
            }
    
    def get_current_values(self) -> Dict[str, float]:
        """Get current metric values"""
        with self._lock:
            current = {}
            for name, points in self.metrics_data.items():
                if points:
                    current[name] = points[-1].value
                else:
                    current[name] = 0
            return current


class MonitoringDashboard:
    """Flask-based monitoring dashboard"""
    
    def __init__(self, webhook_url: str = "http://localhost:5000"):
        """
        Initialize monitoring dashboard
        
        Args:
            webhook_url: URL of webhook service
        """
        self.app = Flask(__name__)
        self.webhook_url = webhook_url
        self.metrics_collector = MetricsCollector(webhook_url)
        
        self._setup_routes()
    
    def _setup_routes(self) -> None:
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/metrics')
        def get_metrics():
            """API endpoint for metrics data"""
            return jsonify(self.metrics_collector.get_metrics())
        
        @self.app.route('/api/current')
        def get_current():
            """API endpoint for current metric values"""
            return jsonify(self.metrics_collector.get_current_values())
        
        @self.app.route('/api/health')
        def health():
            """API endpoint for dashboard health"""
            try:
                response = requests.get(f"{self.webhook_url}/health", timeout=5)
                webhook_status = "healthy" if response.status_code == 200 else "unhealthy"
            except Exception:
                webhook_status = "unreachable"
            
            return jsonify({
                'dashboard': 'healthy',
                'webhook_service': webhook_status,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.app.route('/api/endpoints')
        def get_endpoints():
            """API endpoint for endpoint information"""
            try:
                response = requests.get(f"{self.webhook_url}/admin/endpoints", timeout=5)
                if response.status_code == 200:
                    return jsonify(response.json())
                else:
                    return jsonify({'error': 'Failed to get endpoints'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def start(self, host: str = '127.0.0.1', port: int = 5001, debug: bool = False) -> None:
        """
        Start monitoring dashboard
        
        Args:
            host: Host to bind to
            port: Port to listen on
            debug: Enable debug mode
        """
        # Start metrics collection
        self.metrics_collector.start()
        
        logger.info(f"Starting monitoring dashboard on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


# Template for the dashboard (embedded for standalone execution)
dashboard_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Webhook Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
        }
        .status {
            display: flex;
            justify-content: space-around;
            margin-bottom: 30px;
        }
        .status-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
            min-width: 120px;
        }
        .status-value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        .status-label {
            color: #666;
            margin-top: 5px;
        }
        .charts {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .chart-title {
            text-align: center;
            margin-bottom: 15px;
            color: #333;
            font-weight: bold;
        }
        .endpoints {
            margin-top: 30px;
        }
        .endpoint-card {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .endpoint-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .endpoint-name {
            font-weight: bold;
            color: #333;
        }
        .endpoint-status {
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.9em;
        }
        .status-enabled {
            background-color: #d4edda;
            color: #155724;
        }
        .status-disabled {
            background-color: #f8d7da;
            color: #721c24;
        }
        .endpoint-metrics {
            display: flex;
            gap: 20px;
            margin-top: 10px;
            font-size: 0.9em;
            color: #666;
        }
        .refresh-button {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #667eea;
            color: white;
            border: none;
            padding: 15px 20px;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            font-size: 16px;
        }
        .error {
            background-color: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Webhook Monitoring Dashboard</h1>
        <p>Real-time monitoring for webhook handlers</p>
    </div>

    <div class="status">
        <div class="status-card">
            <div class="status-value" id="total-requests">0</div>
            <div class="status-label">Total Requests</div>
        </div>
        <div class="status-card">
            <div class="status-value" id="success-rate">0%</div>
            <div class="status-label">Success Rate</div>
        </div>
        <div class="status-card">
            <div class="status-value" id="avg-response-time">0ms</div>
            <div class="status-label">Avg Response Time</div>
        </div>
        <div class="status-card">
            <div class="status-value" id="queue-size">0</div>
            <div class="status-label">Queue Size</div>
        </div>
    </div>

    <div class="charts">
        <div class="chart-container">
            <div class="chart-title">Requests Over Time</div>
            <canvas id="requests-chart"></canvas>
        </div>
        <div class="chart-container">
            <div class="chart-title">Success Rate</div>
            <canvas id="success-rate-chart"></canvas>
        </div>
        <div class="chart-container">
            <div class="chart-title">Response Time</div>
            <canvas id="response-time-chart"></canvas>
        </div>
        <div class="chart-container">
            <div class="chart-title">Rate Limit Hits</div>
            <canvas id="rate-limit-chart"></canvas>
        </div>
    </div>

    <div class="endpoints">
        <h2>📡 Endpoint Status</h2>
        <div id="endpoints-container">
            <p>Loading endpoints...</p>
        </div>
    </div>

    <button class="refresh-button" onclick="refreshData()">🔄</button>

    <script>
        // Initialize charts
        const charts = {};
        const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'];

        function initCharts() {
            // Requests chart
            const requestsCtx = document.getElementById('requests-chart').getContext('2d');
            charts.requests = new Chart(requestsCtx, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'Requests', data: [], borderColor: colors[0], tension: 0.1 }] },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });

            // Success rate chart
            const successCtx = document.getElementById('success-rate-chart').getContext('2d');
            charts.success = new Chart(successCtx, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'Success Rate (%)', data: [], borderColor: colors[1], tension: 0.1 }] },
                options: { responsive: true, scales: { y: { beginAtZero: true, max: 100 } } }
            });

            // Response time chart
            const responseCtx = document.getElementById('response-time-chart').getContext('2d');
            charts.response = new Chart(responseCtx, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'Response Time (ms)', data: [], borderColor: colors[2], tension: 0.1 }] },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });

            // Rate limit chart
            const rateLimitCtx = document.getElementById('rate-limit-chart').getContext('2d');
            charts.rateLimit = new Chart(rateLimitCtx, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'Rate Limit Hits', data: [], borderColor: colors[3], tension: 0.1 }] },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });
        }

        function updateStatus(metrics) {
            document.getElementById('total-requests').textContent = metrics.total_requests || 0;
            document.getElementById('success-rate').textContent = (metrics.success_rate || 0).toFixed(1) + '%';
            document.getElementById('avg-response-time').textContent = ((metrics.response_time || 0) * 1000).toFixed(0) + 'ms';
            document.getElementById('queue-size').textContent = metrics.queue_size || 0;
        }

        function updateChart(chart, timestamps, data, label) {
            const labels = timestamps.map(t => new Date(t * 1000).toLocaleTimeString());
            chart.data.labels = labels;
            chart.data.datasets[0].data = data;
            chart.update('none');
        }

        function refreshData() {
            // Get current metrics
            fetch('/api/current')
                .then(response => response.json())
                .then(data => updateStatus(data))
                .catch(error => console.error('Error fetching current metrics:', error));

            // Get historical metrics
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    updateChart(charts.requests, 
                               data.requests_per_minute.map(p => p.timestamp),
                               data.requests_per_minute.map(p => p.value),
                               'Requests');
                    updateChart(charts.success,
                               data.success_rate.map(p => p.timestamp),
                               data.success_rate.map(p => p.value),
                               'Success Rate');
                    updateChart(charts.response,
                               data.response_time.map(p => p.timestamp),
                               data.response_time.map(p => p.value * 1000), // Convert to ms
                               'Response Time');
                    updateChart(charts.rateLimit,
                               data.rate_limit_hits.map(p => p.timestamp),
                               data.rate_limit_hits.map(p => p.value),
                               'Rate Limit Hits');
                })
                .catch(error => console.error('Error fetching metrics:', error));

            // Get endpoints
            fetch('/api/endpoints')
                .then(response => response.json())
                .then(data => updateEndpoints(data))
                .catch(error => console.error('Error fetching endpoints:', error));
        }

        function updateEndpoints(endpoints) {
            const container = document.getElementById('endpoints-container');
            
            if (Object.keys(endpoints).length === 0) {
                container.innerHTML = '<p>No endpoints configured.</p>';
                return;
            }

            let html = '';
            for (const [id, endpoint] of Object.entries(endpoints)) {
                const statusClass = endpoint.enabled ? 'status-enabled' : 'status-disabled';
                const statusText = endpoint.enabled ? 'Enabled' : 'Disabled';
                const metrics = endpoint.metrics || {};
                
                html += `
                    <div class="endpoint-card">
                        <div class="endpoint-header">
                            <div class="endpoint-name">${id}</div>
                            <div class="endpoint-status ${statusClass}">${statusText}</div>
                        </div>
                        <div class="endpoint-metrics">
                            <span>Provider: ${endpoint.provider}</span>
                            <span>Requests: ${metrics.total_requests || 0}</span>
                            <span>Success: ${metrics.successful_requests || 0}</span>
                            <span>Failed: ${metrics.failed_requests || 0}</span>
                        </div>
                    </div>
                `;
            }
            
            container.innerHTML = html;
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            initCharts();
            refreshData();
            
            // Auto-refresh every 30 seconds
            setInterval(refreshData, 30000);
        });
    </script>
</body>
</html>
"""


def create_templates_directory():
    """Create templates directory with dashboard template"""
    import os
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    dashboard_file = os.path.join(templates_dir, 'dashboard.html')
    if not os.path.exists(dashboard_file):
        with open(dashboard_file, 'w') as f:
            f.write(dashboard_template)
        print(f"Created dashboard template: {dashboard_file}")


if __name__ == '__main__':
    # Create templates directory
    create_templates_directory()
    
    # Start monitoring dashboard
    dashboard = MonitoringDashboard()
    dashboard.start(debug=True)
