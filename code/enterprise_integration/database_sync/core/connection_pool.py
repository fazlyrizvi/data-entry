"""
Connection Pool Management

Provides efficient connection pooling for database operations.
"""

import asyncio
import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import weakref
import json


class PoolStatus(Enum):
    """Connection pool status."""
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    EXHAUSTED = "EXHAUSTED"
    ERROR = "ERROR"


@dataclass
class PooledConnection:
    """Represents a pooled database connection."""
    connection_id: str
    connection: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    is_borrowed: bool = False
    
    def refresh_usage(self):
        """Refresh connection usage information."""
        self.last_used = datetime.now()
        self.usage_count += 1
    
    def is_expired(self, max_idle_time: timedelta) -> bool:
        """Check if connection is expired."""
        return datetime.now() - self.last_used > max_idle_time
    
    def get_age(self) -> timedelta:
        """Get the age of the connection."""
        return datetime.now() - self.created_at


class ConnectionPool:
    """Generic connection pool for database connections."""
    
    def __init__(self, 
                 pool_name: str,
                 max_connections: int = 10,
                 min_connections: int = 2,
                 max_idle_time: timedelta = timedelta(minutes=30),
                 connection_timeout: int = 30,
                 health_check_interval: int = 300):
        
        self.pool_name = pool_name
        self.max_connections = max_connections
        self.min_connections = min_connections
        self.max_idle_time = max_idle_time
        self.connection_timeout = connection_timeout
        self.health_check_interval = health_check_interval
        
        self._available_connections: Dict[str, PooledConnection] = {}
        self._borrowed_connections: Dict[str, PooledConnection] = {}
        self._connection_counter = 0
        self._pool_lock = asyncio.Lock()
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics = {
            'total_connections_created': 0,
            'total_connections_reused': 0,
            'total_connections_closed': 0,
            'max_concurrent_borrowed': 0,
            'current_borrowed': 0,
            'current_available': 0,
            'average_connection_age': 0.0,
            'health_check_failures': 0,
            'last_health_check': None
        }
        
        self.logger = logging.getLogger(f"{__name__}.{pool_name}")
    
    async def initialize(self) -> bool:
        """Initialize the connection pool."""
        try:
            # Create minimum number of connections
            for _ in range(self.min_connections):
                await self._create_connection()
            
            # Start health check task
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            self.logger.info(f"Connection pool '{self.pool_name}' initialized with {self.min_connections} connections")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize connection pool: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Clean up the connection pool."""
        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        async with self._pool_lock:
            all_connections = {**self._available_connections, **self._borrowed_connections}
            for connection in all_connections.values():
                await self._close_connection(connection)
            
            self._available_connections.clear()
            self._borrowed_connections.clear()
        
        self.logger.info(f"Connection pool '{self.pool_name}' cleaned up")
    
    async def borrow_connection(self) -> Optional[Any]:
        """Borrow a connection from the pool."""
        async with self._pool_lock:
            # Try to get an available connection
            if self._available_connections:
                connection = next(iter(self._available_connections.values()))
                del self._available_connections[connection.connection_id]
                connection.is_borrowed = True
                self._borrowed_connections[connection.connection_id] = connection
                connection.refresh_usage()
                
                # Update metrics
                self._metrics['total_connections_reused'] += 1
                self._metrics['current_available'] = len(self._available_connections)
                self._metrics['current_borrowed'] = len(self._borrowed_connections)
                self._metrics['max_concurrent_borrowed'] = max(
                    self._metrics['max_concurrent_borrowed'],
                    self._metrics['current_borrowed']
                )
                
                self.logger.debug(f"Borrowed connection {connection.connection_id}")
                return connection.connection
            
            # Create a new connection if under limit
            total_connections = len(self._available_connections) + len(self._borrowed_connections)
            if total_connections < self.max_connections:
                return await self._create_and_borrow_connection()
            
            # Pool exhausted - implement timeout
            try:
                await asyncio.wait_for(self._wait_for_connection(), timeout=self.connection_timeout)
                return await self.borrow_connection()
            except asyncio.TimeoutError:
                self.logger.warning(f"Connection pool '{self.pool_name}' exhausted")
                self._metrics['status'] = PoolStatus.EXHAUSTED
                return None
    
    async def return_connection(self, connection: Any) -> None:
        """Return a connection to the pool."""
        if connection is None:
            return
        
        async with self._pool_lock:
            # Find the connection in borrowed connections
            connection_id = None
            for conn_id, pooled_conn in self._borrowed_connections.items():
                if pooled_conn.connection == connection:
                    connection_id = conn_id
                    break
            
            if connection_id:
                # Return to available pool
                pooled_conn = self._borrowed_connections.pop(connection_id)
                pooled_conn.is_borrowed = False
                self._available_connections[connection_id] = pooled_conn
                
                # Update metrics
                self._metrics['current_available'] = len(self._available_connections)
                self._metrics['current_borrowed'] = len(self._borrowed_connections)
                
                self.logger.debug(f"Returned connection {connection_id}")
    
    async def execute_with_connection(self, operation, *args, **kwargs):
        """Execute an operation with automatic connection management."""
        connection = await self.borrow_connection()
        if connection is None:
            raise Exception("No connection available from pool")
        
        try:
            return await operation(connection, *args, **kwargs)
        finally:
            await self.return_connection(connection)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        async with self._pool_lock:
            return {
                'pool_name': self.pool_name,
                'status': self._get_pool_status().value,
                'total_connections': len(self._available_connections) + len(self._borrowed_connections),
                'available_connections': len(self._available_connections),
                'borrowed_connections': len(self._borrowed_connections),
                'max_connections': self.max_connections,
                'min_connections': self.min_connections,
                'metrics': self._metrics.copy()
            }
    
    async def _create_connection(self) -> Optional[PooledConnection]:
        """Create a new connection (must be implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement _create_connection")
    
    async def _close_connection(self, pooled_conn: PooledConnection) -> None:
        """Close a connection (must be implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement _close_connection")
    
    async def _validate_connection(self, pooled_conn: PooledConnection) -> bool:
        """Validate a connection is still healthy."""
        raise NotImplementedError("Subclasses must implement _validate_connection")
    
    async def _create_and_borrow_connection(self) -> Optional[Any]:
        """Create a new connection and immediately borrow it."""
        pooled_conn = await self._create_connection()
        if pooled_conn:
            pooled_conn.is_borrowed = True
            self._borrowed_connections[pooled_conn.connection_id] = pooled_conn
            
            self._metrics['total_connections_created'] += 1
            self._metrics['current_borrowed'] = len(self._borrowed_connections)
            self._metrics['max_concurrent_borrowed'] = max(
                self._metrics['max_concurrent_borrowed'],
                self._metrics['current_borrowed']
            )
            
            self.logger.debug(f"Created and borrowed connection {pooled_conn.connection_id}")
            return pooled_conn.connection
        return None
    
    async def _wait_for_connection(self) -> None:
        """Wait for a connection to become available."""
        # Simple implementation - could be improved with proper signaling
        await asyncio.sleep(0.1)
    
    async def _health_check_loop(self) -> None:
        """Background task for health checking connections."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
    
    async def _perform_health_check(self) -> None:
        """Perform health check on all connections."""
        expired_connections = []
        unhealthy_connections = []
        
        async with self._pool_lock:
            # Check available connections
            for connection_id, pooled_conn in list(self._available_connections.items()):
                try:
                    if pooled_conn.is_expired(self.max_idle_time):
                        expired_connections.append((connection_id, pooled_conn))
                    elif not await self._validate_connection(pooled_conn):
                        unhealthy_connections.append((connection_id, pooled_conn))
                except Exception as e:
                    self.logger.warning(f"Health check failed for connection {connection_id}: {e}")
                    unhealthy_connections.append((connection_id, pooled_conn))
        
        # Close expired/unhealthy connections
        for connection_id, pooled_conn in expired_connections + unhealthy_connections:
            async with self._pool_lock:
                if connection_id in self._available_connections:
                    del self._available_connections[connection_id]
            
            await self._close_connection(pooled_conn)
            self._metrics['total_connections_closed'] += 1
            
            if connection_id in unhealthy_connections:
                self._metrics['health_check_failures'] += 1
        
        # Maintain minimum connections
        async with self._pool_lock:
            total_connections = len(self._available_connections) + len(self._borrowed_connections)
            if total_connections < self.min_connections:
                for _ in range(self.min_connections - total_connections):
                    await self._create_connection()
        
        self._metrics['current_available'] = len(self._available_connections)
        self._metrics['current_borrowed'] = len(self._borrowed_connections)
        self._metrics['last_health_check'] = datetime.now().isoformat()
    
    def _get_pool_status(self) -> PoolStatus:
        """Get the current pool status."""
        total_connections = len(self._available_connections) + len(self._borrowed_connections)
        
        if total_connections == 0:
            return PoolStatus.IDLE
        elif len(self._borrowed_connections) >= self.max_connections:
            return PoolStatus.EXHAUSTED
        elif len(self._borrowed_connections) > 0:
            return PoolStatus.ACTIVE
        else:
            return PoolStatus.IDLE
    
    def __str__(self):
        return f"ConnectionPool({self.pool_name}, available={len(self._available_connections)}, borrowed={len(self._borrowed_connections)})"


class AsyncConnectionPool(ConnectionPool):
    """Asynchronous version of connection pool."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._waiting_tasks: List[asyncio.Future] = []
    
    async def borrow_connection_with_retry(self, max_retries: int = 3, retry_delay: float = 1.0) -> Optional[Any]:
        """Borrow connection with retry logic."""
        for attempt in range(max_retries):
            connection = await self.borrow_connection()
            if connection:
                return connection
            
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
        
        return None
    
    async def execute_batch(self, operations: List[tuple]) -> List[Any]:
        """Execute a batch of operations using separate connections."""
        if not operations:
            return []
        
        # Use as many connections as needed (or available)
        connections = []
        try:
            for _ in range(min(len(operations), self.max_connections)):
                conn = await self.borrow_connection()
                if not conn:
                    break
                connections.append(conn)
            
            if not connections:
                raise Exception("No connections available")
            
            # Distribute operations across connections
            results = []
            for i, (operation, *args) in enumerate(operations):
                conn = connections[i % len(connections)]
                try:
                    result = await operation(conn, *args)
                    results.append(result)
                except Exception as e:
                    results.append(e)
            
            return results
            
        finally:
            for conn in connections:
                await self.return_connection(conn)


class SyncConnectionPool(ConnectionPool):
    """Synchronous version of connection pool."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def execute_sync(self, operation, *args, **kwargs):
        """Execute a synchronous operation."""
        return await self.execute_with_connection(operation, *args, **kwargs)
