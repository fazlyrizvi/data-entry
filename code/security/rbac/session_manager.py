"""
Session Manager for RBAC Security System

This module provides secure session management for user authentication
and authorization state tracking.

Features:
- Secure session token generation and validation
- Session timeout enforcement
- Concurrent session limits
- Session invalidation and cleanup
- Device fingerprinting
- Geolocation tracking
- Audit logging for session events
"""

import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qs, urlparse

import jwt
from fastapi import Request, Response
from pydantic import BaseModel, Field
from supabase import create_client, Client
import redis

# Configure logging
logger = logging.getLogger(__name__)


class SessionInfo(BaseModel):
    """Information about an active session."""
    session_id: str
    user_id: str
    email: str
    roles: List[str]
    ip_address: str
    user_agent: str
    device_fingerprint: str
    location: Optional[Dict[str, str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    is_active: bool = True
    mfa_verified: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionConfig(BaseModel):
    """Configuration for session management."""
    jwt_secret: str = Field(..., env="SESSION_SECRET")
    jwt_algorithm: str = "HS256"
    session_timeout_minutes: int = 480  # 8 hours
    absolute_timeout_minutes: int = 10080  # 7 days
    max_concurrent_sessions: int = 5
    refresh_threshold_minutes: int = 60
    idle_timeout_minutes: int = 30
    device_tracking_enabled: bool = True
    location_tracking_enabled: bool = True
    require_mfa_for_sensitive: bool = True
    session_cookie_name: str = "session_token"
    csrf_token_name: str = "csrf_token"
    secure_cookies: bool = True
    http_only_cookies: bool = True
    same_site_policy: str = "strict"
    cache_ttl_seconds: int = 3600
    
    class Config:
        env_prefix = "SESSION_"


class DeviceFingerprint:
    """Generate and validate device fingerprints."""
    
    @staticmethod
    def generate(user_agent: str, accept_language: str, accept_encoding: str, 
                 platform: str = "", screen_resolution: str = "", timezone: str = "") -> str:
        """Generate device fingerprint from browser headers."""
        fingerprint_data = {
            'user_agent': user_agent,
            'accept_language': accept_language,
            'accept_encoding': accept_encoding,
            'platform': platform,
            'screen_resolution': screen_resolution,
            'timezone': timezone
        }
        
        # Create hash of fingerprint data
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
    
    @staticmethod
    def is_trusted_device(device_fingerprint: str, trusted_devices: Set[str]) -> bool:
        """Check if device is in trusted devices list."""
        return device_fingerprint in trusted_devices


class SessionValidator:
    """Validates session tokens and checks for anomalies."""
    
    def __init__(self, config: SessionConfig, redis_client: redis.Redis):
        self.config = config
        self.redis_client = redis_client
        self.suspicious_threshold = 3
        
    async def validate_session(self, session_token: str) -> Optional[SessionInfo]:
        """Validate session token and return session info."""
        try:
            # Decode JWT token
            payload = jwt.decode(
                session_token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm],
                options={"verify_signature": True, "verify_exp": True}
            )
            
            # Get session from cache/database
            session_id = payload.get('session_id')
            if not session_id:
                return None
            
            session_data = await self._get_session_data(session_id)
            if not session_data:
                return None
            
            session_info = SessionInfo(**session_data)
            
            # Check if session is still active
            if not session_info.is_active:
                return None
            
            # Check timeouts
            if datetime.utcnow() > session_info.expires_at:
                return None
            
            if session_info.last_activity + timedelta(minutes=self.config.idle_timeout_minutes) < datetime.utcnow():
                return None
            
            return session_info
            
        except jwt.ExpiredSignatureError:
            logger.warning("Session token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid session token: {e}")
            return None
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None
    
    async def _get_session_data(self, session_id: str) -> Optional[Dict]:
        """Get session data from cache or database."""
        # Try cache first
        cached_data = await self.redis_client.get(f"session:{session_id}")
        if cached_data:
            return json.loads(cached_data)
        
        # If not in cache, load from database
        try:
            # This would typically query your session table
            # For now, return None (implement based on your DB schema)
            return None
        except Exception as e:
            logger.error(f"Failed to load session data: {e}")
            return None
    
    async def detect_suspicious_activity(self, session_info: SessionInfo, request: Request) -> bool:
        """Detect suspicious session activity."""
        if not self.config.device_tracking_enabled:
            return False
        
        ip_address = self._get_client_ip(request)
        
        # Check for IP address change
        if session_info.ip_address != ip_address:
            # Check if it's a trusted location change
            if not await self._is_trusted_location_change(session_info, ip_address):
                logger.warning(
                    f"Suspicious IP change for session {session_info.session_id}: "
                    f"{session_info.ip_address} -> {ip_address}"
                )
                return True
        
        # Check for User-Agent change
        user_agent = request.headers.get('User-Agent', '')
        if session_info.user_agent != user_agent:
            logger.warning(
                f"User-Agent change for session {session_info.session_id}: "
                f"Different browser/device detected"
            )
            return True
        
        # Check for rapid requests (potential session hijacking)
        recent_requests = await self._get_recent_requests(session_info.session_id)
        if len(recent_requests) > 100:  # Arbitrary threshold
            logger.warning(
                f"High request frequency for session {session_info.session_id}"
            )
            return True
        
        return False
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else 'unknown'
    
    async def _is_trusted_location_change(self, session_info: SessionInfo, new_ip: str) -> bool:
        """Check if IP address change is from trusted location."""
        # Check for corporate VPN or known good IPs
        trusted_ips = await self._get_trusted_ips(session_info.user_id)
        return new_ip in trusted_ips
    
    async def _get_trusted_ips(self, user_id: str) -> Set[str]:
        """Get trusted IP addresses for user."""
        try:
            trusted_ips_data = await self.redis_client.get(f"trusted_ips:{user_id}")
            if trusted_ips_data:
                return set(json.loads(trusted_ips_data))
            return set()
        except Exception as e:
            logger.error(f"Failed to get trusted IPs: {e}")
            return set()
    
    async def _get_recent_requests(self, session_id: str) -> List[Dict]:
        """Get recent requests for session (for rate limiting)."""
        try:
            requests_data = await self.redis_client.lrange(f"session:{session_id}:requests", 0, -1)
            return [json.loads(req) for req in requests_data]
        except Exception as e:
            logger.error(f"Failed to get recent requests: {e}")
            return []


class SessionStore:
    """Manages session storage in Redis and database."""
    
    def __init__(self, config: SessionConfig, redis_client: redis.Redis, supabase: Client):
        self.config = config
        self.redis_client = redis_client
        self.supabase = supabase
        
    async def create_session(self, session_info: SessionInfo) -> str:
        """Create new session and store it."""
        session_id = secrets.token_urlsafe(32)
        session_info.session_id = session_id
        
        # Store in Redis cache
        await self._cache_session(session_info)
        
        # Store in database for persistence
        await self._persist_session(session_info)
        
        # Track concurrent sessions for user
        await self._track_user_session(session_info.user_id, session_id)
        
        logger.info(f"Created session {session_id} for user {session_info.user_id}")
        return session_id
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session information."""
        try:
            # Get current session
            session_data = await self._get_session_data(session_id)
            if not session_data:
                return False
            
            # Update fields
            session_data.update(updates)
            session_data['last_activity'] = datetime.utcnow()
            
            # Save updated session
            session_info = SessionInfo(**session_data)
            await self._cache_session(session_info)
            await self._persist_session(session_info)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False
    
    async def invalidate_session(self, session_id: str, reason: str = "user_logout") -> bool:
        """Invalidate session."""
        try:
            # Mark as inactive in database
            await self._deactivate_session(session_id)
            
            # Remove from cache
            await self.redis_client.delete(f"session:{session_id}")
            
            # Remove from user session tracking
            session_data = await self._get_session_data(session_id)
            if session_data:
                await self._untrack_user_session(session_data['user_id'], session_id)
            
            logger.info(f"Invalidated session {session_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate session {session_id}: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session information."""
        session_data = await self._get_session_data(session_id)
        return SessionInfo(**session_data) if session_data else None
    
    async def list_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """List all active sessions for user."""
        try:
            session_ids = await self._get_user_sessions(user_id)
            sessions = []
            
            for session_id in session_ids:
                session_data = await self._get_session_data(session_id)
                if session_data:
                    sessions.append(SessionInfo(**session_data))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list sessions for user {user_id}: {e}")
            return []
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        cleaned_count = 0
        
        try:
            # Get all session keys from Redis
            session_keys = await self.redis_client.keys("session:*")
            
            for key in session_keys:
                session_data = await self.redis_client.get(key)
                if session_data:
                    session_info = SessionInfo(**json.loads(session_data))
                    
                    # Check if session is expired
                    if datetime.utcnow() > session_info.expires_at:
                        await self.invalidate_session(session_info.session_id, "expired")
                        cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} expired sessions")
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
        
        return cleaned_count
    
    async def _cache_session(self, session_info: SessionInfo) -> None:
        """Cache session in Redis."""
        session_data = session_info.dict()
        session_data['last_activity'] = session_info.last_activity.isoformat()
        session_data['created_at'] = session_info.created_at.isoformat()
        session_data['expires_at'] = session_info.expires_at.isoformat()
        
        await self.redis_client.setex(
            f"session:{session_info.session_id}",
            self.config.cache_ttl_seconds,
            json.dumps(session_data, default=str)
        )
    
    async def _get_session_data(self, session_id: str) -> Optional[Dict]:
        """Get session data from cache."""
        cached_data = await self.redis_client.get(f"session:{session_id}")
        if cached_data:
            return json.loads(cached_data)
        return None
    
    async def _persist_session(self, session_info: SessionInfo) -> None:
        """Persist session to database."""
        try:
            self.supabase.rpc('security.create_or_update_session', {
                'p_session_id': session_info.session_id,
                'p_user_id': session_info.user_id,
                'p_email': session_info.email,
                'p_roles': session_info.roles,
                'p_ip_address': session_info.ip_address,
                'p_user_agent': session_info.user_agent,
                'p_device_fingerprint': session_info.device_fingerprint,
                'p_location': session_info.location,
                'p_expires_at': session_info.expires_at.isoformat(),
                'p_mfa_verified': session_info.mfa_verified,
                'p_metadata': session_info.metadata
            }).execute()
        except Exception as e:
            logger.error(f"Failed to persist session: {e}")
    
    async def _deactivate_session(self, session_id: str) -> None:
        """Deactivate session in database."""
        try:
            self.supabase.rpc('security.deactivate_session', {
                'p_session_id': session_id
            }).execute()
        except Exception as e:
            logger.error(f"Failed to deactivate session: {e}")
    
    async def _track_user_session(self, user_id: str, session_id: str) -> None:
        """Track user's active sessions."""
        await self.redis_client.sadd(f"user_sessions:{user_id}", session_id)
        await self.redis_client.expire(f"user_sessions:{user_id}", self.config.cache_ttl_seconds)
    
    async def _untrack_user_session(self, user_id: str, session_id: str) -> None:
        """Remove session from user tracking."""
        await self.redis_client.srem(f"user_sessions:{user_id}", session_id)
    
    async def _get_user_sessions(self, user_id: str) -> List[str]:
        """Get all tracked sessions for user."""
        session_ids = await self.redis_client.smembers(f"user_sessions:{user_id}")
        return list(session_ids)


class SessionManager:
    """Main session management class."""
    
    def __init__(self, config: SessionConfig, supabase: Client):
        self.config = config
        self.supabase = supabase
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        self.store = SessionStore(config, self.redis_client, supabase)
        self.validator = SessionValidator(config, self.redis_client)
        self.device_fingerprint = DeviceFingerprint()
        
    async def create_user_session(self, 
                                user_id: str,
                                email: str,
                                roles: List[str],
                                request: Request,
                                mfa_verified: bool = False) -> Tuple[str, SessionInfo]:
        """Create new user session."""
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get('User-Agent', '')
        
        # Generate device fingerprint
        accept_language = request.headers.get('Accept-Language', '')
        accept_encoding = request.headers.get('Accept-Encoding', '')
        device_fingerprint = self.device_fingerprint.generate(
            user_agent, accept_language, accept_encoding
        )
        
        # Check concurrent session limit
        user_sessions = await self.store.list_user_sessions(user_id)
        if len(user_sessions) >= self.config.max_concurrent_sessions:
            # Invalidate oldest session
            oldest_session = min(user_sessions, key=lambda s: s.last_activity)
            await self.store.invalidate_session(
                oldest_session.session_id, 
                "Max concurrent sessions exceeded"
            )
        
        # Create session info
        expires_at = datetime.utcnow() + timedelta(minutes=self.config.session_timeout_minutes)
        session_info = SessionInfo(
            user_id=user_id,
            email=email,
            roles=roles,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            expires_at=expires_at,
            mfa_verified=mfa_verified
        )
        
        # Create session
        session_id = await self.store.create_session(session_info)
        session_info.session_id = session_id
        
        # Generate session token
        token = self._generate_session_token(session_info)
        
        # Log session creation
        await self._log_session_event(session_id, user_id, 'session_created', {'ip_address': ip_address})
        
        return token, session_info
    
    async def validate_session_token(self, session_token: str) -> Optional[SessionInfo]:
        """Validate session token."""
        return await self.validator.validate_session(session_token)
    
    async def refresh_session(self, session_id: str) -> Optional[str]:
        """Refresh session before expiration."""
        session_info = await self.store.get_session(session_id)
        if not session_info:
            return None
        
        # Check if refresh is allowed
        time_until_expiry = (session_info.expires_at - datetime.utcnow()).total_seconds() / 60
        if time_until_expiry > self.config.refresh_threshold_minutes:
            return None
        
        # Extend session
        new_expires_at = datetime.utcnow() + timedelta(minutes=self.config.session_timeout_minutes)
        await self.store.update_session(session_id, {
            'expires_at': new_expires_at,
            'last_activity': datetime.utcnow()
        })
        
        # Generate new token
        session_info.expires_at = new_expires_at
        return self._generate_session_token(session_info)
    
    async def invalidate_user_session(self, session_id: str, reason: str = "user_logout") -> bool:
        """Invalidate specific session."""
        return await self.store.invalidate_session(session_id, reason)
    
    async def invalidate_all_user_sessions(self, user_id: str) -> int:
        """Invalidate all sessions for user."""
        sessions = await self.store.list_user_sessions(user_id)
        invalidated_count = 0
        
        for session in sessions:
            await self.store.invalidate_session(session.session_id, reason)
            invalidated_count += 1
        
        return invalidated_count
    
    async def set_session_cookie(self, response: Response, session_token: str) -> None:
        """Set session cookie in response."""
        response.set_cookie(
            key=self.config.session_cookie_name,
            value=session_token,
            max_age=self.config.session_timeout_minutes * 60,
            secure=self.config.secure_cookies,
            httponly=self.config.http_only_cookies,
            samesite=self.config.same_site_policy,
            domain=None  # Set based on your domain
        )
    
    async def clear_session_cookie(self, response: Response) -> None:
        """Clear session cookie from response."""
        response.delete_cookie(self.config.session_cookie_name)
    
    def _generate_session_token(self, session_info: SessionInfo) -> str:
        """Generate JWT session token."""
        payload = {
            'session_id': session_info.session_id,
            'user_id': session_info.user_id,
            'email': session_info.email,
            'roles': session_info.roles,
            'mfa_verified': session_info.mfa_verified,
            'device_fingerprint': session_info.device_fingerprint,
            'iat': datetime.utcnow(),
            'exp': session_info.expires_at,
            'aud': 'session-management',
            'iss': 'rbac-security'
        }
        
        return jwt.encode(
            payload,
            self.config.jwt_secret,
            algorithm=self.config.jwt_algorithm
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else 'unknown'
    
    async def _log_session_event(self, session_id: str, user_id: str, event_type: str, metadata: Dict) -> None:
        """Log session event for audit trail."""
        try:
            self.supabase.rpc('audit.log_event', {
                'p_event_type': 'session',
                'p_severity': 'low',
                'p_user_id': user_id,
                'p_resource_type': 'session',
                'p_action': event_type,
                'p_description': f'Session event: {event_type}',
                'p_metadata': {
                    'session_id': session_id,
                    **metadata
                }
            }).execute()
        except Exception as e:
            logger.error(f"Failed to log session event: {e}")
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up all expired sessions."""
        return await self.store.cleanup_expired_sessions()


# Global instance
session_manager = None


def get_session_manager(supabase: Optional[Client] = None) -> SessionManager:
    """Get or create session manager instance."""
    global session_manager
    if session_manager is None and supabase:
        config = SessionConfig()
        session_manager = SessionManager(config, supabase)
    if session_manager is None:
        raise ValueError("Session manager not initialized. Provide supabase client.")
    return session_manager
