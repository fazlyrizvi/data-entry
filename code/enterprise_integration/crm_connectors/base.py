"""
Base CRM Connector

Provides common functionality for all CRM connectors including:
- OAuth 2.0 authentication
- Rate limiting
- Retry mechanisms
- Data mapping
- Synchronization capabilities
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
import logging
import asyncio
import json
import time
from dataclasses import dataclass, field
import hashlib
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncDirection(Enum):
    """Synchronization direction enumeration"""
    PUSH = "push"           # Send data to CRM
    PULL = "pull"           # Fetch data from CRM
    BIDIRECTIONAL = "bidirectional"  # Both directions


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    SOURCE_WINS = "source_wins"       # Source system wins
    TARGET_WINS = "target_wins"       # Target system wins
    MANUAL = "manual"                 # Manual resolution required
    TIMESTAMP = "timestamp"           # Most recent timestamp wins
    CUSTOM = "custom"                 # Custom resolution logic


@dataclass
class SyncConfig:
    """Configuration for synchronization operations"""
    direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    conflict_resolution: ConflictResolution = ConflictResolution.TIMESTAMP
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0
    custom_resolver: Optional[Callable] = None
    field_mappings: Dict[str, str] = field(default_factory=dict)
    include_metadata: bool = False
    parallel_operations: int = 1
    timeout: int = 300


@dataclass
class SyncRecord:
    """Represents a single record for synchronization"""
    id: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    checksum: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.checksum is None:
            self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum for data integrity verification"""
        content = json.dumps(self.data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class SyncResult:
    """Result of synchronization operation"""
    success: bool
    records_processed: int = 0
    records_succeeded: int = 0
    records_failed: int = 0
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0


class RateLimiter:
    """Rate limiter implementation for API calls"""
    
    def __init__(self, max_calls: int, time_window: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds (default: 60)
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self._lock = threading.Lock()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        with self._lock:
            now = time.time()
            
            # Remove old calls outside the time window
            self.calls = [call_time for call_time in self.calls 
                         if now - call_time < self.time_window]
            
            # If we're at the limit, wait
            if len(self.calls) >= self.max_calls:
                sleep_time = self.time_window - (now - self.calls[0])
                if sleep_time > 0:
                    logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                    time.sleep(sleep_time)
                    self.wait_if_needed()  # Recursively check again
            else:
                self.calls.append(now)


class RetryManager:
    """Manages retry logic with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.max_retries:
                    logger.error(f"Max retries reached. Last error: {str(e)}")
                    raise
                
                delay = min(
                    self.base_delay * (self.backoff_factor ** attempt),
                    self.max_delay
                )
                logger.warning(f"Attempt {attempt + 1} failed. Retrying in {delay:.2f}s. Error: {str(e)}")
                await asyncio.sleep(delay)
        
        raise last_exception


class DataMapper:
    """Handles data mapping between internal and external formats"""
    
    def __init__(self, mappings: Dict[str, str] = None):
        """
        Initialize data mapper
        
        Args:
            mappings: Field mapping dictionary {internal_field: external_field}
        """
        self.mappings = mappings or {}
        self.reverse_mappings = {v: k for k, v in self.mappings.items()}
    
    def map_to_external(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map internal field names to external CRM field names"""
        return {
            self.mappings.get(key, key): value
            for key, value in data.items()
        }
    
    def map_to_internal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map external CRM field names to internal field names"""
        return {
            self.reverse_mappings.get(key, key): value
            for key, value in data.items()
        }
    
    def add_mapping(self, internal: str, external: str):
        """Add a field mapping"""
        self.mappings[internal] = external
        self.reverse_mappings[external] = internal
    
    def remove_mapping(self, internal: str):
        """Remove a field mapping"""
        if internal in self.mappings:
            external = self.mappings[internal]
            del self.mappings[internal]
            del self.reverse_mappings[external]


class BaseCRMConnector(ABC):
    """Base class for all CRM connectors"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize connector
        
        Args:
            config: Configuration dictionary containing credentials and settings
        """
        self.config = config
        self.rate_limiter = None
        self.retry_manager = None
        self.data_mapper = None
        self.auth_token = None
        self.auth_token_expiry = None
        self.session = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize connector components"""
        # Initialize rate limiter
        rate_limit = self.config.get('rate_limit', {})
        self.rate_limiter = RateLimiter(
            max_calls=rate_limit.get('max_calls', 100),
            time_window=rate_limit.get('time_window', 60)
        )
        
        # Initialize retry manager
        retry_config = self.config.get('retry', {})
        self.retry_manager = RetryManager(
            max_retries=retry_config.get('max_retries', 3),
            base_delay=retry_config.get('base_delay', 1.0),
            max_delay=retry_config.get('max_delay', 60.0),
            backoff_factor=retry_config.get('backoff_factor', 2.0)
        )
        
        # Initialize data mapper
        field_mappings = self.config.get('field_mappings', {})
        self.data_mapper = DataMapper(field_mappings)
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the CRM system using OAuth 2.0"""
        pass
    
    @abstractmethod
    async def create(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in the CRM"""
        pass
    
    @abstractmethod
    async def read(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Read a single record from the CRM"""
        pass
    
    @abstractmethod
    async def update(self, entity_type: str, entity_id: str, 
                     data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record in the CRM"""
        pass
    
    @abstractmethod
    async def delete(self, entity_type: str, entity_id: str) -> bool:
        """Delete a record from the CRM"""
        pass
    
    @abstractmethod
    async def query(self, entity_type: str, filters: Dict[str, Any], 
                    fields: List[str] = None, limit: int = None) -> List[Dict[str, Any]]:
        """Query records from the CRM with optional filters"""
        pass
    
    async def bulk_create(self, entity_type: str, records: List[Dict[str, Any]], 
                          batch_size: int = 100) -> List[Dict[str, Any]]:
        """Create multiple records in batches"""
        results = []
        batch_size = min(batch_size, self.config.get('batch_size', 100))
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_results = []
            
            for record in batch:
                try:
                    result = await self.create(entity_type, record)
                    batch_results.append(result)
                except Exception as e:
                    logger.error(f"Failed to create record in batch: {str(e)}")
                    batch_results.append({'error': str(e), 'record': record})
            
            results.extend(batch_results)
            logger.info(f"Processed batch {i//batch_size + 1}, {len(batch)} records")
        
        return results
    
    async def bulk_update(self, entity_type: str, updates: List[Dict[str, Any]], 
                          batch_size: int = 100) -> List[Dict[str, Any]]:
        """Update multiple records in batches"""
        results = []
        batch_size = min(batch_size, self.config.get('batch_size', 100))
        
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            batch_results = []
            
            for update in batch:
                try:
                    entity_id = update.pop('id')
                    result = await self.update(entity_type, entity_id, update)
                    batch_results.append(result)
                except Exception as e:
                    logger.error(f"Failed to update record in batch: {str(e)}")
                    batch_results.append({'error': str(e), 'update': update})
            
            results.extend(batch_results)
            logger.info(f"Processed batch {i//batch_size + 1}, {len(batch)} updates")
        
        return results
    
    def _apply_rate_limit(self):
        """Apply rate limiting"""
        if self.rate_limiter:
            self.rate_limiter.wait_if_needed()
    
    async def _execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic and rate limiting"""
        self._apply_rate_limit()
        return await self.retry_manager.execute_with_retry(func, *args, **kwargs)
    
    def _sync_records(self, source_records: List[SyncRecord], 
                     target_records: List[SyncRecord],
                     config: SyncConfig) -> SyncResult:
        """Synchronize records between source and target"""
        start_time = time.time()
        result = SyncResult(success=False)
        
        try:
            # Build lookup dictionaries for efficient comparison
            source_lookup = {r.id: r for r in source_records}
            target_lookup = {r.id: r for r in target_records}
            
            # Process records based on sync direction
            if config.direction in [SyncDirection.PUSH, SyncDirection.BIDIRECTIONAL]:
                for record in source_records:
                    if record.id not in target_lookup:
                        # New record - create
                        result.records_succeeded += 1
                    else:
                        # Existing record - check for conflicts
                        target_record = target_lookup[record.id]
                        if self._has_conflict(record, target_record):
                            if not self._resolve_conflict(record, target_record, config):
                                result.conflicts.append({
                                    'record_id': record.id,
                                    'source': record.data,
                                    'target': target_record.data
                                })
                                continue
                        result.records_succeeded += 1
                    
                    result.records_processed += 1
            
            if config.direction in [SyncDirection.PULL, SyncDirection.BIDIRECTIONAL]:
                for record in target_records:
                    if record.id not in source_lookup:
                        # Record exists in target but not in source
                        result.records_succeeded += 1
                    result.records_processed += 1
            
            result.success = True
            result.execution_time = time.time() - start_time
            
        except Exception as e:
            result.errors.append(str(e))
            result.execution_time = time.time() - start_time
            logger.error(f"Synchronization failed: {str(e)}")
        
        return result
    
    def _has_conflict(self, source: SyncRecord, target: SyncRecord) -> bool:
        """Check if records have conflicts"""
        return source.checksum != target.checksum
    
    def _resolve_conflict(self, source: SyncRecord, target: SyncRecord, 
                         config: SyncConfig) -> bool:
        """Resolve conflicts between source and target records"""
        if config.conflict_resolution == ConflictResolution.SOURCE_WINS:
            return True
        elif config.conflict_resolution == ConflictResolution.TARGET_WINS:
            return False
        elif config.conflict_resolution == ConflictResolution.TIMESTAMP:
            return source.timestamp >= target.timestamp
        elif config.conflict_resolution == ConflictResolution.CUSTOM and config.custom_resolver:
            return config.custom_resolver(source, target)
        else:  # MANUAL or other unsupported modes
            return False
    
    def create_sync_records(self, records: List[Dict[str, Any]]) -> List[SyncRecord]:
        """Convert plain records to SyncRecord objects"""
        sync_records = []
        for record in records:
            record_id = record.get('id') or record.get('Id') or hashlib.md5(
                json.dumps(record, sort_keys=True, default=str).encode()
            ).hexdigest()[:8]
            sync_records.append(SyncRecord(
                id=record_id,
                data=record
            ))
        return sync_records
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the connection to the CRM"""
        try:
            await self.authenticate()
            return {
                'success': True,
                'message': 'Connection successful',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection failed: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @abstractmethod
    def get_supported_entities(self) -> List[str]:
        """Get list of supported entity types"""
        pass
    
    @abstractmethod
    def get_entity_schema(self, entity_type: str) -> Dict[str, Any]:
        """Get schema information for an entity type"""
        pass
    
    def close(self):
        """Close any open connections"""
        if self.session:
            self.session.close()
        logger.info("Connector closed")
