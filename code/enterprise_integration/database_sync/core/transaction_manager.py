"""
Transaction Management

Provides distributed transaction management for multi-database operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json
from contextlib import asynccontextmanager


class TransactionStatus(Enum):
    """Transaction status."""
    PENDING = "PENDING"
    PREPARING = "PREPARING"
    PREPARED = "PREPARED"
    COMMITTING = "COMMITTING"
    COMMITTED = "COMMITTED"
    ROLLING_BACK = "ROLLING_BACK"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class TransactionState(Enum):
    """Transaction state in state machine."""
    INITIATED = "INITIATED"
    PHASE_1 = "PHASE_1"  # Prepare phase
    PHASE_2 = "PHASE_2"  # Commit phase
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


@dataclass
class TransactionOperation:
    """Represents an operation within a transaction."""
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    database_id: str = ""
    operation_type: str = ""  # SQL, STORED_PROCEDURE, etc.
    sql: str = ""
    parameters: Optional[tuple] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    executed_at: Optional[datetime] = None
    order: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'operation_id': self.operation_id,
            'database_id': self.database_id,
            'operation_type': self.operation_type,
            'sql': self.sql,
            'parameters': self.parameters,
            'result': str(self.result) if self.result else None,
            'error': self.error,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'order': self.order
        }


@dataclass
class DistributedTransaction:
    """Represents a distributed transaction across multiple databases."""
    
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TransactionStatus = TransactionStatus.PENDING
    state: TransactionState = TransactionState.INITIATED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_seconds: int = 300
    
    # Transaction participants
    participants: List[str] = field(default_factory=list)
    operations: List[TransactionOperation] = field(default_factory=list)
    
    # Two-phase commit metadata
    prepared_operations: Dict[str, bool] = field(default_factory=dict)
    commit_votes: Dict[str, bool] = field(default_factory=dict)
    
    # Error handling
    error_message: Optional[str] = None
    rollback_reason: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    
    def add_operation(self, operation: TransactionOperation) -> None:
        """Add an operation to the transaction."""
        operation.order = len(self.operations)
        self.operations.append(operation)
        
        if operation.database_id not in self.participants:
            self.participants.append(operation.database_id)
    
    def mark_operation_executed(self, operation_id: str, result: Any = None, error: str = None) -> None:
        """Mark an operation as executed."""
        for operation in self.operations:
            if operation.operation_id == operation_id:
                operation.executed_at = datetime.now()
                if error:
                    operation.error = error
                else:
                    operation.result = result
                break
    
    def is_all_operations_executed(self) -> bool:
        """Check if all operations have been executed."""
        return all(op.executed_at is not None or op.error is not None for op in self.operations)
    
    def has_errors(self) -> bool:
        """Check if any operation has errors."""
        return any(op.error for op in self.operations)
    
    def get_operations_by_database(self, database_id: str) -> List[TransactionOperation]:
        """Get operations for a specific database."""
        return [op for op in self.operations if op.database_id == database_id]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'transaction_id': self.transaction_id,
            'status': self.status.value,
            'state': self.state.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'timeout_seconds': self.timeout_seconds,
            'participants': self.participants,
            'operations': [op.to_dict() for op in self.operations],
            'prepared_operations': self.prepared_operations,
            'commit_votes': self.commit_votes,
            'error_message': self.error_message,
            'rollback_reason': self.rollback_reason,
            'metadata': self.metadata,
            'retry_count': self.retry_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DistributedTransaction':
        """Create transaction from dictionary."""
        tx = cls(
            transaction_id=data['transaction_id'],
            status=TransactionStatus(data['status']),
            state=TransactionState(data['state']),
            created_at=datetime.fromisoformat(data['created_at']),
            timeout_seconds=data['timeout_seconds'],
            participants=data['participants'],
            retry_count=data['retry_count']
        )
        
        if data.get('started_at'):
            tx.started_at = datetime.fromisoformat(data['started_at'])
        
        if data.get('completed_at'):
            tx.completed_at = datetime.fromisoformat(data['completed_at'])
        
        if data.get('error_message'):
            tx.error_message = data['error_message']
        
        if data.get('rollback_reason'):
            tx.rollback_reason = data['rollback_reason']
        
        tx.metadata = data.get('metadata', {})
        tx.prepared_operations = data.get('prepared_operations', {})
        tx.commit_votes = data.get('commit_votes', {})
        
        for op_data in data.get('operations', []):
            op = TransactionOperation(
                operation_id=op_data['operation_id'],
                database_id=op_data['database_id'],
                operation_type=op_data['operation_type'],
                sql=op_data['sql'],
                parameters=op_data.get('parameters'),
                order=op_data['order']
            )
            
            if op_data.get('executed_at'):
                op.executed_at = datetime.fromisoformat(op_data['executed_at'])
            
            if op_data.get('error'):
                op.error = op_data['error']
            
            tx.operations.append(op)
        
        return tx


class TransactionManager:
    """Manages distributed transactions across multiple databases."""
    
    def __init__(self, 
                 max_transactions: int = 1000,
                 cleanup_interval: int = 3600,
                 default_timeout: int = 300):
        
        self.max_transactions = max_transactions
        self.cleanup_interval = cleanup_interval
        self.default_timeout = default_timeout
        
        self._active_transactions: Dict[str, DistributedTransaction] = {}
        self._completed_transactions: Dict[str, DistributedTransaction] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._transaction_lock = asyncio.Lock()
        
        self.logger = logging.getLogger(__name__)
    
    async def start(self) -> None:
        """Start the transaction manager."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.logger.info("Transaction manager started")
    
    async def stop(self) -> None:
        """Stop the transaction manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Transaction manager stopped")
    
    async def create_transaction(self, 
                                timeout_seconds: Optional[int] = None,
                                metadata: Optional[Dict[str, Any]] = None) -> DistributedTransaction:
        """Create a new distributed transaction."""
        async with self._transaction_lock:
            if len(self._active_transactions) >= self.max_transactions:
                # Clean up old completed transactions
                await self._cleanup_transactions()
                
                if len(self._active_transactions) >= self.max_transactions:
                    raise Exception("Maximum number of active transactions reached")
            
            timeout = timeout_seconds or self.default_timeout
            transaction = DistributedTransaction(timeout_seconds=timeout)
            if metadata:
                transaction.metadata.update(metadata)
            
            self._active_transactions[transaction.transaction_id] = transaction
            self.logger.info(f"Created transaction {transaction.transaction_id}")
            return transaction
    
    async def add_operation(self, 
                           transaction_id: str,
                           database_id: str,
                           operation_type: str,
                           sql: str,
                           parameters: Optional[tuple] = None) -> str:
        """Add an operation to a transaction."""
        async with self._transaction_lock:
            if transaction_id not in self._active_transactions:
                raise Exception(f"Transaction {transaction_id} not found")
            
            transaction = self._active_transactions[transaction_id]
            operation = TransactionOperation(
                database_id=database_id,
                operation_type=operation_type,
                sql=sql,
                parameters=parameters
            )
            
            transaction.add_operation(operation)
            self.logger.debug(f"Added operation {operation.operation_id} to transaction {transaction_id}")
            return operation.operation_id
    
    async def execute_transaction(self, 
                                 transaction: DistributedTransaction,
                                 execute_operation_func: Callable[[TransactionOperation], Any]) -> bool:
        """Execute a transaction using two-phase commit."""
        try:
            transaction.status = TransactionStatus.PREPARING
            transaction.state = TransactionState.PHASE_1
            transaction.started_at = datetime.now()
            
            # Phase 1: Prepare all operations
            all_prepared = await self._prepare_phase(transaction, execute_operation_func)
            
            if not all_prepared:
                await self._rollback_transaction(transaction)
                return False
            
            # Phase 2: Commit all operations
            success = await self._commit_phase(transaction, execute_operation_func)
            
            if success:
                await self._complete_transaction(transaction, TransactionStatus.COMMITTED)
            else:
                await self._rollback_transaction(transaction)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error executing transaction {transaction.transaction_id}: {e}")
            await self._rollback_transaction(transaction, str(e))
            return False
    
    async def rollback_transaction(self, transaction_id: str, reason: str = "Manual rollback") -> bool:
        """Rollback a transaction."""
        async with self._transaction_lock:
            if transaction_id not in self._active_transactions:
                return False
            
            transaction = self._active_transactions[transaction_id]
            return await self._rollback_transaction(transaction, reason)
    
    async def get_transaction(self, transaction_id: str) -> Optional[DistributedTransaction]:
        """Get a transaction by ID."""
        return self._active_transactions.get(transaction_id) or self._completed_transactions.get(transaction_id)
    
    async def get_active_transactions(self) -> List[DistributedTransaction]:
        """Get all active transactions."""
        return list(self._active_transactions.values())
    
    async def get_transaction_stats(self) -> Dict[str, Any]:
        """Get transaction statistics."""
        async with self._transaction_lock:
            now = datetime.now()
            
            active_by_status = {}
            for tx in self._active_transactions.values():
                status = tx.status.value
                active_by_status[status] = active_by_status.get(status, 0) + 1
            
            completed_by_status = {}
            for tx in self._completed_transactions.values():
                status = tx.status.value
                completed_by_status[status] = completed_by_status.get(status, 0) + 1
            
            # Calculate average execution time
            completed_with_time = [tx for tx in self._completed_transactions.values() 
                                 if tx.completed_at and tx.started_at]
            avg_execution_time = 0
            if completed_with_time:
                total_time = sum((tx.completed_at - tx.started_at).total_seconds() 
                               for tx in completed_with_time)
                avg_execution_time = total_time / len(completed_with_time)
            
            return {
                'active_transactions': len(self._active_transactions),
                'completed_transactions': len(self._completed_transactions),
                'active_by_status': active_by_status,
                'completed_by_status': completed_by_status,
                'average_execution_time_seconds': avg_execution_time,
                'max_concurrent_transactions': len(self._active_transactions),
                'current_time': now.isoformat()
            }
    
    async def _prepare_phase(self, 
                           transaction: DistributedTransaction,
                           execute_operation_func: Callable[[TransactionOperation], Any]) -> bool:
        """Phase 1: Prepare all operations."""
        try:
            for operation in transaction.operations:
                try:
                    # Execute the operation in prepare mode
                    await execute_operation_func(operation, prepare=True)
                    transaction.prepared_operations[operation.operation_id] = True
                except Exception as e:
                    self.logger.error(f"Prepare failed for operation {operation.operation_id}: {e}")
                    transaction.prepared_operations[operation.operation_id] = False
                    transaction.error_message = f"Prepare phase failed: {str(e)}"
                    return False
            
            transaction.status = TransactionStatus.PREPARED
            return True
            
        except Exception as e:
            self.logger.error(f"Prepare phase failed for transaction {transaction.transaction_id}: {e}")
            transaction.error_message = f"Prepare phase failed: {str(e)}"
            return False
    
    async def _commit_phase(self, 
                          transaction: DistributedTransaction,
                          execute_operation_func: Callable[[TransactionOperation], Any]) -> bool:
        """Phase 2: Commit all operations."""
        try:
            transaction.status = TransactionStatus.COMMITTING
            transaction.state = TransactionState.PHASE_2
            
            for operation in transaction.operations:
                if transaction.prepared_operations.get(operation.operation_id):
                    try:
                        await execute_operation_func(operation, commit=True)
                    except Exception as e:
                        self.logger.error(f"Commit failed for operation {operation.operation_id}: {e}")
                        transaction.error_message = f"Commit phase failed: {str(e)}"
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Commit phase failed for transaction {transaction.transaction_id}: {e}")
            transaction.error_message = f"Commit phase failed: {str(e)}"
            return False
    
    async def _rollback_transaction(self, transaction: DistributedTransaction, reason: str = None) -> bool:
        """Rollback a transaction."""
        try:
            transaction.status = TransactionStatus.ROLLING_BACK
            transaction.rollback_reason = reason
            
            # Execute rollback for all operations
            for operation in transaction.operations:
                try:
                    await execute_operation_func(operation, rollback=True)
                except Exception as e:
                    self.logger.error(f"Rollback failed for operation {operation.operation_id}: {e}")
            
            await self._complete_transaction(transaction, TransactionStatus.ROLLED_BACK)
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed for transaction {transaction.transaction_id}: {e}")
            await self._complete_transaction(transaction, TransactionStatus.FAILED)
            return False
    
    async def _complete_transaction(self, transaction: DistributedTransaction, status: TransactionStatus) -> None:
        """Complete a transaction and move to completed list."""
        async with self._transaction_lock:
            transaction.status = status
            transaction.state = TransactionState.COMPLETED if status == TransactionStatus.COMMITTED else TransactionState.ABORTED
            transaction.completed_at = datetime.now()
            
            if transaction.transaction_id in self._active_transactions:
                del self._active_transactions[transaction.transaction_id]
            
            self._completed_transactions[transaction.transaction_id] = transaction
            
            self.logger.info(f"Transaction {transaction.transaction_id} completed with status {status.value}")
    
    async def _cleanup_transactions(self) -> None:
        """Clean up old completed transactions."""
        async with self._transaction_lock:
            # Keep only recent completed transactions
            if len(self._completed_transactions) > self.max_transactions:
                sorted_transactions = sorted(
                    self._completed_transactions.items(),
                    key=lambda x: x[1].completed_at or x[1].created_at
                )
                
                # Remove oldest 50% of completed transactions
                to_remove = len(sorted_transactions) // 2
                for transaction_id, _ in sorted_transactions[:to_remove]:
                    del self._completed_transactions[transaction_id]
    
    async def _cleanup_loop(self) -> None:
        """Background task for cleaning up old transactions."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_transactions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
    
    @asynccontextmanager
    async def transaction_context(self, 
                                 timeout_seconds: Optional[int] = None,
                                 metadata: Optional[Dict[str, Any]] = None):
        """Context manager for transactions."""
        transaction = None
        try:
            transaction = await self.create_transaction(timeout_seconds, metadata)
            yield transaction
        finally:
            if transaction and transaction.transaction_id in self._active_transactions:
                await self._rollback_transaction(transaction, "Transaction context exited")
    
    async def add_operation_to_context(self, 
                                     transaction_id: str,
                                     database_id: str,
                                     operation_type: str,
                                     sql: str,
                                     parameters: Optional[tuple] = None) -> str:
        """Add operation to transaction context."""
        return await self.add_operation(transaction_id, database_id, operation_type, sql, parameters)


class AsyncTransactionManager(TransactionManager):
    """Asynchronous transaction manager."""
    
    async def execute_async_operations(self, 
                                      transaction: DistributedTransaction,
                                      execute_async_func: Callable[[TransactionOperation], Any]) -> bool:
        """Execute transaction with async operations."""
        return await self.execute_transaction(transaction, execute_async_func)


class SyncTransactionManager(TransactionManager):
    """Synchronous transaction manager."""
    
    async def execute_sync_operations(self, 
                                     transaction: DistributedTransaction,
                                     execute_sync_func: Callable[[TransactionOperation], Any]) -> bool:
        """Execute transaction with sync operations."""
        return await self.execute_transaction(transaction, execute_sync_func)
