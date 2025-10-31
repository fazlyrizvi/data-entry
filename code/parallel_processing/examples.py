#!/usr/bin/env python3
"""
Example Usage Script
====================

Demonstrates how to use the parallel processing system for bulk document operations.
"""

import asyncio
import json
import time
from typing import List, Dict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import system components
from main import ParallelProcessingSystem
from config import get_config


async def example_basic_usage():
    """Example: Basic job submission and monitoring."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Job Submission")
    print("="*60)
    
    # Initialize system
    system = ParallelProcessingSystem()
    await system.initialize()
    
    # Submit a batch OCR job
    documents = [f"document_{i}.pdf" for i in range(1, 11)]
    
    print(f"Submitting OCR job with {len(documents)} documents...")
    job_id = await system.submit_batch_job(
        job_type="ocr",
        documents=documents,
        options={"language": "en", "preprocess": True},
        priority=5
    )
    
    print(f"Job submitted with ID: {job_id}")
    
    # Monitor progress
    start_time = time.time()
    while True:
        status = await system.get_job_status(job_id)
        
        print(f"Status: {status['status']} | "
              f"Progress: {status['progress']:.1%} | "
              f"Completed: {status['completed_tasks']}/{status['total_tasks']}")
        
        if status['status'] in ['completed', 'failed', 'cancelled']:
            break
        
        await asyncio.sleep(2)
    
    # Get results if completed
    if status['status'] == 'completed':
        results = await system.get_job_results(job_id)
        print(f"\nJob completed successfully!")
        print(f"Successful: {results['successful']}/{results['total_documents']}")
        print(f"Failed: {results['failed']}")
        
        # Show first result as example
        if results['results']:
            print(f"\nFirst result example:")
            print(json.dumps(results['results'][0], indent=2))
    
    elapsed = time.time() - start_time
    print(f"\nJob completed in {elapsed:.1f} seconds")
    
    # Shutdown
    system.shutdown()


async def example_multiple_job_types():
    """Example: Submit multiple jobs of different types."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Multiple Job Types")
    print("="*60)
    
    system = ParallelProcessingSystem()
    await system.initialize()
    
    # Submit jobs of different types
    job_configs = [
        {
            "job_type": "ocr",
            "documents": [f"ocr_doc_{i}.pdf" for i in range(5)],
            "options": {"language": "en"},
            "priority": 7
        },
        {
            "job_type": "nlp",
            "documents": [f"nlp_doc_{i}.txt" for i in range(5)],
            "options": {"model": "bert-base"},
            "priority": 5
        },
        {
            "job_type": "validation",
            "documents": [f"validation_doc_{i}.pdf" for i in range(5)],
            "options": {"strict_mode": True},
            "priority": 3
        }
    ]
    
    print("Submitting multiple jobs...")
    job_ids = []
    
    for config in job_configs:
        job_id = await system.submit_batch_job(**config)
        job_ids.append(job_id)
        print(f"Submitted {config['job_type']} job: {job_id}")
    
    # Monitor all jobs
    print("\nMonitoring job progress...")
    start_time = time.time()
    
    while True:
        all_completed = True
        
        for i, job_id in enumerate(job_ids):
            status = await system.get_job_status(job_id)
            job_type = job_configs[i]['job_type']
            
            if status['status'] not in ['completed', 'failed', 'cancelled']:
                all_completed = False
            
            print(f"{job_type}: {status['status']} | "
                  f"Progress: {status['progress']:.1%}")
        
        if all_completed:
            break
        
        await asyncio.sleep(3)
    
    elapsed = time.time() - start_time
    print(f"\nAll jobs completed in {elapsed:.1f} seconds")
    
    # Get summary
    total_successful = 0
    total_failed = 0
    
    for job_id in job_ids:
        results = await system.get_job_results(job_id)
        if results:
            total_successful += results['successful']
            total_failed += results['failed']
    
    print(f"Total processed: {total_successful} successful, {total_failed} failed")
    
    system.shutdown()


async def example_high_priority_job():
    """Example: Submit high priority job that preempts others."""
    print("\n" + "="*60)
    print("EXAMPLE 3: High Priority Job")
    print("="*60)
    
    system = ParallelProcessingSystem()
    await system.initialize()
    
    # Submit normal priority jobs first
    normal_docs = [f"normal_doc_{i}.pdf" for i in range(10)]
    normal_job = await system.submit_batch_job(
        job_type="ocr",
        documents=normal_docs,
        priority=1
    )
    
    print("Submitted normal priority job (priority=1)")
    
    # Wait a bit to let processing start
    await asyncio.sleep(2)
    
    # Submit high priority job
    urgent_docs = [f"urgent_doc_{i}.pdf" for i in range(3)]
    urgent_job = await system.submit_batch_job(
        job_type="nlp",
        documents=urgent_docs,
        priority=10  # High priority
    )
    
    print("Submitted high priority job (priority=10)")
    
    # Monitor both jobs
    start_time = time.time()
    
    while True:
        normal_status = await system.get_job_status(normal_job)
        urgent_status = await system.get_job_status(urgent_job)
        
        print(f"Normal job: {normal_status['status']} | Progress: {normal_status['progress']:.1%}")
        print(f"Urgent job: {urgent_status['status']} | Progress: {urgent_status['progress']:.1%}")
        
        if (normal_status['status'] in ['completed', 'failed', 'cancelled'] and
            urgent_status['status'] in ['completed', 'failed', 'cancelled']):
            break
        
        await asyncio.sleep(2)
    
    elapsed = time.time() - start_time
    print(f"\nJobs completed in {elapsed:.1f} seconds")
    
    system.shutdown()


async def example_job_cancellation():
    """Example: Submit and cancel a job."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Job Cancellation")
    print("="*60)
    
    system = ParallelProcessingSystem()
    await system.initialize()
    
    # Submit a long-running job
    documents = [f"long_doc_{i}.pdf" for i in range(20)]
    job_id = await system.submit_batch_job(
        job_type="ocr",
        documents=documents,
        priority=5
    )
    
    print(f"Submitted job: {job_id}")
    
    # Wait a bit and then cancel
    await asyncio.sleep(3)
    
    print("Cancelling job...")
    success = await system.queue_handler.cancel_job(job_id)
    
    if success:
        print("Job cancelled successfully")
    else:
        print("Failed to cancel job")
    
    # Verify cancellation
    status = await system.get_job_status(job_id)
    print(f"Final status: {status['status']}")
    
    system.shutdown()


async def example_performance_monitoring():
    """Example: Monitor system performance."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Performance Monitoring")
    print("="*60)
    
    system = ParallelProcessingSystem()
    await system.initialize()
    
    # Submit some jobs
    print("Submitting test jobs...")
    
    job_ids = []
    for i in range(3):
        job_id = await system.submit_batch_job(
            job_type="ocr",
            documents=[f"perf_doc_{j}.pdf" for j in range(5)],
            priority=5
        )
        job_ids.append(job_id)
    
    # Monitor performance while processing
    print("Monitoring performance metrics...")
    start_time = time.time()
    
    for _ in range(15):  # Monitor for 30 seconds (2 second intervals)
        metrics = await system.get_performance_metrics()
        
        print(f"\nTimestamp: {time.strftime('%H:%M:%S')}")
        print(f"Workers: {metrics['workers']['total_workers']}")
        print(f"Tasks Completed: {metrics['workers']['total_tasks_completed']}")
        print(f"Errors: {metrics['workers']['total_errors']}")
        print(f"Queue Size: {metrics['queue']['current_queue_size']}")
        print(f"Average Memory Usage: {metrics['workers']['average_memory_usage']:.1f} MB")
        print(f"Average CPU Usage: {metrics['workers']['average_cpu_usage']:.1%}")
        
        # Check if all jobs are complete
        all_done = True
        for job_id in job_ids:
            status = await system.get_job_status(job_id)
            if status['status'] not in ['completed', 'failed', 'cancelled']:
                all_done = False
                break
        
        if all_done:
            print("\nAll jobs completed!")
            break
        
        await asyncio.sleep(2)
    
    elapsed = time.time() - start_time
    print(f"\nMonitoring completed in {elapsed:.1f} seconds")
    
    system.shutdown()


async def example_configuration():
    """Example: Using custom configuration."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Custom Configuration")
    print("="*60)
    
    # Create custom configuration
    from config import ProcessingConfig
    
    config = ProcessingConfig()
    config.max_workers = 10
    config.worker_pools['ocr']['max_workers'] = 5
    config.worker_pools['nlp']['max_workers'] = 3
    config.features['autoscaling'] = True
    
    print(f"Custom configuration loaded:")
    print(f"  Max workers: {config.max_workers}")
    print(f"  OCR max workers: {config.worker_pools['ocr']['max_workers']}")
    print(f"  NLP max workers: {config.worker_pools['nlp']['max_workers']}")
    print(f"  Auto-scaling: {config.features['autoscaling']}")
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print(f"Configuration errors: {errors}")
    else:
        print("Configuration is valid")
    
    system = ParallelProcessingSystem()
    await system.initialize()
    
    # Submit a job with custom config
    job_id = await system.submit_batch_job(
        job_type="ocr",
        documents=["config_test.pdf"],
        options={"test_mode": True}
    )
    
    print(f"Job submitted with custom config: {job_id}")
    
    # Wait for completion
    while True:
        status = await system.get_job_status(job_id)
        if status['status'] in ['completed', 'failed', 'cancelled']:
            break
        await asyncio.sleep(1)
    
    print(f"Job status: {status['status']}")
    
    system.shutdown()


async def main():
    """Run all examples."""
    print("Parallel Processing System - Usage Examples")
    print("=" * 60)
    
    examples = [
        ("Basic Usage", example_basic_usage),
        ("Multiple Job Types", example_multiple_job_types),
        ("High Priority Job", example_high_priority_job),
        ("Job Cancellation", example_job_cancellation),
        ("Performance Monitoring", example_performance_monitoring),
        ("Custom Configuration", example_configuration),
    ]
    
    for name, func in examples:
        try:
            await func()
            print(f"\n{name} completed successfully!\n")
        except Exception as e:
            print(f"\n{name} failed with error: {e}\n")
        
        # Wait between examples
        await asyncio.sleep(2)
    
    print("All examples completed!")


if __name__ == "__main__":
    print("Starting Parallel Processing System Examples...")
    print("Note: Make sure Redis is running before starting!")
    print("\nPress Ctrl+C to exit early\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"\nExamples failed: {e}")
        import traceback
        traceback.print_exc()