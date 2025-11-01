# Monitoring System Setup Guide

## Overview

This monitoring system provides comprehensive monitoring and metrics collection for your automation system. It includes:

- **Processing Metrics**: Track task execution times, throughput, and performance
- **Error Tracking**: Log and categorize errors with detailed context
- **Performance Monitoring**: System metrics like CPU, memory, response times
- **System Health**: Overall system status and availability tracking
- **Queue Monitoring**: Processing queue status and backlog management
- **Automated Alerting**: Real-time alerts for critical issues

## Architecture

### Database Tables

1. **processing_metrics** - Task execution tracking
2. **error_tracking** - Comprehensive error logging
3. **performance_monitoring** - System performance metrics
4. **system_health** - Service health status
5. **queue_monitoring** - Queue performance tracking
6. **alerts** - Automated alerting system

### Dashboard Views

Pre-aggregated views for dashboard visualization:
- `v_realtime_processing_status` - Current task processing status
- `v_error_summary` - Error trends and summaries
- `v_system_health_summary` - Component health overview
- `v_queue_performance` - Queue status and performance
- `v_performance_trends` - Performance metric trends
- `v_active_alerts` - Current active alerts

## Installation

### 1. Database Setup

Run the main migration file to create all monitoring tables and functions:

```sql
-- Connect to your database
\c your_automation_db

-- Run the main monitoring migration
\i /path/to/supabase/monitoring/000_main_migration.sql
```

Alternatively, run individual migration files in order:

```sql
\i '001_create_processing_metrics.sql'
\i '002_create_error_tracking.sql'
\i '003_create_performance_monitoring.sql'
\i '004_create_system_health.sql'
\i '005_create_queue_monitoring.sql'
\i '006_create_alerts.sql'
\i '007_create_dashboard_views.sql'
\i '008_alerting_functions.sql'
\i '009_automated_monitoring.sql'
\i '010_monitoring_procedures.sql'
```

### 2. Verify Installation

Run the setup verification function:

```sql
SELECT setup_monitoring_maintenance();
```

This will display available functions and confirm the system is properly configured.

## Configuration

### Alert Thresholds

Edit `monitoring_config.json` to configure alert thresholds:

```json
{
  "alert_thresholds": {
    "error_rates": {
      "critical": 100,  // Errors per hour
      "high": 75,
      "medium": 50,
      "low": 25
    },
    "processing_times": {
      "critical": 900,  // Seconds
      "high": 600,
      "medium": 300,
      "low": 180
    },
    "queue_backlog": {
      "critical": 500,  // Pending tasks
      "high": 200,
      "medium": 100,
      "low": 50
    }
  }
}
```

### Notification Channels

Configure notification channels for alerts:

```json
{
  "notification_channels": {
    "email": {
      "enabled": true,
      "recipients": ["admin@example.com"]
    },
    "slack": {
      "enabled": true,
      "webhook_url": "YOUR_SLACK_WEBHOOK"
    }
  }
}
```

## Integration Guide

### Python Integration

Use the provided `MonitoringClient` class to integrate with your applications:

```python
from monitoring_client import MonitoringClient

# Initialize client
monitor = MonitoringClient("postgresql://user:pass@host:5432/db")

# Start task tracking
task_id = monitor.start_task(
    task_type="document_processing",
    input_size=1024,
    worker_id="worker-001"
)

# Complete task
monitor.complete_task(
    task_id=task_id,
    status="completed",
    output_size=2048,
    processing_steps={
        "preprocessing": 1.2,
        "analysis": 3.4,
        "postprocessing": 0.8
    }
)
```

### Error Tracking

Record errors with detailed context:

```python
# Record an error
error_id = monitor.record_error(
    task_id=task_id,
    error_type="validation_error",
    error_category="medium",
    error_message="Invalid document format",
    component="processor",
    user_impact="minor",
    error_details={
        "file_type": "pdf",
        "file_size": 1024,
        "validation_rules": ["format", "size"]
    }
)
```

### Performance Monitoring

Record performance metrics:

```python
# Record CPU usage
monitor.record_performance_metric(
    metric_name="cpu_usage",
    metric_type="cpu",
    metric_value=45.2,
    metric_unit="%",
    component="system",
    tags={"host": "server-01"}
)

# Record response time
monitor.record_performance_metric(
    metric_name="api_response_time",
    metric_type="response_time",
    metric_value=125.5,
    metric_unit="ms",
    component="api",
    tags={"endpoint": "/api/process"}
)
```

### System Health

Update system health status:

```python
# Update health status
monitor.update_system_health(
    component="api",
    service_name="main_api",
    health_status="healthy",
    response_time_ms=45
)

# Report unhealthy status
monitor.update_system_health(
    component="database",
    service_name="postgres",
    health_status="unhealthy",
    failure_reason="Connection timeout"
)
```

## Automated Monitoring

### Health Checks

Run periodic health checks:

```python
# Run health checks
monitor.run_health_checks()

# This automatically:
# - Checks database connectivity
# - Updates component health status
# - Records health metrics
```

### Alert Checks

Run automated alert checks:

```python
# Run alert checks
monitor.run_alert_checks()

# This automatically:
# - Checks error rates
# - Analyzes processing performance
# - Validates system health
# - Monitors queue backlogs
# - Resolves resolved alerts
```

## Dashboard Views

### Real-time Dashboard

Get dashboard summary data:

```sql
SELECT get_dashboard_summary();
```

Returns JSON with:
- Active tasks count
- Completed tasks today
- Error count today
- System health score
- Queue backlog total
- Active alerts count

### Custom Queries

Use the pre-built views for custom dashboards:

```sql
-- Current processing status
SELECT * FROM v_realtime_processing_status;

-- Error trends (last 24 hours)
SELECT * FROM v_error_summary;

-- System health overview
SELECT * FROM v_system_health_summary;

-- Queue performance
SELECT * FROM v_queue_performance;

-- Performance trends
SELECT * FROM v_performance_trends;

-- Active alerts
SELECT * FROM v_active_alerts;
```

## Maintenance

### Data Cleanup

Clean up old monitoring data:

```sql
SELECT cleanup_old_monitoring_data();
```

Configurable retention periods (in `monitoring_config.json`):
- Processing metrics: 30 days
- Error tracking: 30-90 days (depending on severity)
- Performance metrics: 7 days
- Resolved alerts: 7 days

### Performance Optimization

Create additional indexes for better query performance:

```sql
-- Task-specific indexes
CREATE INDEX CONCURRENTLY idx_processing_metrics_task_id 
ON processing_metrics(task_id);

CREATE INDEX CONCURRENTLY idx_error_tracking_task_id 
ON error_tracking(task_id);

-- Time-based indexes
CREATE INDEX CONCURRENTLY idx_processing_metrics_hour 
ON processing_metrics(DATE_TRUNC('hour', start_time));

CREATE INDEX CONCURRENTLY idx_error_tracking_hour 
ON error_tracking(DATE_TRUNC('hour', occurred_at));
```

## Monitoring Best Practices

### 1. Task Tracking

Always wrap task execution with monitoring:

```python
task_id = monitor.start_task(
    task_type="your_task_type",
    input_size=input_data_size,
    metadata={"user_id": user_id, "priority": priority}
)

try:
    # Your task logic here
    result = process_data()
    
    monitor.complete_task(
        task_id=task_id,
        status="completed",
        output_size=len(result),
        processing_steps={
            "step1": 1.2,
            "step2": 3.4,
            "step3": 0.8
        }
    )
    
except Exception as e:
    monitor.complete_task(task_id, "failed")
    monitor.record_error(
        task_id=task_id,
        error_type="processing_error",
        error_message=str(e),
        component="processor"
    )
    raise
```

### 2. Error Categorization

Use consistent error categories:

- **Critical**: System-wide failures, security issues
- **High**: Service degradation, data corruption
- **Medium**: Processing failures, validation errors
- **Low**: Minor issues, warnings

### 3. Performance Metrics

Record meaningful metrics:

```python
import psutil
import time

# At task start
start_time = time.time()
start_memory = psutil.virtual_memory().percent

# At task completion
duration = time.time() - start_time
end_memory = psutil.virtual_memory().percent

monitor.record_performance_metric(
    metric_name="task_duration",
    metric_type="response_time",
    metric_value=duration,
    metric_unit="seconds",
    component="processor",
    tags={"task_type": "document_processing"}
)
```

### 4. Health Monitoring

Implement health checks for all components:

```python
def check_api_health():
    try:
        response = requests.get("http://api/health", timeout=5)
        if response.status_code == 200:
            monitor.update_system_health("api", "main_api", "healthy", 
                                       response_time=response.elapsed.total_seconds() * 1000)
        else:
            monitor.update_system_health("api", "main_api", "degraded", 
                                       failure_reason=f"Status code: {response.status_code}")
    except Exception as e:
        monitor.update_system_health("api", "main_api", "unhealthy", 
                                   failure_reason=str(e))
```

## Troubleshooting

### Common Issues

1. **High Alert Volume**
   - Review threshold configurations
   - Check for systematic issues
   - Implement alert suppression rules

2. **Performance Degradation**
   - Monitor query performance
   - Add missing indexes
   - Clean up old data regularly

3. **Missing Metrics**
   - Verify monitoring integration
   - Check function permissions
   - Review error logs

### Debug Queries

```sql
-- Check recent errors
SELECT * FROM error_tracking 
WHERE occurred_at >= NOW() - INTERVAL '1 hour'
ORDER BY occurred_at DESC;

-- Monitor task performance
SELECT task_type, execution_status, COUNT(*), AVG(duration_seconds)
FROM processing_metrics
WHERE start_time >= NOW() - INTERVAL '1 hour'
GROUP BY task_type, execution_status;

-- System health status
SELECT component, service_name, health_status, last_check
FROM system_health
ORDER BY component, service_name;
```

## API Reference

### Core Functions

- `start_task_tracking()` - Begin task monitoring
- `complete_task_tracking()` - Complete task monitoring
- `record_error()` - Log an error
- `record_performance_metrics()` - Record performance data
- `update_system_health()` - Update health status
- `get_dashboard_summary()` - Get dashboard data

### Alert Functions

- `check_error_rate_alerts()` - Generate error rate alerts
- `check_processing_performance_alerts()` - Generate performance alerts
- `check_system_health_alerts()` - Generate health alerts
- `check_queue_backlog_alerts()` - Generate queue alerts
- `resolve_resolved_alerts()` - Auto-resolve resolved alerts

### Maintenance Functions

- `cleanup_old_monitoring_data()` - Clean up old data
- `calculate_queue_metrics()` - Update queue statistics

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the monitoring logs
3. Verify database connection and permissions
4. Test monitoring functions manually

The monitoring system is designed to be robust and self-healing, but manual intervention may be required for complex issues.