"""
Synchronization Manager

Orchestrates the entire database synchronization process.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
from concurrent.futures import ThreadPoolExecutor

from .change_event import ChangeEvent, EventBatch, ChangeType, EventStatus
from .conflict_resolver import ConflictResolver, ConflictInfo, ResolutionResult, ConflictStrategy
from .transaction_manager import TransactionManager, DistributedTransaction
from .error_recovery import ErrorRecovery, ErrorEvent, RecoveryStrategy


class SyncMode(Enum):
    """Synchronization modes."""
    REAL_TIME = "REAL_TIME"
    BATCH = "BATCH"
    SCHEDULED = "SCHEDULED"
    MANUAL = "MANUAL"


class SyncDirection(Enum):
    """Synchronization directions."""
    BIDIRECTIONAL = "BIDIRECTIONAL"
    SOURCE_TO_TARGET = "SOURCE_TO_TARGET"
    TARGET_TO_SOURCE = "TARGET_TO_SOURCE"


class SyncStatus(Enum):
    """Synchronization status."""
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    COMPLETED = "COMPLETED"


@dataclass
class SyncConfiguration:
    """Configuration for synchronization."""
    sync_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    source_database_id: str = ""
    target_database_id: str = ""
    
    # Sync settings
    sync_mode: SyncMode = SyncMode.REAL_TIME
    sync_direction: SyncDirection = SyncDirection.SOURCE_TO_TARGET
    sync_interval: int = 60  # seconds
    batch_size: int = 100
    max_concurrent_operations: int = 10
    
    # Conflict resolution
    conflict_resolution_strategy: ConflictStrategy = ConflictStrategy.SOURCE_WINS
    conflict_threshold: int = 10  # Max conflicts before pause
    
    # Error handling
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_dead_letter_queue: bool = True
    
    # Performance settings
    connection_pool_size: int = 10
    operation_timeout: int = 30
    heartbeat_interval: int = 5
    
    # Filters and transformations
    include_tables: Optional[List[str]] = None
    exclude_tables: Optional[List[str]] = None
    transformations: Optional[Dict[str, Callable]] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_sync_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'sync_id': self.sync_id,
            'name': self.name,
            'source_database_id': self.source_database_id,
            'target_database_id': self.target_database_id,
            'sync_mode': self.sync_mode.value,
            'sync_direction': self.sync_direction.value,
            'sync_interval': self.sync_interval,
            'batch_size': self.batch_size,
            'max_concurrent_operations': self.max_concurrent_operations,
            'conflict_resolution_strategy': self.conflict_resolution_strategy.value,
            'conflict_threshold': self.conflict_threshold,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'enable_dead_letter_queue': self.enable_dead_letter_queue,
            'connection_pool_size': self.connection_pool_size,
            'operation_timeout': self.operation_timeout,
            'heartbeat_interval': self.heartbeat_interval,
            'include_tables': self.include_tables,
            'exclude_tables': self.exclude_tables,
            'transformations': self.transformations,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'metadata': self.metadata
        }


@dataclass
class SyncStatistics:
    """Synchronization statistics."""
    sync_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Event statistics
    total_events_processed: int = 0
    events_inserted: int = 0
    events_updated: int = 0
    events_deleted: int = 0
    events_failed: int = 0
    events_conflicted: int = 0
    events_resolved: int = 0
    
    # Performance statistics
    average_processing_time_ms: float = 0.0
    throughput_events_per_second: float = 0.0
    max_processing_latency_ms: float = 0.0
    
    # Error statistics
    total_errors: int = 0
    errors_by_category: Dict[str, int] = field(default_factory=dict)
    retry_success_rate: float = 0.0
    
    # Status
    status: SyncStatus = SyncStatus.RUNNING
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'sync_id': self.sync_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_events_processed': self.total_events_processed,
            'events_inserted': self.events_inserted,
            'events_updated': self.events_updated,
            'events_deleted': self.events_deleted,
            'events_failed': self.events_failed,
            'events_conflicted': self.events_conflicted,
            'events_resolved': self.events_resolved,
            'average_processing_time_ms': self.average_processing_time_ms,
            'throughput_events_per_second': self.throughput_events_per_second,
            'max_processing_latency_ms': self.max_processing_latency_ms,
            'total_errors': self.total_errors,
            'errors_by_category': self.errors_by_category,
            'retry_success_rate': self.retry_success_rate,
            'status': self.status.value
        }


class SyncManager:
    """Manages database synchronization operations."""
    
    def __init__(self, 
                 error_recovery: Optional[ErrorRecovery] = None,
                 conflict_resolver: Optional[ConflictResolver] = None,
                 transaction_manager: Optional[TransactionManager] = None):
        
        self.error_recovery = error_recovery or ErrorRecovery()
        self.conflict_resolver = conflict_resolver or ConflictResolver()
        self.transaction_manager = transaction_manager or TransactionManager()
        
        # Sync configurations and instances
        self.sync_configurations: Dict[str, SyncConfiguration] = {}
        self.active_syncs: Dict[str, 'SyncInstance'] = {}
        self.sync_statistics: Dict[str, SyncStatistics] = {}
        
        # Background tasks
        self.monitor_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Thread pool for concurrent operations
        self.thread_pool = ThreadPoolExecutor(max_workers=20)
        
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the synchronization manager."""
        await self.error_recovery.start()
        await self.transaction_manager.start()
        
        self.monitor_task = asyncio.create_task(self._monitor_syncs())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.logger.info("Sync manager started")
    
    async def stop(self):
        """Stop the synchronization manager."""
        # Stop all active syncs
        for sync_id in list(self.active_syncs.keys()):
            await self.stop_sync(sync_id)
        
        # Cancel background tasks
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Stop services
        await self.error_recovery.stop()
        await self.transaction_manager.stop()
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        self.logger.info("Sync manager stopped")
    
    async def create_sync_configuration(self, config: SyncConfiguration) -> str:
        """Create a new synchronization configuration."""
        if config.sync_id in self.sync_configurations:
            raise ValueError(f"Sync configuration {config.sync_id} already exists")
        
        self.sync_configurations[config.sync_id] = config
        self.logger.info(f"Created sync configuration: {config.name} ({config.sync_id})")
        
        return config.sync_id
    
    async def start_sync(self, sync_id: str) -> bool:
        """Start a synchronization process."""
        if sync_id not in self.sync_configurations:
            raise ValueError(f"Sync configuration {sync_id} not found")
        
        if sync_id in self.active_syncs:
            self.logger.warning(f"Sync {sync_id} is already active")
            return False
        
        try:
            config = self.sync_configurations[sync_id]
            sync_instance = SyncInstance(sync_id, config, self)
            
            await sync_instance.start()
            self.active_syncs[sync_id] = sync_instance
            
            # Create statistics tracking
            self.sync_statistics[sync_id] = SyncStatistics(
                sync_id=sync_id,
                start_time=datetime.now()
            )
            
            self.logger.info(f"Started sync: {config.name} ({sync_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start sync {sync_id}: {e}")
            return False
    
    async def stop_sync(self, sync_id: str) -> bool:
        """Stop a synchronization process."""
        if sync_id not in self.active_syncs:
            self.logger.warning(f"Sync {sync_id} is not active")
            return False
        
        try:
            sync_instance = self.active_syncs[sync_id]
            await sync_instance.stop()
            del self.active_syncs[sync_id]
            
            # Update statistics
            if sync_id in self.sync_statistics:
                stats = self.sync_statistics[sync_id]
                stats.end_time = datetime.now()
                stats.status = SyncStatus.COMPLETED
            
            self.logger.info(f"Stopped sync: {sync_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop sync {sync_id}: {e}")
            return False
    
    async def pause_sync(self, sync_id: str) -> bool:
        """Pause a synchronization process."""
        if sync_id not in self.active_syncs:
            return False
        
        sync_instance = self.active_syncs[sync_id]
        await sync_instance.pause()
        return True
    
    async def resume_sync(self, sync_id: str) -> bool:
        """Resume a paused synchronization process."""
        if sync_id not in self.active_syncs:
            return False
        
        sync_instance = self.active_syncs[sync_id]
        await sync_instance.resume()
        return True
    
    async def trigger_manual_sync(self, sync_id: str) -> bool:
        """Trigger a manual synchronization."""
        if sync_id not in self.active_syncs:
            return False
        
        sync_instance = self.active_syncs[sync_id]
        return await sync_instance.trigger_manual_sync()
    
    async def get_sync_status(self, sync_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a synchronization."""
        if sync_id not in self.active_syncs:
            return None
        
        sync_instance = self.active_syncs[sync_id]
        return {
            'sync_id': sync_id,
            'status': sync_instance.status.value,
            'last_heartbeat': sync_instance.last_heartbeat.isoformat(),
            'events_processed': sync_instance.events_processed,
            'conflicts_detected': sync_instance.conflicts_detected,
            'errors_encountered': len(sync_instance.pending_errors)
        }
    
    async def get_all_sync_status(self) -> List[Dict[str, Any]]:
        """Get status of all active synchronizations."""
        return [await self.get_sync_status(sync_id) for sync_id in self.active_syncs.keys()]
    
    async def get_statistics(self, sync_id: str) -> Optional[SyncStatistics]:
        """Get statistics for a synchronization."""
        return self.sync_statistics.get(sync_id)
    
    async def get_global_statistics(self) -> Dict[str, Any]:
        """Get global synchronization statistics."""
        total_syncs = len(self.sync_configurations)
        active_syncs = len(self.active_syncs)
        
        # Aggregate statistics from all syncs
        total_events = 0
        total_errors = 0
        total_conflicts = 0
        
        for stats in self.sync_statistics.values():
            total_events += stats.total_events_processed
            total_errors += stats.total_errors
            total_conflicts += stats.events_conflicted
        
        return {
            'total_sync_configurations': total_syncs,
            'active_syncs': active_syncs,
            'total_events_processed': total_events,
            'total_errors': total_errors,
            'total_conflicts': total_conflicts,
            'error_recovery_stats': self.error_recovery.get_error_statistics(),
            'transaction_stats': await self.transaction_manager.get_transaction_stats()
        }
    
    async def _monitor_syncs(self) -> None:
        """Background task to monitor active synchronizations."""
        while True:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds
                await self._check_sync_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Sync monitoring error: {e}")
    
    async def _cleanup_loop(self) -> None:
        """Background task for cleanup operations."""
        while True:
            try:
                await asyncio.sleep(3600)  # Clean up every hour
                await self._cleanup_old_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
    
    async def _check_sync_health(self) -> None:
        """Check health of all active synchronizations."""
        now = datetime.now()
        
        for sync_id, sync_instance in list(self.active_syncs.items()):
            # Check for stale heartbeats
            if now - sync_instance.last_heartbeat > timedelta(minutes=5):
                self.logger.warning(f"Sync {sync_id} heartbeat is stale, restarting")
                await sync_instance.restart()
            
            # Check for excessive conflicts
            if sync_instance.conflicts_detected > sync_instance.config.conflict_threshold:
                self.logger.warning(f"Sync {sync_id} has excessive conflicts, pausing")
                await sync_instance.pause()
    
    async def _cleanup_old_data(self) -> None:
        """Clean up old synchronization data."""
        cutoff_time = datetime.now() - timedelta(days=7)
        
        # Clean up old statistics
        to_remove = []
        for sync_id, stats in self.sync_statistics.items():
            if stats.end_time and stats.end_time < cutoff_time:
                to_remove.append(sync_id)
        
        for sync_id in to_remove:
            del self.sync_statistics[sync_id]
        
        self.logger.info(f"Cleaned up {len(to_remove)} old sync statistics")


class SyncInstance:
    """Represents an active synchronization instance."""
    
    def __init__(self, sync_id: str, config: SyncConfiguration, sync_manager: SyncManager):
        self.sync_id = sync_id
        self.config = config
        self.sync_manager = sync_manager
        
        # Status tracking
        self.status = SyncStatus.STOPPED
        self.last_heartbeat = datetime.now()
        self.events_processed = 0
        self.conflicts_detected = 0
        self.pending_errors: List[ErrorEvent] = []
        
        # Background tasks
        self.main_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        # Database connectors (to be set by implementation)
        self.source_connector = None
        self.target_connector = None
        
        self.logger = logging.getLogger(f"{__name__}.{sync_id}")
    
    async def start(self):
        """Start the synchronization instance."""
        if self.status != SyncStatus.STOPPED:
            raise ValueError(f"Sync {self.sync_id} is already running")
        
        self.status = SyncStatus.STARTING
        
        try:
            # Initialize database connectors
            await self._initialize_connectors()
            
            # Start background tasks
            self.main_task = asyncio.create_task(self._main_loop())
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            self.status = SyncStatus.RUNNING
            self.logger.info(f"Started sync instance {self.sync_id}")
            
        except Exception as e:
            self.status = SyncStatus.ERROR
            self.logger.error(f"Failed to start sync {self.sync_id}: {e}")
            raise
    
    async def stop(self):
        """Stop the synchronization instance."""
        if self.status == SyncStatus.STOPPED:
            return
        
        self.status = SyncStatus.STOPPED
        
        # Cancel background tasks
        if self.main_task:
            self.main_task.cancel()
            try:
                await self.main_task
            except asyncio.CancelledError:
                pass
        
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup
        await self._cleanup_connectors()
        
        self.logger.info(f"Stopped sync instance {self.sync_id}")
    
    async def pause(self):
        """Pause the synchronization instance."""
        if self.status == SyncStatus.RUNNING:
            self.status = SyncStatus.PAUSED
            self.logger.info(f"Paused sync instance {self.sync_id}")
    
    async def resume(self):
        """Resume the synchronization instance."""
        if self.status == SyncStatus.PAUSED:
            self.status = SyncStatus.RUNNING
            self.logger.info(f"Resumed sync instance {self.sync_id}")
    
    async def restart(self):
        """Restart the synchronization instance."""
        await self.stop()
        await self.start()
    
    async def trigger_manual_sync(self) -> bool:
        """Trigger a manual synchronization."""
        if self.status != SyncStatus.RUNNING:
            return False
        
        # Trigger immediate synchronization
        await self._process_sync_batch()
        return True
    
    async def _main_loop(self):
        """Main synchronization loop."""
        while self.status in [SyncStatus.STARTING, SyncStatus.RUNNING, SyncStatus.PAUSED]:
            try:
                if self.status == SyncStatus.RUNNING:
                    await self._process_sync_batch()
                    
                    # Wait for next sync interval
                    await asyncio.sleep(self.config.sync_interval)
                else:
                    # Paused or starting - just wait
                    await asyncio.sleep(1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in main loop for sync {self.sync_id}: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _heartbeat_loop(self):
        """Heartbeat loop to indicate active state."""
        while self.status != SyncStatus.STOPPED:
            self.last_heartbeat = datetime.now()
            await asyncio.sleep(self.config.heartbeat_interval)
    
    async def _process_sync_batch(self):
        """Process a batch of synchronization operations."""
        try:
            # Get changes from source
            changes = await self._get_source_changes()
            
            if not changes:
                return
            
            # Process changes in batches
            for i in range(0, len(changes), self.config.batch_size):
                batch = changes[i:i + self.config.batch_size]
                await self._process_change_batch(batch)
                
        except Exception as e:
            self.logger.error(f"Error processing sync batch: {e}")
    
    async def _get_source_changes(self) -> List[ChangeEvent]:
        """Get changes from source database."""
        # This would be implemented by specific sync strategies
        # For now, return empty list
        return []
    
    async def _process_change_batch(self, changes: List[ChangeEvent]):
        """Process a batch of changes."""
        event_batch = EventBatch()
        for change in changes:
            event_batch.add_event(change)
        
        # Apply transformations if configured
        if self.config.transformations:
            await self._apply_transformations(event_batch)
        
        # Detect conflicts
        conflicts = await self._detect_conflicts(event_batch)
        
        # Resolve conflicts
        if conflicts:
            await self._resolve_conflicts(conflicts)
        
        # Apply changes to target
        await self._apply_changes(event_batch)
        
        self.events_processed += len(changes)
    
    async def _apply_transformations(self, event_batch: EventBatch):
        """Apply data transformations to events."""
        for event in event_batch.events:
            if event.new_values and self.config.transformations:
                for field_name, transform_func in self.config.transformations.items():
                    if field_name in event.new_values:
                        try:
                            event.new_values[field_name] = await transform_func(event.new_values[field_name])
                        except Exception as e:
                            self.logger.warning(f"Transformation failed for field {field_name}: {e}")
    
    async def _detect_conflicts(self, event_batch: EventBatch) -> List[ConflictInfo]:
        """Detect conflicts in the event batch."""
        conflicts = []
        
        for event in event_batch.events:
            if event.event_type == ChangeType.UPDATE:
                # Get current target data
                target_data = await self._get_target_data(event.target_table, event.primary_key)
                
                if target_data:
                    # Detect conflicts
                    detected_conflicts = await self.sync_manager.conflict_resolver.detect_conflicts(
                        event.new_values, target_data, event.target_table, event.primary_key
                    )
                    conflicts.extend(detected_conflicts)
        
        self.conflicts_detected += len(conflicts)
        return conflicts
    
    async def _resolve_conflicts(self, conflicts: List[ConflictInfo]):
        """Resolve detected conflicts."""
        resolution_results = await self.sync_manager.conflict_resolver.resolve_conflicts(conflicts)
        
        for conflict, result in zip(conflicts, resolution_results):
            if result.resolved:
                self.logger.info(f"Resolved conflict {conflict.conflict_id}")
            else:
                self.logger.error(f"Failed to resolve conflict {conflict.conflict_id}")
    
    async def _apply_changes(self, event_batch: EventBatch):
        """Apply changes to target database."""
        # This would be implemented by specific database connectors
        pass
    
    async def _get_target_data(self, table_name: str, primary_key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get data from target database."""
        # This would be implemented by specific database connectors
        return None
    
    async def _initialize_connectors(self):
        """Initialize database connectors."""
        # This would be implemented to set up actual database connections
        pass
    
    async def _cleanup_connectors(self):
        """Clean up database connectors."""
        # This would be implemented to clean up connections
        pass


class AsyncSyncManager(SyncManager):
    """Asynchronous synchronization manager."""
    
    async def execute_concurrent_syncs(self, sync_ids: List[str]) -> Dict[str, bool]:
        """Execute multiple synchronizations concurrently."""
        tasks = []
        for sync_id in sync_ids:
            task = asyncio.create_task(self.start_sync(sync_id))
            tasks.append((sync_id, task))
        
        results = {}
        for sync_id, task in tasks:
            try:
                results[sync_id] = await task
            except Exception as e:
                self.logger.error(f"Failed to start sync {sync_id}: {e}")
                results[sync_id] = False
        
        return results


class SyncManagerWithMetrics(SyncManager):
    """Sync manager with enhanced metrics and monitoring."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.performance_metrics = {}
        self.alert_conditions = []
    
    async def add_alert_condition(self, condition: Dict[str, Any]):
        """Add an alert condition."""
        self.alert_conditions.append(condition)
    
    async def evaluate_alerts(self):
        """Evaluate alert conditions."""
        stats = await self.get_global_statistics()
        
        for condition in self.alert_conditions:
            if await self._check_alert_condition(condition, stats):
                await self._trigger_alert(condition, stats)
    
    async def _check_alert_condition(self, condition: Dict[str, Any], stats: Dict[str, Any]) -> bool:
        """Check if an alert condition is met."""
        # Implementation would check various metrics
        return False
    
    async def _trigger_alert(self, condition: Dict[str, Any], stats: Dict[str, Any]):
        """Trigger an alert."""
        # Implementation would send notifications
        self.logger.warning(f"Alert triggered: {condition}")
