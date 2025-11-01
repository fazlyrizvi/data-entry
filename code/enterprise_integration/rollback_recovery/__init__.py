"""
Rollback and Recovery System

An enterprise-grade solution for managing data operations with robust rollback capabilities,
backup and restore functionality, and disaster recovery procedures.
"""

from .main import RollbackRecoverySystem, get_system
from .transaction_manager import (
    TransactionManager,
    get_transaction_manager,
    TransactionState,
    IsolationLevel,
    TransactionOperation,
    TransactionSnapshot,
    LockInfo
)
from .backup_handler import (
    BackupHandler,
    get_backup_handler,
    BackupType,
    BackupStatus,
    CompressionType,
    BackupMetadata,
    DataChunk
)
from .recovery_orchestrator import (
    RecoveryOrchestrator,
    get_recovery_orchestrator,
    RecoveryType,
    RecoveryStatus,
    ConflictResolutionStrategy,
    RecoveryOperation,
    RecoveryPlan,
    ConsistencyCheck
)

__version__ = "1.0.0"
__author__ = "Enterprise Integration Team"

__all__ = [
    # Main system
    "RollbackRecoverySystem",
    "get_system",
    
    # Transaction management
    "TransactionManager",
    "get_transaction_manager",
    "TransactionState",
    "IsolationLevel",
    "TransactionOperation",
    "TransactionSnapshot",
    "LockInfo",
    
    # Backup handling
    "BackupHandler",
    "get_backup_handler",
    "BackupType",
    "BackupStatus",
    "CompressionType",
    "BackupMetadata",
    "DataChunk",
    
    # Recovery orchestration
    "RecoveryOrchestrator",
    "get_recovery_orchestrator",
    "RecoveryType",
    "RecoveryStatus",
    "ConflictResolutionStrategy",
    "RecoveryOperation",
    "RecoveryPlan",
    "ConsistencyCheck"
]
