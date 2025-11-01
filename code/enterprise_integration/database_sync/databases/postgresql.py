"""
PostgreSQL Database Connector

Provides PostgreSQL-specific implementation for database synchronization.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import uuid

import asyncpg
from asyncpg import Pool, Connection

from ..core.base_connector import BaseCDCConnector, DatabaseConfig, SyncOperation, ConnectorType
from ..core.change_event import ChangeEvent, ChangeType
from ..core.connection_pool import AsyncConnectionPool, PooledConnection


class PostgreSQLConfig(DatabaseConfig):
    """PostgreSQL-specific configuration."""
    
    def __init__(self, 
                 host: str,
                 port: int,
                 database: str,
                 username: str,
                 password: str,
                 ssl_mode: Optional[str] = None,
                 timeout: int = 30,
                 max_connections: int = 10,
                 connection_string: Optional[str] = None,
                 # PostgreSQL-specific options
                 application_name: str = "database_sync",
                 prepared_statements: bool = True,
                 binary_protocol: bool = True,
                 server_settings: Optional[Dict[str, str]] = None):
        
        super().__init__(
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            ssl_mode=ssl_mode,
            timeout=timeout,
            max_connections=max_connections,
            connection_string=connection_string
        )
        
        self.application_name = application_name
        self.prepared_statements = prepared_statements
        self.binary_protocol = binary_protocol
        self.server_settings = server_settings or {}
    
    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        if self.connection_string:
            return self.connection_string
        
        scheme = "postgresql"
        if self.ssl_mode:
            scheme = "postgresql+ssl"
        
        auth = f"{self.username}:{self.password}"
        if "@" in self.username:
            # URL-encode username and password
            from urllib.parse import quote
            auth = f"{quote(self.username)}:{quote(self.password)}"
        
        return (f"{scheme}://{auth}@{self.host}:{self.port}/{self.database}"
                f"?application_name={self.application_name}")


class PostgreSQLPool(AsyncConnectionPool):
    """PostgreSQL connection pool."""
    
    def __init__(self, config: PostgreSQLConfig, **kwargs):
        self.config = config
        super().__init__(
            pool_name=f"postgresql_{config.database}_{config.host}",
            max_connections=config.max_connections,
            **kwargs
        )
    
    async def _create_connection(self) -> Optional[PooledConnection]:
        """Create a new PostgreSQL connection."""
        try:
            connection = await asyncpg.connect(
                self.config.get_connection_string(),
                server_settings=self.config.server_settings,
                timeout=self.config.timeout
            )
            
            pooled_conn = PooledConnection(
                connection_id=str(uuid.uuid4()),
                connection=connection
            )
            
            self.logger.debug(f"Created PostgreSQL connection {pooled_conn.connection_id}")
            return pooled_conn
            
        except Exception as e:
            self.logger.error(f"Failed to create PostgreSQL connection: {e}")
            return None
    
    async def _close_connection(self, pooled_conn: PooledConnection) -> None:
        """Close a PostgreSQL connection."""
        try:
            if pooled_conn.connection:
                await pooled_conn.connection.close()
            self.logger.debug(f"Closed PostgreSQL connection {pooled_conn.connection_id}")
        except Exception as e:
            self.logger.error(f"Error closing PostgreSQL connection: {e}")
    
    async def _validate_connection(self, pooled_conn: PooledConnection) -> bool:
        """Validate a PostgreSQL connection."""
        try:
            if pooled_conn.connection:
                await pooled_conn.connection.fetchval("SELECT 1")
                return True
        except Exception:
            pass
        return False


class PostgreSQLConnector(BaseCDCConnector):
    """PostgreSQL database connector with CDC support."""
    
    def __init__(self, config: PostgreSQLConfig):
        super().__init__(config)
        self.config = config
        self.pool = None
        self.change_stream = None
        self.is_connected = False
        
        self.logger = logging.getLogger(__name__)
        
        # CDC settings
        self.cdc_enabled = False
        self.cdc_tables = []
        self.last_lsn = None  # Last log sequence number
    
    async def connect(self) -> bool:
        """Establish connection to PostgreSQL."""
        try:
            self.pool = PostgreSQLPool(self.config)
            initialized = await self.pool.initialize()
            
            if initialized:
                self.is_connected = True
                self.logger.info(f"Connected to PostgreSQL: {self.config.host}:{self.config.port}/{self.config.database}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Close connection to PostgreSQL."""
        try:
            if self.pool:
                await self.pool.cleanup()
                self.pool = None
            
            self.is_connected = False
            self.cdc_enabled = False
            self.logger.info("Disconnected from PostgreSQL")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from PostgreSQL: {e}")
            return False
    
    async def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        if not self.is_connected:
            raise Exception("Not connected to PostgreSQL")
        
        try:
            async with self.pool.execute_with_connection(
                self._execute_query_impl, query, params
            ) as results:
                return results
                
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise
    
    async def _execute_query_impl(self, connection, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Implementation of query execution."""
        rows = await connection.fetch(query, *params if params else [])
        return [dict(row) for row in rows]
    
    async def execute_operation(self, operation: SyncOperation) -> bool:
        """Execute a synchronization operation."""
        if not self.is_connected:
            raise Exception("Not connected to PostgreSQL")
        
        try:
            async with self.pool.execute_with_connection(
                self._execute_operation_impl, operation
            ):
                return True
                
        except Exception as e:
            self.logger.error(f"Operation execution failed: {e}")
            return False
    
    async def _execute_operation_impl(self, connection, operation: SyncOperation) -> None:
        """Implementation of operation execution."""
        if operation.operation_type == "INSERT":
            await self._execute_insert(connection, operation)
        elif operation.operation_type == "UPDATE":
            await self._execute_update(connection, operation)
        elif operation.operation_type == "DELETE":
            await self._execute_delete(connection, operation)
        else:
            raise ValueError(f"Unsupported operation type: {operation.operation_type}")
    
    async def _execute_insert(self, connection, operation: SyncOperation):
        """Execute INSERT operation."""
        if not operation.data:
            raise ValueError("Insert operation requires data")
        
        columns = list(operation.data.keys())
        values = list(operation.data.values())
        placeholders = [f"${i+1}" for i in range(len(values))]
        
        query = f"""
            INSERT INTO {operation.target_table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        await connection.execute(query, *values)
    
    async def _execute_update(self, connection, operation: SyncOperation):
        """Execute UPDATE operation."""
        if not operation.data:
            raise ValueError("Update operation requires data")
        
        if not operation.conditions:
            raise ValueError("Update operation requires conditions")
        
        set_clauses = []
        values = []
        param_count = 0
        
        for column, value in operation.data.items():
            param_count += 1
            set_clauses.append(f"{column} = ${param_count}")
            values.append(value)
        
        where_clauses = []
        for column, value in operation.conditions.items():
            param_count += 1
            where_clauses.append(f"{column} = ${param_count}")
            values.append(value)
        
        query = f"""
            UPDATE {operation.target_table}
            SET {', '.join(set_clauses)}
            WHERE {' AND '.join(where_clauses)}
        """
        
        await connection.execute(query, *values)
    
    async def _execute_delete(self, connection, operation: SyncOperation):
        """Execute DELETE operation."""
        if not operation.conditions:
            raise ValueError("Delete operation requires conditions")
        
        where_clauses = []
        values = []
        param_count = 0
        
        for column, value in operation.conditions.items():
            param_count += 1
            where_clauses.append(f"{column} = ${param_count}")
            values.append(value)
        
        query = f"""
            DELETE FROM {operation.target_table}
            WHERE {' AND '.join(where_clauses)}
        """
        
        await connection.execute(query, *values)
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get the schema of a table."""
        query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_name = $1 AND table_schema = 'public'
            ORDER BY ordinal_position
        """
        
        rows = await self.execute_query(query, (table_name,))
        
        return {
            'table_name': table_name,
            'columns': rows,
            'primary_keys': await self._get_primary_keys(table_name)
        }
    
    async def _get_primary_keys(self, table_name: str) -> List[str]:
        """Get primary keys for a table."""
        query = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = $1 
                AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.ordinal_position
        """
        
        rows = await self.execute_query(query, (table_name,))
        return [row['column_name'] for row in rows]
    
    async def get_changes(self, last_position: Optional[Any] = None) -> List[SyncOperation]:
        """Get changes since the last position (for CDC)."""
        if not self.cdc_enabled:
            return []
        
        try:
            # Use logical decoding for PostgreSQL
            changes = await self._get_logical_decoding_changes(last_position)
            return [self._change_to_operation(change) for change in changes]
            
        except Exception as e:
            self.logger.error(f"Failed to get CDC changes: {e}")
            return []
    
    async def _get_logical_decoding_changes(self, last_lsn: Optional[str]) -> List[Dict[str, Any]]:
        """Get changes using logical decoding."""
        if not last_lsn:
            # Get current LSN position
            query = "SELECT pg_current_wal_lsn() as lsn"
            result = await self.execute_query(query)
            if result:
                last_lsn = result[0]['lsn']
        
        # This is a simplified implementation
        # In practice, you'd use pgoutput plugin or similar
        changes = []
        
        # Example: Get recent WAL entries (requires superuser privileges)
        if last_lsn:
            query = """
                SELECT 
                    lsn,
                    xid,
                    data
                FROM pg_logical_slot_get_binary_changes(
                    'replication_slot',
                    $1,
                    NULL,
                    'proto-version', '1',
                    'publication-names', 'mypublication'
                )
            """
            
            try:
                rows = await self.execute_query(query, (last_lsn,))
                for row in rows:
                    change = self._parse_wal_entry(row)
                    if change:
                        changes.append(change)
            except Exception as e:
                self.logger.warning(f"Logical decoding not available: {e}")
                # Fallback to manual change tracking
        
        return changes
    
    def _parse_wal_entry(self, wal_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a WAL entry into a change event."""
        try:
            # Simplified WAL parsing - in practice, this would be more complex
            data = wal_entry['data']
            
            # Extract operation type, table, and values from WAL data
            # This is a placeholder implementation
            return {
                'lsn': wal_entry['lsn'],
                'xid': wal_entry['xid'],
                'operation': 'INSERT',  # Would be parsed from WAL data
                'table': 'table_name',  # Would be parsed from WAL data
                'values': {},  # Would be parsed from WAL data
                'old_values': {}
            }
        except Exception as e:
            self.logger.error(f"Failed to parse WAL entry: {e}")
            return None
    
    def _change_to_operation(self, change: Dict[str, Any]) -> SyncOperation:
        """Convert a change to a SyncOperation."""
        return SyncOperation(
            operation_id=str(uuid.uuid4()),
            source_table=change['table'],
            target_table=change['table'],  # Same table for now
            operation_type=change['operation'],
            data=change['values'],
            timestamp=datetime.now(),
            metadata={'lsn': change['lsn'], 'xid': change['xid']}
        )
    
    async def apply_changes(self, operations: List[SyncOperation]) -> bool:
        """Apply a batch of changes atomically."""
        if not operations:
            return True
        
        try:
            async with self.pool.execute_with_connection(
                self._apply_changes_impl, operations
            ):
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to apply changes: {e}")
            return False
    
    async def _apply_changes_impl(self, connection, operations: List[SyncOperation]) -> None:
        """Implementation of batch change application."""
        async with connection.transaction():
            for operation in operations:
                await self._execute_operation_impl(connection, operation)
    
    async def validate_connection(self) -> bool:
        """Validate the database connection."""
        try:
            async with self.pool.execute_with_connection(
                lambda conn: conn.fetchval("SELECT 1")
            ):
                return True
        except Exception:
            return False
    
    def get_connector_type(self) -> ConnectorType:
        """Get the connector type."""
        return ConnectorType.POSTGRESQL
    
    async def start_cdc(self, tables: List[str]) -> bool:
        """Start change data capture for specified tables."""
        try:
            # Enable logical decoding
            await self._enable_logical_decoding()
            
            # Create replication slot if needed
            await self._create_replication_slot()
            
            # Enable CDC for tables
            self.cdc_tables = tables
            self.cdc_enabled = True
            
            self.logger.info(f"Started CDC for tables: {tables}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start CDC: {e}")
            return False
    
    async def stop_cdc(self) -> bool:
        """Stop change data capture."""
        try:
            self.cdc_enabled = False
            self.cdc_tables = []
            
            # Drop replication slot
            await self._drop_replication_slot()
            
            self.logger.info("Stopped CDC")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop CDC: {e}")
            return False
    
    async def get_current_position(self) -> Any:
        """Get the current CDC position."""
        try:
            result = await self.execute_query("SELECT pg_current_wal_lsn() as lsn")
            if result:
                return result[0]['lsn']
        except Exception as e:
            self.logger.error(f"Failed to get current position: {e}")
        return None
    
    async def set_position(self, position: Any) -> bool:
        """Set the CDC position."""
        # For PostgreSQL, this would typically involve setting the replication slot position
        # Implementation depends on specific CDC mechanism used
        self.last_lsn = position
        return True
    
    async def _enable_logical_decoding(self):
        """Enable logical decoding on the PostgreSQL server."""
        # This requires superuser privileges
        try:
            await self.execute_query("ALTER SYSTEM SET wal_level = logical")
            # Note: In a real implementation, you'd need to reload configuration
            # or restart the server for this to take effect
        except Exception as e:
            self.logger.warning(f"Could not enable logical decoding: {e}")
    
    async def _create_replication_slot(self):
        """Create a replication slot for CDC."""
        try:
            await self.execute_query(
                "SELECT pg_create_logical_replication_slot('replication_slot', 'pgoutput')"
            )
        except Exception as e:
            if "already exists" not in str(e).lower():
                raise
            # Slot already exists, that's fine
    
    async def _drop_replication_slot(self):
        """Drop the replication slot."""
        try:
            await self.execute_query(
                "SELECT pg_drop_replication_slot('replication_slot')"
            )
        except Exception as e:
            self.logger.warning(f"Could not drop replication slot: {e}")
    
    async def begin_transaction(self) -> str:
        """Begin a new transaction."""
        # PostgreSQL transaction management is handled by the connection pool
        return f"pg_txn_{datetime.now().timestamp()}"
    
    async def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a transaction."""
        # Transactions are managed automatically by the connection pool
        return True
    
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a transaction."""
        # Transactions are managed automatically by the connection pool
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the connection."""
        try:
            start_time = datetime.now()
            
            # Check connection
            if not await self.validate_connection():
                return {
                    "status": "unhealthy",
                    "timestamp": datetime.now(),
                    "connector_type": self.get_connector_type().value,
                    "error": "Connection validation failed"
                }
            
            # Get server version
            version_result = await self.execute_query("SELECT version() as version")
            version = version_result[0]['version'] if version_result else "Unknown"
            
            # Get database stats
            stats_result = await self.execute_query("""
                SELECT 
                    numbackends,
                    xact_commit,
                    xact_rollback,
                    blks_read,
                    blks_hit,
                    tup_returned,
                    tup_fetched
                FROM pg_stat_database 
                WHERE datname = current_database()
            """)
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "timestamp": datetime.now(),
                "connector_type": self.get_connector_type().value,
                "response_time_ms": response_time,
                "server_version": version,
                "connection_count": stats_result[0]['numbackends'] if stats_result else 0,
                "transactions_committed": stats_result[0]['xact_commit'] if stats_result else 0,
                "transactions_rolled_back": stats_result[0]['xact_rollback'] if stats_result else 0,
                "cache_hit_ratio": self._calculate_cache_hit_ratio(stats_result[0]) if stats_result else 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now(),
                "connector_type": self.get_connector_type().value,
                "error": str(e)
            }
    
    def _calculate_cache_hit_ratio(self, stats: Dict[str, Any]) -> float:
        """Calculate cache hit ratio from database stats."""
        blks_read = stats.get('blks_read', 0)
        blks_hit = stats.get('blks_hit', 0)
        
        if blks_read + blks_hit == 0:
            return 0.0
        
        return blks_hit / (blks_read + blks_hit) * 100
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    def __repr__(self):
        return f"PostgreSQLConnector(host={self.config.host}, database={self.config.database})"


class PostgreSQLReplicationConnector(PostgreSQLConnector):
    """PostgreSQL connector with replication slot support."""
    
    def __init__(self, config: PostgreSQLConfig, slot_name: str = "replication_slot"):
        super().__init__(config)
        self.slot_name = slot_name
        self.publication_name = "sync_publication"
    
    async def start_cdc_with_replication(self, tables: List[str]) -> bool:
        """Start CDC using replication slots."""
        try:
            # Create publication for tables
            await self._create_publication(tables)
            
            # Create replication slot
            await self.execute_query(
                f"SELECT pg_create_logical_replication_slot('{self.slot_name}', 'pgoutput')"
            )
            
            self.cdc_enabled = True
            self.cdc_tables = tables
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start CDC with replication: {e}")
            return False
    
    async def _create_publication(self, tables: List[str]):
        """Create a publication for table replication."""
        # Create publication
        try:
            await self.execute_query(
                f"CREATE PUBLICATION {self.publication_name} FOR TABLE {', '.join(tables)}"
            )
        except Exception as e:
            if "already exists" not in str(e).lower():
                raise
    
    async def get_replication_changes(self, last_lsn: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get changes from replication slot."""
        try:
            if not last_lsn:
                # Get current position
                result = await self.execute_query("SELECT pg_current_wal_lsn() as lsn")
                if result:
                    last_lsn = result[0]['lsn']
            
            # Get changes from replication slot
            query = f"""
                SELECT lsn, xid, data
                FROM pg_logical_slot_get_binary_changes(
                    '{self.slot_name}',
                    '{last_lsn}',
                    NULL,
                    'proto-version', '1'
                )
            """
            
            rows = await self.execute_query(query)
            return [self._parse_replication_data(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"Failed to get replication changes: {e}")
            return []
    
    def _parse_replication_data(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Parse replication data from binary format."""
        # This would require proper pgoutput parsing
        # Simplified implementation
        return {
            'lsn': row['lsn'],
            'xid': row['xid'],
            'data': row['data'].hex(),  # Convert to hex for simplicity
            'operation': 'UNKNOWN',
            'table': 'unknown',
            'values': {},
            'old_values': {}
        }
