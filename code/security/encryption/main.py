"""
Main encryption service for end-to-end encryption.
Provides unified interface for all encryption operations.
"""

import os
import json
import logging
from typing import Dict, Optional, Union, Any
from datetime import datetime, timedelta

from key_manager import KeyManager, KeyManagerError
from crypto_utils import (
    AESCrypto, FernetCrypto, FileEncryption, DatabaseFieldEncryption, CryptoError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EncryptionServiceError(Exception):
    """Custom exception for encryption service operations."""
    pass


class EncryptionService:
    """
    Main encryption service providing unified interface.
    
    Handles all encryption operations including:
    - Data at rest encryption (AES-256-GCM)
    - File encryption
    - Database field encryption
    - Key management and rotation
    - API middleware integration
    """
    
    def __init__(self, storage_path: str = "/var/lib/encryption/keys",
                 master_password: Optional[str] = None,
                 auto_rotation_enabled: bool = True):
        """
        Initialize the encryption service.
        
        Args:
            storage_path: Path to key storage directory
            master_password: Master password for key derivation
            auto_rotation_enabled: Enable automatic key rotation
        """
        self.storage_path = storage_path
        self.auto_rotation_enabled = auto_rotation_enabled
        
        try:
            self.key_manager = KeyManager(storage_path, master_password)
            logger.info("Encryption service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {e}")
            raise EncryptionServiceError(f"Initialization failed: {e}")
    
    # ===== Key Management =====
    
    def create_encryption_key(self, key_id: str, algorithm: str = "AES-256-GCM",
                            rotation_interval_days: int = 90) -> str:
        """
        Create a new encryption key.
        
        Args:
            key_id: Unique identifier for the key
            algorithm: Encryption algorithm
            rotation_interval_days: Automatic rotation interval in days
            
        Returns:
            Key ID
            
        Raises:
            EncryptionServiceError: If key creation fails
        """
        try:
            key = self.key_manager.create_key(key_id, algorithm, rotation_interval_days)
            logger.info(f"Created encryption key: {key_id}")
            return key_id
        except KeyManagerError as e:
            logger.error(f"Key creation failed: {e}")
            raise EncryptionServiceError(f"Key creation failed: {e}")
    
    def get_encryption_key(self, key_id: str) -> bytes:
        """
        Retrieve an encryption key.
        
        Args:
            key_id: Key identifier
            
        Returns:
            Encryption key bytes
            
        Raises:
            EncryptionServiceError: If key retrieval fails
        """
        try:
            return self.key_manager.get_key(key_id)
        except KeyManagerError as e:
            logger.error(f"Key retrieval failed: {e}")
            raise EncryptionServiceError(f"Key retrieval failed: {e}")
    
    def delete_encryption_key(self, key_id: str) -> None:
        """
        Delete an encryption key.
        
        Args:
            key_id: Key identifier
            
        Raises:
            EncryptionServiceError: If key deletion fails
        """
        try:
            self.key_manager.delete_key(key_id)
            logger.info(f"Deleted encryption key: {key_id}")
        except KeyManagerError as e:
            logger.error(f"Key deletion failed: {e}")
            raise EncryptionServiceError(f"Key deletion failed: {e}")
    
    def list_keys(self) -> list:
        """List all encryption key IDs."""
        return self.key_manager.list_keys()
    
    def get_key_info(self, key_id: str) -> dict:
        """Get detailed information about a key."""
        return self.key_manager.get_key_info(key_id)
    
    # ===== Data Encryption =====
    
    def encrypt_data(self, data: Union[str, bytes], key_id: str,
                    associated_data: Optional[bytes] = None) -> str:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            data: Data to encrypt
            key_id: Key identifier to use
            associated_data: Additional authenticated data
            
        Returns:
            Base64-encoded encrypted data
            
        Raises:
            EncryptionServiceError: If encryption fails
        """
        try:
            key = self.get_encryption_key(key_id)
            encrypted_data = AESCrypto.encrypt_to_base64(data, key)
            logger.debug(f"Encrypted data using key: {key_id}")
            return encrypted_data
        except (CryptoError, EncryptionServiceError) as e:
            logger.error(f"Data encryption failed: {e}")
            raise EncryptionServiceError(f"Data encryption failed: {e}")
    
    def decrypt_data(self, encrypted_data: str, key_id: str) -> bytes:
        """
        Decrypt data using AES-256-GCM.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            key_id: Key identifier to use
            
        Returns:
            Decrypted data bytes
            
        Raises:
            EncryptionServiceError: If decryption fails
        """
        try:
            key = self.get_encryption_key(key_id)
            decrypted_data = AESCrypto.decrypt_from_base64(encrypted_data, key)
            logger.debug(f"Decrypted data using key: {key_id}")
            return decrypted_data
        except (CryptoError, EncryptionServiceError) as e:
            logger.error(f"Data decryption failed: {e}")
            raise EncryptionServiceError(f"Data decryption failed: {e}")
    
    # ===== Database Field Encryption =====
    
    def encrypt_field(self, value: Union[str, bytes], key_id: str) -> str:
        """
        Encrypt a database field value.
        
        Args:
            value: Field value to encrypt
            key_id: Key identifier to use
            
        Returns:
            Base64-encoded encrypted value
            
        Raises:
            EncryptionServiceError: If field encryption fails
        """
        try:
            key = self.get_encryption_key(key_id)
            return DatabaseFieldEncryption.encrypt_field(value, key)
        except CryptoError as e:
            logger.error(f"Field encryption failed: {e}")
            raise EncryptionServiceError(f"Field encryption failed: {e}")
    
    def decrypt_field(self, encrypted_value: str, key_id: str) -> bytes:
        """
        Decrypt a database field value.
        
        Args:
            encrypted_value: Base64-encoded encrypted value
            key_id: Key identifier to use
            
        Returns:
            Decrypted field value
            
        Raises:
            EncryptionServiceError: If field decryption fails
        """
        try:
            key = self.get_encryption_key(key_id)
            return DatabaseFieldEncryption.decrypt_field(encrypted_value, key)
        except CryptoError as e:
            logger.error(f"Field decryption failed: {e}")
            raise EncryptionServiceError(f"Field decryption failed: {e}")
    
    # ===== File Encryption =====
    
    def encrypt_file(self, input_path: str, output_path: str, key_id: str) -> None:
        """
        Encrypt a file.
        
        Args:
            input_path: Path to input file
            output_path: Path to encrypted output file
            key_id: Key identifier to use
            
        Raises:
            EncryptionServiceError: If file encryption fails
        """
        try:
            key = self.get_encryption_key(key_id)
            FileEncryption.encrypt_file(input_path, output_path, key)
            logger.info(f"Encrypted file: {input_path} -> {output_path}")
        except CryptoError as e:
            logger.error(f"File encryption failed: {e}")
            raise EncryptionServiceError(f"File encryption failed: {e}")
    
    def decrypt_file(self, input_path: str, output_path: str, key_id: str) -> None:
        """
        Decrypt a file.
        
        Args:
            input_path: Path to encrypted file
            output_path: Path to decrypted output file
            key_id: Key identifier to use
            
        Raises:
            EncryptionServiceError: If file decryption fails
        """
        try:
            key = self.get_encryption_key(key_id)
            FileEncryption.decrypt_file(input_path, output_path, key)
            logger.info(f"Decrypted file: {input_path} -> {output_path}")
        except CryptoError as e:
            logger.error(f"File decryption failed: {e}")
            raise EncryptionServiceError(f"File decryption failed: {e}")
    
    # ===== Key Rotation =====
    
    def rotate_expired_keys(self) -> list:
        """
        Rotate all expired keys.
        
        Returns:
            List of rotated key pairs (old_id, new_id)
        """
        try:
            rotated_keys = self.key_manager.rotate_expired_keys()
            logger.info(f"Rotated {len(rotated_keys)} keys")
            return rotated_keys
        except KeyManagerError as e:
            logger.error(f"Key rotation failed: {e}")
            raise EncryptionServiceError(f"Key rotation failed: {e}")
    
    def check_key_rotation_needed(self, key_id: str) -> bool:
        """Check if a key needs rotation."""
        return self.key_manager.rotation_manager.check_rotation_needed(key_id)
    
    # ===== Security Utilities =====
    
    def verify_data_integrity(self, data: Union[str, bytes], signature: str,
                            key_id: str) -> bool:
        """
        Verify data integrity using HMAC.
        
        Args:
            data: Original data
            signature: HMAC signature to verify
            key_id: Key identifier for HMAC key derivation
            
        Returns:
            True if signature is valid
        """
        try:
            key = self.get_encryption_key(key_id)
            # Use first 32 bytes of key for HMAC
            hmac_key = key[:32]
            
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            expected_signature = hmac.new(hmac_key, data, hashlib.sha256).hexdigest()
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Integrity verification failed: {e}")
            return False
    
    def generate_data_signature(self, data: Union[str, bytes], key_id: str) -> str:
        """
        Generate HMAC signature for data integrity.
        
        Args:
            data: Data to sign
            key_id: Key identifier for HMAC key derivation
            
        Returns:
            HMAC signature
        """
        import hmac
        import hashlib
        
        key = self.get_encryption_key(key_id)
        hmac_key = key[:32]
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return hmac.new(hmac_key, data, hashlib.sha256).hexdigest()
    
    # ===== API Middleware Integration =====
    
    def create_api_middleware(self) -> 'APIMiddleware':
        """Create API middleware for automatic encryption/decryption."""
        return APIMiddleware(self)
    
    def encrypt_response_data(self, data: dict, key_id: str) -> dict:
        """
        Encrypt sensitive fields in API response.
        
        Args:
            data: Response data dictionary
            key_id: Key identifier for encryption
            
        Returns:
            Data with encrypted fields
        """
        # Define sensitive field patterns
        sensitive_fields = [
            'password', 'token', 'secret', 'key', 'ssn', 'credit_card',
            'email', 'phone', 'address', 'name', 'birth_date'
        ]
        
        encrypted_data = data.copy()
        
        for field_name, field_value in data.items():
            # Check if field should be encrypted
            if any(pattern in field_name.lower() for pattern in sensitive_fields):
                if isinstance(field_value, str):
                    encrypted_data[field_name] = self.encrypt_data(field_value, key_id)
        
        return encrypted_data
    
    def decrypt_request_data(self, data: dict, key_id: str) -> dict:
        """
        Decrypt sensitive fields in API request.
        
        Args:
            data: Request data dictionary
            key_id: Key identifier for decryption
            
        Returns:
            Data with decrypted fields
        """
        # This would be used in API middleware to decrypt incoming data
        decrypted_data = data.copy()
        
        # Implementation would depend on how encrypted fields are marked
        # For now, return as-is
        return decrypted_data


class APIMiddleware:
    """
    Middleware for automatic encryption/decryption in API endpoints.
    
    Provides decorators and utilities for protecting sensitive API data.
    """
    
    def __init__(self, encryption_service: EncryptionService):
        self.encryption_service = encryption_service
    
    def encrypt_response(self, key_id: str, sensitive_fields: list = None):
        """
        Decorator to automatically encrypt sensitive fields in API responses.
        
        Args:
            key_id: Key identifier for encryption
            sensitive_fields: List of field names to encrypt
            
        Returns:
            Decorated function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                
                if isinstance(result, dict):
                    # Default sensitive fields if none specified
                    if sensitive_fields is None:
                        sensitive_fields = [
                            'password', 'token', 'secret', 'key', 'ssn',
                            'credit_card', 'email', 'phone', 'address'
                        ]
                    
                    # Encrypt sensitive fields
                    for field_name in sensitive_fields:
                        if field_name in result and isinstance(result[field_name], str):
                            result[field_name] = self.encryption_service.encrypt_data(
                                result[field_name], key_id
                            )
                
                return result
            return wrapper
        return decorator
    
    def decrypt_request(self, key_id: str, encrypted_fields: list = None):
        """
        Decorator to automatically decrypt sensitive fields in API requests.
        
        Args:
            key_id: Key identifier for decryption
            encrypted_fields: List of field names to decrypt
            
        Returns:
            Decorated function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Assuming first argument is request data
                if args and isinstance(args[0], dict):
                    request_data = args[0].copy()
                    
                    if encrypted_fields is None:
                        encrypted_fields = [
                            'password', 'token', 'secret', 'key', 'ssn',
                            'credit_card', 'email', 'phone', 'address'
                        ]
                    
                    # Decrypt encrypted fields
                    for field_name in encrypted_fields:
                        if field_name in request_data:
                            try:
                                decrypted_value = self.encryption_service.decrypt_data(
                                    request_data[field_name], key_id
                                )
                                request_data[field_name] = decrypted_value.decode('utf-8')
                            except Exception as e:
                                logger.warning(f"Failed to decrypt field {field_name}: {e}")
                    
                    args = (request_data,) + args[1:]
                
                return func(*args, **kwargs)
            return wrapper
        return decorator


# ===== Usage Examples =====

def main():
    """Example usage of the encryption service."""
    
    # Initialize encryption service
    encryption_service = EncryptionService(
        storage_path="/tmp/encryption_keys",
        master_password="strong_master_password_123"
    )
    
    # Create encryption keys
    encryption_service.create_encryption_key("user_data_key", rotation_interval_days=90)
    encryption_service.create_encryption_key("financial_data_key", rotation_interval_days=30)
    
    # Encrypt data
    sensitive_data = "user_password_123"
    encrypted = encryption_service.encrypt_data(sensitive_data, "user_data_key")
    print(f"Encrypted: {encrypted}")
    
    # Decrypt data
    decrypted = encryption_service.decrypt_data(encrypted, "user_data_key")
    print(f"Decrypted: {decrypted.decode('utf-8')}")
    
    # Create API middleware
    middleware = encryption_service.create_api_middleware()
    
    # Example API endpoint with automatic encryption
    @middleware.encrypt_response("user_data_key")
    def get_user_data():
        return {
            "id": 123,
            "username": "john_doe",
            "email": "john@example.com",
            "password": "secret123"
        }
    
    # Test API middleware
    user_data = get_user_data()
    print(f"Encrypted API response: {user_data}")
    
    # Key rotation
    rotated = encryption_service.rotate_expired_keys()
    print(f"Rotated keys: {rotated}")


if __name__ == "__main__":
    main()
