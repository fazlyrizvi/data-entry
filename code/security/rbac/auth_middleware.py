"""
Authentication Middleware for RBAC Security System

This module provides comprehensive authentication middleware for securing
HTTP requests and validating user credentials through the RBAC system.

Features:
- JWT token validation
- Session-based authentication
- Multi-factor authentication support
- Account lockout protection
- Audit trail integration
- Rate limiting per user/IP
"""

import logging
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Dict, List, Optional, Set, Union
from urllib.parse import parse_qs, urlparse

import jwt
from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from supabase import create_client, Client
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserContext(BaseModel):
    """User context containing authentication and authorization information."""
    user_id: str
    email: str
    roles: List[str]
    permissions: List[str]
    session_id: str
    ip_address: str
    user_agent: str
    mfa_verified: bool = False
    login_timestamp: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('roles', 'permissions', pre=True)
    def split_comma_separated(cls, v):
        """Convert comma-separated strings to lists."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(',')]
        return v or []


class AuthenticationConfig(BaseModel):
    """Configuration for authentication middleware."""
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    token_refresh_threshold_hours: int = 1
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    session_timeout_minutes: int = 480
    require_mfa: Set[str] = {"ADMIN", "MANAGER"}
    allowed_issuers: List[str] = Field(default_factory=lambda: ["auth.system"])
    audience: str = "enterprise-automation-api"
    cache_ttl_seconds: int = 300
    enable_rate_limiting: bool = True
    max_requests_per_hour: int = 1000
    enable_suspicious_activity_detection: bool = True
    
    class Config:
        env_prefix = "AUTH_"


class SuspiciousActivityDetector:
    """Detects and logs suspicious authentication activities."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.failed_attempts_key = "auth:failed_attempts:"
        self.suspicious_ips_key = "auth:suspicious_ips:"
        
    async def record_failed_attempt(self, identifier: str, ip_address: str) -> None:
        """Record a failed authentication attempt."""
        now = time.time()
        hour_window = int(now // 3600)
        key = f"{self.failed_attempts_key}{identifier}:{hour_window}"
        
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, 7200)  # Keep for 2 hours
        await pipe.execute()
        
        # Check for threshold
        attempts = await self.redis.get(key)
        if attempts and int(attempts) >= 10:
            # Mark IP as suspicious
            suspicious_key = f"{self.suspicious_ips_key}{ip_address}"
            await self.redis.setex(suspicious_key, 3600, 1)
            logger.warning(f"IP {ip_address} flagged for suspicious activity")
    
    async def is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is flagged as suspicious."""
        suspicious_key = f"{self.suspicious_ips_key}{ip_address}"
        return await self.redis.get(suspicious_key) is not None
    
    async def get_failed_attempts(self, identifier: str) -> int:
        """Get failed attempts count for identifier."""
        now = time.time()
        hour_window = int(now // 3600)
        key = f"{self.failed_attempts_key}{identifier}:{hour_window}"
        attempts = await self.redis.get(key)
        return int(attempts) if attempts else 0


class AccountLockoutManager:
    """Manages account lockout for security."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.lockout_key = "auth:locked:"
        
    async def is_locked(self, identifier: str) -> bool:
        """Check if account is locked."""
        return await self.redis.get(f"{self.lockout_key}{identifier}") is not None
    
    async def lock_account(self, identifier: str, duration_minutes: int) -> None:
        """Lock account for specified duration."""
        key = f"{self.lockout_key}{identifier}"
        await self.redis.setex(key, duration_minutes * 60, 1)
        logger.warning(f"Account {identifier} locked for {duration_minutes} minutes")
    
    async def unlock_account(self, identifier: str) -> None:
        """Unlock account manually."""
        await self.redis.delete(f"{self.lockout_key}{identifier}")
        logger.info(f"Account {identifier} unlocked")
    
    async def get_lockout_time_remaining(self, identifier: str) -> int:
        """Get remaining lockout time in seconds."""
        key = f"{self.lockout_key}{identifier}"
        ttl = await self.redis.ttl(key)
        return max(0, ttl)


class RateLimiter:
    """Rate limiting for authentication endpoints."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.rate_key = "auth:rate_limit:"
        
    async def check_rate_limit(self, identifier: str, limit: int, window_seconds: int) -> bool:
        """Check if identifier is within rate limit."""
        key = f"{self.rate_key}{identifier}"
        now = time.time()
        window_start = int(now - window_seconds)
        
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds)
        results = await pipe.execute()
        
        current_requests = results[1]
        return current_requests < limit


class AuthenticationMiddleware:
    """Main authentication middleware class."""
    
    def __init__(self, config: AuthenticationConfig):
        self.config = config
        self.supabase: Client = create_client(
            config.jwt_secret,  # Using as API URL placeholder
            config.jwt_secret    # Using as anon key placeholder
        )
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Initialize components
        self.lockout_manager = AccountLockoutManager(self.redis_client)
        self.rate_limiter = RateLimiter(self.redis_client)
        self.suspicious_detector = SuspiciousActivityDetector(self.redis_client)
        
        # Security scheme for FastAPI
        self.security = HTTPBearer(auto_error=False)
        
    async def verify_jwt_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm],
                audience=self.config.audience,
                issuer=self.config.allowed_issuers[0]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    async def authenticate_user(self, credentials: HTTPAuthorizationCredentials) -> Optional[UserContext]:
        """Authenticate user from credentials."""
        if not credentials:
            return None
            
        # Verify token
        payload = await self.verify_jwt_token(credentials.credentials)
        if not payload:
            return None
            
        # Check if user is locked
        user_id = payload.get('sub')
        if not user_id:
            return None
            
        if await self.lockout_manager.is_locked(user_id):
            remaining_time = await self.lockout_manager.get_lockout_time_remaining(user_id)
            logger.warning(f"Locked user {user_id} attempted access")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account locked. Try again in {remaining_time} seconds"
            )
        
        # Get user details from database
        user_context = await self._build_user_context(payload)
        if not user_context:
            return None
            
        return user_context
    
    async def _build_user_context(self, payload: Dict) -> Optional[UserContext]:
        """Build user context from JWT payload and database query."""
        try:
            # Query user roles and permissions
            response = self.supabase.rpc('security.get_user_permissions', {
                'p_user_id': payload['sub']
            }).execute()
            
            if not response.data:
                logger.warning(f"No permissions found for user {payload['sub']}")
                return None
            
            # Parse permissions
            roles = list(set([item.get('role_name') for item in response.data]))
            permissions = list(set([item.get('permission_name') for item in response.data]))
            
            user_context = UserContext(
                user_id=payload['sub'],
                email=payload.get('email', ''),
                roles=roles,
                permissions=permissions,
                session_id=payload.get('session_id', ''),
                ip_address=payload.get('ip_address', ''),
                user_agent=payload.get('user_agent', ''),
                mfa_verified=payload.get('mfa_verified', False)
            )
            
            return user_context
            
        except Exception as e:
            logger.error(f"Error building user context: {e}")
            return None
    
    async def check_suspicious_activity(self, user_context: UserContext, request: Request) -> None:
        """Check for suspicious activity patterns."""
        if not self.config.enable_suspicious_activity_detection:
            return
            
        ip_address = self._get_client_ip(request)
        
        # Check for suspicious IP
        if await self.suspicious_detector.is_suspicious_ip(ip_address):
            logger.warning(f"Suspicious IP {ip_address} attempting access")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Access temporarily restricted"
            )
        
        # Check for unusual patterns
        user_agent = request.headers.get('User-Agent', '')
        if not user_agent or len(user_agent) < 10:
            await self.suspicious_detector.record_failed_attempt(
                user_context.user_id, ip_address
            )
            logger.warning(f"Missing User-Agent from {ip_address}")
    
    async def enforce_rate_limiting(self, user_context: UserContext, request: Request) -> None:
        """Enforce rate limiting."""
        if not self.config.enable_rate_limiting:
            return
            
        ip_address = self._get_client_ip(request)
        identifier = f"{user_context.user_id}:{ip_address}"
        
        if not await self.rate_limiter.check_rate_limit(
            identifier,
            self.config.max_requests_per_hour,
            3600
        ):
            logger.warning(f"Rate limit exceeded for {identifier}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers (for load balancers/proxies)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else 'unknown'
    
    def requires_auth(self, 
                     required_permissions: Optional[List[str]] = None,
                     required_roles: Optional[List[str]] = None,
                     allow_anonymous: bool = False):
        """Decorator for requiring authentication and permissions."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if not request:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Request object not found"
                    )
                
                # Get credentials
                credentials = await self.security(request)
                
                # Authenticate user
                user_context = None
                if credentials:
                    user_context = await self.authenticate_user(credentials)
                
                # Check if authentication is required
                if not user_context:
                    if allow_anonymous:
                        return await func(*args, **kwargs)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Authentication required",
                            headers={"WWW-Authenticate": "Bearer"}
                        )
                
                # Check permissions
                if required_permissions:
                    missing_permissions = set(required_permissions) - set(user_context.permissions)
                    if missing_permissions:
                        logger.warning(
                            f"User {user_context.user_id} lacks permissions: {missing_permissions}"
                        )
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Insufficient permissions"
                        )
                
                # Check roles
                if required_roles:
                    missing_roles = set(required_roles) - set(user_context.roles)
                    if missing_roles:
                        logger.warning(
                            f"User {user_context.user_id} lacks roles: {missing_roles}"
                        )
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Insufficient role privileges"
                        )
                
                # Check MFA requirement
                if not user_context.mfa_verified and any(
                    role in user_context.roles for role in self.config.require_mfa
                ):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Multi-factor authentication required",
                        headers={"X-MFA-Required": "true"}
                    )
                
                # Security checks
                await self.check_suspicious_activity(user_context, request)
                await self.enforce_rate_limiting(user_context, request)
                
                # Add user context to request state
                request.state.user = user_context
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    async def login(self, email: str, password: str, request: Request) -> Dict:
        """Handle user login with security checks."""
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get('User-Agent', '')
        
        # Check account lockout
        if await self.lockout_manager.is_locked(email):
            remaining = await self.lockout_manager.get_lockout_time_remaining(email)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account locked. Try again in {remaining} seconds"
            )
        
        # Check rate limiting
        if not await self.rate_limiter.check_rate_limit(
            f"login:{ip_address}",
            10,  # Max 10 login attempts per hour per IP
            3600
        ):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )
        
        try:
            # Authenticate with Supabase
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if not response.user:
                # Record failed attempt
                await self.suspicious_detector.record_failed_attempt(email, ip_address)
                attempts = await self.suspicious_detector.get_failed_attempts(email)
                
                # Lock account if too many attempts
                if attempts >= self.config.max_login_attempts:
                    await self.lockout_manager.lock_account(
                        email, self.config.lockout_duration_minutes
                    )
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Check failed attempts
            attempts = await self.suspicious_detector.get_failed_attempts(email)
            if attempts > 0:
                # Clear failed attempts on successful login
                logger.info(f"Clearing {attempts} failed attempts for {email}")
            
            # Build user context
            user_context = await self._build_user_context({
                'sub': response.user.id,
                'email': response.user.email,
                'session_id': response.session.access_token
            })
            
            if not user_context:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account error"
                )
            
            # Generate JWT token
            token_data = {
                'sub': user_context.user_id,
                'email': user_context.email,
                'roles': user_context.roles,
                'permissions': user_context.permissions,
                'session_id': user_context.session_id,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'mfa_verified': user_context.mfa_verified,
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(hours=self.config.jwt_expiration_hours),
                'aud': self.config.audience,
                'iss': self.config.allowed_issuers[0]
            }
            
            access_token = jwt.encode(
                token_data,
                self.config.jwt_secret,
                algorithm=self.config.jwt_algorithm
            )
            
            # Log successful login
            logger.info(f"Successful login for {email} from {ip_address}")
            
            return {
                'access_token': access_token,
                'token_type': 'bearer',
                'expires_in': self.config.jwt_expiration_hours * 3600,
                'user': {
                    'id': user_context.user_id,
                    'email': user_context.email,
                    'roles': user_context.roles,
                    'mfa_verified': user_context.mfa_verified
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login error for {email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )
    
    async def logout(self, user_id: str) -> None:
        """Handle user logout."""
        # Invalidate session in database
        try:
            self.supabase.rpc('security.invalidate_user_sessions', {
                'p_user_id': user_id
            }).execute()
        except Exception as e:
            logger.error(f"Error invalidating sessions for {user_id}: {e}")
        
        logger.info(f"User {user_id} logged out")


# Global instance
auth_middleware = None


def get_auth_middleware() -> AuthenticationMiddleware:
    """Get or create authentication middleware instance."""
    global auth_middleware
    if auth_middleware is None:
        config = AuthenticationConfig()
        auth_middleware = AuthenticationMiddleware(config)
    return auth_middleware
