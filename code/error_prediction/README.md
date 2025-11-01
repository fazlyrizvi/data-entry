# Error Prediction and Notification System

An intelligent, machine learning-powered system for predicting processing errors, sending smart notifications, and automatically recovering from failures in document processing workflows.

## Features

- 🤖 **Machine Learning Prediction**: Predict errors before they occur using Random Forest, Gradient Boosting, and Logistic Regression
- 📧 **Multi-Channel Notifications**: Email, Slack, SMS, webhooks with intelligent alert rules
- 🔄 **Automated Recovery**: Self-healing workflows with retry, fallback, and escalation mechanisms
- 📊 **Real-time Monitoring**: Comprehensive system health monitoring and analytics
- 🛡️ **Resilience Patterns**: Circuit breaker, bulkhead, and timeout patterns built-in

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from predictor import ErrorPredictor, DocumentCharacteristics

# Create predictor
predictor = ErrorPredictor()

# Define document characteristics
doc_chars = DocumentCharacteristics(
    file_size=50 * 1024 * 1024,  # 50MB
    file_type="pdf",
    page_count=25,
    text_density=0.6,
    image_count=5,
    image_quality_score=0.8,
    language="en",
    processing_time=120,
    confidence_score=0.9,
    document_complexity=0.7,
    time_of_day=14,
    day_of_week=1,
    historical_failure_rate=0.05
)

# Predict error probability
prediction = predictor.predict_error_probability(doc_chars)
print(f"Error probability: {prediction.error_probability:.2%}")
print(f"Severity: {prediction.severity_prediction.value}")
```

### Run Full System

```python
from main import ErrorPredictionSystem, load_config

# Load configuration
config = load_config('error_prediction_config.json')

# Create and start system
system = ErrorPredictionSystem(config)
system.start()

# Keep running...
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    system.shutdown()
```

### Run Examples

```bash
python example_usage.py
```

## Project Structure

```
code/error_prediction/
├── main.py                 # Main system orchestrator
├── predictor.py            # ML error prediction engine
├── notifier.py             # Multi-channel notification system
├── recovery.py             # Automated recovery workflows
├── requirements.txt        # Python dependencies
├── example_usage.py        # Usage examples
└── error_prediction_config.json  # Configuration template

docs/
└── error_prediction_implementation.md  # Complete documentation
```

## Key Components

### Error Predictor (`predictor.py`)
- Machine learning models for error prediction
- Feature extraction from document characteristics
- Confidence scoring and uncertainty quantification
- Model training and persistence

### Notification Orchestrator (`notifier.py`)
- Email notifications with rich formatting
- Slack integration with interactive elements
- Rule-based alert triggering
- Rate limiting and cooldown management

### Recovery Engine (`recovery.py`)
- Automated workflow execution
- Multiple recovery strategies (retry, fallback, escalate)
- Escalation procedures
- Circuit breaker patterns

### System Orchestrator (`main.py`)
- Component coordination
- System health monitoring
- Statistics and metrics collection
- Dashboard data generation

## Configuration

Create `error_prediction_config.json`:

```json
{
  "notifications": {
    "email": {
      "smtp_server": "smtp.gmail.com",
      "smtp_port": "587",
      "username": "your-email@company.com",
      "password": "your-app-password",
      "from_email": "alerts@company.com"
    },
    "slack": {
      "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
      "channel": "#alerts"
    }
  },
  "model_settings": {
    "model_save_path": "./models/error_predictor.pkl",
    "prediction_threshold": 0.7
  }
}
```

## Error Types Predicted

- `processing_timeout` - Document processing exceeds time limits
- `invalid_format` - Unsupported or corrupted file format
- `corrupted_data` - Data integrity issues
- `extraction_failure` - Text/image extraction problems
- `validation_error` - Data validation failures
- `system_overload` - Resource exhaustion
- `network_error` - Connectivity issues
- `authentication_failure` - Access control problems
- `quota_exceeded` - Resource limits exceeded

## Recovery Actions

- **Retry**: Exponential backoff retry mechanisms
- **Skip**: Continue processing, skip problematic items
- **Escalate**: Automatic escalation to support teams
- **Rollback**: Revert to previous stable state
- **Compensate**: Apply compensation logic
- **Fallback**: Switch to alternative processing paths
- **Defer**: Postpone processing until conditions improve
- **Quarantine**: Isolate problematic items for review

## Example Scenarios

### High-Risk Document Detection
```python
# Large, complex document during peak hours
high_risk_doc = DocumentCharacteristics(
    file_size=150 * 1024 * 1024,  # 150MB
    processing_time=600,           # 10 minutes
    confidence_score=0.6,         # Low confidence
    time_of_day=14,               # Peak hours
    # ... other characteristics
)

prediction = predictor.predict_error_probability(high_risk_doc)
# Output: High error probability, recommends chunked processing
```

### Automated Recovery Workflow
```python
# System automatically detects timeout and triggers recovery
# 1. Retry with extended timeout
# 2. Switch to backup processor if retry fails
# 3. Escalate to support if backup fails
```

### Smart Alerting
```python
# Alerts triggered based on configurable rules
# - Critical alerts: Immediate notification
# - Warning alerts: Rate-limited notifications
# - Info alerts: Summary notifications
```

## Monitoring and Analytics

### System Health
```python
health = system.get_health_status()
print(f"System status: {health['overall_status']}")
```

### Statistics
```python
stats = system.get_comprehensive_stats()
print(f"Error detection rate: {stats['derived_metrics']['error_detection_rate']}")
print(f"Workflow success rate: {stats['derived_metrics']['workflow_success_rate']}")
```

### Dashboard Data
```python
dashboard = system.get_system_dashboard_data()
# Real-time metrics for monitoring dashboards
```

## Best Practices

1. **Model Training**: Retrain models regularly with new data
2. **Alert Tuning**: Adjust thresholds to prevent alert fatigue
3. **Recovery Testing**: Regularly test recovery workflows
4. **Monitoring**: Set up comprehensive system monitoring
5. **Security**: Secure credential storage and access control

## Production Deployment

### With Gunicorn
```bash
gunicorn main:app --bind 0.0.0.0:8000 --workers 4
```

### As System Service
```bash
sudo systemctl enable error-prediction
sudo systemctl start error-prediction
```

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## Documentation

For complete documentation, API reference, and advanced usage patterns, see:
- [`docs/error_prediction_implementation.md`](../docs/error_prediction_implementation.md)

## Support

For issues, questions, or contributions:
1. Check the troubleshooting section in the documentation
2. Review the example usage patterns
3. Examine the system logs for detailed error information

## License

This project is part of the document processing system implementation.