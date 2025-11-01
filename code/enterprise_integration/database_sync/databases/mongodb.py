"""
MongoDB Database Connector

Provides MongoDB-specific implementation for database synchronization.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import json
import uuid
from bson import ObjectId
from bson.json_util import dumps, loads

import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import ReturnDocument

from ..core.base_connector import BaseCDCConnector, DatabaseConfig, SyncOperation, ConnectorType
from ..core.change_event import ChangeEvent, ChangeType
from ..core.connection_pool import AsyncConnectionPool, PooledConnection


class MongoDBConfig(DatabaseConfig):
    """MongoDB-specific configuration."""
    
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
                 # MongoDB-specific options
                 auth_source: str = "admin",
                 retry_writes: bool = True,
                 retry_reads: bool = True,
                 read_preference: str = "primary",
                 write_concern: str = "majority",
                 read_concern: str = "local",
                 max_pool_size: Optional[int] = None,
                 min_pool_size: int = 5):
        
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
        
        self.auth_source = auth_source
        self.retry_writes = retry_writes
        self.retry_reads = retry_reads
        self.read_preference = read_preference
        self.write_concern = write_concern
        self.read_concern = read_concern
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
    
    def get_connection_string(self) -> str:
        """Get MongoDB connection string."""
        if self.connection_string:
            return self.connection_string
        
        auth_part = f"{self.username}:{self.password}@" if self.username else ""
        ssl_part = f"?ssl=true" if self.ssl_mode else ""
        
        return (f"mongodb://{auth_part}{self.host}:{self.port}/{self.database}"
                f"{ssl_part}")


class MongoDBPool(AsyncConnectionPool):
    """MongoDB connection pool."""
    
    def __init__(self, config: MongoDBConfig, **kwargs):
        self.config = config
        super().__init__(
            pool_name=f"mongodb_{config.database}_{config.host}",
            max_connections=config.max_connections,
            **kwargs
        )
    
    async def _create_connection(self) -> Optional[PooledConnection]:
        """Create a new MongoDB connection."""
        try:
            # Create Motor client
            client = AsyncIOMotorClient(
                self.config.get_connection_string(),
                maxPoolSize=self.config.max_pool_size,
                minPoolSize=self.config.min_pool_size,
                retryWrites=self.config.retry_writes,
                retryReads=self.config.retry_reads,
                connectTimeoutMS=self.config.timeout * 1000,
                serverSelectionTimeoutMS=self.config.timeout * 1000
            )
            
            # Test connection
            await client.admin.command('ping')
            
            pooled_conn = PooledConnection(
                connection_id=str(uuid.uuid4()),
                connection=client
            )
            
            self.logger.debug(f"Created MongoDB connection {pooled_conn.connection_id}")
            return pooled_conn
            
        except Exception as e:
            self.logger.error(f"Failed to create MongoDB connection: {e}")
            return None
    
    async def _close_connection(self, pooled_conn: PooledConnection) -> None:
        """Close a MongoDB connection."""
        try:
            if pooled_conn.connection:
                pooled_conn.connection.close()
            self.logger.debug(f"Closed MongoDB connection {pooled_conn.connection_id}")
        except Exception as e:
            self.logger.error(f"Error closing MongoDB connection: {e}")
    
    async def _validate_connection(self, pooled_conn: PooledConnection) -> bool:
        """Validate a MongoDB connection."""
        try:
            if pooled_conn.connection:
                await pooled_conn.connection.admin.command('ping')
                return True
        except Exception:
            pass
        return False


class MongoDBConnector(BaseCDCConnector):
    """MongoDB database connector with CDC support."""
    
    def __init__(self, config: MongoDBConfig):
        super().__init__(config)
        self.config = config
        self.pool = None
        self.client = None
        self.db = None
        self.is_connected = False
        
        self.logger = logging.getLogger(__name__)
        
        # CDC settings
        self.cdc_enabled = False
        self.change_streams = {}
        self.change_streams_task = None
    
    async def connect(self) -> bool:
        """Establish connection to MongoDB."""
        try:
            self.pool = MongoDBPool(self.config)
            initialized = await self.pool.initialize()
            
            if initialized:
                self.is_connected = True
                self.client = self.pool._available_connections[list(self.pool._available_connections.keys())[0]].connection
                self.db = self.client[self.config.database]
                self.logger.info(f"Connected to MongoDB: {self.config.host}:{self.config.port}/{self.config.database}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Close connection to MongoDB."""
        try:
            if self.pool:
                await self.pool.cleanup()
                self.pool = None
            
            self.client = None
            self.db = None
            self.is_connected = False
            self.cdc_enabled = False
            
            # Stop change streams
            if self.change_streams_task:
                self.change_streams_task.cancel()
                try:
                    await self.change_streams_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("Disconnected from MongoDB")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from MongoDB: {e}")
            return False
    
    async def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute a MongoDB query (aggregated to Python dict)."""
        if not self.is_connected:
            raise Exception("Not connected to MongoDB")
        
        try:
            # For MongoDB, queries are typically Python dicts, not strings
            # This method would be used for raw commands or complex operations
            result = await self.db.command(eval(query))  # Use eval with caution
            return [result] if isinstance(result, dict) else [result]
            
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise
    
    async def execute_operation(self, operation: SyncOperation) -> bool:
        """Execute a synchronization operation."""
        if not self.is_connected:
            raise Exception("Not connected to MongoDB")
        
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
        
        collection = self.db[operation.target_table]
        result = await collection.insert_one(operation.data)
        return result
    
    async def _execute_update(self, connection, operation: SyncOperation):
        """Execute UPDATE operation."""
        if not operation.data:
            raise ValueError("Update operation requires data")
        
        if not operation.conditions:
            raise ValueError("Update operation requires conditions")
        
        collection = self.db[operation.target_table]
        result = await collection.update_many(
            operation.conditions,
            {"$set": operation.data}
        )
        return result
    
    async def _execute_delete(self, connection, operation: SyncOperation):
        """Execute DELETE operation."""
        if not operation.conditions:
            raise ValueError("Delete operation requires conditions")
        
        collection = self.db[operation.target_table]
        result = await collection.delete_many(operation.conditions)
        return result
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get the schema of a collection."""
        try:
            # Get sample documents to infer schema
            collection = self.db[table_name]
            sample_docs = await collection.find().limit(100).to_list(length=100)
            
            if not sample_docs:
                return {
                    'collection_name': table_name,
                    'columns': [],
                    'indexes': [],
                    'sample_count': 0
                }
            
            # Extract schema from sample documents
            schema_info = {
                'collection_name': table_name,
                'sample_count': len(sample_docs),
                'indexes': [],
                'field_types': {}
            }
            
            # Analyze fields from sample documents
            for doc in sample_docs:
                for field_name, value in doc.items():
                    if field_name != '_id':
                        field_type = type(value).__name__
                        if field_name not in schema_info['field_types']:
                            schema_info['field_types'][field_name] = set()
                        schema_info['field_types'][field_name].add(field_type)
            
            # Convert sets to lists for JSON serialization
            for field_name in schema_info['field_types']:
                schema_info['field_types'][field_name] = list(schema_info['field_types'][field_name])
            
            # Get indexes
            indexes = await collection.list_indexes().to_list(length=None)
            schema_info['indexes'] = [
                {
                    'name': idx['name'],
                    'keys': list(idx.get('key', {}).items())
                }
                for idx in indexes
            ]
            
            return schema_info
            
        except Exception as e:
            self.logger.error(f"Failed to get schema for {table_name}: {e}")
            return {'collection_name': table_name, 'error': str(e)}
    
    async def get_changes(self, last_position: Optional[Any] = None) -> List[SyncOperation]:
        """Get changes since the last position (for CDC)."""
        if not self.cdc_enabled:
            return []
        
        try:
            changes = await self._get_change_stream_changes(last_position)
            return [self._change_to_operation(change) for change in changes]
            
        except Exception as e:
            self.logger.error(f"Failed to get CDC changes: {e}")
            return []
    
    async def _get_change_stream_changes(self, last_position: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get changes from MongoDB change streams."""
        changes = []
        
        for collection_name, change_stream in self.change_streams.items():
            try:
                async for change in change_stream:
                    if last_position:
                        # Filter changes based on position
                        if change.get('_id') <= ObjectId(last_position.get('change_id')):
                            continue
                    
                    changes.append(change)
                    
            except Exception as e:
                self.logger.error(f"Error reading change stream for {collection_name}: {e}")
        
        return changes
    
    def _change_to_operation(self, change: Dict[str, Any]) -> SyncOperation:
        """Convert a MongoDB change stream event to SyncOperation."""
        operation_type_map = {
            'insert': 'INSERT',
            'update': 'UPDATE',
            'delete': 'DELETE',
            'replace': 'UPDATE'
        }
        
        operation_type = operation_type_map.get(change.get('operationType'), 'UPDATE')
        
        # Extract document from change event
        if operation_type == 'DELETE':
            # For deletes, we have the document key in 'documentKey'
            document_id = change.get('documentKey', {}).get('_id')
            conditions = {'_id': document_id} if document_id else {}
            data = None
            old_values = change.get('fullDocument', {})
        else:
            # For inserts/updates, we have the full document
            document = change.get('fullDocument', {})
            document_id = document.get('_id')
            conditions = {'_id': document_id} if document_id else {}
            data = document
            old_values = change.get('updateDescription', {}).get('removedFields', {})
        
        return SyncOperation(
            operation_id=str(uuid.uuid4()),
            source_table=change.get('ns', {}).get('coll', 'unknown'),
            target_table=change.get('ns', {}).get('coll', 'unknown'),
            operation_type=operation_type,
            data=data,
            conditions=conditions,
            timestamp=datetime.now(),
            metadata={
                'change_id': str(change.get('_id')),
                'operation_type': change.get('operationType'),
                'cluster_time': change.get('clusterTime')
            }
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
        # MongoDB doesn't have traditional transactions across collections
        # but we can use session-based transactions for operations on a single collection
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                for operation in operations:
                    await self._execute_operation_impl(connection, operation)
    
    async def validate_connection(self) -> bool:
        """Validate the database connection."""
        try:
            async with self.pool.execute_with_connection(
                lambda conn: conn.admin.command('ping')
            ):
                return True
        except Exception:
            return False
    
    def get_connector_type(self) -> ConnectorType:
        """Get the connector type."""
        return ConnectorType.MONGODB
    
    async def start_cdc(self, tables: List[str]) -> bool:
        """Start change data capture for specified collections."""
        try:
            self.change_streams = {}
            
            for collection_name in tables:
                collection = self.db[collection_name]
                change_stream = collection.watch([
                    {"$match": {"operationType": {"$in": ["insert", "update", "delete", "replace"]}}}
                ])
                
                self.change_streams[collection_name] = change_stream
            
            self.cdc_enabled = True
            self.cdc_tables = tables
            
            # Start background task to process changes
            self.change_streams_task = asyncio.create_task(self._process_change_streams())
            
            self.logger.info(f"Started CDC for collections: {tables}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start CDC: {e}")
            return False
    
    async def stop_cdc(self) -> bool:
        """Stop change data capture."""
        try:
            self.cdc_enabled = False
            
            # Close all change streams
            for change_stream in self.change_streams.values():
                change_stream.close()
            
            self.change_streams.clear()
            
            # Cancel background task
            if self.change_streams_task:
                self.change_streams_task.cancel()
                try:
                    await self.change_streams_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("Stopped CDC")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop CDC: {e}")
            return False
    
    async def get_current_position(self) -> Any:
        """Get the current CDC position."""
        # Return the latest change stream position
        # This is simplified - in practice, you'd track the change stream resume tokens
        return {'change_id': str(ObjectId()), 'timestamp': datetime.now()}
    
    async def set_position(self, position: Any) -> bool:
        """Set the CDC position."""
        # For MongoDB change streams, this would involve resume tokens
        # Implementation depends on the specific change stream mechanism
        return True
    
    async def _process_change_streams(self):
        """Background task to process change stream events."""
        while self.cdc_enabled:
            try:
                # Process pending change stream events
                await asyncio.sleep(1)  # Small delay to avoid busy waiting
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in change stream processing: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def find_documents(self, 
                           collection_name: str,
                           filter_dict: Optional[Dict[str, Any]] = None,
                           projection: Optional[Dict[str, Any]] = None,
                           limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find documents in a collection."""
        if not self.is_connected:
            raise Exception("Not connected to MongoDB")
        
        try:
            collection = self.db[collection_name]
            cursor = collection.find(filter_dict or {}, projection)
            
            if limit:
                cursor = cursor.limit(limit)
            
            documents = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string for JSON serialization
            for doc in documents:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Failed to find documents: {e}")
            raise
    
    async def aggregate_documents(self, 
                                collection_name: str,
                                pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run aggregation pipeline on a collection."""
        if not self.is_connected:
            raise Exception("Not connected to MongoDB")
        
        try:
            collection = self.db[collection_name]
            cursor = collection.aggregate(pipeline)
            documents = await cursor.to_list(length=None)
            
            # Convert ObjectId to string for JSON serialization
            for doc in documents:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Failed to aggregate documents: {e}")
            raise
    
    async def create_index(self, 
                          collection_name: str,
                          index_spec: Dict[str, int],
                          options: Optional[Dict[str, Any]] = None) -> str:
        """Create an index on a collection."""
        if not self.is_connected:
            raise Exception("Not connected to MongoDB")
        
        try:
            collection = self.db[collection_name]
            result = await collection.create_index(
                list(index_spec.items()),
                **(options or {})
            )
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to create index: {e}")
            raise
    
    async def bulk_write_operations(self, 
                                  collection_name: str,
                                  operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute bulk write operations on a collection."""
        if not self.is_connected:
            raise Exception("Not connected to MongoDB")
        
        try:
            collection = self.db[collection_name]
            
            # Convert operations to Motor bulk operations
            bulk_ops = []
            for op in operations:
                op_type = op.get('type')
                if op_type == 'insert':
                    bulk_ops.append(collection.insert_one(op.get('document')))
                elif op_type == 'update':
                    bulk_ops.append(collection.update_many(
                        op.get('filter', {}),
                        op.get('update', {})
                    ))
                elif op_type == 'delete':
                    bulk_ops.append(collection.delete_many(op.get('filter', {})))
            
            results = await asyncio.gather(*bulk_ops, return_exceptions=True)
            
            # Process results
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            error_count = len(results) - success_count
            
            return {
                'success_count': success_count,
                'error_count': error_count,
                'errors': [str(r) for r in results if isinstance(r, Exception)]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to execute bulk operations: {e}")
            raise
    
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
            server_status = await self.client.admin.command('serverStatus')
            
            # Get database stats
            db_stats = await self.db.command('dbStats')
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "timestamp": datetime.now(),
                "connector_type": self.get_connector_type().value,
                "response_time_ms": response_time,
                "server_version": server_status.get('version', 'Unknown'),
                "max_bson_size": server_status.get('maxBsonObjectSize', 0),
                "connections_current": server_status.get('connections', {}).get('current', 0),
                "connections_available": server_status.get('connections', {}).get('available', 0),
                "database_size_mb": db_stats.get('dataSize', 0) / (1024 * 1024),
                "database_collections": db_stats.get('collections', 0),
                "database_objects": db_stats.get('objects', 0)
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
        # MongoDB transaction management would be handled at the session level
        return f"mongo_txn_{datetime.now().timestamp()}"
    
    async def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a transaction."""
        # MongoDB transactions are managed by sessions
        return True
    
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a transaction."""
        # MongoDB transactions are managed by sessions
        return True
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    def __repr__(self):
        return f"MongoDBConnector(host={self.config.host}, database={self.config.database})"


class MongoDBReplicaSetConnector(MongoDBConnector):
    """MongoDB connector for replica sets."""
    
    def __init__(self, config: MongoDBConfig, read_preference='secondaryPreferred'):
        super().__init__(config)
        self.read_preference = read_preference
    
    async def connect(self) -> bool:
        """Establish connection to MongoDB replica set."""
        try:
            self.pool = MongoDBPool(self.config)
            initialized = await self.pool.initialize()
            
            if initialized:
                self.is_connected = True
                # Get first available connection
                self.client = self.pool._available_connections[list(self.pool._available_connections.keys())[0]].connection
                self.db = self.client[self.config.database].with_options(
                    read_preference=getattr(__import__('pymongo'), self.read_preference)
                )
                self.logger.info(f"Connected to MongoDB replica set: {self.config.host}:{self.config.port}/{self.config.database}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB replica set: {e}")
            return False
