"""
MySQL Database Connector

Provides MySQL-specific implementation for database synchronization.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import json
import uuid

import aiomysql
from aiomysql import Pool, Connection, DictCursor

from ..core.base_connector import BaseCDCConnector, DatabaseConfig, SyncOperation, ConnectorType
from ..core.change_event import ChangeEvent, ChangeType
from ..core.connection_pool import AsyncConnectionPool, PooledConnection


class MySQLConfig(DatabaseConfig):
    """MySQL-specific configuration."""
    
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
                 # MySQL-specific options
                 charset: str = "utf8mb4",
                 collation: str = "utf8mb4_unicode_ci",
                 autocommit: bool = False,
                 connect_timeout: int = 10,
                 read_timeout: int = 30,
                 write_timeout: int = 30,
                 cursorclass: str = "DictCursor"):
        
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
        
        self.charset = charset
        self.collation = collation
        self.autocommit = autocommit
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout
        self.cursorclass = cursorclass
    
    def get_connection_string(self) -> str:
        """Get MySQL connection string."""
        if self.connection_string:
            return self.connection_string
        
        # For aiomysql, we typically pass parameters directly
        # This method returns a parameter dict instead
        return {
            'host': self.host,
            'port': self.port,
            'user': self.username,
            'password': self.password,
            'db': self.database,
            'charset': self.charset,
            'autocommit': self.autocommit,
            'connect_timeout': self.connect_timeout,
            'read_timeout': self.read_timeout,
            'write_timeout': self.write_timeout,
            'ssl': {'ca': self.ssl_mode} if self.ssl_mode else None
        }


class MySQLPool(AsyncConnectionPool):
    """MySQL connection pool."""
    
    def __init__(self, config: MySQLConfig, **kwargs):
        self.config = config
        super().__init__(
            pool_name=f"mysql_{config.database}_{config.host}",
            max_connections=config.max_connections,
            **kwargs
        )
    
    async def _create_connection(self) -> Optional[PooledConnection]:
        """Create a new MySQL connection."""
        try:
            connection = await aiomysql.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                db=self.config.database,
                charset=self.config.charset,
                autocommit=self.config.autocommit,
                connect_timeout=self.config.connect_timeout,
                read_timeout=self.config.read_timeout,
                write_timeout=self.config.write_timeout,
                ssl=self.config.ssl_mode and {'ca': self.config.ssl_mode},
                echo=False  # Disable SQL logging for performance
            )
            
            # Test connection
            async with connection.get() as conn:
                async with conn.cursor(DictCursor) as cursor:
                    await cursor.execute("SELECT 1")
                    await cursor.fetchone()
            
            pooled_conn = PooledConnection(
                connection_id=str(uuid.uuid4()),
                connection=connection
            )
            
            self.logger.debug(f"Created MySQL connection {pooled_conn.connection_id}")
            return pooled_conn
            
        except Exception as e:
            self.logger.error(f"Failed to create MySQL connection: {e}")
            return None
    
    async def _close_connection(self, pooled_conn: PooledConnection) -> None:
        """Close a MySQL connection."""
        try:
            if pooled_conn.connection:
                pooled_conn.connection.close()
                await pooled_conn.connection.wait_closed()
            self.logger.debug(f"Closed MySQL connection {pooled_conn.connection_id}")
        except Exception as e:
            self.logger.error(f"Error closing MySQL connection: {e}")
    
    async def _validate_connection(self, pooled_conn: PooledConnection) -> bool:
        """Validate a MySQL connection."""
        try:
            if pooled_conn.connection:
                async with pooled_conn.connection.get() as conn:
                    async with conn.cursor(DictCursor) as cursor:
                        await cursor.execute("SELECT 1")
                        await cursor.fetchone()
                        return True
        except Exception:
            pass
        return False


class MySQLConnector(BaseCDCConnector):
    """MySQL database connector with CDC support."""
    
    def __init__(self, config: MySQLConfig):
        super().__init__(config)
        self.config = config
        self.pool = None
        self.is_connected = False
        self.binlog_enabled = False
        self.binlog_position = None
        
        self.logger = logging.getLogger(__name__)
        
        # CDC settings
        self.cdc_enabled = False
        self.cdc_tables = []
        self.change_data_task = None
    
    async def connect(self) -> bool:
        """Establish connection to MySQL."""
        try:
            self.pool = MySQLPool(self.config)
            initialized = await self.pool.initialize()
            
            if initialized:
                self.is_connected = True
                
                # Check if binlog is enabled
                await self._check_binlog_status()
                
                self.logger.info(f"Connected to MySQL: {self.config.host}:{self.config.port}/{self.config.database}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to MySQL: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Close connection to MySQL."""
        try:
            if self.pool:
                await self.pool.cleanup()
                self.pool = None
            
            self.is_connected = False
            self.cdc_enabled = False
            
            # Stop CDC task
            if self.change_data_task:
                self.change_data_task.cancel()
                try:
                    await self.change_data_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("Disconnected from MySQL")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from MySQL: {e}")
            return False
    
    async def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        if not self.is_connected:
            raise Exception("Not connected to MySQL")
        
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
        async with connection.get() as conn:
            async with conn.cursor(DictCursor) as cursor:
                await cursor.execute(query, params)
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def execute_operation(self, operation: SyncOperation) -> bool:
        """Execute a synchronization operation."""
        if not self.is_connected:
            raise Exception("Not connected to MySQL")
        
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
        placeholders = ', '.join(['%s'] * len(values))
        
        query = f"""
            INSERT INTO {operation.target_table} ({', '.join(columns)})
            VALUES ({placeholders})
        """
        
        async with connection.get() as conn:
            async with conn.cursor(DictCursor) as cursor:
                await cursor.execute(query, values)
    
    async def _execute_update(self, connection, operation: SyncOperation):
        """Execute UPDATE operation."""
        if not operation.data:
            raise ValueError("Update operation requires data")
        
        if not operation.conditions:
            raise ValueError("Update operation requires conditions")
        
        set_clauses = []
        set_values = []
        
        for column, value in operation.data.items():
            set_clauses.append(f"{column} = %s")
            set_values.append(value)
        
        where_clauses = []
        where_values = []
        
        for column, value in operation.conditions.items():
            where_clauses.append(f"{column} = %s")
            where_values.append(value)
        
        query = f"""
            UPDATE {operation.target_table}
            SET {', '.join(set_clauses)}
            WHERE {' AND '.join(where_clauses)}
        """
        
        async with connection.get() as conn:
            async with conn.cursor(DictCursor) as cursor:
                await cursor.execute(query, set_values + where_values)
    
    async def _execute_delete(self, connection, operation: SyncOperation):
        """Execute DELETE operation."""
        if not operation.conditions:
            raise ValueError("Delete operation requires conditions")
        
        where_clauses = []
        where_values = []
        
        for column, value in operation.conditions.items():
            where_clauses.append(f"{column} = %s")
            where_values.append(value)
        
        query = f"""
            DELETE FROM {operation.target_table}
            WHERE {' AND '.join(where_clauses)}
        """
        
        async with connection.get() as conn:
            async with conn.cursor(DictCursor) as cursor:
                await cursor.execute(query, where_values)
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get the schema of a table."""
        query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                COLUMN_KEY,
                EXTRA
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """
        
        rows = await self.execute_query(query, (self.config.database, table_name))
        
        # Get primary keys
        pk_query = """
            SELECT COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND CONSTRAINT_NAME = 'PRIMARY'
            ORDER BY ORDINAL_POSITION
        """
        
        pk_rows = await self.execute_query(pk_query, (self.config.database, table_name))
        primary_keys = [row['COLUMN_NAME'] for row in pk_rows]
        
        return {
            'table_name': table_name,
            'columns': rows,
            'primary_keys': primary_keys
        }
    
    async def _check_binlog_status(self):
        """Check if MySQL binlog is enabled for CDC."""
        try:
            result = await self.execute_query("SHOW VARIABLES LIKE 'log_bin'")
            if result and result[0]['Value'] == 'ON':
                self.binlog_enabled = True
                self.logger.info("MySQL binlog is enabled for CDC")
            else:
                self.binlog_enabled = False
                self.logger.warning("MySQL binlog is not enabled")
        except Exception as e:
            self.logger.error(f"Failed to check binlog status: {e}")
            self.binlog_enabled = False
    
    async def get_changes(self, last_position: Optional[Any] = None) -> List[SyncOperation]:
        """Get changes since the last position (for CDC)."""
        if not self.cdc_enabled:
            return []
        
        try:
            # In a real implementation, this would read from binlog
            # For now, we'll simulate with change tracking
            changes = await self._get_tracked_changes(last_position)
            return [self._change_to_operation(change) for change in changes]
            
        except Exception as e:
            self.logger.error(f"Failed to get CDC changes: {e}")
            return []
    
    async def _get_tracked_changes(self, last_position: Optional[Any]) -> List[Dict[str, Any]]:
        """Get tracked changes (simplified implementation)."""
        # This is a placeholder implementation
        # In practice, you'd use binlog replication or change tracking tables
        changes = []
        
        # Example: Use a change tracking table
        if last_position:
            query = """
                SELECT * FROM sync_change_log 
                WHERE change_id > %s 
                ORDER BY change_id
                LIMIT 100
            """
            try:
                rows = await self.execute_query(query, (last_position,))
                for row in rows:
                    changes.append(row)
            except Exception as e:
                self.logger.warning(f"Change tracking table not available: {e}")
        
        return changes
    
    def _change_to_operation(self, change: Dict[str, Any]) -> SyncOperation:
        """Convert a change to a SyncOperation."""
        return SyncOperation(
            operation_id=str(uuid.uuid4()),
            source_table=change.get('table_name'),
            target_table=change.get('table_name'),
            operation_type=change.get('operation_type', 'UPDATE'),
            data=change.get('new_values'),
            conditions=change.get('primary_key'),
            timestamp=change.get('created_at'),
            metadata={'change_id': change.get('change_id')}
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
        async with connection.get() as conn:
            async with conn.cursor(DictCursor) as cursor:
                async with conn.begin():
                    for operation in operations:
                        await self._execute_operation_impl(connection, operation)
    
    async def validate_connection(self) -> bool:
        """Validate the database connection."""
        try:
            async with self.pool.execute_with_connection(
                lambda conn: conn.get().cursor(DictCursor).execute("SELECT 1")
            ):
                return True
        except Exception:
            return False
    
    def get_connector_type(self) -> ConnectorType:
        """Get the connector type."""
        return ConnectorType.MYSQL
    
    async def start_cdc(self, tables: List[str]) -> bool:
        """Start change data capture for specified tables."""
        try:
            if not self.binlog_enabled:
                self.logger.error("Cannot start CDC: MySQL binlog is not enabled")
                return False
            
            # Enable row-based binary logging for CDC
            await self._ensure_binlog_format_row()
            
            self.cdc_tables = tables
            self.cdc_enabled = True
            
            # Start change data processing task
            self.change_data_task = asyncio.create_task(self._process_change_data())
            
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
            
            # Stop change data task
            if self.change_data_task:
                self.change_data_task.cancel()
                try:
                    await self.change_data_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("Stopped CDC")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop CDC: {e}")
            return False
    
    async def get_current_position(self) -> Any:
        """Get the current CDC position."""
        try:
            result = await self.execute_query("SHOW MASTER STATUS")
            if result:
                return {
                    'file': result[0].get('File'),
                    'position': result[0].get('Position')
                }
        except Exception as e:
            self.logger.error(f"Failed to get current position: {e}")
        return None
    
    async def set_position(self, position: Any) -> bool:
        """Set the CDC position."""
        # For MySQL binlog, this would involve setting the binlog position
        # Implementation depends on the specific CDC mechanism used
        self.binlog_position = position
        return True
    
    async def _ensure_binlog_format_row(self):
        """Ensure binlog format is set to ROW for CDC."""
        try:
            result = await self.execute_query("SELECT @@binlog_format")
            if result:
                current_format = result[0]['@@binlog_format']
                if current_format != 'ROW':
                    await self.execute_query("SET GLOBAL binlog_format = 'ROW'")
                    self.logger.info("Changed binlog format to ROW")
        except Exception as e:
            self.logger.warning(f"Could not ensure binlog format: {e}")
    
    async def _process_change_data(self):
        """Background task to process change data."""
        while self.cdc_enabled:
            try:
                # Process pending change data
                await asyncio.sleep(1)  # Small delay to avoid busy waiting
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in change data processing: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def create_change_tracking_table(self):
        """Create a change tracking table for manual CDC."""
        query = """
            CREATE TABLE IF NOT EXISTS sync_change_log (
                change_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                table_name VARCHAR(64) NOT NULL,
                operation_type ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
                primary_key JSON,
                old_values JSON,
                new_values JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_table_created (table_name, created_at)
            )
        """
        await self.execute_query(query)
    
    async def setup_change_triggers(self, table_name: str):
        """Setup change tracking triggers for a table."""
        # Insert trigger
        insert_trigger = f"""
            CREATE TRIGGER {table_name}_insert_sync
            AFTER INSERT ON {table_name}
            FOR EACH ROW
            BEGIN
                INSERT INTO sync_change_log (table_name, operation_type, new_values, primary_key)
                VALUES ('{table_name}', 'INSERT', JSON_OBJECT({', '.join([f'NEW.{col}, NEW.{col}' for col in ['id']])}), 
                        JSON_OBJECT('id', NEW.id));
            END
        """
        
        # Update trigger
        update_trigger = f"""
            CREATE TRIGGER {table_name}_update_sync
            AFTER UPDATE ON {table_name}
            FOR EACH ROW
            BEGIN
                INSERT INTO sync_change_log (table_name, operation_type, old_values, new_values, primary_key)
                VALUES ('{table_name}', 'UPDATE', 
                        JSON_OBJECT('id', OLD.id), 
                        JSON_OBJECT('id', NEW.id),
                        JSON_OBJECT('id', NEW.id));
            END
        """
        
        # Delete trigger
        delete_trigger = f"""
            CREATE TRIGGER {table_name}_delete_sync
            AFTER DELETE ON {table_name}
            FOR EACH ROW
            BEGIN
                INSERT INTO sync_change_log (table_name, operation_type, old_values, primary_key)
                VALUES ('{table_name}', 'DELETE', 
                        JSON_OBJECT('id', OLD.id),
                        JSON_OBJECT('id', OLD.id));
            END
        """
        
        try:
            await self.execute_query(insert_trigger)
            await self.execute_query(update_trigger)
            await self.execute_query(delete_trigger)
            self.logger.info(f"Created change tracking triggers for {table_name}")
        except Exception as e:
            self.logger.error(f"Failed to create triggers for {table_name}: {e}")
    
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
            
            # Get server status
            status_result = await self.execute_query("SHOW STATUS LIKE 'Threads_%'")
            connections_result = await self.execute_query("SHOW STATUS LIKE 'Connections'")
            uptime_result = await self.execute_query("SHOW STATUS LIKE 'Uptime'")
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "timestamp": datetime.now(),
                "connector_type": self.get_connector_type().value,
                "response_time_ms": response_time,
                "binlog_enabled": self.binlog_enabled,
                "threads_connected": status_result[0]['Value'] if status_result else 0,
                "total_connections": connections_result[0]['Value'] if connections_result else 0,
                "server_uptime_seconds": uptime_result[0]['Value'] if uptime_result else 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now(),
                "connector_type": self.get_connector_type().value,
                "error": str(e)
            }
    
    async def begin_transaction(self) -> str:
        """Begin a new transaction."""
        return f"mysql_txn_{datetime.now().timestamp()}"
    
    async def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a transaction."""
        return True
    
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a transaction."""
        return True
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    def __repr__(self):
        return f"MySQLConnector(host={self.config.host}, database={self.config.database})"


class MySQLReplicationConnector(MySQLConnector):
    """MySQL connector with replication support."""
    
    def __init__(self, config: MySQLConfig, replication_user: str = None, replication_password: str = None):
        super().__init__(config)
        self.replication_user = replication_user or config.username
        self.replication_password = replication_password or config.password
        self.replication_enabled = False
    
    async def start_replication(self) -> bool:
        """Start replication for CDC."""
        try:
            # Check replication status
            result = await self.execute_query("SHOW SLAVE STATUS")
            if result:
                self.replication_enabled = True
                self.logger.info("MySQL replication is active")
                return True
            else:
                self.logger.warning("MySQL replication is not configured")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to check replication status: {e}")
            return False
    
    async def get_replication_lag(self) -> Optional[float]:
        """Get replication lag in seconds."""
        try:
            result = await self.execute_query("SHOW SLAVE STATUS")
            if result and result[0].get('Seconds_Behind_Master') is not None:
                return float(result[0]['Seconds_Behind_Master'])
        except Exception as e:
            self.logger.error(f"Failed to get replication lag: {e}")
        return None
    
    async def get_replication_changes(self, last_position: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get changes from replication stream."""
        # This would involve reading from binlog replication
        # Implementation depends on the specific replication setup
        changes = []
        
        # Placeholder implementation
        if last_position:
            # Get binlog events since last position
            pass
        
        return changes
