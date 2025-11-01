#!/usr/bin/env python3
"""
Queue Handler - Job Queue Management
===================================

Manages job queues with Redis backend, handles job submission, progress tracking,
task distribution, and result management for parallel document processing.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis
import pickle

from config import ProcessingConfig

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


@dataclass
class Job:
    """Job data structure."""
    job_id: str
    job_type: str
    documents: List[str]
    options: Dict[str, Any]
    status: JobStatus
    priority: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    progress: float = 0.0
    worker_type: str = "general"
    timeout: int = 3600  # 1 hour default timeout
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


@dataclass
class Task:
    """Task data structure."""
    task_id: str
    job_id: str
    document_id: str
    task_type: str
    status: TaskStatus
    worker_id: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class QueueHandler:
    """Handles job queue management with Redis backend."""
    
    def __init__(self, redis_url: str, max_workers: int = 100, max_queue_size: int = 10000):
        """Initialize the queue handler."""
        self.redis_url = redis_url
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.redis_client = None
        self.is_running = False
        
        # Job and task storage
        self.jobs: Dict[str, Job] = {}
        self.tasks: Dict[str, Task] = {}
        
        # Queue names
        self.queues = {
            'ocr': 'queue:ocr',
            'nlp': 'queue:nlp',
            'validation': 'queue:validation',
            'preprocessing': 'queue:preprocessing',
            'general': 'queue:general'
        }
        
        # Priority queues for different job types
        self.priority_queues = {
            'high': 'priority:high',
            'normal': 'priority:normal',
            'low': 'priority:low'
        }
        
        # Worker assignment tracking
        self.worker_assignments: Dict[str, str] = {}  # worker_id -> queue_name
        
        # Performance metrics
        self.metrics = {
            'jobs_submitted': 0,
            'jobs_completed': 0,
            'jobs_failed': 0,
            'tasks_processed': 0,
            'average_processing_time': 0.0,
            'current_queue_size': 0,
            'worker_utilization': 0.0
        }
        
        # Job type configurations
        self.job_type_configs = {
            'ocr': {
                'worker_type': 'ocr',
                'default_timeout': 300,  # 5 minutes
                'priority': 'normal'
            },
            'nlp': {
                'worker_type': 'nlp', 
                'default_timeout': 180,  # 3 minutes
                'priority': 'normal'
            },
            'validation': {
                'worker_type': 'validation',
                'default_timeout': 120,  # 2 minutes
                'priority': 'low'
            },
            'batch_process': {
                'worker_type': 'general',
                'default_timeout': 600,  # 10 minutes
                'priority': 'normal'
            }
        }
        
        logger.info("Queue Handler initialized")
    
    async def initialize(self) -> None:
        """Initialize Redis connection and setup."""
        try:
            # Connect to Redis
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # We'll handle our own serialization
                max_connections=20,
                retry_on_timeout=True
            )
            
            # Test connection
            await self.redis_client.ping()
            
            # Load existing jobs and tasks from Redis
            await self._load_state()
            
            # Start background tasks
            self.is_running = True
            asyncio.create_task(self._cleanup_expired_jobs())
            asyncio.create_task(self._monitor_queue_health())
            asyncio.create_task(self._update_metrics())
            
            logger.info("Queue Handler initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Queue Handler: {e}")
            raise
    
    async def _load_state(self) -> None:
        """Load existing jobs and tasks from Redis."""
        try:
            # Load jobs
            job_keys = await self.redis_client.keys("job:*")
            for key in job_keys:
                try:
                    job_data = await self.redis_client.get(key)
                    if job_data:
                        job_dict = pickle.loads(job_data)
                        job = Job(**job_dict)
                        self.jobs[job.job_id] = job
                except Exception as e:
                    logger.error(f"Failed to load job from {key}: {e}")
            
            # Load tasks
            task_keys = await self.redis_client.keys("task:*")
            for key in task_keys:
                try:
                    task_data = await self.redis_client.get(key)
                    if task_data:
                        task_dict = pickle.loads(task_data)
                        task = Task(**task_dict)
                        self.tasks[task.task_id] = task
                except Exception as e:
                    logger.error(f"Failed to load task from {key}: {e}")
            
            logger.info(f"Loaded {len(self.jobs)} jobs and {len(self.tasks)} tasks from Redis")
            
        except Exception as e:
            logger.error(f"Failed to load state from Redis: {e}")
    
    async def submit_job(self, job_type: str, documents: List[str], 
                        options: Optional[Dict] = None, 
                        priority: int = 1) -> str:
        """Submit a new job for processing."""
        try:
            job_id = str(uuid.uuid4())
            config = self.job_type_configs.get(job_type, {})
            
            # Create job
            job = Job(
                job_id=job_id,
                job_type=job_type,
                documents=documents,
                options=options or {},
                status=JobStatus.PENDING,
                priority=priority,
                created_at=datetime.utcnow(),
                worker_type=config.get('worker_type', 'general'),
                timeout=config.get('default_timeout', 3600),
                total_tasks=len(documents)
            )
            
            # Create tasks for each document
            tasks = []
            for i, document_id in enumerate(documents):
                task_id = f"{job_id}_task_{i}"
                task = Task(
                    task_id=task_id,
                    job_id=job_id,
                    document_id=document_id,
                    task_type=job_type,
                    status=TaskStatus.PENDING,
                    created_at=datetime.utcnow()
                )
                tasks.append(task)
                self.tasks[task_id] = task
            
            # Store job and tasks in memory
            self.jobs[job_id] = job
            
            # Store in Redis
            await self._store_job(job)
            for task in tasks:
                await self._store_task(task)
            
            # Queue the job
            await self._queue_job(job)
            
            # Update metrics
            self.metrics['jobs_submitted'] += 1
            self.metrics['current_queue_size'] += 1
            
            logger.info(f"Job {job_id} submitted with {len(documents)} documents")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to submit job: {e}")
            raise
    
    async def _store_job(self, job: Job) -> None:
        """Store job in Redis."""
        try:
            key = f"job:{job.job_id}"
            value = pickle.dumps(asdict(job))
            await self.redis_client.setex(key, job.timeout + 3600, value)  # Store for timeout + 1 hour
        except Exception as e:
            logger.error(f"Failed to store job {job.job_id}: {e}")
    
    async def _store_task(self, task: Task) -> None:
        """Store task in Redis."""
        try:
            key = f"task:{task.task_id}"
            value = pickle.dumps(asdict(task))
            await self.redis_client.setex(key, 3600, value)  # Store for 1 hour
        except Exception as e:
            logger.error(f"Failed to store task {task.task_id}: {e}")
    
    async def _queue_job(self, job: Job) -> None:
        """Queue a job for processing."""
        try:
            # Determine queue based on job type
            queue_name = self.queues.get(job.worker_type, self.queues['general'])
            
            # Add to priority queue
            priority_queue = self.priority_queues['normal']
            if job.priority >= 10:
                priority_queue = self.priority_queues['high']
            elif job.priority <= -10:
                priority_queue = self.priority_queues['low']
            
            # Store job with score based on priority (higher score = higher priority)
            score = job.priority * 1000 - job.created_at.timestamp()
            await self.redis_client.zadd(priority_queue, {job.job_id: score})
            
            # Mark job as queued
            job.status = JobStatus.QUEUED
            
            # Store updated job
            await self._store_job(job)
            
        except Exception as e:
            logger.error(f"Failed to queue job {job.job_id}: {e}")
            raise
    
    async def get_next_job(self, worker_id: str, worker_type: str) -> Optional[Job]:
        """Get next job for a worker."""
        try:
            # Check if worker already has a job assigned
            if worker_id in self.worker_assignments:
                assigned_job_id = self.worker_assignments[worker_id]
                job = self.jobs.get(assigned_job_id)
                if job and job.status in [JobStatus.QUEUED, JobStatus.RUNNING]:
                    return job
                else:
                    # Clean up stale assignment
                    del self.worker_assignments[worker_id]
            
            # Get appropriate queue
            queue_name = self.queues.get(worker_type, self.queues['general'])
            
            # Try to get job from priority queues
            for priority_queue in [self.priority_queues['high'], 
                                 self.priority_queues['normal'], 
                                 self.priority_queues['low']]:
                # Get highest priority job
                job_ids = await self.redis_client.zrevrange(priority_queue, 0, 0)
                
                if job_ids:
                    job_id = job_ids[0].decode() if isinstance(job_ids[0], bytes) else job_ids[0]
                    
                    # Remove from priority queue
                    await self.redis_client.zrem(priority_queue, job_id)
                    
                    # Get job details
                    job = self.jobs.get(job_id)
                    if job and job.status == JobStatus.QUEUED:
                        # Assign job to worker
                        job.status = JobStatus.RUNNING
                        job.started_at = datetime.utcnow()
                        self.worker_assignments[worker_id] = job_id
                        
                        # Update job in Redis and memory
                        await self._store_job(job)
                        
                        logger.info(f"Assigned job {job_id} to worker {worker_id}")
                        return job
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get next job for worker {worker_id}: {e}")
            return None
    
    async def update_job_progress(self, job_id: str, completed_tasks: int, 
                                 failed_tasks: int = 0) -> None:
        """Update job progress."""
        try:
            job = self.jobs.get(job_id)
            if not job:
                return
            
            job.completed_tasks = completed_tasks
            job.failed_tasks = failed_tasks
            
            if job.total_tasks > 0:
                job.progress = (completed_tasks + failed_tasks) / job.total_tasks
            
            # Update job in Redis
            await self._store_job(job)
            
        except Exception as e:
            logger.error(f"Failed to update job progress for {job_id}: {e}")
    
    async def complete_task(self, task_id: str, result: Optional[Dict] = None, 
                           error: Optional[str] = None) -> None:
        """Mark a task as completed."""
        try:
            task = self.tasks.get(task_id)
            if not task:
                return
            
            task.status = TaskStatus.COMPLETED if not error else TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.result = result
            task.error_message = error
            
            # Update in Redis
            await self._store_task(task)
            
            # Update job progress
            job = self.jobs.get(task.job_id)
            if job:
                if task.status == TaskStatus.COMPLETED:
                    await self.update_job_progress(job.job_id, job.completed_tasks + 1, job.failed_tasks)
                else:
                    await self.update_job_progress(job.job_id, job.completed_tasks, job.failed_tasks + 1)
                
                # Check if job is complete
                if job.completed_tasks + job.failed_tasks >= job.total_tasks:
                    await self._complete_job(job.job_id)
            
            self.metrics['tasks_processed'] += 1
            
        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {e}")
    
    async def _complete_job(self, job_id: str) -> None:
        """Complete a job when all tasks are finished."""
        try:
            job = self.jobs.get(job_id)
            if not job:
                return
            
            job.status = JobStatus.COMPLETED if job.failed_tasks == 0 else JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            
            # Collect results from all tasks
            results = []
            for task in self.tasks.values():
                if task.job_id == job_id and task.status == TaskStatus.COMPLETED:
                    results.append({
                        'task_id': task.task_id,
                        'document_id': task.document_id,
                        'result': task.result
                    })
            
            job.results = {
                'total_documents': job.total_tasks,
                'successful': job.completed_tasks,
                'failed': job.failed_tasks,
                'results': results
            }
            
            # Store updated job
            await self._store_job(job)
            
            # Update metrics
            self.metrics['jobs_completed'] += 1
            self.metrics['current_queue_size'] = max(0, self.metrics['current_queue_size'] - 1)
            
            # Remove from worker assignments
            worker_to_remove = [wid for wid, jid in self.worker_assignments.items() if jid == job_id]
            for wid in worker_to_remove:
                del self.worker_assignments[wid]
            
            logger.info(f"Job {job_id} completed: {job.completed_tasks} successful, {job.failed_tasks} failed")
            
        except Exception as e:
            logger.error(f"Failed to complete job {job_id}: {e}")
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        try:
            job = self.jobs.get(job_id)
            if not job or job.status not in [JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING]:
                return False
            
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            
            # Cancel all pending tasks
            for task in self.tasks.values():
                if task.job_id == job_id and task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                    task.completed_at = datetime.utcnow()
                    await self._store_task(task)
            
            # Remove from worker assignments
            worker_to_remove = [wid for wid, jid in self.worker_assignments.items() if jid == job_id]
            for wid in worker_to_remove:
                del self.worker_assignments[wid]
            
            # Store updated job
            await self._store_job(job)
            
            self.metrics['current_queue_size'] = max(0, self.metrics['current_queue_size'] - 1)
            
            logger.info(f"Job {job_id} cancelled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    async def retry_job(self, job_id: str) -> bool:
        """Retry a failed job."""
        try:
            job = self.jobs.get(job_id)
            if not job or job.status != JobStatus.FAILED:
                return False
            
            if job.retry_count >= job.max_retries:
                return False
            
            # Reset job state
            job.status = JobStatus.PENDING
            job.retry_count += 1
            job.completed_tasks = 0
            job.failed_tasks = 0
            job.progress = 0.0
            job.error_message = None
            job.results = None
            
            # Reset all tasks
            for task in self.tasks.values():
                if task.job_id == job_id:
                    task.status = TaskStatus.PENDING
                    task.retry_count += 1
                    task.started_at = None
                    task.completed_at = None
                    task.error_message = None
                    task.result = None
                    await self._store_task(task)
            
            # Queue job again
            await self._queue_job(job)
            await self._store_job(job)
            
            # Remove from worker assignments
            worker_to_remove = [wid for wid, jid in self.worker_assignments.items() if jid == job_id]
            for wid in worker_to_remove:
                del self.worker_assignments[wid]
            
            self.metrics['current_queue_size'] += 1
            
            logger.info(f"Job {job_id} queued for retry (attempt {job.retry_count})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to retry job {job_id}: {e}")
            return False
    
    async def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status."""
        job = self.jobs.get(job_id)
        if not job:
            return None
        
        return {
            'job_id': job.job_id,
            'job_type': job.job_type,
            'status': job.status.value,
            'priority': job.priority,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'total_tasks': job.total_tasks,
            'completed_tasks': job.completed_tasks,
            'failed_tasks': job.failed_tasks,
            'progress': job.progress,
            'worker_type': job.worker_type,
            'timeout': job.timeout,
            'retry_count': job.retry_count,
            'max_retries': job.max_retries,
            'error_message': job.error_message
        }
    
    async def get_job_results(self, job_id: str) -> Optional[Dict]:
        """Get job results."""
        job = self.jobs.get(job_id)
        if not job or job.status != JobStatus.COMPLETED:
            return None
        
        return job.results
    
    async def get_queue_metrics(self, worker_type: str = None) -> Dict:
        """Get queue metrics for a specific worker type."""
        try:
            metrics = {
                'pending_jobs': 0,
                'active_jobs': 0,
                'completed_jobs': 0,
                'failed_jobs': 0,
                'pending_tasks': 0,
                'active_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0
            }
            
            # Calculate metrics from job data
            for job in self.jobs.values():
                if worker_type and job.worker_type != worker_type:
                    continue
                
                if job.status == JobStatus.QUEUED:
                    metrics['pending_jobs'] += 1
                elif job.status == JobStatus.RUNNING:
                    metrics['active_jobs'] += 1
                elif job.status == JobStatus.COMPLETED:
                    metrics['completed_jobs'] += 1
                elif job.status == JobStatus.FAILED:
                    metrics['failed_jobs'] += 1
            
            # Calculate task metrics
            for task in self.tasks.values():
                if worker_type:
                    job = self.jobs.get(task.job_id)
                    if not job or job.worker_type != worker_type:
                        continue
                
                if task.status == TaskStatus.PENDING:
                    metrics['pending_tasks'] += 1
                elif task.status == TaskStatus.RUNNING:
                    metrics['active_tasks'] += 1
                elif task.status == TaskStatus.COMPLETED:
                    metrics['completed_tasks'] += 1
                elif task.status == TaskStatus.FAILED:
                    metrics['failed_tasks'] += 1
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get queue metrics: {e}")
            return {}
    
    async def _cleanup_expired_jobs(self) -> None:
        """Clean up expired jobs and tasks."""
        while self.is_running:
            try:
                current_time = datetime.utcnow()
                
                # Clean up expired jobs
                expired_job_ids = []
                for job_id, job in self.jobs.items():
                    if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] and
                        job.completed_at and 
                        (current_time - job.completed_at).total_seconds() > 3600):  # 1 hour
                        expired_job_ids.append(job_id)
                
                for job_id in expired_job_ids:
                    await self._cleanup_job(job_id)
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_job(self, job_id: str) -> None:
        """Clean up a job and its tasks."""
        try:
            # Remove from Redis
            await self.redis_client.delete(f"job:{job_id}")
            
            # Remove tasks
            for task in list(self.tasks.values()):
                if task.job_id == job_id:
                    await self.redis_client.delete(f"task:{task.task_id}")
                    del self.tasks[task.task_id]
            
            # Remove from memory
            del self.jobs[job_id]
            
            logger.debug(f"Cleaned up expired job {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup job {job_id}: {e}")
    
    async def _monitor_queue_health(self) -> None:
        """Monitor queue health and detect issues."""
        while self.is_running:
            try:
                # Check Redis connection
                try:
                    await self.redis_client.ping()
                except:
                    logger.error("Redis connection lost")
                    # Try to reconnect
                    await self.initialize()
                
                # Check for stale worker assignments
                current_time = datetime.utcnow()
                stale_assignments = []
                
                for worker_id, job_id in self.worker_assignments.items():
                    job = self.jobs.get(job_id)
                    if job and job.started_at:
                        time_since_start = (current_time - job.started_at).total_seconds()
                        if time_since_start > job.timeout:
                            stale_assignments.append(worker_id)
                
                # Clean up stale assignments
                for worker_id in stale_assignments:
                    logger.warning(f"Cleaning up stale assignment for worker {worker_id}")
                    del self.worker_assignments[worker_id]
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in queue health monitor: {e}")
                await asyncio.sleep(30)
    
    async def _update_metrics(self) -> None:
        """Update performance metrics."""
        while self.is_running:
            try:
                # Calculate worker utilization
                total_assignments = len(self.worker_assignments)
                self.metrics['worker_utilization'] = total_assignments / max(self.max_workers, 1)
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
                await asyncio.sleep(30)
    
    async def get_health_status(self) -> Dict:
        """Get queue handler health status."""
        try:
            # Check Redis connection
            redis_healthy = False
            try:
                await self.redis_client.ping()
                redis_healthy = True
            except:
                pass
            
            return {
                'status': 'healthy' if redis_healthy else 'unhealthy',
                'redis_connection': redis_healthy,
                'total_jobs': len(self.jobs),
                'total_tasks': len(self.tasks),
                'active_assignments': len(self.worker_assignments),
                'metrics': self.metrics,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def get_metrics(self) -> Dict:
        """Get performance metrics."""
        return {
            **self.metrics,
            'total_jobs': len(self.jobs),
            'total_tasks': len(self.tasks),
            'active_assignments': len(self.worker_assignments),
            'queue_sizes': {
                queue_type: await self.redis_client.zcard(queue_name)
                for queue_type, queue_name in self.priority_queues.items()
            }
        }
    
    def shutdown(self) -> None:
        """Shutdown the queue handler."""
        logger.info("Shutting down Queue Handler...")
        
        self.is_running = False
        
        if self.redis_client:
            self.redis_client.close()
        
        # Store final state
        asyncio.create_task(self._save_final_state())
        
        logger.info("Queue Handler shutdown completed")
    
    async def _save_final_state(self) -> None:
        """Save final state before shutdown."""
        try:
            # Save all jobs and tasks to Redis
            for job in self.jobs.values():
                await self._store_job(job)
            
            for task in self.tasks.values():
                await self._store_task(task)
            
        except Exception as e:
            logger.error(f"Failed to save final state: {e}")


# Worker task processing functions

async def process_task(task: Task, worker_config: Dict) -> Dict:
    """Process a single task (runs in worker process)."""
    try:
        logger.info(f"Processing task {task.task_id} for document {task.document_id}")
        
        # Simulate task processing based on task type
        if task.task_type == 'ocr':
            result = await _process_ocr_task(task, worker_config)
        elif task.task_type == 'nlp':
            result = await _process_nlp_task(task, worker_config)
        elif task.task_type == 'validation':
            result = await _process_validation_task(task, worker_config)
        else:
            result = await _process_general_task(task, worker_config)
        
        return {
            'success': True,
            'task_id': task.task_id,
            'document_id': task.document_id,
            'result': result
        }
        
    except Exception as e:
        logger.error(f"Task processing failed for {task.task_id}: {e}")
        return {
            'success': False,
            'task_id': task.task_id,
            'document_id': task.document_id,
            'error': str(e)
        }


async def _process_ocr_task(task: Task, worker_config: Dict) -> Dict:
    """Process OCR task."""
    # Simulate OCR processing
    await asyncio.sleep(0.1)  # Simulate processing time
    
    return {
        'text_extracted': f"OCR result for document {task.document_id}",
        'confidence': 0.95,
        'processing_time': 0.1
    }


async def _process_nlp_task(task: Task, worker_config: Dict) -> Dict:
    """Process NLP task."""
    # Simulate NLP processing
    await asyncio.sleep(0.2)  # Simulate processing time
    
    return {
        'entities': ['Entity1', 'Entity2'],
        'sentiment': 'positive',
        'keywords': ['keyword1', 'keyword2'],
        'processing_time': 0.2
    }


async def _process_validation_task(task: Task, worker_config: Dict) -> Dict:
    """Process validation task."""
    # Simulate validation
    await asyncio.sleep(0.05)  # Simulate processing time
    
    return {
        'is_valid': True,
        'validation_score': 0.98,
        'issues': [],
        'processing_time': 0.05
    }


async def _process_general_task(task: Task, worker_config: Dict) -> Dict:
    """Process general task."""
    # Simulate general processing
    await asyncio.sleep(0.1)  # Simulate processing time
    
    return {
        'processed': True,
        'output': f"Processed document {task.document_id}",
        'processing_time': 0.1
    }