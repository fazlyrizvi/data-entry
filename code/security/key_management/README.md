# Secure API Key Management System

A comprehensive, enterprise-grade API key management solution with automatic rotation, secure storage, and comprehensive audit logging.

## 🚀 Features

- **Secure Key Generation**: Support for HMAC, RSA, ECDSA, JWT, and custom API tokens
- **Automatic Rotation**: Flexible rotation policies with multiple strategies
- **Encrypted Storage**: AES-256 encryption at rest with HSM support
- **Supabase Integration**: Native cloud storage and edge function support
- **Comprehensive Audit**: Complete audit trails for all key operations
- **Rate Limiting**: Built-in rate limiting and usage tracking
- **Monitoring**: Real-time metrics and alerting integration

## 📋 Prerequisites

- Python 3.9 or higher
- pip package manager
- (Optional) Supabase account for cloud storage
- (Optional) HSM for production key management

## 🔧 Installation

1. **Clone or download the project:**
```bash
cd /workspace/code/security/key_management
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
# Create .env file
cat > .env << 'EOF'
KEY_STORE_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
EOF
```

## 🎯 Quick Start

### Basic Usage

```python
from key_generator import SecureKeyGenerator, KeyType, KeyScope
from key_store import SecureKeyStore
from cryptography.fernet import Fernet

# Initialize components
generator = SecureKeyGenerator()
encryption_key = Fernet.generate_key()
store = SecureKeyStore(storage_backend="local", encryption_key=encryption_key)

# Generate an API key
api_key = generator.generate_api_key(
    key_type=KeyType.API_TOKEN,
    key_scope=KeyScope.READ_WRITE,
    expires_in=86400 * 30  # 30 days
)

# Store securely
store.store_key(api_key)

# Verify the key
is_valid, message = store.verify_key(api_key.key_id)
print(f"Key valid: {is_valid}")
```

### Run Examples

```bash
python example_usage.py
```

This will run through several examples showing:
- Basic key generation and storage
- Rotation policy setup
- Monitoring and audit trails
- Supabase integration
- Batch operations
- Security features

## 📁 Project Structure

```
key_management/
├── key_generator.py      # Cryptographic key generation
├── key_store.py          # Secure storage with encryption
├── key_rotator.py        # Automatic rotation policies
├── example_usage.py      # Comprehensive examples
├── requirements.txt      # Python dependencies
├── storage/              # Local storage (created at runtime)
│   ├── keys.json.enc     # Encrypted keys
│   ├── metadata.json     # Key metadata
│   └── audit.jsonl       # Audit log
├── rotation_policies.json  # Rotation policies
└── rotation_history.jsonl  # Rotation history
```

## 🔐 Key Types

| Type | Description | Use Case |
|------|-------------|----------|
| `HMAC` | Hash-based Message Authentication | API request signing |
| `RSA` | RSA key pairs | Asymmetric encryption |
| `ECDSA` | Elliptic Curve signatures | Modern signatures |
| `JWT` | JSON Web Token keys | Token signing |
| `API_TOKEN` | Custom API tokens | Authentication |
| `PROVISIONING` | Provisioning keys | System provisioning |

## 🔄 Rotation Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| `IMMEDIATE` | Replace key immediately | Development |
| `GRADUAL` | Phased rollout | Load-balanced services |
| `OVERLAPPING` | Maintain overlap period | Production |
| `BLUE_GREEN` | Complete environment switch | Critical systems |

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│        Application Layer            │
├─────────────────────────────────────┤
│  Key Generator → Key Store → Rotator│
├─────────────────────────────────────┤
│        Security Layer               │
│  AES-256 • HSM • Access Control     │
├─────────────────────────────────────┤
│       Storage Backend               │
│  Supabase • Local Filesystem        │
└─────────────────────────────────────┘
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `KEY_STORE_ENCRYPTION_KEY` | Yes | 32-byte encryption key (base64) |
| `SUPABASE_URL` | No | Supabase project URL |
| `SUPABASE_KEY` | No | Supabase service role key |
| `HSM_ENABLED` | No | Enable HSM integration |
| `ROTATION_CHECK_INTERVAL` | No | Rotation check interval (seconds) |

### Storage Backends

#### Local Storage (Development)
```python
store = SecureKeyStore(storage_backend="local", encryption_key=key)
```

#### Supabase (Production)
```python
store = SecureKeyStore(
    storage_backend="supabase",
    encryption_key=key,
    supabase_url=os.environ["SUPABASE_URL"],
    supabase_key=os.environ["SUPABASE_KEY"]
)
```

## 📊 Monitoring

### Audit Events
- `key_created` - New key generated
- `key_retrieved` - Key accessed
- `key_used` - Key used for authentication
- `key_revoked` - Key revoked
- `key_rotated` - Key rotated
- `verify_failed` - Verification failed

### Metrics
```python
# Get key statistics
keys = store.list_keys()
active_keys = [k for k in keys if k.is_active]

# Get rotation statistics
from key_rotator import KeyRotator
stats = rotator.get_rotation_statistics()
print(f"Total rotations: {stats['total_rotations']}")
print(f"Success rate: {stats['successful_rotations'] / max(stats['total_rotations'], 1) * 100:.1f}%")
```

## 🧪 Testing

```bash
# Run example script
python example_usage.py

# Run tests (if test suite is available)
pytest tests/
```

## 📚 Documentation

See [Documentation](../docs/key_management_implementation.md) for:
- Complete API reference
- Security best practices
- Supabase integration guide
- HSM integration
- Deployment instructions

## 🔒 Security Considerations

### Production Checklist

- [ ] Use HSM for key generation/storage
- [ ] Set proper environment variables
- [ ] Enable audit logging
- [ ] Configure rate limiting
- [ ] Set up monitoring and alerting
- [ ] Implement proper access controls
- [ ] Test rotation procedures
- [ ] Create backup/recovery plan
- [ ] Review security audit logs
- [ ] Implement anomaly detection

### Key Management

- Generate strong encryption keys (256-bit minimum)
- Use environment-specific configurations
- Rotate secrets regularly
- Never commit secrets to version control
- Implement proper access logging

## 🆘 Troubleshooting

### Common Issues

**Key verification fails:**
```python
# Check if key exists and is active
metadata = store.get_key_metadata(key_id)
if not metadata or not metadata.is_active:
    print("Key not found or revoked")
```

**Rotation fails:**
```python
# Check rotation history
history = rotator.get_rotation_history(key_id=key_id)
for event in history[-5:]:
    if not event.success:
        print(f"Error: {event.error_message}")
```

**Storage issues:**
```python
# Test storage backend
try:
    result = store.list_keys()
    print(f"Storage OK: {len(result)} keys")
except Exception as e:
    print(f"Storage error: {e}")
```

## 📄 License

This project is part of the Enterprise Data Automation System.

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the documentation
3. Run the example script to verify setup
4. Check audit logs for errors

## 🔄 Version History

- **v1.0.0** - Initial release
  - Basic key generation and storage
  - Automatic rotation policies
  - Supabase integration
  - Comprehensive audit logging
  - Rate limiting and monitoring

## 🎯 Roadmap

- [ ] HSM vendor integrations (AWS KMS, Azure Key Vault, GCP KMS)
- [ ] GraphQL API interface
- [ ] Kubernetes operator
- [ ] Advanced anomaly detection with ML
- [ ] Multi-region replication
- [ ] Zero-downtime key rotations
- [ ] Certificate management (PKI)
- [ ] Hardware token support (YubiKey, etc.)
