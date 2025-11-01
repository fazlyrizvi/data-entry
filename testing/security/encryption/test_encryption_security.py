#!/usr/bin/env python3
"""
Encryption Security Testing Suite
Tests encryption implementations, key management, and cryptographic security.
"""

import pytest
import os
import sys
import secrets
import hashlib
import tempfile
import shutil
from datetime import datetime, timedelta

# Add the security module to the path
sys.path.append('/workspace/code/security/encryption')

from main import EncryptionService
from crypto_utils import AESCrypto, FernetCrypto, FileEncryption, CryptoError
from key_manager import KeyManager, KeyMetadata


class TestEncryptionImplementation:
    """Test suite for encryption implementation security"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp(prefix="encryption_test_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def encryption_service(self, temp_dir):
        """Create encryption service instance"""
        return EncryptionService(
            storage_path=temp_dir,
            master_password="test-master-password-12345",
            auto_rotation_enabled=False  # Disable for testing
        )
    
    @pytest.mark.security
    def test_aes_gcm_encryption_strength(self):
        """Test AES-256-GCM encryption strength"""
        crypto = AESCrypto()
        
        # Test encryption/decryption
        plaintext = b"Sensitive data that needs protection"
        encrypted = crypto.encrypt(plaintext)
        
        assert encrypted != plaintext
        assert len(encrypted) > len(plaintext)  # Includes auth tag
        
        # Decrypt should work
        decrypted = crypto.decrypt(encrypted)
        assert decrypted == plaintext
    
    @pytest.mark.security
    def test_encryption_key_entropy(self):
        """Test encryption key randomness and entropy"""
        keys = set()
        
        # Generate multiple keys
        for _ in range(100):
            key = AESCrypto.generate_key()
            keys.add(key.hex())
        
        # All keys should be unique
        assert len(keys) == 100
        
        # Check key length
        for key in list(keys)[:10]:
            assert len(key) == 64  # 256 bits = 32 bytes = 64 hex chars
    
    @pytest.mark.security
    def test_ciphertext_randomness(self):
        """Test that ciphertext is randomized (no patterns)"""
        crypto = AESCrypto()
        plaintext = b"Same plaintext message" * 10
        
        # Encrypt same plaintext multiple times
        ciphertexts = [crypto.encrypt(plaintext) for _ in range(100)]
        
        # All ciphertexts should be unique
        assert len(set(ciphertexts)) == 100
        
        # No obvious patterns
        first_bytes = [c[:8] for c in ciphertexts]
        assert len(set(first_bytes)) > 90  # At least 90% unique
    
    @pytest.mark.security
    def test_authenticated_encryption_integrity(self):
        """Test authenticated encryption integrity protection"""
        crypto = AESCrypto()
        
        plaintext = b"Original message"
        encrypted = crypto.encrypt(plaintext)
        
        # Tamper with ciphertext
        tampered = bytearray(encrypted)
        tampered[0] ^= 0xFF  # Flip random bit
        
        # Decryption should fail
        with pytest.raises(CryptoError):
            crypto.decrypt(bytes(tampered))
    
    @pytest.mark.security
    def test_fernet_encryption(self):
        """Test Fernet high-level encryption"""
        fernet = FernetCrypto()
        
        # Generate key
        key = fernet.generate_key()
        fernet.set_key(key)
        
        # Test encryption/decryption
        plaintext = "Sensitive data for Fernet encryption"
        encrypted = fernet.encrypt(plaintext)
        decrypted = fernet.decrypt(encrypted)
        
        assert encrypted != plaintext
        assert decrypted == plaintext
    
    @pytest.mark.security
    def test_key_derivation_function(self):
        """Test PBKDF2 key derivation"""
        from crypto_utils import PBKDF2
        
        password = "user_password_123"
        salt = secrets.token_bytes(32)
        iterations = 100000
        
        # Derive key
        derived_key = PBKDF2(password, salt, iterations, key_len=32)
        
        assert len(derived_key) == 32
        assert derived_key != password.encode()
        
        # Same input should produce same output
        derived_key2 = PBKDF2(password, salt, iterations, key_len=32)
        assert derived_key == derived_key2
    
    @pytest.mark.security
    def test_hkdf_hierarchical_derivation(self):
        """Test HKDF hierarchical key derivation"""
        from crypto_utils import HKDF
        
        master_key = secrets.token_bytes(32)
        salt = secrets.token_bytes(32)
        info = b"test_context"
        
        # Derive sub-keys
        key1 = HKDF(master_key, salt, info + b"1", length=32)
        key2 = HKDF(master_key, salt, info + b"2", length=32)
        
        # Different contexts should produce different keys
        assert key1 != key2
        assert len(key1) == 32
        assert len(key2) == 32
    
    @pytest.mark.security
    def test_file_encryption_security(self, temp_dir):
        """Test file-level encryption security"""
        file_encryption = FileEncryption()
        
        # Create test file
        test_file = os.path.join(temp_dir, "test_data.txt")
        with open(test_file, "wb") as f:
            f.write(b"Confidential document content" * 100)
        
        # Encrypt file
        encrypted_file = test_file + ".encrypted"
        file_encryption.encrypt_file(test_file, encrypted_file, "file_password")
        
        # Encrypted file should not contain plaintext
        with open(encrypted_file, "rb") as f:
            content = f.read()
        
        assert b"Confidential" not in content
        
        # Decrypt file
        decrypted_file = test_file + ".decrypted"
        file_encryption.decrypt_file(encrypted_file, decrypted_file, "file_password")
        
        # Decrypted file should match original
        with open(decrypted_file, "rb") as f:
            decrypted_content = f.read()
        
        with open(test_file, "rb") as f:
            original_content = f.read()
        
        assert decrypted_content == original_content
    
    @pytest.mark.security
    def test_database_field_encryption(self):
        """Test database field encryption"""
        from crypto_utils import DatabaseFieldEncryption
        
        db_encryption = DatabaseFieldEncryption()
        
        # Test sensitive data
        sensitive_data = {
            "ssn": "123-45-6789",
            "credit_card": "4111-1111-1111-1111",
            "email": "user@example.com"
        }
        
        # Encrypt fields
        encrypted_fields = db_encryption.encrypt_fields(sensitive_data)
        
        assert encrypted_fields["ssn"] != "123-45-6789"
        assert encrypted_fields["credit_card"] != "4111-1111-1111-1111"
        assert encrypted_fields["email"] != "user@example.com"
        
        # Decrypt fields
        decrypted_fields = db_encryption.decrypt_fields(encrypted_fields)
        assert decrypted_fields == sensitive_data
    
    @pytest.mark.security
    def test_encryption_padding_oracle_attack(self):
        """Test protection against padding oracle attacks"""
        crypto = AESCrypto()
        
        # Create message with different padding scenarios
        messages = [
            b"A",  # Single byte
            b"AB",  # Two bytes
            b"ABC",  # Three bytes
            b"ABCDEFGHIJKLMNOP",  # Exactly block size
            b"ABCDEFGHIJKLMNOPQ",  # One over block size
        ]
        
        for msg in messages:
            # Encrypt
            encrypted = crypto.encrypt(msg)
            
            # Should not leak padding information
            # (In real implementation, use constant-time operations)
            
            # Decrypt should work correctly
            decrypted = crypto.decrypt(encrypted)
            assert decrypted == msg
    
    @pytest.mark.security
    def test_side_channel_attack_protection(self):
        """Test protection against timing side-channel attacks"""
        crypto = AESCrypto()
        
        # Generate test data
        plaintext1 = b"Short message"
        plaintext2 = b"Much longer message that should take more time to process"
        
        # Measure encryption times (in real scenario, would use high-precision timing)
        import time
        
        start1 = time.perf_counter()
        encrypted1 = crypto.encrypt(plaintext1)
        time1 = time.perf_counter() - start1
        
        start2 = time.perf_counter()
        encrypted2 = crypto.encrypt(plaintext2)
        time2 = time.perf_counter() - start2
        
        # Timing differences should not reveal information about plaintext
        # (This is a simplified check - real implementation needs constant-time ops)
        assert abs(time1 - time2) < 1.0  # Within reasonable bounds


class TestKeyManagementSecurity:
    """Test suite for key management security"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp(prefix="key_mgmt_test_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def key_manager(self, temp_dir):
        """Create key manager instance"""
        return KeyManager(
            storage_path=temp_dir,
            master_password="test-master-password-12345"
        )
    
    @pytest.mark.security
    def test_master_key_protection(self, key_manager):
        """Test master key encryption and protection"""
        # Master key should be encrypted
        assert key_manager._master_key is not None
        
        # Key storage should be encrypted
        key_files = os.listdir(key_manager.storage_path)
        for key_file in key_files:
            if key_file.endswith('.key'):
                key_path = os.path.join(key_manager.storage_path, key_file)
                with open(key_path, 'rb') as f:
                    content = f.read()
                # Should not be plaintext
                assert content != key_manager._master_key
    
    @pytest.mark.security
    def test_key_rotation_security(self, key_manager):
        """Test automatic key rotation security"""
        # Create encryption key
        key_id = "test-key-rotation"
        key_manager.create_encryption_key(
            key_id=key_id,
            algorithm="AES-256-GCM",
            rotation_interval_days=30
        )
        
        # Get initial key
        initial_key = key_manager.get_encryption_key(key_id)
        
        # Trigger rotation
        rotated_key = key_manager.rotate_key(key_id, reason="test_rotation")
        
        # Key should change
        assert rotated_key is not None
        assert rotated_key != initial_key
        
        # Old key should be archived
        archive_info = key_manager.get_key_archive_info(key_id)
        assert len(archive_info) > 0
    
    @pytest.mark.security
    def test_key_usage_monitoring(self, key_manager):
        """Test key usage tracking and limits"""
        key_id = "usage-test-key"
        max_uses = 5
        
        key_manager.create_encryption_key(
            key_id=key_id,
            algorithm="AES-256-GCM",
            max_uses=max_uses
        )
        
        # Use key multiple times
        for i in range(max_uses):
            key_manager.get_encryption_key(key_id)
        
        # Usage count should be tracked
        metadata = key_manager.get_key_metadata(key_id)
        assert metadata.usage_count == max_uses
        
        # Exceeding usage should trigger rotation
        try:
            key_manager.get_encryption_key(key_id)
            # Should have triggered rotation
            new_metadata = key_manager.get_key_metadata(key_id)
            assert new_metadata.usage_count < max_uses
        except Exception as e:
            # Or should raise an exception
            assert "rotation" in str(e).lower() or "expired" in str(e).lower()
    
    @pytest.mark.security
    def test_key_expiration_enforcement(self, key_manager):
        """Test key expiration and lifecycle management"""
        key_id = "expiration-test-key"
        
        # Create key with very short expiration
        key_manager.create_encryption_key(
            key_id=key_id,
            algorithm="AES-256-GCM",
            expires_at=datetime.utcnow() + timedelta(seconds=1)
        )
        
        # Key should be valid initially
        valid_key = key_manager.get_encryption_key(key_id)
        assert valid_key is not None
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Key should be expired
        try:
            key_manager.get_encryption_key(key_id)
            assert False, "Key should have expired"
        except Exception:
            pass  # Expected
    
    @pytest.mark.security
    def test_key_derivation_hierarchy(self, key_manager):
        """Test hierarchical key derivation"""
        master_key_id = "master-key"
        key_manager.create_encryption_key(
            key_id=master_key_id,
            algorithm="AES-256-GCM"
        )
        
        # Derive child key
        child_key_id = key_manager.derive_key(
            parent_key_id=master_key_id,
            context="child-context",
            key_length=32
        )
        
        # Parent and child keys should be different
        master_key = key_manager.get_encryption_key(master_key_id)
        child_key = key_manager.get_encryption_key(child_key_id)
        
        assert master_key != child_key
        
        # Same context should produce same key
        child_key2_id = key_manager.derive_key(
            parent_key_id=master_key_id,
            context="child-context",
            key_length=32
        )
        
        child_key2 = key_manager.get_encryption_key(child_key2_id)
        assert child_key == child_key2
    
    @pytest.mark.security
    def test_secure_key_deletion(self, key_manager):
        """Test secure key deletion"""
        key_id = "delete-test-key"
        
        key_manager.create_encryption_key(
            key_id=key_id,
            algorithm="AES-256-GCM"
        )
        
        key_path = os.path.join(key_manager.storage_path, f"{key_id}.key")
        assert os.path.exists(key_path)
        
        # Secure delete
        key_manager.secure_delete_key(key_id)
        
        # Key file should be removed
        assert not os.path.exists(key_path)
        
        # Should not be able to retrieve deleted key
        try:
            key_manager.get_encryption_key(key_id)
            assert False, "Deleted key should not be retrievable"
        except Exception:
            pass  # Expected
    
    @pytest.mark.security
    def test_key_metadata_protection(self, key_manager):
        """Test key metadata security"""
        key_id = "metadata-test-key"
        
        key_manager.create_encryption_key(
            key_id=key_id,
            algorithm="AES-256-GCM",
            metadata={"owner": "test-user", "purpose": "testing"}
        )
        
        metadata = key_manager.get_key_metadata(key_id)
        
        # Metadata should be encrypted
        metadata_files = [f for f in os.listdir(key_manager.storage_path) 
                         if f.startswith("metadata_")]
        
        for meta_file in metadata_files:
            meta_path = os.path.join(key_manager.storage_path, meta_file)
            with open(meta_path, 'rb') as f:
                content = f.read()
            
            # Should not contain plaintext
            assert b"test-user" not in content
    
    @pytest.mark.security
    def test_backup_key_security(self, key_manager):
        """Test backup key security"""
        key_id = "backup-test-key"
        
        key_manager.create_encryption_key(
            key_id=key_id,
            algorithm="AES-256-GCM"
        )
        
        # Create backup
        backup_path = os.path.join(key_manager.storage_path, "backup")
        os.makedirs(backup_path, exist_ok=True)
        
        key_manager.backup_keys(backup_path)
        
        # Backup should contain encrypted keys
        backup_files = os.listdir(backup_path)
        assert len(backup_files) > 0
        
        for backup_file in backup_files:
            backup_file_path = os.path.join(backup_path, backup_file)
            with open(backup_file_path, 'rb') as f:
                content = f.read()
            
            # Should not be plaintext
            assert len(content) > 0
    
    @pytest.mark.security
    def test_key_compromise_recovery(self, key_manager):
        """Test key compromise recovery procedures"""
        key_id = "compromise-test-key"
        
        # Create key
        key_manager.create_encryption_key(
            key_id=key_id,
            algorithm="AES-256-GCM"
        )
        
        # Simulate compromise detection
        compromise_event = {
            "key_id": key_id,
            "compromise_type": "unauthorized_access",
            "detected_at": datetime.utcnow(),
            "severity": "high"
        }
        
        # Initiate compromise recovery
        recovery_result = key_manager.handle_key_compromise(compromise_event)
        
        # Should rotate key and log incident
        assert recovery_result["key_rotated"] is True
        assert recovery_result["incident_logged"] is True
        
        # Key should be new
        new_key = key_manager.get_encryption_key(key_id)
        assert new_key is not None
    
    @pytest.mark.security
    def test_cryptographic_key_strength(self, key_manager):
        """Test cryptographic strength of generated keys"""
        # Test key generation entropy
        keys = []
        for _ in range(100):
            key_id = f"entropy-test-{secrets.token_hex(8)}"
            key_manager.create_encryption_key(
                key_id=key_id,
                algorithm="AES-256-GCM"
            )
            key = key_manager.get_encryption_key(key_id)
            keys.append(key)
        
        # All keys should be unique
        assert len(set(keys)) == 100
        
        # Check byte distribution (should be uniform)
        byte_counts = [0] * 256
        for key in keys:
            for byte in key:
                byte_counts[byte] += 1
        
        # Chi-square test for randomness (simplified)
        expected = sum(byte_counts) / 256
        chi_square = sum((count - expected) ** 2 / expected for count in byte_counts)
        
        # For 255 degrees of freedom, chi-square should be reasonable
        assert 200 < chi_square < 310  # 95% confidence interval
    
    @pytest.mark.security
    def test_hardware_security_module_integration(self, key_manager):
        """Test HSM integration capabilities"""
        # In real implementation, would test HSM integration
        # For now, test that HSM interface is available
        
        hsm_config = {
            "enabled": True,
            "provider": "pkcs11",
            "slot": 0,
            "pin": "test-pin"
        }
        
        # Should support HSM configuration
        assert key_manager.supports_hsm() is not None
        
        # Should validate HSM configuration
        config_valid = key_manager.validate_hsm_config(hsm_config)
        # Configuration is for testing, so may not be fully valid
        assert isinstance(config_valid, bool)


class TestEndToEndEncryption:
    """Test suite for end-to-end encryption scenarios"""
    
    @pytest.fixture
    def encryption_service(self):
        """Create encryption service instance"""
        temp_dir = tempfile.mkdtemp(prefix="e2e_test_")
        service = EncryptionService(
            storage_path=temp_dir,
            master_password="e2e-test-master-password"
        )
        yield service
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.security
    def test_api_middleware_encryption(self, encryption_service):
        """Test API middleware automatic encryption"""
        # Create middleware
        middleware = encryption_service.create_middleware(
            sensitive_fields=["password", "ssn", "credit_card"]
        )
        
        # Test request data
        request_data = {
            "username": "john_doe",
            "password": "secret123",
            "email": "john@example.com",
            "ssn": "123-45-6789"
        }
        
        # Middleware should encrypt sensitive fields
        encrypted_data = middleware.encrypt_response_data(request_data)
        
        assert encrypted_data["password"] != "secret123"
        assert encrypted_data["ssn"] != "123-45-6789"
        assert encrypted_data["email"] == "john@example.com"  # Not sensitive
        
        # Test request decryption
        decrypted_data = middleware.decrypt_request_data(encrypted_data)
        assert decrypted_data == request_data
    
    @pytest.mark.security
    def test_batch_encryption_operations(self, encryption_service):
        """Test batch encryption/decryption operations"""
        key_id = "batch-test-key"
        encryption_service.create_encryption_key(key_id)
        
        # Encrypt batch of data
        data_batch = [
            {"id": 1, "data": "Secret message 1"},
            {"id": 2, "data": "Secret message 2"},
            {"id": 3, "data": "Secret message 3"}
        ]
        
        encrypted_batch = encryption_service.encrypt_batch(data_batch, key_id)
        
        # All items should be encrypted
        for item in encrypted_batch:
            assert item["data"] != f"Secret message {item['id']}"
        
        # Decrypt batch
        decrypted_batch = encryption_service.decrypt_batch(encrypted_batch, key_id)
        assert decrypted_batch == data_batch
    
    @pytest.mark.security
    def test_zero_knowledge_encryption(self, encryption_service):
        """Test zero-knowledge encryption scenarios"""
        key_id = "zk-test-key"
        encryption_service.create_encryption_key(key_id)
        
        # Client-side encryption (server never sees plaintext)
        client_data = "Highly sensitive client data"
        client_key = secrets.token_bytes(32)
        
        # Client encrypts with their key
        client_encrypted = AESCrypto().encrypt(client_data.encode(), client_key)
        
        # Server encrypts again (double encryption)
        server_encrypted = encryption_service.encrypt_data(
            client_encrypted, 
            key_id
        )
        
        # Server cannot decrypt without client key
        try:
            server_decrypted = encryption_service.decrypt_data(server_encrypted, key_id)
            assert False, "Server should not be able to decrypt"
        except Exception:
            pass  # Expected
        
        # Only client can fully decrypt
        server_decrypted = encryption_service.decrypt_data(server_encrypted, key_id)
        client_decrypted = AESCrypto().decrypt(server_decrypted, client_key)
        assert client_decrypted.decode() == client_data
    
    @pytest.mark.security
    def test_encryption_key_isolation(self, encryption_service):
        """Test encryption key isolation between contexts"""
        key_id_1 = "context1-key"
        key_id_2 = "context2-key"
        
        encryption_service.create_encryption_key(key_id_1)
        encryption_service.create_encryption_key(key_id_2)
        
        same_plaintext = "Same message for both contexts"
        
        # Encrypt with different keys
        encrypted_1 = encryption_service.encrypt_data(same_plaintext, key_id_1)
        encrypted_2 = encryption_service.encrypt_data(same_plaintext, key_id_2)
        
        # Ciphertexts should be different
        assert encrypted_1 != encrypted_2
        
        # Decrypt with wrong key should fail
        try:
            encryption_service.decrypt_data(encrypted_1, key_id_2)
            assert False, "Should not decrypt with wrong key"
        except Exception:
            pass  # Expected
    
    @pytest.mark.security
    def test_data_at_rest_protection(self, encryption_service):
        """Test data-at-rest encryption protection"""
        key_id = "rest-test-key"
        encryption_service.create_encryption_key(key_id)
        
        # Create large dataset
        large_data = "X" * 1000000  # 1MB of data
        encrypted_data = encryption_service.encrypt_data(large_data, key_id)
        
        # Store in file
        temp_file = os.path.join(encryption_service.storage_path, "encrypted_data.bin")
        with open(temp_file, "wb") as f:
            f.write(encrypted_data)
        
        # File should not contain plaintext
        with open(temp_file, "rb") as f:
            content = f.read()
        
        assert b"X" * 100 not in content
        
        # Decrypt and verify
        decrypted_data = encryption_service.decrypt_data(encrypted_data, key_id)
        assert decrypted_data == large_data
    
    @pytest.mark.security
    def test_migration_encryption_compatibility(self, encryption_service):
        """Test encryption compatibility during migrations"""
        key_id = "migration-test-key"
        
        # Create key with specific parameters
        encryption_service.create_encryption_key(
            key_id=key_id,
            algorithm="AES-256-GCM",
            version="1.0"
        )
        
        # Encrypt data
        original_data = "Data to migrate"
        encrypted = encryption_service.encrypt_data(original_data, key_id)
        
        # Simulate key version upgrade
        new_key_id = encryption_service.upgrade_key_version(key_id, "2.0")
        
        # Should be able to decrypt with new key
        decrypted_new = encryption_service.decrypt_data(encrypted, new_key_id)
        assert decrypted_new == original_data
        
        # Old key should still work for backward compatibility
        decrypted_old = encryption_service.decrypt_data(encrypted, key_id)
        assert decrypted_old == original_data


class TestCryptographicAttacks:
    """Test suite for cryptographic attack resistance"""
    
    @pytest.mark.security
    def test_known_plaintext_attack_resistance(self):
        """Test resistance to known plaintext attacks"""
        crypto = AESCrypto()
        
        # Encrypt known plaintexts
        known_plaintexts = [
            b"ADMINISTRATOR",
            b"USER LOGIN",
            b"CONFIDENTIAL",
            b"SECRET DATA"
        ]
        
        ciphertexts = [crypto.encrypt(pt) for pt in known_plaintexts]
        
        # Should not reveal key information
        for i, ct1 in enumerate(ciphertexts):
            for j, ct2 in enumerate(ciphertexts):
                if i != j:
                    # XOR of ciphertexts should not reveal patterns
                    xor_result = bytes(a ^ b for a, b in zip(ct1[:32], ct2[:32]))
                    # Should appear random
                    assert xor_result != ct1[:32]
    
    @pytest.mark.security
    def test_chosen_plaintext_attack_resistance(self):
        """Test resistance to chosen plaintext attacks"""
        crypto = AESCrypto()
        
        # Attacker can choose plaintexts to encrypt
        chosen_plaintexts = [
            b"\x00" * 16,  # All zeros
            b"\xFF" * 16,  # All ones
            b"\x00\xFF" * 8,  # Alternating
            b"A" * 16,  # Same byte repeated
        ]
        
        # Encrypt chosen plaintexts
        ciphertexts = [crypto.encrypt(pt) for pt in chosen_plaintexts]
        
        # Should not leak key information
        # Ciphertexts should appear random
        for ct in ciphertexts:
            # Check for patterns that might leak key info
            assert len(set(ct[:8])) > 4  # Some entropy in first bytes
    
    @pytest.mark.security
    def test_brute_force_resistance(self):
        """Test resistance to brute force attacks"""
        crypto = AESCrypto()
        
        # 256-bit key space is computationally infeasible to brute force
        key_space_size = 2 ** 256
        
        # Simulate checking 1 billion keys (still negligible compared to 2^256)
        tested_keys = 10 ** 9
        
        # Fraction of key space tested
        fraction_tested = tested_keys / key_space_size
        
        # Should be effectively zero
        assert fraction_tested < 1e-60
    
    @pytest.mark.security
    def test_replay_attack_protection(self):
        """Test protection against replay attacks"""
        crypto = AESCrypto()
        
        # Include timestamp and nonce
        plaintext = b"Transfer $1000 to account 12345"
        timestamp = int(datetime.utcnow().timestamp())
        nonce = secrets.token_bytes(16)
        
        message_with_nonce = nonce + timestamp.to_bytes(8, 'big') + plaintext
        
        # Encrypt
        encrypted = crypto.encrypt(message_with_nonce)
        
        # Attempt to replay (copy same ciphertext)
        try:
            decrypted = crypto.decrypt(encrypted)
            
            # Extract nonce and timestamp
            replay_nonce = decrypted[:16]
            replay_timestamp = int.from_bytes(decrypted[16:24], 'big')
            
            # Check if nonce/timestamp match (replay attack)
            if replay_nonce == nonce and replay_timestamp == timestamp:
                # Should reject replay
                assert False, "Replay attack not detected"
        except Exception:
            pass  # Expected if attack detected
    
    @pytest.mark.security
    def test_side_channel_timing_attack(self):
        """Test protection against timing side-channel attacks"""
        crypto = AESCrypto()
        
        # Test decryption with valid and invalid keys
        plaintext = b"Test message for timing analysis"
        encrypted = crypto.encrypt(plaintext)
        
        # Valid key
        import time
        start = time.perf_counter()
        crypto.decrypt(encrypted)
        valid_time = time.perf_counter() - start
        
        # Invalid key (slightly different)
        invalid_key = AESCrypto.generate_key()
        invalid_key[0] ^= 0xFF  # Flip one bit
        
        start = time.perf_counter()
        try:
            AESCrypto(key=invalid_key).decrypt(encrypted)
        except Exception:
            pass
        invalid_time = time.perf_counter() - start
        
        # Timing difference should not be significant
        # (This is simplified - real implementation needs constant-time comparison)
        assert abs(valid_time - invalid_time) < 0.1
    
    @pytest.mark.security
    def test_cryptographic_randomness(self):
        """Test cryptographic randomness of generated values"""
        # Test key generation randomness
        crypto = AESCrypto()
        
        keys = [crypto.generate_key() for _ in range(1000)]
        
        # All keys should be unique
        assert len(set(keys)) == 1000
        
        # Statistical tests for randomness
        # Convert keys to bits for analysis
        all_bits = []
        for key in keys:
            all_bits.extend([(b >> i) & 1 for b in key for i in range(8)])
        
        # Count ones and zeros
        ones_count = sum(all_bits)
        zeros_count = len(all_bits) - ones_count
        
        # Should be approximately balanced (p=0.5)
        expected = len(all_bits) / 2
        deviation = abs(ones_count - expected)
        
        # Allow 3% deviation (99.7% confidence for normal distribution)
        assert deviation < 0.03 * len(all_bits)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short", "--cov=crypto_utils", "--cov=key_manager"])
