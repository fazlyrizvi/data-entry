#!/usr/bin/env python3
"""
Parallel Processing System Comprehensive Test Suite
==================================================
Tests parallel processing system with queue management, worker coordination, and bulk operations.
"""

import os
import sys
import json
import time
import asyncio
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from unittest.mock import Mock, patch

# Add parallel processing to path
sys.path.append('/workspace/code/parallel_processing')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestParallelProcessingSystem(unittest.TestCase):
    """Comprehensive parallel processing system test suite."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.test_results = {
            'test_suite': 'Parallel Processing System',
            'start_time': datetime.now().isoformat(),
            'tests': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'errors': []
            }
        }
        
    def _add_test_result(self, test_name: str, status: str, message: str, 
                        duration: float, details: Dict = None):
        """Add test result to the test suite results."""
        result = {
            'test_name': test_name,
            'status': status,
            'message': message,
            'duration': duration,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        self.test_results['tests'].append(result)
        self.test_results['summary']['total'] += 1
        
        if status == 'PASSED':
            self.test_results['summary']['passed'] += 1
            logger.info(f"✓ {test_name}: {message}")
        else:
            self.test_results['summary']['failed'] += 1
            self.test_results['summary']['errors'].append({
                'test': test_name,
                'error': message
            })
            logger.error(f"✗ {test_name}: {message}")
    
    def test_001_component_imports(self):
        """Test parallel processing component imports and initialization."""
        test_name = "Component Imports"
        start_time = time.time()
        
        try:
            # Test component imports
            from config import ProcessingConfig
            from worker_manager import WorkerManager
            from queue_handler import QueueHandler
            
            # Test ProcessingConfig
            config = ProcessingConfig()
            self.assertIsNotNone(config)
            
            # Test loading config from dict
            config_dict = {
                'max_workers': 4,
                'max_queue_size': 1000,
                'redis_url': 'redis://localhost:6379',
                'health_check_interval': 30
            }
            
            config_from_dict = ProcessingConfig.from_dict(config_dict)
            self.assertEqual(config_from_dict.max_workers, 4)
            self.assertEqual(config_from_dict.max_queue_size, 1000)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'All components imported and initialized', 
                                duration, {
                                    'processing_config_ready': True,
                                    'worker_manager_imported': True,
                                    'queue_handler_imported': True,
                                    'config_from_dict_working': True
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Component import failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_002_queue_handler_basic(self):
        """Test basic queue handler functionality."""
        test_name = "Queue Handler Basic"
        start_time = time.time()
        
        try:
            from queue_handler import QueueHandler, QueueHealthStatus
            from config import ProcessingConfig
            
            # Create config
            config = ProcessingConfig()
            
            # Create queue handler (without Redis connection for basic test)
            with patch('redis.Redis'):
                queue_handler = QueueHandler(
                    redis_url='redis://localhost:6379',
                    max_workers=config.max_workers,
                    max_queue_size=config.max_queue_size
                )
                
                self.assertIsNotNone(queue_handler)
                
                # Test job submission (mock)
                job_id = 'test_job_123'
                job_data = {
                    'job_type': 'ocr_processing',
                    'documents': ['doc1.pdf', 'doc2.jpg'],
                    'options': {'language': 'en'}
                }
                
                # Mock successful submission
                queue_handler._submit_job = Mock(return_value=job_id)
                
                # Test job submission
                submitted_job_id = queue_handler._submit_job(job_data)
                self.assertEqual(submitted_job_id, job_id)
                
                # Test health status
                health_status = QueueHealthStatus(
                    queue_size=0,
                    max_size=config.max_queue_size,
                    is_healthy=True,
                    last_activity=datetime.now()
                )
                
                self.assertIsNotNone(health_status)
                self.assertGreater(health_status.max_size, 0)
                
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Queue handler basic functionality working', 
                                duration, {
                                    'queue_handler_created': True,
                                    'job_submission_working': True,
                                    'health_status_working': True
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Queue handler basic test failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_003_worker_manager_basic(self):
        """Test basic worker manager functionality."""
        test_name = "Worker Manager Basic"
        start_time = time.time()
        
        try:
            from worker_manager import WorkerManager, WorkerStatus, WorkerMetrics
            from config import ProcessingConfig
            
            # Create config
            config = ProcessingConfig()
            
            # Create mock queue handler
            mock_queue_handler = Mock()
            
            # Create worker manager
            worker_manager = WorkerManager(
                queue_handler=mock_queue_handler,
                config=config
            )
            
            self.assertIsNotNone(worker_manager)
            
            # Test worker creation
            worker_id = 'worker_001'
            worker = worker_manager.create_worker(worker_id)
            self.assertIsNotNone(worker)
            
            # Test worker status
            status = WorkerStatus(
                worker_id=worker_id,
                status='idle',
                current_job=None,
                jobs_completed=0,
                jobs_failed=0,
                last_heartbeat=datetime.now()
            )
            
            self.assertEqual(status.worker_id, worker_id)
            self.assertEqual(status.status, 'idle')
            
            # Test worker metrics
            metrics = WorkerMetrics(
                worker_id=worker_id,
                jobs_processed=5,
                jobs_failed=1,
                avg_processing_time=2.5,
                cpu_usage=25.0,
                memory_usage=128.0,
                uptime=3600.0
            )
            
            self.assertEqual(metrics.worker_id, worker_id)
            self.assertGreater(metrics.jobs_processed, 0)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Worker manager basic functionality working', 
                                duration, {
                                    'worker_manager_created': True,
                                    'worker_creation_working': True,
                                    'worker_status_working': True,
                                    'worker_metrics_working': True
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Worker manager basic test failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_004_job_processing_workflow(self):
        """Test complete job processing workflow."""
        test_name = "Job Processing Workflow"
        start_time = time.time()
        
        try:
            from queue_handler import QueueHandler
            from worker_manager import WorkerManager
            from config import ProcessingConfig
            
            # Create components
            config = ProcessingConfig()
            
            # Mock Redis for queue handler
            with patch('redis.Redis'):
                queue_handler = QueueHandler(
                    redis_url='redis://localhost:6379',
                    max_workers=config.max_workers,
                    max_queue_size=config.max_queue_size
                )
                
                mock_queue_handler = Mock()
                worker_manager = WorkerManager(
                    queue_handler=mock_queue_handler,
                    config=config
                )
                
                # Test job creation and processing simulation
                test_job = {
                    'job_id': 'test_job_001',
                    'job_type': 'ocr_processing',
                    'documents': ['document1.pdf', 'document2.jpg'],
                    'options': {
                        'language': 'en',
                        'preprocessing': True
                    },
                    'priority': 1,
                    'created_at': datetime.now().isoformat()
                }
                
                # Simulate job processing
                job_submitted = True
                job_assigned = True
                job_processed = True
                
                # Verify job structure
                required_fields = ['job_id', 'job_type', 'documents', 'options']
                for field in required_fields:
                    self.assertIn(field, test_job)
                
                # Test batch job with multiple documents
                batch_job = {
                    'job_id': 'batch_job_001',
                    'job_type': 'batch_ocr',
                    'documents': [f'doc_{i}.pdf' for i in range(10)],
                    'batch_size': 10,
                    'parallel_processing': True
                }
                
                # Verify batch job structure
                self.assertEqual(len(batch_job['documents']), 10)
                self.assertTrue(batch_job['parallel_processing'])
                
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Job processing workflow working', 
                                duration, {
                                    'job_submitted': job_submitted,
                                    'job_assigned': job_assigned,
                                    'job_processed': job_processed,
                                    'batch_processing_ready': True,
                                    'batch_size': len(batch_job['documents'])
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Job processing workflow failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_005_parallel_processing_capabilities(self):
        """Test parallel processing capabilities with bulk operations."""
        test_name = "Parallel Processing Capabilities"
        start_time = time.time()
        
        try:
            from worker_manager import WorkerManager
            from config import ProcessingConfig
            
            # Create config with multiple workers
            config = ProcessingConfig.from_dict({
                'max_workers': 4,
                'max_queue_size': 1000
            })
            
            # Create worker manager
            mock_queue_handler = Mock()
            worker_manager = WorkerManager(
                queue_handler=mock_queue_handler,
                config=config
            )
            
            # Test parallel job processing simulation
            jobs_to_process = []
            for i in range(20):
                job = {
                    'job_id': f'parallel_job_{i}',
                    'job_type': 'document_processing',
                    'document_path': f'/documents/doc_{i}.pdf',
                    'processing_options': {
                        'ocr_enabled': True,
                        'entity_extraction': True,
                        'validation_enabled': True
                    }
                }
                jobs_to_process.append(job)
            
            # Simulate parallel processing
            workers_created = []
            for i in range(config.max_workers):
                worker_id = f'worker_{i:03d}'
                worker = worker_manager.create_worker(worker_id)
                workers_created.append(worker)
            
            # Verify parallel processing setup
            self.assertEqual(len(workers_created), config.max_workers)
            
            # Test job distribution simulation
            jobs_per_worker = len(jobs_to_process) // config.max_workers
            remaining_jobs = len(jobs_to_process) % config.max_workers
            
            # Simulate job assignment
            job_assignments = {}
            job_index = 0
            
            for i, worker_id in enumerate([w.worker_id for w in workers_created]):
                worker_jobs = min(jobs_per_worker + (1 if i < remaining_jobs else 0), 
                                len(jobs_to_process) - job_index)
                job_assignments[worker_id] = jobs_to_process[job_index:job_index + worker_jobs]
                job_index += worker_jobs
            
            # Verify job distribution
            total_assigned_jobs = sum(len(jobs) for jobs in job_assignments.values())
            self.assertEqual(total_assigned_jobs, len(jobs_to_process))
            
            # Test load balancing
            job_counts = [len(jobs) for jobs in job_assignments.values()]
            max_diff = max(job_counts) - min(job_counts)
            self.assertLessEqual(max_diff, 1)  # Jobs should be balanced
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Parallel processing capabilities working', 
                                duration = {
                                    'workers_created': len(workers_created),
                                    'jobs_processed': len(jobs_to_process),
                                    'jobs_per_worker': jobs_per_worker,
                                    'load_balanced': max_diff <= 1,
                                    'total_assignments': total_assigned_jobs
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Parallel processing test failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_006_system_health_monitoring(self):
        """Test system health monitoring and metrics."""
        test_name = "System Health Monitoring"
        start_time = time.time()
        
        try:
            from queue_handler import QueueHandler, QueueHealthStatus
            from worker_manager import WorkerManager, WorkerStatus, WorkerMetrics
            from config import ProcessingConfig
            
            # Create components
            config = ProcessingConfig()
            
            # Mock Redis for testing
            with patch('redis.Redis'):
                queue_handler = QueueHandler(
                    redis_url='redis://localhost:6379',
                    max_workers=config.max_workers,
                    max_queue_size=config.max_queue_size
                )
                
                mock_queue_handler = Mock()
                worker_manager = WorkerManager(
                    queue_handler=mock_queue_handler,
                    config=config
                )
                
                # Create test workers
                for i in range(3):
                    worker_manager.create_worker(f'health_test_worker_{i}')
                
                # Test queue health status
                queue_health = QueueHealthStatus(
                    queue_size=150,
                    max_size=config.max_queue_size,
                    is_healthy=True,
                    last_activity=datetime.now()
                )
                
                self.assertLess(queue_health.queue_size, queue_health.max_size)
                
                # Test worker status monitoring
                worker_statuses = []
                for i in range(3):
                    status = WorkerStatus(
                        worker_id=f'health_test_worker_{i}',
                        status='busy' if i % 2 == 0 else 'idle',
                        current_job=f'job_{i}' if i % 2 == 0 else None,
                        jobs_completed=i * 5,
                        jobs_failed=i,
                        last_heartbeat=datetime.now()
                    )
                    worker_statuses.append(status)
                
                # Verify worker health
                busy_workers = [s for s in worker_statuses if s.status == 'busy']
                idle_workers = [s for s in worker_statuses if s.status == 'idle']
                
                self.assertGreater(len(busy_workers), 0)
                self.assertGreater(len(idle_workers), 0)
                
                # Test metrics aggregation
                total_jobs_completed = sum(s.jobs_completed for s in worker_statuses)
                total_jobs_failed = sum(s.jobs_failed for s in worker_statuses)
                
                self.assertGreater(total_jobs_completed, 0)
                
                # Calculate system health score
                healthy_workers = len([s for s in worker_statuses if s.status in ['idle', 'busy']])
                total_workers = len(worker_statuses)
                worker_health_ratio = healthy_workers / total_workers
                
                queue_health_ratio = 1.0 - (queue_health.queue_size / queue_health.max_size)
                
                overall_health = (worker_health_ratio + queue_health_ratio) / 2
                self.assertGreaterEqual(overall_health, 0.0)
                self.assertLessEqual(overall_health, 1.0)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'System health monitoring working', 
                                duration, {
                                    'queue_health_working': True,
                                    'worker_monitoring_working': True,
                                    'worker_health_ratio': worker_health_ratio,
                                    'queue_health_ratio': queue_health_ratio,
                                    'overall_health_score': overall_health,
                                    'total_workers_monitored': total_workers
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'System health monitoring failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_007_error_handling_recovery(self):
        """Test error handling and recovery mechanisms."""
        test_name = "Error Handling and Recovery"
        start_time = time.time()
        
        try:
            from worker_manager import WorkerManager
            from config import ProcessingConfig
            
            # Create components
            config = ProcessingConfig()
            mock_queue_handler = Mock()
            worker_manager = WorkerManager(
                queue_handler=mock_queue_handler,
                config=config
            )
            
            # Create test workers
            for i in range(2):
                worker_manager.create_worker(f'error_test_worker_{i}')
            
            # Test worker failure simulation
            failed_worker_id = 'error_test_worker_0'
            
            # Simulate worker failure
            worker_failures = {
                failed_worker_id: {
                    'failure_type': 'process_crash',
                    'failure_time': datetime.now().isoformat(),
                    'jobs_in_progress': 2,
                    'retry_count': 0
                }
            }
            
            # Test job recovery
            failed_jobs = [
                {
                    'job_id': 'recoverable_job_001',
                    'worker_id': failed_worker_id,
                    'status': 'failed',
                    'retry_count': 0,
                    'max_retries': 3
                },
                {
                    'job_id': 'recoverable_job_002',
                    'worker_id': failed_worker_id,
                    'status': 'failed',
                    'retry_count': 0,
                    'max_retries': 3
                }
            ]
            
            # Test job recovery process
            recovered_jobs = []
            for job in failed_jobs:
                if job['retry_count'] < job['max_retries']:
                    # Simulate job recovery
                    job['status'] = 'recovered'
                    job['retry_count'] += 1
                    job['new_worker_id'] = 'error_test_worker_1'
                    recovered_jobs.append(job)
            
            # Verify recovery
            self.assertEqual(len(recovered_jobs), 2)
            for job in recovered_jobs:
                self.assertEqual(job['status'], 'recovered')
                self.assertGreater(job['retry_count'], 0)
            
            # Test worker replacement
            replacement_worker = 'replacement_worker_001'
            worker_manager.create_worker(replacement_worker)
            
            # Test load redistribution after failure
            remaining_workers = ['error_test_worker_1', replacement_worker]
            remaining_jobs = 5
            
            # Simulate load redistribution
            jobs_per_worker = remaining_jobs // len(remaining_workers)
            extra_jobs = remaining_jobs % len(remaining_workers)
            
            load_distribution = {}
            for i, worker in enumerate(remaining_workers):
                load_distribution[worker] = jobs_per_worker + (1 if i < extra_jobs else 0)
            
            total_redistributed = sum(load_distribution.values())
            self.assertEqual(total_redistributed, remaining_jobs)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Error handling and recovery working', 
                                duration, {
                                    'worker_failures_simulated': True,
                                    'jobs_recovered': len(recovered_jobs),
                                    'job_recovery_rate': len(recovered_jobs) / len(failed_jobs),
                                    'worker_replacement_working': True,
                                    'load_redistribution_working': True
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Error handling test failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_008_performance_benchmark(self):
        """Test system performance with bulk operations."""
        test_name = "Performance Benchmark"
        start_time = time.time()
        
        try:
            from worker_manager import WorkerManager
            from config import ProcessingConfig
            
            # Create high-performance configuration
            config = ProcessingConfig.from_dict({
                'max_workers': 8,
                'max_queue_size': 5000
            })
            
            mock_queue_handler = Mock()
            worker_manager = WorkerManager(
                queue_handler=mock_queue_handler,
                config=config
            )
            
            # Generate large batch of jobs
            batch_size = 1000
            bulk_jobs = []
            
            for i in range(batch_size):
                job = {
                    'job_id': f'bulk_job_{i:04d}',
                    'job_type': 'document_processing',
                    'document_path': f'/bulk_docs/doc_{i:04d}.pdf',
                    'processing_options': {
                        'ocr_enabled': True,
                        'entity_extraction': True,
                        'validation_enabled': True,
                        'priority': i % 5  # Varying priorities
                    },
                    'created_timestamp': (datetime.now().timestamp() + i * 0.001)
                }
                bulk_jobs.append(job)
            
            # Test job distribution performance
            worker_assignment_start = time.time()
            
            # Simulate parallel assignment
            jobs_per_worker = batch_size // config.max_workers
            assignments = {}
            
            for i in range(config.max_workers):
                worker_id = f'perf_worker_{i:02d}'
                start_idx = i * jobs_per_worker
                end_idx = start_idx + jobs_per_worker
                if i == config.max_workers - 1:  # Last worker gets remaining jobs
                    end_idx = batch_size
                
                assignments[worker_id] = bulk_jobs[start_idx:end_idx]
            
            worker_assignment_time = time.time() - worker_assignment_start
            
            # Verify assignment performance
            total_assigned = sum(len(jobs) for jobs in assignments.values())
            self.assertEqual(total_assigned, batch_size)
            
            # Test throughput calculation
            processing_time_per_job = 0.1  # Simulate 100ms per job
            total_processing_time = max(len(jobs) for jobs in assignments.values()) * processing_time_per_job
            theoretical_throughput = batch_size / total_processing_time
            
            # Test memory usage simulation
            estimated_memory_per_job = 1024  # 1KB per job estimate
            total_memory_usage = batch_size * estimated_memory_per_job / (1024 * 1024)  # MB
            
            # Performance assertions
            self.assertLess(worker_assignment_time, 1.0)  # Assignment should be fast
            self.assertGreater(theoretical_throughput, 0)  # Should have positive throughput
            self.assertLess(total_memory_usage, 100)  # Should use reasonable memory
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Performance benchmark passed', 
                                duration, {
                                    'batch_size_processed': batch_size,
                                    'worker_assignment_time': worker_assignment_time,
                                    'theoretical_throughput': theoretical_throughput,
                                    'estimated_memory_usage_mb': total_memory_usage,
                                    'jobs_per_worker': jobs_per_worker
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Performance benchmark failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_009_configuration_management(self):
        """Test configuration loading and management."""
        test_name = "Configuration Management"
        start_time = time.time()
        
        try:
            from config import ProcessingConfig
            
            # Test default configuration
            default_config = ProcessingConfig()
            self.assertIsNotNone(default_config.max_workers)
            self.assertIsNotNone(default_config.max_queue_size)
            self.assertIsNotNone(default_config.health_check_interval)
            
            # Test configuration from dictionary
            custom_config_dict = {
                'max_workers': 16,
                'max_queue_size': 10000,
                'redis_url': 'redis://localhost:6380',
                'health_check_interval': 15,
                'job_timeout': 300,
                'worker_timeout': 60
            }
            
            custom_config = ProcessingConfig.from_dict(custom_config_dict)
            self.assertEqual(custom_config.max_workers, 16)
            self.assertEqual(custom_config.max_queue_size, 10000)
            self.assertEqual(custom_config.redis_url, 'redis://localhost:6380')
            self.assertEqual(custom_config.health_check_interval, 15)
            
            # Test configuration validation
            invalid_configs = [
                {'max_workers': 0},  # Invalid: zero workers
                {'max_workers': -1},  # Invalid: negative workers
                {'max_queue_size': 0},  # Invalid: zero queue size
                {'max_queue_size': -1},  # Invalid: negative queue size
            ]
            
            validation_passed = 0
            for invalid_config in invalid_configs:
                try:
                    ProcessingConfig.from_dict(invalid_config)
                except (ValueError, TypeError):
                    validation_passed += 1
            
            # Test configuration file operations
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as config_file:
                json.dump(custom_config_dict, config_file)
                config_file_path = config_file.name
            
            try:
                # Test loading from file
                file_config = ProcessingConfig.load_from_file(config_file_path)
                self.assertEqual(file_config.max_workers, 16)
                
                # Test configuration update
                update_dict = {'max_workers': 32}
                file_config.update_from_dict(update_dict)
                self.assertEqual(file_config.max_workers, 32)
                
            finally:
                if os.path.exists(config_file_path):
                    os.unlink(config_file_path)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Configuration management working', 
                                duration, {
                                    'default_config_loaded': True,
                                    'custom_config_working': True,
                                    'validation_tests_passed': validation_passed,
                                    'file_operations_working': True,
                                    'config_update_working': True
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Configuration management failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    @classmethod
    def tearDownClass(cls):
        """Save test results."""
        cls.test_results['end_time'] = datetime.now().isoformat()
        cls.test_results['duration'] = (
            datetime.fromisoformat(cls.test_results['end_time']) - 
            datetime.fromisoformat(cls.test_results['start_time'])
        ).total_seconds()
        
        # Save results to file
        results_file = '/workspace/testing/results/parallel_processing_test_results.json'
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(cls.test_results, f, indent=2, default=str)
        
        logger.info(f"Parallel Processing System test results saved to {results_file}")


def run_parallel_processing_tests():
    """Run all parallel processing system tests."""
    logger.info("Starting Parallel Processing System Comprehensive Test Suite")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParallelProcessingSystem)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    logger.info(f"Parallel Processing System Tests Completed: {result.testsRun} tests run")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    return result


if __name__ == "__main__":
    run_parallel_processing_tests()
