"""
Webhook Testing Tools

Utilities for testing webhook endpoints and validating webhook configurations.
"""

import json
import time
import requests
import hashlib
import hmac
from typing import Dict, Any, Optional
from datetime import datetime


class WebhookTester:
    """Testing utilities for webhook endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize webhook tester
        
        Args:
            base_url: Base URL of webhook service
        """
        self.base_url = base_url.rstrip('/')
    
    def generate_signature(self, payload: str, secret: str, algorithm: str = 'sha256') -> str:
        """
        Generate HMAC signature for testing
        
        Args:
            payload: Payload to sign
            secret: Secret key
            algorithm: Hash algorithm (sha256, sha1)
            
        Returns:
            Generated signature
        """
        if algorithm == 'sha256':
            signature = hmac.new(
                secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
        elif algorithm == 'sha1':
            signature = hmac.new(
                secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha1
            ).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        return f"sha256={signature}" if algorithm == 'sha256' else signature
    
    def send_webhook(self, endpoint_id: str, payload: Dict[str, Any], 
                    secret: Optional[str] = None, 
                    provider: str = 'custom') -> Dict[str, Any]:
        """
        Send test webhook
        
        Args:
            endpoint_id: Endpoint to send to
            payload: Webhook payload
            secret: Secret key for signing (optional)
            provider: Provider type for signature header format
            
        Returns:
            Response from webhook endpoint
        """
        url = f"{self.base_url}/webhook/{endpoint_id}"
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add signature if secret is provided
        if secret:
            payload_str = json.dumps(payload, separators=(',', ':'))
            
            if provider == 'stripe':
                signature = self.generate_signature(payload_str, secret, 'sha256')
                timestamp = str(int(time.time()))
                headers['Stripe-Signature'] = f"t={timestamp},v1={signature}"
            elif provider == 'github':
                signature = self.generate_signature(payload_str, secret, 'sha256')
                headers['X-Hub-Signature-256'] = f"sha256={signature}"
            elif provider == 'slack':
                signature = self.generate_signature(payload_str, secret, 'sha256')
                headers['X-Slack-Signature'] = signature
                headers['X-Slack-Request-Timestamp'] = str(int(time.time()))
            else:
                # Custom provider
                signature = self.generate_signature(payload_str, secret, 'sha256')
                headers['X-Webhook-Signature'] = signature
                headers['X-Webhook-Timestamp'] = str(int(time.time()))
        
        # Send request
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                'headers': dict(response.headers)
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_stripe_webhook(self, endpoint_id: str, secret: str, 
                          event_type: str = 'payment_intent.succeeded') -> Dict[str, Any]:
        """
        Send Stripe-style webhook
        
        Args:
            endpoint_id: Endpoint to send to
            secret: Stripe webhook secret
            event_type: Stripe event type
            
        Returns:
            Test result
        """
        payload = {
            'id': 'evt_test_webhook',
            'object': 'event',
            'type': event_type,
            'created': int(time.time()),
            'data': {
                'object': {
                    'id': 'pi_test_payment_intent',
                    'object': 'payment_intent',
                    'amount': 2000,
                    'currency': 'usd',
                    'status': 'succeeded',
                    'metadata': {
                        'test': True
                    }
                }
            },
            'livemode': False,
            'pending_webhooks': 1,
            'request': {
                'id': 'req_test_request',
                'idempotency_key': None
            }
        }
        
        return self.send_webhook(endpoint_id, payload, secret, 'stripe')
    
    def test_github_webhook(self, endpoint_id: str, secret: str,
                          event_type: str = 'push') -> Dict[str, Any]:
        """
        Send GitHub-style webhook
        
        Args:
            endpoint_id: Endpoint to send to
            secret: GitHub webhook secret
            event_type: GitHub event type
            
        Returns:
            Test result
        """
        payload = {
            'ref': 'refs/heads/main',
            'before': 'abc123',
            'after': 'def456',
            'repository': {
                'id': 12345,
                'name': 'test-repo',
                'full_name': 'user/test-repo',
                'private': False
            },
            'pusher': {
                'name': 'test-user',
                'email': 'test@example.com'
            },
            'commits': [
                {
                    'id': 'def456',
                    'message': 'Test commit',
                    'timestamp': datetime.utcnow().isoformat(),
                    'url': 'https://github.com/user/test-repo/commit/def456'
                }
            ],
            'head_commit': {
                'id': 'def456',
                'message': 'Test commit',
                'timestamp': datetime.utcnow().isoformat(),
                'url': 'https://github.com/user/test-repo/commit/def456'
            }
        }
        
        return self.send_webhook(endpoint_id, payload, secret, 'github')
    
    def test_custom_webhook(self, endpoint_id: str, secret: str,
                          event_type: str = 'custom.event') -> Dict[str, Any]:
        """
        Send custom webhook
        
        Args:
            endpoint_id: Endpoint to send to
            secret: Webhook secret
            event_type: Custom event type
            
        Returns:
            Test result
        """
        payload = {
            'type': event_type,
            'id': f'evt_{int(time.time())}',
            'timestamp': datetime.utcnow().isoformat(),
            'data': {
                'message': 'Test webhook event',
                'timestamp': time.time(),
                'source': 'test_suite'
            }
        }
        
        return self.send_webhook(endpoint_id, payload, secret, 'custom')
    
    def test_rate_limiting(self, endpoint_id: str, count: int = 10, 
                          interval: float = 0.1) -> Dict[str, Any]:
        """
        Test rate limiting by sending multiple requests
        
        Args:
            endpoint_id: Endpoint to test
            count: Number of requests to send
            interval: Interval between requests in seconds
            
        Returns:
            Test results
        """
        results = []
        start_time = time.time()
        
        for i in range(count):
            payload = {
                'type': 'test.rate_limit',
                'id': f'test_{i}_{int(time.time())}',
                'data': {'request_number': i + 1}
            }
            
            result = self.send_webhook(endpoint_id, payload)
            results.append(result)
            
            if i < count - 1:  # Don't sleep after last request
                time.sleep(interval)
        
        end_time = time.time()
        
        # Analyze results
        successful = [r for r in results if r['success']]
        rate_limited = [r for r in results if r.get('status_code') == 429]
        errors = [r for r in results if not r['success'] and r.get('status_code') != 429]
        
        return {
            'total_requests': count,
            'successful': len(successful),
            'rate_limited': len(rate_limited),
            'errors': len(errors),
            'duration': end_time - start_time,
            'success_rate': len(successful) / count * 100,
            'results': results
        }
    
    def load_test(self, endpoint_id: str, concurrent_requests: int = 5,
                 total_requests: int = 100) -> Dict[str, Any]:
        """
        Load test webhook endpoint
        
        Args:
            endpoint_id: Endpoint to test
            concurrent_requests: Number of concurrent requests
            total_requests: Total requests to send
            
        Returns:
            Load test results
        """
        import concurrent.futures
        import threading
        
        results = []
        start_time = time.time()
        
        def send_request(request_num):
            payload = {
                'type': 'test.load',
                'id': f'load_{request_num}_{int(time.time())}',
                'data': {'request_number': request_num}
            }
            
            return self.send_webhook(endpoint_id, payload)
        
        # Send requests in batches
        batch_size = concurrent_requests
        num_batches = (total_requests + batch_size - 1) // batch_size
        
        for batch in range(num_batches):
            batch_start = batch * batch_size
            batch_end = min(batch_start + batch_size, total_requests)
            batch_requests = list(range(batch_start, batch_end))
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
                batch_results = list(executor.map(send_request, batch_requests))
                results.extend(batch_results)
        
        end_time = time.time()
        
        # Analyze results
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        return {
            'total_requests': total_requests,
            'concurrent_requests': concurrent_requests,
            'successful': len(successful),
            'failed': len(failed),
            'duration': end_time - start_time,
            'requests_per_second': total_requests / (end_time - start_time),
            'success_rate': len(successful) / total_requests * 100,
            'error_summary': self._summarize_errors(failed)
        }
    
    def _summarize_errors(self, failed_results: list) -> Dict[str, Any]:
        """Summarize error types from failed results"""
        error_summary = {}
        
        for result in failed_results:
            status_code = result.get('status_code', 'unknown')
            error_type = result.get('error', 'unknown_error')
            
            if status_code not in error_summary:
                error_summary[status_code] = {}
            
            if error_type not in error_summary[status_code]:
                error_summary[status_code][error_type] = 0
            
            error_summary[status_code][error_type] += 1
        
        return error_summary
    
    def test_signature_verification(self, endpoint_id: str, secret: str,
                                  provider: str = 'custom') -> Dict[str, Any]:
        """
        Test signature verification by sending valid and invalid signatures
        
        Args:
            endpoint_id: Endpoint to test
            secret: Valid secret key
            provider: Provider type
            
        Returns:
            Signature test results
        """
        payload = {
            'type': 'test.signature',
            'id': f'sig_test_{int(time.time())}',
            'data': {'message': 'Testing signature verification'}
        }
        
        # Test with valid signature
        valid_result = self.send_webhook(endpoint_id, payload, secret, provider)
        
        # Test with invalid signature
        invalid_payload = payload.copy()
        invalid_payload['data']['tampered'] = True
        invalid_result = self.send_webhook(endpoint_id, invalid_payload, 'wrong_secret', provider)
        
        # Test with missing signature
        no_signature_result = self.send_webhook(endpoint_id, payload, None, provider)
        
        return {
            'valid_signature': {
                'success': valid_result['success'],
                'status_code': valid_result.get('status_code')
            },
            'invalid_signature': {
                'success': invalid_result['success'],
                'status_code': invalid_result.get('status_code'),
                'should_fail': True
            },
            'no_signature': {
                'success': no_signature_result['success'],
                'status_code': no_signature_result.get('status_code'),
                'should_fail': True
            },
            'verification_working': (
                valid_result['success'] and 
                not invalid_result['success'] and 
                not no_signature_result['success']
            )
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics
        
        Returns:
            Current system metrics
        """
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'Failed to get metrics: {response.status_code}'}
        except requests.RequestException as e:
            return {'error': str(e)}
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check system health
        
        Returns:
            Health check results
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {'status': 'unhealthy', 'error': f'Status code: {response.status_code}'}
        except requests.RequestException as e:
            return {'status': 'unhealthy', 'error': str(e)}


def run_comprehensive_test(base_url: str = "http://localhost:5000") -> Dict[str, Any]:
    """
    Run comprehensive webhook testing suite
    
    Args:
        base_url: Base URL of webhook service
        
    Returns:
        Complete test results
    """
    tester = WebhookTester(base_url)
    results = {}
    
    print("🔍 Running comprehensive webhook tests...\n")
    
    # Health check
    print("1. Health Check")
    health = tester.check_health()
    results['health'] = health
    print(f"   Status: {health.get('status', 'unknown')}")
    
    # Get metrics
    print("\n2. Initial Metrics")
    initial_metrics = tester.get_metrics()
    results['initial_metrics'] = initial_metrics
    print(f"   Total requests: {initial_metrics.get('requests', {}).get('total', 0)}")
    
    # Test custom webhook
    print("\n3. Custom Webhook Test")
    custom_result = tester.test_custom_webhook('test_endpoint', 'test_secret')
    results['custom_webhook'] = custom_result
    print(f"   Success: {custom_result['success']}")
    
    # Test Stripe webhook
    print("\n4. Stripe Webhook Test")
    stripe_result = tester.test_stripe_webhook('test_stripe', 'whsec_test_secret')
    results['stripe_webhook'] = stripe_result
    print(f"   Success: {stripe_result['success']}")
    
    # Test GitHub webhook
    print("\n5. GitHub Webhook Test")
    github_result = tester.test_github_webhook('test_github', 'github_test_secret')
    results['github_webhook'] = github_result
    print(f"   Success: {github_result['success']}")
    
    # Test rate limiting
    print("\n6. Rate Limiting Test")
    rate_limit_result = tester.test_rate_limiting('test_endpoint', count=15, interval=0.1)
    results['rate_limiting'] = rate_limit_result
    print(f"   Requests: {rate_limit_result['total_requests']}")
    print(f"   Successful: {rate_limit_result['successful']}")
    print(f"   Rate Limited: {rate_limit_result['rate_limited']}")
    
    # Test signature verification
    print("\n7. Signature Verification Test")
    signature_result = tester.test_signature_verification('test_endpoint', 'test_secret')
    results['signature_verification'] = signature_result
    print(f"   Verification Working: {signature_result['verification_working']}")
    
    # Final metrics
    print("\n8. Final Metrics")
    final_metrics = tester.get_metrics()
    results['final_metrics'] = final_metrics
    total_requests = final_metrics.get('requests', {}).get('total', 0)
    success_rate = final_metrics.get('requests', {}).get('success_rate', 0)
    print(f"   Total Requests: {total_requests}")
    print(f"   Success Rate: {success_rate:.2f}%")
    
    print("\n✅ Comprehensive test completed!")
    return results


if __name__ == '__main__':
    # Run comprehensive test
    results = run_comprehensive_test()
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    all_tests_passed = True
    
    # Check health
    if results['health'].get('status') != 'healthy':
        print("❌ Health check failed")
        all_tests_passed = False
    else:
        print("✅ Health check passed")
    
    # Check webhook tests
    for test_name, result in results.items():
        if test_name in ['custom_webhook', 'stripe_webhook', 'github_webhook']:
            if result['success']:
                print(f"✅ {test_name} passed")
            else:
                print(f"❌ {test_name} failed")
                all_tests_passed = False
    
    # Check signature verification
    if results['signature_verification']['verification_working']:
        print("✅ Signature verification working")
    else:
        print("❌ Signature verification failed")
        all_tests_passed = False
    
    # Final status
    print("\n" + "="*50)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("="*50)
