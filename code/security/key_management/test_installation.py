#!/usr/bin/env python3
"""
Installation Test Script

Tests that all components of the key management system are properly installed
and functional.
"""

import sys
import os
import traceback
from datetime import datetime

# Test results tracker
test_results = []
total_tests = 0
passed_tests = 0


def test(name, test_func):
    """Run a test and track results"""
    global total_tests, passed_tests
    total_tests += 1
    
    print(f"\n{'=' * 60}")
    print(f"Test {total_tests}: {name}")
    print('=' * 60)
    
    try:
        test_func()
        passed_tests += 1
        test_results.append((name, "PASS", None))
        print(f"✅ PASSED: {name}")
    except Exception as e:
        error_msg = str(e)
        test_results.append((name, "FAIL", error_msg))
        print(f"❌ FAILED: {name}")
        print(f"Error: {error_msg}")
        traceback.print_exc()


def test_python_version():
    """Test Python version"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        raise Exception("Python 3.9 or higher is required")
    
    print("✅ Python version OK")


def test_dependencies():
    """Test required dependencies"""
    print("Checking dependencies...")
    
    required_modules = [
        'cryptography',
        'secrets',
        'json',
        'time',
        'logging',
        'base64',
        'pathlib',
        'dataclasses',
        'enum',
        'typing'
    ]
    
    optional_modules = [
        ('supabase', 'Supabase client'),
        ('croniter', 'Cron parser for rotation schedules'),
    ]
    
    # Check required modules
    missing_required = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            missing_required.append(module)
            print(f"  ❌ {module} - {e}")
    
    # Check optional modules
    missing_optional = []
    for module, description in optional_modules:
        try:
            __import__(module)
            print(f"  ✅ {module} ({description})")
        except ImportError:
            missing_optional.append((module, description))
            print(f"  ⚠️  {module} ({description}) - optional")
    
    if missing_required:
        raise Exception(f"Missing required modules: {', '.join(missing_required)}")
    
    if missing_optional:
        print(f"\n⚠️  Warning: {len(missing_optional)} optional modules missing")
        print("   Some features may not be available without these modules")


def test_imports():
    """Test importing all modules"""
    print("Testing module imports...")
    
    try:
        from key_generator import (
            SecureKeyGenerator,
            GeneratedKey,
            KeyType,
            KeyScope,
            KeyLength
        )
        print("  ✅ key_generator module")
    except Exception as e:
        raise Exception(f"Failed to import key_generator: {e}")
    
    try:
        from key_store import (
            SecureKeyStore,
            KeyMetadata,
            KeyUsageEvent
        )
        print("  ✅ key_store module")
    except Exception as e:
        raise Exception(f"Failed to import key_store: {e}")
    
    try:
        from key_rotator import (
            KeyRotator,
            RotationPolicy,
            RotationFrequency,
            RotationStrategy,
            RotationEvent
        )
        print("  ✅ key_rotator module")
    except Exception as e:
        raise Exception(f"Failed to import key_rotator: {e}")


def test_key_generation():
    """Test key generation functionality"""
    print("Testing key generation...")
    
    from key_generator import SecureKeyGenerator, KeyType, KeyScope
    
    generator = SecureKeyGenerator(hsm_enabled=False)
    print("  ✅ SecureKeyGenerator initialized")
    
    # Test HMAC key generation
    hmac_key = generator.generate_api_key(
        key_type=KeyType.HMAC,
        key_scope=KeyScope.READ,
        expires_in=3600
    )
    assert hmac_key.key_id is not None
    assert hmac_key.key_value is not None
    assert hmac_key.key_type == KeyType.HMAC.value
    print(f"  ✅ HMAC key generated: {hmac_key.key_id}")
    
    # Test API token generation
    token_key = generator.generate_api_key(
        key_type=KeyType.API_TOKEN,
        key_scope=KeyScope.READ_WRITE,
        expires_in=86400
    )
    assert token_key.key_id is not None
    assert token_key.key_value is not None
    assert token_key.key_type == KeyType.API_TOKEN.value
    print(f"  ✅ API token generated: {token_key.key_id}")
    
    # Test batch generation
    batch_keys = generator.generate_key_batch(
        count=3,
        key_type=KeyType.API_TOKEN,
        key_scope=KeyScope.READ,
        expires_in=7200
    )
    assert len(batch_keys) == 3
    print(f"  ✅ Batch generation: {len(batch_keys)} keys")


def test_key_storage():
    """Test key storage functionality"""
    print("Testing key storage...")
    
    from key_generator import SecureKeyGenerator, KeyType, KeyScope
    from key_store import SecureKeyStore
    from cryptography.fernet import Fernet
    
    # Generate test encryption key
    encryption_key = Fernet.generate_key()
    
    generator = SecureKeyGenerator()
    store = SecureKeyStore(
        storage_backend="local",
        encryption_key=encryption_key
    )
    print("  ✅ SecureKeyStore initialized")
    
    # Generate and store a key
    test_key = generator.generate_api_key(
        key_type=KeyType.API_TOKEN,
        key_scope=KeyScope.READ_WRITE,
        expires_in=3600,
        metadata={"test": True}
    )
    
    success = store.store_key(test_key)
    assert success, "Failed to store key"
    print(f"  ✅ Key stored: {test_key.key_id}")
    
    # Retrieve the key
    retrieved_key = store.retrieve_key(test_key.key_id)
    assert retrieved_key is not None, "Failed to retrieve key"
    assert retrieved_key.key_id == test_key.key_id
    print(f"  ✅ Key retrieved: {retrieved_key.key_id}")
    
    # Verify the key
    is_valid, message = store.verify_key(test_key.key_id)
    assert is_valid, f"Key verification failed: {message}"
    print(f"  ✅ Key verified: {message}")
    
    # List keys
    keys = store.list_keys()
    assert len(keys) > 0, "No keys found in storage"
    print(f"  ✅ Listed {len(keys)} keys")
    
    # Revoke the key
    revoked = store.revoke_key(test_key.key_id, "test_revocation")
    assert revoked, "Failed to revoke key"
    print(f"  ✅ Key revoked: {test_key.key_id}")


def test_key_rotation():
    """Test key rotation functionality"""
    print("Testing key rotation...")
    
    from key_generator import SecureKeyGenerator, KeyType, KeyScope
    from key_store import SecureKeyStore
    from key_rotator import KeyRotator, RotationPolicy, RotationFrequency, RotationStrategy
    from cryptography.fernet import Fernet
    
    encryption_key = Fernet.generate_key()
    
    generator = SecureKeyGenerator()
    store = SecureKeyStore(storage_backend="local", encryption_key=encryption_key)
    rotator = KeyRotator(generator, store)
    
    # Create a test key
    test_key = generator.generate_api_key(
        key_type=KeyType.API_TOKEN,
        key_scope=KeyScope.ADMIN,
        expires_in=7200
    )
    store.store_key(test_key)
    print(f"  ✅ Test key created: {test_key.key_id}")
    
    # Create a rotation policy
    policy = RotationPolicy(
        policy_id="test_policy",
        name="Test Policy",
        key_type=KeyType.API_TOKEN,
        scope=KeyScope.ADMIN,
        frequency=RotationFrequency.DAILY,
        strategy=RotationStrategy.IMMEDIATE
    )
    success = rotator.create_rotation_policy(policy)
    assert success, "Failed to create rotation policy"
    print(f"  ✅ Rotation policy created: {policy.policy_id}")
    
    # Rotate the key
    rotated_key = rotator.rotate_key(
        test_key.key_id,
        rotation_type="manual"
    )
    assert rotated_key is not None, "Failed to rotate key"
    assert rotated_key.key_id != test_key.key_id
    print(f"  ✅ Key rotated: {test_key.key_id} -> {rotated_key.key_id}")
    
    # Check rotation statistics
    stats = rotator.get_rotation_statistics()
    assert "total_rotations" in stats
    print(f"  ✅ Rotation statistics: {stats['total_rotations']} total rotations")


def test_key_derivation():
    """Test key derivation functionality"""
    print("Testing key derivation...")
    
    from key_generator import SecureKeyGenerator
    
    generator = SecureKeyGenerator()
    
    # Test HKDF derivation
    secret = "test_secret"
    salt = b"test_salt_16_bytes"
    
    derived_key = generator.derive_key_from_secret(
        secret=secret,
        salt=salt,
        key_length=32,
        info="test_derivation"
    )
    
    assert len(derived_key) == 32, "Derived key length incorrect"
    print(f"  ✅ Key derivation: {len(derived_key)} bytes")
    
    # Test that same inputs produce same output
    derived_key2 = generator.derive_key_from_secret(
        secret=secret,
        salt=salt,
        key_length=32,
        info="test_derivation"
    )
    
    assert derived_key == derived_key2, "Key derivation not deterministic"
    print("  ✅ Key derivation is deterministic")


def test_key_integrity():
    """Test key integrity verification"""
    print("Testing key integrity verification...")
    
    from key_generator import SecureKeyGenerator, KeyType, KeyScope
    
    generator = SecureKeyGenerator()
    
    # Generate various key types
    key_types = [KeyType.HMAC, KeyType.API_TOKEN, KeyType.JWT]
    
    for key_type in key_types:
        key = generator.generate_api_key(
            key_type=key_type,
            key_scope=KeyScope.READ
        )
        
        is_valid = generator.verify_key_integrity(key)
        assert is_valid, f"Key integrity check failed for {key_type}"
        print(f"  ✅ {key_type.value} integrity verified")


def test_audit_logging():
    """Test audit logging functionality"""
    print("Testing audit logging...")
    
    from key_generator import SecureKeyGenerator, KeyType, KeyScope
    from key_store import SecureKeyStore
    from cryptography.fernet import Fernet
    
    encryption_key = Fernet.generate_key()
    
    generator = SecureKeyGenerator()
    store = SecureKeyStore(storage_backend="local", encryption_key=encryption_key)
    
    # Create and use a key
    test_key = generator.generate_api_key(
        key_type=KeyType.API_TOKEN,
        key_scope=KeyScope.READ
    )
    store.store_key(test_key)
    store.retrieve_key(test_key.key_id)
    store.verify_key(test_key.key_id)
    
    # Check audit log
    audit_events = store.get_audit_log(limit=100)
    
    assert len(audit_events) > 0, "No audit events recorded"
    print(f"  ✅ Audit log: {len(audit_events)} events recorded")
    
    # Verify event types
    event_types = [event.action for event in audit_events[-5:]]
    assert "key_created" in event_types or any(e.action == "key_created" for e in audit_events)
    print(f"  ✅ Audit events: {', '.join(set(event_types))}")


def test_file_operations():
    """Test file system operations"""
    print("Testing file operations...")
    
    import json
    from pathlib import Path
    
    storage_dir = Path("./storage")
    
    # Check if storage directory is created
    if storage_dir.exists():
        print("  ✅ Storage directory exists")
    else:
        print("  ⚠️  Storage directory not yet created (will be created on first use)")
    
    # Test JSON serialization
    test_data = {"key": "value", "number": 123}
    json_str = json.dumps(test_data)
    parsed_data = json.loads(json_str)
    assert parsed_data == test_data
    print("  ✅ JSON serialization/deserialization")


def print_summary():
    """Print test summary"""
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {total_tests - passed_tests} ❌")
    print(f"Success Rate: {(passed_tests / max(total_tests, 1) * 100):.1f}%")
    
    if test_results:
        print("\n" + "=" * 60)
        print("  DETAILED RESULTS")
        print("=" * 60)
        
        for name, status, error in test_results:
            status_symbol = "✅" if status == "PASS" else "❌"
            print(f"\n{status_symbol} {name}")
            if error:
                print(f"   Error: {error}")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("  RECOMMENDATIONS")
    print("=" * 60)
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! The system is ready to use.")
        print("\nNext steps:")
        print("  1. Review the README.md for configuration options")
        print("  2. Run example_usage.py to see the system in action")
        print("  3. Set up Supabase for production storage")
        print("  4. Configure environment variables")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        print("\nCommon issues:")
        print("  1. Missing dependencies: Run 'pip install -r requirements.txt'")
        print("  2. Python version: Ensure Python 3.9+ is installed")
        print("  3. Import errors: Check that all files are in the correct location")
    
    print("\nFor detailed documentation, see:")
    print("  docs/key_management_implementation.md")


def main():
    """Run all tests"""
    print("=" * 60)
    print("  KEY MANAGEMENT SYSTEM - INSTALLATION TEST")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    test("Python Version", test_python_version)
    test("Dependencies", test_dependencies)
    test("Module Imports", test_imports)
    test("Key Generation", test_key_generation)
    test("Key Storage", test_key_storage)
    test("Key Rotation", test_key_rotation)
    test("Key Derivation", test_key_derivation)
    test("Key Integrity", test_key_integrity)
    test("Audit Logging", test_audit_logging)
    test("File Operations", test_file_operations)
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if passed_tests == total_tests else 1)


if __name__ == "__main__":
    main()
