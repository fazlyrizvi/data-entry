#!/usr/bin/env python3
"""
Example usage of the Secure API Key Management System

This script demonstrates how to use the key management system
for generating, storing, rotating, and monitoring API keys.
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta

# Add the current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from key_generator import (
    SecureKeyGenerator,
    KeyType,
    KeyScope,
    KeyLength,
    GeneratedKey
)
from key_store import SecureKeyStore, KeyMetadata
from key_rotator import (
    KeyRotator,
    RotationPolicy,
    RotationFrequency,
    RotationStrategy
)


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_key_info(key: GeneratedKey, title: str = "Key Information"):
    """Print formatted key information"""
    print(f"{title}:")
    print(f"  ID: {key.key_id}")
    print(f"  Type: {key.key_type}")
    print(f"  Scope: {key.scope}")
    print(f"  Algorithm: {key.algorithm}")
    print(f"  Value: {key.key_value[:50]}...")
    if key.expires_at:
        expiry = datetime.fromtimestamp(key.expires_at)
        print(f"  Expires: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def notification_handler(notification_type: str, data: dict):
    """Example notification handler for rotation events"""
    print(f"\n🔔 NOTIFICATION: {notification_type}")
    print(f"   Data: {json.dumps(data, indent=2)}\n")


def example_basic_usage():
    """Example 1: Basic key generation and storage"""
    print_section("Example 1: Basic Key Generation and Storage")

    # Generate encryption key (in production, use environment variable)
    from cryptography.fernet import Fernet
    encryption_key = Fernet.generate_key()
    
    # Initialize components
    generator = SecureKeyGenerator(hsm_enabled=False)
    store = SecureKeyStore(
        storage_backend="local",
        encryption_key=encryption_key
    )

    # Generate an API key
    api_key = generator.generate_api_key(
        key_type=KeyType.API_TOKEN,
        key_scope=KeyScope.READ_WRITE,
        expires_in=86400 * 30,  # 30 days
        metadata={
            "environment": "production",
            "application": "web_app",
            "created_by": "example_script"
        }
    )

    print("Generated API Key:")
    print_key_info(api_key)

    # Store the key
    print("Storing key in secure storage...")
    success = store.store_key(api_key)
    if success:
        print("✅ Key stored successfully")
    else:
        print("❌ Failed to store key")
        return

    # Retrieve the key
    print("Retrieving key from storage...")
    retrieved_key = store.retrieve_key(api_key.key_id)
    if retrieved_key:
        print("✅ Key retrieved successfully")
        print_key_info(retrieved_key, "Retrieved Key")
    else:
        print("❌ Failed to retrieve key")
        return

    # Verify the key
    print("Verifying key...")
    is_valid, message = store.verify_key(api_key.key_id)
    print(f"✅ Key verification: {is_valid} - {message}")


def example_rotation_policies():
    """Example 2: Setting up rotation policies"""
    print_section("Example 2: Key Rotation Policies")

    from cryptography.fernet import Fernet
    encryption_key = Fernet.generate_key()
    
    generator = SecureKeyGenerator()
    store = SecureKeyStore(storage_backend="local", encryption_key=encryption_key)
    rotator = KeyRotator(generator, store, notification_handler)

    # Create multiple keys for different services
    services = [
        ("user_service", KeyScope.READ_WRITE),
        ("payment_service", KeyScope.ADMIN),
        ("notification_service", KeyScope.WRITE),
        ("analytics_service", KeyScope.READ)
    ]

    service_keys = []
    for service_name, scope in services:
        key = generator.generate_api_key(
            key_type=KeyType.API_TOKEN,
            key_scope=scope,
            expires_in=86400 * 60,  # 60 days
            metadata={
                "service": service_name,
                "environment": "production"
            }
        )
        store.store_key(key)
        service_keys.append((service_name, key))
        print(f"Created key for {service_name}: {key.key_id}")

    # Create rotation policies
    print("\nCreating rotation policies...")

    # High-security weekly rotation
    policy1 = RotationPolicy(
        policy_id="high_security_weekly",
        name="High Security Weekly Rotation",
        key_type=KeyType.API_TOKEN,
        scope=KeyScope.ADMIN,
        frequency=RotationFrequency.WEEKLY,
        strategy=RotationStrategy.OVERLAPPING,
        advance_notice_hours=24,
        overlap_duration_hours=48
    )
    rotator.create_rotation_policy(policy1)
    print(f"✅ Created policy: {policy1.name}")

    # Standard monthly rotation
    policy2 = RotationPolicy(
        policy_id="standard_monthly",
        name="Standard Monthly Rotation",
        key_type=KeyType.API_TOKEN,
        scope=KeyScope.READ_WRITE,
        frequency=RotationFrequency.MONTHLY,
        strategy=RotationStrategy.GRADUAL,
        advance_notice_hours=48,
        overlap_duration_hours=72
    )
    rotator.create_rotation_policy(policy2)
    print(f"✅ Created policy: {policy2.name}")

    # Manually rotate one key
    print(f"\nManually rotating key for {service_keys[0][0]}...")
    _, first_key = service_keys[0]
    rotated_key = rotator.rotate_key(
        first_key.key_id,
        rotation_type="manual",
        strategy=RotationStrategy.IMMEDIATE
    )

    if rotated_key:
        print_key_info(rotated_key, "Rotated Key")
    else:
        print("❌ Rotation failed")


def example_monitoring():
    """Example 3: Monitoring and audit"""
    print_section("Example 3: Monitoring and Audit")

    from cryptography.fernet import Fernet
    encryption_key = Fernet.generate_key()
    
    generator = SecureKeyGenerator()
    store = SecureKeyStore(storage_backend="local", encryption_key=encryption_key)

    # Generate and use some keys
    keys = []
    for i in range(5):
        key = generator.generate_api_key(
            key_type=KeyType.API_TOKEN,
            key_scope=KeyScope.READ_WRITE,
            metadata={"test_key": f"key_{i}"}
        )
        store.store_key(key)
        keys.append(key)

    # Simulate usage by retrieving keys multiple times
    print("Simulating key usage...")
    for key in keys[:3]:
        # Retrieve key (logs usage)
        retrieved = store.retrieve_key(key.key_id)
        # Verify key (logs verification)
        is_valid, _ = store.verify_key(key.key_id)
        print(f"Used {key.key_id}: valid={is_valid}")

    # Get all stored keys
    print("\nStored keys:")
    all_keys = store.list_keys()
    for key_metadata in all_keys:
        print(f"  - {key_metadata.key_id}")
        print(f"    Type: {key_metadata.key_type}")
        print(f"    Scope: {key_metadata.scope}")
        print(f"    Usage count: {key_metadata.usage_count}")
        print(f"    Active: {key_metadata.is_active}")
        if key_metadata.last_used:
            last_used = datetime.fromtimestamp(key_metadata.last_used)
            print(f"    Last used: {last_used.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    # Get audit log
    print("Recent audit events:")
    audit_events = store.get_audit_log(limit=20)
    for event in audit_events[-10:]:  # Last 10 events
        timestamp = datetime.fromtimestamp(event.timestamp)
        status = "✅" if event.success else "❌"
        print(f"  {status} {event.action} - {timestamp.strftime('%H:%M:%S')} - {event.key_id}")
        if event.error_message:
            print(f"      Error: {event.error_message}")


def example_supabase_format():
    """Example 4: Exporting keys for Supabase"""
    print_section("Example 4: Exporting Keys for Supabase")

    from cryptography.fernet import Fernet
    encryption_key = Fernet.generate_key()
    
    generator = SecureKeyGenerator()
    store = SecureKeyStore(storage_backend="local", encryption_key=encryption_key)

    # Generate a provisioning key
    prov_key = generator.generate_api_key(
        key_type=KeyType.PROVISIONING,
        key_scope=KeyScope.FULL,
        expires_in=86400 * 365,  # 1 year
        metadata={
            "environment": "production",
            "purpose": "service_provisioning",
            "owner": "devops_team"
        }
    )

    store.store_key(prov_key)

    # Export for Supabase edge function
    supabase_format = generator.export_key_for_supabase(prov_key)
    print("Key exported in Supabase-compatible format:")
    print(json.dumps(supabase_format, indent=2))

    # Save to file
    output_file = "/workspace/code/security/key_management/supabase_key_export.json"
    with open(output_file, 'w') as f:
        json.dump(supabase_format, f, indent=2)
    print(f"\n✅ Exported to: {output_file}")


def example_batch_operations():
    """Example 5: Batch key generation"""
    print_section("Example 5: Batch Key Generation")

    from cryptography.fernet import Fernet
    encryption_key = Fernet.generate_key()
    
    generator = SecureKeyGenerator()
    store = SecureKeyStore(storage_backend="local", encryption_key=encryption_key)

    # Generate a batch of development keys
    print("Generating batch of 10 development API keys...")
    dev_keys = generator.generate_key_batch(
        count=10,
        key_type=KeyType.API_TOKEN,
        key_scope=KeyScope.READ,
        key_length=KeyLength.SHORT,
        expires_in=86400 * 7,  # 7 days
        metadata={
            "environment": "development",
            "batch_id": "dev_batch_001"
        }
    )

    print(f"Generated {len(dev_keys)} keys")
    
    # Store all keys
    stored_count = 0
    for key in dev_keys:
        if store.store_key(key):
            stored_count += 1

    print(f"✅ Stored {stored_count} keys")

    # List all development keys
    dev_metadata = store.list_keys(
        key_type=KeyType.API_TOKEN,
        active_only=True
    )

    print(f"\nActive API keys: {len(dev_metadata)}")
    for i, key_meta in enumerate(dev_metadata[:5], 1):  # Show first 5
        print(f"  {i}. {key_meta.key_id}")
        print(f"     Scope: {key_meta.scope}, Usage: {key_meta.usage_count}")


def example_security_features():
    """Example 6: Security features demonstration"""
    print_section("Example 6: Security Features")

    from cryptography.fernet import Fernet
    encryption_key = Fernet.generate_key()
    
    generator = SecureKeyGenerator()
    store = SecureKeyStore(storage_backend="local", encryption_key=encryption_key)

    # Generate different types of keys
    key_types = [
        (KeyType.HMAC, "HMAC Key"),
        (KeyType.RSA, "RSA Key Pair"),
        (KeyType.ECDSA, "ECDSA Key Pair"),
        (KeyType.JWT, "JWT Signing Key"),
        (KeyType.API_TOKEN, "API Token")
    ]

    security_keys = []
    for key_type, description in key_types:
        key = generator.generate_api_key(
            key_type=key_type,
            key_scope=KeyScope.ADMIN,
            metadata={"security_test": True, "description": description}
        )
        store.store_key(key)
        security_keys.append(key)
        print(f"✅ Generated {description}: {key.key_id}")

    # Test key integrity verification
    print("\nTesting key integrity...")
    for key in security_keys:
        is_valid = generator.verify_key_integrity(key)
        status = "✅" if is_valid else "❌"
        print(f"  {status} {key.key_type}: integrity {'valid' if is_valid else 'invalid'}")

    # Test rate limiting
    print("\nTesting rate limiting...")
    test_key = security_keys[0]
    print(f"  Using key: {test_key.key_id}")
    
    # Simulate multiple requests
    for i in range(5):
        is_valid, message = store.verify_key(test_key.key_id)
        rate_limited = "Rate limit" in message
        print(f"    Request {i+1}: {'⚠️  Rate limited' if rate_limited else '✅ Allowed'}")


def example_cleanup():
    """Example 7: Cleanup and maintenance"""
    print_section("Example 7: Cleanup and Maintenance")

    from cryptography.fernet import Fernet
    encryption_key = Fernet.generate_key()
    
    generator = SecureKeyGenerator()
    store = SecureKeyStore(storage_backend="local", encryption_key=encryption_key)

    # Create some test keys with different ages
    print("Creating test keys for cleanup demonstration...")

    # Create a key and manually set it as expired
    expired_key = generator.generate_api_key(
        key_type=KeyType.API_TOKEN,
        key_scope=KeyScope.READ,
        expires_in=-86400  # Already expired
    )
    store.store_key(expired_key)

    # Create active keys
    for i in range(3):
        key = generator.generate_api_key(
            key_type=KeyType.API_TOKEN,
            key_scope=KeyScope.READ
        )
        store.store_key(key)

    # Show statistics before cleanup
    all_keys = store.list_keys(active_only=False)
    active_keys = [k for k in all_keys if k.is_active]
    expired_keys = [k for k in all_keys if k.expires_at and k.expires_at < time.time()]

    print(f"\nBefore cleanup:")
    print(f"  Total keys: {len(all_keys)}")
    print(f"  Active keys: {len(active_keys)}")
    print(f"  Expired keys: {len(expired_keys)}")

    # Perform cleanup
    cleaned_count = store.cleanup_expired_keys()
    print(f"\n🧹 Cleaned up {cleaned_count} expired keys")

    # Show statistics after cleanup
    all_keys_after = store.list_keys(active_only=False)
    active_keys_after = [k for k in all_keys_after if k.is_active]

    print(f"\nAfter cleanup:")
    print(f"  Total keys: {len(all_keys_after)}")
    print(f"  Active keys: {len(active_keys_after)}")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("  Secure API Key Management System - Examples")
    print("=" * 60)

    examples = [
        ("Basic Usage", example_basic_usage),
        ("Rotation Policies", example_rotation_policies),
        ("Monitoring & Audit", example_monitoring),
        ("Supabase Export", example_supabase_format),
        ("Batch Operations", example_batch_operations),
        ("Security Features", example_security_features),
        ("Cleanup & Maintenance", example_cleanup)
    ]

    for name, example_func in examples:
        try:
            example_func()
            print(f"\n✅ Example '{name}' completed successfully")
        except Exception as e:
            print(f"\n❌ Example '{name}' failed with error: {e}")
            import traceback
            traceback.print_exc()

    print_section("All Examples Completed")
    print("Review the output above to see how the key management system works.")
    print("\nFor production use:")
    print("  1. Set proper environment variables")
    print("  2. Use HSM for key generation/storage")
    print("  3. Configure Supabase backend")
    print("  4. Set up monitoring and alerting")
    print("  5. Implement proper access controls")


if __name__ == "__main__":
    main()
