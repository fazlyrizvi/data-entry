"""
Enterprise Database Synchronization System

A comprehensive solution for real-time and batch database synchronization
across PostgreSQL, MongoDB, MySQL, and other enterprise databases.
"""

__version__ = "1.0.0"
__author__ = "Enterprise Integration Team"

from .core.base_connector import BaseConnector
from .core.sync_manager import SyncManager
from .core.change_event import ChangeEvent
from .core.conflict_resolver import ConflictResolver
from .core.connection_pool import ConnectionPool
from .core.transaction_manager import TransactionManager
from .core.error_recovery import ErrorRecovery

__all__ = [
    "BaseConnector",
    "SyncManager", 
    "ChangeEvent",
    "ConflictResolver",
    "ConnectionPool",
    "TransactionManager",
    "ErrorRecovery",
]
