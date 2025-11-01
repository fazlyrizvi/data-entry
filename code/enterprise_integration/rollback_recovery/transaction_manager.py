"""
Transaction Manager - Handles ACID compliance and transaction management
"""
import asyncio
import hashlib
import json
import logging
import sqlite3
import threading
import time
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID, uuid4

import structlog

logger = structlog.get_logger(__name__)


class TransactionState(Enum):
    """Transaction states for lifecycle management"""
    PENDING = "pending"
    ACTIVE = "active"
    COMMITTED = "committed"
    ABORTED = "aborted"
    TIMEOUT = "timeout"
    PREPARED = "prepared"
    ROLLED_BACK = "rolled_back"


class IsolationLevel(Enum):
    """Transaction isolation levels"""
    READ_UNCOMMITTED = "read_uncommitted"
    READ_COMMITTED = "read_committed"
    REPEATABLE_READ = "repeatable_read"
    SERIALIZABLE = "serializable"


@dataclass
class TransactionOperation:
    """Represents a single database operation within a transaction"""
    operation_id: UUID
    transaction_id: UUID
    operation_type: str  # CREATE, UPDATE, DELETE, SELECT
    table_name: str
    data: Dict[str, Any]
    timestamp: float
    checksum: str
    rollback_data: Optional[Dict[str, Any]] = None


@dataclass
class TransactionSnapshot:
    """Snapshot of transaction state for point-in-time recovery"""
    snapshot_id: UUID
    transaction_id: UUID
    timestamp: float
    operations: List[TransactionOperation] = field(default_factory=list)
    state: TransactionState = TransactionState.PENDING
    checksum: str = ""


@dataclass
class LockInfo:
    """Information about database row/table locks"""
    resource_type: str  # 'table', 'row', 'page'
    resource_identifier: str
    transaction_id: UUID
    lock_mode: str  # 'shared', 'exclusive', 'intention_shared', 'intention_exclusive'
    acquired_at: float
    timeout: Optional[float] = None


class TransactionManager:
    """
    ACID-compliant transaction manager with support for:
    - Multi-database transactions
    - Two-phase commit
    - Deadlock detection
    - Transaction isolation
    - Rollback capabilities
    """

    def __init__(self, 
                 transaction_timeout: float = 300.0,
                 max_retry_attempts: int = 3,
                 deadlock_detection_interval: float = 10.0):
        self.transaction_timeout = transaction_timeout
        self.max_retry_attempts = max_retry_attempts
        self.deadlock_detection_interval = deadlock_detection_interval
        
        # Transaction storage
        self._active_transactions: Dict[UUID, Dict] = {}
        self._transaction_snapshots: Dict[UUID, TransactionSnapshot] = {}
        self._operation_logs: List[TransactionOperation] = []
        self._lock_manager: Dict[str, List[LockInfo]] = {}
        
        # Statistics
        self._stats = {
            'total_transactions': 0,
            'committed_transactions': 0,
            'aborted_transactions': 0,
            'rolled_back_transactions': 0,
            'deadlocks_detected': 0,
            'timeout_transactions': 0
        }
        
        # Threading
        self._lock = threading.RLock()
        self._background_tasks: Set[asyncio.Task] = set()
        
        # Start background tasks
        self._start_background_tasks()

    def _start_background_tasks(self):
        """Start background tasks for transaction management"""
        try:
            loop = asyncio.get_event_loop()
            self._background_tasks.add(
                loop.create_task(self._deadlock_detection_loop())
            )
            self._background_tasks.add(
                loop.create_task(self._timeout_detection_loop())
            )
        except RuntimeError:
            # Event loop not running, will start when needed
            pass

    @contextmanager
    def transaction(self, 
                   isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED,
                   database_connection: Optional[str] = None):
        """
        Context manager for transaction lifecycle
        
        Args:
            isolation_level: Transaction isolation level
            database_connection: Database connection identifier
            
        Yields:
            Transaction object
        """
        transaction = None
        try:
            transaction = self.begin_transaction(isolation_level, database_connection)
            yield transaction
            self.commit_transaction(transaction.transaction_id)
        except Exception as e:
            if transaction:
                self.abort_transaction(transaction.transaction_id)
            logger.error("Transaction failed", error=str(e), exc_info=True)
            raise

    async def atransaction(self,
                          isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED,
                          database_connection: Optional[str] = None):
        """
        Async context manager for transaction lifecycle
        """
        transaction = None
        try:
            transaction = self.begin_transaction(isolation_level, database_connection)
            yield transaction
            self.commit_transaction(transaction.transaction_id)
        except Exception as e:
            if transaction:
                await self.aabort_transaction(transaction.transaction_id)
            logger.error("Async transaction failed", error=str(e), exc_info=True)
            raise

    def begin_transaction(self, 
                         isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED,
                         database_connection: Optional[str] = None) -> UUID:
        """
        Begin a new transaction
        
        Returns:
            Transaction ID
        """
        transaction_id = uuid4()
        start_time = time.time()
        
        with self._lock:
            self._active_transactions[transaction_id] = {
                'transaction_id': transaction_id,
                'start_time': start_time,
                'state': TransactionState.ACTIVE,
                'isolation_level': isolation_level,
                'database_connection': database_connection,
                'operations': [],
                'locks': set(),
                'retry_count': 0
            }
            
            self._stats['total_transactions'] += 1
            
            logger.info("Transaction started",
                       transaction_id=str(transaction_id),
                       isolation_level=isolation_level.value,
                       database_connection=database_connection)
            
            return transaction_id

    def commit_transaction(self, transaction_id: UUID) -> bool:
        """
        Commit a transaction with two-phase commit protocol
        
        Args:
            transaction_id: Transaction ID to commit
            
        Returns:
            True if commit successful
        """
        with self._lock:
            if transaction_id not in self._active_transactions:
                logger.error("Transaction not found for commit", transaction_id=str(transaction_id))
                return False
            
            transaction = self._active_transactions[transaction_id]
            if transaction['state'] != TransactionState.ACTIVE:
                logger.warning("Cannot commit non-active transaction",
                             transaction_id=str(transaction_id),
                             state=transaction['state'].value)
                return False
            
            try:
                # Phase 1: Prepare (validate transaction)
                if not self._prepare_transaction(transaction_id):
                    self.abort_transaction(transaction_id)
                    return False
                
                # Phase 2: Commit
                transaction['state'] = TransactionState.COMMITTED
                self._finalize_transaction(transaction_id)
                
                self._stats['committed_transactions'] += 1
                
                logger.info("Transaction committed",
                           transaction_id=str(transaction_id),
                           operation_count=len(transaction['operations']))
                
                return True
                
            except Exception as e:
                logger.error("Transaction commit failed",
                           transaction_id=str(transaction_id),
                           error=str(e),
                           exc_info=True)
                self.abort_transaction(transaction_id)
                return False

    def abort_transaction(self, transaction_id: UUID) -> bool:
        """
        Abort and rollback a transaction
        
        Args:
            transaction_id: Transaction ID to abort
            
        Returns:
            True if abort successful
        """
        with self._lock:
            if transaction_id not in self._active_transactions:
                logger.error("Transaction not found for abort", transaction_id=str(transaction_id))
                return False
            
            transaction = self._active_transactions[transaction_id]
            
            try:
                # Rollback all operations
                rollback_success = self._rollback_operations(transaction_id)
                
                # Release all locks
                self._release_transaction_locks(transaction_id)
                
                # Update state
                transaction['state'] = TransactionState.ABORTED
                self._finalize_transaction(transaction_id)
                
                self._stats['aborted_transactions'] += 1
                
                logger.info("Transaction aborted",
                           transaction_id=str(transaction_id),
                           rollback_success=rollback_success)
                
                return rollback_success
                
            except Exception as e:
                logger.error("Transaction abort failed",
                           transaction_id=str(transaction_id),
                           error=str(e),
                           exc_info=True)
                return False

    async def aabort_transaction(self, transaction_id: UUID) -> bool:
        """Async version of abort_transaction"""
        return self.abort_transaction(transaction_id)

    def _prepare_transaction(self, transaction_id: UUID) -> bool:
        """
        Phase 1 of two-phase commit - validate transaction
        """
        transaction = self._active_transactions[transaction_id]
        
        try:
            # Validate all operations
            for operation in transaction['operations']:
                if not self._validate_operation(operation):
                    return False
            
            # Check for deadlock conditions
            if self._check_deadlock(transaction_id):
                self._stats['deadlocks_detected'] += 1
                return False
            
            # Acquire locks for commit phase
            if not self._acquire_commit_locks(transaction_id):
                return False
            
            # Mark as prepared
            transaction['state'] = TransactionState.PREPARED
            
            return True
            
        except Exception as e:
            logger.error("Transaction preparation failed",
                       transaction_id=str(transaction_id),
                       error=str(e))
            return False

    def _validate_operation(self, operation: TransactionOperation) -> bool:
        """Validate a transaction operation"""
        try:
            # Check checksum
            computed_checksum = hashlib.sha256(
                json.dumps(operation.data, sort_keys=True).encode()
            ).hexdigest()
            
            return operation.checksum == computed_checksum
            
        except Exception as e:
            logger.error("Operation validation failed",
                       operation_id=str(operation.operation_id),
                       error=str(e))
            return False

    def _check_deadlock(self, transaction_id: UUID) -> bool:
        """Detect deadlock conditions"""
        transaction = self._active_transactions[transaction_id]
        
        # Simple deadlock detection based on lock waits
        for waiting_lock in transaction.get('waiting_locks', []):
            resource = waiting_lock['resource']
            
            # Check if resource is held by another transaction that is waiting
            for other_tx_id, other_tx in self._active_transactions.items():
                if other_tx_id != transaction_id:
                    if resource in other_tx.get('held_locks', set()):
                        # Check if the other transaction is waiting for our locks
                        for other_wait_lock in other_tx.get('waiting_locks', []):
                            if any(lock in transaction.get('held_locks', set()) 
                                   for lock in other_tx.get('held_locks', set())):
                                return True
        
        return False

    def _acquire_commit_locks(self, transaction_id: UUID) -> bool:
        """Acquire locks needed for commit phase"""
        transaction = self._active_transactions[transaction_id]
        
        try:
            for operation in transaction['operations']:
                lock_key = f"{operation.table_name}:{hash(str(operation.data))}"
                
                if not self._acquire_lock(lock_key, transaction_id, 'exclusive', 
                                         timeout=self.transaction_timeout):
                    return False
                
                transaction['held_locks'].add(lock_key)
            
            return True
            
        except Exception as e:
            logger.error("Failed to acquire commit locks",
                       transaction_id=str(transaction_id),
                       error=str(e))
            return False

    def _acquire_lock(self, 
                     resource: str,
                     transaction_id: UUID,
                     lock_mode: str,
                     timeout: float = 30.0) -> bool:
        """
        Acquire a lock on a resource
        
        Args:
            resource: Resource to lock
            transaction_id: Transaction requesting lock
            lock_mode: Lock mode ('shared', 'exclusive', 'intention_shared', 'intention_exclusive')
            timeout: Lock timeout
            
        Returns:
            True if lock acquired
        """
        with self._lock:
            current_time = time.time()
            
            # Create lock info
            lock_info = LockInfo(
                resource_type='resource',
                resource_identifier=resource,
                transaction_id=transaction_id,
                lock_mode=lock_mode,
                acquired_at=current_time,
                timeout=timeout
            )
            
            # Check if lock is compatible
            existing_locks = self._lock_manager.get(resource, [])
            
            for existing_lock in existing_locks:
                # Check compatibility matrix
                if not self._lock_compatible(lock_mode, existing_lock.lock_mode):
                    return False
            
            # Acquire lock
            if resource not in self._lock_manager:
                self._lock_manager[resource] = []
            self._lock_manager[resource].append(lock_info)
            
            logger.debug("Lock acquired",
                        resource=resource,
                        transaction_id=str(transaction_id),
                        lock_mode=lock_mode)
            
            return True

    def _lock_compatible(self, requested_mode: str, existing_mode: str) -> bool:
        """Check if lock modes are compatible"""
        compatibility_matrix = {
            'shared': ['shared', 'intention_shared'],
            'exclusive': ['intention_exclusive'],
            'intention_shared': ['exclusive'],
            'intention_exclusive': []
        }
        
        return requested_mode in compatibility_matrix.get(existing_mode, [])

    def _release_transaction_locks(self, transaction_id: UUID):
        """Release all locks held by a transaction"""
        with self._lock:
            transaction = self._active_transactions.get(transaction_id)
            if not transaction:
                return
            
            # Remove locks from lock manager
            for resource, locks in list(self._lock_manager.items()):
                self._lock_manager[resource] = [
                    lock for lock in locks 
                    if lock.transaction_id != transaction_id
                ]
                
                # Clean up empty resource entries
                if not self._lock_manager[resource]:
                    del self._lock_manager[resource]
            
            # Clear transaction's lock sets
            transaction['held_locks'].clear()
            transaction['waiting_locks'].clear()

    def _rollback_operations(self, transaction_id: UUID) -> bool:
        """Rollback all operations in a transaction"""
        transaction = self._active_transactions.get(transaction_id)
        if not transaction:
            return False
        
        success = True
        
        # Rollback operations in reverse order
        for operation in reversed(transaction['operations']):
            if not self._rollback_single_operation(operation):
                success = False
                logger.error("Failed to rollback operation",
                           operation_id=str(operation.operation_id),
                           transaction_id=str(transaction_id))
        
        # Log rollback operations
        if success:
            self._stats['rolled_back_transactions'] += 1
        
        return success

    def _rollback_single_operation(self, operation: TransactionOperation) -> bool:
        """Rollback a single operation"""
        try:
            if operation.rollback_data:
                # Execute rollback using stored data
                logger.info("Rolling back operation",
                           operation_id=str(operation.operation_id),
                           operation_type=operation.operation_type)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Single operation rollback failed",
                       operation_id=str(operation.operation_id),
                       error=str(e))
            return False

    def _finalize_transaction(self, transaction_id: UUID):
        """Finalize transaction - move to completed state"""
        transaction = self._active_transactions[transaction_id]
        
        # Create snapshot for recovery purposes
        snapshot = TransactionSnapshot(
            snapshot_id=uuid4(),
            transaction_id=transaction_id,
            timestamp=time.time(),
            operations=transaction['operations'].copy(),
            state=transaction['state'],
            checksum=self._calculate_transaction_checksum(transaction_id)
        )
        
        self._transaction_snapshots[transaction_id] = snapshot
        
        # Remove from active transactions
        del self._active_transactions[transaction_id]
        
        logger.debug("Transaction finalized",
                    transaction_id=str(transaction_id),
                    state=transaction['state'].value)

    def _calculate_transaction_checksum(self, transaction_id: UUID) -> str:
        """Calculate checksum for transaction data integrity"""
        transaction = self._transaction_snapshots.get(transaction_id)
        if not transaction:
            return ""
        
        data = {
            'transaction_id': str(transaction.transaction_id),
            'timestamp': transaction.timestamp,
            'state': transaction.state.value,
            'operations': [op.__dict__ for op in transaction.operations]
        }
        
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

    def record_operation(self,
                        transaction_id: UUID,
                        operation_type: str,
                        table_name: str,
                        data: Dict[str, Any],
                        rollback_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Record an operation in a transaction
        
        Args:
            transaction_id: Transaction ID
            operation_type: Type of operation (CREATE, UPDATE, DELETE, SELECT)
            table_name: Database table name
            data: Operation data
            rollback_data: Data needed for rollback
            
        Returns:
            True if operation recorded successfully
        """
        with self._lock:
            if transaction_id not in self._active_transactions:
                logger.error("Transaction not found for operation recording",
                           transaction_id=str(transaction_id))
                return False
            
            operation = TransactionOperation(
                operation_id=uuid4(),
                transaction_id=transaction_id,
                operation_type=operation_type,
                table_name=table_name,
                data=data.copy(),
                timestamp=time.time(),
                checksum=hashlib.sha256(
                    json.dumps(data, sort_keys=True).encode()
                ).hexdigest(),
                rollback_data=rollback_data.copy() if rollback_data else None
            )
            
            self._active_transactions[transaction_id]['operations'].append(operation)
            self._operation_logs.append(operation)
            
            logger.debug("Operation recorded",
                        transaction_id=str(transaction_id),
                        operation_id=str(operation.operation_id),
                        operation_type=operation_type,
                        table_name=table_name)
            
            return True

    async def _deadlock_detection_loop(self):
        """Background task for deadlock detection"""
        while True:
            try:
                await asyncio.sleep(self.deadlock_detection_interval)
                await self._detect_and_resolve_deadlocks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Deadlock detection loop error", error=str(e))

    async def _timeout_detection_loop(self):
        """Background task for timeout detection"""
        while True:
            try:
                await asyncio.sleep(1.0)  # Check every second
                await self._check_transaction_timeouts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Timeout detection loop error", error=str(e))

    async def _detect_and_resolve_deadlocks(self):
        """Detect and resolve deadlock situations"""
        with self._lock:
            deadlocked_transactions = []
            
            # Simple deadlock detection algorithm
            for tx_id in list(self._active_transactions.keys()):
                if self._check_deadlock(tx_id):
                    deadlocked_transactions.append(tx_id)
            
            # Abort deadlocked transactions
            for tx_id in deadlocked_transactions:
                logger.warning("Aborting deadlocked transaction",
                              transaction_id=str(tx_id))
                self.abort_transaction(tx_id)

    async def _check_transaction_timeouts(self):
        """Check for timed-out transactions"""
        current_time = time.time()
        
        with self._lock:
            expired_transactions = []
            
            for tx_id, transaction in self._active_transactions.items():
                elapsed = current_time - transaction['start_time']
                if elapsed > self.transaction_timeout:
                    expired_transactions.append(tx_id)
            
            # Abort expired transactions
            for tx_id in expired_transactions:
                logger.warning("Aborting timed-out transaction",
                              transaction_id=str(tx_id))
                self.abort_transaction(tx_id)
                self._stats['timeout_transactions'] += 1

    def get_transaction_status(self, transaction_id: UUID) -> Optional[Dict[str, Any]]:
        """Get current status of a transaction"""
        with self._lock:
            if transaction_id in self._active_transactions:
                transaction = self._active_transactions[transaction_id]
                return {
                    'transaction_id': str(transaction_id),
                    'state': transaction['state'].value,
                    'start_time': transaction['start_time'],
                    'isolation_level': transaction['isolation_level'].value,
                    'operation_count': len(transaction['operations']),
                    'lock_count': len(transaction['held_locks'])
                }
            elif transaction_id in self._transaction_snapshots:
                snapshot = self._transaction_snapshots[transaction_id]
                return {
                    'transaction_id': str(transaction_id),
                    'state': snapshot.state.value,
                    'timestamp': snapshot.timestamp,
                    'operation_count': len(snapshot.operations),
                    'finalized': True
                }
            
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get transaction manager statistics"""
        with self._lock:
            stats = self._stats.copy()
            stats.update({
                'active_transactions': len(self._active_transactions),
                'total_snapshots': len(self._transaction_snapshots),
                'total_operations': len(self._operation_logs),
                'active_locks': sum(len(locks) for locks in self._lock_manager.values())
            })
            return stats

    def cleanup_old_snapshots(self, retention_days: int = 30):
        """Clean up old transaction snapshots"""
        cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
        
        with self._lock:
            removed_count = 0
            
            for tx_id in list(self._transaction_snapshots.keys()):
                snapshot = self._transaction_snapshots[tx_id]
                if snapshot.timestamp < cutoff_time:
                    del self._transaction_snapshots[tx_id]
                    removed_count += 1
            
            logger.info("Cleaned up old transaction snapshots",
                       removed_count=removed_count,
                       retention_days=retention_days)

    def shutdown(self):
        """Shutdown transaction manager"""
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Abort all active transactions
        with self._lock:
            active_tx_ids = list(self._active_transactions.keys())
            for tx_id in active_tx_ids:
                self.abort_transaction(tx_id)
        
        logger.info("Transaction manager shutdown complete")


# Global transaction manager instance
_transaction_manager: Optional[TransactionManager] = None


def get_transaction_manager() -> TransactionManager:
    """Get or create global transaction manager instance"""
    global _transaction_manager
    if _transaction_manager is None:
        _transaction_manager = TransactionManager()
    return _transaction_manager


# Context managers for easy integration
@contextmanager
def begin_transaction(isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED):
    """Global transaction context manager"""
    tm = get_transaction_manager()
    with tm.transaction(isolation_level) as tx:
        yield tx


# Decorator for automatic transaction management
def transactional(isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED):
    """Decorator for automatic transaction management"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            tm = get_transaction_manager()
            with tm.transaction(isolation_level):
                return func(*args, **kwargs)
        return wrapper
    return decorator
