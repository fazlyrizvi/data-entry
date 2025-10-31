"""
Main Webhook Handler

Comprehensive webhook handler with security, rate limiting, event processing,
and monitoring capabilities.
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from flask import Flask, request, jsonify, Response
from dataclasses import dataclass, asdict
import hashlib
import secrets
import logging
from collections import defaultdict, deque
import threading
import time
from functools import wraps

from signature_verifier import ProviderSignatureHandler, create_verifier
from event_router import EventRouter, EventRoute, EventFilter, EventPriority


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    block_duration: int = 300  # 5 minutes


@dataclass
class EndpointConfig:
    """Webhook endpoint configuration"""
    endpoint_id: str
    path: str
    provider: str
    secret_key: str
    enabled: bool = True
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    signature_verification: bool = True
    event_format: str = "json"  # json, xml, form
    cors_enabled: bool = True
    allowed_origins: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebhookMetrics:
    """Webhook metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    signature_failures: int = 0
    rate_limit_hits: int = 0
    avg_response_time: float = 0.0
    last_activity: Optional[datetime] = None


class RateLimiter:
    """Rate limiter with sliding window and burst protection"""
    
    def __init__(self, config: RateLimitConfig):
        """
        Initialize rate limiter
        
        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.request_times = defaultdict(deque)
        self.blocked_ips = defaultdict(datetime)
        self._lock = threading.Lock()
    
    def is_allowed(self, client_ip: str) -> tuple[bool, str]:
        """
        Check if request is allowed for client IP
        
        Args:
            client_ip: Client IP address
            
        Returns:
            Tuple of (is_allowed, reason)
        """
        with self._lock:
            now = datetime.utcnow()
            current_time = time.time()
            
            # Check if IP is blocked
            if client_ip in self.blocked_ips:
                block_expires = self.blocked_ips[client_ip]
                if now < block_expires:
                    return False, f"IP blocked until {block_expires}"
                else:
                    # Unblock IP
                    del self.blocked_ips[client_ip]
            
            # Get request times for this IP
            times = self.request_times[client_ip]
            
            # Clean old requests (older than 1 hour)
            hour_ago = current_time - 3600
            while times and times[0] < hour_ago:
                times.popleft()
            
            # Check burst limit
            recent_requests = [t for t in times if current_time - t < 60]  # Last minute
            if len(recent_requests) >= self.config.burst_limit:
                self._block_ip(client_ip, "Burst limit exceeded")
                return False, "Burst limit exceeded"
            
            # Check per-minute limit
            minute_ago = current_time - 60
            minute_requests = [t for t in times if t > minute_ago]
            if len(minute_requests) >= self.config.requests_per_minute:
                return False, "Rate limit exceeded (per minute)"
            
            # Check per-hour limit
            if len(times) >= self.config.requests_per_hour:
                return False, "Rate limit exceeded (per hour)"
            
            # Record this request
            times.append(current_time)
            
            return True, "Request allowed"
    
    def _block_ip(self, client_ip: str, reason: str, duration: Optional[int] = None) -> None:
        """
        Block IP address
        
        Args:
            client_ip: Client IP to block
            reason: Reason for blocking
            duration: Block duration in seconds
        """
        block_duration = duration or self.config.block_duration
        block_until = datetime.utcnow() + timedelta(seconds=block_duration)
        self.blocked_ips[client_ip] = block_until
        logger.warning(f"Blocked IP {client_ip} for {duration}s: {reason}")


class WebhookHandler:
    """
    Main webhook handler with all security and processing features
    """
    
    def __init__(self, app_name: str = "WebhookHandler"):
        """
        Initialize webhook handler
        
        Args:
            app_name: Name of the application
        """
        self.app = Flask(__name__)
        self.app_name = app_name
        self.endpoints: Dict[str, EndpointConfig] = {}
        self.verifiers: Dict[str, ProviderSignatureHandler] = {}
        self.router = EventRouter()
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.metrics: Dict[str, WebhookMetrics] = defaultdict(WebhookMetrics)
        self.ddos_protection = True
        self.request_sizes = defaultdict(deque)  # For tracking request sizes
        self.max_request_size = 1024 * 1024  # 1MB default
        
        self._setup_routes()
        self._setup_hooks()
    
    def _setup_routes(self) -> None:
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0.0'
            })
        
        @self.app.route('/webhook/<endpoint_id>', methods=['POST'])
        def webhook_endpoint(endpoint_id):
            """Generic webhook endpoint"""
            return self._handle_webhook_request(endpoint_id)
        
        @self.app.route('/metrics', methods=['GET'])
        def metrics():
            """Metrics endpoint"""
            return jsonify(self.get_metrics())
        
        @self.app.route('/admin/endpoints', methods=['GET'])
        def list_endpoints():
            """List all configured endpoints"""
            endpoints_info = {}
            for ep_id, config in self.endpoints.items():
                endpoints_info[ep_id] = {
                    'path': config.path,
                    'provider': config.provider,
                    'enabled': config.enabled,
                    'metrics': asdict(self.metrics[ep_id])
                }
            return jsonify(endpoints_info)
        
        @self.app.route('/admin/test-webhook', methods=['POST'])
        def test_webhook():
            """Test webhook endpoint"""
            data = request.get_json() or {}
            endpoint_id = data.get('endpoint_id')
            test_payload = data.get('payload', {})
            
            if not endpoint_id or endpoint_id not in self.endpoints:
                return jsonify({'error': 'Invalid endpoint_id'}), 400
            
            # Simulate webhook call
            result = self._process_webhook(endpoint_id, test_payload, {'test': True})
            return jsonify(result)
    
    def _setup_hooks(self) -> None:
        """Setup Flask hooks for request tracking"""
        
        @self.app.before_request
        def before_request():
            """Track request start time"""
            request.start_time = time.time()
            
            # Check request size
            content_length = request.content_length or 0
            if content_length > self.max_request_size:
                return Response(
                    "Request too large",
                    status=413,
                    headers={'Content-Type': 'text/plain'}
                )
        
        @self.app.after_request
        def after_request(response):
            """Track request completion"""
            # Add security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            return response
    
    def add_endpoint(self, config: EndpointConfig) -> None:
        """
        Add webhook endpoint configuration
        
        Args:
            config: Endpoint configuration
        """
        self.endpoints[config.endpoint_id] = config
        
        # Create signature verifier
        if config.signature_verification:
            self.verifiers[config.endpoint_id] = create_verifier(
                config.provider, 
                config.secret_key
            )
        
        # Create rate limiter
        self.rate_limiters[config.endpoint_id] = RateLimiter(config.rate_limit)
        
        # Initialize metrics
        self.metrics[config.endpoint_id] = WebhookMetrics()
        
        logger.info(f"Added webhook endpoint: {config.endpoint_id}")
    
    def _handle_webhook_request(self, endpoint_id: str):
        """
        Handle incoming webhook request
        
        Args:
            endpoint_id: Endpoint identifier
            
        Returns:
            Flask response
        """
        config = self.endpoints.get(endpoint_id)
        if not config or not config.enabled:
            return jsonify({'error': 'Endpoint not found'}), 404
        
        # Get client IP
        client_ip = self._get_client_ip()
        
        # Rate limiting
        rate_limiter = self.rate_limiters[endpoint_id]
        allowed, reason = rate_limiter.is_allowed(client_ip)
        
        if not allowed:
            self.metrics[endpoint_id].rate_limit_hits += 1
            logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint_id}: {reason}")
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Parse request data
        try:
            event_data, event_type, event_id = self._parse_request(request, config)
        except Exception as e:
            logger.error(f"Failed to parse webhook request: {e}")
            return jsonify({'error': 'Invalid request format'}), 400
        
        # Signature verification
        if config.signature_verification:
            verifier = self.verifiers[endpoint_id]
            valid, error_msg = verifier.verify_webhook(
                json.dumps(event_data),
                dict(request.headers)
            )
            
            if not valid:
                self.metrics[endpoint_id].signature_failures += 1
                logger.warning(f"Signature verification failed for {endpoint_id}: {error_msg}")
                return jsonify({'error': 'Invalid signature'}), 401
        
        # Process webhook
        try:
            result = self._process_webhook(endpoint_id, event_data, dict(request.headers))
            return jsonify(result), 200
        except Exception as e:
            self.metrics[endpoint_id].failed_requests += 1
            logger.error(f"Webhook processing failed: {e}")
            return jsonify({'error': 'Processing failed'}), 500
    
    def _parse_request(self, req, config: EndpointConfig) -> tuple[Dict[str, Any], str, str]:
        """
        Parse webhook request based on format
        
        Args:
            req: Flask request object
            config: Endpoint configuration
            
        Returns:
            Tuple of (event_data, event_type, event_id)
        """
        if config.event_format == 'json':
            event_data = req.get_json() or {}
        elif config.event_format == 'xml':
            try:
                root = ET.fromstring(req.data)
                event_data = self._xml_to_dict(root)
            except ET.ParseError:
                raise ValueError("Invalid XML format")
        elif config.event_format == 'form':
            event_data = dict(req.form)
        else:
            raise ValueError(f"Unsupported event format: {config.event_format}")
        
        # Extract event type and ID
        event_type = event_data.get('type') or event_data.get('event_type') or 'unknown'
        event_id = self._generate_event_id(event_data, event_type)
        
        return event_data, event_type, event_id
    
    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}
        
        # Add attributes
        if element.attrib:
            result.update(element.attrib)
        
        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result['text'] = element.text.strip()
        
        # Add child elements
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    def _generate_event_id(self, event_data: Dict[str, Any], event_type: str) -> str:
        """Generate unique event ID"""
        content = f"{event_type}:{json.dumps(event_data, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _process_webhook(self, endpoint_id: str, event_data: Dict[str, Any], 
                        headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Process webhook event
        
        Args:
            endpoint_id: Endpoint identifier
            event_data: Event data
            headers: Request headers
            
        Returns:
            Processing result
        """
        config = self.endpoints[endpoint_id]
        event_id = self._generate_event_id(event_data, event_data.get('type', 'unknown'))
        
        # Route event
        processed_event = self.router.route_event(
            event_data=event_data,
            source=config.provider,
            event_type=event_data.get('type', 'unknown'),
            event_id=event_id,
            async_processing=True
        )
        
        # Update metrics
        metrics = self.metrics[endpoint_id]
        metrics.total_requests += 1
        metrics.successful_requests += 1
        metrics.last_activity = datetime.utcnow()
        
        # Calculate response time
        if hasattr(request, 'start_time'):
            response_time = time.time() - request.start_time
            metrics.avg_response_time = (metrics.avg_response_time + response_time) / 2
        
        return {
            'status': 'accepted',
            'event_id': event_id,
            'processed': processed_event.status.value,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _get_client_ip(self) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or 'unknown'
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics
        
        Returns:
            Dictionary with metrics
        """
        total_requests = sum(m.total_requests for m in self.metrics.values())
        total_successful = sum(m.successful_requests for m in self.metrics.values())
        total_failed = sum(m.failed_requests for m in self.metrics.values())
        total_signature_failures = sum(m.signature_failures for m in self.metrics.values())
        total_rate_limit_hits = sum(m.rate_limit_hits for m in self.metrics.values())
        
        avg_response_time = 0
        if total_requests > 0:
            total_response_time = sum(m.avg_response_time * m.total_requests for m in self.metrics.values())
            avg_response_time = total_response_time / total_requests
        
        return {
            'system': {
                'endpoints_total': len(self.endpoints),
                'endpoints_enabled': len([e for e in self.endpoints.values() if e.enabled]),
                'router_stats': self.router.get_statistics()
            },
            'requests': {
                'total': total_requests,
                'successful': total_successful,
                'failed': total_failed,
                'success_rate': (total_successful / total_requests * 100) if total_requests > 0 else 0,
                'signature_failures': total_signature_failures,
                'rate_limit_hits': total_rate_limit_hits,
                'avg_response_time': avg_response_time
            },
            'endpoints': {
                ep_id: asdict(metrics) for ep_id, metrics in self.metrics.items()
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def create_stripe_endpoint(self, endpoint_id: str, path: str, secret_key: str) -> EndpointConfig:
        """
        Create Stripe webhook endpoint
        
        Args:
            endpoint_id: Unique endpoint identifier
            path: URL path for the endpoint
            secret_key: Stripe webhook secret key
            
        Returns:
            EndpointConfig instance
        """
        config = EndpointConfig(
            endpoint_id=endpoint_id,
            path=path,
            provider='stripe',
            secret_key=secret_key,
            signature_verification=True,
            event_format='json',
            rate_limit=RateLimitConfig(
                requests_per_minute=100,
                requests_per_hour=5000,
                burst_limit=20
            )
        )
        
        self.add_endpoint(config)
        return config
    
    def create_github_endpoint(self, endpoint_id: str, path: str, secret_key: str) -> EndpointConfig:
        """
        Create GitHub webhook endpoint
        
        Args:
            endpoint_id: Unique endpoint identifier
            path: URL path for the endpoint
            secret_key: GitHub webhook secret key
            
        Returns:
            EndpointConfig instance
        """
        config = EndpointConfig(
            endpoint_id=endpoint_id,
            path=path,
            provider='github',
            secret_key=secret_key,
            signature_verification=True,
            event_format='json',
            rate_limit=RateLimitConfig(
                requests_per_minute=200,
                requests_per_hour=10000,
                burst_limit=30
            )
        )
        
        self.add_endpoint(config)
        return config
    
    def create_generic_endpoint(self, endpoint_id: str, path: str, 
                               secret_key: str, provider: str = 'custom') -> EndpointConfig:
        """
        Create generic webhook endpoint
        
        Args:
            endpoint_id: Unique endpoint identifier
            path: URL path for the endpoint
            secret_key: Secret key for verification
            provider: Provider name
            
        Returns:
            EndpointConfig instance
        """
        config = EndpointConfig(
            endpoint_id=endpoint_id,
            path=path,
            provider=provider,
            secret_key=secret_key,
            signature_verification=True,
            event_format='json',
            rate_limit=RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=3000,
                burst_limit=10
            )
        )
        
        self.add_endpoint(config)
        return config
    
    def add_custom_route(self, route_config: EventRoute) -> None:
        """
        Add custom event route
        
        Args:
            route_config: Event route configuration
        """
        self.router.add_route(route_config)
    
    def start(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False) -> None:
        """
        Start the webhook handler
        
        Args:
            host: Host to bind to
            port: Port to listen on
            debug: Enable debug mode
        """
        logger.info(f"Starting {self.app_name} on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


# Global webhook handler instance
webhook_handler = WebhookHandler()


# Create default routes
from event_router import create_default_routes
create_default_routes(webhook_handler.router)


if __name__ == '__main__':
    # Example usage
    handler = WebhookHandler()
    
    # Add example endpoints
    handler.create_stripe_endpoint('stripe_webhook', '/webhook/stripe', 'whsec_example')
    handler.create_github_endpoint('github_webhook', '/webhook/github', 'github_secret')
    
    # Start server
    handler.start(debug=True)
