"""
Cryptographic utilities for AES-256-GCM encryption and decryption.
Provides secure encryption/decryption operations with integrity verification.
"""

import os
import base64
from typing import Optional, Tuple, Union
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)


class CryptoError(Exception):
    """Custom exception for cryptographic operations."""
    pass


class AESCrypto:
    """
    AES-256-GCM encryption/decryption utilities.
    
    Provides authenticated encryption with associated data (AEAD)
    ensuring both confidentiality and integrity.
    """
    
    KEY_LENGTH = 32  # 256 bits
    NONCE_LENGTH = 12  # 96 bits (recommended for GCM)
    TAG_LENGTH = 16  # 128 bits
    
    @staticmethod
    def generate_key(key_length: int = KEY_LENGTH) -> bytes:
        """
        Generate a cryptographically secure random key.
        
        Args:
            key_length: Length of key in bytes (default: 32 bytes for AES-256)
            
        Returns:
            Random bytes key
            
        Raises:
            CryptoError: If key generation fails
        """
        try:
            key = os.urandom(key_length)
            logger.debug(f"Generated {key_length * 8}-bit key")
            return key
        except Exception as e:
            logger.error(f"Key generation failed: {e}")
            raise CryptoError(f"Key generation failed: {e}")
    
    @staticmethod
    def derive_key_from_password(password: str, salt: bytes, iterations: int = 100000) -> bytes:
        """
        Derive encryption key from password using PBKDF2.
        
        Args:
            password: Password to derive key from
            salt: Random salt (should be unique per password)
            iterations: Number of PBKDF2 iterations (default: 100000)
            
        Returns:
            Derived key (32 bytes for AES-256)
            
        Raises:
            CryptoError: If key derivation fails
        """
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=iterations,
                backend=default_backend()
            )
            key = kdf.derive(password.encode('utf-8'))
            logger.debug(f"Derived key using PBKDF2 with {iterations} iterations")
            return key
        except Exception as e:
            logger.error(f"Key derivation failed: {e}")
            raise CryptoError(f"Key derivation failed: {e}")
    
    @staticmethod
    def encrypt(plaintext: Union[str, bytes], key: bytes, 
                associated_data: Optional[bytes] = None) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            plaintext: Data to encrypt (str or bytes)
            key: 32-byte encryption key
            associated_data: Additional authenticated data (optional)
            
        Returns:
            Tuple of (nonce, ciphertext, tag)
            - nonce: 12-byte random nonce
            - ciphertext: Encrypted data
            - tag: 16-byte authentication tag
            
        Raises:
            CryptoError: If encryption fails
        """
        try:
            # Convert string to bytes if needed
            if isinstance(plaintext, str):
                plaintext = plaintext.encode('utf-8')
            
            # Generate random nonce
            nonce = os.urandom(AESCrypto.NONCE_LENGTH)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce),
                backend=default_backend()
            )
            
            # Encrypt data
            encryptor = cipher.encryptor()
            
            # Authenticate associated data if provided
            if associated_data:
                encryptor.authenticate_additional_data(associated_data)
            
            ciphertext = encryptor.update(plaintext) + encryptor.finalize()
            tag = encryptor.tag
            
            logger.debug(f"Encrypted {len(plaintext)} bytes with AES-256-GCM")
            return nonce, ciphertext, tag
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise CryptoError(f"Encryption failed: {e}")
    
    @staticmethod
    def decrypt(nonce: bytes, ciphertext: bytes, tag: bytes, key: bytes,
                associated_data: Optional[bytes] = None) -> bytes:
        """
        Decrypt data using AES-256-GCM.
        
        Args:
            nonce: 12-byte nonce used during encryption
            ciphertext: Encrypted data
            tag: 16-byte authentication tag
            key: 32-byte decryption key
            associated_data: Additional authenticated data (optional)
            
        Returns:
            Decrypted plaintext bytes
            
        Raises:
            CryptoError: If decryption fails or authenticity cannot be verified
        """
        try:
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce, tag),
                backend=default_backend()
            )
            
            # Decrypt data
            decryptor = cipher.decryptor()
            
            # Authenticate associated data if provided
            if associated_data:
                decryptor.authenticate_additional_data(associated_data)
            
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            logger.debug(f"Decrypted {len(ciphertext)} bytes with AES-256-GCM")
            return plaintext
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise CryptoError(f"Decryption failed: {e}")
    
    @staticmethod
    def encrypt_to_base64(plaintext: Union[str, bytes], key: bytes) -> str:
        """
        Encrypt data and return base64-encoded result.
        
        Args:
            plaintext: Data to encrypt
            key: 32-byte encryption key
            
        Returns:
            Base64-encoded string containing nonce|ciphertext|tag
        """
        nonce, ciphertext, tag = AESCrypto.encrypt(plaintext, key)
        combined = nonce + ciphertext + tag
        return base64.b64encode(combined).decode('utf-8')
    
    @staticmethod
    def decrypt_from_base64(encrypted_data: str, key: bytes) -> bytes:
        """
        Decrypt base64-encoded data.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            key: 32-byte decryption key
            
        Returns:
            Decrypted plaintext bytes
        """
        try:
            combined = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Extract nonce, ciphertext, and tag
            nonce = combined[:AESCrypto.NONCE_LENGTH]
            tag = combined[-AESCrypto.TAG_LENGTH:]
            ciphertext = combined[AESCrypto.NONCE_LENGTH:-AESCrypto.TAG_LENGTH]
            
            return AESCrypto.decrypt(nonce, ciphertext, tag, key)
            
        except Exception as e:
            logger.error(f"Base64 decryption failed: {e}")
            raise CryptoError(f"Base64 decryption failed: {e}")


class FernetCrypto:
    """
    High-level Fernet encryption wrapper for simple operations.
    
    Uses AES-128-CBC for encryption and HMAC-SHA256 for authentication.
    """
    
    @staticmethod
    def generate_key() -> bytes:
        """Generate a Fernet encryption key."""
        return Fernet.generate_key()
    
    @staticmethod
    def encrypt(data: Union[str, bytes], key: bytes) -> bytes:
        """
        Encrypt data using Fernet.
        
        Args:
            data: Data to encrypt
            key: Fernet key
            
        Returns:
            Encrypted data with timestamp and HMAC
        """
        f = Fernet(key)
        if isinstance(data, str):
            data = data.encode('utf-8')
        return f.encrypt(data)
    
    @staticmethod
    def decrypt(encrypted_data: bytes, key: bytes) -> bytes:
        """
        Decrypt Fernet-encrypted data.
        
        Args:
            encrypted_data: Encrypted data
            key: Fernet key
            
        Returns:
            Decrypted plaintext
        """
        f = Fernet(key)
        return f.decrypt(encrypted_data)


class FileEncryption:
    """Utilities for encrypting and decrypting files."""
    
    @staticmethod
    def encrypt_file(input_path: str, output_path: str, key: bytes) -> None:
        """
        Encrypt a file using AES-256-GCM.
        
        Args:
            input_path: Path to input file
            output_path: Path to encrypted output file
            key: 32-byte encryption key
            
        Raises:
            CryptoError: If file encryption fails
        """
        try:
            with open(input_path, 'rb') as f:
                plaintext = f.read()
            
            nonce, ciphertext, tag = AESCrypto.encrypt(plaintext, key)
            
            # Write nonce, ciphertext, and tag to output file
            with open(output_path, 'wb') as f:
                f.write(nonce)
                f.write(tag)
                f.write(ciphertext)
            
            logger.info(f"Encrypted {input_path} to {output_path}")
            
        except Exception as e:
            logger.error(f"File encryption failed: {e}")
            raise CryptoError(f"File encryption failed: {e}")
    
    @staticmethod
    def decrypt_file(input_path: str, output_path: str, key: bytes) -> None:
        """
        Decrypt a file using AES-256-GCM.
        
        Args:
            input_path: Path to encrypted file
            output_path: Path to decrypted output file
            key: 32-byte decryption key
            
        Raises:
            CryptoError: If file decryption fails
        """
        try:
            with open(input_path, 'rb') as f:
                data = f.read()
            
            # Extract nonce, tag, and ciphertext
            nonce = data[:AESCrypto.NONCE_LENGTH]
            tag = data[AESCrypto.NONCE_LENGTH:AESCrypto.NONCE_LENGTH + AESCrypto.TAG_LENGTH]
            ciphertext = data[AESCrypto.NONCE_LENGTH + AESCrypto.TAG_LENGTH:]
            
            plaintext = AESCrypto.decrypt(nonce, ciphertext, tag, key)
            
            with open(output_path, 'wb') as f:
                f.write(plaintext)
            
            logger.info(f"Decrypted {input_path} to {output_path}")
            
        except Exception as e:
            logger.error(f"File decryption failed: {e}")
            raise CryptoError(f"File decryption failed: {e}")


class DatabaseFieldEncryption:
    """
    Utilities for encrypting database fields.
    Provides transparent encryption/decryption for sensitive data.
    """
    
    @staticmethod
    def encrypt_field(value: Union[str, bytes], key: bytes) -> str:
        """
        Encrypt a database field value.
        
        Args:
            value: Field value to encrypt
            key: 32-byte encryption key
            
        Returns:
            Base64-encoded encrypted value
        """
        return AESCrypto.encrypt_to_base64(value, key)
    
    @staticmethod
    def decrypt_field(encrypted_value: str, key: bytes) -> bytes:
        """
        Decrypt a database field value.
        
        Args:
            encrypted_value: Base64-encoded encrypted value
            key: 32-byte decryption key
            
        Returns:
            Decrypted field value
        """
        return AESCrypto.decrypt_from_base64(encrypted_value, key)
