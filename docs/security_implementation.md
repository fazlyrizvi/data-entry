# Security Implementation Documentation

## Overview

This document provides comprehensive documentation for the security policies implemented in the data automation system. The security framework implements defense-in-depth principles with role-based access control (RBAC), comprehensive audit trails, encryption at rest and in transit, and compliance-ready monitoring systems.

## Security Architecture

### Defense-in-Depth Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway & WAF                        │
├─────────────────────────────────────────────────────────────┤
│              Authentication & Authorization                 │
├─────────────────────────────────────────────────────────────┤
│         Row Level Security (RLS) & Data Access             │
├─────────────────────────────────────────────────────────────┤
│           Encryption & Key Management                      │
├─────────────────────────────────────────────────────────────┤
│              Audit & Compliance Monitoring                 │
└─────────────────────────────────────────────────────────────┘
```

### Core Security Components

1. **Role-Based Access Control (RBAC) System**
2. **Row Level Security (RLS) Policies**
3. **API Security Policies**
4. **Encryption & Key Management**
5. **Audit Trail & Compliance Monitoring**

## 1. Role-Based Access Control (RBAC) System

### Role Hierarchy

The system implements a four-tier role hierarchy:

- **VIEWER**: Read-only access to non-sensitive data and basic system information
- **OPERATOR**: Execute pipelines, manage data operations, limited configuration access
- **MANAGER**: Approve workflows, manage team resources, configure pipelines
- **ADMIN**: Full system access, user management, security configuration

### Role Permission Matrix

| Permission | VIEWER | OPERATOR | MANAGER | ADMIN |
|------------|--------|----------|---------|-------|
| Read Datasets | ✓ | ✓ | ✓ | ✓ |
| Write Datasets | ✗ | ✓ | ✓ | ✓ |
| Execute Pipelines | ✗ | ✓ | ✓ | ✓ |
| Create Pipelines | ✗ | ✗ | ✓ | ✓ |
| Manage Users | ✗ | ✗ | ✗ | ✓ |
| Access Audit Logs | ✓ | ✓ | ✓ | ✓ |
| System Configuration | ✗ | ✗ | ✗ | ✓ |

### Separation of Duties (SoD) Constraints

The system enforces SoD constraints to prevent conflicts of interest:

1. **No Single Admin Control**: Prevents single Admin from having full control without oversight
2. **No User Approval of Own Roles**: Users cannot approve their own role assignments
3. **Pipeline and Approval Separation**: Pipeline creators cannot approve their own changes
4. **No Audit and Admin Combination**: Audit readers cannot have admin privileges
5. **No User Delete and Create**: User creators cannot delete users without approval

### Key Functions

#### `security.has_permission(user_id, resource_pattern, action)`
Checks if a user has specific permission for a resource and action.

```sql
-- Example: Check if user can read datasets
SELECT security.has_permission('user-uuid', 'dataset:*', 'read');
```

#### `security.assign_role_to_user(user_id, role_name, assigned_by, approval_expires_at)`
Assigns a role to a user with validation.

```sql
-- Example: Assign Viewer role to new user
SELECT security.assign_role_to_user(
    'user-uuid',
    'VIEWER',
    'admin-uuid',
    NULL  -- No expiration
);
```

## 2. Row Level Security (RLS) Policies

RLS policies provide granular access control at the database level. Each table has policies that restrict row access based on user roles and permissions.

### Protected Tables

- **datasets**: Data storage with sensitivity levels
- **pipelines**: Workflow configurations and executions
- **data_sources**: External data connections
- **audit_logs**: Security and activity logging
- **api_keys**: API authentication tokens
- **security_events**: Security incident tracking

### Data Classification Levels

- **Level 1 (Public)**: Unrestricted access
- **Level 2 (Internal)**: Internal users only
- **Level 3 (Confidential)**: Restricted access with approval
- **Level 4 (Secret)**: Highest security clearance required

### RLS Policy Example

```sql
-- Policy: Viewers can read non-confidential datasets
CREATE POLICY "Viewers can read datasets" ON datasets
    FOR SELECT USING (
        sensitivity_level <= 2 AND
        (
            owner_id = auth.uid() OR
            security.has_permission('dataset', 'read')
        )
    );
```

## 3. API Security Policies

### Authentication & Authorization

- **OAuth 2.0 / OpenID Connect**: Standard delegated authentication
- **JWT Token Validation**: Strict validation of token claims
- **API Key Management**: Secure key generation, rotation, and monitoring

### Rate Limiting

The system implements multi-level rate limiting:

1. **User-based**: Per-user request limits
2. **API Key-based**: Per-key request limits
3. **IP-based**: Per-IP address limits
4. **Endpoint-specific**: Custom limits per API endpoint

### Input Validation

- **Schema Validation**: JSON schema validation for request bodies
- **SQL Injection Protection**: Pattern-based detection
- **XSS Prevention**: Script injection detection
- **Input Sanitization**: Automatic sanitization of user input

### JWT Validation Checklist

| Check | Implementation |
|-------|----------------|
| Issuer validation | Exact match to allow-list |
| Audience validation | Resource server ID verification |
| Expiration checking | Token lifetime enforcement |
| Algorithm allowlist | Only strong algorithms (RS256, ES256, EdDSA) |
| Header validation | Key ID and certificate validation |
| Token uniqueness | JTI replay protection |

### Key Functions

#### `api.validate_jwt_token(token, expected_audience, required_issuer)`
Validates JWT token according to security requirements.

```sql
-- Example: Validate API token
SELECT api.validate_jwt_token(
    'jwt-token-string',
    'api-audience',
    'https://issuer.example.com'
);
```

#### `api.check_rate_limit(identifier_type, identifier_value, endpoint_pattern)`
Checks rate limits for API requests.

```sql
-- Example: Check user rate limit
SELECT api.check_rate_limit(
    'user_id',
    'user-uuid',
    '/datasets*'
);
```

#### `api.detect_suspicious_activity(user_id, ip_address, user_agent, request_pattern)`
Detects suspicious API activity patterns.

```sql
-- Example: Check for suspicious activity
SELECT api.detect_suspicious_activity(
    'user-uuid',
    '192.168.1.100',
    'Mozilla/5.0...',
    '{"endpoint": "/datasets", "method": "POST"}'
);
```

## 4. Encryption & Key Management

### Encryption Algorithms

| Algorithm | Type | Key Size | Use Case |
|-----------|------|----------|----------|
| AES-256 | Symmetric | 256-bit | Data at rest encryption |
| RSA-2048 | Asymmetric | 2048-bit | Key exchange, digital signatures |
| HMAC-SHA256 | MAC | 256-bit | Message authentication |
| EdDSA | Asymmetric | 256-bit | Modern digital signatures |

### Key Types

1. **Master Keys**: Encrypt other encryption keys
2. **Data Keys**: Encrypt actual data content
3. **API Keys**: Authentication tokens
4. **Backup Keys**: Secure backup encryption

### Key Rotation Policy

- **Master Keys**: 365 days (1 year)
- **Data Keys**: 90 days (quarterly)
- **API Keys**: 30 days (monthly)
- **Backup Keys**: 180 days (semi-annual)

### Automated Key Rotation

```sql
-- Function to rotate expired keys
SELECT encryption.rotate_expired_keys();
```

### Encryption Configuration

```sql
-- Configure encryption for sensitive column
SELECT encryption.configure_table_encryption(
    'users',
    'email',
    'user_data_encryption_key',
    'AES256-GCM'
);
```

### Data Classification & Encryption

```sql
-- Classify data sensitivity
SELECT encryption.classify_data_sensitivity(
    'users',
    'ssn',
    '123-45-6789'
);
-- Returns: 'SECRET'
```

## 5. Audit Trail & Compliance Monitoring

### Audit Event Types

1. **Authentication Events**: Login/logout attempts
2. **Authorization Events**: Permission changes
3. **Data Access Events**: Dataset reads/writes
4. **Data Modification Events**: Content changes
5. **Configuration Changes**: System settings
6. **Security Violations**: Policy breaches
7. **System Events**: Infrastructure changes

### Compliance Frameworks

- **GDPR**: European data protection regulation
- **HIPAA**: Healthcare data protection
- **SOC 2**: Service organization controls
- **ISO 27001**: Information security management
- **PCI DSS**: Payment card security
- **SOX**: Financial reporting controls

### Audit Functions

#### `audit.log_event(event_type, severity, user_id, resource_type, action, description)`
Logs comprehensive audit events.

```sql
-- Example: Log dataset access
SELECT audit.log_event(
    'data_access',
    'medium',
    'user-uuid',
    'dataset',
    'read',
    'User accessed sensitive dataset'
);
```

#### `audit.create_security_incident(incident_type, severity, title, description)`
Creates security incidents from audit events.

```sql
-- Example: Create security incident
SELECT audit.create_security_incident(
    'unauthorized_access',
    'high',
    'Unauthorized Dataset Access',
    'User attempted to access restricted dataset'
);
```

#### `audit.generate_compliance_report(framework, start_date, end_date)`
Generates compliance reports for frameworks.

```sql
-- Example: Generate GDPR compliance report
SELECT audit.generate_compliance_report(
    'GDPR',
    '2024-01-01'::DATE,
    '2024-12-31'::DATE
);
```

### Data Subject Rights (GDPR)

```sql
-- Initiate data subject request
SELECT audit.initiate_data_subject_request(
    'erasure',
    'user@example.com',
    ARRAY['email', 'name', 'phone'],
    'Request to delete personal data',
    'Article 17 - Right to erasure'
);
```

### Privacy Impact Assessments (DPIA)

```sql
-- Create privacy impact assessment
INSERT INTO audit.privacy_impact_assessments (
    assessment_name,
    description,
    processing_purpose,
    data_categories,
    legal_basis,
    risk_level
) VALUES (
    'New Analytics System DPIA',
    'Assessment for new customer analytics platform',
    'Customer behavior analysis and personalization',
    ARRAY['email', 'browsing_history', 'purchase_history'],
    'Legitimate interest',
    'high'
);
```

## 6. Security Monitoring Views

### Compliance Dashboard

```sql
-- View compliance metrics
SELECT * FROM audit.compliance_dashboard;
```

### Security Incidents Summary

```sql
-- View recent security incidents
SELECT * FROM audit.security_incidents_summary;
```

### User Activity Heatmap

```sql
-- View user activity patterns
SELECT * FROM audit.user_activity_heatmap;
```

### High-Risk Activities

```sql
-- View high-risk user activities
SELECT * FROM audit.high_risk_activities;
```

## 7. Implementation Examples

### Complete User Onboarding

```sql
-- 1. Create user
INSERT INTO auth.users (email, encrypted_password) VALUES
('newuser@example.com', 'encrypted_password_hash');

-- 2. Assign role
SELECT security.assign_role_to_user(
    (SELECT id FROM auth.users WHERE email = 'newuser@example.com'),
    'VIEWER',
    'admin-uuid'
);

-- 3. Create API key
INSERT INTO api_keys (user_id, key_name, hashed_key, scopes)
VALUES (
    (SELECT id FROM auth.users WHERE email = 'newuser@example.com'),
    'Primary API Key',
    'hashed_api_key',
    ARRAY['dataset:read', 'pipeline:read']
);

-- 4. Log the onboarding
SELECT audit.log_event(
    'authorization',
    'low',
    'admin-uuid',
    'user',
    'create',
    'New user onboarding completed',
    jsonb_build_object('new_user_email', 'newuser@example.com')
);
```

### Data Classification and Protection

```sql
-- 1. Classify sensitive data
SELECT encryption.classify_data_sensitivity(
    'customers',
    'credit_card',
    '4111-1111-1111-1111'
);
-- Returns: 'SECRET'

-- 2. Configure encryption
SELECT encryption.configure_table_encryption(
    'customers',
    'credit_card',
    'payment_data_key',
    'AES256-GCM'
);

-- 3. Encrypt data
SELECT encryption.encrypt_data(
    '4111-1111-1111-1111',
    (SELECT id FROM encryption.keys WHERE key_name = 'payment_data_key'),
    'AES256-GCM'
);
```

### Security Incident Response

```sql
-- 1. Detect suspicious activity
SELECT api.detect_suspicious_activity(
    'user-uuid',
    '192.168.1.100',
    'Suspicious Bot',
    '{"endpoint": "/admin/users", "method": "GET"}'
);

-- 2. Create security incident if risk score high
IF (SELECT risk_score FROM suspicious_activity_check) >= 50 THEN
    SELECT audit.create_security_incident(
        'suspicious_api_activity',
        'high',
        'Suspicious API Activity Detected',
        'Multiple failed requests from suspicious user agent'
    );
END IF;

-- 3. Implement emergency access controls
UPDATE security.user_roles 
SET is_active = false 
WHERE user_id = 'suspicious-user-uuid';

-- 4. Log the response actions
SELECT audit.log_event(
    'security_violation',
    'critical',
    'security-officer-uuid',
    'user_account',
    'disable',
    'Emergency account suspension due to suspicious activity'
);
```

## 8. Security Best Practices

### 1. Principle of Least Privilege
- Grant minimum necessary permissions
- Regularly review and revoke unnecessary access
- Use time-limited access where possible

### 2. Defense in Depth
- Implement security at multiple layers
- Never rely on a single security control
- Monitor and validate security effectiveness

### 3. Zero Trust Architecture
- Verify every access request
- Assume breach and minimize blast radius
- Continuously monitor and validate

### 4. Data Minimization
- Collect only necessary data
- Encrypt sensitive data at rest and in transit
- Implement proper data retention policies

### 5. Regular Security Reviews
- Conduct quarterly access reviews
- Perform annual penetration testing
- Review and update security policies

### 6. Incident Response
- Maintain incident response procedures
- Train staff on incident detection and reporting
- Conduct post-incident reviews and improvements

## 9. Compliance Mapping

### GDPR Compliance

| GDPR Requirement | Implementation |
|------------------|----------------|
| Data Protection by Design | Encryption at rest and in transit |
| Right to Access | Data subject request system |
| Right to Rectification | Data modification audit trail |
| Right to Erasure | Automated data deletion workflows |
| Data Portability | Export capabilities with audit |
| Privacy Impact Assessments | DPIA workflow and documentation |
| Breach Notification | Automated alerting system |

### HIPAA Compliance

| HIPAA Safeguard | Implementation |
|-----------------|----------------|
| Access Control | RBAC with unique user IDs |
| Audit Controls | Comprehensive audit logging |
| Integrity Controls | Data validation and checksums |
| Transmission Security | TLS 1.3 encryption |
| Person/Entity Authentication | Multi-factor authentication |
| Automatic Logoff | Session timeout policies |

### SOC 2 Compliance

| Trust Service Criteria | Implementation |
|-----------------------|----------------|
| Security | RBAC, encryption, monitoring |
| Availability | Redundancy, monitoring, alerting |
| Processing Integrity | Data validation, audit trails |
| Confidentiality | Encryption, access controls |
| Privacy | Data classification, retention policies |

## 10. Deployment and Maintenance

### Initial Setup

1. **Deploy RBAC System**:
   ```sql
   -- Run the RBAC system setup
   \i supabase/security/roles/rbac_system.sql
   ```

2. **Configure RLS Policies**:
   ```sql
   -- Apply comprehensive RLS policies
   \i supabase/security/rls-policies/comprehensive_rls_policies.sql
   ```

3. **Setup API Security**:
   ```sql
   -- Configure API security policies
   \i supabase/security/api-policies/api_security_policies.sql
   ```

4. **Initialize Encryption**:
   ```sql
   -- Setup encryption and key management
   \i supabase/security/encryption/encryption_policies.sql
   ```

5. **Configure Audit System**:
   ```sql
   -- Initialize audit trail system
   \i supabase/security/audit/audit_trail_policies.sql
   ```

### Regular Maintenance

1. **Key Rotation** (Quarterly):
   ```sql
   SELECT encryption.rotate_expired_keys();
   ```

2. **Audit Log Archival** (Monthly):
   ```sql
   SELECT audit.archive_old_events();
   ```

3. **Compliance Reports** (Monthly):
   ```sql
   SELECT audit.generate_compliance_report('SOC2', CURRENT_DATE - INTERVAL '1 month', CURRENT_DATE);
   ```

4. **Access Review** (Quarterly):
   ```sql
   -- Review user permissions and SoD compliance
   SELECT * FROM security.user_permissions WHERE is_active = true;
   ```

### Monitoring and Alerting

Key metrics to monitor:

1. **Failed Authentication Attempts**: > 5 per user per hour
2. **High Severity Security Events**: Any occurrence
3. **Failed Compliance Controls**: > 10% failure rate
4. **Overdue Key Rotations**: Any overdue keys
5. **Anomalous API Usage**: 300% increase from baseline

## 11. Troubleshooting

### Common Issues

#### Authentication Failures
```sql
-- Check user authentication logs
SELECT * FROM audit.events 
WHERE event_type = 'authentication' 
AND success = false 
ORDER BY timestamp DESC 
LIMIT 10;
```

#### Permission Denied Errors
```sql
-- Check user permissions
SELECT * FROM security.user_permissions 
WHERE user_id = 'user-uuid';

-- Check SoD constraints
SELECT * FROM security.sod_constraints;
```

#### Encryption Key Issues
```sql
-- Check key rotation status
SELECT * FROM encryption.key_rotation_status 
WHERE rotation_status != 'CURRENT';

-- Verify key integrity
SELECT * FROM encryption.audit_log 
WHERE operation = 'generate' 
AND success = false;
```

### Emergency Procedures

#### Account Compromise
1. Immediately disable user account
2. Revoke all active API keys
3. Rotate all encryption keys
4. Review audit logs for compromise scope
5. Notify affected parties

#### Data Breach Response
1. Assess scope and impact
2. Implement containment measures
3. Preserve evidence for investigation
4. Notify regulatory authorities (GDPR: 72 hours)
5. Conduct post-incident review

## Conclusion

This security implementation provides a comprehensive, defense-in-depth approach to protecting the data automation system. The multi-layered architecture ensures that security controls work together to protect against various threats while maintaining compliance with major regulatory frameworks.

Regular monitoring, testing, and updates are essential to maintaining effective security posture. The system is designed to scale and adapt as security requirements evolve.

For questions or issues with the security implementation, contact the security team or refer to the troubleshooting section above.