# Parallel Processing System

A high-performance parallel processing system for bulk document operations with worker pools, job queues, and distributed processing capabilities.

## Features

- **Job Queue System**: Redis-backed job queuing with priority support
- **Worker Pools**: Dynamic worker pool management with auto-scaling
- **Load Balancing**: Intelligent task distribution across workers
- **Progress Tracking**: Real-time job and task progress monitoring
- **Resource Management**: CPU, memory, and I/O monitoring and limits
- **Failover Mechanisms**: Automatic recovery and retry logic
- **Performance Monitoring**: Comprehensive metrics and health checks

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up Redis:
   ```bash
   redis-server
   ```

3. Configure environment:
   ```bash
   export REDIS_URL="redis://localhost:6379/0"
   export MAX_WORKERS="20"
   ```

4. Run the system:
   ```bash
   python main.py
   ```

## Architecture

- **main.py**: System orchestration and main entry point
- **worker_manager.py**: Worker pool management and auto-scaling
- **queue_handler.py**: Job queue management and task distribution
- **config.py**: Configuration management and environment settings

## Usage

```python
from main import ParallelProcessingSystem
import asyncio

async def main():
    system = ParallelProcessingSystem()
    await system.start()
    
    # Submit a batch job
    job_id = await system.submit_batch_job(
        job_type="ocr",
        documents=["doc1.pdf", "doc2.pdf", "doc3.pdf"],
        options={"language": "en"}
    )
    
    # Monitor progress
    status = await system.get_job_status(job_id)
    print(f"Job status: {status}")
    
    # Get results
    results = await system.get_job_results(job_id)
    print(f"Results: {results}")

asyncio.run(main())
```

## Configuration

The system supports extensive configuration through environment variables or config files. See `config.py` for all available options.

## Worker Types

- **OCR**: Optical character recognition processing
- **NLP**: Natural language processing tasks  
- **Validation**: Document validation and quality checks
- **Preprocessing**: Document preparation and formatting

## Performance

- Supports thousands of documents in parallel
- Configurable worker pools (1-100+ workers)
- Redis-backed persistent job storage
- Automatic scaling based on queue load
- Real-time monitoring and metrics

## Documentation

See `docs/parallel_processing_implementation.md` for detailed documentation.