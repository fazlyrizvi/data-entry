"""
Permission Guard for RBAC Security System

This module provides granular permission checking utilities for enforcing
role-based access control throughout the application.

Features:
- Permission inheritance checking
- Resource-based access control
- Permission composition and grouping
- Dynamic permission evaluation
- Audit trail for permission checks
- Context-aware permission validation
"""

import logging
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Union
from enum import Enum
import re

from fastapi import HTTPException, Request
from supabase import create_client, Client
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)


class ResourceType(str, Enum):
    """Enum for resource types."""
    DATASET = "dataset"
    PIPELINE = "pipeline"
    USER = "user"
    SYSTEM = "system"
    AUDIT = "audit"
    CONFIG = "config"
    REPORT = "report"
    FILE = "file"
    API = "api"


class ActionType(str, Enum):
    """Enum for action types."""
    READ = "read"
    WRITE = "write"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    EXPORT = "export"
    IMPORT = "import"
    ADMIN = "admin"
    APPROVE = "approve"
    REVIEW = "review"
    CONFIGURE = "configure"


class PermissionContext(BaseModel):
    """Context information for permission checks."""
    resource_id: Optional[str] = None
    resource_owner_id: Optional[str] = None
    data_classification: Optional[str] = None
    is_critical_operation: bool = False
    requires_approval: bool = False
    approval_threshold: Optional[int] = None
    additional_metadata: Dict[str, Any] = Field(default_factory=dict)


class PermissionResult(BaseModel):
    """Result of permission check."""
    allowed: bool
    reason: Optional[str] = None
    required_permissions: List[str] = Field(default_factory=list)
    granted_permissions: List[str] = Field(default_factory=list)
    missing_permissions: List[str] = Field(default_factory=list)
    audit_required: bool = False
    approval_required: bool = False


class PermissionChecker:
    """Core permission checking engine."""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self._permission_cache: Dict[str, Dict] = {}
        self._cache_ttl = 300  # 5 minutes
        
    def _build_permission_key(self, user_id: str, resource: str, action: str) -> str:
        """Build cache key for permission lookup."""
        return f"{user_id}:{resource}:{action}"
    
    async def check_permission(self,
                              user_id: str,
                              resource: str,
                              action: str,
                              context: Optional[PermissionContext] = None) -> PermissionResult:
        """Check if user has permission for resource/action."""
        cache_key = self._build_permission_key(user_id, resource, action)
        
        # Check cache first
        if cache_key in self._permission_cache:
            cached_result, timestamp = self._permission_cache[cache_key]
            if (datetime.utcnow() - timestamp).seconds < self._cache_ttl:
                return cached_result
        
        try:
            # Query database for permission
            response = self.supabase.rpc('security.has_permission', {
                'p_user_id': user_id,
                'p_resource_pattern': resource,
                'p_action': action
            }).execute()
            
            if not response.data:
                result = PermissionResult(
                    allowed=False,
                    reason="Permission query failed"
                )
            else:
                permission_info = response.data[0]
                result = PermissionResult(
                    allowed=permission_info.get('has_permission', False),
                    required_permissions=[f"{resource}:{action}"],
                    granted_permissions=[f"{resource}:{action}"] if permission_info.get('has_permission') else [],
                    audit_required=permission_info.get('is_critical', False),
                    approval_required=permission_info.get('requires_dual_approval', False)
                )
            
            # Cache result
            self._permission_cache[cache_key] = (result, datetime.utcnow())
            
            return result
            
        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return PermissionResult(
                allowed=False,
                reason=f"Permission check error: {str(e)}"
            )
    
    async def check_resource_ownership(self,
                                     user_id: str,
                                     resource_id: str,
                                     resource_type: ResourceType,
                                     context: Optional[PermissionContext] = None) -> bool:
        """Check if user owns or has special access to resource."""
        try:
            # Query resource ownership
            response = self.supabase.rpc('security.check_resource_access', {
                'p_user_id': user_id,
                'p_resource_id': resource_id,
                'p_resource_type': resource_type.value
            }).execute()
            
            if not response.data:
                return False
            
            return response.data[0].get('has_access', False)
            
        except Exception as e:
            logger.error(f"Ownership check failed: {e}")
            return False
    
    async def check_data_classification(self,
                                      user_id: str,
                                      classification_level: str,
                                      context: Optional[PermissionContext] = None) -> bool:
        """Check if user has clearance for data classification level."""
        classification_hierarchy = {
            'PUBLIC': 0,
            'INTERNAL': 1,
            'CONFIDENTIAL': 2,
            'RESTRICTED': 3,
            'SECRET': 4,
            'TOP_SECRET': 5
        }
        
        user_clearance = await self._get_user_clearance(user_id)
        required_level = classification_hierarchy.get(classification_level, 0)
        
        return user_clearance >= required_level
    
    async def _get_user_clearance(self, user_id: str) -> int:
        """Get user's security clearance level."""
        try:
            response = self.supabase.rpc('security.get_user_clearance', {
                'p_user_id': user_id
            }).execute()
            
            if not response.data:
                return 0
            
            clearance_mapping = {
                'VIEWER': 1,
                'OPERATOR': 2,
                'MANAGER': 3,
                'ADMIN': 4
            }
            
            role = response.data[0].get('highest_role', 'VIEWER')
            return clearance_mapping.get(role, 0)
            
        except Exception as e:
            logger.error(f"Clearance check failed: {e}")
            return 0


class PermissionGuard:
    """High-level permission guard with decorators and utilities."""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.checker = PermissionChecker(supabase)
        
    def require_permissions(self, 
                           permissions: Union[str, List[str]],
                           context: Optional[PermissionContext] = None):
        """Decorator to require specific permissions."""
        if isinstance(permissions, str):
            permissions = [permissions]
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request = None
                user_id = None
                
                # Find request and user context
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        user_id = getattr(arg.state, 'user', None)
                        if user_id:
                            user_id = user_id.user_id
                        break
                
                if not request or not user_id:
                    raise HTTPException(
                        status_code=401,
                        detail="Authentication required"
                    )
                
                # Check all required permissions
                missing_permissions = []
                granted_permissions = []
                
                for permission in permissions:
                    # Parse permission (format: resource:action)
                    if ':' not in permission:
                        permission = f"*:{permission}"
                    
                    resource, action = permission.split(':', 1)
                    
                    result = await self.checker.check_permission(
                        user_id, resource, action, context
                    )
                    
                    if not result.allowed:
                        missing_permissions.append(permission)
                    else:
                        granted_permissions.append(permission)
                
                if missing_permissions:
                    logger.warning(
                        f"User {user_id} lacks permissions: {missing_permissions}"
                    )
                    raise HTTPException(
                        status_code=403,
                        detail=f"Insufficient permissions: {', '.join(missing_permissions)}"
                    )
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def require_roles(self, roles: Union[str, List[str]]):
        """Decorator to require specific roles."""
        if isinstance(roles, str):
            roles = [roles]
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request = None
                user_context = None
                
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        user_context = getattr(arg.state, 'user', None)
                        break
                
                if not request or not user_context:
                    raise HTTPException(
                        status_code=401,
                        detail="Authentication required"
                    )
                
                user_roles = set(user_context.roles)
                required_roles = set(roles)
                
                if not required_roles.issubset(user_roles):
                    missing_roles = required_roles - user_roles
                    logger.warning(
                        f"User {user_context.user_id} lacks roles: {missing_roles}"
                    )
                    raise HTTPException(
                        status_code=403,
                        detail=f"Insufficient role privileges: {', '.join(missing_roles)}"
                    )
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def require_resource_ownership(self, 
                                  resource_type: ResourceType,
                                  resource_id_param: str = 'id',
                                  context: Optional[PermissionContext] = None):
        """Decorator to require resource ownership or special access."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request = None
                user_context = None
                
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        user_context = getattr(arg.state, 'user', None)
                        break
                
                if not request or not user_context:
                    raise HTTPException(
                        status_code=401,
                        detail="Authentication required"
                    )
                
                # Get resource ID from kwargs
                resource_id = kwargs.get(resource_id_param)
                if not resource_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Resource ID '{resource_id_param}' required"
                    )
                
                # Check ownership
                has_access = await self.checker.check_resource_ownership(
                    user_context.user_id,
                    resource_id,
                    resource_type,
                    context
                )
                
                if not has_access:
                    logger.warning(
                        f"User {user_context.user_id} lacks access to {resource_type.value} {resource_id}"
                    )
                    raise HTTPException(
                        status_code=403,
                        detail="Insufficient privileges for this resource"
                    )
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    async def enforce_permission_check(self,
                                      user_id: str,
                                      resource: str,
                                      action: str,
                                      context: Optional[PermissionContext] = None) -> None:
        """Enforce permission check in non-decorator context."""
        result = await self.checker.check_permission(user_id, resource, action, context)
        
        if not result.allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {result.reason or f'{resource}:{action}'}"
            )
    
    async def get_user_permissions(self, user_id: str) -> Dict[str, List[str]]:
        """Get all permissions for a user grouped by resource type."""
        try:
            response = self.supabase.rpc('security.get_user_permissions', {
                'p_user_id': user_id
            }).execute()
            
            if not response.data:
                return {}
            
            permissions = {}
            for item in response.data:
                scope = item.get('scope', 'system')
                permission_name = item.get('permission_name', '')
                resource_pattern = item.get('resource_pattern', '*')
                
                if scope not in permissions:
                    permissions[scope] = []
                
                permissions[scope].append(permission_name)
            
            return permissions
            
        except Exception as e:
            logger.error(f"Failed to get user permissions: {e}")
            return {}
    
    async def get_permission_matrix(self) -> Dict[str, Dict[str, bool]]:
        """Get permission matrix for all roles."""
        try:
            response = self.supabase.rpc('security.get_permission_matrix').execute()
            
            if not response.data:
                return {}
            
            matrix = {}
            for item in response.data:
                role = item.get('role_name')
                permission = item.get('permission_name')
                has_permission = item.get('has_permission', False)
                
                if role not in matrix:
                    matrix[role] = {}
                
                matrix[role][permission] = has_permission
            
            return matrix
            
        except Exception as e:
            logger.error(f"Failed to get permission matrix: {e}")
            return {}
    
    async def check_separation_of_duties(self,
                                       user_id: str,
                                       requested_action: str,
                                       context: Optional[PermissionContext] = None) -> bool:
        """Check if action violates separation of duties constraints."""
        try:
            response = self.supabase.rpc('security.check_sod_violation', {
                'p_user_id': user_id,
                'p_action': requested_action
            }).execute()
            
            if not response.data:
                return True  # No constraint violation
            
            return not response.data[0].get('violation_detected', False)
            
        except Exception as e:
            logger.error(f"Failed to check SoD constraints: {e}")
            return True
    
    async def log_permission_check(self,
                                  user_id: str,
                                  resource: str,
                                  action: str,
                                  allowed: bool,
                                  context: Optional[PermissionContext] = None) -> None:
        """Log permission check for audit trail."""
        try:
            self.supabase.rpc('audit.log_event', {
                'p_event_type': 'authorization',
                'p_severity': 'low' if allowed else 'medium',
                'p_user_id': user_id,
                'p_resource_type': resource,
                'p_action': action,
                'p_description': f'Permission check: {resource}:{action}',
                'p_metadata': {
                    'allowed': allowed,
                    'context': context.dict() if context else None
                }
            }).execute()
            
        except Exception as e:
            logger.error(f"Failed to log permission check: {e}")
    
    def create_permission_group(self, name: str, permissions: List[str]) -> Callable:
        """Create a reusable permission group."""
        def check_permissions(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await self.require_permissions(permissions)(func)(*args, **kwargs)
            return wrapper
        return check_permissions


# Predefined permission groups
class PermissionGroups:
    """Predefined permission groups for common use cases."""
    
    # Dataset operations
    DATASET_READ = ["dataset:read"]
    DATASET_WRITE = ["dataset:read", "dataset:write"]
    DATASET_ADMIN = ["dataset:read", "dataset:write", "dataset:delete", "dataset:export"]
    
    # Pipeline operations
    PIPELINE_EXECUTE = ["pipeline:read", "pipeline:execute"]
    PIPELINE_MANAGE = ["pipeline:read", "pipeline:execute", "pipeline:create", "pipeline:update"]
    PIPELINE_ADMIN = ["pipeline:read", "pipeline:execute", "pipeline:create", "pipeline:update", "pipeline:delete"]
    
    # User management
    USER_READ = ["user:read"]
    USER_MANAGE = ["user:read", "user:create", "user:update"]
    USER_ADMIN = ["user:read", "user:create", "user:update", "user:delete", "user:role:assign"]
    
    # System administration
    SYSTEM_ADMIN = ["system:admin"]
    SYSTEM_CONFIG = ["system:config"]
    AUDIT_READ = ["audit:read"]
    AUDIT_ANALYZE = ["audit:read", "audit:analyze"]


# Utility functions for permission patterns
def match_permission_pattern(permission: str, pattern: str) -> bool:
    """Check if permission matches pattern (supports wildcards)."""
    # Convert pattern to regex
    regex_pattern = pattern.replace('*', '.*')
    return bool(re.match(f'^{regex_pattern}$', permission))


def build_permission(resource: str, action: str) -> str:
    """Build permission string from resource and action."""
    return f"{resource}:{action}"


def parse_permission(permission: str) -> tuple[str, str]:
    """Parse permission string into resource and action."""
    if ':' not in permission:
        raise ValueError(f"Invalid permission format: {permission}")
    return permission.split(':', 1)


# Global instance
permission_guard = None


def get_permission_guard(supabase: Optional[Client] = None) -> PermissionGuard:
    """Get or create permission guard instance."""
    global permission_guard
    if permission_guard is None and supabase:
        permission_guard = PermissionGuard(supabase)
    if permission_guard is None:
        raise ValueError("Permission guard not initialized. Provide supabase client.")
    return permission_guard
