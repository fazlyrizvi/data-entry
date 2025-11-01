"""
Error Recovery System

Provides comprehensive error recovery mechanisms for database synchronization.
"""

import asyncio
import logging
import traceback
from typing import Dict, List, Any, Optional, Callable, Type, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
from collections import defaultdict, deque
import hashlib


class RecoveryStrategy(Enum):
    """Error recovery strategies."""
    RETRY = "RETRY"
    SKIP = "SKIP"
    ROLLBACK = "ROLLBACK"
    COMPENSATE = "COMPENSATE"
    MANUAL_INTERVENTION = "MANUAL_INTERVENTION"
    FAIL_FAST = "FAIL_FAST"
    DEAD_LETTER = "DEAD_LETTER"


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ErrorCategory(Enum):
    """Categories of errors."""
    CONNECTION_ERROR = "CONNECTION_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    DATA_CONVERSION = "DATA_CONVERSION"
    PERMISSION_ERROR = "PERMISSION_ERROR"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class ErrorEvent:
    """Represents an error event."""
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    error_type: str = ""
    error_category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    
    # Error details
    error_message: str = ""
    error_details: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    
    # Context information
    operation_id: Optional[str] = None
    transaction_id: Optional[str] = None
    database_id: Optional[str] = None
    table_name: Optional[str] = None
    
    # Recovery information
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None
    resolved: bool = False
    resolution_details: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'error_id': self.error_id,
            'error_type': self.error_type,
            'error_category': self.error_category.value,
            'severity': self.severity.value,
            'error_message': self.error_message,
            'error_details': self.error_details,
            'stack_trace': self.stack_trace,
            'operation_id': self.operation_id,
            'transaction_id': self.transaction_id,
            'database_id': self.database_id,
            'table_name': self.table_name,
            'recovery_strategy': self.recovery_strategy.value,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'next_retry_at': self.next_retry_at.isoformat() if self.next_retry_at else None,
            'resolved': self.resolved,
            'resolution_details': self.resolution_details,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'metadata': self.metadata
        }


@dataclass
class RecoveryAction:
    """Represents a recovery action."""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str = ""
    target_error_id: str = ""
    action_parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Execution tracking
    status: str = "PENDING"  # PENDING, EXECUTING, COMPLETED, FAILED
    executed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error_message: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ErrorRecovery:
    """Comprehensive error recovery system for database synchronization."""
    
    def __init__(self, 
                 max_retries: int = 3,
                 retry_delay_base: float = 1.0,
                 retry_delay_max: float = 300.0,
                 dead_letter_queue_enabled: bool = True,
                 max_errors_per_hour: int = 1000):
        
        self.max_retries = max_retries
        self.retry_delay_base = retry_delay_base
        self.retry_delay_max = retry_delay_max
        self.dead_letter_queue_enabled = dead_letter_queue_enabled
        self.max_errors_per_hour = max_errors_per_hour
        
        # Error tracking
        self.error_events: Dict[str, ErrorEvent] = {}
        self.error_history: deque = deque(maxlen=10000)
        self.dead_letter_queue: List[ErrorEvent] = []
        
        # Recovery tracking
        self.recovery_actions: Dict[str, RecoveryAction] = {}
        
        # Error rate limiting
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.last_error_reset: Dict[str, datetime] = {}
        
        # Registered recovery handlers
        self.error_handlers: Dict[ErrorCategory, Callable] = {}
        self.exception_handlers: Dict[Type[Exception], Callable] = {}
        
        # Background tasks
        self.recovery_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        self.logger = logging.getLogger(__name__)
        
        # Register default handlers
        self._register_default_handlers()
    
    async def start(self):
        """Start the error recovery system."""
        self.recovery_task = asyncio.create_task(self._recovery_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.logger.info("Error recovery system started")
    
    async def stop(self):
        """Stop the error recovery system."""
        if self.recovery_task:
            self.recovery_task.cancel()
            try:
                await self.recovery_task
            except asyncio.CancelledError:
                pass
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Error recovery system stopped")
    
    def register_error_handler(self, error_category: ErrorCategory, handler: Callable):
        """Register an error handler for a specific error category."""
        self.error_handlers[error_category] = handler
    
    def register_exception_handler(self, exception_type: Type[Exception], handler: Callable):
        """Register an exception handler for a specific exception type."""
        self.exception_handlers[exception_type] = handler
    
    async def handle_error(self, 
                          error: Exception,
                          operation_context: Optional[Dict[str, Any]] = None,
                          recovery_strategy: Optional[RecoveryStrategy] = None) -> ErrorEvent:
        """Handle an error and determine recovery strategy."""
        # Create error event
        error_event = await self._create_error_event(error, operation_context)
        
        # Determine recovery strategy
        if recovery_strategy:
            error_event.recovery_strategy = recovery_strategy
        else:
            error_event.recovery_strategy = await self._determine_recovery_strategy(error_event)
        
        # Check rate limits
        if await self._is_rate_limited(error_event):
            error_event.recovery_strategy = RecoveryStrategy.FAIL_FAST
            error_event.severity = ErrorSeverity.CRITICAL
        
        # Store error event
        self.error_events[error_event.error_id] = error_event
        self.error_history.append(error_event)
        
        # Update error counts
        await self._update_error_counts(error_event)
        
        self.logger.warning(f"Error handled: {error_event.error_id} - {error_event.error_message}")
        
        return error_event
    
    async def recover_from_error(self, error_event: ErrorEvent) -> bool:
        """Attempt to recover from an error."""
        try:
            if error_event.resolved:
                return True
            
            # Check if recovery is needed
            if error_event.recovery_strategy == RecoveryStrategy.FAIL_FAST:
                await self._mark_as_unrecoverable(error_event, "Fail fast strategy")
                return False
            
            # Attempt recovery based on strategy
            success = await self._execute_recovery_strategy(error_event)
            
            if success:
                error_event.resolved = True
                error_event.resolved_at = datetime.now()
                error_event.resolution_details = f"Recovered using {error_event.recovery_strategy.value}"
                
                self.logger.info(f"Recovered from error: {error_event.error_id}")
            else:
                # Check if we should retry
                if error_event.retry_count < error_event.max_retries:
                    await self._schedule_retry(error_event)
                else:
                    await self._handle_max_retries_reached(error_event)
            
            return success
            
        except Exception as recovery_error:
            self.logger.error(f"Recovery failed for error {error_event.error_id}: {recovery_error}")
            error_event.resolution_details = f"Recovery failed: {str(recovery_error)}"
            return False
    
    async def recover_from_errors(self, error_events: List[ErrorEvent]) -> Dict[str, bool]:
        """Attempt to recover from multiple errors."""
        results = {}
        
        # Group by recovery strategy for batch processing
        strategy_groups = defaultdict(list)
        for error_event in error_events:
            if not error_event.resolved:
                strategy_groups[error_event.recovery_strategy].append(error_event)
        
        # Process each group
        for strategy, events in strategy_groups.items():
            if strategy == RecoveryStrategy.RETRY:
                results.update(await self._batch_retry(events))
            elif strategy == RecoveryStrategy.SKIP:
                results.update(await self._batch_skip(events))
            elif strategy == RecoveryStrategy.DEAD_LETTER:
                results.update(await self._batch_dead_letter(events))
            else:
                # Process individually
                for error_event in events:
                    results[error_event.error_id] = await self.recover_from_error(error_event)
        
        return results
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        now = datetime.now()
        
        # Count errors by category and severity
        categories = defaultdict(int)
        severities = defaultdict(int)
        strategies = defaultdict(int)
        
        recent_errors = []
        
        for error_event in self.error_history:
            categories[error_event.error_category.value] += 1
            severities[error_event.severity.value] += 1
            strategies[error_event.recovery_strategy.value] += 1
            
            # Count errors in last hour
            if now - error_event.created_at <= timedelta(hours=1):
                recent_errors.append(error_event)
        
        # Calculate recovery success rate
        resolved_errors = [e for e in self.error_history if e.resolved]
        recovery_rate = len(resolved_errors) / len(self.error_history) if self.error_history else 0
        
        return {
            'total_errors': len(self.error_history),
            'active_errors': len([e for e in self.error_events.values() if not e.resolved]),
            'dead_letter_queue_size': len(self.dead_letter_queue),
            'errors_by_category': dict(categories),
            'errors_by_severity': dict(severities),
            'recovery_strategies_used': dict(strategies),
            'recovery_success_rate': recovery_rate,
            'errors_last_hour': len(recent_errors),
            'current_rate_limit_status': self._get_rate_limit_status(),
            'most_common_error_type': max(categories.items(), key=lambda x: x[1])[0] if categories else None
        }
    
    def get_error_details(self, error_id: str) -> Optional[ErrorEvent]:
        """Get detailed information about an error."""
        return self.error_events.get(error_id)
    
    def get_pending_errors(self) -> List[ErrorEvent]:
        """Get all pending errors that need recovery."""
        return [e for e in self.error_events.values() if not e.resolved and e.next_retry_at is None]
    
    def get_errors_for_operation(self, operation_id: str) -> List[ErrorEvent]:
        """Get all errors related to a specific operation."""
        return [e for e in self.error_events.values() if e.operation_id == operation_id]
    
    def mark_error_as_manual_intervention(self, error_id: str, details: str) -> bool:
        """Mark an error as requiring manual intervention."""
        if error_id in self.error_events:
            error_event = self.error_events[error_id]
            error_event.recovery_strategy = RecoveryStrategy.MANUAL_INTERVENTION
            error_event.resolution_details = details
            return True
        return False
    
    async def _create_error_event(self, 
                                error: Exception, 
                                operation_context: Optional[Dict[str, Any]] = None) -> ErrorEvent:
        """Create an error event from an exception."""
        # Determine error category
        error_category = await self._categorize_error(error)
        
        # Determine severity
        severity = await self._determine_severity(error, error_category)
        
        # Extract context information
        context = operation_context or {}
        
        error_event = ErrorEvent(
            error_type=type(error).__name__,
            error_category=error_category,
            severity=severity,
            error_message=str(error),
            error_details={
                'exception_type': type(error).__name__,
                'exception_module': type(error).__module__,
                'operation_context': context
            },
            stack_trace=traceback.format_exc(),
            operation_id=context.get('operation_id'),
            transaction_id=context.get('transaction_id'),
            database_id=context.get('database_id'),
            table_name=context.get('table_name'),
            metadata=context
        )
        
        return error_event
    
    async def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize an error."""
        error_type = type(error).__name__.lower()
        
        if any(keyword in error_type for keyword in ['connection', 'connect', 'network']):
            return ErrorCategory.CONNECTION_ERROR
        elif any(keyword in error_type for keyword in ['timeout', 'timed', 'deadline']):
            return ErrorCategory.TIMEOUT_ERROR
        elif any(keyword in error_type for keyword in ['constraint', 'unique', 'foreign', 'not null']):
            return ErrorCategory.CONSTRAINT_VIOLATION
        elif any(keyword in error_type for keyword in ['schema', 'column', 'table', 'field']):
            return ErrorCategory.SCHEMA_MISMATCH
        elif any(keyword in error_type for keyword in ['permission', 'auth', 'unauthorized']):
            return ErrorCategory.PERMISSION_ERROR
        elif any(keyword in error_type for keyword in ['resource', 'memory', 'disk', 'quota']):
            return ErrorCategory.RESOURCE_EXHAUSTED
        else:
            return ErrorCategory.UNKNOWN_ERROR
    
    async def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine the severity of an error."""
        if category in [ErrorCategory.CONNECTION_ERROR, ErrorCategory.RESOURCE_EXHAUSTED]:
            return ErrorSeverity.HIGH
        elif category in [ErrorCategory.TIMEOUT_ERROR, ErrorCategory.PERMISSION_ERROR]:
            return ErrorSeverity.MEDIUM
        elif category == ErrorCategory.UNKNOWN_ERROR:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    async def _determine_recovery_strategy(self, error_event: ErrorEvent) -> RecoveryStrategy:
        """Determine the best recovery strategy for an error."""
        category = error_event.error_category
        
        # Use registered handlers if available
        if category in self.error_handlers:
            handler = self.error_handlers[category]
            try:
                return await handler(error_event)
            except Exception:
                pass
        
        # Default strategies based on category
        strategy_map = {
            ErrorCategory.CONNECTION_ERROR: RecoveryStrategy.RETRY,
            ErrorCategory.TIMEOUT_ERROR: RecoveryStrategy.RETRY,
            ErrorCategory.CONSTRAINT_VIOLATION: RecoveryStrategy.SKIP,
            ErrorCategory.SCHEMA_MISMATCH: RecoveryStrategy.MANUAL_INTERVENTION,
            ErrorCategory.PERMISSION_ERROR: RecoveryStrategy.MANUAL_INTERVENTION,
            ErrorCategory.RESOURCE_EXHAUSTED: RecoveryStrategy.RETRY,
            ErrorCategory.UNKNOWN_ERROR: RecoveryStrategy.RETRY
        }
        
        return strategy_map.get(category, RecoveryStrategy.RETRY)
    
    async def _execute_recovery_strategy(self, error_event: ErrorEvent) -> bool:
        """Execute the recovery strategy for an error."""
        strategy = error_event.recovery_strategy
        
        if strategy == RecoveryStrategy.RETRY:
            return await self._retry_error(error_event)
        elif strategy == RecoveryStrategy.SKIP:
            return await self._skip_error(error_event)
        elif strategy == RecoveryStrategy.DEAD_LETTER:
            return await self._send_to_dead_letter_queue(error_event)
        elif strategy == RecoveryStrategy.MANUAL_INTERVENTION:
            return await self._request_manual_intervention(error_event)
        else:
            return False
    
    async def _retry_error(self, error_event: ErrorEvent) -> bool:
        """Retry an error."""
        # Calculate backoff delay
        delay = min(
            self.retry_delay_base * (2 ** error_event.retry_count),
            self.retry_delay_max
        )
        
        error_event.next_retry_at = datetime.now() + timedelta(seconds=delay)
        return True
    
    async def _skip_error(self, error_event: ErrorEvent) -> bool:
        """Skip an error."""
        error_event.resolved = True
        error_event.resolved_at = datetime.now()
        error_event.resolution_details = "Skipped"
        return True
    
    async def _send_to_dead_letter_queue(self, error_event: ErrorEvent) -> bool:
        """Send error to dead letter queue."""
        if self.dead_letter_queue_enabled:
            self.dead_letter_queue.append(error_event)
            error_event.resolved = True
            error_event.resolved_at = datetime.now()
            error_event.resolution_details = "Sent to dead letter queue"
            return True
        return False
    
    async def _request_manual_intervention(self, error_event: ErrorEvent) -> bool:
        """Mark error as requiring manual intervention."""
        # In a real implementation, this might send alerts, notifications, etc.
        self.logger.error(f"Manual intervention required for error: {error_event.error_id}")
        return False
    
    async def _handle_max_retries_reached(self, error_event: ErrorEvent) -> None:
        """Handle when maximum retries are reached."""
        if error_event.severity == ErrorSeverity.CRITICAL:
            error_event.recovery_strategy = RecoveryStrategy.FAIL_FAST
        else:
            error_event.recovery_strategy = RecoveryStrategy.DEAD_LETTER
            if self.dead_letter_queue_enabled:
                self.dead_letter_queue.append(error_event)
        
        error_event.resolution_details = f"Max retries ({error_event.max_retries}) reached"
    
    async def _schedule_retry(self, error_event: ErrorEvent) -> None:
        """Schedule a retry for an error."""
        error_event.retry_count += 1
        delay = min(
            self.retry_delay_base * (2 ** error_event.retry_count),
            self.retry_delay_max
        )
        error_event.next_retry_at = datetime.now() + timedelta(seconds=delay)
    
    async def _batch_retry(self, error_events: List[ErrorEvent]) -> Dict[str, bool]:
        """Retry multiple errors in batch."""
        results = {}
        for error_event in error_events:
            success = await self._retry_error(error_event)
            results[error_event.error_id] = success
        return results
    
    async def _batch_skip(self, error_events: List[ErrorEvent]) -> Dict[str, bool]:
        """Skip multiple errors in batch."""
        results = {}
        for error_event in error_events:
            success = await self._skip_error(error_event)
            results[error_event.error_id] = success
        return results
    
    async def _batch_dead_letter(self, error_events: List[ErrorEvent]) -> Dict[str, bool]:
        """Send multiple errors to dead letter queue."""
        results = {}
        for error_event in error_events:
            success = await self._send_to_dead_letter_queue(error_event)
            results[error_event.error_id] = success
        return results
    
    def _register_default_handlers(self):
        """Register default error handlers."""
        
        async def connection_error_handler(error_event: ErrorEvent) -> RecoveryStrategy:
            return RecoveryStrategy.RETRY
        
        async def schema_error_handler(error_event: ErrorEvent) -> RecoveryStrategy:
            return RecoveryStrategy.MANUAL_INTERVENTION
        
        self.register_error_handler(ErrorCategory.CONNECTION_ERROR, connection_error_handler)
        self.register_error_handler(ErrorCategory.SCHEMA_MISMATCH, schema_error_handler)
    
    async def _is_rate_limited(self, error_event: ErrorEvent) -> bool:
        """Check if we're rate limited for this error type."""
        category = error_event.error_category.value
        now = datetime.now()
        
        # Reset counter if it's been an hour
        if category in self.last_error_reset:
            if now - self.last_error_reset[category] > timedelta(hours=1):
                self.error_counts[category] = 0
                self.last_error_reset[category] = now
        
        return self.error_counts[category] >= self.max_errors_per_hour
    
    async def _update_error_counts(self, error_event: ErrorEvent) -> None:
        """Update error counts for rate limiting."""
        category = error_event.error_category.value
        now = datetime.now()
        
        if category not in self.error_counts:
            self.error_counts[category] = 0
            self.last_error_reset[category] = now
        
        self.error_counts[category] += 1
    
    def _get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        now = datetime.now()
        status = {}
        
        for category, count in self.error_counts.items():
            last_reset = self.last_error_reset.get(category, now)
            time_until_reset = max(timedelta(0), timedelta(hours=1) - (now - last_reset))
            
            status[category] = {
                'current_count': count,
                'max_allowed': self.max_errors_per_hour,
                'time_until_reset_seconds': time_until_reset.total_seconds(),
                'rate_limited': count >= self.max_errors_per_hour
            }
        
        return status
    
    async def _recovery_loop(self) -> None:
        """Background task for processing recovery actions."""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                await self._process_pending_recoveries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Recovery loop error: {e}")
    
    async def _cleanup_loop(self) -> None:
        """Background task for cleaning up old errors."""
        while True:
            try:
                await asyncio.sleep(3600)  # Clean up every hour
                await self._cleanup_old_errors()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
    
    async def _process_pending_recoveries(self) -> None:
        """Process pending recovery actions."""
        now = datetime.now()
        
        # Process retryable errors
        for error_event in self.error_events.values():
            if (not error_event.resolved and 
                error_event.next_retry_at and 
                error_event.next_retry_at <= now):
                
                # Clear retry time and attempt recovery
                error_event.next_retry_at = None
                await self.recover_from_error(error_event)
    
    async def _cleanup_old_errors(self) -> None:
        """Clean up old error events."""
        cutoff_time = datetime.now() - timedelta(days=7)  # Keep errors for 7 days
        
        # Remove old resolved errors
        to_remove = []
        for error_id, error_event in self.error_events.items():
            if error_event.resolved and error_event.created_at < cutoff_time:
                to_remove.append(error_id)
        
        for error_id in to_remove:
            del self.error_events[error_id]
        
        if to_remove:
            self.logger.info(f"Cleaned up {len(to_remove)} old error events")


class AsyncErrorRecovery(ErrorRecovery):
    """Asynchronous version of error recovery."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def handle_operation_error(self, 
                                   operation_func: Callable,
                                   *args, 
                                   operation_context: Optional[Dict[str, Any]] = None,
                                   **kwargs) -> Any:
        """Execute an operation with error handling."""
        try:
            return await operation_func(*args, **kwargs)
        except Exception as error:
            error_event = await self.handle_error(error, operation_context)
            
            # Attempt recovery
            if await self.recover_from_error(error_event):
                # Retry the operation
                return await operation_func(*args, **kwargs)
            else:
                # Re-raise if recovery failed
                raise error


class SyncErrorRecovery(ErrorRecovery):
    """Synchronous version of error recovery."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def handle_operation_error(self, 
                             operation_func: Callable,
                             *args, 
                             operation_context: Optional[Dict[str, Any]] = None,
                             **kwargs) -> Any:
        """Execute an operation with error handling."""
        try:
            return operation_func(*args, **kwargs)
        except Exception as error:
            # Run async error handling in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                error_event = loop.run_until_complete(self.handle_error(error, operation_context))
                recovery_success = loop.run_until_complete(self.recover_from_error(error_event))
                
                if recovery_success:
                    # Retry the operation
                    return operation_func(*args, **kwargs)
                else:
                    raise error
            finally:
                loop.close()
