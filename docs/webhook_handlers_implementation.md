# Webhook Handlers Implementation

## Overview

The Webhook Handlers system provides comprehensive webhook handling capabilities for enterprise integration scenarios. It includes secure signature verification, rate limiting, DDoS protection, event routing, and monitoring features.

## Architecture

### Core Components

#### 1. Main Webhook Handler (`main.py`)
The central Flask application that handles all webhook requests with:
- **Security Features**: Request validation, signature verification, CORS support
- **Rate Limiting**: Sliding window rate limiting with burst protection
- **DDoS Protection**: Request size limits, IP blocking, and monitoring
- **Multi-format Support**: JSON, XML, and form-data parsing
- **Monitoring**: Real-time metrics and health checks

#### 2. Signature Verifier (`signature_verifier.py`)
Handles secure signature verification with:
- **Multiple Algorithms**: HMAC-SHA256, HMAC-SHA1, RSA-SHA256, RSA-SHA1
- **Provider Support**: Built-in configurations for Stripe, GitHub, Slack, and custom providers
- **Timestamp Verification**: Protects against replay attacks
- **Timing Attack Protection**: Constant-time comparison for signatures

#### 3. Event Router (`event_router.py`)
Intelligent event routing system with:
- **Dynamic Routing**: Route events based on type, source, and custom filters
- **Priority Queues**: High-priority events processed first
- **Retry Mechanisms**: Exponential backoff for failed events
- **Async Processing**: Non-blocking event processing
- **Event Filtering**: Complex filter conditions with multiple operators

## Features

### Security

#### Signature Verification
```python
from signature_verifier import create_verifier

# Create verifier for different providers
verifier = create_verifier('stripe', 'whsec_your_secret_key')
valid, error = verifier.verify_webhook(payload, headers)

# Custom signature verification
from signature_verifier import SignatureVerifier

verifier = SignatureVerifier(
    secret_key='your-secret-key',
    algorithm='hmac-sha256',
    timestamp_tolerance=300  # 5 minutes
)
```

#### Rate Limiting
- **Sliding Window**: Tracks requests over time windows
- **Burst Protection**: Limits immediate request bursts
- **IP Blocking**: Temporarily blocks abusive IPs
- **Configurable Limits**: Per-endpoint rate limit settings

#### DDoS Protection
- Request size validation (default: 1MB)
- IP-based request tracking
- Automatic suspicious activity detection
- Block duration management

### Event Processing

#### Event Routing
```python
from event_router import EventRoute, EventFilter, EventPriority

# Create custom route
route = EventRoute(
    name="payment_processor",
    event_types=["payment.succeeded", "payment.failed"],
    source_filters=["stripe", "paypal"],
    filters=[
        EventFilter("amount", "greater_than", 1000, "High value payments"),
        EventFilter("currency", "equals", "USD", "USD transactions only")
    ],
    handler=handle_payment_event,
    priority=EventPriority.HIGH,
    retry_count=3
)

# Add to router
router.add_route(route)
```

#### Event Filtering
Supported filter operators:
- `equals`: Exact match
- `contains`: Substring match (case-insensitive)
- `regex`: Regular expression match
- `in`: Value in list
- `not_in`: Value not in list
- `range`: Numeric range
- `greater_than`: Numeric comparison
- `less_than`: Numeric comparison
- `exists`: Field exists
- `not_exists`: Field does not exist

#### Retry Mechanisms
- Exponential backoff (2^retry_count seconds)
- Maximum retry limit per route
- Configurable timeouts
- Failed event tracking

### Monitoring and Metrics

#### Built-in Metrics
```python
# Get system metrics
metrics = handler.get_metrics()

print(f"Total requests: {metrics['requests']['total']}")
print(f"Success rate: {metrics['requests']['success_rate']:.2f}%")
print(f"Average response time: {metrics['requests']['avg_response_time']:.3f}s")
```

#### Health Checks
```bash
# Health check endpoint
curl http://localhost:5000/health

# Metrics endpoint
curl http://localhost:5000/metrics

# List endpoints
curl http://localhost:5000/admin/endpoints
```

#### Available Metrics
- Total requests and success/failure counts
- Signature verification failures
- Rate limit hits
- Average response times
- Queue size and processing statistics
- Endpoint-specific metrics

## Usage Examples

### Basic Setup

```python
from main import WebhookHandler, EndpointConfig, RateLimitConfig

# Create webhook handler
handler = WebhookHandler("MyWebhookService")

# Create Stripe endpoint
stripe_config = handler.create_stripe_endpoint(
    endpoint_id='payments',
    path='/webhook/stripe',
    secret_key='whsec_your_stripe_secret'
)

# Create GitHub endpoint
github_config = handler.create_github_endpoint(
    endpoint_id='repos',
    path='/webhook/github',
    secret_key='your_github_secret'
)

# Start server
handler.start(host='0.0.0.0', port=5000)
```

### Custom Event Handler

```python
def handle_payment_webhook(event_data):
    """Custom payment event handler"""
    payment_id = event_data['data']['object']['id']
    amount = event_data['data']['object']['amount']
    
    if event_data['type'] == 'payment_intent.succeeded':
        # Process successful payment
        print(f"Payment {payment_id} succeeded: ${amount/100:.2f}")
        return {'status': 'processed', 'amount': amount}
    
    return {'status': 'ignored'}

# Create route for payment events
payment_route = EventRoute(
    name="process_payments",
    event_types=["payment_intent.succeeded"],
    source_filters=["stripe"],
    filters=[
        EventFilter("data.object.status", "equals", "succeeded")
    ],
    handler=handle_payment_webhook,
    priority=EventPriority.HIGH
)

handler.add_custom_route(payment_route)
```

### XML Webhook Support

```python
# Create XML webhook endpoint
xml_config = EndpointConfig(
    endpoint_id='xml_webhook',
    path='/webhook/xml',
    provider='custom',
    secret_key='xml_secret_key',
    event_format='xml',
    signature_verification=False  # XML signature verification requires custom implementation
)

handler.add_endpoint(xml_config)
```

### Rate Limit Configuration

```python
# Custom rate limit configuration
rate_config = RateLimitConfig(
    requests_per_minute=10,  # 10 requests per minute
    requests_per_hour=100,   # 100 requests per hour
    burst_limit=3,           # Max 3 requests in burst
    block_duration=600       # Block for 10 minutes on violation
)

custom_config = EndpointConfig(
    endpoint_id='restricted',
    path='/webhook/restricted',
    provider='custom',
    secret_key='restricted_secret',
    rate_limit=rate_config
)

handler.add_endpoint(custom_config)
```

## Configuration

### Environment Variables
```bash
# Flask configuration
FLASK_ENV=production
FLASK_DEBUG=False

# Rate limiting
DEFAULT_RATE_LIMIT=60

# Security
MAX_REQUEST_SIZE=1048576  # 1MB

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

### Endpoint Configuration Options
```python
config = EndpointConfig(
    endpoint_id='my_endpoint',
    path='/webhook/endpoint',
    provider='custom',
    secret_key='secret_key',
    enabled=True,
    signature_verification=True,
    event_format='json',  # json, xml, form
    cors_enabled=True,
    allowed_origins=['https://yourdomain.com'],
    metadata={
        'description': 'My custom webhook endpoint',
        'version': '1.0'
    }
)
```

## Testing

### Unit Tests
```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=webhook_handlers tests/

# Run specific test
pytest tests/test_signature_verifier.py
```

### Integration Tests
```python
# Test webhook endpoint
import requests

# Send test webhook
response = requests.post(
    'http://localhost:5000/webhook/test',
    json={
        'type': 'test.event',
        'data': {'message': 'Hello World'}
    },
    headers={
        'X-Webhook-Signature': 'test_signature',
        'Content-Type': 'application/json'
    }
)

print(response.json())
```

### Load Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test rate limiting
ab -n 1000 -c 10 http://localhost:5000/webhook/test

# Test multiple endpoints
for i in {1..100}; do
    curl -X POST http://localhost:5000/webhook/test \
         -H "Content-Type: application/json" \
         -d '{"type":"test","id":'$i'}' &
done
```

## Production Deployment

### Using Gunicorn
```bash
# Install dependencies
pip install -r requirements.txt

# Start with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 30 main:webhook_handler.app
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "main:webhook_handler.app"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  webhook-handler:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    volumes:
      - ./logs:/app/logs

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - webhook-handler
```

## Security Best Practices

### Secret Management
- Use environment variables for secret keys
- Rotate secret keys regularly
- Use different keys for different environments
- Implement secret key hashing

### HTTPS Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /webhook/ {
        proxy_pass http://webhook-handler:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Monitoring and Alerting
```python
# Set up monitoring alerts
from prometheus_client import Counter, Histogram

# Define metrics
request_count = Counter('webhook_requests_total', 'Total webhook requests', ['endpoint', 'status'])
response_time = Histogram('webhook_response_time_seconds', 'Webhook response time')

# Alert on high failure rate
# Alert on signature verification failures
# Alert on rate limit violations
```

## Troubleshooting

### Common Issues

#### Signature Verification Failures
```python
# Debug signature verification
verifier = create_verifier('stripe', 'whsec_your_key')
payload = json.dumps(event_data)
signature = headers['Stripe-Signature']
valid, error = verifier.verify_webhook(payload, headers)

print(f"Valid: {valid}, Error: {error}")
```

#### Rate Limiting Issues
```python
# Check rate limiter status
limiter = handler.rate_limiters['endpoint_id']
stats = limiter.get_stats()
print(f"Requests in last hour: {stats['hourly_requests']}")
```

#### Event Routing Problems
```python
# Debug event routing
routes = handler.router.get_routes()
for name, route in routes.items():
    print(f"Route {name}: {route.enabled}")
    print(f"  Event types: {route.event_types}")
    print(f"  Filters: {len(route.filters)}")

# Test routing
event_data = {'type': 'payment.succeeded', 'amount': 1000}
result = handler.router.route_event(
    event_data, 'stripe', 'payment.succeeded', 'test-id',
    async_processing=False
)
print(f"Route result: {result.status}")
```

### Logging Configuration
```python
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/webhooks.log'),
        logging.StreamHandler()
    ]
)

# Set specific logger levels
logging.getLogger('webhook_handlers.signature_verifier').setLevel(logging.DEBUG)
logging.getLogger('webhook_handlers.event_router').setLevel(logging.INFO)
```

## API Reference

### Endpoint: `/health`
- **Method**: GET
- **Description**: Health check endpoint
- **Response**: `{"status": "healthy", "timestamp": "...", "version": "1.0.0"}`

### Endpoint: `/webhook/<endpoint_id>`
- **Method**: POST
- **Description**: Webhook endpoint for receiving events
- **Headers**: Provider-specific signature headers
- **Body**: Event data in configured format
- **Response**: `{"status": "accepted", "event_id": "...", "processed": "pending"}`

### Endpoint: `/metrics`
- **Method**: GET
- **Description**: System metrics
- **Response**: JSON object with detailed metrics

### Endpoint: `/admin/endpoints`
- **Method**: GET
- **Description**: List all configured endpoints
- **Response**: JSON object with endpoint information and metrics

### Endpoint: `/admin/test-webhook`
- **Method**: POST
- **Description**: Test webhook endpoint
- **Body**: `{"endpoint_id": "...", "payload": {...}}`
- **Response**: Test result

## Performance Optimization

### Caching
```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379'
})

@app.route('/webhook/<endpoint_id>')
@cache.cached(timeout=60)
def webhook_endpoint(endpoint_id):
    # Your webhook handling code
    pass
```

### Database Integration
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database configuration
engine = create_engine('postgresql://user:pass@localhost/webhooks')
Session = sessionmaker(bind=engine)

# Store webhook events
def store_webhook_event(event_data):
    session = Session()
    event = WebhookEvent(
        id=event_data['id'],
        type=event_data['type'],
        data=json.dumps(event_data),
        timestamp=datetime.utcnow()
    )
    session.add(event)
    session.commit()
    session.close()
```

## Conclusion

The Webhook Handlers system provides a robust, secure, and scalable solution for handling webhooks in enterprise environments. With comprehensive security features, intelligent event routing, and extensive monitoring capabilities, it can handle high-volume webhook traffic while maintaining reliability and security.

For additional support or customization needs, refer to the inline documentation in the source code or contact the development team.
