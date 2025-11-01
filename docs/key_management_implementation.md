# Secure API Key Management System - Implementation Guide

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Components](#components)
5. [Installation & Setup](#installation--setup)
6. [Usage Examples](#usage-examples)
7. [Security Considerations](#security-considerations)
8. [Supabase Integration](#supabase-integration)
9. [Key Lifecycle Management](#key-lifecycle-management)
10. [Rotation Policies](#rotation-policies)
11. [Monitoring & Audit](#monitoring--audit)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)
14. [API Reference](#api-reference)

## Overview

The Secure API Key Management System provides enterprise-grade API key generation, storage, rotation, and monitoring. It implements industry best practices for cryptographic key management with support for Hardware Security Modules (HSM), cloud key management services, and comprehensive audit logging.

### Key Benefits

- **Security First**: Encryption at rest and in transit, HSM integration support
- **Automation**: Automatic key rotation with flexible policies
- **Scalability**: Support for millions of keys with efficient storage
- **Compliance**: Comprehensive audit trails and compliance reporting
- **Integration**: Native Supabase integration and edge function support
- **Monitoring**: Real-time usage tracking and anomaly detection

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 API Key Management System               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Key Generator │  │ Key Store    │  │ Key Rotator  │  │
│  │               │  │              │  │              │  │
│  │ • HMAC        │  │ • Encryption │  │ • Policies   │  │
│  │ • RSA         │  │ • HSM        │  │ • Scheduling │  │
│  │ • ECDSA       │  │ • Supabase   │  │ • Strategies │  │
│  │ • JWT         │  │ • Rate Limit │  │ • Audit      │  │
│  │ • Tokens      │  │ • Audit      │  │              │  │
│  └───────────────┘  └──────────────┘  └──────────────┘  │
│         │                   │                   │        │
│         └───────────────────┼───────────────────┘        │
│                             │                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │         Security Layer                            │  │
│  │  • AES-256 Encryption                             │  │
│  │  • HSM Integration                                │  │
│  │  • Access Control                                 │  │
│  │  • Key Derivation (PBKDF2, HKDF)                  │  │
│  └────────────────────────────────────────────────────┘  │
│                             │                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │         Storage Backend                            │  │
│  │  • Supabase (Primary)                             │  │
│  │  • Local File System (Fallback)                   │  │
│  │  • Encrypted at Rest                              │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Features

### Key Generation
- Multiple cryptographic algorithms (HMAC, RSA, ECDSA, JWT)
- Secure random number generation
- Custom key formats and prefixes
- Metadata attachment
- Key versioning support

### Secure Storage
- AES-256 encryption at rest
- HSM integration ready
- Encrypted key transport
- Access control and permissions
- Rate limiting per key
- Automatic key expiration

### Key Rotation
- Flexible rotation policies
- Multiple rotation strategies (immediate, gradual, overlapping, blue-green)
- Automatic scheduling
- Service continuity maintenance
- Rotation audit trails
- Notification system integration

### Monitoring & Audit
- Comprehensive usage tracking
- Audit log for all key operations
- Real-time monitoring
- Anomaly detection
- Compliance reporting
- Metrics export (Prometheus compatible)

### Integration
- Supabase native integration
- Edge function support
- Environment variable management
- RESTful API interface
- Webhook notifications
- CI/CD pipeline integration

## Components

### 1. Key Generator (`key_generator.py`)

Responsible for secure cryptographic key generation.

**Key Classes:**
- `SecureKeyGenerator`: Main key generation class
- `GeneratedKey`: Key data container
- `KeyType`: Supported key types enum
- `KeyScope`: Permission scopes enum

**Key Types:**
- HMAC: Hash-based Message Authentication
- RSA: RSA key pairs
- ECDSA: Elliptic Curve Digital Signature
- JWT: JSON Web Token signing keys
- API_TOKEN: Custom API tokens
- PROVISIONING: Provisioning keys

### 2. Key Store (`key_store.py`)

Handles secure storage and retrieval of API keys.

**Key Classes:**
- `SecureKeyStore`: Main storage class
- `KeyMetadata`: Key metadata container
- `KeyUsageEvent`: Audit event record

**Features:**
- AES encryption at rest
- Supabase and local storage backends
- Rate limiting
- Automatic expiration
- Usage tracking
- Audit logging

### 3. Key Rotator (`key_rotator.py`)

Manages automatic key rotation policies and schedules.

**Key Classes:**
- `KeyRotator`: Main rotation management class
- `RotationPolicy`: Policy configuration
- `RotationEvent`: Rotation audit record
- `RotationFrequency`: Rotation schedule enum
- `RotationStrategy`: Rotation method enum

**Rotation Strategies:**
- **Immediate**: Replace key immediately
- **Gradual**: Phased rollout
- **Overlapping**: Maintain overlap period
- **Blue-Green**: Complete environment switch

## Installation & Setup

### Prerequisites

```bash
# Python 3.9 or higher
python --version

# pip for package management
pip --version
```

### Installation

1. **Clone or download the key management system:**

```bash
# Create project directory
mkdir -p /workspace/code/security/key_management
cd /workspace/code/security/key_management
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**

Create a `.env` file:

```bash
# Encryption key (generate a 32-byte key)
KEY_STORE_ENCRYPTION_KEY=YOUR_BASE64_ENCODED_32_BYTE_KEY

# Supabase configuration (optional, for cloud storage)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key

# HSM configuration (if using)
HSM_ENABLED=false
HSM_CONFIG_PATH=/path/to/hsm/config

# Rotation scheduling
ROTATION_CHECK_INTERVAL=3600  # seconds
NOTIFICATION_WEBHOOK_URL=https://your-webhook-url.com/notify
```

### Quick Start

```python
from key_generator import SecureKeyGenerator, KeyType, KeyScope
from key_store import SecureKeyStore
from key_rotator import KeyRotator, RotationPolicy, RotationFrequency, RotationStrategy

# Initialize components
generator = SecureKeyGenerator(hsm_enabled=False)
store = SecureKeyStore(
    storage_backend="local",
    encryption_key=base64.b64decode(os.environ["KEY_STORE_ENCRYPTION_KEY"])
)
rotator = KeyRotator(generator, store)

# Generate an API key
api_key = generator.generate_api_key(
    key_type=KeyType.API_TOKEN,
    key_scope=KeyScope.READ_WRITE,
    expires_in=86400 * 30  # 30 days
)

# Store the key
store.store_key(api_key)

# Verify the key
is_valid, message = store.verify_key(api_key.key_id)
print(f"Key valid: {is_valid}, Message: {message}")

# Create rotation policy
policy = RotationPolicy(
    policy_id="monthly_rotation",
    name="Monthly Key Rotation",
    key_type=KeyType.API_TOKEN,
    scope=KeyScope.ADMIN,
    frequency=RotationFrequency.MONTHLY,
    strategy=RotationStrategy.OVERLAPPING,
    overlap_duration_hours=48
)
rotator.create_rotation_policy(policy)
```

## Usage Examples

### Example 1: Basic API Key Management

```python
import os
import base64
from key_generator import SecureKeyGenerator, KeyType, KeyScope
from key_store import SecureKeyStore

# Initialize with encryption
encryption_key = os.environ.get("KEY_STORE_ENCRYPTION_KEY")
if not encryption_key:
    # Generate for development
    from cryptography.fernet import Fernet
    encryption_key = Fernet.generate_key()

store = SecureKeyStore(
    storage_backend="local",
    encryption_key=base64.b64decode(encryption_key)
)

generator = SecureKeyGenerator()

# Generate a production API key
api_key = generator.generate_api_key(
    key_type=KeyType.API_TOKEN,
    key_scope=KeyScope.READ_WRITE,
    expires_in=86400 * 90,  # 90 days
    metadata={
        "environment": "production",
        "application": "mobile_app",
        "created_by": "admin"
    }
)

# Store the key
success = store.store_key(api_key)
if success:
    print(f"API Key generated: {api_key.key_id}")
    print(f"Key value: {api_key.key_value}")

# Later, retrieve the key
retrieved_key = store.retrieve_key(api_key.key_id)
if retrieved_key:
    print(f"Retrieved key: {retrieved_key.key_value}")

# Verify key validity
is_valid, message = store.verify_key(api_key.key_id)
print(f"Key status: {is_valid} - {message}")
```

### Example 2: Automatic Key Rotation

```python
from key_rotator import (
    KeyRotator, RotationPolicy, RotationFrequency, RotationStrategy
)

rotator = KeyRotator(generator, store)

# Create a policy for high-security keys
policy = RotationPolicy(
    policy_id="high_security_rotation",
    name="High Security Key Rotation",
    key_type=KeyType.HMAC,
    scope=KeyScope.ADMIN,
    frequency=RotationFrequency.WEEKLY,
    strategy=RotationStrategy.BLUE_GREEN,
    advance_notice_hours=24,
    overlap_duration_hours=12
)

rotator.create_rotation_policy(policy)

# Rotate keys manually
rotated_key = rotator.rotate_key(
    key_id="existing_key_id",
    rotation_type="manual"
)

# Check for scheduled rotations
keys_due = rotator.check_rotation_schedules()
print(f"Keys due for rotation: {keys_due}")
```

### Example 3: Supabase Integration

```python
from key_store import SecureKeyStore

# Initialize Supabase storage
store = SecureKeyStore(
    storage_backend="supabase",
    encryption_key=base64.b64decode(encryption_key),
    supabase_url=os.environ["SUPABASE_URL"],
    supabase_key=os.environ["SUPABASE_KEY"]
)

# Generate and store with Supabase
api_key = generator.generate_api_key(
    key_type=KeyType.PROVISIONING,
    key_scope=KeyScope.FULL,
    expires_in=86400 * 365  # 1 year
)

store.store_key(api_key)

# Export for Supabase edge function
supabase_format = generator.export_key_for_supabase(api_key)
print(json.dumps(supabase_format, indent=2))
```

### Example 4: Custom Notification Handler

```python
def rotation_notification_handler(notification_type: str, data: dict):
    """Custom notification handler for rotation events"""
    if notification_type == "rotation_scheduled":
        # Send email/SMS/webhook
        send_notification(
            subject=f"Key Rotation Scheduled: {data['policy_name']}",
            message=f"Rotation scheduled for {data['scheduled_time']}"
        )
    elif notification_type == "key_rotated":
        # Log the rotation
        log_rotation(data['new_key_id'], data['old_key_id'])

# Initialize with custom notification handler
rotator = KeyRotator(generator, store, rotation_notification_handler)
```

### Example 5: Edge Function Integration (Supabase)

```typescript
// supabase/functions/verify-api-key/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

interface VerifyKeyRequest {
  key_id: string;
}

serve(async (req) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
  }

  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  try {
    const { key_id }: VerifyKeyRequest = await req.json()
    
    // Verify key using key management system
    const result = await verifyKey(key_id)
    
    return new Response(
      JSON.stringify({ valid: result.valid, message: result.message }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: result.valid ? 200 : 401
      }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: 'Key verification failed', message: error.message }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})

async function verifyKey(keyId: string) {
  // Implementation would use the key store to verify the key
  // This is a placeholder for the actual implementation
  return { valid: true, message: 'Key is valid' }
}
```

### Example 6: Monitoring and Audit

```python
# Get usage statistics
keys = store.list_keys()
for key in keys:
    print(f"Key: {key.key_id}")
    print(f"  Usage count: {key.usage_count}")
    print(f"  Last used: {key.last_used}")
    print(f"  Active: {key.is_active}")

# Get audit log
audit_events = store.get_audit_log(
    key_id="specific_key_id",
    limit=50
)
for event in audit_events:
    print(f"Event: {event.action} at {event.timestamp}")
    print(f"  Success: {event.success}")
    if not event.success:
        print(f"  Error: {event.error_message}")

# Get rotation statistics
stats = rotator.get_rotation_statistics()
print(f"Total policies: {stats['total_policies']}")
print(f"Total rotations: {stats['total_rotations']}")
print(f"Success rate: {stats['successful_rotations'] / max(stats['total_rotations'], 1) * 100:.1f}%")
```

## Security Considerations

### Encryption

1. **At Rest**: All keys are encrypted using AES-256
2. **In Transit**: Use HTTPS/TLS for all communications
3. **Key Derivation**: PBKDF2/HKDF for key derivation
4. **Salting**: Unique salt for each key derivation

### Access Control

1. **Authentication**: Verify caller identity
2. **Authorization**: Check permissions before key access
3. **Audit Logging**: Log all key operations
4. **Rate Limiting**: Prevent abuse with rate limits

### Key Storage

1. **HSM Integration**: Use Hardware Security Modules for production
2. **Separation of Duties**: Separate key generation from storage
3. **Backup Security**: Encrypt backup data
4. **Key Escrow**: Implement secure key recovery

### Rotation Security

1. **Secure Rotation**: Ensure old keys are properly revoked
2. **Overlap Period**: Maintain both old and new keys during transition
3. **Audit Trail**: Log all rotation activities
4. **Emergency Procedures**: Have emergency rotation procedures

### Environment Variables

**Critical Variables:**
- `KEY_STORE_ENCRYPTION_KEY`: Master encryption key
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase service key

**Security:**
- Never commit secrets to version control
- Use environment-specific configurations
- Rotate secrets regularly
- Use secret management services

## Supabase Integration

### Database Schema

```sql
-- API Keys table
CREATE TABLE api_keys (
  id SERIAL PRIMARY KEY,
  key_id VARCHAR(255) UNIQUE NOT NULL,
  encrypted_value TEXT NOT NULL,
  stored_at TIMESTAMP DEFAULT NOW()
);

-- Key Metadata table
CREATE TABLE api_key_metadata (
  id SERIAL PRIMARY KEY,
  key_id VARCHAR(255) UNIQUE NOT NULL,
  key_type VARCHAR(50) NOT NULL,
  scope VARCHAR(100) NOT NULL,
  algorithm VARCHAR(50) NOT NULL,
  key_length INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL,
  last_used TIMESTAMP,
  expires_at TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,
  usage_count INTEGER DEFAULT 0,
  metadata JSONB,
  rotation_history JSONB,
  revoked_at TIMESTAMP,
  revocation_reason TEXT
);

-- Audit Log table
CREATE TABLE api_key_audit_log (
  id SERIAL PRIMARY KEY,
  event_id VARCHAR(255) UNIQUE NOT NULL,
  key_id VARCHAR(255) NOT NULL,
  action VARCHAR(50) NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  source_ip INET,
  user_agent TEXT,
  endpoint VARCHAR(255),
  success BOOLEAN NOT NULL,
  error_message TEXT
);

-- Row Level Security (RLS)
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_key_metadata ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users
CREATE POLICY "Authenticated users can read keys" ON api_keys
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Service role can manage keys" ON api_keys
  FOR ALL USING (auth.role() = 'service_role');
```

### Environment Setup

```bash
# Set Supabase environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-service-role-key"

# Set encryption key
export KEY_STORE_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

### Edge Function Example

```typescript
// supabase/functions/api-key-manager/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    const { action, key_id, key_data } = await req.json()

    let result
    switch (action) {
      case 'verify':
        result = await verifyKey(supabase, key_id)
        break
      case 'rotate':
        result = await rotateKey(supabase, key_id)
        break
      case 'generate':
        result = await generateKey(supabase, key_data)
        break
      default:
        throw new Error('Invalid action')
    }

    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})

async function verifyKey(supabase: any, keyId: string) {
  const { data, error } = await supabase
    .from('api_key_metadata')
    .select('*')
    .eq('key_id', keyId)
    .single()

  if (error || !data) {
    return { valid: false, message: 'Key not found' }
  }

  const now = new Date()
  if (data.expires_at && new Date(data.expires_at) < now) {
    return { valid: false, message: 'Key expired' }
  }

  if (!data.is_active) {
    return { valid: false, message: 'Key revoked' }
  }

  // Log usage
  await supabase
    .from('api_key_audit_log')
    .insert({
      key_id: keyId,
      action: 'verify',
      timestamp: new Date().toISOString(),
      success: true
    })

  return { valid: true, message: 'Key is valid', data }
}
```

## Key Lifecycle Management

### Phase 1: Key Creation

1. **Generate Key**
   ```python
   key = generator.generate_api_key(
       key_type=KeyType.API_TOKEN,
       key_scope=KeyScope.READ_WRITE,
       expires_in=86400 * 90
   )
   ```

2. **Store Key**
   ```python
   store.store_key(key)
   ```

3. **Distribute Key**
   ```python
   # Export for distribution
   export_data = generator.export_key_for_supabase(key)
   ```

### Phase 2: Key Usage

1. **Verify Key**
   ```python
   is_valid, message = store.verify_key(key_id)
   ```

2. **Log Usage**
   ```python
   # Automatic with verify_key()
   ```

3. **Monitor Usage**
   ```python
   events = store.get_audit_log(key_id=key_id)
   ```

### Phase 3: Key Rotation

1. **Schedule Rotation**
   ```python
   policy = RotationPolicy(
       policy_id="auto_rotation",
       frequency=RotationFrequency.MONTHLY,
       strategy=RotationStrategy.OVERLAPPING
   )
   rotator.create_rotation_policy(policy)
   ```

2. **Perform Rotation**
   ```python
   new_key = rotator.rotate_key(key_id)
   ```

3. **Distribute New Key**
   ```python
   # Automatic notification to services
   ```

### Phase 4: Key Retirement

1. **Revoke Key**
   ```python
   store.revoke_key(key_id, reason="replaced")
   ```

2. **Archive Audit Data**
   ```python
   audit_events = store.get_audit_log(key_id=key_id)
   ```

3. **Secure Deletion**
   ```python
   # Implementation depends on storage backend
   ```

## Rotation Policies

### Policy Configuration

```python
from key_rotator import RotationPolicy, RotationFrequency, RotationStrategy

# Example: High-security weekly rotation with overlap
policy = RotationPolicy(
    policy_id="high_security_weekly",
    name="High Security Weekly Rotation",
    key_type=KeyType.HMAC,
    scope=KeyScope.ADMIN,
    frequency=RotationFrequency.WEEKLY,
    strategy=RotationStrategy.OVERLAPPING,
    advance_notice_hours=48,  # 48 hours notice
    overlap_duration_hours=72,  # 72 hours overlap
    conditions={
        "max_usage_count": 10000,  # Rotate after 10k uses
        "max_age_days": 7  # Rotate after 7 days
    }
)
```

### Rotation Strategies

1. **Immediate Rotation**
   - Old key revoked immediately
   - New key activated immediately
   - Fastest but requires coordinated deployment
   - Best for: Development environments

2. **Gradual Rotation**
   - New key introduced alongside old
   - Traffic gradually shifted to new key
   - Old key marked as "phasing out"
   - Best for: Load-balanced services

3. **Overlapping Rotation**
   - Both keys active for overlap period
   - Graceful transition window
   - Automatic old key revocation
   - Best for: Production environments

4. **Blue-Green Deployment**
   - Complete environment switch
   - Zero-downtime rotation
   - Easy rollback capability
   - Best for: Critical production services

### Automatic Scheduling

```python
# Check for rotations due
keys_due = rotator.check_rotation_schedules()

# For each key due, rotation is automatic
# Notifications sent in advance
# Audit events logged
```

## Monitoring & Audit

### Audit Log Events

- `key_created`: New key generated
- `key_retrieved`: Key accessed
- `key_used`: Key used for authentication
- `key_revoked`: Key revoked
- `key_rotated`: Key rotated
- `verify_failed`: Key verification failed
- `rotation_scheduled`: Rotation scheduled
- `rotation_completed`: Rotation completed

### Metrics

```python
# Key store metrics
total_keys = len(store.list_keys())
active_keys = len(store.list_keys(active_only=True))
expired_keys = len([k for k in store.list_keys() if k.expires_at and k.expires_at < time.time()])

# Rotation metrics
stats = rotator.get_rotation_statistics()
success_rate = stats['successful_rotations'] / max(stats['total_rotations'], 1) * 100

print(f"Total keys: {total_keys}")
print(f"Active keys: {active_keys}")
print(f"Rotation success rate: {success_rate:.1f}%")
```

### Monitoring Integration

```python
# Export metrics for Prometheus
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
key_operations = Counter('api_key_operations_total', 'Total key operations', ['operation'])
key_rotation_duration = Histogram('key_rotation_duration_seconds', 'Key rotation duration')
active_keys = Gauge('api_keys_active_total', 'Number of active keys')
```

### Alerting

Set up alerts for:
- High key rotation failure rate
- Unusual key usage patterns
- Expired keys still in use
- Failed verification attempts
- Storage capacity issues

## Best Practices

### Key Generation

1. **Use Strong Algorithms**: Prefer HMAC-SHA256 or RSA-4096
2. **Adequate Key Length**: Use minimum 256-bit for HMAC, 4096-bit for RSA
3. **Proper Expiration**: Set reasonable expiration times
4. **Metadata**: Include context (environment, application, owner)

### Key Storage

1. **Encryption**: Always encrypt keys at rest
2. **Access Control**: Implement strict access controls
3. **Backup Security**: Encrypt backup data
4. **Regular Cleanup**: Remove expired/expired keys

### Key Rotation

1. **Regular Rotation**: Implement rotation policies
2. **Overlap Period**: Use overlap for smooth transitions
3. **Monitoring**: Monitor rotation success rates
4. **Testing**: Test rotation procedures regularly

### Security

1. **HSM Usage**: Use HSM for production environments
2. **Audit Logging**: Enable comprehensive audit logging
3. **Rate Limiting**: Implement rate limiting
4. **Anomaly Detection**: Monitor for unusual patterns

### Operations

1. **Documentation**: Document all procedures
2. **Training**: Train operators on procedures
3. **Testing**: Regular testing of rotation/recovery
4. **Monitoring**: 24/7 monitoring of key operations

## Troubleshooting

### Common Issues

1. **Key Verification Fails**
   ```python
   # Check key exists
   metadata = store.get_key_metadata(key_id)
   
   # Check expiration
   if metadata.expires_at and time.time() > metadata.expires_at:
       print("Key has expired")
   
   # Check if revoked
   if not metadata.is_active:
       print("Key is revoked")
   ```

2. **Rotation Failure**
   ```python
   # Check rotation history
   history = rotator.get_rotation_history(key_id=key_id)
   for event in history[-5:]:  # Last 5 events
       print(f"Event: {event.action}, Success: {event.success}")
       if not event.success:
           print(f"Error: {event.error_message}")
   ```

3. **Storage Issues**
   ```python
   # Check storage backend status
   if storage_backend == "supabase":
       # Check Supabase connection
       try:
           result = supabase_client.table("api_keys").select("count").execute()
           print("Supabase connection OK")
       except Exception as e:
           print(f"Supabase error: {e}")
   ```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will output detailed logs for troubleshooting
```

### Health Checks

```python
def health_check():
    """System health check"""
    try:
        # Test key generation
        test_key = generator.generate_api_key(
            key_type=KeyType.API_TOKEN,
            key_scope=KeyScope.READ
        )
        
        # Test storage
        success = store.store_key(test_key)
        if not success:
            return {"status": "unhealthy", "error": "Storage failed"}
        
        # Test retrieval
        retrieved = store.retrieve_key(test_key.key_id)
        if not retrieved:
            return {"status": "unhealthy", "error": "Retrieval failed"}
        
        # Cleanup
        store.revoke_key(test_key.key_id, "health_check")
        
        return {"status": "healthy", "message": "All checks passed"}
        
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## API Reference

### SecureKeyGenerator

#### Methods

```python
generate_api_key(
    key_type: KeyType,
    key_scope: KeyScope,
    key_length: KeyLength = KeyLength.MEDIUM,
    expires_in: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
    version: int = 1
) -> GeneratedKey
```

Generate a new API key.

**Parameters:**
- `key_type`: Type of key to generate
- `key_scope`: Permissions scope
- `key_length`: Key length (128, 256, 4096, 8192 bits)
- `expires_in`: Expiration time in seconds
- `metadata`: Additional metadata
- `version`: Key version number

**Returns:** `GeneratedKey` object

---

```python
generate_key_batch(
    count: int,
    key_type: KeyType,
    key_scope: KeyScope,
    **kwargs
) -> List[GeneratedKey]
```

Generate multiple keys in batch.

---

```python
derive_key_from_secret(
    secret: str,
    salt: bytes,
    key_length: int = 32,
    info: str = "api-key-derivation"
) -> bytes
```

Derive a cryptographic key from a secret.

---

```python
verify_key_integrity(key: GeneratedKey) -> bool
```

Verify the integrity of a generated key.

---

```python
rotate_key(
    old_key: GeneratedKey,
    expires_in: Optional[int] = None
) -> GeneratedKey
```

Generate a rotated version of a key.

### SecureKeyStore

#### Methods

```python
store_key(key: GeneratedKey, encrypt: bool = True) -> bool
```

Store an API key securely.

---

```python
retrieve_key(key_id: str, decrypt: bool = True) -> Optional[GeneratedKey]
```

Retrieve a stored API key.

---

```python
verify_key(key_id: str) -> Tuple[bool, str]
```

Verify a key is valid and active.

Returns tuple of (is_valid, message).

---

```python
list_keys(
    key_type: Optional[KeyType] = None,
    scope: Optional[KeyScope] = None,
    active_only: bool = True
) -> List[KeyMetadata]
```

List stored keys with optional filtering.

---

```python
revoke_key(key_id: str, reason: str = "manual_revocation") -> bool
```

Revoke an API key.

---

```python
get_audit_log(
    key_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100
) -> List[KeyUsageEvent]
```

Retrieve audit log entries.

### KeyRotator

#### Methods

```python
create_rotation_policy(policy: RotationPolicy) -> bool
```

Create a new rotation policy.

---

```python
rotate_key(
    key_id: str,
    policy_id: Optional[str] = None,
    rotation_type: str = "manual",
    **kwargs
) -> Optional[GeneratedKey]
```

Rotate a specific key.

---

```python
check_rotation_schedules() -> List[str]
```

Check for keys that need rotation.

Returns list of policy IDs with keys due for rotation.

---

```python
get_rotation_history(
    policy_id: Optional[str] = None,
    limit: int = 100
) -> List[RotationEvent]
```

Get rotation history.

---

```python
get_rotation_statistics() -> Dict[str, Any]
```

Get rotation statistics.

---

```python
cleanup_old_rotations(keep_days: int = 90) -> int
```

Clean up old rotation events.

Returns number of events kept.

## Conclusion

The Secure API Key Management System provides enterprise-grade security for API key lifecycle management. With support for multiple cryptographic algorithms, automatic rotation policies, and comprehensive audit logging, it meets the requirements of modern security-conscious applications.

For questions or support, please refer to the implementation files or create an issue in the project repository.

---

**Version:** 1.0.0  
**Last Updated:** 2025-10-31  
**Author:** Security Team
