"""
Secure API Key Storage Module

Provides secure storage for API keys with encryption, HSM integration,
and Supabase backend support. Implements proper access controls and audit logging.
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from pathlib import Path

# Supabase imports
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logging.warning("Supabase client not available. Using local storage only.")

from key_generator import GeneratedKey, KeyType, KeyScope

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class KeyMetadata:
    """Metadata for stored keys"""
    key_id: str
    key_type: str
    scope: str
    algorithm: str
    key_length: int
    created_at: float
    last_used: Optional[float] = None
    expires_at: Optional[float] = None
    is_active: bool = True
    usage_count: int = 0
    metadata: Optional[Dict[str, Any]] = None
    rotation_history: Optional[List[str]] = None
    revoked_at: Optional[float] = None
    revocation_reason: Optional[str] = None


@dataclass
class KeyUsageEvent:
    """Record of key usage for audit trails"""
    event_id: str
    key_id: str
    action: str
    timestamp: float
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class SecureKeyStore:
    """
    Secure API key storage with encryption and access control
    
    Features:
    - AES encryption at rest
    - HSM integration ready
    - Supabase backend support
    - Comprehensive audit logging
    - Rate limiting per key
    - Automatic key expiration
    """

    def __init__(
        self,
        storage_backend: str = "local",  # or "supabase"
        encryption_key: Optional[bytes] = None,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        hsm_enabled: bool = False,
        hsm_config: Optional[Dict] = None
    ):
        """
        Initialize the key store
        
        Args:
            storage_backend: Storage backend ('local' or 'supabase')
            encryption_key: Master encryption key (32 bytes)
            supabase_url: Supabase project URL
            supabase_key: Supabase service key
            hsm_enabled: Whether to use HSM for key operations
            hsm_config: HSM configuration
        """
        self.storage_backend = storage_backend
        self.hsm_enabled = hsm_enabled
        self.hsm_config = hsm_config or {}
        
        # Initialize encryption
        if encryption_key:
            self.encryption_key = encryption_key
        else:
            # Generate from environment or use default
            self.encryption_key = self._get_or_create_encryption_key()
        
        self.fernet = Fernet(self.encryption_key)
        
        # Initialize storage backend
        if storage_backend == "supabase" and SUPABASE_AVAILABLE:
            self._init_supabase(supabase_url, supabase_key)
        else:
            self._init_local_storage()
        
        # Rate limiting storage
        self.rate_limits: Dict[str, Dict] = {}
        
        logger.info(f"Key store initialized (backend: {storage_backend}, HSM: {hsm_enabled})")

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key from environment"""
        key_env = os.environ.get("KEY_STORE_ENCRYPTION_KEY")
        
        if key_env:
            # Decode base64 encoded key
            key_bytes = base64.b64decode(key_env)
            if len(key_bytes) == 32:
                return key_bytes
        
        # Generate new key and log warning (in production, always use env var)
        key = Fernet.generate_key()
        logger.warning("Generated new encryption key. Set KEY_STORE_ENCRYPTION_KEY in production!")
        return key

    def _init_local_storage(self):
        """Initialize local file-based storage"""
        self.storage_dir = Path("/workspace/code/security/key_management/storage")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.keys_file = self.storage_dir / "keys.json.enc"
        self.metadata_file = self.storage_dir / "metadata.json"
        self.audit_file = self.storage_dir / "audit.jsonl"

    def _init_supabase(self, supabase_url: str, supabase_key: str):
        """Initialize Supabase storage"""
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase client not installed")
        
        self.supabase_client: Client = create_client(supabase_url, supabase_key)
        
        # Create tables if they don't exist
        self._ensure_supabase_tables()
        
        logger.info("Supabase storage initialized")

    def _ensure_supabase_tables(self):
        """Ensure required tables exist in Supabase"""
        # This would typically be done via migrations
        # For now, we'll assume tables exist
        pass

    def store_key(self, key: GeneratedKey, encrypt: bool = True) -> bool:
        """
        Store an API key securely
        
        Args:
            key: GeneratedKey to store
            encrypt: Whether to encrypt the key value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare key data for storage
            if encrypt and self.fernet:
                encrypted_value = self.fernet.encrypt(key.key_value.encode()).decode()
            else:
                encrypted_value = key.key_value
            
            # Create metadata
            metadata = KeyMetadata(
                key_id=key.key_id,
                key_type=key.key_type,
                scope=key.scope,
                algorithm=key.algorithm,
                key_length=key.key_length,
                created_at=key.created_at,
                expires_at=key.expires_at,
                metadata=key.metadata or {}
            )
            
            # Store based on backend
            if self.storage_backend == "supabase":
                success = self._store_key_supabase(key.key_id, encrypted_value, metadata)
            else:
                success = self._store_key_local(key.key_id, encrypted_value, metadata)
            
            if success:
                logger.info(f"Key stored successfully: {key.key_id}")
                self._log_audit_event("key_created", key.key_id, True)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to store key: {e}")
            self._log_audit_event("key_created", key.key_id, False, str(e))
            return False

    def _store_key_local(self, key_id: str, encrypted_value: str, metadata: KeyMetadata) -> bool:
        """Store key in local file storage"""
        try:
            # Load existing keys
            keys_data = {}
            if self.keys_file.exists():
                with open(self.keys_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self.fernet.decrypt(encrypted_data).decode()
                keys_data = json.loads(decrypted_data)
            
            # Add new key
            keys_data[key_id] = {
                "value": encrypted_value,
                "stored_at": time.time()
            }
            
            # Save encrypted keys
            encrypted_data = self.fernet.encrypt(json.dumps(keys_data).encode())
            with open(self.keys_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Save metadata separately (not encrypted for quick lookups)
            metadata_data = {}
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    metadata_data = json.load(f)
            
            metadata_data[key_id] = asdict(metadata)
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata_data, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Local storage error: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _store_key_supabase(self, key_id: str, encrypted_value: str, metadata: KeyMetadata) -> bool:
        """Store key in Supabase"""
        try:
            # Store key value
            key_data = {
                "key_id": key_id,
                "encrypted_value": encrypted_value,
                "stored_at": time.time()
            }
            
            result = self.supabase_client.table("api_keys").insert(key_data).execute()
            
            # Store metadata
            metadata_result = self.supabase_client.table("api_key_metadata").insert(
                asdict(metadata)
            ).execute()
            
            return bool(result.data and metadata_result.data)
            
        except Exception as e:
            logger.error(f"Supabase storage error: {e}")
            return False

    def retrieve_key(self, key_id: str, decrypt: bool = True) -> Optional[GeneratedKey]:
        """
        Retrieve a stored API key
        
        Args:
            key_id: ID of the key to retrieve
            decrypt: Whether to decrypt the key value
            
        Returns:
            GeneratedKey or None if not found
        """
        try:
            # Get metadata first
            metadata = self.get_key_metadata(key_id)
            if not metadata:
                logger.warning(f"Key metadata not found: {key_id}")
                return None
            
            # Check if key is expired
            if metadata.expires_at and time.time() > metadata.expires_at:
                logger.warning(f"Key expired: {key_id}")
                self._log_audit_event("key_retrieved", key_id, False, "Key expired")
                return None
            
            # Get encrypted value
            if self.storage_backend == "supabase":
                key_data = self._get_key_data_supabase(key_id)
            else:
                key_data = self._get_key_data_local(key_id)
            
            if not key_data:
                logger.warning(f"Key data not found: {key_id}")
                return None
            
            # Decrypt if needed
            key_value = key_data["value"]
            if decrypt and self.fernet:
                try:
                    key_value = self.fernet.decrypt(key_value.encode()).decode()
                except Exception as e:
                    logger.error(f"Failed to decrypt key: {e}")
                    return None
            
            # Log usage
            self._log_audit_event("key_retrieved", key_id, True)
            self._update_usage_stats(key_id)
            
            return GeneratedKey(
                key_id=metadata.key_id,
                key_type=metadata.key_type,
                key_value=key_value,
                scope=metadata.scope,
                algorithm=metadata.algorithm,
                key_length=metadata.key_length,
                created_at=metadata.created_at,
                expires_at=metadata.expires_at,
                metadata=metadata.metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve key {key_id}: {e}")
            self._log_audit_event("key_retrieved", key_id, False, str(e))
            return None

    def _get_key_data_local(self, key_id: str) -> Optional[Dict]:
        """Get key data from local storage"""
        try:
            if not self.keys_file.exists():
                return None
            
            with open(self.keys_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data).decode()
            keys_data = json.loads(decrypted_data)
            
            return keys_data.get(key_id)
            
        except Exception as e:
            logger.error(f"Local key retrieval error: {e}")
            return None

    def _get_key_data_supabase(self, key_id: str) -> Optional[Dict]:
        """Get key data from Supabase"""
        try:
            result = self.supabase_client.table("api_keys").select("*").eq(
                "key_id", key_id
            ).execute()
            
            if result.data:
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Supabase key retrieval error: {e}")
            return None

    def get_key_metadata(self, key_id: str) -> Optional[KeyMetadata]:
        """Get metadata for a key"""
        try:
            if self.storage_backend == "supabase":
                result = self.supabase_client.table("api_key_metadata").select("*").eq(
                    "key_id", key_id
                ).execute()
                
                if result.data:
                    data = result.data[0]
                    return KeyMetadata(**data)
            else:
                if self.metadata_file.exists():
                    with open(self.metadata_file, 'r') as f:
                        metadata_data = json.load(f)
                    
                    if key_id in metadata_data:
                        return KeyMetadata(**metadata_data[key_id])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get metadata for {key_id}: {e}")
            return None

    def list_keys(
        self,
        key_type: Optional[KeyType] = None,
        scope: Optional[KeyScope] = None,
        active_only: bool = True
    ) -> List[KeyMetadata]:
        """List all stored keys with optional filtering"""
        try:
            keys = []
            
            if self.storage_backend == "supabase":
                query = self.supabase_client.table("api_key_metadata").select("*")
                
                if key_type:
                    query = query.eq("key_type", key_type.value)
                if scope:
                    query = query.eq("scope", scope.value)
                if active_only:
                    query = query.eq("is_active", True)
                
                result = query.execute()
                
                if result.data:
                    keys = [KeyMetadata(**item) for item in result.data]
            
            else:
                if self.metadata_file.exists():
                    with open(self.metadata_file, 'r') as f:
                        metadata_data = json.load(f)
                    
                    for key_id, data in metadata_data.items():
                        metadata = KeyMetadata(**data)
                        
                        # Apply filters
                        if key_type and metadata.key_type != key_type.value:
                            continue
                        if scope and metadata.scope != scope.value:
                            continue
                        if active_only and not metadata.is_active:
                            continue
                        
                        keys.append(metadata)
            
            logger.info(f"Listed {len(keys)} keys")
            return keys
            
        except Exception as e:
            logger.error(f"Failed to list keys: {e}")
            return []

    def revoke_key(self, key_id: str, reason: str = "manual_revocation") -> bool:
        """
        Revoke an API key
        
        Args:
            key_id: ID of the key to revoke
            reason: Reason for revocation
            
        Returns:
            True if successful
        """
        try:
            if self.storage_backend == "supabase":
                result = self.supabase_client.table("api_key_metadata").update({
                    "is_active": False,
                    "revoked_at": time.time(),
                    "revocation_reason": reason
                }).eq("key_id", key_id).execute()
            else:
                # Update local metadata
                if self.metadata_file.exists():
                    with open(self.metadata_file, 'r') as f:
                        metadata_data = json.load(f)
                    
                    if key_id in metadata_data:
                        metadata_data[key_id]["is_active"] = False
                        metadata_data[key_id]["revoked_at"] = time.time()
                        metadata_data[key_id]["revocation_reason"] = reason
                        
                        with open(self.metadata_file, 'w') as f:
                            json.dump(metadata_data, f, indent=2)
                        
                        result = {"data": [metadata_data[key_id]]}
                    else:
                        result = None
            
            if result:
                logger.info(f"Key revoked: {key_id} (reason: {reason})")
                self._log_audit_event("key_revoked", key_id, True, reason)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to revoke key {key_id}: {e}")
            self._log_audit_event("key_revoked", key_id, False, str(e))
            return False

    def verify_key(self, key_id: str) -> Tuple[bool, str]:
        """
        Verify a key is valid and active
        
        Args:
            key_id: ID of the key to verify
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Get metadata
            metadata = self.get_key_metadata(key_id)
            if not metadata:
                return False, "Key not found"
            
            # Check if active
            if not metadata.is_active:
                return False, "Key is revoked"
            
            # Check expiration
            if metadata.expires_at and time.time() > metadata.expires_at:
                return False, "Key expired"
            
            # Check rate limits
            if self._check_rate_limit(key_id):
                return False, "Rate limit exceeded"
            
            return True, "Key is valid"
            
        except Exception as e:
            logger.error(f"Key verification error: {e}")
            return False, str(e)

    def _check_rate_limit(self, key_id: str, limit: int = 1000, window: int = 3600) -> bool:
        """
        Check if key has exceeded rate limit
        
        Args:
            key_id: Key ID to check
            limit: Maximum requests in window
            window: Time window in seconds
            
        Returns:
            True if limit exceeded
        """
        now = time.time()
        
        if key_id not in self.rate_limits:
            self.rate_limits[key_id] = {"count": 0, "window_start": now}
            return False
        
        rate_data = self.rate_limits[key_id]
        
        # Reset window if expired
        if now - rate_data["window_start"] > window:
            rate_data["count"] = 0
            rate_data["window_start"] = now
        
        # Check limit
        if rate_data["count"] >= limit:
            return True
        
        rate_data["count"] += 1
        return False

    def _update_usage_stats(self, key_id: str):
        """Update usage statistics for a key"""
        try:
            now = time.time()
            
            if self.storage_backend == "supabase":
                self.supabase_client.table("api_key_metadata").update({
                    "last_used": now,
                    "usage_count": "usage_count + 1"
                }).eq("key_id", key_id).execute()
            else:
                # Update local metadata
                if self.metadata_file.exists():
                    with open(self.metadata_file, 'r') as f:
                        metadata_data = json.load(f)
                    
                    if key_id in metadata_data:
                        metadata_data[key_id]["last_used"] = now
                        metadata_data[key_id]["usage_count"] = metadata_data[key_id].get("usage_count", 0) + 1
                        
                        with open(self.metadata_file, 'w') as f:
                            json.dump(metadata_data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to update usage stats: {e}")

    def _log_audit_event(
        self,
        action: str,
        key_id: str,
        success: bool,
        message: Optional[str] = None
    ):
        """Log an audit event"""
        try:
            event = KeyUsageEvent(
                event_id=f"{action}_{key_id}_{int(time.time())}",
                key_id=key_id,
                action=action,
                timestamp=time.time(),
                success=success,
                error_message=message
            )
            
            if self.storage_backend == "supabase":
                self.supabase_client.table("api_key_audit_log").insert(
                    asdict(event)
                ).execute()
            else:
                # Append to local audit file
                with open(self.audit_file, 'a') as f:
                    f.write(json.dumps(asdict(event)) + '\n')
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")

    def get_audit_log(
        self,
        key_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[KeyUsageEvent]:
        """Retrieve audit log entries"""
        try:
            events = []
            
            if self.storage_backend == "supabase":
                query = self.supabase_client.table("api_key_audit_log").select("*")
                
                if key_id:
                    query = query.eq("key_id", key_id)
                if action:
                    query = query.eq("action", action)
                
                result = query.limit(limit).order("timestamp", desc=True).execute()
                
                if result.data:
                    events = [KeyUsageEvent(**item) for item in result.data]
            
            else:
                # Read from local audit file
                if self.audit_file.exists():
                    with open(self.audit_file, 'r') as f:
                        for line in f:
                            event_data = json.loads(line.strip())
                            event = KeyUsageEvent(**event_data)
                            
                            # Apply filters
                            if key_id and event.key_id != key_id:
                                continue
                            if action and event.action != action:
                                continue
                            
                            events.append(event)
                
                # Sort by timestamp descending and limit
                events = sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to retrieve audit log: {e}")
            return []

    def cleanup_expired_keys(self) -> int:
        """Clean up expired keys from storage"""
        try:
            now = time.time()
            cleaned_count = 0
            
            if self.storage_backend == "supabase":
                result = self.supabase_client.table("api_key_metadata").update({
                    "is_active": False,
                    "cleaned_at": now
                }).lt("expires_at", now).eq("is_active", True).execute()
                
                if result.data:
                    cleaned_count = len(result.data)
            else:
                # Clean up local storage
                if self.metadata_file.exists():
                    with open(self.metadata_file, 'r') as f:
                        metadata_data = json.load(f)
                    
                    for key_id, data in list(metadata_data.items()):
                        if data.get("expires_at") and data["expires_at"] < now and data.get("is_active", True):
                            data["is_active"] = False
                            data["cleaned_at"] = now
                            cleaned_count += 1
                    
                    with open(self.metadata_file, 'w') as f:
                        json.dump(metadata_data, f, indent=2)
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired keys")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired keys: {e}")
            return 0

    def export_keys_for_backup(self, output_file: str) -> bool:
        """Export keys for backup (without sensitive data)"""
        try:
            export_data = {
                "exported_at": time.time(),
                "version": "1.0",
                "keys": []
            }
            
            keys = self.list_keys(active_only=False)
            
            for key_metadata in keys:
                # Export metadata only (no actual key values)
                export_data["keys"].append(asdict(key_metadata))
            
            if self.storage_backend == "supabase":
                # Store in Supabase storage
                result = self.supabase_client.table("key_exports").insert(export_data).execute()
                return bool(result.data)
            else:
                # Save to local file
                with open(output_file, 'w') as f:
                    json.dump(export_data, f, indent=2)
                return True
            
        except Exception as e:
            logger.error(f"Failed to export keys: {e}")
            return False
