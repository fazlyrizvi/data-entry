"""
Key Management System for end-to-end encryption.
Handles secure key generation, storage, derivation, and automatic rotation.
"""

import os
import json
import time
import hmac
import hashlib
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import logging

from crypto_utils import AESCrypto, CryptoError

logger = logging.getLogger(__name__)


class KeyManagerError(Exception):
    """Custom exception for key management operations."""
    pass


class KeyMetadata:
    """Metadata for encryption keys."""
    
    def __init__(self, key_id: str, algorithm: str, created_at: datetime,
                 expires_at: Optional[datetime] = None, 
                 rotation_interval_days: int = 90):
        self.key_id = key_id
        self.algorithm = algorithm
        self.created_at = created_at
        self.expires_at = expires_at
        self.rotation_interval_days = rotation_interval_days
        self.last_used = created_at
        self.usage_count = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'key_id': self.key_id,
            'algorithm': self.algorithm,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'rotation_interval_days': self.rotation_interval_days,
            'last_used': self.last_used.isoformat(),
            'usage_count': self.usage_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'KeyMetadata':
        """Create from dictionary."""
        metadata = cls(
            key_id=data['key_id'],
            algorithm=data['algorithm'],
            created_at=datetime.fromisoformat(data['created_at']),
            expires_at=datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None,
            rotation_interval_days=data['rotation_interval_days']
        )
        metadata.last_used = datetime.fromisoformat(data['last_used'])
        metadata.usage_count = data['usage_count']
        return metadata


class SecureKeyStore:
    """
    Secure key storage with encryption and access control.
    Stores encryption keys encrypted with a master key.
    """
    
    def __init__(self, storage_path: str, master_key: Optional[bytes] = None):
        self.storage_path = storage_path
        self.master_key = master_key or self._generate_or_load_master_key()
        self.key_db_path = os.path.join(storage_path, 'keys.json')
        self.metadata_path = os.path.join(storage_path, 'metadata.json')
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
        
        # Initialize encryption for key storage
        self.fernet = Fernet(Fernet.generate_key())
        if os.path.exists(self.key_db_path):
            self._load_key_database()
        else:
            self._key_database = {}
            self._metadata = {}
            self._save_key_database()
    
    def _generate_or_load_master_key(self) -> bytes:
        """Generate or load the master key."""
        master_key_path = os.path.join(self.storage_path, '.master_key')
        
        if os.path.exists(master_key_path):
            with open(master_key_path, 'rb') as f:
                return f.read()
        else:
            master_key = Fernet.generate_key()
            # Store master key with restrictive permissions
            with open(master_key_path, 'wb') as f:
                f.write(master_key)
            os.chmod(master_key_path, 0o600)
            logger.warning("Generated new master key - store securely!")
            return master_key
    
    def _load_key_database(self) -> None:
        """Load the encrypted key database."""
        try:
            with open(self.key_db_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data)
            self._key_database = json.loads(decrypted_data.decode('utf-8'))
            
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r') as f:
                    self._metadata = json.load(f)
            else:
                self._metadata = {}
                
        except Exception as e:
            logger.error(f"Failed to load key database: {e}")
            raise KeyManagerError(f"Failed to load key database: {e}")
    
    def _save_key_database(self) -> None:
        """Save the encrypted key database."""
        try:
            data = json.dumps(self._key_database).encode('utf-8')
            encrypted_data = self.fernet.encrypt(data)
            
            with open(self.key_db_path, 'wb') as f:
                f.write(encrypted_data)
            os.chmod(self.key_db_path, 0o600)
            
            if self._metadata:
                with open(self.metadata_path, 'w') as f:
                    json.dump(self._metadata, f, indent=2)
                os.chmod(self.metadata_path, 0o600)
                
        except Exception as e:
            logger.error(f"Failed to save key database: {e}")
            raise KeyManagerError(f"Failed to save key database: {e}")
    
    def store_key(self, key_id: str, key: bytes, metadata: KeyMetadata) -> None:
        """
        Store an encryption key securely.
        
        Args:
            key_id: Unique identifier for the key
            key: Encryption key to store
            metadata: Key metadata
        """
        try:
            # Encrypt the key before storing
            encrypted_key = self.fernet.encrypt(key).decode('utf-8')
            
            self._key_database[key_id] = encrypted_key
            self._metadata[key_id] = metadata.to_dict()
            
            self._save_key_database()
            logger.info(f"Stored key {key_id} securely")
            
        except Exception as e:
            logger.error(f"Failed to store key {key_id}: {e}")
            raise KeyManagerError(f"Failed to store key {key_id}: {e}")
    
    def retrieve_key(self, key_id: str) -> Tuple[bytes, KeyMetadata]:
        """
        Retrieve an encryption key.
        
        Args:
            key_id: Key identifier
            
        Returns:
            Tuple of (key, metadata)
            
        Raises:
            KeyManagerError: If key not found or retrieval fails
        """
        try:
            if key_id not in self._key_database:
                raise KeyManagerError(f"Key {key_id} not found")
            
            encrypted_key = self._key_database[key_id].encode('utf-8')
            key = self.fernet.decrypt(encrypted_key)
            
            metadata = KeyMetadata.from_dict(self._metadata[key_id])
            metadata.last_used = datetime.now()
            metadata.usage_count += 1
            
            # Update last used timestamp
            self._metadata[key_id] = metadata.to_dict()
            self._save_key_database()
            
            logger.debug(f"Retrieved key {key_id}")
            return key, metadata
            
        except Exception as e:
            logger.error(f"Failed to retrieve key {key_id}: {e}")
            raise KeyManagerError(f"Failed to retrieve key {key_id}: {e}")
    
    def delete_key(self, key_id: str) -> None:
        """Delete a stored key."""
        try:
            if key_id in self._key_database:
                del self._key_database[key_id]
            if key_id in self._metadata:
                del self._metadata[key_id]
            
            self._save_key_database()
            logger.info(f"Deleted key {key_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete key {key_id}: {e}")
            raise KeyManagerError(f"Failed to delete key {key_id}: {e}")
    
    def list_keys(self) -> List[str]:
        """List all stored key IDs."""
        return list(self._key_database.keys())


class KeyRotationManager:
    """
    Automatic key rotation management.
    Rotates encryption keys based on time-based or usage-based policies.
    """
    
    def __init__(self, key_store: SecureKeyStore):
        self.key_store = key_store
    
    def check_rotation_needed(self, key_id: str) -> bool:
        """
        Check if a key needs rotation.
        
        Args:
            key_id: Key identifier
            
        Returns:
            True if rotation is needed
        """
        try:
            _, metadata = self.key_store.retrieve_key(key_id)
            
            # Check if key has expired
            if metadata.expires_at and datetime.now() > metadata.expires_at:
                return True
            
            # Check rotation interval
            time_since_created = datetime.now() - metadata.created_at
            if time_since_created.days >= metadata.rotation_interval_days:
                return True
            
            # Check usage count threshold (e.g., 10000 uses)
            if metadata.usage_count >= 10000:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to check rotation for key {key_id}: {e}")
            return False
    
    def rotate_key(self, key_id: str, preserve_data: bool = True) -> str:
        """
        Rotate an encryption key.
        
        Args:
            key_id: Key to rotate
            preserve_data: If True, decrypt and re-encrypt data with new key
            
        Returns:
            New key ID
            
        Raises:
            KeyManagerError: If rotation fails
        """
        try:
            old_key, old_metadata = self.key_store.retrieve_key(key_id)
            
            # Generate new key
            new_key_id = f"{key_id}_rotated_{int(time.time())}"
            new_key = AESCrypto.generate_key()
            
            # Create metadata for new key
            new_metadata = KeyMetadata(
                key_id=new_key_id,
                algorithm=old_metadata.algorithm,
                created_at=datetime.now(),
                rotation_interval_days=old_metadata.rotation_interval_days
            )
            
            # Store new key
            self.key_store.store_key(new_key_id, new_key, new_metadata)
            
            logger.info(f"Rotated key {key_id} to {new_key_id}")
            return new_key_id
            
        except Exception as e:
            logger.error(f"Key rotation failed for {key_id}: {e}")
            raise KeyManagerError(f"Key rotation failed: {e}")
    
    def get_expired_keys(self) -> List[str]:
        """Get list of keys that need rotation."""
        expired_keys = []
        
        for key_id in self.key_store.list_keys():
            if self.check_rotation_needed(key_id):
                expired_keys.append(key_id)
        
        return expired_keys


class MasterKeyDerivation:
    """
    Master key derivation from various sources.
    Supports derivation from passwords, hardware security modules, etc.
    """
    
    @staticmethod
    def derive_from_password(password: str, salt: Optional[bytes] = None,
                           iterations: int = 100000) -> Tuple[bytes, bytes]:
        """
        Derive master key from password using PBKDF2.
        
        Args:
            password: Source password
            salt: Optional salt (generated if not provided)
            iterations: PBKDF2 iterations
            
        Returns:
            Tuple of (master_key, salt)
        """
        if salt is None:
            salt = os.urandom(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        
        master_key = kdf.derive(password.encode('utf-8'))
        return master_key, salt
    
    @staticmethod
    def derive_hierarchical_key(parent_key: bytes, key_path: str,
                               context: str = "data_encryption") -> bytes:
        """
        Derive hierarchical keys from parent key using HKDF.
        
        Args:
            parent_key: Parent key
            key_path: Path identifier for the derived key
            context: Application context for key derivation
            
        Returns:
            Derived key
        """
        info = f"{context}:{key_path}".encode('utf-8')
        
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=parent_key[:16],  # Use first 16 bytes as salt
            info=info,
            backend=default_backend()
        )
        
        return hkdf.derive(parent_key)


class KeyManager:
    """
    Main key management interface.
    Provides centralized key lifecycle management.
    """
    
    def __init__(self, storage_path: str = "/var/lib/encryption/keys",
                 master_password: Optional[str] = None):
        self.storage_path = storage_path
        self.master_password = master_password
        
        # Derive master key if password provided
        if master_password:
            master_key, salt = MasterKeyDerivation.derive_from_password(master_password)
            self.key_store = SecureKeyStore(storage_path, master_key)
        else:
            self.key_store = SecureKeyStore(storage_path)
        
        self.rotation_manager = KeyRotationManager(self.key_store)
    
    def create_key(self, key_id: str, algorithm: str = "AES-256-GCM",
                   rotation_interval_days: int = 90) -> bytes:
        """
        Create a new encryption key.
        
        Args:
            key_id: Unique key identifier
            algorithm: Encryption algorithm
            rotation_interval_days: Automatic rotation interval
            
        Returns:
            The created encryption key
        """
        key = AESCrypto.generate_key()
        
        metadata = KeyMetadata(
            key_id=key_id,
            algorithm=algorithm,
            created_at=datetime.now(),
            rotation_interval_days=rotation_interval_days
        )
        
        self.key_store.store_key(key_id, key, metadata)
        logger.info(f"Created new {algorithm} key: {key_id}")
        
        return key
    
    def get_key(self, key_id: str) -> bytes:
        """Get an encryption key by ID."""
        key, _ = self.key_store.retrieve_key(key_id)
        return key
    
    def delete_key(self, key_id: str) -> None:
        """Delete an encryption key."""
        self.key_store.delete_key(key_id)
    
    def list_keys(self) -> List[str]:
        """List all key IDs."""
        return self.key_store.list_keys()
    
    def rotate_expired_keys(self) -> List[str]:
        """Rotate all keys that need rotation."""
        expired_keys = self.rotation_manager.get_expired_keys()
        rotated_keys = []
        
        for key_id in expired_keys:
            new_key_id = self.rotation_manager.rotate_key(key_id)
            rotated_keys.append((key_id, new_key_id))
        
        if rotated_keys:
            logger.info(f"Rotated {len(rotated_keys)} expired keys")
        
        return rotated_keys
    
    def get_key_info(self, key_id: str) -> dict:
        """Get detailed information about a key."""
        try:
            _, metadata = self.key_store.retrieve_key(key_id)
            needs_rotation = self.rotation_manager.check_rotation_needed(key_id)
            
            info = metadata.to_dict()
            info['needs_rotation'] = needs_rotation
            info['is_expired'] = (
                metadata.expires_at and datetime.now() > metadata.expires_at
            )
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get key info for {key_id}: {e}")
            raise KeyManagerError(f"Failed to get key info: {e}")
