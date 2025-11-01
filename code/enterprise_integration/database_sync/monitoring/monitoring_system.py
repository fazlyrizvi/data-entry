"""
Database Synchronization Monitoring System

Provides comprehensive monitoring and alerting for database synchronization.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Union, NamedTuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
import time
from collections import deque, defaultdict
from abc import ABC, abstractmethod

from ..core.change_event import ChangeEvent, EventBatch
from ..core.sync_manager import SyncManager, SyncConfiguration, SyncStatistics
from ..cdc.cdc_system import CDCSystem, CDCStatistics


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "COUNTER"
    GAUGE = "GAUGE"
    HISTOGRAM = "HISTOGRAM"
    TIMER = "TIMER"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlertStatus(Enum):
    """Alert status."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    SUPPRESSED = "SUPPRESSED"


@dataclass
class Metric:
    """A metric data point."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags,
            'type': self.metric_type.value
        }


@dataclass
class Alert:
    """An alert condition."""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    severity: AlertSeverity = AlertSeverity.WARNING
    
    # Alert conditions
    metric_name: str = ""
    condition: str = ""  # e.g., ">", "<", ">=", "<=", "=="
    threshold: float = 0.0
    duration: timedelta = field(default_factory=lambda: timedelta(seconds=60))
    
    # Alert management
    enabled: bool = True
    status: AlertStatus = AlertStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    triggered_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Alert data
    current_value: Optional[float] = None
    trigger_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'name': self.name,
            'description': self.description,
            'severity': self.severity.value,
            'metric_name': self.metric_name,
            'condition': self.condition,
            'threshold': self.threshold,
            'duration': self.duration.total_seconds(),
            'enabled': self.enabled,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'current_value': self.current_value,
            'trigger_count': self.trigger_count,
            'metadata': self.metadata
        }


class TimeSeriesPoint(NamedTuple):
    """A point in a time series."""
    timestamp: datetime
    value: float
    tags: Dict[str, str]


class TimeSeries:
    """A time series for metrics."""
    
    def __init__(self, name: str, max_points: int = 10000):
        self.name = name
        self.max_points = max_points
        self.points: deque = deque(maxlen=max_points)
        self._lock = asyncio.Lock()
    
    async def add_point(self, value: float, tags: Optional[Dict[str, str]] = None, timestamp: Optional[datetime] = None):
        """Add a point to the time series."""
        async with self._lock:
            if timestamp is None:
                timestamp = datetime.now()
            
            point = TimeSeriesPoint(timestamp=timestamp, value=value, tags=tags or {})
            self.points.append(point)
    
    async def get_range(self, start_time: datetime, end_time: datetime) -> List[TimeSeriesPoint]:
        """Get points in a time range."""
        async with self._lock:
            return [point for point in self.points if start_time <= point.timestamp <= end_time]
    
    async def get_latest(self, count: int = 1) -> List[TimeSeriesPoint]:
        """Get latest points."""
        async with self._lock:
            return list(self.points)[-count:] if count <= len(self.points) else list(self.points)
    
    async def get_aggregated(self, start_time: datetime, end_time: datetime, aggregation: str = "avg") -> float:
        """Get aggregated value for time range."""
        points = await self.get_range(start_time, end_time)
        if not points:
            return 0.0
        
        values = [point.value for point in points]
        
        if aggregation == "avg":
            return sum(values) / len(values)
        elif aggregation == "sum":
            return sum(values)
        elif aggregation == "min":
            return min(values)
        elif aggregation == "max":
            return max(values)
        elif aggregation == "count":
            return len(values)
        else:
            raise ValueError(f"Unknown aggregation: {aggregation}")


class BaseAlertHandler(ABC):
    """Abstract base class for alert handlers."""
    
    @abstractmethod
    async def handle_alert(self, alert: Alert, context: Dict[str, Any]):
        """Handle an alert."""
        pass


class LoggingAlertHandler(BaseAlertHandler):
    """Alert handler that logs alerts."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    async def handle_alert(self, alert: Alert, context: Dict[str, Any]):
        """Log the alert."""
        if alert.severity == AlertSeverity.CRITICAL:
            self.logger.critical(f"CRITICAL ALERT: {alert.name} - {alert.description}")
        elif alert.severity == AlertSeverity.ERROR:
            self.logger.error(f"ERROR ALERT: {alert.name} - {alert.description}")
        elif alert.severity == AlertSeverity.WARNING:
            self.logger.warning(f"WARNING ALERT: {alert.name} - {alert.description}")
        else:
            self.logger.info(f"INFO ALERT: {alert.name} - {alert.description}")


class WebhookAlertHandler(BaseAlertHandler):
    """Alert handler that sends alerts to webhooks."""
    
    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}
    
    async def handle_alert(self, alert: Alert, context: Dict[str, Any]):
        """Send alert to webhook."""
        import aiohttp
        
        payload = {
            'alert': alert.to_dict(),
            'context': context
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        logging.getLogger(__name__).error(f"Webhook failed with status {response.status}")
        except Exception as e:
            logging.getLogger(__name__).error(f"Webhook error: {e}")


class MonitoringSystem:
    """Database synchronization monitoring system."""
    
    def __init__(self, retention_period: timedelta = timedelta(days=7)):
        self.retention_period = retention_period
        
        # Metrics storage
        self.metrics: Dict[str, TimeSeries] = {}
        self.recent_metrics: deque = deque(maxlen=1000)
        
        # Alert management
        self.alerts: Dict[str, Alert] = {}
        self.alert_handlers: List[BaseAlertHandler] = []
        self.alert_history: deque = deque(maxlen=10000)
        
        # Monitoring tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self.performance_data = defaultdict(list)
        
        # Context data
        self.sync_manager: Optional[SyncManager] = None
        self.cdc_system: Optional[CDCSystem] = None
        
        self.logger = logging.getLogger(__name__)
        
        # Register default alert handlers
        self.add_alert_handler(LoggingAlertHandler())
    
    async def start(self):
        """Start the monitoring system."""
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.logger.info("Monitoring system started")
    
    async def stop(self):
        """Stop the monitoring system."""
        # Cancel monitoring tasks
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Monitoring system stopped")
    
    def set_sync_manager(self, sync_manager: SyncManager):
        """Set the sync manager to monitor."""
        self.sync_manager = sync_manager
    
    def set_cdc_system(self, cdc_system: CDCSystem):
        """Set the CDC system to monitor."""
        self.cdc_system = cdc_system
    
    def add_alert_handler(self, handler: BaseAlertHandler):
        """Add an alert handler."""
        self.alert_handlers.append(handler)
    
    async def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, timestamp: Optional[datetime] = None):
        """Record a metric."""
        if name not in self.metrics:
            self.metrics[name] = TimeSeries(name)
        
        await self.metrics[name].add_point(value, tags, timestamp)
        
        # Add to recent metrics for quick access
        metric = Metric(name=name, value=value, timestamp=timestamp or datetime.now(), tags=tags or {})
        self.recent_metrics.append(metric)
        
        # Check alerts
        await self._check_alerts(name, value)
    
    async def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        # Get current value
        current_value = await self._get_current_counter_value(name)
        new_value = current_value + value
        
        await self.record_metric(name, new_value, tags)
    
    async def _get_current_counter_value(self, name: str) -> float:
        """Get the current value of a counter."""
        if name in self.metrics:
            series = self.metrics[name]
            if series.points:
                return series.points[-1].value
        return 0.0
    
    async def create_alert(self, alert: Alert) -> str:
        """Create a new alert."""
        self.alerts[alert.alert_id] = alert
        self.logger.info(f"Created alert: {alert.name}")
        return alert.alert_id
    
    async def update_alert(self, alert_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing alert."""
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        for key, value in updates.items():
            if hasattr(alert, key):
                setattr(alert, key, value)
        
        alert.metadata['updated_at'] = datetime.now()
        return True
    
    async def delete_alert(self, alert_id: str) -> bool:
        """Delete an alert."""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            return True
        return False
    
    async def get_metrics(self, name: Optional[str] = None, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get metrics data."""
        if name:
            if name in self.metrics:
                series = self.metrics[name]
                if start_time and end_time:
                    points = await series.get_range(start_time, end_time)
                else:
                    points = await series.get_latest(100)
                
                return {
                    'name': name,
                    'points': [
                        {'timestamp': p.timestamp.isoformat(), 'value': p.value, 'tags': p.tags}
                        for p in points
                    ]
                }
            else:
                return {'name': name, 'points': []}
        else:
            # Return all metrics
            result = {}
            for metric_name, series in self.metrics.items():
                points = await series.get_latest(10)  # Latest 10 points
                result[metric_name] = [
                    {'timestamp': p.timestamp.isoformat(), 'value': p.value, 'tags': p.tags}
                    for p in points
                ]
            return result
    
    async def get_alerts(self, status: Optional[AlertStatus] = None) -> List[Alert]:
        """Get alerts by status."""
        alerts = list(self.alerts.values())
        if status:
            alerts = [alert for alert in alerts if alert.status == status]
        return alerts
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        summary = {
            'timestamp': now.isoformat(),
            'metrics_count': len(self.metrics),
            'active_alerts': len([a for a in self.alerts.values() if a.status == AlertStatus.ACTIVE]),
            'alerts_summary': {
                'total': len(self.alerts),
                'active': len([a for a in self.alerts.values() if a.status == AlertStatus.ACTIVE]),
                'resolved': len([a for a in self.alerts.values() if a.status == AlertStatus.RESOLVED]),
                'pending': len([a for a in self.alerts.values() if a.status == AlertStatus.PENDING])
            }
        }
        
        # Add sync manager metrics if available
        if self.sync_manager:
            try:
                global_stats = await self.sync_manager.get_global_statistics()
                summary['sync_manager'] = global_stats
            except Exception as e:
                summary['sync_manager'] = {'error': str(e)}
        
        # Add CDC system metrics if available
        if self.cdc_system:
            try:
                cdc_stats = await self.cdc_system.get_global_statistics()
                summary['cdc_system'] = cdc_stats
            except Exception as e:
                summary['cdc_system'] = {'error': str(e)}
        
        return summary
    
    async def _check_alerts(self, metric_name: str, value: float):
        """Check if any alerts should be triggered."""
        now = datetime.now()
        
        for alert in self.alerts.values():
            if not alert.enabled or alert.metric_name != metric_name:
                continue
            
            # Check condition
            condition_met = self._evaluate_condition(value, alert.condition, alert.threshold)
            
            if condition_met:
                # Start or continue tracking
                if alert.status == AlertStatus.PENDING:
                    alert.triggered_at = now
                    alert.trigger_count = 1
                    alert.status = AlertStatus.ACTIVE
                    alert.current_value = value
                    
                    # Check if duration threshold is met
                    if alert.duration.total_seconds() == 0 or (now - alert.triggered_at) >= alert.duration:
                        await self._trigger_alert(alert)
                else:
                    # Already active, just update
                    alert.current_value = value
                    alert.trigger_count += 1
            else:
                # Condition not met
                if alert.status == AlertStatus.ACTIVE:
                    alert.status = AlertStatus.RESOLVED
                    alert.resolved_at = now
                    await self._resolve_alert(alert)
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate if a condition is met."""
        if condition == ">":
            return value > threshold
        elif condition == "<":
            return value < threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "==":
            return value == threshold
        else:
            return False
    
    async def _trigger_alert(self, alert: Alert):
        """Trigger an alert."""
        self.logger.warning(f"Triggering alert: {alert.name}")
        
        # Send to all handlers
        context = {
            'alert': alert,
            'current_value': alert.current_value,
            'timestamp': datetime.now()
        }
        
        for handler in self.alert_handlers:
            try:
                await handler.handle_alert(alert, context)
            except Exception as e:
                self.logger.error(f"Alert handler error: {e}")
        
        # Add to history
        self.alert_history.append(alert)
    
    async def _resolve_alert(self, alert: Alert):
        """Resolve an alert."""
        self.logger.info(f"Resolving alert: {alert.name}")
        
        # Add to history
        self.alert_history.append(alert)
    
    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while True:
            try:
                # Collect metrics from monitored systems
                await self._collect_system_metrics()
                
                # Check for alert conditions
                await self._check_all_alerts()
                
                await asyncio.sleep(10)  # Monitor every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(30)
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(3600)  # Clean up every hour
                await self._cleanup_old_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
    
    async def _collect_system_metrics(self):
        """Collect metrics from monitored systems."""
        now = datetime.now()
        
        # Collect sync manager metrics
        if self.sync_manager:
            try:
                stats = await self.sync_manager.get_global_statistics()
                
                # Record sync-related metrics
                await self.record_metric("sync.total_configurations", stats.get('total_sync_configurations', 0))
                await self.record_metric("sync.active_syncs", stats.get('active_syncs', 0))
                await self.record_metric("sync.total_events_processed", stats.get('total_events_processed', 0))
                await self.record_metric("sync.total_errors", stats.get('total_errors', 0))
                await self.record_metric("sync.total_conflicts", stats.get('total_conflicts', 0))
                
            except Exception as e:
                await self.record_metric("sync.error_count", 1, {'error': str(e)})
        
        # Collect CDC system metrics
        if self.cdc_system:
            try:
                stats = await self.cdc_system.get_global_statistics()
                
                await self.record_metric("cdc.total_configurations", stats.get('total_cdc_configurations', 0))
                await self.record_metric("cdc.total_events_captured", stats.get('total_events_captured', 0))
                await self.record_metric("cdc.total_errors", stats.get('total_errors', 0))
                await self.record_metric("cdc.active_configurations", stats.get('active_configurations', 0))
                
            except Exception as e:
                await self.record_metric("cdc.error_count", 1, {'error': str(e)})
    
    async def _check_all_alerts(self):
        """Check all alerts for conditions."""
        # This would check historical data for alerts that need time-based evaluation
        # For now, alerts are checked when metrics are recorded
    
    async def _cleanup_old_data(self):
        """Clean up old metrics and alert history."""
        cutoff_time = datetime.now() - self.retention_period
        
        # Clean up old metrics
        for name, series in list(self.metrics.items()):
            # Remove points older than retention period
            old_points = []
            async with series._lock:
                for point in series.points:
                    if point.timestamp < cutoff_time:
                        old_points.append(point)
                
                for point in old_points:
                    series.points.remove(point)
        
        # Clean up old alert history
        while self.alert_history and self.alert_history[0].created_at < cutoff_time:
            self.alert_history.popleft()
    
    async def create_default_alerts(self):
        """Create default monitoring alerts."""
        default_alerts = [
            Alert(
                name="High Error Rate",
                description="Error rate is above normal threshold",
                severity=AlertSeverity.ERROR,
                metric_name="sync.total_errors",
                condition=">",
                threshold=10.0,
                duration=timedelta(minutes=5)
            ),
            Alert(
                name="Sync Performance Degraded",
                description="Synchronization throughput has decreased significantly",
                severity=AlertSeverity.WARNING,
                metric_name="sync.throughput_events_per_second",
                condition="<",
                threshold=1.0,
                duration=timedelta(minutes=10)
            ),
            Alert(
                name="CDC Lag Detected",
                description="CDC processing lag is above threshold",
                severity=AlertSeverity.WARNING,
                metric_name="cdc.lag_seconds",
                condition=">",
                threshold=60.0,
                duration=timedelta(minutes=5)
            ),
            Alert(
                name="Critical System Error",
                description="Critical system error detected",
                severity=AlertSeverity.CRITICAL,
                metric_name="system.critical_errors",
                condition=">",
                threshold=0.0,
                duration=timedelta(seconds=0)
            )
        ]
        
        for alert in default_alerts:
            await self.create_alert(alert)


class AdvancedMonitoringSystem(MonitoringSystem):
    """Advanced monitoring system with additional features."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Predictive analytics
        self.trend_analysis = {}
        self.anomaly_detection_enabled = True
        
        # Performance baselines
        self.baselines = {}
        
        # Custom metrics collectors
        self.custom_collectors: List[Callable] = []
        
        # Dashboard data
        self.dashboard_cache = {}
        self.dashboard_cache_ttl = 60  # seconds
    
    async def enable_anomaly_detection(self, sensitivity: float = 0.1):
        """Enable anomaly detection."""
        self.anomaly_detection_enabled = True
        self._anomaly_sensitivity = sensitivity
        
        # Create anomaly detection alerts
        await self._create_anomaly_alerts()
    
    async def add_custom_collector(self, collector_func: Callable):
        """Add a custom metrics collector."""
        self.custom_collectors.append(collector_func)
    
    async def establish_baselines(self, metric_name: str, training_period: timedelta = timedelta(days=7)):
        """Establish performance baselines for metrics."""
        if metric_name not in self.metrics:
            return
        
        series = self.metrics[metric_name]
        start_time = datetime.now() - training_period
        end_time = datetime.now()
        
        try:
            points = await series.get_range(start_time, end_time)
            if points:
                values = [point.value for point in points]
                
                self.baselines[metric_name] = {
                    'mean': sum(values) / len(values),
                    'std_dev': self._calculate_std_dev(values),
                    'min': min(values),
                    'max': max(values),
                    'training_period': training_period.total_seconds(),
                    'established_at': datetime.now()
                }
                
                self.logger.info(f"Established baseline for {metric_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to establish baseline for {metric_name}: {e}")
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    async def _create_anomaly_alerts(self):
        """Create alerts for anomaly detection."""
        anomaly_alert = Alert(
            name="Anomaly Detected",
            description="Anomalous metric behavior detected",
            severity=AlertSeverity.WARNING,
            metric_name="anomaly.score",
            condition=">",
            threshold=self._anomaly_sensitivity,
            duration=timedelta(minutes=2)
        )
        
        await self.create_alert(anomaly_alert)
    
    async def _detect_anomalies(self, metric_name: str, value: float):
        """Detect anomalies in metric values."""
        if metric_name not in self.baselines or not self.anomaly_detection_enabled:
            return
        
        baseline = self.baselines[metric_name]
        mean = baseline['mean']
        std_dev = baseline['std_dev']
        
        # Calculate z-score
        if std_dev > 0:
            z_score = abs(value - mean) / std_dev
            
            # Record anomaly score
            await self.record_metric("anomaly.score", z_score, {'metric': metric_name})
            
            # Log anomaly if significant
            if z_score > 3:  # 3-sigma rule
                self.logger.warning(f"Anomaly detected in {metric_name}: value={value}, z_score={z_score:.2f}")
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data with caching."""
        now = datetime.now()
        
        # Check cache
        if self.dashboard_cache and 'timestamp' in self.dashboard_cache:
            if (now - self.dashboard_cache['timestamp']).total_seconds() < self.dashboard_cache_ttl:
                return self.dashboard_cache['data']
        
        # Collect dashboard data
        dashboard_data = {
            'timestamp': now.isoformat(),
            'summary': await self.get_performance_summary(),
            'recent_alerts': [alert.to_dict() for alert in list(self.alert_history)[-10:]],
            'key_metrics': await self._get_key_metrics(),
            'system_health': await self._get_system_health(),
            'trends': await self._get_trend_analysis()
        }
        
        # Update cache
        self.dashboard_cache = {
            'timestamp': now,
            'data': dashboard_data
        }
        
        return dashboard_data
    
    async def _get_key_metrics(self) -> Dict[str, Any]:
        """Get key metrics for dashboard."""
        key_metrics = {}
        
        # Get latest values for important metrics
        important_metrics = [
            'sync.active_syncs',
            'sync.total_events_processed',
            'sync.total_errors',
            'cdc.total_events_captured',
            'cdc.active_configurations',
            'anomaly.score'
        ]
        
        for metric_name in important_metrics:
            if metric_name in self.metrics:
                series = self.metrics[metric_name]
                latest_points = await series.get_latest(1)
                if latest_points:
                    key_metrics[metric_name] = {
                        'value': latest_points[0].value,
                        'timestamp': latest_points[0].timestamp.isoformat()
                    }
        
        return key_metrics
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        health_score = 1.0
        health_issues = []
        
        # Check active alerts
        active_alerts = [a for a in self.alerts.values() if a.status == AlertStatus.ACTIVE]
        critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
        
        if critical_alerts:
            health_score = 0.0
            health_issues.append(f"Critical alerts: {len(critical_alerts)}")
        elif active_alerts:
            health_score = 0.7
            health_issues.append(f"Active alerts: {len(active_alerts)}")
        
        # Check error rates
        try:
            recent_errors = await self._get_recent_error_count()
            if recent_errors > 10:
                health_score = min(health_score, 0.5)
                health_issues.append(f"High error count: {recent_errors}")
        except:
            pass
        
        return {
            'score': health_score,
            'status': 'healthy' if health_score > 0.8 else 'degraded' if health_score > 0.5 else 'unhealthy',
            'issues': health_issues,
            'last_check': datetime.now().isoformat()
        }
    
    async def _get_recent_error_count(self) -> int:
        """Get count of recent errors."""
        # This would count error metrics from the last hour
        return 0  # Placeholder
    
    async def _get_trend_analysis(self) -> Dict[str, Any]:
        """Get trend analysis for key metrics."""
        trends = {}
        
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        # Analyze trends for key metrics
        for metric_name in ['sync.total_events_processed', 'sync.total_errors', 'cdc.total_events_captured']:
            if metric_name in self.metrics:
                series = self.metrics[metric_name]
                
                hour_value = await series.get_aggregated(hour_ago, now, "sum")
                day_value = await series.get_aggregated(day_ago, now, "sum")
                
                trends[metric_name] = {
                    'last_hour': hour_value,
                    'last_day': day_value,
                    'trend': 'increasing' if hour_value > day_value / 24 else 'decreasing'
                }
        
        return trends
    
    async def export_metrics(self, start_time: datetime, end_time: datetime, format: str = "json") -> str:
        """Export metrics in specified format."""
        if format == "json":
            metrics_data = {}
            for metric_name, series in self.metrics.items():
                points = await series.get_range(start_time, end_time)
                metrics_data[metric_name] = [
                    {'timestamp': p.timestamp.isoformat(), 'value': p.value, 'tags': p.tags}
                    for p in points
                ]
            return json.dumps(metrics_data, indent=2)
        
        elif format == "csv":
            # Simple CSV export
            lines = ["metric_name,timestamp,value"]
            for metric_name, series in self.metrics.items():
                points = await series.get_range(start_time, end_time)
                for point in points:
                    lines.append(f"{metric_name},{point.timestamp.isoformat()},{point.value}")
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
