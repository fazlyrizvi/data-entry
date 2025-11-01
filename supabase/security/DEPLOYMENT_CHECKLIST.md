# Security Policies Implementation Checklist

## Pre-Deployment Verification

### System Requirements
- [ ] PostgreSQL 14+ with UUID extension
- [ ] Supabase/PostgREST API gateway
- [ ] TLS 1.3 configured for all connections
- [ ] KMS/HSM integration (production)
- [ ] SIEM system for log aggregation

### Access Control
- [ ] Database superuser credentials secured
- [ ] Service accounts created with minimal privileges
- [ ] Network access restricted to authorized IPs
- [ ] VPN access configured for admin users

## Deployment Steps

### 1. Deploy RBAC System
```bash
# Execute RBAC SQL
psql -h [host] -U [user] -d [database] -f supabase/security/roles/rbac_system.sql

# Verify roles created
psql -h [host] -U [user] -d [database] -c "SELECT * FROM security.roles;"

# Expected output: 4 rows (ADMIN, MANAGER, OPERATOR, VIEWER)
```

**Verification Checklist:**
- [ ] Security schema created
- [ ] 4 system roles created (ADMIN, MANAGER, OPERATOR, VIEWER)
- [ ] Permission tables populated
- [ ] SoD constraints defined
- [ ] User role management functions available
- [ ] RLS policies enabled

### 2. Deploy RLS Policies
```bash
# Execute RLS SQL
psql -h [host] -U [user] -d [database] -f supabase/security/rls-policies/comprehensive_rls_policies.sql

# Verify tables protected
psql -h [host] -U [user] -d [database] -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
```

**Verification Checklist:**
- [ ] All application tables protected by RLS
- [ ] Sensitive tables have appropriate policies
- [ ] Audit triggers created
- [ ] Data classification system active

### 3. Deploy API Security
```bash
# Execute API Security SQL
psql -h [host] -U [user] -d [database] -f supabase/security/api-policies/api_security_policies.sql

# Verify API endpoints configured
psql -h [host] -U [user] -d [database] -c "SELECT COUNT(*) FROM api_endpoints;"
```

**Verification Checklist:**
- [ ] API endpoint registry populated
- [ ] Rate limiting configured
- [ ] JWT validation functions active
- [ ] Security monitoring views created
- [ ] Input validation schemas defined

### 4. Deploy Encryption System
```bash
# Execute Encryption SQL
psql -h [host] -U [user] -d [database] -f supabase/security/encryption/encryption_policies.sql

# Verify keys created
psql -h [host] -U [user] -d [database] -c "SELECT key_name, is_active FROM encryption.keys;"
```

**Verification Checklist:**
- [ ] Encryption schema created
- [ ] Master keys generated and secured
- [ ] Key rotation policies configured
- [ ] Encryption functions available
- [ ] Data classification functions active

### 5. Deploy Audit System
```bash
# Execute Audit SQL
psql -h [host] -U [user] -d [database] -f supabase/security/audit/audit_trail_policies.sql

# Verify audit tables created
psql -h [host] -U [user] -d [database] -c "SELECT COUNT(*) FROM audit.events;"
```

**Verification Checklist:**
- [ ] Audit schema created
- [ ] Event logging active
- [ ] Compliance tracking enabled
- [ ] Security incident management ready
- [ ] Retention policies configured

## Post-Deployment Configuration

### 1. Create Initial Admin User
```sql
-- Create admin user
INSERT INTO auth.users (email, encrypted_password) VALUES
('admin@yourcompany.com', '[encrypted_password]');

-- Assign admin role
SELECT security.assign_role_to_user(
    (SELECT id FROM auth.users WHERE email = 'admin@yourcompany.com'),
    'ADMIN',
    (SELECT id FROM auth.users WHERE email = 'admin@yourcompany.com')
);

-- Verify admin created
SELECT * FROM security.user_permissions 
WHERE role_name = 'ADMIN' AND user_email = 'admin@yourcompany.com';
```

**Verification Checklist:**
- [ ] Admin user created in auth.users
- [ ] Admin role assigned
- [ ] Admin can access all permissions
- [ ] Audit log shows admin creation

### 2. Configure API Keys
```sql
-- Create system API key
INSERT INTO api_keys (
    user_id,
    key_name,
    hashed_key,
    scopes,
    is_active
) VALUES (
    (SELECT id FROM auth.users WHERE email = 'admin@yourcompany.com'),
    'System API Key',
    '[hashed_key]',
    ARRAY['system:admin', 'user:read', 'dataset:read'],
    true
);

-- Verify API key
SELECT * FROM api_keys WHERE user_id = (SELECT id FROM auth.users WHERE email = 'admin@yourcompany.com');
```

**Verification Checklist:**
- [ ] API key created and hashed
- [ ] Appropriate scopes assigned
- [ ] Rate limits configured
- [ ] Key can authenticate requests

### 3. Test Encryption
```sql
-- Test data encryption
SELECT encryption.encrypt_data(
    'test sensitive data',
    (SELECT id FROM encryption.keys WHERE key_name = 'user_data_encryption_key'),
    'AES256-GCM'
);

-- Test data decryption
SELECT encryption.decrypt_data(
    '[encrypted_data]',
    '[iv]',
    (SELECT id FROM encryption.keys WHERE key_name = 'user_data_encryption_key'),
    'AES256-GCM'
);
```

**Verification Checklist:**
- [ ] Encryption function works
- [ ] Decryption function works
- [ ] Audit log shows encryption activity
- [ ] Keys are properly rotated

### 4. Test Audit Logging
```sql
-- Log a test event
SELECT audit.log_event(
    'authentication',
    'medium',
    (SELECT id FROM auth.users WHERE email = 'admin@yourcompany.com'),
    'test_resource',
    'test_action',
    'Test audit event'
);

-- Verify event logged
SELECT * FROM audit.events ORDER BY timestamp DESC LIMIT 1;
```

**Verification Checklist:**
- [ ] Audit events being logged
- [ ] Events show correct details
- [ ] Compliance tags applied
- [ ] Retention policies active

### 5. Configure Rate Limiting
```sql
-- Check default rate limits
SELECT * FROM api_rate_limits WHERE is_active = true;

-- Test rate limiting
-- (This would be tested via actual API calls)
```

**Verification Checklist:**
- [ ] Default rate limits configured
- [ ] Endpoint-specific limits active
- [ ] User/IP-based limits working
- [ ] Rate limit violations logged

## Security Testing

### 1. Authentication Testing
```sql
-- Test invalid login attempt
SELECT audit.log_event(
    'authentication',
    'medium',
    NULL, -- no user
    'auth',
    'login',
    'Invalid login attempt',
    jsonb_build_object('email', 'invalid@user.com')
);

-- Verify failed login logged
SELECT * FROM audit.events WHERE action = 'login' AND success = false;
```

**Test Cases:**
- [ ] Valid login succeeds
- [ ] Invalid login fails and logs
- [ ] Account lockout after failed attempts
- [ ] Session timeout enforced

### 2. Authorization Testing
```sql
-- Test permission checking
SELECT security.has_permission(
    (SELECT id FROM auth.users WHERE email = 'admin@yourcompany.com'),
    'dataset:*',
    'read'
);

-- Should return true for admin
```

**Test Cases:**
- [ ] Users can only access authorized resources
- [ ] Role-based restrictions enforced
- [ ] SoD constraints prevent conflicts
- [ ] Privilege escalation blocked

### 3. Data Protection Testing
```sql
-- Test data classification
SELECT encryption.classify_data_sensitivity(
    'users',
    'ssn',
    '123-45-6789'
);

-- Should return 'SECRET'
```

**Test Cases:**
- [ ] Sensitive data automatically classified
- [ ] Encryption required for classified data
- [ ] Data access properly logged
- [ ] Retention policies enforced

## Production Readiness Checklist

### Compliance
- [ ] GDPR controls implemented
- [ ] HIPAA safeguards active
- [ ] SOC 2 criteria mapped
- [ ] ISO 27001 controls covered
- [ ] Audit trails complete

### Monitoring
- [ ] Security events monitored
- [ ] Compliance dashboards active
- [ ] Alert thresholds configured
- [ ] Incident response procedures documented

### Backup & Recovery
- [ ] Encryption keys backed up securely
- [ ] Audit logs backed up
- [ ] Configuration backed up
- [ ] Recovery procedures tested

### Documentation
- [ ] Security policies documented
- [ ] User guides created
- [ ] Incident response playbooks
- [ ] Compliance reports generated

## Deployment Validation Commands

```bash
# 1. Check all schemas created
psql -h [host] -U [user] -d [database] -c "\dn"

# Expected output:
# security
# encryption
# audit
# api

# 2. Verify role hierarchy
psql -h [host] -U [user] -d [database] -c "
SELECT role_name, description 
FROM security.roles 
ORDER BY role_name;"

# 3. Check key rotation status
psql -h [host] -U [user] -d [database] -c "
SELECT key_name, is_active, next_rotation_at
FROM encryption.keys;"

# 4. Verify audit events
psql -h [host] -U [user] -d [database] -c "
SELECT event_type, severity, COUNT(*)
FROM audit.events
GROUP BY event_type, severity;"

# 5. Check API endpoints
psql -h [host] -U [user] -d [database] -c "
SELECT endpoint_path, method, rate_limit_per_hour
FROM api_endpoints
ORDER BY endpoint_path;"
```

## Troubleshooting Guide

### Common Issues

#### Issue: RLS policies blocking all access
**Solution:**
```sql
-- Temporarily disable RLS
ALTER TABLE [table_name] DISABLE ROW LEVEL SECURITY;

-- Check policy
SELECT * FROM pg_policies WHERE tablename = '[table_name]';

-- Fix policy and re-enable
ALTER TABLE [table_name] ENABLE ROW LEVEL SECURITY;
```

#### Issue: Key rotation failing
**Solution:**
```sql
-- Check key status
SELECT * FROM encryption.key_rotation_status WHERE rotation_status = 'FAILED';

-- Manual rotation
SELECT encryption.rotate_key('[key_id]', 'manual');

-- Check rotation log
SELECT * FROM encryption.rotation_log ORDER BY created_at DESC LIMIT 5;
```

#### Issue: Audit logs not being created
**Solution:**
```sql
-- Check audit function
SELECT * FROM pg_proc WHERE proname = 'log_data_changes';

-- Test manual audit
SELECT audit.log_event('test', 'low', auth.uid(), 'test', 'test', 'Manual test');

-- Check trigger
SELECT trigger_name, event_manipulation 
FROM information_schema.triggers 
WHERE event_object_table = '[table_name]';
```

#### Issue: API rate limiting too aggressive
**Solution:**
```sql
-- Check current limits
SELECT * FROM api_rate_limit_violations;

-- Update rate limit
UPDATE api_rate_limits 
SET requests_per_hour = 2000 
WHERE identifier_type = 'user_id' 
AND identifier_value = '[user_id]';
```

## Security Verification Script

Create a script to verify security deployment:

```bash
#!/bin/bash
# security_verify.sh

DB_HOST=$1
DB_USER=$2
DB_NAME=$3

echo "=== Security Deployment Verification ==="
echo "Database: $DB_NAME"
echo "Host: $DB_HOST"
echo "User: $DB_USER"
echo ""

# Check schemas
echo "1. Checking schemas..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\dn" | grep -E "(security|encryption|audit|api)"
echo ""

# Check roles
echo "2. Checking roles..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT role_name FROM security.roles ORDER BY role_name;"
echo ""

# Check keys
echo "3. Checking encryption keys..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT key_name, is_active FROM encryption.keys;"
echo ""

# Check API endpoints
echo "4. Checking API endpoints..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as endpoint_count FROM api_endpoints;"
echo ""

# Check audit events
echo "5. Checking audit events..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as event_count FROM audit.events;"
echo ""

# Test function
echo "6. Testing security functions..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT security.has_permission(auth.uid(), 'system', 'admin');"
echo ""

echo "=== Verification Complete ==="
```

## Sign-off Checklist

- [ ] All security schemas deployed
- [ ] RBAC system functional
- [ ] RLS policies active
- [ ] API security configured
- [ ] Encryption system operational
- [ ] Audit logging active
- [ ] Initial admin user created
- [ ] Security tests passed
- [ ] Compliance mappings verified
- [ ] Documentation complete
- [ ] Backup procedures tested
- [ ] Incident response ready

**Deployed by:** ________________  
**Date:** ________________  
**Signature:** ________________

## Next Steps

1. **User Onboarding**: Begin assigning appropriate roles to users
2. **Data Classification**: Classify existing data and configure encryption
3. **Monitoring Setup**: Configure SIEM integration and alerting
4. **Compliance Reporting**: Generate initial compliance reports
5. **Training**: Conduct security awareness training for users
6. **Regular Reviews**: Schedule quarterly security reviews

## Support Contacts

- **Security Team**: security@yourcompany.com
- **Compliance Team**: compliance@yourcompany.com
- **Database Admin**: dba@yourcompany.com
- **Emergency Contact**: +1-XXX-XXX-XXXX

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-31  
**Next Review Date:** 2026-01-31