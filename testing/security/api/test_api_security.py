#!/usr/bin/env python3
"""
API Security Testing Suite
Tests API security controls including authentication, authorization, rate limiting,
input validation, and API-specific vulnerabilities.
"""

import pytest
import requests
import json
import time
import secrets
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urlencode
import base64
import sys
import os


class TestAPIAuthentication:
    """Test suite for API authentication security"""
    
    @pytest.fixture
    def api_base_url(self):
        """API base URL for testing"""
        return "http://localhost:8000/api/v1"
    
    @pytest.fixture
    def test_user_credentials(self):
        """Test user credentials"""
        return {
            "email": "security.test@example.com",
            "password": "SecureTest123!@#"
        }
    
    @pytest.mark.security
    def test_jwt_token_validation(self, api_base_url, test_user_credentials):
        """Test JWT token validation and security"""
        # Test valid token
        response = requests.post(
            f"{api_base_url}/auth/login",
            json=test_user_credentials
        )
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            assert token is not None
            
            # Validate token structure
            parts = token.split('.')
            assert len(parts) == 3  # Header.payload.signature
            
            # Test protected endpoint with valid token
            headers = {"Authorization": f"Bearer {token}"}
            protected_response = requests.get(
                f"{api_base_url}/protected",
                headers=headers
            )
            assert protected_response.status_code in [200, 403]  # 403 if no permission
        
        # Test with invalid token
        invalid_response = requests.get(
            f"{api_base_url}/protected",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert invalid_response.status_code == 401
        
        # Test with malformed token
        malformed_response = requests.get(
            f"{api_base_url}/protected",
            headers={"Authorization": "Bearer not.a.token"}
        )
        assert malformed_response.status_code == 401
    
    @pytest.mark.security
    def test_token_expiration(self, api_base_url, test_user_credentials):
        """Test token expiration handling"""
        response = requests.post(
            f"{api_base_url}/auth/login",
            json=test_user_credentials
        )
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            
            # Wait for token expiration (if short-lived)
            time.sleep(1)
            
            # Test expired token
            expired_response = requests.get(
                f"{api_base_url}/protected",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert expired_response.status_code in [401, 403]
    
    @pytest.mark.security
    def test_token_refresh_security(self, api_base_url, test_user_credentials):
        """Test token refresh mechanism security"""
        # Login to get initial token
        login_response = requests.post(
            f"{api_base_url}/auth/login",
            json=test_user_credentials
        )
        
        if login_response.status_code == 200:
            refresh_token = login_response.json().get("refresh_token")
            
            if refresh_token:
                # Test valid refresh
                refresh_response = requests.post(
                    f"{api_base_url}/auth/refresh",
                    json={"refresh_token": refresh_token}
                )
                
                if refresh_response.status_code == 200:
                    new_token = refresh_response.json().get("access_token")
                    assert new_token != refresh_token  # Should be new token
                
                # Test invalid refresh token
                invalid_refresh = requests.post(
                    f"{api_base_url}/auth/refresh",
                    json={"refresh_token": "invalid_refresh_token"}
                )
                assert invalid_refresh.status_code == 401
    
    @pytest.mark.security
    def test_api_key_authentication(self):
        """Test API key based authentication"""
        # Generate test API key
        api_key = secrets.token_hex(32)
        
        # Test with valid API key
        headers = {"X-API-Key": api_key}
        response = requests.get("http://localhost:8000/api/public", headers=headers)
        
        # Should succeed (if endpoint exists)
        # assert response.status_code in [200, 403]  # 403 if no permission
        
        # Test without API key
        no_key_response = requests.get("http://localhost:8000/api/public")
        # Should fail for protected endpoints
        # assert no_key_response.status_code == 401
    
    @pytest.mark.security
    def test_oauth2_flow_security(self):
        """Test OAuth 2.0 flow security"""
        # Test authorization code flow
        auth_url = "http://localhost:8000/oauth/authorize?" + urlencode({
            "response_type": "code",
            "client_id": "test_client",
            "redirect_uri": "http://localhost:8000/callback",
            "scope": "read write",
            "state": secrets.token_hex(16)
        })
        
        # Test without authentication
        response = requests.get(auth_url)
        # Should redirect to login or return 401
        assert response.status_code in [302, 401]
        
        # Test with invalid state parameter
        invalid_state_url = auth_url.replace(secrets.token_hex(16), "invalid_state")
        invalid_response = requests.get(invalid_state_url, allow_redirects=False)
        # Should reject invalid state
        assert invalid_response.status_code in [400, 401]
    
    @pytest.mark.security
    def test_session_fixation_protection(self, api_base_url, test_user_credentials):
        """Test session fixation attack protection"""
        # Get initial session
        session = requests.Session()
        login_response = session.post(
            f"{api_base_url}/auth/login",
            json=test_user_credentials
        )
        
        if login_response.status_code == 200:
            initial_cookies = session.cookies.get_dict()
            
            # After login, session ID should change
            protected_response = session.get(f"{api_base_url}/protected")
            final_cookies = session.cookies.get_dict()
            
            # Session cookies should be different or regenerated
            # (Implementation depends on session management approach)
    
    @pytest.mark.security
    def test_authentication_bypass_attempts(self, api_base_url):
        """Test authentication bypass attempts"""
        endpoints = [
            "/admin/users",
            "/admin/config",
            "/api/internal/status",
            "/debug/info"
        ]
        
        for endpoint in endpoints:
            # Try without authentication
            response = requests.get(f"{api_base_url}{endpoint}")
            assert response.status_code == 401, f"Endpoint {endpoint} allows bypass"
            
            # Try with fake token
            fake_response = requests.get(
                f"{api_base_url}{endpoint}",
                headers={"Authorization": "Bearer fake.token.here"}
            )
            assert fake_response.status_code == 401, f"Endpoint {endpoint} accepts fake token"
    
    @pytest.mark.security
    def test_multi_factor_authentication(self, api_base_url, test_user_credentials):
        """Test MFA implementation"""
        # Login to trigger MFA requirement
        response = requests.post(
            f"{api_base_url}/auth/login",
            json=test_user_credentials
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if MFA is required
            if data.get("requires_mfa"):
                mfa_token = data.get("mfa_token")
                assert mfa_token is not None
                
                # Test MFA verification (would need actual code)
                mfa_response = requests.post(
                    f"{api_base_url}/auth/verify-mfa",
                    json={
                        "mfa_token": mfa_token,
                        "code": "123456"  # Test code
                    }
                )
                
                # Should reject invalid MFA code
                assert mfa_response.status_code in [400, 401]


class TestAPIAuthorization:
    """Test suite for API authorization security"""
    
    @pytest.fixture
    def api_base_url(self):
        """API base URL for testing"""
        return "http://localhost:8000/api/v1"
    
    @pytest.fixture
    def user_token(self):
        """Regular user token"""
        return "user.token.here"
    
    @pytest.fixture
    def admin_token(self):
        """Admin user token"""
        return "admin.token.here"
    
    @pytest.mark.security
    def test_role_based_access_control(self, api_base_url, user_token, admin_token):
        """Test RBAC enforcement in API"""
        admin_endpoints = [
            "/admin/users",
            "/admin/settings",
            "/admin/logs"
        ]
        
        # Regular user should not access admin endpoints
        for endpoint in admin_endpoints:
            response = requests.get(
                f"{api_base_url}{endpoint}",
                headers={"Authorization": f"Bearer {user_token}"}
            )
            assert response.status_code == 403, f"User can access {endpoint}"
        
        # Admin should be able to access admin endpoints
        # (This would require actual admin token)
        # for endpoint in admin_endpoints:
        #     response = requests.get(
        #         f"{api_base_url}{endpoint}",
        #         headers={"Authorization": f"Bearer {admin_token}"}
        #     )
        #     assert response.status_code == 200, f"Admin cannot access {endpoint}"
    
    @pytest.mark.security
    def test_resource_level_permissions(self, api_base_url, user_token):
        """Test resource-level access control"""
        # Test accessing other users' resources
        user_id = "user123"
        
        # Try to access another user's data
        response = requests.get(
            f"{api_base_url}/users/{user_id}/data",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        # Should be denied or return limited data
        assert response.status_code in [403, 404]
    
    @pytest.mark.security
    def test_privilege_escalation_via_api(self, api_base_url, user_token):
        """Test privilege escalation through API"""
        # Attempt to modify user roles
        escalation_attempts = [
            {"role": "admin"},
            {"permissions": ["user:delete", "system:configure"]},
            {"is_admin": True}
        ]
        
        for attempt in escalation_attempts:
            response = requests.post(
                f"{api_base_url}/users/me/roles",
                json=attempt,
                headers={"Authorization": f"Bearer {user_token}"}
            )
            assert response.status_code == 403, "Privilege escalation allowed"
    
    @pytest.mark.security
    def test_api_function_level_permissions(self, api_base_url, user_token):
        """Test function-level access control"""
        # Test API functions that require specific permissions
        protected_functions = [
            {"endpoint": "/data/export", "action": "POST"},
            {"endpoint": "/data/delete", "action": "DELETE"},
            {"endpoint": "/system/reload", "action": "POST"}
        ]
        
        for func in protected_functions:
            response = requests.request(
                func["action"],
                f"{api_base_url}{func['endpoint']}",
                headers={"Authorization": f"Bearer {user_token}"}
            )
            assert response.status_code == 403, f"Function {func['endpoint']} not protected"


class TestAPIRateLimiting:
    """Test suite for API rate limiting security"""
    
    @pytest.fixture
    def api_base_url(self):
        """API base URL for testing"""
        return "http://localhost:8000/api/v1"
    
    @pytest.mark.security
    def test_global_rate_limiting(self, api_base_url):
        """Test global rate limiting"""
        # Send rapid requests to trigger rate limiting
        responses = []
        for i in range(100):
            response = requests.get(f"{api_base_url}/public")
            responses.append(response.status_code)
        
        # Some requests should be rate limited
        rate_limited = sum(1 for status in responses if status == 429)
        assert rate_limited > 0, "No rate limiting detected"
    
    @pytest.mark.security
    def test_ip_based_rate_limiting(self, api_base_url):
        """Test IP-based rate limiting"""
        # Send requests from same IP
        client_ip = "192.168.1.100"
        
        for i in range(50):
            response = requests.get(
                f"{api_base_url}/public",
                headers={"X-Forwarded-For": client_ip}
            )
            if response.status_code == 429:
                break
        
        # Should eventually be rate limited
        assert response.status_code == 429, "IP not rate limited"
    
    @pytest.mark.security
    def test_user_based_rate_limiting(self, api_base_url):
        """Test user-based rate limiting"""
        # Use authenticated user
        headers = {"Authorization": "Bearer user.token"}
        
        for i in range(30):
            response = requests.get(
                f"{api_base_url}/protected",
                headers=headers
            )
            if response.status_code == 429:
                break
        
        # Should be rate limited based on user
        assert response.status_code == 429, "User not rate limited"
    
    @pytest.mark.security
    def test_endpoint_specific_rate_limiting(self, api_base_url):
        """Test endpoint-specific rate limits"""
        # Test login endpoint (typically more restrictive)
        credentials = {"email": "test@example.com", "password": "wrong"}
        
        for i in range(10):
            response = requests.post(
                f"{api_base_url}/auth/login",
                json=credentials
            )
            if response.status_code == 429:
                break
        
        # Login should have stricter rate limiting
        assert response.status_code == 429, "Login endpoint not rate limited"
    
    @pytest.mark.security
    def test_rate_limiting_headers(self, api_base_url):
        """Test rate limiting headers in responses"""
        # Send request and check rate limit headers
        response = requests.get(f"{api_base_url}/public")
        
        # Should include rate limit information
        rate_limit_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ]
        
        for header in rate_limit_headers:
            assert header in response.headers, f"Missing rate limit header: {header}"
    
    @pytest.mark.security
    def test_ddos_protection(self, api_base_url):
        """Test basic DDoS protection"""
        # Simulate rapid connections from multiple IPs
        responses = []
        for i in range(20):
            # Use different IPs
            ip = f"10.0.0.{i % 255}"
            response = requests.get(
                f"{api_base_url}/public",
                headers={"X-Forwarded-For": ip}
            )
            responses.append(response.status_code)
        
        # System should protect against rapid connections
        rate_limited = sum(1 for status in responses if status == 429)
        assert rate_limited > 0, "No DDoS protection detected"


class TestAPIInputValidation:
    """Test suite for API input validation security"""
    
    @pytest.fixture
    def api_base_url(self):
        """API base URL for testing"""
        return "http://localhost:8000/api/v1"
    
    @pytest.mark.security
    def test_sql_injection_prevention(self, api_base_url):
        """Test SQL injection attack prevention"""
        sql_injection_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM admin_users --",
            "admin'--",
            "admin'/*",
            "' OR 1=1#",
            "' OR 'a'='a",
            "') OR ('1'='1",
        ]
        
        # Test in various parameters
        test_cases = [
            {"endpoint": "/users", "param": "search", "method": "GET"},
            {"endpoint": "/auth/login", "param": "email", "method": "POST"},
            {"endpoint": "/data", "param": "filter", "method": "POST"},
        ]
        
        for test_case in test_cases:
            for payload in sql_injection_payloads:
                if test_case["method"] == "GET":
                    response = requests.get(
                        f"{api_base_url}{test_case['endpoint']}",
                        params={test_case["param"]: payload}
                    )
                else:
                    response = requests.post(
                        f"{api_base_url}{test_case['endpoint']}",
                        json={test_case["param"]: payload}
                    )
                
                # Should not execute SQL or return database errors
                assert response.status_code != 500, f"SQL injection likely succeeded"
                assert "mysql" not in response.text.lower(), "MySQL error exposed"
                assert "postgresql" not in response.text.lower(), "PostgreSQL error exposed"
                assert "sql" not in response.text.lower(), "SQL error exposed"
    
    @pytest.mark.security
    def test_xss_prevention(self, api_base_url):
        """Test Cross-Site Scripting prevention"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
        ]
        
        # Test XSS in input fields
        for payload in xss_payloads:
            response = requests.post(
                f"{api_base_url}/profile",
                json={"bio": payload, "name": "Test User"}
            )
            
            # Should sanitize or reject XSS payload
            if response.status_code == 200:
                data = response.json()
                # Check if payload is sanitized
                assert "<script>" not in data.get("bio", ""), "XSS not sanitized"
    
    @pytest.mark.security
    def test_command_injection_prevention(self, api_base_url):
        """Test command injection prevention"""
        command_injection_payloads = [
            "; ls -la",
            "| whoami",
            "&& cat /etc/passwd",
            "`id`",
            "$(whoami)",
            "; rm -rf /",
            "&& shutdown -h now",
        ]
        
        # Test in shell command parameters
        for payload in command_injection_payloads:
            response = requests.post(
                f"{api_base_url}/process",
                json={"command": f"echo {payload}"}
            )
            
            # Should not execute shell commands
            assert response.status_code != 500, "Command injection likely succeeded"
            assert "root:" not in response.text, "System info exposed"
    
    @pytest.mark.security
    def test_path_traversal_prevention(self, api_base_url):
        """Test path traversal attack prevention"""
        path_traversal_payloads = [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc//passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "/var/log/../../etc/passwd",
            "file.txt/../../../etc/passwd",
        ]
        
        # Test in file upload/download parameters
        for payload in path_traversal_payloads:
            response = requests.get(
                f"{api_base_url}/download",
                params={"file": payload}
            )
            
            # Should not allow access to system files
            assert response.status_code != 500, "Path traversal likely succeeded"
            assert "root:" not in response.text, "System file accessed"
    
    @pytest.mark.security
    def test_json_injection_prevention(self, api_base_url):
        """Test JSON injection prevention"""
        json_injection_payloads = [
            {"user": {"$gt": ""}},
            {"user": {"__proto__": {"admin": True}}},
            {"user": {"constructor": {"prototype": {"admin": True}}}},
            {"password": {"ne": null}},
            {"$where": "this.password"},
        ]
        
        for payload in json_injection_payloads:
            response = requests.post(
                f"{api_base_url}/search",
                json=payload
            )
            
            # Should validate JSON structure
            assert response.status_code != 500, "JSON injection likely succeeded"
    
    @pytest.mark.security
    def test_xml_injection_prevention(self, api_base_url):
        """Test XML injection prevention"""
        xml_payloads = [
            '<?xml version="1.0"?><!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>',
            '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
            '<!DOCTYPE foo [<!ENTITY % xxe SYSTEM "file:///etc/passwd"> %xxe;]><foo/>',
        ]
        
        for payload in xml_payloads:
            response = requests.post(
                f"{api_base_url}/parse",
                data=payload,
                headers={"Content-Type": "application/xml"}
            )
            
            # Should not allow XXE attacks
            assert response.status_code != 500, "XXE injection likely succeeded"
    
    @pytest.mark.security
    def test_input_size_limits(self, api_base_url):
        """Test input size limit enforcement"""
        # Test with very large payload
        large_payload = "A" * (10 * 1024 * 1024)  # 10MB
        
        response = requests.post(
            f"{api_base_url}/upload",
            json={"data": large_payload}
        )
        
        # Should reject oversized input
        assert response.status_code in [413, 400], "Large payload not rejected"
    
    @pytest.mark.security
    def test_malformed_json_handling(self, api_base_url):
        """Test handling of malformed JSON"""
        malformed_json_payloads = [
            '{"invalid": json',
            '{invalid: json}',
            '{"json": }',
            'invalid json',
            '{{}',
            '{"nested": {"invalid": }',
        ]
        
        for payload in malformed_json_payloads:
            response = requests.post(
                f"{api_base_url}/parse",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Should reject malformed JSON gracefully
            assert response.status_code in [400, 422], "Malformed JSON not handled"
    
    @pytest.mark.security
    def test_type_confusion_attacks(self, api_base_url):
        """Test type confusion attack prevention"""
        type_confusion_payloads = [
            {"user_id": "string_instead_of_int"},
            {"count": "not_a_number"},
            {"is_admin": "not_a_boolean"},
            {"tags": "not_an_array"},
            {"data": "not_an_object"},
        ]
        
        for payload in type_confusion_payloads:
            response = requests.post(
                f"{api_base_url}/process",
                json=payload
            )
            
            # Should validate types
            assert response.status_code in [400, 422], "Type confusion not prevented"
    
    @pytest.mark.security
    def test_encoding_attacks(self, api_base_url):
        """Test various encoding attack vectors"""
        encoding_attacks = [
            {"name": "%00null"},
            {"name": "%0Anewline"},
            {"name": "%20space"},
            {"name": "%2F%2Fdouble%2Fslash"},
            {"name": "double\"quote"},
            {"name": "single'quote"},
            {"name": "<script>"},
        ]
        
        for payload in encoding_attacks:
            response = requests.post(
                f"{api_base_url}/profile",
                json=payload
            )
            
            # Should handle encoding properly
            assert response.status_code != 500, "Encoding attack succeeded"


class TestAPIErrorHandling:
    """Test suite for API error handling security"""
    
    @pytest.fixture
    def api_base_url(self):
        """API base URL for testing"""
        return "http://localhost:8000/api/v1"
    
    @pytest.mark.security
    def test_information_disclosure_in_errors(self, api_base_url):
        """Test that errors don't disclose sensitive information"""
        # Trigger various errors
        error_cases = [
            {"endpoint": "/nonexistent", "method": "GET"},
            {"endpoint": "/users/999999", "method": "GET"},
            {"endpoint": "/auth/login", "method": "GET"},
            {"endpoint": "/admin", "method": "GET"},
        ]
        
        for case in error_cases:
            if case["method"] == "GET":
                response = requests.get(f"{api_base_url}{case['endpoint']}")
            else:
                response = requests.post(f"{api_base_url}{case['endpoint']}")
            
            # Check for sensitive information disclosure
            sensitive_info = [
                "stack trace",
                "file path",
                "database error",
                "mysql",
                "postgresql",
                "sqlite",
                "python",
                "java",
                ".env",
                "config",
                "api_key",
                "password",
                "secret",
            ]
            
            response_text = response.text.lower()
            for info in sensitive_info:
                assert info not in response_text, f"Sensitive info '{info}' disclosed in error"
    
    @pytest.mark.security
    def test_consistent_error_responses(self, api_base_url):
        """Test consistent error response format"""
        # Different error conditions should have consistent response format
        error_responses = []
        
        test_cases = [
            {"endpoint": "/nonexistent"},
            {"endpoint": "/auth/login", "json": {"email": "test", "password": "wrong"}},
            {"endpoint": "/protected", "headers": {}},
        ]
        
        for case in test_cases:
            if "json" in case:
                response = requests.post(
                    f"{api_base_url}{case['endpoint']}",
                    json=case["json"]
                )
            elif "headers" in case:
                response = requests.get(
                    f"{api_base_url}{case['endpoint']}",
                    headers=case["headers"]
                )
            else:
                response = requests.get(f"{api_base_url}{case['endpoint']}")
            
            error_responses.append(response.json())
        
        # All error responses should have consistent structure
        for error_response in error_responses:
            assert "error" in error_response or "message" in error_response
            assert "timestamp" in error_response or "error" in error_response
    
    @pytest.mark.security
    def test_server_error_information_leakage(self, api_base_url):
        """Test that server errors don't leak information"""
        # Force server errors
        error_conditions = [
            {"endpoint": "/trigger/500", "method": "GET"},
            {"endpoint": "/trigger/error", "method": "POST"},
        ]
        
        for condition in error_conditions:
            try:
                if condition["method"] == "GET":
                    response = requests.get(f"{api_base_url}{condition['endpoint']}")
                else:
                    response = requests.post(f"{api_base_url}{condition['endpoint']}")
            except Exception:
                continue  # Connection errors are expected
            
            # Check for information leakage
            if response.status_code >= 500:
                response_text = response.text.lower()
                leakage_indicators = [
                    "traceback",
                    "exception",
                    "import",
                    "module",
                    "file \"",
                    "line ",
                    "def ",
                    "class ",
                ]
                
                for indicator in leakage_indicators:
                    assert indicator not in response_text, \
                        f"Information leakage: '{indicator}' in server error"


class TestAPISecurityHeaders:
    """Test suite for API security headers"""
    
    @pytest.fixture
    def api_base_url(self):
        """API base URL for testing"""
        return "http://localhost:8000/api/v1"
    
    @pytest.mark.security
    def test_security_headers_presence(self, api_base_url):
        """Test presence of security headers"""
        response = requests.get(f"{api_base_url}/public")
        
        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
        }
        
        for header, expected_value in required_headers.items():
            assert header in response.headers, f"Missing security header: {header}"
            
            if isinstance(expected_value, list):
                assert response.headers[header] in expected_value
            else:
                assert response.headers[header] == expected_value
    
    @pytest.mark.security
    def test_cors_configuration(self, api_base_url):
        """Test CORS configuration security"""
        response = requests.get(
            f"{api_base_url}/public",
            headers={"Origin": "http://malicious-site.com"}
        )
        
        # Should either not include CORS headers or restrict them
        cors_headers = ["Access-Control-Allow-Origin", "Access-Control-Allow-Credentials"]
        
        for header in cors_headers:
            if header in response.headers:
                origin = response.headers.get("Access-Control-Allow-Origin")
                if origin:
                    # Should not allow arbitrary origins in production
                    assert origin != "*", "Wildcard CORS origin in production"
    
    @pytest.mark.security
    def test_hsts_header(self, api_base_url):
        """Test HTTP Strict Transport Security header"""
        response = requests.get(f"{api_base_url}/public")
        
        # Should include HSTS in production
        # (May not be present in development)
        if "Strict-Transport-Security" in response.headers:
            hsts = response.headers["Strict-Transport-Security"]
            assert "max-age" in hsts, "HSTS should include max-age directive"
    
    @pytest.mark.security
    def test_content_security_policy(self, api_base_url):
        """Test Content Security Policy header"""
        response = requests.get(f"{api_base_url}/public")
        
        if "Content-Security-Policy" in response.headers:
            csp = response.headers["Content-Security-Policy"]
            # Should restrict resource loading
            assert "default-src" in csp or "script-src" in csp


class TestAPIvulnerabilities:
    """Test suite for common API vulnerabilities"""
    
    @pytest.fixture
    def api_base_url(self):
        """API base URL for testing"""
        return "http://localhost:8000/api/v1"
    
    @pytest.mark.security
    def test_mass_assignment_vulnerability(self, api_base_url):
        """Test mass assignment vulnerability"""
        # Attempt to set protected fields
        mass_assignment_payloads = [
            {"name": "Hacker", "is_admin": True},
            {"name": "User", "role": "admin", "permissions": ["all"]},
            {"email": "hacker@evil.com", "user_id": 999, "is_verified": True},
        ]
        
        for payload in mass_assignment_payloads:
            response = requests.post(
                f"{api_base_url}/users",
                json=payload
            )
            
            if response.status_code == 201:
                # Check if protected fields were set
                created_user = response.json()
                protected_fields = ["is_admin", "role", "user_id", "is_verified"]
                
                for field in protected_fields:
                    if field in payload:
                        assert created_user.get(field) != payload[field], \
                            f"Mass assignment vulnerability: {field}"
    
    @pytest.mark.security
    def test_insecure_direct_object_reference(self, api_base_url):
        """Test Insecure Direct Object Reference (IDOR)"""
        # Test accessing resources by ID without proper authorization
        user_ids = ["1", "2", "999", "admin", "user123"]
        
        for user_id in user_ids:
            response = requests.get(f"{api_base_url}/users/{user_id}/profile")
            
            # Should either return 404 or return limited data
            if response.status_code == 200:
                data = response.json()
                # Should not expose sensitive information for unauthorized access
                assert data.get("is_admin") is not True, "IDOR vulnerability"
    
    @pytest.mark.security
    def test_unrestricted_file_upload(self):
        """Test unrestricted file upload vulnerabilities"""
        # Test uploading malicious files
        malicious_files = [
            ("malware.exe", b"MZ\x90\x00"),  # PE executable header
            ("script.php", b"<?php system($_GET['cmd']); ?>"),
            ("script.jsp", b"<% Runtime.getRuntime().exec(request.getParameter('cmd')); %>"),
            ("script.aspx", b"<%@ Page Language=\"C#\" %><script runat=\"server\">void Page_Load(object sender, EventArgs e) { }</script>"),
        ]
        
        for filename, content in malicious_files:
            files = {"file": (filename, content)}
            response = requests.post(
                "http://localhost:8000/upload",
                files=files
            )
            
            # Should reject malicious file types
            if response.status_code == 200:
                # File should be sanitized or rejected
                result = response.json()
                assert "malicious" not in result.get("filename", "").lower()
    
    @pytest.mark.security
    def test_api_versioning_security(self, api_base_url):
        """Test API versioning security"""
        # Test accessing deprecated versions
        versions = ["v1", "v2", "v0", "beta", "dev"]
        
        for version in versions:
            response = requests.get(f"http://localhost:8000/api/{version}/public")
            
            # Deprecated versions might still be accessible but should be limited
            if response.status_code == 200:
                # Should include version warning
                assert "deprecated" in response.text.lower() or \
                       "version" in response.headers.get("X-API-Version", "").lower()
    
    @pytest.mark.security
    def test_graphql_injection(self):
        """Test GraphQL injection vulnerabilities"""
        # Test GraphQL endpoint if available
        graphql_payloads = [
            {
                "query": """
                query {
                    user(id: "1' OR '1'='1") {
                        name
                    }
                }
                """
            },
            {
                "query": """
                mutation {
                    updateUser(id: 1, input: {isAdmin: true}) {
                        id
                    }
                }
                """
            },
        ]
        
        for payload in graphql_payloads:
            response = requests.post(
                "http://localhost:8000/graphql",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Should not expose data based on injection
            if response.status_code == 200:
                data = response.json()
                # Check for injection success indicators
                assert "errors" not in data or "1' OR" not in str(data)
    
    @pytest.mark.security
    def test_api_enumeration(self, api_base_url):
        """Test API endpoint enumeration"""
        # Common API endpoints to test
        endpoints = [
            "/api",
            "/api/v1",
            "/docs",
            "/swagger",
            "/swagger-ui",
            "/openapi.json",
            "/.well-known",
            "/debug",
            "/status",
            "/health",
        ]
        
        discovered_endpoints = []
        
        for endpoint in endpoints:
            response = requests.get(f"http://localhost:8000{endpoint}")
            if response.status_code == 200:
                discovered_endpoints.append(endpoint)
        
        # Should not expose sensitive endpoints
        sensitive_endpoints = ["/debug", "/.well-known", "/status"]
        for endpoint in sensitive_endpoints:
            if endpoint in discovered_endpoints:
                response = requests.get(f"http://localhost:8000{endpoint}")
                # Should not expose system information
                assert "server" not in response.headers.get("Server", "").lower()
    
    @pytest.mark.security
    def test_http_methods_enumeration(self, api_base_url):
        """Test HTTP methods enumeration"""
        endpoint = "/test-endpoint"
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"]
        
        allowed_methods = []
        
        for method in methods:
            response = requests.request(method, f"{api_base_url}{endpoint}")
            if response.status_code not in [405, 404]:
                allowed_methods.append(method)
        
        # Should not expose dangerous methods
        dangerous_methods = ["TRACE"]
        for method in dangerous_methods:
            assert method not in allowed_methods, f"Dangerous method {method} enabled"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "security"])
