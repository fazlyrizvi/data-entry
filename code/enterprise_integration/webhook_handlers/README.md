# 🚀 Webhook Handlers - Quick Start Guide

A comprehensive, secure, and scalable webhook handling system for enterprise integration scenarios.

## ✨ Features

- 🔐 **Secure Signature Verification** - HMAC & RSA support for multiple providers
- ⚡ **Rate Limiting & DDoS Protection** - Sliding window with burst protection  
- 🎯 **Smart Event Routing** - Dynamic routing with custom filters
- 📊 **Real-time Monitoring** - Dashboard with metrics and alerting
- 🔄 **Retry Mechanisms** - Exponential backoff for failed events
- 📦 **Multi-format Support** - JSON, XML, and form-data parsing
- 🐳 **Docker Ready** - Complete containerization with compose
- 🧪 **Comprehensive Testing** - Built-in testing tools and examples

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the webhook handlers
cd webhook_handlers

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your secrets
```

### 2. Basic Usage

```python
from main import WebhookHandler, EndpointConfig

# Create webhook handler
handler = WebhookHandler("MyWebhookService")

# Add endpoints
handler.create_stripe_endpoint(
    endpoint_id='payments',
    path='/webhook/stripe',
    secret_key='whsec_your_stripe_secret'
)

handler.create_github_endpoint(
    endpoint_id='repos',
    path='/webhook/github', 
    secret_key='your_github_secret'
)

# Start server
handler.start(host='0.0.0.0', port=5000)
```

### 3. Using the Startup Script

```bash
# Development mode with monitoring
python run.py --mode dev

# Production mode
python run.py --mode prod --host 0.0.0.0 --port 5000

# Run tests
python run.py --test

# Disable monitoring
python run.py --no-monitoring
```

## 🐳 Docker Deployment

### Development

```bash
# Start with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Production

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f webhook-handler

# Scale webhook handler
docker-compose up -d --scale webhook-handler=3
```

## 📡 Endpoints

### Webhook Endpoints

| Endpoint | Purpose | Provider |
|----------|---------|----------|
| `POST /webhook/{endpoint_id}` | Receive webhooks | Any |
| `POST /webhook/stripe` | Stripe payments | Stripe |
| `POST /webhook/github` | GitHub events | GitHub |

### Management Endpoints

| Endpoint | Purpose | Auth |
|----------|---------|------|
| `GET /health` | Health check | None |
| `GET /metrics` | System metrics | None |
| `GET /admin/endpoints` | List endpoints | None |
| `POST /admin/test-webhook` | Test webhook | None |
| `GET /` | Monitoring dashboard | None |

## 🔧 Configuration

### Environment Variables

```bash
# Required
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@host:port/db

# Optional
CACHE_TYPE=redis
CACHE_URL=redis://localhost:6379/0
MONITORING_ENABLED=true
PROMETHEUS_PORT=9090
```

### Endpoint Configuration

```python
from main import EndpointConfig, RateLimitConfig

# Custom endpoint with rate limiting
config = EndpointConfig(
    endpoint_id='custom_api',
    path='/webhook/api',
    provider='custom',
    secret_key='your-secret',
    rate_limit=RateLimitConfig(
        requests_per_minute=100,
        requests_per_hour=5000,
        burst_limit=20
    )
)

handler.add_endpoint(config)
```

## 📊 Monitoring

### Access Dashboard
```
http://localhost:5001
```

### Key Metrics
- Total requests and success rate
- Average response time
- Rate limit hits
- Queue size
- Endpoint-specific statistics

### Prometheus Integration
Metrics available at `http://localhost:9090`

## 🧪 Testing

### Built-in Testing

```bash
# Run comprehensive tests
python test_webhooks.py

# Or using the manager
python run.py --test
```

### Manual Testing

```python
from test_webhooks import WebhookTester

tester = WebhookTester("http://localhost:5000")

# Test Stripe webhook
result = tester.test_stripe_webhook('payments', 'whsec_secret')

# Test rate limiting
result = tester.test_rate_limiting('api', count=20)

# Load test
result = tester.load_test('api', concurrent_requests=5, total_requests=100)
```

### Send Test Webhooks

```bash
# Test with curl
curl -X POST http://localhost:5000/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"type":"test.event","data":{"message":"Hello World"}}'

# With signature
curl -X POST http://localhost:5000/webhook/test \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: sha256=..." \
  -d '{"type":"test.event","data":{"message":"Hello World"}}'
```

## 🔒 Security

### Signature Verification

```python
# Automatic verification for supported providers
handler.create_stripe_endpoint('stripe', '/webhook/stripe', 'whsec_secret')

# Custom verification
from signature_verifier import SignatureVerifier

verifier = SignatureVerifier(
    secret_key='your-secret',
    algorithm='hmac-sha256'
)

valid, error = verifier.verify_signature(payload, signature, headers)
```

### Rate Limiting

Built-in rate limiting with:
- Per-minute limits
- Per-hour limits  
- Burst protection
- IP-based blocking

## 🎯 Event Routing

### Custom Routes

```python
from event_router import EventRoute, EventFilter, EventPriority

# Create route
route = EventRoute(
    name="high_value_payments",
    event_types=["payment.succeeded"],
    source_filters=["stripe"],
    filters=[
        EventFilter("amount", "greater_than", 10000, "High value"),
        EventFilter("currency", "equals", "USD", "USD only")
    ],
    handler=handle_high_value_payment,
    priority=EventPriority.HIGH
)

# Add to router
handler.add_custom_route(route)
```

### Filter Operators

- `equals`, `contains`, `regex`
- `in`, `not_in`, `range`
- `greater_than`, `less_than`
- `exists`, `not_exists`

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale webhook handlers
docker-compose up -d --scale webhook-handler=3

# Use load balancer (nginx configured)
```

### Database Scaling

- PostgreSQL for persistent storage
- Redis for caching and rate limiting
- Connection pooling enabled

## 🐛 Troubleshooting

### Common Issues

1. **Signature Verification Fails**
   ```python
   # Debug signature
   from signature_verifier import create_verifier
   verifier = create_verifier('stripe', 'your_secret')
   valid, error = verifier.verify_webhook(payload, headers)
   print(f"Valid: {valid}, Error: {error}")
   ```

2. **Rate Limiting Issues**
   ```python
   # Check rate limiter
   limiter = handler.rate_limiters['endpoint_id']
   stats = limiter.get_stats()
   ```

3. **Event Routing Problems**
   ```python
   # Debug routing
   routes = handler.router.get_routes()
   for name, route in routes.items():
       print(f"Route {name}: enabled={route.enabled}")
   ```

### Logs

```bash
# View application logs
docker-compose logs -f webhook-handler

# View nginx logs
docker-compose logs -f nginx

# Debug mode
python run.py --debug
```

## 🔧 Production Deployment

### 1. Environment Setup

```bash
# Set production secrets
export SECRET_KEY="your-super-secure-secret"
export JWT_SECRET="your-jwt-secret"
export DB_PASSWORD="secure-db-password"

# Use production compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 2. SSL Configuration

```nginx
# nginx/ssl/nginx.conf
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location /webhook/ {
        proxy_pass http://webhook-handler:5000;
    }
}
```

### 3. Monitoring Setup

```bash
# Access Grafana at http://localhost:3000
# Default credentials: admin/password

# Prometheus at http://localhost:9090
```

## 📚 Examples

See the `examples/` directory for complete examples:

- `stripe_integration.py` - Full Stripe integration
- `github_integration.py` - GitHub webhook handler
- `custom_provider.py` - Custom webhook provider
- `high_volume_processing.py` - High-volume event processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- 📖 Documentation: `docs/webhook_handlers_implementation.md`
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions

---

**Built with ❤️ for secure, scalable webhook handling**
