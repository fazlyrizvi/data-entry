# RBAC Security Integration Documentation

## Overview

This document provides comprehensive documentation for integrating the Role-Based Access Control (RBAC) security system into the enterprise data automation platform. The implementation provides a multi-layered security architecture with authentication, authorization, session management, and audit logging.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Auth         │  │ Permission   │  │ Session      │     │
│  │ Middleware   │  │ Guard        │  │ Manager      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                    Supabase Database                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ RBAC Schema  │  │ RLS Policies │  │ Audit Logs   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Authentication Middleware (`auth_middleware.py`)

The authentication middleware provides comprehensive security controls for HTTP requests.

#### Key Features

- **JWT Token Validation**: Validates tokens against security requirements
- **Session-based Authentication**: Maintains secure session state
- **Multi-Factor Authentication**: Enforces MFA for sensitive operations
- **Account Lockout Protection**: Prevents brute force attacks
- **Rate Limiting**: Controls request frequency per user/IP
- **Suspicious Activity Detection**: Identifies potential security threats

#### Usage Example

```python
from fastapi import FastAPI, Depends
from auth_middleware import get_auth_middleware, require_permissions

app = FastAPI()
auth = get_auth_middleware()

@app.get("/datasets")
@auth.require_permissions(["dataset:read"])
async def get_datasets(user = Depends(auth.get_current_user)):
    return {"data": "sensitive data"}
```

#### Configuration

```python
from auth_middleware import AuthenticationConfig

config = AuthenticationConfig(
    jwt_secret="your-secret-key",
    jwt_expiration_hours=24,
    max_login_attempts=5,
    lockout_duration_minutes=30,
    session_timeout_minutes=480,
    require_mfa={"ADMIN", "MANAGER"}
)
```

### 2. Permission Guard (`permission_guard.py`)

The permission guard provides granular permission checking and enforcement.

#### Key Features

- **Resource-based Access Control**: Checks permissions for specific resources
- **Role-based Authorization**: Validates user roles
- **Permission Inheritance**: Supports hierarchical permission models
- **Dynamic Permission Evaluation**: Context-aware permission checks
- **Separation of Duties**: Enforces compliance constraints
- **Audit Integration**: Logs permission checks

#### Permission Groups

Predefined permission groups for common operations:

```python
from permission_guard import PermissionGroups

# Dataset operations
@require_permissions(PermissionGroups.DATASET_ADMIN)

# Pipeline management
@require_permissions(PermissionGroups.PIPELINE_MANAGE)

# User administration
@require_permissions(PermissionGroups.USER_ADMIN)
```

#### Custom Permission Checking

```python
from permission_guard import get_permission_guard, PermissionContext

guard = get_permission_guard(supabase_client)

# Check specific permission
await guard.enforce_permission_check(
    user_id="user-uuid",
    resource="dataset",
    action="write",
    context=PermissionContext(
        resource_id="dataset-123",
        data_classification="CONFIDENTIAL",
        is_critical_operation=True
    )
)
```

### 3. Session Manager (`session_manager.py`)

Secure session management with comprehensive tracking and validation.

#### Key Features

- **Secure Token Generation**: Cryptographically secure session tokens
- **Session Timeout Enforcement**: Automatic timeout handling
- **Concurrent Session Limits**: Control multiple active sessions
- **Device Fingerprinting**: Track devices for security
- **Location Tracking**: Monitor geographic access patterns
- **Session Invalidation**: Clean session termination

#### Usage Example

```python
from session_manager import get_session_manager

manager = get_session_manager(supabase_client)

# Create user session
token, session_info = await manager.create_user_session(
    user_id="user-uuid",
    email="user@example.com",
    roles=["MANAGER"],
    request=request,
    mfa_verified=True
)

# Validate session
session = await manager.validate_session_token(token)

# Refresh session
new_token = await manager.refresh_session(session_id)
```

## Role Hierarchy

The system implements a 4-tier role hierarchy with proper separation of duties:

### VIEWER
- **Description**: Read-only access to non-sensitive data
- **Permissions**:
  - Read datasets
  - Read pipelines
  - Read user information
  - Access basic audit logs

### OPERATOR
- **Description**: Execute pipelines, manage data operations
- **Permissions**:
  - All VIEWER permissions
  - Write datasets
  - Execute pipelines
  - Export datasets
  - Read detailed audit logs

### MANAGER
- **Description**: Approve workflows, manage team resources
- **Permissions**:
  - All OPERATOR permissions
  - Create pipelines
  - Create users
  - Export audit logs
  - Analyze audit patterns

### ADMIN
- **Description**: Full system access, user management
- **Permissions**:
  - All system permissions
  - User management
  - System configuration
  - Security settings
  - Delete operations

## Permission Matrix

| Resource | Action | VIEWER | OPERATOR | MANAGER | ADMIN |
|----------|--------|--------|----------|---------|-------|
| Dataset | Read | ✓ | ✓ | ✓ | ✓ |
| Dataset | Write | ✗ | ✓ | ✓ | ✓ |
| Dataset | Delete | ✗ | ✗ | ✗ | ✓ |
| Pipeline | Execute | ✗ | ✓ | ✓ | ✓ |
| Pipeline | Create | ✗ | ✗ | ✓ | ✓ |
| Pipeline | Delete | ✗ | ✗ | ✗ | ✓ |
| User | Read | ✓ | ✓ | ✓ | ✓ |
| User | Create | ✗ | ✗ | ✓ | ✓ |
| User | Delete | ✗ | ✗ | ✗ | ✓ |
| System | Admin | ✗ | ✗ | ✗ | ✓ |
| Audit | Read | ✓ | ✓ | ✓ | ✓ |
| Audit | Export | ✗ | ✗ | ✓ | ✓ |

## Separation of Duties (SoD)

The system enforces SoD constraints to prevent conflicts of interest:

### Constraints

1. **No Single Admin Control**: Prevents single Admin from having full control without oversight
2. **No User Approval of Own Roles**: Users cannot approve their own role assignments
3. **Pipeline and Approval Separation**: Pipeline creators cannot approve their own changes
4. **No Audit and Admin Combination**: Audit readers cannot have admin privileges
5. **No User Delete and Create**: User creators cannot delete users without approval

### Implementation

```python
# Check SoD constraints
is_valid = await guard.check_separation_of_duties(
    user_id="user-uuid",
    requested_action="user:delete"
)

if not is_valid:
    raise HTTPException(status_code=403, detail="SoD constraint violation")
```

## Implementation Guide

### 1. Installation

```bash
pip install -r code/security/rbac/requirements.txt
```

### 2. Database Setup

Apply the RBAC schema to your database:

```sql
-- Run the RBAC system setup
\i supabase/security/roles/rbac_system.sql

-- Apply comprehensive RLS policies
\i supabase/security/rls-policies/comprehensive_rls_policies.sql
```

### 3. FastAPI Integration

#### Main Application Setup

```python
from fastapi import FastAPI, Request
from auth_middleware import get_auth_middleware
from permission_guard import get_permission_guard, PermissionGroups
from session_manager import get_session_manager

app = FastAPI()

# Initialize security components
auth = get_auth_middleware()
guard = get_permission_guard(supabase_client)
session_manager = get_session_manager(supabase_client)

# Add middleware
app.middleware("http")(auth.authentication_middleware)

# Protect endpoints
@app.get("/protected-endpoint")
@auth.require_permissions(PermissionGroups.DATASET_READ)
async def protected_endpoint(request: Request):
    user = request.state.user
    return {"message": f"Hello, {user.email}"}
```

#### Authentication Endpoints

```python
@app.post("/login")
async def login(request: Request, credentials: LoginRequest):
    auth = get_auth_middleware()
    result = await auth.login(
        email=credentials.email,
        password=credentials.password,
        request=request
    )
    
    # Set session cookie
    response = JSONResponse(content=result)
    await session_manager.set_session_cookie(response, result["access_token"])
    return response

@app.post("/logout")
async def logout(request: Request):
    user = request.state.user
    await session_manager.invalidate_all_user_sessions(user.user_id)
    
    response = JSONResponse(content={"message": "Logged out"})
    await session_manager.clear_session_cookie(response)
    return response

@app.post("/refresh")
async def refresh_session(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="No session token")
    
    session_info = await session_manager.validate_session_token(token)
    if not session_info:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    new_token = await session_manager.refresh_session(session_info.session_id)
    
    response = JSONResponse(content={"access_token": new_token})
    await session_manager.set_session_cookie(response, new_token)
    return response
```

### 4. Frontend Integration

#### React Components

```typescript
// Access Control Component
import { useAuth } from './contexts/AuthContext';

interface ProtectedProps {
  requiredPermissions: string[];
  children: React.ReactNode;
}

export const Protected: React.FC<ProtectedProps> = ({
  requiredPermissions,
  children
}) => {
  const { user, hasPermission } = useAuth();
  
  if (!user) {
    return <Navigate to="/login" />;
  }
  
  if (!hasPermission(requiredPermissions)) {
    return <AccessDenied />;
  }
  
  return <>{children}</>;
};

// Usage
<Protected requiredPermissions={["dataset:read"]}>
  <DatasetList />
</Protected>
```

#### Authentication Context

```typescript
// contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: string;
  email: string;
  roles: string[];
  permissions: string[];
  mfa_verified: boolean;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (permissions: string[]) => boolean;
  hasRole: (roles: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  
  const hasPermission = (requiredPermissions: string[]): boolean => {
    if (!user) return false;
    return requiredPermissions.every(perm => 
      user.permissions.includes(perm)
    );
  };
  
  const hasRole = (requiredRoles: string[]): boolean => {
    if (!user) return false;
    return requiredRoles.some(role => user.roles.includes(role));
  };
  
  return (
    <AuthContext.Provider value={{
      user,
      login,
      logout,
      hasPermission,
      hasRole
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

## Security Best Practices

### 1. Environment Configuration

```bash
# .env file
JWT_SECRET=your-very-secure-secret-key-here
SESSION_SECRET=another-secure-session-secret
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
REDIS_URL=redis://localhost:6379
```

### 2. HTTPS Configuration

Always use HTTPS in production:

```python
if settings.environment == "production":
    session_manager.config.secure_cookies = True
    session_manager.config.same_site_policy = "strict"
```

### 3. Rate Limiting

Configure appropriate rate limits:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    # Login logic
```

### 4. Security Headers

Add security headers to all responses:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

## Monitoring and Alerting

### 1. Security Events

Monitor key security events:

```sql
-- Failed authentication attempts
SELECT * FROM audit.events 
WHERE event_type = 'authentication' 
AND success = false 
AND timestamp > NOW() - INTERVAL '1 hour';

-- Permission denials
SELECT * FROM audit.events 
WHERE event_type = 'authorization' 
AND severity IN ('medium', 'high')
AND timestamp > NOW() - INTERVAL '1 hour';
```

### 2. Session Monitoring

Track session activities:

```sql
-- Active sessions count
SELECT user_id, COUNT(*) as session_count
FROM security.sessions
WHERE expires_at > NOW()
GROUP BY user_id;

-- Suspicious session activities
SELECT * FROM security.sessions
WHERE last_activity < NOW() - INTERVAL '30 minutes'
AND ip_address NOT IN (
    SELECT DISTINCT ip_address 
    FROM security.sessions 
    WHERE created_at > NOW() - INTERVAL '7 days'
);
```

### 3. Alerts

Configure alerts for:

- More than 5 failed login attempts per hour
- Permission denials for critical operations
- Session hijacking attempts
- Unauthorized access to sensitive resources

## Troubleshooting

### Common Issues

#### 1. Authentication Failures

```python
# Check user permissions
from permission_guard import get_permission_guard

guard = get_permission_guard(supabase_client)
permissions = await guard.get_user_permissions(user_id)
print(f"User permissions: {permissions}")
```

#### 2. Session Timeout Issues

```python
# Check active sessions
from session_manager import get_session_manager

manager = get_session_manager(supabase_client)
sessions = await manager.list_user_sessions(user_id)
print(f"Active sessions: {len(sessions)}")
```

#### 3. Permission Denials

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add logging to permission checks
result = await guard.check_permission(user_id, resource, action)
logger.debug(f"Permission check result: {result}")
```

### Database Queries for Debugging

```sql
-- Check user roles
SELECT u.email, r.role_name, ur.is_active
FROM auth.users u
JOIN security.user_roles ur ON u.id = ur.user_id
JOIN security.roles r ON ur.role_id = r.id
WHERE u.email = 'user@example.com';

-- Check role permissions
SELECT r.role_name, p.permission_name
FROM security.roles r
JOIN security.role_permissions rp ON r.id = rp.role_id
JOIN security.permissions p ON rp.permission_id = p.id
WHERE r.role_name = 'MANAGER';

-- Check SoD violations
SELECT * FROM security.sod_violations
WHERE user_id = 'user-uuid';
```

## Compliance and Auditing

### GDPR Compliance

- **Data Minimization**: Only collect necessary user data
- **Right to Access**: Provide user data export functionality
- **Right to Erasure**: Implement user deletion workflows
- **Privacy by Design**: Encrypt all sensitive data

### HIPAA Compliance

- **Access Control**: Unique user IDs and role-based access
- **Audit Controls**: Comprehensive audit logging
- **Automatic Logoff**: Session timeout policies
- **Transmission Security**: TLS encryption

### SOC 2 Compliance

- **Security**: RBAC, encryption, monitoring
- **Availability**: Redundancy and failover
- **Confidentiality**: Data classification and protection
- **Privacy**: Privacy policy and procedures

## Deployment Checklist

### Pre-Deployment

- [ ] Configure environment variables
- [ ] Set up Redis instance
- [ ] Apply database migrations
- [ ] Test authentication flow
- [ ] Verify permission matrix
- [ ] Configure rate limiting
- [ ] Set up monitoring
- [ ] Test session management

### Post-Deployment

- [ ] Monitor authentication logs
- [ ] Check permission checks
- [ ] Verify session handling
- [ ] Test security headers
- [ ] Validate audit logging
- [ ] Check rate limiting
- [ ] Monitor security events
- [ ] Review compliance metrics

## Performance Optimization

### 1. Caching

- Cache permission checks for 5 minutes
- Cache user sessions in Redis
- Use connection pooling for database
- Implement Redis clustering for high availability

### 2. Database Optimization

```sql
-- Add indexes for performance
CREATE INDEX idx_user_roles_active ON security.user_roles(user_id, is_active);
CREATE INDEX idx_permissions_resource ON security.permissions(resource_pattern);
CREATE INDEX idx_sessions_user ON security.sessions(user_id, is_active);

-- Enable query optimization
SET work_mem = '256MB';
SET shared_buffers = '1GB';
```

### 3. Rate Limiting

- Use Redis for distributed rate limiting
- Implement token bucket algorithm
- Configure per-user and per-IP limits
- Monitor rate limit violations

## Support and Maintenance

### Regular Tasks

1. **Daily**:
   - Review security logs
   - Check failed authentication attempts
   - Monitor session activities

2. **Weekly**:
   - Review permission assignments
   - Check for inactive users
   - Audit security events

3. **Monthly**:
   - Generate compliance reports
   - Review SoD violations
   - Update security policies

4. **Quarterly**:
   - Conduct access reviews
   - Rotate encryption keys
   - Update role assignments
   - Review incident response

### Emergency Procedures

#### Account Compromise

1. Immediately disable user account
2. Revoke all active sessions
3. Review audit logs
4. Notify security team
5. Reset user credentials
6. Document incident

#### System Breach

1. Activate incident response plan
2. Preserve audit logs
3. Review access patterns
4. Implement containment measures
5. Notify authorities if required
6. Conduct forensic analysis

## Conclusion

This RBAC implementation provides a comprehensive, enterprise-grade security solution that:

- Enforces strict access controls
- Maintains detailed audit trails
- Supports compliance requirements
- Provides granular permissions
- Implements security best practices

The system is designed to scale and adapt as security requirements evolve. Regular monitoring, testing, and updates are essential to maintaining effective security posture.

For questions or support, contact the security team or refer to the troubleshooting section above.
