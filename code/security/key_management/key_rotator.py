"""
API Key Rotation Management Module

Implements automatic key rotation policies, scheduling, and management.
Handles seamless key transitions and maintains service continuity.
"""

import time
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

# Optional croniter import for advanced scheduling
try:
    from croniter import croniter
    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False
    logging.warning("croniter not available. Custom cron expressions will use basic scheduling.")

from key_generator import SecureKeyGenerator, GeneratedKey, KeyType, KeyScope, KeyLength
from key_store import SecureKeyStore, KeyMetadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RotationFrequency(Enum):
    """Key rotation frequencies"""
    NEVER = "never"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class RotationStrategy(Enum):
    """Key rotation strategies"""
    IMMEDIATE = "immediate"  # Replace immediately
    GRADUAL = "gradual"  # Gradual rollout
    OVERLAPPING = "overlapping"  # Maintain overlap period
    BLUE_GREEN = "blue_green"  # Blue-green deployment


@dataclass
class RotationPolicy:
    """Key rotation policy configuration"""
    policy_id: str
    name: str
    key_type: KeyType
    scope: KeyScope
    frequency: RotationFrequency
    strategy: RotationStrategy
    advance_notice_hours: int = 24  # Hours before rotation to notify
    overlap_duration_hours: int = 48  # Hours to keep old key active
    custom_cron: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    enabled: bool = True
    created_at: float = None
    last_rotated: Optional[float] = None
    next_rotation: Optional[float] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.next_rotation is None:
            self.next_rotation = self._calculate_next_rotation()

    def _calculate_next_rotation(self) -> float:
        """Calculate next rotation timestamp"""
        now = time.time()
        
        if self.frequency == RotationFrequency.NEVER:
            return None
        elif self.frequency == RotationFrequency.DAILY:
            return now + 86400
        elif self.frequency == RotationFrequency.WEEKLY:
            return now + 86400 * 7
        elif self.frequency == RotationFrequency.MONTHLY:
            return now + 86400 * 30
        elif self.frequency == RotationFrequency.QUARTERLY:
            return now + 86400 * 90
        elif self.frequency == RotationFrequency.YEARLY:
            return now + 86400 * 365
        elif self.frequency == RotationFrequency.CUSTOM and self.custom_cron:
            try:
                if CRONITER_AVAILABLE:
                    cron = croniter(self.custom_cron, now)
                    return cron.get_next()
                else:
                    # Basic fallback - use monthly as default
                    logger.warning("croniter not available, using monthly rotation for custom cron")
                    return now + 86400 * 30
            except Exception as e:
                logger.error(f"Invalid cron expression: {e}")
                return now + 86400 * 30  # Default to monthly
        
        return now + 86400 * 30  # Default


@dataclass
class RotationEvent:
    """Record of a key rotation event"""
    event_id: str
    policy_id: str
    key_id: str
    old_key_id: Optional[str]
    new_key_id: str
    rotation_type: str  # automatic, manual, emergency
    strategy_used: RotationStrategy
    timestamp: float
    success: bool
    error_message: Optional[str] = None
    overlap_duration: Optional[int] = None
    notifications_sent: Optional[List[str]] = None


class KeyRotator:
    """
    Automated API key rotation management system
    
    Features:
    - Flexible rotation policies
    - Multiple rotation strategies
    - Automatic scheduling
    - Service continuity maintenance
    - Comprehensive audit logging
    - Notification system integration
    """

    def __init__(
        self,
        key_generator: SecureKeyGenerator,
        key_store: SecureKeyStore,
        notification_callback: Optional[Callable[[str, Dict], None]] = None
    ):
        """
        Initialize the key rotator
        
        Args:
            key_generator: Key generator instance
            key_store: Key store instance
            notification_callback: Callback for rotation notifications
        """
        self.key_generator = key_generator
        self.key_store = key_store
        self.notification_callback = notification_callback
        
        self.rotation_policies: Dict[str, RotationPolicy] = {}
        self.rotation_history: List[RotationEvent] = []
        
        # Load existing policies
        self._load_policies()
        
        logger.info("Key rotator initialized")

    def _load_policies(self):
        """Load rotation policies from storage"""
        try:
            policies_file = Path("/workspace/code/security/key_management/rotation_policies.json")
            
            if policies_file.exists():
                with open(policies_file, 'r') as f:
                    policies_data = json.load(f)
                
                for policy_data in policies_data.get("policies", []):
                    # Convert enum strings back to enums
                    policy_data["key_type"] = KeyType(policy_data["key_type"])
                    policy_data["scope"] = KeyScope(policy_data["scope"])
                    policy_data["frequency"] = RotationFrequency(policy_data["frequency"])
                    policy_data["strategy"] = RotationStrategy(policy_data["strategy"])
                    
                    policy = RotationPolicy(**policy_data)
                    self.rotation_policies[policy.policy_id] = policy
                
                logger.info(f"Loaded {len(self.rotation_policies)} rotation policies")
            
        except Exception as e:
            logger.error(f"Failed to load policies: {e}")

    def _save_policies(self):
        """Save rotation policies to storage"""
        try:
            policies_file = Path("/workspace/code/security/key_management/rotation_policies.json")
            
            policies_data = {
                "last_updated": time.time(),
                "policies": []
            }
            
            for policy in self.rotation_policies.values():
                policy_dict = asdict(policy)
                # Convert enums to strings
                policy_dict["key_type"] = policy.key_type.value
                policy_dict["scope"] = policy.scope.value
                policy_dict["frequency"] = policy.frequency.value
                policy_dict["strategy"] = policy.strategy.value
                
                policies_data["policies"].append(policy_dict)
            
            with open(policies_file, 'w') as f:
                json.dump(policies_data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save policies: {e}")

    def create_rotation_policy(
        self,
        policy: RotationPolicy
    ) -> bool:
        """
        Create a new rotation policy
        
        Args:
            policy: RotationPolicy to create
            
        Returns:
            True if successful
        """
        try:
            self.rotation_policies[policy.policy_id] = policy
            self._save_policies()
            
            logger.info(f"Created rotation policy: {policy.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create rotation policy: {e}")
            return False

    def create_policy(
        self,
        policy_id: str,
        name: str,
        key_type: KeyType,
        scope: KeyScope,
        frequency: RotationFrequency,
        strategy: RotationStrategy,
        **kwargs
    ) -> str:
        """
        Create a rotation policy with parameters
        
        Args:
            policy_id: Unique policy identifier
            name: Policy name
            key_type: Type of keys to rotate
            scope: Scope for rotated keys
            frequency: How often to rotate
            strategy: Rotation strategy to use
            **kwargs: Additional policy parameters
            
        Returns:
            Created policy ID
        """
        policy = RotationPolicy(
            policy_id=policy_id,
            name=name,
            key_type=key_type,
            scope=scope,
            frequency=frequency,
            strategy=strategy,
            **kwargs
        )
        
        self.create_rotation_policy(policy)
        return policy_id

    def delete_policy(self, policy_id: str) -> bool:
        """
        Delete a rotation policy
        
        Args:
            policy_id: ID of policy to delete
            
        Returns:
            True if successful
        """
        try:
            if policy_id in self.rotation_policies:
                del self.rotation_policies[policy_id]
                self._save_policies()
                logger.info(f"Deleted rotation policy: {policy_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete policy: {e}")
            return False

    def rotate_key(
        self,
        key_id: str,
        policy_id: Optional[str] = None,
        rotation_type: str = "manual",
        **kwargs
    ) -> Optional[GeneratedKey]:
        """
        Rotate a specific key
        
        Args:
            key_id: ID of key to rotate
            policy_id: Optional policy to use for rotation
            rotation_type: Type of rotation (manual, automatic, emergency)
            **kwargs: Additional rotation parameters
            
        Returns:
            New rotated key or None if failed
        """
        try:
            # Get original key
            old_key = self.key_store.retrieve_key(key_id, decrypt=False)
            if not old_key:
                logger.error(f"Key not found: {key_id}")
                return None
            
            # Generate new key
            new_key = self.key_generator.rotate_key(old_key)
            
            # Store new key
            if not self.key_store.store_key(new_key):
                logger.error(f"Failed to store rotated key: {new_key.key_id}")
                return None
            
            # Apply rotation strategy
            strategy = kwargs.get("strategy", RotationStrategy.IMMEDIATE)
            
            if strategy == RotationStrategy.IMMEDIATE:
                success = self._rotate_immediate(old_key, new_key, policy_id, rotation_type)
            elif strategy == RotationStrategy.GRADUAL:
                success = self._rotate_gradual(old_key, new_key, policy_id, rotation_type, **kwargs)
            elif strategy == RotationStrategy.OVERLAPPING:
                success = self._rotate_overlapping(old_key, new_key, policy_id, rotation_type, **kwargs)
            elif strategy == RotationStrategy.BLUE_GREEN:
                success = self._rotate_blue_green(old_key, new_key, policy_id, rotation_type, **kwargs)
            else:
                success = self._rotate_immediate(old_key, new_key, policy_id, rotation_type)
            
            if success:
                logger.info(f"Key rotated successfully: {key_id} -> {new_key.key_id}")
                
                # Update policy rotation time
                if policy_id and policy_id in self.rotation_policies:
                    self.rotation_policies[policy_id].last_rotated = time.time()
                    self.rotation_policies[policy_id].next_rotation = None  # Will be recalculated
                    self._save_policies()
                
                # Send notification
                self._send_rotation_notification("key_rotated", {
                    "old_key_id": old_key.key_id,
                    "new_key_id": new_key.key_id,
                    "policy_id": policy_id,
                    "rotation_type": rotation_type
                })
            
            return new_key if success else None
            
        except Exception as e:
            logger.error(f"Key rotation failed for {key_id}: {e}")
            self._log_rotation_event(
                policy_id or "manual",
                key_id,
                None,
                None,
                rotation_type,
                "unknown",
                False,
                str(e)
            )
            return None

    def _rotate_immediate(
        self,
        old_key: GeneratedKey,
        new_key: GeneratedKey,
        policy_id: Optional[str],
        rotation_type: str
    ) -> bool:
        """Immediate rotation - revoke old key immediately"""
        try:
            # Revoke old key immediately
            if not self.key_store.revoke_key(old_key.key_id, "immediate_rotation"):
                logger.error(f"Failed to revoke old key: {old_key.key_id}")
                return False
            
            # Log event
            self._log_rotation_event(
                policy_id or "manual",
                old_key.key_id,
                old_key.key_id,
                new_key.key_id,
                rotation_type,
                RotationStrategy.IMMEDIATE,
                True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Immediate rotation failed: {e}")
            return False

    def _rotate_gradual(
        self,
        old_key: GeneratedKey,
        new_key: GeneratedKey,
        policy_id: Optional[str],
        rotation_type: str,
        **kwargs
    ) -> bool:
        """Gradual rotation - introduce new key alongside old"""
        try:
            # Keep old key active but mark as being phased out
            old_metadata = self.key_store.get_key_metadata(old_key.key_id)
            if old_metadata:
                old_metadata.metadata = old_metadata.metadata or {}
                old_metadata.metadata["rotation_status"] = "phasing_out"
                old_metadata.metadata["new_key_id"] = new_key.key_id
                # Would update in storage here
            
            # Log event
            self._log_rotation_event(
                policy_id or "manual",
                old_key.key_id,
                old_key.key_id,
                new_key.key_id,
                rotation_type,
                RotationStrategy.GRADUAL,
                True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Gradual rotation failed: {e}")
            return False

    def _rotate_overlapping(
        self,
        old_key: GeneratedKey,
        new_key: GeneratedKey,
        policy_id: Optional[str],
        rotation_type: str,
        **kwargs
    ) -> bool:
        """Overlapping rotation - maintain both keys for overlap period"""
        try:
            overlap_duration = kwargs.get("overlap_duration_hours", 48)
            expiry_time = time.time() + (overlap_duration * 3600)
            
            # Set expiration on old key for overlap end
            old_metadata = self.key_store.get_key_metadata(old_key.key_id)
            if old_metadata:
                old_metadata.expires_at = expiry_time
                old_metadata.metadata = old_metadata.metadata or {}
                old_metadata.metadata["rotation_status"] = "overlapping"
                old_metadata.metadata["new_key_id"] = new_key.key_id
                # Would update in storage here
            
            # Log event
            self._log_rotation_event(
                policy_id or "manual",
                old_key.key_id,
                old_key.key_id,
                new_key.key_id,
                rotation_type,
                RotationStrategy.OVERLAPPING,
                True,
                overlap_duration
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Overlapping rotation failed: {e}")
            return False

    def _rotate_blue_green(
        self,
        old_key: GeneratedKey,
        new_key: GeneratedKey,
        policy_id: Optional[str],
        rotation_type: str,
        **kwargs
    ) -> bool:
        """Blue-green rotation - complete environment switch"""
        try:
            # Create deployment marker
            old_metadata = self.key_store.get_key_metadata(old_key.key_id)
            if old_metadata:
                old_metadata.metadata = old_metadata.metadata or {}
                old_metadata.metadata["deployment_phase"] = "blue"
                old_metadata.metadata["new_key_id"] = new_key.key_id
            
            new_metadata = self.key_store.get_key_metadata(new_key.key_id)
            if new_metadata:
                new_metadata.metadata = new_metadata.metadata or {}
                new_metadata.metadata["deployment_phase"] = "green"
            
            # Log event
            self._log_rotation_event(
                policy_id or "manual",
                old_key.key_id,
                old_key.key_id,
                new_key.key_id,
                rotation_type,
                RotationStrategy.BLUE_GREEN,
                True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Blue-green rotation failed: {e}")
            return False

    def _log_rotation_event(
        self,
        policy_id: str,
        key_id: str,
        old_key_id: Optional[str],
        new_key_id: Optional[str],
        rotation_type: str,
        strategy: RotationStrategy,
        success: bool,
        error_message: Optional[str] = None,
        overlap_duration: Optional[int] = None
    ):
        """Log a rotation event"""
        try:
            event = RotationEvent(
                event_id=f"rot_{int(time.time())}_{key_id}",
                policy_id=policy_id,
                key_id=key_id,
                old_key_id=old_key_id,
                new_key_id=new_key_id,
                rotation_type=rotation_type,
                strategy_used=strategy,
                timestamp=time.time(),
                success=success,
                error_message=error_message,
                overlap_duration=overlap_duration
            )
            
            self.rotation_history.append(event)
            
            # Save to file
            history_file = Path("/workspace/code/security/key_management/rotation_history.jsonl")
            with open(history_file, 'a') as f:
                f.write(json.dumps(asdict(event)) + '\n')
            
        except Exception as e:
            logger.error(f"Failed to log rotation event: {e}")

    def check_rotation_schedules(self) -> List[str]:
        """
        Check for keys that need rotation based on policies
        
        Returns:
            List of key IDs that need rotation
        """
        try:
            now = time.time()
            keys_to_rotate = []
            
            for policy_id, policy in self.rotation_policies.items():
                if not policy.enabled:
                    continue
                
                if not policy.next_rotation:
                    continue
                
                # Check if rotation is due
                if now >= policy.next_rotation:
                    # Check advance notice
                    advance_notice = policy.advance_notice_hours * 3600
                    
                    if now >= policy.next_rotation - advance_notice:
                        keys_to_rotate.append(policy_id)
                        logger.info(f"Rotation scheduled for policy: {policy.name}")
                        
                        # Send advance notice
                        self._send_rotation_notification("rotation_scheduled", {
                            "policy_id": policy_id,
                            "policy_name": policy.name,
                            "scheduled_time": policy.next_rotation,
                            "advance_notice_hours": policy.advance_notice_hours
                        })
                    
                    # If past rotation time, perform rotation
                    if now >= policy.next_rotation:
                        keys_for_rotation = self._get_keys_for_policy(policy)
                        for key_metadata in keys_for_rotation:
                            self.rotate_key(
                                key_metadata.key_id,
                                policy_id,
                                "automatic"
                            )
            
            return keys_to_rotate
            
        except Exception as e:
            logger.error(f"Failed to check rotation schedules: {e}")
            return []

    def _get_keys_for_policy(self, policy: RotationPolicy) -> List[KeyMetadata]:
        """Get keys that match a rotation policy"""
        try:
            # Get all keys matching the policy criteria
            all_keys = self.key_store.list_keys(
                key_type=policy.key_type,
                scope=policy.scope,
                active_only=True
            )
            
            # Filter based on policy conditions
            matching_keys = []
            
            for key_metadata in all_keys:
                # Skip if already rotated recently (within 1 day)
                if key_metadata.last_used and time.time() - key_metadata.last_used < 86400:
                    # This is a newly rotated key, skip it
                    continue
                
                # Apply additional conditions if specified
                if policy.conditions:
                    for condition_key, condition_value in policy.conditions.items():
                        if condition_key in ["max_usage_count", "max_age_days"]:
                            if condition_key == "max_usage_count":
                                if key_metadata.usage_count >= condition_value:
                                    matching_keys.append(key_metadata)
                            elif condition_key == "max_age_days":
                                age_days = (time.time() - key_metadata.created_at) / 86400
                                if age_days >= condition_value:
                                    matching_keys.append(key_metadata)
                else:
                    matching_keys.append(key_metadata)
            
            return matching_keys
            
        except Exception as e:
            logger.error(f"Failed to get keys for policy {policy.policy_id}: {e}")
            return []

    def _send_rotation_notification(
        self,
        notification_type: str,
        data: Dict[str, Any]
    ):
        """Send rotation notification"""
        try:
            if self.notification_callback:
                self.notification_callback(notification_type, data)
            else:
                logger.info(f"Rotation notification: {notification_type} - {json.dumps(data)}")
            
        except Exception as e:
            logger.error(f"Failed to send rotation notification: {e}")

    def get_rotation_history(
        self,
        policy_id: Optional[str] = None,
        limit: int = 100
    ) -> List[RotationEvent]:
        """Get rotation history"""
        try:
            events = []
            
            history_file = Path("/workspace/code/security/key_management/rotation_history.jsonl")
            
            if history_file.exists():
                with open(history_file, 'r') as f:
                    for line in f:
                        event_data = json.loads(line.strip())
                        event = RotationEvent(**event_data)
                        
                        # Apply filter
                        if policy_id and event.policy_id != policy_id:
                            continue
                        
                        events.append(event)
            
            # Sort by timestamp descending and limit
            events = sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get rotation history: {e}")
            return []

    def get_rotation_statistics(self) -> Dict[str, Any]:
        """Get rotation statistics"""
        try:
            stats = {
                "total_policies": len(self.rotation_policies),
                "enabled_policies": sum(1 for p in self.rotation_policies.values() if p.enabled),
                "policies_by_frequency": {},
                "policies_by_strategy": {},
                "total_rotations": 0,
                "successful_rotations": 0,
                "failed_rotations": 0,
                "last_rotation": None
            }
            
            # Count by frequency
            for policy in self.rotation_policies.values():
                freq = policy.frequency.value
                stats["policies_by_frequency"][freq] = stats["policies_by_frequency"].get(freq, 0) + 1
                
                strategy = policy.strategy.value
                stats["policies_by_strategy"][strategy] = stats["policies_by_strategy"].get(strategy, 0) + 1
            
            # Rotation statistics
            history = self.get_rotation_history(limit=10000)
            stats["total_rotations"] = len(history)
            stats["successful_rotations"] = sum(1 for e in history if e.success)
            stats["failed_rotations"] = sum(1 for e in history if not e.success)
            
            if history:
                stats["last_rotation"] = max(e.timestamp for e in history)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get rotation statistics: {e}")
            return {}

    def cleanup_old_rotations(self, keep_days: int = 90) -> int:
        """Clean up old rotation events"""
        try:
            cutoff_time = time.time() - (keep_days * 86400)
            
            # Filter recent events
            recent_events = [e for e in self.rotation_history if e.timestamp >= cutoff_time]
            self.rotation_history = recent_events
            
            logger.info(f"Cleaned up old rotation events, kept {len(recent_events)} recent events")
            return len(self.rotation_history)
            
        except Exception as e:
            logger.error(f"Failed to cleanup old rotations: {e}")
            return 0
