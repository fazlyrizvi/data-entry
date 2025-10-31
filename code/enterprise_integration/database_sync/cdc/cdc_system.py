"""
Change Data Capture (CDC) System

Provides universal CDC functionality for multiple database types.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
from abc import ABC, abstractmethod

from ..core.change_event import ChangeEvent, EventBatch, ChangeType, EventStatus
from ..core.sync_manager import SyncManager, SyncConfiguration, SyncMode
from ..core.error_recovery import ErrorRecovery, ErrorEvent


class CDCType(Enum):
    """Types of CDC mechanisms."""
    LOGICAL_DECODING = "LOGICAL_DECODING"
    BINLOG_REPLICATION = "BINLOG_REPLICATION"
    CHANGE_STREAMS = "CHANGE_STREAMS"
    TRIGGER_BASED = "TRIGGER_BASED"
    POLLING = "POLLING"
    WEBHOOKS = "WEBHOOKS"


class CDCStatus(Enum):
    """CDC system status."""
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    RECONNECTING = "RECONNECTING"


@dataclass
class CDCConfiguration:
    """Configuration for CDC system."""
    cdc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    source_database_id: str = ""
    target_database_id: str = ""
    
    # CDC settings
    cdc_type: CDCType = CDCType.LOGICAL_DECODING
    tables: List[str] = field(default_factory=list)
    exclude_tables: List[str] = field(default_factory=list)
    
    # Performance settings
    batch_size: int = 100
    poll_interval: float = 1.0
    max_lag_seconds: int = 60
    buffer_size: int = 1000
    
    # Error handling
    retry_attempts: int = 3
    retry_delay: float = 5.0
    dead_letter_queue_enabled: bool = True
    
    # Filter settings
    schema_filter: Optional[List[str]] = None
    operation_filter: Optional[List[ChangeType]] = None
    custom_filters: Optional[Dict[str, Any]] = None
    
    # Transformation settings
    transformations: Optional[Dict[str, Callable]] = None
    field_mappings: Optional[Dict[str, str]] = None
    
    # Monitoring
    heartbeat_interval: int = 30
    metrics_enabled: bool = True
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_started_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cdc_id': self.cdc_id,
            'name': self.name,
            'source_database_id': self.source_database_id,
            'target_database_id': self.target_database_id,
            'cdc_type': self.cdc_type.value,
            'tables': self.tables,
            'exclude_tables': self.exclude_tables,
            'batch_size': self.batch_size,
            'poll_interval': self.poll_interval,
            'max_lag_seconds': self.max_lag_seconds,
            'buffer_size': self.buffer_size,
            'retry_attempts': self.retry_attempts,
            'retry_delay': self.retry_delay,
            'dead_letter_queue_enabled': self.dead_letter_queue_enabled,
            'schema_filter': self.schema_filter,
            'operation_filter': self.operation_filter,
            'custom_filters': self.custom_filters,
            'transformations': self.transformations,
            'field_mappings': self.field_mappings,
            'heartbeat_interval': self.heartbeat_interval,
            'metrics_enabled': self.metrics_enabled,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_started_at': self.last_started_at.isoformat() if self.last_started_at else None,
            'metadata': self.metadata
        }


@dataclass
class CDCStatistics:
    """CDC system statistics."""
    cdc_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Event statistics
    total_events_captured: int = 0
    events_insert: int = 0
    events_update: int = 0
    events_delete: int = 0
    events_filtered: int = 0
    events_transformed: int = 0
    events_sent: int = 0
    events_failed: int = 0
    
    # Performance statistics
    average_latency_ms: float = 0.0
    throughput_events_per_second: float = 0.0
    max_lag_detected_ms: float = 0.0
    buffer_utilization: float = 0.0
    
    # Error statistics
    connection_errors: int = 0
    parsing_errors: int = 0
    transformation_errors: int = 0
    network_errors: int = 0
    
    # Status
    status: CDCStatus = CDCStatus.RUNNING
    last_heartbeat: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cdc_id': self.cdc_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_events_captured': self.total_events_captured,
            'events_insert': self.events_insert,
            'events_update': self.events_update,
            'events_delete': self.events_delete,
            'events_filtered': self.events_filtered,
            'events_transformed': self.events_transformed,
            'events_sent': self.events_sent,
            'events_failed': self.events_failed,
            'average_latency_ms': self.average_latency_ms,
            'throughput_events_per_second': self.throughput_events_per_second,
            'max_lag_detected_ms': self.max_lag_detected_ms,
            'buffer_utilization': self.buffer_utilization,
            'connection_errors': self.connection_errors,
            'parsing_errors': self.parsing_errors,
            'transformation_errors': self.transformation_errors,
            'network_errors': self.network_errors,
            'status': self.status.value,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }


class BaseCDCProvider(ABC):
    """Abstract base class for CDC providers."""
    
    def __init__(self, config: CDCConfiguration):
        self.config = config
        self.status = CDCStatus.STOPPED
        self.last_position = None
        self.event_buffer: asyncio.Queue = asyncio.Queue(maxsize=config.buffer_size)
        
        # Statistics
        self.statistics = CDCStatistics(
            cdc_id=config.cdc_id,
            start_time=datetime.now()
        )
        
        # Event handlers
        self.event_handlers: List[Callable] = []
        self.error_handlers: List[Callable] = []
        
        # Background tasks
        self.main_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.monitor_task: Optional[asyncio.Task] = None
        
        self.logger = logging.getLogger(f"{__name__}.{config.cdc_id}")
    
    @abstractmethod
    async def start_capture(self) -> bool:
        """Start CDC capture."""
        pass
    
    @abstractmethod
    async def stop_capture(self) -> bool:
        """Stop CDC capture."""
        pass
    
    @abstractmethod
    async def get_current_position(self) -> Any:
        """Get current CDC position."""
        pass
    
    @abstractmethod
    async def set_position(self, position: Any) -> bool:
        """Set CDC position."""
        pass
    
    async def add_event_handler(self, handler: Callable):
        """Add an event handler."""
        self.event_handlers.append(handler)
    
    async def remove_event_handler(self, handler: Callable):
        """Remove an event handler."""
        if handler in self.event_handlers:
            self.event_handlers.remove(handler)
    
    async def add_error_handler(self, handler: Callable):
        """Add an error handler."""
        self.error_handlers.append(handler)
    
    async def get_statistics(self) -> CDCStatistics:
        """Get CDC statistics."""
        return self.statistics
    
    async def get_status(self) -> Dict[str, Any]:
        """Get CDC status."""
        return {
            'cdc_id': self.config.cdc_id,
            'status': self.status.value,
            'last_heartbeat': self.statistics.last_heartbeat.isoformat() if self.statistics.last_heartbeat else None,
            'total_events_captured': self.statistics.total_events_captured,
            'buffer_size': self.event_buffer.qsize(),
            'buffer_capacity': self.event_buffer.maxsize,
            'current_position': str(self.last_position) if self.last_position else None
        }


class PostgreSQLCDCProvider(BaseCDCProvider):
    """PostgreSQL CDC provider using logical decoding."""
    
    async def start_capture(self) -> bool:
        """Start PostgreSQL CDC capture."""
        try:
            self.status = CDCStatus.STARTING
            
            # Initialize logical decoding replication slot
            await self._initialize_replication_slot()
            
            # Start background tasks
            self.main_task = asyncio.create_task(self._main_capture_loop())
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            
            self.status = CDCStatus.RUNNING
            self.statistics.last_heartbeat = datetime.now()
            
            self.logger.info(f"Started PostgreSQL CDC for {self.config.name}")
            return True
            
        except Exception as e:
            self.status = CDCStatus.ERROR
            self.logger.error(f"Failed to start PostgreSQL CDC: {e}")
            return False
    
    async def stop_capture(self) -> bool:
        """Stop PostgreSQL CDC capture."""
        try:
            self.status = CDCStatus.STOPPED
            
            # Cancel background tasks
            for task in [self.main_task, self.heartbeat_task, self.monitor_task]:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Drop replication slot
            await self._cleanup_replication_slot()
            
            self.logger.info(f"Stopped PostgreSQL CDC for {self.config.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop PostgreSQL CDC: {e}")
            return False
    
    async def get_current_position(self) -> Any:
        """Get current PostgreSQL CDC position."""
        try:
            # Get current WAL LSN
            return await self._get_current_lsn()
        except Exception as e:
            self.logger.error(f"Failed to get current position: {e}")
            return None
    
    async def set_position(self, position: Any) -> bool:
        """Set PostgreSQL CDC position."""
        try:
            self.last_position = position
            return True
        except Exception as e:
            self.logger.error(f"Failed to set position: {e}")
            return False
    
    async def _initialize_replication_slot(self):
        """Initialize PostgreSQL replication slot."""
        # This would involve creating a replication slot and setting up logical decoding
        # Implementation depends on the specific PostgreSQL setup
        pass
    
    async def _cleanup_replication_slot(self):
        """Cleanup PostgreSQL replication slot."""
        # Drop the replication slot
        pass
    
    async def _get_current_lsn(self) -> str:
        """Get current WAL LSN."""
        # Query PostgreSQL for current LSN
        return "0/123456"  # Placeholder
    
    async def _main_capture_loop(self):
        """Main CDC capture loop."""
        while self.status == CDCStatus.RUNNING:
            try:
                # Read changes from replication slot
                changes = await self._read_replication_changes()
                
                for change in changes:
                    # Process change
                    await self._process_change(change)
                
                # Wait for next poll
                await asyncio.sleep(self.config.poll_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in capture loop: {e}")
                self.statistics.connection_errors += 1
                await asyncio.sleep(self.config.retry_delay)
    
    async def _read_replication_changes(self) -> List[Dict[str, Any]]:
        """Read changes from replication slot."""
        # This would read from pg_logical_slot_get_changes or similar
        changes = []
        
        # Placeholder implementation
        if self.last_position:
            # Read changes since last position
            pass
        
        return changes
    
    async def _process_change(self, change: Dict[str, Any]):
        """Process a single change."""
        try:
            # Convert change to ChangeEvent
            event = self._change_to_event(change)
            
            # Apply filters
            if not await self._apply_filters(event):
                self.statistics.events_filtered += 1
                return
            
            # Apply transformations
            await self._apply_transformations(event)
            
            # Add to buffer
            try:
                await asyncio.wait_for(
                    self.event_buffer.put(event), 
                    timeout=1.0
                )
                self.statistics.total_events_captured += 1
                
                # Update event type statistics
                if event.event_type == ChangeType.INSERT:
                    self.statistics.events_insert += 1
                elif event.event_type == ChangeType.UPDATE:
                    self.statistics.events_update += 1
                elif event.event_type == ChangeType.DELETE:
                    self.statistics.events_delete += 1
                
            except asyncio.TimeoutError:
                self.logger.warning("Event buffer is full, dropping event")
                self.statistics.events_failed += 1
            
        except Exception as e:
            self.logger.error(f"Failed to process change: {e}")
            self.statistics.parsing_errors += 1
    
    def _change_to_event(self, change: Dict[str, Any]) -> ChangeEvent:
        """Convert a replication change to ChangeEvent."""
        operation_type_map = {
            'I': ChangeType.INSERT,
            'U': ChangeType.UPDATE,
            'D': ChangeType.DELETE
        }
        
        return ChangeEvent(
            event_type=operation_type_map.get(change.get('operation'), ChangeType.UPDATE),
            source_table=change.get('table_name', ''),
            target_table=change.get('table_name', ''),
            primary_key=change.get('primary_key'),
            old_values=change.get('old_values'),
            new_values=change.get('new_values'),
            timestamp=datetime.now()
        )
    
    async def _apply_filters(self, event: ChangeEvent) -> bool:
        """Apply CDC filters."""
        # Table filter
        if self.config.tables and event.source_table not in self.config.tables:
            return False
        
        # Exclude table filter
        if event.source_table in self.config.exclude_tables:
            return False
        
        # Operation filter
        if (self.config.operation_filter and 
            event.event_type not in self.config.operation_filter):
            return False
        
        return True
    
    async def _apply_transformations(self, event: ChangeEvent):
        """Apply data transformations."""
        if not self.config.transformations:
            return
        
        try:
            # Apply field mappings
            if self.config.field_mappings and event.new_values:
                mapped_values = {}
                for source_field, target_field in self.config.field_mappings.items():
                    if source_field in event.new_values:
                        mapped_values[target_field] = event.new_values[source_field]
                
                event.new_values = mapped_values
            
            # Apply custom transformations
            for field_name, transform_func in self.config.transformations.items():
                if event.new_values and field_name in event.new_values:
                    try:
                        event.new_values[field_name] = await transform_func(
                            event.new_values[field_name]
                        )
                        self.statistics.events_transformed += 1
                    except Exception as e:
                        self.logger.warning(f"Transformation failed for {field_name}: {e}")
            
        except Exception as e:
            self.logger.error(f"Failed to apply transformations: {e}")
            self.statistics.transformation_errors += 1
    
    async def _heartbeat_loop(self):
        """Heartbeat loop."""
        while self.status == CDCStatus.RUNNING:
            self.statistics.last_heartbeat = datetime.now()
            await asyncio.sleep(self.config.heartbeat_interval)
    
    async def _monitor_loop(self):
        """Monitor loop for health checks."""
        while self.status == CDCStatus.RUNNING:
            try:
                # Check lag
                lag = await self._calculate_lag()
                if lag > self.config.max_lag_seconds:
                    self.logger.warning(f"CDC lag detected: {lag} seconds")
                
                # Update buffer utilization
                self.statistics.buffer_utilization = (
                    self.event_buffer.qsize() / self.event_buffer.maxsize
                )
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Monitor error: {e}")
                await asyncio.sleep(30)
    
    async def _calculate_lag(self) -> float:
        """Calculate CDC lag in seconds."""
        # This would calculate the difference between current time and latest change time
        return 0.0  # Placeholder


class MongoDBCDCProvider(BaseCDCProvider):
    """MongoDB CDC provider using change streams."""
    
    async def start_capture(self) -> bool:
        """Start MongoDB CDC capture."""
        try:
            self.status = CDCStatus.STARTING
            
            # Initialize change streams for each table
            await self._initialize_change_streams()
            
            # Start background tasks
            self.main_task = asyncio.create_task(self._main_capture_loop())
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            
            self.status = CDCStatus.RUNNING
            self.statistics.last_heartbeat = datetime.now()
            
            self.logger.info(f"Started MongoDB CDC for {self.config.name}")
            return True
            
        except Exception as e:
            self.status = CDCStatus.ERROR
            self.logger.error(f"Failed to start MongoDB CDC: {e}")
            return False
    
    async def stop_capture(self) -> bool:
        """Stop MongoDB CDC capture."""
        try:
            self.status = CDCStatus.STOPPED
            
            # Cancel background tasks
            for task in [self.main_task, self.heartbeat_task, self.monitor_task]:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Close change streams
            await self._cleanup_change_streams()
            
            self.logger.info(f"Stopped MongoDB CDC for {self.config.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop MongoDB CDC: {e}")
            return False
    
    async def get_current_position(self) -> Any:
        """Get current MongoDB CDC position."""
        # Return resume token or timestamp
        return {'timestamp': datetime.now()}  # Placeholder
    
    async def set_position(self, position: Any) -> bool:
        """Set MongoDB CDC position."""
        # Set resume token for change streams
        return True
    
    async def _initialize_change_streams(self):
        """Initialize change streams for tables."""
        # Set up change streams for each table
        pass
    
    async def _cleanup_change_streams(self):
        """Close all change streams."""
        # Close change streams
        pass
    
    async def _main_capture_loop(self):
        """Main CDC capture loop."""
        while self.status == CDCStatus.RUNNING:
            try:
                # Process change stream events
                events = await self._read_change_stream_events()
                
                for event in events:
                    await self._process_change(event)
                
                await asyncio.sleep(self.config.poll_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in capture loop: {e}")
                await asyncio.sleep(self.config.retry_delay)
    
    async def _read_change_stream_events(self) -> List[ChangeEvent]:
        """Read events from change streams."""
        # This would read from MongoDB change streams
        events = []
        
        # Placeholder implementation
        # In practice, this would iterate over change streams and yield events
        
        return events
    
    async def _process_change(self, change: ChangeEvent):
        """Process a single change."""
        # Similar to PostgreSQL provider but for change streams
        try:
            # Apply filters
            if not await self._apply_filters(change):
                self.statistics.events_filtered += 1
                return
            
            # Apply transformations
            await self._apply_transformations(change)
            
            # Add to buffer
            try:
                await asyncio.wait_for(
                    self.event_buffer.put(change), 
                    timeout=1.0
                )
                self.statistics.total_events_captured += 1
                
                # Update event type statistics
                if change.event_type == ChangeType.INSERT:
                    self.statistics.events_insert += 1
                elif change.event_type == ChangeType.UPDATE:
                    self.statistics.events_update += 1
                elif change.event_type == ChangeType.DELETE:
                    self.statistics.events_delete += 1
                
            except asyncio.TimeoutError:
                self.logger.warning("Event buffer is full, dropping event")
                self.statistics.events_failed += 1
            
        except Exception as e:
            self.logger.error(f"Failed to process change: {e}")
            self.statistics.parsing_errors += 1
    
    async def _apply_filters(self, event: ChangeEvent) -> bool:
        """Apply CDC filters."""
        # Similar to PostgreSQL provider
        if self.config.tables and event.source_table not in self.config.tables:
            return False
        
        if event.source_table in self.config.exclude_tables:
            return False
        
        if (self.config.operation_filter and 
            event.event_type not in self.config.operation_filter):
            return False
        
        return True
    
    async def _apply_transformations(self, event: ChangeEvent):
        """Apply data transformations."""
        # Similar to PostgreSQL provider
        pass
    
    async def _heartbeat_loop(self):
        """Heartbeat loop."""
        while self.status == CDCStatus.RUNNING:
            self.statistics.last_heartbeat = datetime.now()
            await asyncio.sleep(self.config.heartbeat_interval)
    
    async def _monitor_loop(self):
        """Monitor loop for health checks."""
        while self.status == CDCStatus.RUNNING:
            try:
                # Check lag
                lag = await self._calculate_lag()
                if lag > self.config.max_lag_seconds:
                    self.logger.warning(f"CDC lag detected: {lag} seconds")
                
                # Update buffer utilization
                self.statistics.buffer_utilization = (
                    self.event_buffer.qsize() / self.event_buffer.maxsize
                )
                
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Monitor error: {e}")
                await asyncio.sleep(30)
    
    async def _calculate_lag(self) -> float:
        """Calculate CDC lag in seconds."""
        return 0.0  # Placeholder


class MySQLCDCProvider(BaseCDCProvider):
    """MySQL CDC provider using binlog replication."""
    
    async def start_capture(self) -> bool:
        """Start MySQL CDC capture."""
        try:
            self.status = CDCStatus.STARTING
            
            # Initialize binlog reader
            await self._initialize_binlog_reader()
            
            # Start background tasks
            self.main_task = asyncio.create_task(self._main_capture_loop())
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            
            self.status = CDCStatus.RUNNING
            self.statistics.last_heartbeat = datetime.now()
            
            self.logger.info(f"Started MySQL CDC for {self.config.name}")
            return True
            
        except Exception as e:
            self.status = CDCStatus.ERROR
            self.logger.error(f"Failed to start MySQL CDC: {e}")
            return False
    
    async def stop_capture(self) -> bool:
        """Stop MySQL CDC capture."""
        try:
            self.status = CDCStatus.STOPPED
            
            # Cancel background tasks
            for task in [self.main_task, self.heartbeat_task, self.monitor_task]:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Cleanup binlog reader
            await self._cleanup_binlog_reader()
            
            self.logger.info(f"Stopped MySQL CDC for {self.config.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop MySQL CDC: {e}")
            return False
    
    async def get_current_position(self) -> Any:
        """Get current MySQL CDC position."""
        return {'file': 'mysql-bin.000001', 'position': 1234}  # Placeholder
    
    async def set_position(self, position: Any) -> bool:
        """Set MySQL CDC position."""
        # Set binlog position
        return True
    
    async def _initialize_binlog_reader(self):
        """Initialize binlog reader."""
        # Set up binlog reading
        pass
    
    async def _cleanup_binlog_reader(self):
        """Cleanup binlog reader."""
        pass
    
    async def _main_capture_loop(self):
        """Main CDC capture loop."""
        while self.status == CDCStatus.RUNNING:
            try:
                # Read binlog events
                events = await self._read_binlog_events()
                
                for event in events:
                    await self._process_change(event)
                
                await asyncio.sleep(self.config.poll_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in capture loop: {e}")
                await asyncio.sleep(self.config.retry_delay)
    
    async def _read_binlog_events(self) -> List[ChangeEvent]:
        """Read events from binlog."""
        # This would read from MySQL binlog
        events = []
        
        # Placeholder implementation
        # In practice, this would use a binlog reader library
        
        return events
    
    async def _process_change(self, change: ChangeEvent):
        """Process a single change."""
        # Similar to other providers
        pass
    
    async def _apply_filters(self, event: ChangeEvent) -> bool:
        """Apply CDC filters."""
        # Similar to other providers
        return True
    
    async def _apply_transformations(self, event: ChangeEvent):
        """Apply data transformations."""
        # Similar to other providers
        pass
    
    async def _heartbeat_loop(self):
        """Heartbeat loop."""
        while self.status == CDCStatus.RUNNING:
            self.statistics.last_heartbeat = datetime.now()
            await asyncio.sleep(self.config.heartbeat_interval)
    
    async def _monitor_loop(self):
        """Monitor loop for health checks."""
        while self.status == CDCStatus.RUNNING:
            try:
                # Check lag
                lag = await self._calculate_lag()
                if lag > self.config.max_lag_seconds:
                    self.logger.warning(f"CDC lag detected: {lag} seconds")
                
                # Update buffer utilization
                self.statistics.buffer_utilization = (
                    self.event_buffer.qsize() / self.event_buffer.maxsize
                )
                
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Monitor error: {e}")
                await asyncio.sleep(30)
    
    async def _calculate_lag(self) -> float:
        """Calculate CDC lag in seconds."""
        return 0.0  # Placeholder


class CDCSystem:
    """Universal CDC system coordinator."""
    
    def __init__(self, error_recovery: Optional[ErrorRecovery] = None):
        self.error_recovery = error_recovery or ErrorRecovery()
        
        # CDC providers by configuration
        self.providers: Dict[str, BaseCDCProvider] = {}
        
        # Event queues for downstream processing
        self.event_queues: Dict[str, asyncio.Queue] = {}
        
        # Background tasks
        self.dispatcher_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.global_statistics = {}
        
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the CDC system."""
        await self.error_recovery.start()
        
        # Start event dispatcher
        self.dispatcher_task = asyncio.create_task(self._event_dispatcher_loop())
        
        self.logger.info("CDC system started")
    
    async def stop(self):
        """Stop the CDC system."""
        # Stop all providers
        for provider in self.providers.values():
            await provider.stop_capture()
        
        # Cancel dispatcher task
        if self.dispatcher_task:
            self.dispatcher_task.cancel()
            try:
                await self.dispatcher_task
            except asyncio.CancelledError:
                pass
        
        await self.error_recovery.stop()
        
        self.logger.info("CDC system stopped")
    
    async def create_cdc_configuration(self, config: CDCConfiguration) -> str:
        """Create a new CDC configuration."""
        # Create appropriate provider based on CDC type
        if config.cdc_type == CDCType.LOGICAL_DECODING:
            provider = PostgreSQLCDCProvider(config)
        elif config.cdc_type == CDCType.CHANGE_STREAMS:
            provider = MongoDBCDCProvider(config)
        elif config.cdc_type == CDCType.BINLOG_REPLICATION:
            provider = MySQLCDCProvider(config)
        else:
            raise ValueError(f"Unsupported CDC type: {config.cdc_type}")
        
        self.providers[config.cdc_id] = provider
        
        # Create event queue
        self.event_queues[config.cdc_id] = asyncio.Queue(maxsize=config.buffer_size)
        
        return config.cdc_id
    
    async def start_cdc(self, cdc_id: str) -> bool:
        """Start CDC for a configuration."""
        if cdc_id not in self.providers:
            raise ValueError(f"CDC configuration {cdc_id} not found")
        
        provider = self.providers[cdc_id]
        success = await provider.start_capture()
        
        if success:
            self.logger.info(f"Started CDC: {cdc_id}")
        else:
            self.logger.error(f"Failed to start CDC: {cdc_id}")
        
        return success
    
    async def stop_cdc(self, cdc_id: str) -> bool:
        """Stop CDC for a configuration."""
        if cdc_id not in self.providers:
            return False
        
        provider = self.providers[cdc_id]
        success = await provider.stop_capture()
        
        if success:
            self.logger.info(f"Stopped CDC: {cdc_id}")
        else:
            self.logger.error(f"Failed to stop CDC: {cdc_id}")
        
        return success
    
    async def get_cdc_status(self, cdc_id: str) -> Optional[Dict[str, Any]]:
        """Get CDC status."""
        if cdc_id not in self.providers:
            return None
        
        return await self.providers[cdc_id].get_status()
    
    async def get_all_cdc_status(self) -> List[Dict[str, Any]]:
        """Get status of all CDC configurations."""
        return [await self.get_cdc_status(cdc_id) for cdc_id in self.providers.keys()]
    
    async def get_cdc_statistics(self, cdc_id: str) -> Optional[CDCStatistics]:
        """Get CDC statistics."""
        if cdc_id not in self.providers:
            return None
        
        return await self.providers[cdc_id].get_statistics()
    
    async def get_global_statistics(self) -> Dict[str, Any]:
        """Get global CDC statistics."""
        total_events = 0
        total_errors = 0
        
        for provider in self.providers.values():
            stats = await provider.get_statistics()
            total_events += stats.total_events_captured
            total_errors += (stats.connection_errors + stats.parsing_errors + 
                           stats.transformation_errors + stats.network_errors)
        
        return {
            'total_cdc_configurations': len(self.providers),
            'total_events_captured': total_events,
            'total_errors': total_errors,
            'active_configurations': len([p for p in self.providers.values() 
                                        if p.status == CDCStatus.RUNNING]),
            'error_recovery_stats': self.error_recovery.get_error_statistics()
        }
    
    async def _event_dispatcher_loop(self):
        """Background task to dispatch events to downstream processors."""
        while True:
            try:
                # Collect events from all provider buffers
                events = await self._collect_events()
                
                # Dispatch events to processors
                await self._dispatch_events(events)
                
                await asyncio.sleep(0.1)  # Small delay
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Event dispatcher error: {e}")
                await asyncio.sleep(1)
    
    async def _collect_events(self) -> List[ChangeEvent]:
        """Collect events from all provider buffers."""
        events = []
        
        for cdc_id, provider in self.providers.items():
            try:
                # Collect events from provider buffer (non-blocking)
                batch_events = []
                try:
                    while len(batch_events) < 10:  # Limit batch size
                        event = await asyncio.wait_for(
                            provider.event_buffer.get(), 
                            timeout=0.1
                        )
                        batch_events.append(event)
                except asyncio.TimeoutError:
                    pass  # No more events in buffer
                
                events.extend(batch_events)
                
            except Exception as e:
                self.logger.error(f"Error collecting events from {cdc_id}: {e}")
        
        return events
    
    async def _dispatch_events(self, events: List[ChangeEvent]):
        """Dispatch events to downstream processors."""
        if not events:
            return
        
        # Group events by CDC configuration
        events_by_cdc = {}
        for event in events:
            # Extract CDC ID from event metadata if available
            cdc_id = getattr(event, 'cdc_id', 'unknown')
            if cdc_id not in events_by_cdc:
                events_by_cdc[cdc_id] = []
            events_by_cdc[cdc_id].append(event)
        
        # Send events to appropriate processors
        for cdc_id, cdc_events in events_by_cdc.items():
            if cdc_id in self.event_queues:
                for event in cdc_events:
                    try:
                        await asyncio.wait_for(
                            self.event_queues[cdc_id].put(event),
                            timeout=0.1
                        )
                    except asyncio.TimeoutError:
                        self.logger.warning(f"Event queue full for CDC {cdc_id}")


class UniversalCDCSystem(CDCSystem):
    """Universal CDC system with enhanced features."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aggregation_pipeline = None
        self.routing_rules: Dict[str, Any] = {}
    
    async def setup_event_routing(self, rules: Dict[str, Any]):
        """Setup event routing rules."""
        self.routing_rules = rules
    
    async def setup_aggregation_pipeline(self, pipeline: Callable):
        """Setup event aggregation pipeline."""
        self.aggregation_pipeline = pipeline
    
    async def add_custom_provider(self, provider_id: str, provider: BaseCDCProvider):
        """Add a custom CDC provider."""
        self.providers[provider_id] = provider
        self.event_queues[provider_id] = asyncio.Queue()
    
    async def get_cdc_metrics(self) -> Dict[str, Any]:
        """Get detailed CDC metrics."""
        metrics = {}
        
        for cdc_id, provider in self.providers.items():
            try:
                status = await provider.get_status()
                stats = await provider.get_statistics()
                
                metrics[cdc_id] = {
                    'status': status,
                    'statistics': stats.to_dict(),
                    'health_score': self._calculate_health_score(stats)
                }
            except Exception as e:
                metrics[cdc_id] = {'error': str(e)}
        
        return metrics
    
    def _calculate_health_score(self, stats: CDCStatistics) -> float:
        """Calculate a health score for CDC provider."""
        if stats.total_events_captured == 0:
            return 1.0  # No data, assume healthy
        
        error_rate = (
            (stats.connection_errors + stats.parsing_errors + 
             stats.transformation_errors + stats.network_errors) /
            stats.total_events_captured
        )
        
        return max(0.0, 1.0 - error_rate)
