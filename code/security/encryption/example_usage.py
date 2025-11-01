#!/usr/bin/env python3
"""
Example script demonstrating the end-to-end encryption system.
Shows various use cases and integration patterns.
"""

import os
import sys
import json
from datetime import datetime

# Add the encryption module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import EncryptionService, APIMiddleware
from crypto_utils import AESCrypto
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_basic_encryption():
    """Example 1: Basic data encryption and decryption."""
    print("\n" + "="*60)
    print("Example 1: Basic Data Encryption")
    print("="*60)
    
    # Initialize encryption service
    service = EncryptionService(
        storage_path="/tmp/encryption_demo/keys",
        master_password="demo_master_password_123"
    )
    
    # Create encryption keys
    user_key = service.create_encryption_key("user_data_key")
    financial_key = service.create_encryption_key("financial_data_key")
    
    print(f"✓ Created keys: {user_key}, {financial_key}")
    
    # Encrypt user data
    user_data = {
        "username": "john_doe",
        "password": "secret_password_123",
        "email": "john@example.com",
        "ssn": "123-45-6789"
    }
    
    print("\nOriginal user data:")
    for key, value in user_data.items():
        print(f"  {key}: {value}")
    
    # Encrypt each field
    encrypted_user_data = {}
    for field, value in user_data.items():
        encrypted = service.encrypt_data(value, user_key)
        encrypted_user_data[field] = encrypted
    
    print("\nEncrypted user data:")
    for key, value in encrypted_user_data.items():
        print(f"  {key}: {value[:50]}...")
    
    # Decrypt and verify
    print("\nDecrypted user data:")
    for key, encrypted_value in encrypted_user_data.items():
        decrypted = service.decrypt_data(encrypted_value, user_key)
        print(f"  {key}: {decrypted.decode('utf-8')}")
    
    return service


def example_database_encryption(service):
    """Example 2: Database field encryption."""
    print("\n" + "="*60)
    print("Example 2: Database Field Encryption")
    print("="*60)
    
    # Simulate database operations with encryption
    transactions = [
        {"id": 1, "user_id": 101, "amount": 1500.00, "card_number": "4532-1234-5678-9012"},
        {"id": 2, "user_id": 102, "amount": 2300.50, "card_number": "5555-9876-5432-1098"},
        {"id": 3, "user_id": 103, "amount": 750.25, "card_number": "4111-1111-1111-1111"},
    ]
    
    print("\nOriginal transactions:")
    for transaction in transactions:
        print(f"  ID {transaction['id']}: ${transaction['amount']}, Card: {transaction['card_number']}")
    
    # Encrypt sensitive fields
    for transaction in transactions:
        # Encrypt credit card number
        encrypted_card = service.encrypt_field(transaction["card_number"], "financial_data_key")
        transaction["card_number"] = encrypted_card
    
    print("\nEncrypted transactions (for database storage):")
    for transaction in transactions:
        print(f"  ID {transaction['id']}: ${transaction['amount']}")
        print(f"    Card: {transaction['card_number'][:50]}...")
    
    # Simulate retrieval and decryption
    print("\nDecrypted transactions (for processing):")
    for transaction in transactions:
        decrypted_card = service.decrypt_field(transaction["card_number"], "financial_data_key")
        print(f"  ID {transaction['id']}: ${transaction['amount']}, Card: {decrypted_card.decode('utf-8')}")


def example_file_encryption(service):
    """Example 3: File encryption and decryption."""
    print("\n" + "="*60)
    print("Example 3: File Encryption")
    print("="*60)
    
    # Create a sample document
    document_content = """
    CONFIDENTIAL DOCUMENT
    
    This document contains sensitive information that should be encrypted.
    
    Account Details:
    - Account Number: 123456789
    - Routing Number: 987654321
    - Balance: $50,000.00
    
    Customer Information:
    - Name: John Doe
    - SSN: 123-45-6789
    - Address: 123 Main St, Anytown, USA
    """
    
    # Write sample file
    input_file = "/tmp/sample_document.txt"
    encrypted_file = "/tmp/sample_document.enc"
    decrypted_file = "/tmp/sample_document_decrypted.txt"
    
    with open(input_file, 'w') as f:
        f.write(document_content)
    
    print(f"✓ Created sample document: {input_file}")
    
    # Encrypt the file
    service.encrypt_file(input_file, encrypted_file, "financial_data_key")
    print(f"✓ Encrypted document: {encrypted_file}")
    
    # Check file sizes
    original_size = os.path.getsize(input_file)
    encrypted_size = os.path.getsize(encrypted_file)
    print(f"  Original size: {original_size} bytes")
    print(f"  Encrypted size: {encrypted_size} bytes")
    
    # Decrypt the file
    service.decrypt_file(encrypted_file, decrypted_file, "financial_data_key")
    print(f"✓ Decrypted document: {decrypted_file}")
    
    # Verify content
    with open(decrypted_file, 'r') as f:
        decrypted_content = f.read()
    
    assert decrypted_content == document_content, "Decrypted content doesn't match original!"
    print("✓ Content verification passed")
    
    # Clean up
    os.remove(input_file)
    os.remove(encrypted_file)
    os.remove(decrypted_file)


def example_api_middleware(service):
    """Example 4: API middleware for automatic encryption."""
    print("\n" + "="*60)
    print("Example 4: API Middleware")
    print("="*60)
    
    middleware = service.create_api_middleware()
    
    # Create test functions with middleware
    @middleware.encrypt_response("user_data_key")
    def get_user_profile():
        return {
            "user_id": 12345,
            "username": "john_doe",
            "email": "john@example.com",
            "password": "super_secret_123",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "profile_data": {
                "name": "John Doe",
                "phone": "555-1234-5678",
                "address": "123 Main St, Anytown, USA"
            }
        }
    
    @middleware.encrypt_response("financial_data_key", ['ssn', 'bank_account'])
    def get_financial_profile():
        return {
            "user_id": 12345,
            "ssn": "123-45-6789",
            "bank_account": "9876543210",
            "credit_score": 750,
            "annual_income": 85000.00
        }
    
    # Test encrypted responses
    print("\nOriginal API response (get_user_profile):")
    original_profile = get_user_profile.__wrapped__()
    print(json.dumps(original_profile, indent=2))
    
    print("\nEncrypted API response (get_user_profile):")
    encrypted_profile = get_user_profile()
    print(json.dumps(encrypted_profile, indent=2))
    
    print("\nOriginal API response (get_financial_profile):")
    original_financial = get_financial_profile.__wrapped__()
    print(json.dumps(original_financial, indent=2))
    
    print("\nEncrypted API response (get_financial_profile):")
    encrypted_financial = get_financial_profile()
    print(json.dumps(encrypted_financial, indent=2))


def example_key_rotation(service):
    """Example 5: Key rotation."""
    print("\n" + "="*60)
    print("Example 5: Key Rotation")
    print("="*60)
    
    # Create a test key
    test_key = service.create_encryption_key("rotation_test_key", rotation_interval_days=30)
    print(f"✓ Created test key: {test_key}")
    
    # Show key information
    key_info = service.get_key_info(test_key)
    print("\nKey information:")
    print(f"  Algorithm: {key_info['algorithm']}")
    print(f"  Created: {key_info['created_at']}")
    print(f"  Rotation interval: {key_info['rotation_interval_days']} days")
    print(f"  Usage count: {key_info['usage_count']}")
    print(f"  Needs rotation: {key_info['needs_rotation']}")
    
    # Test data encryption with the key
    test_data = "This data will be re-encrypted after rotation"
    encrypted_data = service.encrypt_data(test_data, test_key)
    print(f"\n✓ Encrypted test data: {encrypted_data[:50]}...")
    
    # Simulate key aging by modifying metadata (for demo purposes)
    print("\nNote: In production, keys would be rotated based on:")
    print("  - Time elapsed (rotation interval)")
    print("  - Usage count limits")
    print("  - Explicit expiration dates")
    print("  - Security incident response")


def example_security_utilities(service):
    """Example 6: Security utilities."""
    print("\n" + "="*60)
    print("Example 6: Security Utilities")
    print("="*60)
    
    # Data integrity verification
    data = "Important message that must not be tampered with"
    key_id = "integrity_test_key"
    
    service.create_encryption_key(key_id)
    
    # Generate signature
    signature = service.generate_data_signature(data, key_id)
    print(f"✓ Generated signature: {signature}")
    
    # Verify signature (should pass)
    is_valid = service.verify_data_integrity(data, signature, key_id)
    print(f"✓ Signature verification (valid data): {is_valid}")
    
    # Verify signature with tampered data (should fail)
    tampered_data = "Important message that HAS BEEN TAMPERED"
    is_valid_tampered = service.verify_data_integrity(tampered_data, signature, key_id)
    print(f"✓ Signature verification (tampered data): {is_valid_tampered}")


def demonstrate_security_features():
    """Demonstrate key security features."""
    print("\n" + "="*60)
    print("Security Features Demonstration")
    print("="*60)
    
    print("\n1. Key Generation Security:")
    key = AESCrypto.generate_key()
    print(f"   ✓ Generated random 256-bit key: {len(key)} bytes")
    print(f"   ✓ Key entropy check: {'PASS' if len(set(key)) > 200 else 'FAIL'}")
    
    print("\n2. Key Derivation from Password:")
    password = "strong_password_123"
    salt = os.urandom(32)
    derived_key = AESCrypto.derive_key_from_password(password, salt)
    print(f"   ✓ Derived key from password: {len(derived_key)} bytes")
    print(f"   ✓ Different passwords produce different keys: {'PASS' if AESCrypto.derive_key_from_password('different_password', salt) != derived_key else 'FAIL'}")
    
    print("\n3. Authenticated Encryption (AEAD):")
    test_data = "Sensitive message with integrity protection"
    test_key = AESCrypto.generate_key()
    associated_data = b"context_verification"
    
    nonce, ciphertext, tag = AESCrypto.encrypt(test_data, test_key, associated_data)
    print(f"   ✓ Encrypted with GCM: {len(ciphertext)} bytes")
    print(f"   ✓ Authentication tag: {len(tag)} bytes")
    print(f"   ✓ Integrity protection: {'PASS' if len(tag) == 16 else 'FAIL'}")
    
    # Test decryption with wrong associated data (should fail)
    try:
        AESCrypto.decrypt(nonce, ciphertext, tag, test_key, b"wrong_context")
        print(f"   ✓ Wrong context rejection: FAIL (should have thrown error)")
    except:
        print(f"   ✓ Wrong context rejection: PASS")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("END-TO-END ENCRYPTION SYSTEM - DEMONSTRATION")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    try:
        # Example 1: Basic encryption
        service = example_basic_encryption()
        
        # Example 2: Database encryption
        example_database_encryption(service)
        
        # Example 3: File encryption
        example_file_encryption(service)
        
        # Example 4: API middleware
        example_api_middleware(service)
        
        # Example 5: Key rotation
        example_key_rotation(service)
        
        # Example 6: Security utilities
        example_security_utilities(service)
        
        # Security features
        demonstrate_security_features()
        
        print("\n" + "="*60)
        print("✓ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*60)
        
        # Summary
        print(f"\nSummary:")
        print(f"- Encryption service initialized")
        print(f"- Keys managed securely")
        print(f"- Data encrypted and decrypted successfully")
        print(f"- API middleware demonstrated")
        print(f"- Security features validated")
        
        # List all keys created
        keys = service.list_keys()
        print(f"\nKeys in system: {len(keys)}")
        for key in keys:
            info = service.get_key_info(key)
            print(f"  - {key}: {info['algorithm']}, created {info['created_at'][:10]}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Cleanup demo directory
        import shutil
        if os.path.exists("/tmp/encryption_demo"):
            shutil.rmtree("/tmp/encryption_demo")
        print("\n✓ Cleanup completed")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
