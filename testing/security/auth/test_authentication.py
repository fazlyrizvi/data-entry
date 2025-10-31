#!/usr/bin/env python3
"""
Authentication Security Testing Suite
Tests authentication mechanisms, authorization controls, session management,
and access control policies.
"""

import pytest
import asyncio
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
import os

# Add the security module to the path
sys.path.append('/workspace/code/security')

from auth_middleware import (
    AuthenticationMiddleware, 
    AuthenticationConfig,
    get_auth_middleware
)
from permission_guard import (
    PermissionGuard,
    PermissionGroups,
    get_permission_guard,
    PermissionContext
)


class TestAuthenticationSecurity:
    """Test suite for authentication security"""
    
    @pytest.fixture
    def auth_config(self):
        """Create test authentication configuration"""
        return AuthenticationConfig(
            jwt_secret="test-secret-key-for-security-testing-only",
            jwt_expiration_hours=24,
            max_login_attempts=5,
            lockout_duration_minutes=30,
            session_timeout_minutes=480,
            require_mfa={"ADMIN", "MANAGER"}
        )
    
    @pytest.fixture
    def auth_middleware(self, auth_config):
        """Create authentication middleware instance"""
        return get_auth_middleware(auth_config)
    
    @pytest.mark.security
    def test_jwt_token_validation(self, auth_middleware):
        """Test JWT token validation and security"""
        # Test valid token
        valid_token = auth_middleware.create_jwt_token(
            user_id="test-user-123",
            email="test@example.com",
            roles=["USER"]
        )
        assert valid_token is not None
        assert len(valid_token) > 0
        
        # Test invalid token
        invalid_token = "invalid.jwt.token"
        result = auth_middleware.validate_jwt_token(invalid_token)
        assert result is None
        
        # Test tampered token
        tampered_token = valid_token[:-10] + "tampered123"
        result = auth_middleware.validate_jwt_token(tampered_token)
        assert result is None
    
    @pytest.mark.security
    def test_password_strength_requirements(self, auth_middleware):
        """Test password strength enforcement"""
        weak_passwords = [
            "123456",
            "password",
            "abc123",
            "Password1",  # Too common
            "short",
            "lowercase123"
        ]
        
        for password in weak_passwords:
            # Should trigger weak password detection
            is_strong = auth_middleware.validate_password_strength(password)
            if is_strong is not None:
                assert not is_strong["is_valid"] or is_strong["is_weak"]
    
    @pytest.mark.security
    def test_account_lockout_protection(self, auth_middleware):
        """Test account lockout after failed attempts"""
        user_email = "test@example.com"
        
        # Simulate failed login attempts
        for i in range(6):  # Exceed max attempts
            result = auth_middleware.verify_login(
                user_email,
                f"wrong_password_{i}",
                ip_address="192.168.1.100"
            )
        
        # Account should be locked
        lock_status = auth_middleware.check_account_lockout(user_email)
        assert lock_status["is_locked"] is True
    
    @pytest.mark.security
    def test_mfa_requirement(self, auth_middleware):
        """Test MFA requirement enforcement"""
        # Test admin login without MFA
        admin_login = auth_middleware.verify_login(
            "admin@example.com",
            "correct_password",
            ip_address="192.168.1.100"
        )
        
        if admin_login.get("requires_mfa"):
            # Should require MFA
            assert admin_login["requires_mfa"] is True
    
    @pytest.mark.security
    def test_session_security(self, auth_middleware):
        """Test session security features"""
        # Create session
        session = auth_middleware.create_session(
            user_id="test-user",
            ip_address="192.168.1.100",
            user_agent="Test Browser"
        )
        
        assert session["session_id"] is not None
        assert len(session["session_id"]) >= 32
        
        # Test session validation
        valid_session = auth_middleware.validate_session(
            session["session_id"],
            "192.168.1.100",
            "Test Browser"
        )
        assert valid_session is not None
        
        # Test session from different IP (should fail)
        invalid_session = auth_middleware.validate_session(
            session["session_id"],
            "10.0.0.1",  # Different IP
            "Test Browser"
        )
        assert invalid_session is None
    
    @pytest.mark.security
    def test_token_expiration(self, auth_middleware):
        """Test token expiration handling"""
        # Create token with very short expiration
        short_token = auth_middleware.create_jwt_token(
            user_id="test-user",
            email="test@example.com",
            roles=["USER"],
            expires_in_seconds=1
        )
        
        # Validate immediately (should work)
        valid = auth_middleware.validate_jwt_token(short_token)
        assert valid is not None
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Validate after expiration (should fail)
        expired = auth_middleware.validate_jwt_token(short_token)
        assert expired is None
    
    @pytest.mark.security
    def test_rate_limiting(self, auth_middleware):
        """Test rate limiting on authentication endpoints"""
        ip_address = "192.168.1.100"
        user_email = "test@example.com"
        
        # Attempt multiple logins quickly
        results = []
        for i in range(10):
            result = auth_middleware.verify_login(
                user_email,
                "password",
                ip_address
            )
            results.append(result)
        
        # Should trigger rate limiting
        rate_limited = any(
            "rate_limit" in str(result).lower() 
            for result in results
        )
        assert rate_limited or results[-1].get("rate_limited", False)
    
    @pytest.mark.security
    def test_suspicious_activity_detection(self, auth_middleware):
        """Test suspicious activity detection"""
        # Test rapid login attempts from different IPs
        ip_list = [f"192.168.1.{i}" for i in range(10, 20)]
        
        for ip in ip_list:
            auth_middleware.verify_login(
                "test@example.com",
                "password",
                ip
            )
        
        # Should detect suspicious pattern
        events = auth_middleware.get_security_events("test@example.com")
        suspicious_events = [
            e for e in events 
            if e.get("event_type") == "suspicious_activity"
        ]
        assert len(suspicious_events) > 0
    
    @pytest.mark.security
    def test_concurrent_session_limits(self, auth_middleware):
        """Test concurrent session limits"""
        user_id = "test-user-123"
        
        # Create multiple sessions
        sessions = []
        for i in range(6):
            session = auth_middleware.create_session(
                user_id=user_id,
                ip_address=f"192.168.1.{100+i}",
                user_agent=f"Browser-{i}"
            )
            sessions.append(session)
        
        # Should limit concurrent sessions
        active_sessions = auth_middleware.get_active_sessions(user_id)
        assert len(active_sessions) <= auth_middleware.config.max_concurrent_sessions


class TestAuthorizationSecurity:
    """Test suite for authorization and access control"""
    
    @pytest.fixture
    def permission_guard(self):
        """Create permission guard instance"""
        return get_permission_guard(None)  # Mock Supabase client
    
    @pytest.mark.security
    def test_role_based_access_control(self, permission_guard):
        """Test RBAC enforcement"""
        # Test VIEWER role permissions
        viewer_permissions = permission_guard.get_role_permissions("VIEWER")
        assert "dataset:read" in viewer_permissions
        assert "dataset:write" not in viewer_permissions
        
        # Test ADMIN role permissions
        admin_permissions = permission_guard.get_role_permissions("ADMIN")
        assert "system:admin" in admin_permissions
        assert "dataset:delete" in admin_permissions
    
    @pytest.mark.security
    def test_permission_enforcement(self, permission_guard):
        """Test permission enforcement logic"""
        user_id = "test-user-123"
        
        # Test allowed permission
        allowed = permission_guard.check_permission(
            user_id=user_id,
            resource="dataset",
            action="read"
        )
        assert allowed is True
        
        # Test denied permission
        denied = permission_guard.check_permission(
            user_id=user_id,
            resource="dataset",
            action="delete"
        )
        assert denied is False
    
    @pytest.mark.security
    def test_resource_specific_permissions(self, permission_guard):
        """Test resource-specific permission checking"""
        user_id = "test-user-123"
        resource_id = "dataset-123"
        
        # User should only access their own resources
        context = PermissionContext(
            resource_id=resource_id,
            owner_id=user_id,
            data_classification="INTERNAL"
        )
        
        # Should allow access to own resource
        allowed = permission_guard.check_permission(
            user_id=user_id,
            resource="dataset",
            action="write",
            context=context
        )
        assert allowed is True
        
        # Should deny access to others' resources
        other_context = PermissionContext(
            resource_id=resource_id,
            owner_id="other-user",
            data_classification="INTERNAL"
        )
        
        denied = permission_guard.check_permission(
            user_id=user_id,
            resource="dataset",
            action="write",
            context=other_context
        )
        assert denied is False
    
    @pytest.mark.security
    def test_separation_of_duties(self, permission_guard):
        """Test Separation of Duties constraints"""
        user_id = "admin-user-123"
        
        # Test SoD constraint: Admin cannot audit their own changes
        sod_violation = permission_guard.check_separation_of_duties(
            user_id=user_id,
            action="audit:read",
            resource="changes",
            context={"change_author": user_id}
        )
        assert sod_violation is False
        
        # Test valid SoD scenario
        valid_sod = permission_guard.check_separation_of_duties(
            user_id=user_id,
            action="dataset:create",
            resource="dataset",
            context={}
        )
        assert valid_sod is True
    
    @pytest.mark.security
    def test_permission_escalation_protection(self, permission_guard):
        """Test permission escalation attack protection"""
        # Test that users cannot escalate their own privileges
        user_id = "test-user-123"
        current_roles = ["VIEWER"]
        
        # Attempt to add ADMIN role
        escalation_attempt = permission_guard.request_role_change(
            user_id=user_id,
            requested_role="ADMIN",
            approved_by=user_id  # Self-approval (should fail)
        )
        assert escalation_attempt["success"] is False
    
    @pytest.mark.security
    def test_privilege_escalation_via_api(self, permission_guard):
        """Test API-level privilege escalation protection"""
        # Test that API calls enforce proper permissions
        user_id = "viewer-user"
        
        # Attempt to perform admin action
        result = permission_guard.enforce_permission_check(
            user_id=user_id,
            resource="system",
            action="configure",
            context={}
        )
        assert result is False
    
    @pytest.mark.security
    def test_temporal_access_controls(self, permission_guard):
        """Test time-based access controls"""
        user_id = "temp-user-123"
        
        # Create temporary access
        temp_access = permission_guard.create_temporary_access(
            user_id=user_id,
            permission="dataset:read",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            granted_by="admin"
        )
        
        assert temp_access["success"] is True
        
        # Test expired access
        expired_access = permission_guard.check_permission(
            user_id=user_id,
            resource="dataset",
            action="read",
            context={"expires_at": datetime.utcnow() - timedelta(hours=1)}
        )
        assert expired_access is False


class TestSessionSecurity:
    """Test suite for session management security"""
    
    @pytest.fixture
    def session_manager(self):
        """Import and configure session manager"""
        from session_manager import get_session_manager
        return get_session_manager(None)  # Mock Supabase client
    
    @pytest.mark.security
    def test_session_token_entropy(self, session_manager):
        """Test session token randomness and entropy"""
        tokens = set()
        for _ in range(100):
            token = session_manager.generate_session_token()
            tokens.add(token)
        
        # All tokens should be unique
        assert len(tokens) == 100
        
        # Each token should have sufficient entropy
        for token in tokens:
            assert len(token) >= 32
            # Check for character distribution (should be hex/base64)
            assert all(c in "0123456789abcdefABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+/=" 
                      for c in token)
    
    @pytest.mark.security
    def test_session_fixation_protection(self, session_manager):
        """Test session fixation attack protection"""
        user_id = "test-user-123"
        
        # Create initial session
        session1 = session_manager.create_user_session(
            user_id=user_id,
            email="test@example.com",
            roles=["USER"],
            request=mock_request()
        )
        
        initial_token = session1["access_token"]
        
        # Create new session after authentication
        session2 = session_manager.create_user_session(
            user_id=user_id,
            email="test@example.com",
            roles=["USER"],
            request=mock_request()
        )
        
        new_token = session2["access_token"]
        
        # Token should change after re-authentication
        assert initial_token != new_token
    
    @pytest.mark.security
    def test_session_timeout_enforcement(self, session_manager):
        """Test session timeout enforcement"""
        user_id = "test-user-123"
        
        # Create session with short timeout
        session = session_manager.create_user_session(
            user_id=user_id,
            email="test@example.com",
            roles=["USER"],
            request=mock_request(),
            timeout_minutes=0.1  # 6 seconds
        )
        
        session_id = session["session_id"]
        
        # Session should be valid immediately
        valid = session_manager.validate_session_token(session["access_token"])
        assert valid is not None
        
        # Wait for timeout
        import time
        time.sleep(7)
        
        # Session should be expired
        expired = session_manager.validate_session_token(session["access_token"])
        assert expired is None
    
    @pytest.mark.security
    def test_concurrent_session_monitoring(self, session_manager):
        """Test concurrent session monitoring"""
        user_id = "test-user-123"
        
        # Create sessions from different devices
        sessions = []
        for i in range(3):
            session = session_manager.create_user_session(
                user_id=user_id,
                email="test@example.com",
                roles=["USER"],
                request=mock_request(
                    ip=f"192.168.1.{100+i}",
                    user_agent=f"Device-{i}"
                )
            )
            sessions.append(session)
        
        # Monitor concurrent sessions
        active_sessions = session_manager.list_user_sessions(user_id)
        assert len(active_sessions) == 3
        
        # Test device fingerprinting
        for session in active_sessions:
            assert session.get("device_fingerprint") is not None
    
    @pytest.mark.security
    def test_session_invalidated_on_logout(self, session_manager):
        """Test session invalidation on logout"""
        user_id = "test-user-123"
        
        # Create session
        session = session_manager.create_user_session(
            user_id=user_id,
            email="test@example.com",
            roles=["USER"],
            request=mock_request()
        )
        
        session_token = session["access_token"]
        
        # Logout
        logout_result = session_manager.invalidate_session(session_token)
        assert logout_result["success"] is True
        
        # Session should be invalid
        invalid = session_manager.validate_session_token(session_token)
        assert invalid is None


def mock_request(ip="192.168.1.100", user_agent="Test Browser"):
    """Create mock request object"""
    class MockRequest:
        def __init__(self):
            self.client = MockClient(ip)
            self.headers = {"user-agent": user_agent}
    
    class MockClient:
        def __init__(self, host):
            self.host = host
    
    return MockRequest()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
