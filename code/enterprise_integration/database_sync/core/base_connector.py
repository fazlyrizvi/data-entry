"""
Base Database Connector Interface

Defines the common interface for all database connectors.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime


class ConnectorType(Enum):
    """Supported database connector types."""
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    MYSQL = "mysql"
    ORACLE = "oracle"
    SQLSERVER = "sqlserver"
    SQLITE = "sqlite"


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_mode: Optional[str] = None
    timeout: int = 30
    max_connections: int = 10
    connection_string: Optional[str] = None


@dataclass
class SyncOperation:
    """Represents a synchronization operation."""
    operation_id: str
    source_table: str
    target_table: str
    operation_type: str  # INSERT, UPDATE, DELETE, BULK
    data: Optional[Dict[str, Any]] = None
    conditions: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseConnector(ABC):
    """Abstract base class for database connectors."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection_pool = None
        self.is_connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the database."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection to the database."""
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        pass
    
    @abstractmethod
    async def execute_operation(self, operation: SyncOperation) -> bool:
        """Execute a synchronization operation."""
        pass
    
    @abstractmethod
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get the schema of a table."""
        pass
    
    @abstractmethod
    async def get_changes(self, last_position: Optional[Any] = None) -> List[SyncOperation]:
        """Get changes since the last position (for CDC)."""
        pass
    
    @abstractmethod
    async def apply_changes(self, operations: List[SyncOperation]) -> bool:
        """Apply a batch of changes atomically."""
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate the database connection."""
        pass
    
    @abstractmethod
    def get_connector_type(self) -> ConnectorType:
        """Get the connector type."""
        pass
    
    async def begin_transaction(self) -> str:
        """Begin a new transaction."""
        transaction_id = f"txn_{datetime.now().timestamp()}"
        return transaction_id
    
    async def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a transaction."""
        return True
    
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a transaction."""
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the connection."""
        return {
            "status": "healthy" if self.is_connected else "unhealthy",
            "timestamp": datetime.now(),
            "connector_type": self.get_connector_type().value,
            "response_time_ms": 0
        }
    
    def __repr__(self):
        return f"{self.__class__.__name__}(host={self.config.host}, database={self.config.database})"


class BaseCDCConnector(BaseConnector):
    """Base class for Change Data Capture (CDC) connectors."""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.last_position = None
        self.change_stream = None
    
    @abstractmethod
    async def start_cdc(self, tables: List[str]) -> bool:
        """Start change data capture for specified tables."""
        pass
    
    @abstractmethod
    async def stop_cdc(self) -> bool:
        """Stop change data capture."""
        pass
    
    @abstractmethod
    async def get_current_position(self) -> Any:
        """Get the current CDC position."""
        pass
    
    @abstractmethod
    async def set_position(self, position: Any) -> bool:
        """Set the CDC position."""
        pass
