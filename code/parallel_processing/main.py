#!/usr/bin/env python3
"""
Parallel Processing System - Main Entry Point
===========================================

Main entry point for the parallel document processing system.
Handles initialization, configuration, and coordination of all components.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from worker_manager import WorkerManager
from queue_handler import QueueHandler
from config import ProcessingConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parallel_processing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class ParallelProcessingSystem:
    """Main system orchestrator for parallel document processing."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the parallel processing system."""
        self.config = ProcessingConfig.load_from_file(config_path)
        self.worker_manager = None
        self.queue_handler = None
        self.is_running = False
        
        logger.info("Initializing Parallel Processing System...")
    
    async def initialize(self) -> None:
        """Initialize all system components."""
        try:
            # Initialize queue handler
            self.queue_handler = QueueHandler(
                redis_url=self.config.redis_url,
                max_workers=self.config.max_workers,
                max_queue_size=self.config.max_queue_size
            )
            await self.queue_handler.initialize()
            
            # Initialize worker manager
            self.worker_manager = WorkerManager(
                queue_handler=self.queue_handler,
                config=self.config
            )
            
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            logger.info("System initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            raise
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        import signal
        
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown()
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    async def start(self) -> None:
        """Start the processing system."""
        if self.is_running:
            logger.warning("System is already running")
            return
        
        await self.initialize()
        
        try:
            # Start worker manager
            await self.worker_manager.start()
            
            self.is_running = True
            logger.info("Parallel Processing System started successfully")
            
            # Keep the system running
            await self._monitor_system()
            
        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            await self.shutdown()
            raise
    
    async def _monitor_system(self) -> None:
        """Monitor system health and performance."""
        while self.is_running:
            try:
                # Check system health
                health_status = await self.get_health_status()
                
                if health_status['status'] != 'healthy':
                    logger.warning(f"System health issues detected: {health_status}")
                    await self._handle_health_issues(health_status)
                
                # Log performance metrics
                await self._log_performance_metrics()
                
                # Sleep for monitoring interval
                await asyncio.sleep(self.config.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                await asyncio.sleep(5)
    
    async def get_health_status(self) -> Dict:
        """Get current system health status."""
        if not self.worker_manager or not self.queue_handler:
            return {'status': 'unhealthy', 'error': 'System not initialized'}
        
        worker_health = await self.worker_manager.get_health_status()
        queue_health = await self.queue_handler.get_health_status()
        
        return {
            'status': 'healthy' if all([
                worker_health['status'] == 'healthy',
                queue_health['status'] == 'healthy'
            ]) else 'degraded',
            'workers': worker_health,
            'queue': queue_health,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _handle_health_issues(self, health_status: Dict) -> None:
        """Handle detected health issues."""
        if health_status['workers']['status'] != 'healthy':
            logger.warning("Attempting to recover worker pool...")
            await self.worker_manager.recover_workers()
    
    async def _log_performance_metrics(self) -> None:
        """Log current performance metrics."""
        if not self.worker_manager or not self.queue_handler:
            return
        
        metrics = await self.get_performance_metrics()
        logger.info(f"Performance metrics: {metrics}")
    
    async def get_performance_metrics(self) -> Dict:
        """Get current performance metrics."""
        return {
            'workers': await self.worker_manager.get_metrics(),
            'queue': await self.queue_handler.get_metrics(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def shutdown(self) -> None:
        """Gracefully shutdown the system."""
        logger.info("Shutting down Parallel Processing System...")
        
        self.is_running = False
        
        if self.worker_manager:
            self.worker_manager.shutdown()
        
        if self.queue_handler:
            self.queue_handler.shutdown()
        
        logger.info("System shutdown completed")
    
    # Public API for job submission
    async def submit_batch_job(self, job_type: str, documents: List[str], 
                              options: Optional[Dict] = None) -> str:
        """Submit a batch processing job."""
        if not self.queue_handler:
            raise RuntimeError("System not initialized")
        
        job_id = await self.queue_handler.submit_job(
            job_type=job_type,
            documents=documents,
            options=options or {}
        )
        
        logger.info(f"Submitted batch job {job_id} with {len(documents)} documents")
        return job_id
    
    async def get_job_status(self, job_id: str) -> Dict:
        """Get status of a specific job."""
        if not self.queue_handler:
            raise RuntimeError("System not initialized")
        
        return await self.queue_handler.get_job_status(job_id)
    
    async def get_job_results(self, job_id: str) -> Optional[Dict]:
        """Get results of a completed job."""
        if not self.queue_handler:
            raise RuntimeError("System not initialized")
        
        return await self.queue_handler.get_job_results(job_id)


async def main():
    """Main entry point."""
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    system = ParallelProcessingSystem(config_path)
    
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())