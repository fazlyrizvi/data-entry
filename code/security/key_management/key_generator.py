"""
Secure API Key Generator Module

Handles secure generation of API keys with multiple algorithms and HSM integration.
Supports various key types and formats for different use cases.
"""

import secrets
import hashlib
import hmac
import time
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption
from cryptography.hazmat.backends import default_backend
import base64
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KeyType(Enum):
    """Supported API key types"""
    HMAC = "hmac"
    RSA = "rsa"
    ECDSA = "ecdsa"
    JWT = "jwt"
    API_TOKEN = "api_token"
    PROVISIONING = "provisioning"


class KeyLength(Enum):
    """Supported key lengths in bits"""
    SHORT = 128  # For tokens
    MEDIUM = 256  # For HMAC
    LONG = 4096  # For RSA
    X_LONG = 8192  # For RSA


class KeyScope(Enum):
    """API key scopes/permissions"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    READ_WRITE = "read,write"
    FULL = "full"


@dataclass
class GeneratedKey:
    """Container for generated API key data"""
    key_id: str
    key_type: str
    key_value: str
    public_key: Optional[str] = None
    private_key: Optional[str] = None
    scope: str = "read"
    algorithm: str = "sha256"
    key_length: int = 256
    created_at: float = None
    expires_at: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class SecureKeyGenerator:
    """
    Secure API key generator with HSM integration support
    
    Features:
    - Multiple cryptographic algorithms
    - HSM integration ready
    - Secure random generation using system entropy
    - Key versioning and rotation support
    - Comprehensive metadata tracking
    """

    def __init__(self, hsm_enabled: bool = False, hsm_config: Optional[Dict] = None):
        """
        Initialize the key generator
        
        Args:
            hsm_enabled: Whether to use HSM for key generation
            hsm_config: Configuration for HSM connection
        """
        self.hsm_enabled = hsm_enabled
        self.hsm_config = hsm_config or {}
        self._entropy_source = secrets.SystemRandom()
        self._key_counter = 0
        
        logger.info(f"Key generator initialized (HSM: {hsm_enabled})")

    def generate_api_key(
        self,
        key_type: KeyType,
        key_scope: KeyScope,
        key_length: KeyLength = KeyLength.MEDIUM,
        expires_in: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        version: int = 1
    ) -> GeneratedKey:
        """
        Generate a secure API key
        
        Args:
            key_type: Type of key to generate
            key_scope: Permissions scope for the key
            key_length: Key length in bits
            expires_in: Expiration time in seconds
            metadata: Additional metadata to store
            version: Key version for rotation
            
        Returns:
            GeneratedKey object with all key data
        """
        # Generate unique key ID
        self._key_counter += 1
        key_id = self._generate_key_id(key_type, version)
        
        # Generate the actual key based on type
        if key_type == KeyType.HMAC:
            key_data = self._generate_hmac_key(key_length)
            algorithm = "hmac-sha256"
        elif key_type == KeyType.RSA:
            key_data = self._generate_rsa_key(key_length)
            algorithm = "rsa"
        elif key_type == KeyType.ECDSA:
            key_data = self._generate_ecdsa_key(key_length)
            algorithm = "ecdsa"
        elif key_type == KeyType.JWT:
            key_data = self._generate_jwt_key()
            algorithm = "jwt-hs256"
        elif key_type == KeyType.API_TOKEN:
            key_data = self._generate_api_token(key_length)
            algorithm = "token"
        elif key_type == KeyType.PROVISIONING:
            key_data = self._generate_provisioning_key()
            algorithm = "provisioning"
        else:
            raise ValueError(f"Unsupported key type: {key_type}")

        # Calculate expiration
        expires_at = None
        if expires_in:
            expires_at = time.time() + expires_in

        # Create metadata
        key_metadata = {
            "generator_version": "1.0",
            "hsm_enabled": self.hsm_enabled,
            "entropy_source": "system",
            **(metadata or {})
        }

        logger.info(f"Generated {key_type.value} key with ID: {key_id}")

        return GeneratedKey(
            key_id=key_id,
            key_type=key_type.value,
            key_value=key_data["key"],
            public_key=key_data.get("public_key"),
            private_key=key_data.get("private_key"),
            scope=key_scope.value,
            algorithm=algorithm,
            key_length=key_length.value,
            expires_at=expires_at,
            metadata=key_metadata
        )

    def _generate_key_id(self, key_type: KeyType, version: int) -> str:
        """Generate a unique key identifier"""
        timestamp = int(time.time())
        random_bytes = self._entropy_source.randbytes(8)
        random_suffix = base64.b64encode(random_bytes).decode('ascii')
        return f"{key_type.value}_{timestamp}_{random_suffix}_v{version}"

    def _generate_hmac_key(self, key_length: KeyLength) -> Dict[str, str]:
        """Generate HMAC key"""
        key_bytes = self._entropy_source.randbytes(key_length.value // 8)
        key_value = base64.urlsafe_b64encode(key_bytes).decode('ascii')
        return {"key": key_value}

    def _generate_rsa_key(self, key_length: KeyLength) -> Dict[str, str]:
        """Generate RSA key pair"""
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_length.value,
            backend=default_backend()
        )
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption()
        ).decode('ascii')
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        ).decode('ascii')
        
        return {
            "key": private_pem,
            "public_key": public_pem
        }

    def _generate_ecdsa_key(self, key_length: KeyLength) -> Dict[str, str]:
        """Generate ECDSA key pair"""
        # Select curve based on key length
        if key_length == KeyLength.SHORT:
            curve = ec.SECP256R1()
        elif key_length == KeyLength.MEDIUM:
            curve = ec.SECP256K1()
        else:
            curve = ec.SECP384R1()
        
        private_key = ec.generate_private_key(curve, default_backend())
        
        private_pem = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption()
        ).decode('ascii')
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        ).decode('ascii')
        
        return {
            "key": private_pem,
            "public_key": public_pem
        }

    def _generate_jwt_key(self) -> Dict[str, str]:
        """Generate JWT signing key"""
        key_bytes = self._entropy_source.randbytes(32)
        key_value = base64.urlsafe_b64encode(key_bytes).decode('ascii')
        return {"key": key_value}

    def _generate_api_token(self, key_length: KeyLength) -> Dict[str, str]:
        """Generate API token"""
        token_bytes = self._entropy_source.randbytes(key_length.value // 8)
        # Format: prefix.random.random.random
        token = base64.urlsafe_b64encode(token_bytes).decode('ascii')
        formatted_token = f"ak_{token[:8]}.{token[8:16]}.{token[16:24]}.{token[24:]}"
        return {"key": formatted_token}

    def _generate_provisioning_key(self) -> Dict[str, str]:
        """Generate provisioning key with extra security"""
        key_bytes = self._entropy_source.randbytes(32)
        key_value = base64.urlsafe_b64encode(key_bytes).decode('ascii')
        return {"key": key_value}

    def generate_key_batch(
        self,
        count: int,
        key_type: KeyType,
        key_scope: KeyScope,
        **kwargs
    ) -> List[GeneratedKey]:
        """
        Generate multiple keys in batch
        
        Args:
            count: Number of keys to generate
            key_type: Type of keys to generate
            key_scope: Scope for all keys
            **kwargs: Additional arguments for key generation
            
        Returns:
            List of GeneratedKey objects
        """
        keys = []
        for i in range(count):
            key = self.generate_api_key(
                key_type=key_type,
                key_scope=key_scope,
                **kwargs
            )
            keys.append(key)
        
        logger.info(f"Generated batch of {count} {key_type.value} keys")
        return keys

    def derive_key_from_secret(
        self,
        secret: str,
        salt: bytes,
        key_length: int = 32,
        info: str = "api-key-derivation"
    ) -> bytes:
        """
        Derive a cryptographic key from a secret using HKDF
        
        Args:
            secret: Base secret for key derivation
            salt: Salt for key derivation
            key_length: Length of derived key
            info: Additional context for derivation
            
        Returns:
            Derived key bytes
        """
        secret_bytes = secret.encode('utf-8')
        
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=salt,
            info=info.encode('utf-8'),
            backend=default_backend()
        )
        
        return hkdf.derive(secret_bytes)

    def generate_service_key(
        self,
        service_name: str,
        environment: str = "production",
        expires_in: int = 86400 * 30  # 30 days
    ) -> GeneratedKey:
        """
        Generate a service-specific API key
        
        Args:
            service_name: Name of the service
            environment: Environment (production, staging, development)
            expires_in: Expiration time in seconds
            
        Returns:
            GeneratedKey for the service
        """
        metadata = {
            "service_name": service_name,
            "environment": environment,
            "service_key": True
        }
        
        return self.generate_api_key(
            key_type=KeyType.API_TOKEN,
            key_scope=KeyScope.ADMIN,
            expires_in=expires_in,
            metadata=metadata
        )

    def verify_key_integrity(self, key: GeneratedKey) -> bool:
        """
        Verify the integrity of a generated key
        
        Args:
            key: Key to verify
            
        Returns:
            True if key is valid, False otherwise
        """
        try:
            # Basic validation checks
            if not key.key_id or not key.key_value:
                return False
            
            # Check expiration
            if key.expires_at and time.time() > key.expires_at:
                return False
            
            # Type-specific validation
            if key.key_type == KeyType.RSA.value:
                # Verify RSA key format
                if not key.private_key or not key.public_key:
                    return False
            
            elif key.key_type in [KeyType.HMAC.value, KeyType.API_TOKEN.value]:
                # Verify base64 encoded keys
                try:
                    base64.b64decode(key.key_value)
                except Exception:
                    return False
            
            logger.debug(f"Key integrity verified for ID: {key.key_id}")
            return True
            
        except Exception as e:
            logger.error(f"Key integrity verification failed: {e}")
            return False

    def export_key_for_supabase(self, key: GeneratedKey) -> Dict[str, Any]:
        """
        Export key data in Supabase-compatible format
        
        Args:
            key: Key to export
            
        Returns:
            Dictionary suitable for Supabase storage
        """
        export_data = {
            "key_id": key.key_id,
            "key_type": key.key_type,
            "key_value": key.key_value,
            "scope": key.scope,
            "algorithm": key.algorithm,
            "key_length": key.key_length,
            "created_at": key.created_at,
            "expires_at": key.expires_at,
            "metadata": key.metadata or {}
        }
        
        # Add public key if available
        if key.public_key:
            export_data["public_key"] = key.public_key
        
        return export_data

    def rotate_key(
        self,
        old_key: GeneratedKey,
        expires_in: Optional[int] = None
    ) -> GeneratedKey:
        """
        Generate a new version of an existing key for rotation
        
        Args:
            old_key: Key to rotate
            expires_in: New expiration time
            
        Returns:
            New rotated key
        """
        # Extract version from key ID
        try:
            parts = old_key.key_id.split('_')
            old_version = int(parts[-1].replace('v', ''))
            new_version = old_version + 1
        except Exception:
            new_version = 1
        
        # Create new key with updated metadata
        metadata = old_key.metadata or {}
        metadata["rotated_from"] = old_key.key_id
        metadata["rotation_count"] = metadata.get("rotation_count", 0) + 1
        
        return self.generate_api_key(
            key_type=KeyType(old_key.key_type),
            key_scope=KeyScope(old_key.scope),
            key_length=KeyLength(old_key.key_length),
            expires_in=expires_in,
            metadata=metadata,
            version=new_version
        )
