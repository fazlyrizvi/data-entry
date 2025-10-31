# Automation System Monitoring

Comprehensive monitoring and metrics collection system for automation workflows.

## Quick Start

1. **Setup Database Schema**
   ```bash
   # Run the main migration
   psql -d your_automation_db -f 000_main_migration.sql
   ```

2. **Configure Alert Thresholds**
   ```bash
   # Edit configuration
   nano monitoring_config.json
   ```

3. **Integrate with Your Application**
   ```python
   from integration_example import MonitoringClient
   
   monitor = MonitoringClient("postgresql://user:pass@host:5432/db")
   task_id = monitor.start_task("my_task", input_size=1024)
   # ... your processing logic ...
   monitor.complete_task(task_id, "completed")
   ```

## What's Included

### Database Schema
- **6 Core Tables**: processing_metrics, error_tracking, performance_monitoring, system_health, queue_monitoring, alerts
- **6 Dashboard Views**: Pre-aggregated views for visualization
- **20+ Functions**: Automated monitoring, alerting, and maintenance functions

### Features
- ✅ Real-time processing metrics tracking
- ✅ Comprehensive error logging and categorization
- ✅ System performance monitoring (CPU, memory, response times)
- ✅ Service health status tracking
- ✅ Queue monitoring and backlog management
- ✅ Automated alerting for critical issues
- ✅ Dashboard-ready views and data
- ✅ Python integration client
- ✅ Automated maintenance and cleanup

### Files Created

#### Database Migrations (supabase/monitoring/)
```
000_main_migration.sql              # Main migration orchestrator
001_create_processing_metrics.sql   # Task execution tracking
002_create_error_tracking.sql       # Error logging system
003_create_performance_monitoring.sql # Performance metrics
004_create_system_health.sql        # Service health tracking
005_create_queue_monitoring.sql     # Queue performance
006_create_alerts.sql               # Alert management
007_create_dashboard_views.sql      # Dashboard views
008_alerting_functions.sql          # Automated alerting
009_automated_monitoring.sql        # Monitoring functions
010_monitoring_procedures.sql       # Integration procedures
```

#### Configuration
```
monitoring_config.json              # Alert thresholds and settings
```

#### Integration
```
integration_example.py              # Python client library
```

#### Documentation
```
/workspace/docs/monitoring_setup.md  # Complete setup guide
README.md                           # This file
```

## Key Functions

### Task Monitoring
```sql
SELECT start_task_tracking('task-123', 'document_processing', 1024, 'worker-01');
SELECT complete_task_tracking('task-123', 'completed', 2048, '{"step1": 1.2}');
```

### Error Tracking
```sql
SELECT record_error('task-123', 'validation_error', 'medium', 'Invalid input', 'processor');
```

### System Health
```sql
SELECT update_system_health('api', 'main_api', 'healthy', 50);
```

### Dashboard Data
```sql
SELECT get_dashboard_summary();  -- Returns JSON dashboard summary
```

### Automated Checks
```sql
SELECT check_error_rate_alerts();
SELECT check_processing_performance_alerts();
SELECT check_system_health_alerts();
SELECT check_queue_backlog_alerts();
SELECT resolve_resolved_alerts();
SELECT cleanup_old_monitoring_data();
```

## Dashboard Views

- `v_realtime_processing_status` - Current task status
- `v_error_summary` - Error trends (24h)
- `v_system_health_summary` - Component health
- `v_queue_performance` - Queue statistics
- `v_performance_trends` - Performance trends
- `v_active_alerts` - Current alerts

## Monitoring Workflow

### 1. Task Lifecycle
1. Start: `start_task_tracking()` called when task begins
2. Processing: Performance metrics recorded during execution
3. Complete: `complete_task_tracking()` called when task finishes
4. Analysis: Automated checks run periodically

### 2. Error Handling
1. Error occurs: `record_error()` logs the error
2. Categorization: Error classified by type and severity
3. Alerting: Automated alerts generated based on thresholds
4. Resolution: Alerts auto-resolve when conditions improve

### 3. Health Monitoring
1. Periodic checks: Health status updated regularly
2. Alert generation: Unhealthy components trigger alerts
3. Recovery tracking: Uptime calculated when health restored

### 4. Performance Tracking
1. Metrics collection: Performance data recorded continuously
2. Trend analysis: Historical data used for capacity planning
3. Threshold alerts: Performance degradation triggers alerts

## Configuration

### Alert Thresholds (monitoring_config.json)
```json
{
  "alert_thresholds": {
    "error_rates": {
      "critical": 100,    // errors per hour
      "high": 75,
      "medium": 50,
      "low": 25
    },
    "processing_times": {
      "critical": 900,    // seconds
      "high": 600,
      "medium": 300,
      "low": 180
    },
    "queue_backlog": {
      "critical": 500,    // pending tasks
      "high": 200,
      "medium": 100,
      "low": 50
    }
  }
}
```

### Data Retention
- Processing metrics: 30 days
- Error tracking: 30-90 days (by severity)
- Performance metrics: 7 days
- Resolved alerts: 7 days

## Integration Examples

### Simple Task Tracking
```python
from monitoring_client import MonitoringClient

monitor = MonitoringClient("postgresql://...")

# Start tracking
task_id = monitor.start_task("document_processing", 1024)

try:
    # Your processing logic
    result = process_document()
    
    # Success
    monitor.complete_task(task_id, "completed", output_size=len(result))
    
except Exception as e:
    # Failure
    monitor.complete_task(task_id, "failed")
    monitor.record_error(task_id, "processing_error", "medium", str(e), "processor")
```

### Performance Monitoring
```python
import time
import psutil

start = time.time()
start_mem = psutil.virtual_memory().percent

# ... processing logic ...

duration = time.time() - start
end_mem = psutil.virtual_memory().percent

monitor.record_performance_metric(
    "processing_duration", "response_time", duration, "seconds", "processor"
)
monitor.record_performance_metric(
    "memory_usage", "memory", end_mem, "%", "system"
)
```

### Health Checks
```python
import requests

try:
    response = requests.get("http://api/health", timeout=5)
    if response.status_code == 200:
        monitor.update_system_health("api", "main_api", "healthy", 
                                   response_time=response.elapsed.total_seconds() * 1000)
except Exception as e:
    monitor.update_system_health("api", "main_api", "unhealthy", 
                               failure_reason=str(e))
```

## Maintenance

### Automated Cleanup
```sql
-- Run daily to clean old data
SELECT cleanup_old_monitoring_data();
```

### Health Check Automation
```sql
-- Run every 5 minutes
SELECT check_system_health_alerts();
SELECT check_error_rate_alerts();
SELECT check_processing_performance_alerts();
SELECT check_queue_backlog_alerts();
SELECT resolve_resolved_alerts();
```

### Performance Optimization
```sql
-- Additional indexes for better performance
CREATE INDEX CONCURRENTLY idx_pm_hour ON processing_metrics(DATE_TRUNC('hour', start_time));
CREATE INDEX CONCURRENTLY idx_et_hour ON error_tracking(DATE_TRUNC('hour', occurred_at));
CREATE INDEX CONCURRENTLY idx_pm_task_type ON processing_metrics(task_type);
CREATE INDEX CONCURRENTLY idx_et_component ON error_tracking(component);
```

## Next Steps

1. **Deploy**: Run the migration files in your database
2. **Configure**: Adjust alert thresholds in `monitoring_config.json`
3. **Integrate**: Add monitoring calls to your automation tasks
4. **Setup Alerts**: Configure notification channels (email, Slack, etc.)
5. **Create Dashboards**: Use the provided views for visualization
6. **Schedule Maintenance**: Set up cron jobs for automated checks
7. **Monitor**: Review dashboard data and alerts regularly

## Support

- Complete setup guide: `/workspace/docs/monitoring_setup.md`
- Integration examples: `integration_example.py`
- Configuration reference: `monitoring_config.json`
- API documentation: Available in setup guide

The monitoring system is designed to be production-ready and scalable for enterprise automation workflows.