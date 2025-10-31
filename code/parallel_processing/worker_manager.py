#!/usr/bin/env python3
"""
Worker Manager - Worker Pool Management
======================================

Manages worker pools, load balancing, worker lifecycle, and resource allocation.
Provides automatic scaling and failover mechanisms.
"""

import asyncio
import logging
import psutil
import resource
import time
from typing import Dict, List, Optional, Set, Any
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import weakref

from config import ProcessingConfig

logger = logging.getLogger(__name__)


@dataclass
class WorkerInfo:
    """Information about a worker process."""
    worker_id: str
    process_id: int
    worker_type: str
    status: str
    current_task: Optional[str]
    start_time: datetime
    last_heartbeat: datetime
    tasks_completed: int
    errors_count: int
    memory_usage: float
    cpu_usage: float
    load_average: float


@dataclass
class WorkerPool:
    """Worker pool configuration and state."""
    pool_id: str
    worker_type: str
    min_workers: int
    max_workers: int
    current_workers: int
    workers: Dict[str, WorkerInfo]
    task_queue: asyncio.Queue
    is_active: bool
    created_at: datetime


class WorkerManager:
    """Manages worker pools and load balancing."""
    
    def __init__(self, queue_handler, config: ProcessingConfig):
        """Initialize the worker manager."""
        self.queue_handler = queue_handler
        self.config = config
        self.pools: Dict[str, WorkerPool] = {}
        self.worker_executors: Dict[str, ProcessPoolExecutor] = {}
        self.system_monitor = SystemMonitor()
        self.autoscaling_enabled = True
        self.is_running = False
        self._shutdown_event = asyncio.Event()
        self._lock = asyncio.Lock()
        
        # Worker type configurations
        self.worker_types = {
            'ocr': {'pool_size': 4, 'memory_limit': 1024, 'cpu_limit': 0.8},
            'nlp': {'pool_size': 2, 'memory_limit': 2048, 'cpu_limit': 0.6},
            'validation': {'pool_size': 3, 'memory_limit': 512, 'cpu_limit': 0.4},
            'preprocessing': {'pool_size': 6, 'memory_limit': 768, 'cpu_limit': 0.5}
        }
        
        logger.info("Worker Manager initialized")
    
    async def start(self) -> None:
        """Start the worker manager."""
        if self.is_running:
            logger.warning("Worker Manager is already running")
            return
        
        self.is_running = True
        
        # Start system monitoring
        await self.system_monitor.start()
        
        # Initialize worker pools
        await self._initialize_pools()
        
        # Start autoscaling and monitoring tasks
        asyncio.create_task(self._autoscaling_monitor())
        asyncio.create_task(self._health_monitor())
        
        logger.info("Worker Manager started successfully")
    
    async def _initialize_pools(self) -> None:
        """Initialize worker pools based on configuration."""
        for worker_type, config in self.worker_types.items():
            pool_id = f"{worker_type}_pool"
            min_workers = max(1, min(config['pool_size'], self.config.max_workers // 4))
            max_workers = min(config['pool_size'], self.config.max_workers)
            
            pool = WorkerPool(
                pool_id=pool_id,
                worker_type=worker_type,
                min_workers=min_workers,
                max_workers=max_workers,
                current_workers=0,
                workers={},
                task_queue=asyncio.Queue(),
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            self.pools[pool_id] = pool
            
            # Start initial workers
            await self._scale_pool(pool_id, min_workers)
            
            logger.info(f"Initialized {worker_type} pool with {min_workers} workers")
    
    async def _scale_pool(self, pool_id: str, target_count: int) -> None:
        """Scale a worker pool to target worker count."""
        pool = self.pools.get(pool_id)
        if not pool:
            raise ValueError(f"Pool {pool_id} not found")
        
        pool_id_lock = f"pool_{pool_id}"
        async with self._lock:
            current_count = pool.current_workers
            
            if target_count > current_count:
                # Scale up - add workers
                workers_to_add = min(target_count - current_count, 
                                   pool.max_workers - current_count)
                
                for _ in range(workers_to_add):
                    worker_info = await self._create_worker(pool)
                    if worker_info:
                        pool.workers[worker_info.worker_id] = worker_info
                        pool.current_workers += 1
                        logger.info(f"Added worker {worker_info.worker_id} to {pool_id}")
            
            elif target_count < current_count:
                # Scale down - remove workers
                workers_to_remove = current_count - target_count
                workers_to_stop = list(pool.workers.values())[:workers_to_remove]
                
                for worker_info in workers_to_stop:
                    await self._stop_worker(pool, worker_info.worker_id)
                    del pool.workers[worker_info.worker_id]
                    pool.current_workers -= 1
                    logger.info(f"Removed worker {worker_info.worker_id} from {pool_id}")
    
    async def _create_worker(self, pool: WorkerPool) -> Optional[WorkerInfo]:
        """Create a new worker process."""
        try:
            worker_id = f"{pool.worker_type}_{int(time.time() * 1000)}"
            
            # Create worker executor
            executor = ProcessPoolExecutor(
                max_workers=1,
                mp_context=None
            )
            
            self.worker_executors[worker_id] = executor
            
            worker_info = WorkerInfo(
                worker_id=worker_id,
                process_id=0,  # Will be updated
                worker_type=pool.worker_type,
                status='starting',
                current_task=None,
                start_time=datetime.utcnow(),
                last_heartbeat=datetime.utcnow(),
                tasks_completed=0,
                errors_count=0,
                memory_usage=0.0,
                cpu_usage=0.0,
                load_average=0.0
            )
            
            # Start worker process
            await self._start_worker_process(worker_info, pool)
            
            return worker_info
            
        except Exception as e:
            logger.error(f"Failed to create worker: {e}")
            return None
    
    async def _start_worker_process(self, worker_info: WorkerInfo, pool: WorkerPool) -> None:
        """Start a worker process."""
        try:
            executor = self.worker_executors.get(worker_info.worker_id)
            if not executor:
                raise ValueError(f"Executor not found for worker {worker_info.worker_id}")
            
            # Submit initialization task to worker
            future = executor.submit(
                initialize_worker,
                worker_info.worker_id,
                pool.worker_type,
                self.config
            )
            
            # Wait for initialization
            result = future.result(timeout=30)
            
            if result['success']:
                worker_info.process_id = result['process_id']
                worker_info.status = 'running'
                logger.info(f"Worker {worker_info.worker_id} started successfully")
            else:
                raise Exception(f"Worker initialization failed: {result['error']}")
                
        except Exception as e:
            logger.error(f"Failed to start worker process {worker_info.worker_id}: {e}")
            worker_info.status = 'failed'
            await self._cleanup_worker(worker_info)
    
    async def _stop_worker(self, pool: WorkerPool, worker_id: str) -> None:
        """Stop a worker process."""
        worker_info = pool.workers.get(worker_id)
        if not worker_info:
            return
        
        try:
            worker_info.status = 'stopping'
            
            # Cancel current task if any
            if worker_info.current_task:
                await self.queue_handler.cancel_task(worker_info.current_task)
            
            # Cleanup worker
            await self._cleanup_worker(worker_info)
            
            worker_info.status = 'stopped'
            logger.info(f"Worker {worker_id} stopped successfully")
            
        except Exception as e:
            logger.error(f"Failed to stop worker {worker_id}: {e}")
    
    async def _cleanup_worker(self, worker_info: WorkerInfo) -> None:
        """Cleanup worker resources."""
        try:
            executor = self.worker_executors.pop(worker_info.worker_id, None)
            if executor:
                executor.shutdown(wait=False)
        except Exception as e:
            logger.error(f"Error cleaning up worker {worker_info.worker_id}: {e}")
    
    async def _autoscaling_monitor(self) -> None:
        """Monitor and adjust worker pool sizes based on load."""
        while self.is_running:
            try:
                if not self.autoscaling_enabled:
                    await asyncio.sleep(30)
                    continue
                
                for pool_id, pool in self.pools.items():
                    if not pool.is_active:
                        continue
                    
                    # Get queue metrics
                    queue_metrics = await self.queue_handler.get_queue_metrics(pool.worker_type)
                    
                    # Calculate optimal worker count
                    optimal_count = self._calculate_optimal_worker_count(pool, queue_metrics)
                    
                    # Adjust pool size if needed
                    if optimal_count != pool.current_workers:
                        logger.info(f"Scaling {pool_id} from {pool.current_workers} to {optimal_count} workers")
                        await self._scale_pool(pool_id, optimal_count)
                
                await asyncio.sleep(self.config.autoscaling_interval)
                
            except Exception as e:
                logger.error(f"Error in autoscaling monitor: {e}")
                await asyncio.sleep(10)
    
    def _calculate_optimal_worker_count(self, pool: WorkerPool, queue_metrics: Dict) -> int:
        """Calculate optimal worker count based on queue metrics."""
        if not queue_metrics:
            return pool.current_workers
        
        pending_tasks = queue_metrics.get('pending_tasks', 0)
        active_tasks = queue_metrics.get('active_tasks', 0)
        
        # Simple scaling logic
        if pending_tasks > pool.current_workers * 10:
            # High load - scale up
            return min(pool.current_workers + 1, pool.max_workers)
        elif pending_tasks < pool.current_workers * 2 and active_tasks < pool.current_workers:
            # Low load - scale down
            return max(pool.current_workers - 1, pool.min_workers)
        else:
            # Stable load - maintain current size
            return pool.current_workers
    
    async def _health_monitor(self) -> None:
        """Monitor worker health and perform recovery actions."""
        while self.is_running:
            try:
                await self._check_workers_health()
                await asyncio.sleep(self.config.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(10)
    
    async def _check_workers_health(self) -> None:
        """Check health of all workers and perform recovery."""
        for pool_id, pool in self.pools.items():
            if not pool.is_active:
                continue
            
            unhealthy_workers = []
            
            for worker_id, worker_info in pool.workers.items():
                # Check if worker is healthy
                if not await self._is_worker_healthy(worker_info):
                    unhealthy_workers.append(worker_id)
            
            # Replace unhealthy workers
            for worker_id in unhealthy_workers:
                logger.warning(f"Worker {worker_id} is unhealthy, replacing...")
                await self._stop_worker(pool, worker_id)
                
                # Remove from pool
                del pool.workers[worker_id]
                pool.current_workers -= 1
                
                # Add new worker
                new_worker = await self._create_worker(pool)
                if new_worker:
                    pool.workers[new_worker.worker_id] = new_worker
                    pool.current_workers += 1
    
    async def _is_worker_healthy(self, worker_info: WorkerInfo) -> bool:
        """Check if a worker is healthy."""
        try:
            # Check heartbeat
            time_since_heartbeat = (datetime.utcnow() - worker_info.last_heartbeat).total_seconds()
            if time_since_heartbeat > self.config.worker_timeout:
                return False
            
            # Check error rate
            if worker_info.tasks_completed > 0:
                error_rate = worker_info.errors_count / worker_info.tasks_completed
                if error_rate > self.config.max_error_rate:
                    return False
            
            # Check resource usage
            if worker_info.memory_usage > self.config.max_memory_per_worker:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking worker health: {e}")
            return False
    
    async def get_health_status(self) -> Dict:
        """Get worker manager health status."""
        total_workers = sum(pool.current_workers for pool in self.pools.values())
        total_unhealthy = 0
        
        for pool in self.pools.values():
            for worker_info in pool.workers.values():
                if not await self._is_worker_healthy(worker_info):
                    total_unhealthy += 1
        
        status = 'healthy' if total_unhealthy == 0 else 'degraded'
        
        return {
            'status': status,
            'total_workers': total_workers,
            'unhealthy_workers': total_unhealthy,
            'pools': {
                pool_id: {
                    'worker_type': pool.worker_type,
                    'current_workers': pool.current_workers,
                    'min_workers': pool.min_workers,
                    'max_workers': pool.max_workers,
                    'is_active': pool.is_active
                }
                for pool_id, pool in self.pools.items()
            },
            'system_resources': await self.system_monitor.get_system_metrics(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def get_metrics(self) -> Dict:
        """Get worker manager performance metrics."""
        total_tasks = 0
        total_errors = 0
        total_memory = 0
        total_cpu = 0
        
        for pool in self.pools.values():
            for worker_info in pool.workers.values():
                total_tasks += worker_info.tasks_completed
                total_errors += worker_info.errors_count
                total_memory += worker_info.memory_usage
                total_cpu += worker_info.cpu_usage
        
        return {
            'total_workers': sum(pool.current_workers for pool in self.pools.values()),
            'total_tasks_completed': total_tasks,
            'total_errors': total_errors,
            'average_memory_usage': total_memory / max(len(self.pools), 1),
            'average_cpu_usage': total_cpu / max(len(self.pools), 1),
            'pool_details': {
                pool_id: {
                    'worker_type': pool.worker_type,
                    'current_workers': pool.current_workers,
                    'tasks_completed': sum(w.tasks_completed for w in pool.workers.values()),
                    'errors_count': sum(w.errors_count for w in pool.workers.values())
                }
                for pool_id, pool in self.pools.items()
            }
        }
    
    async def recover_workers(self) -> None:
        """Attempt to recover failed workers."""
        logger.info("Attempting to recover workers...")
        
        for pool_id, pool in self.pools.items():
            if not pool.is_active:
                continue
            
            # Check if pool needs recovery
            if pool.current_workers < pool.min_workers:
                workers_needed = pool.min_workers - pool.current_workers
                logger.info(f"Recovering {workers_needed} workers in {pool_id}")
                
                for _ in range(workers_needed):
                    new_worker = await self._create_worker(pool)
                    if new_worker:
                        pool.workers[new_worker.worker_id] = new_worker
                        pool.current_workers += 1
    
    def shutdown(self) -> None:
        """Shutdown the worker manager."""
        logger.info("Shutting down Worker Manager...")
        
        self.is_running = False
        self._shutdown_event.set()
        
        # Stop all worker pools
        for pool_id, pool in self.pools.items():
            pool.is_active = False
        
        # Stop all workers
        for pool_id, pool in self.pools.items():
            for worker_id in list(pool.workers.keys()):
                # Create a new event loop for synchronous operations
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self._stop_worker(pool, worker_id))
                finally:
                    loop.close()
        
        # Cleanup executors
        for executor in self.worker_executors.values():
            executor.shutdown(wait=False)
        
        self.worker_executors.clear()
        self.pools.clear()
        
        # Stop system monitor
        self.system_monitor.stop()
        
        logger.info("Worker Manager shutdown completed")


class SystemMonitor:
    """Monitor system resources and performance."""
    
    def __init__(self):
        self.is_running = False
        self._monitor_task = None
        self.metrics_history = []
        self.max_history = 100
    
    async def start(self) -> None:
        """Start system monitoring."""
        self.is_running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("System Monitor started")
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_running:
            try:
                metrics = await self._collect_metrics()
                self._update_metrics_history(metrics)
                await asyncio.sleep(5)  # Monitor every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                await asyncio.sleep(10)
    
    async def _collect_metrics(self) -> Dict:
        """Collect current system metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory usage
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Load average (Unix-like systems)
        try:
            load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0.0
        except:
            load_avg = 0.0
        
        return {
            'cpu_percent': cpu_percent,
            'cpu_count': cpu_count,
            'memory_percent': memory.percent,
            'memory_used_gb': memory.used / (1024**3),
            'memory_total_gb': memory.total / (1024**3),
            'swap_percent': swap.percent,
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / (1024**3),
            'load_average': load_avg,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _update_metrics_history(self, metrics: Dict) -> None:
        """Update metrics history."""
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)
    
    async def get_system_metrics(self) -> Dict:
        """Get current system metrics."""
        if self.metrics_history:
            return self.metrics_history[-1]
        else:
            return await self._collect_metrics()
    
    def stop(self) -> None:
        """Stop system monitoring."""
        self.is_running = False
        if self._monitor_task:
            self._monitor_task.cancel()
        logger.info("System Monitor stopped")


def initialize_worker(worker_id: str, worker_type: str, config: Dict) -> Dict:
    """Initialize a worker process (runs in separate process)."""
    try:
        import os
        import signal
        
        process_id = os.getpid()
        
        # Setup worker-specific configuration
        worker_config = {
            'worker_id': worker_id,
            'worker_type': worker_type,
            'config': config
        }
        
        # Register signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Worker {worker_id} received signal {signum}")
            # Worker will be terminated by the main process
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        return {
            'success': True,
            'process_id': process_id,
            'worker_id': worker_id,
            'worker_type': worker_type
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize worker {worker_id}: {e}")
        return {
            'success': False,
            'error': str(e)
        }