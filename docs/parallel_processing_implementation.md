# Parallel Processing Implementation Documentation

## Overview

This document provides comprehensive documentation for the Parallel Processing System designed for bulk document operations. The system implements a scalable, fault-tolerant architecture that can handle thousands of documents in parallel across multiple worker pools.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Job Queue System](#job-queue-system)
4. [Worker Management](#worker-management)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Performance Monitoring](#performance-monitoring)
8. [Deployment Guide](#deployment-guide)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Architecture Overview

### System Architecture

The Parallel Processing System follows a distributed microservices architecture with the following key components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Main System   │    │  Queue Handler  │    │ Worker Manager  │
│   (Orchestrator)│    │   (Job Queue)   │    │ (Worker Pools)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │     Redis       │              │
         └──────────────│   (Backend)     │──────────────┘
                        └─────────────────┘
                                │
                    ┌─────────────────┐
                    │ Worker Processes│
                    │  (OCR, NLP,     │
                    │  Validation,    │
                    │  Preprocessing) │
                    └─────────────────┘
```

### Key Design Principles

1. **Horizontal Scalability**: Add more workers dynamically based on load
2. **Fault Tolerance**: Automatic retry mechanisms and failover handling
3. **Resource Management**: CPU, memory, and I/O monitoring and limits
4. **Persistence**: Redis-backed job storage for reliability
5. **Monitoring**: Comprehensive metrics and health checks
6. **Modularity**: Separate concerns for queue management, worker management, and orchestration

## Core Components

### 1. Main System (`main.py`)

The main system serves as the orchestrator, providing:

- **System Initialization**: Coordinates startup of all components
- **Health Monitoring**: Continuous system health checks
- **Job Submission API**: Public interface for submitting jobs
- **Graceful Shutdown**: Proper cleanup on termination signals

**Key Features:**
- Async/await based architecture for high concurrency
- Signal handling for graceful shutdown
- Performance metrics collection
- Health status reporting

### 2. Worker Manager (`worker_manager.py`)

Manages worker pools and provides:

- **Worker Pool Management**: Creates and manages worker pools by type
- **Load Balancing**: Distributes tasks across available workers
- **Auto-scaling**: Dynamically adjusts worker count based on load
- **Health Monitoring**: Monitors worker health and performs recovery
- **Resource Monitoring**: Tracks CPU, memory, and system resources

**Worker Types:**
- **OCR Workers**: Handle optical character recognition tasks
- **NLP Workers**: Process natural language processing tasks
- **Validation Workers**: Perform document validation and quality checks
- **Preprocessing Workers**: Prepare documents for downstream processing

### 3. Queue Handler (`queue_handler.py`)

Provides job queue management with:

- **Redis Backend**: Persistent job storage and queuing
- **Priority Queues**: Support for high, normal, and low priority jobs
- **Task Distribution**: Manages task assignment to workers
- **Progress Tracking**: Real-time progress updates
- **Result Management**: Stores and retrieves job results

**Queue Types:**
- **Priority Queues**: Separate queues for different priority levels
- **Worker-specific Queues**: Queues organized by worker type
- **Dead Letter Queue**: Failed jobs for manual review

### 4. Configuration (`config.py`)

Centralized configuration management:

- **Environment Variables**: Support for all config via env vars
- **Configuration Files**: JSON/YAML configuration file support
- **Environment-specific Configs**: Development, testing, and production configs
- **Validation**: Configuration validation and error reporting
- **Feature Flags**: Runtime feature toggles

## Job Queue System

### Job Structure

Each job consists of:
- **Job ID**: Unique identifier
- **Job Type**: Type of processing (ocr, nlp, validation, etc.)
- **Documents**: List of document identifiers or paths
- **Options**: Processing options and parameters
- **Priority**: Job priority (-10 to 10)
- **Status**: Current status (pending, queued, running, completed, failed, etc.)
- **Progress**: Completion percentage

### Task Structure

Each job is split into tasks:
- **Task ID**: Unique task identifier
- **Job ID**: Parent job identifier
- **Document ID**: Specific document to process
- **Task Type**: Type of task (matches job type)
- **Status**: Task status
- **Worker ID**: Assigned worker (if running)
- **Retry Count**: Number of retry attempts

### Queue Management

#### Priority System

The system implements a three-tier priority system:

1. **High Priority** (priority >= 10): Urgent jobs, processed first
2. **Normal Priority** (priority 1-9): Standard jobs
3. **Low Priority** (priority <= -10): Background jobs

#### Job Lifecycle

```
PENDING → QUEUED → RUNNING → COMPLETED
              ↓
            FAILED → [RETRY] → QUEUED
              ↓
           CANCELLED
```

#### Redis Storage

Jobs and tasks are stored in Redis with:
- **Job Storage**: `job:{job_id}` - Full job data
- **Task Storage**: `task:{task_id}` - Individual task data
- **Queue Storage**: Sorted sets with priority scores
- **TTL**: Automatic expiration based on job timeout

## Worker Management

### Worker Pools

Each worker type has a dedicated pool with:

- **Min Workers**: Minimum number of workers to maintain
- **Max Workers**: Maximum number of workers allowed
- **Memory Limit**: Maximum memory per worker (MB)
- **CPU Limit**: Maximum CPU usage per worker (0.0-1.0)
- **Timeout**: Worker timeout (seconds)

### Auto-scaling

The system automatically scales worker pools based on:

- **Queue Length**: Number of pending tasks
- **System Load**: CPU and memory usage
- **Processing Rate**: Tasks completed per time unit
- **Error Rate**: Failed tasks percentage

### Load Balancing

Tasks are distributed using:

- **Round Robin**: Even distribution across workers
- **Worker Health**: Skip unhealthy workers
- **Resource Awareness**: Consider worker resource usage
- **Priority Queuing**: Higher priority tasks get assigned first

### Worker Health Monitoring

Each worker is monitored for:

- **Heartbeat**: Regular health check signals
- **Error Rate**: Failure rate monitoring
- **Memory Usage**: Memory consumption tracking
- **CPU Usage**: CPU utilization monitoring
- **Task Completion**: Successful task completion rate

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `MAX_WORKERS` | `50` | Maximum total workers |
| `MAX_QUEUE_SIZE` | `10000` | Maximum queue size |
| `WORKER_TIMEOUT` | `300` | Worker timeout (seconds) |
| `HEALTH_CHECK_INTERVAL` | `30` | Health check interval (seconds) |
| `AUTOSCALING_INTERVAL` | `60` | Auto-scaling check interval |
| `MAX_MEMORY_PER_WORKER` | `1024` | Max memory per worker (MB) |
| `MAX_ERROR_RATE` | `0.1` | Maximum error rate (0.0-1.0) |

### Worker Pool Configuration

Each worker type can be configured with:

```python
OCR_WORKERS=8          # OCR worker pool size
NLP_WORKERS=4          # NLP worker pool size  
VALIDATION_WORKERS=6   # Validation worker pool size
PREPROCESSING_WORKERS=12 # Preprocessing worker pool size
```

### Configuration File

Create a `config.json` file:

```json
{
  "max_workers": 50,
  "redis_url": "redis://localhost:6379/0",
  "worker_pools": {
    "ocr": {
      "min_workers": 2,
      "max_workers": 8,
      "memory_limit": 1024,
      "cpu_limit": 0.8,
      "timeout": 300
    }
  },
  "features": {
    "autoscaling": true,
    "monitoring": true,
    "alerts": false
  }
}
```

## API Reference

### Main System API

#### Initialize System

```python
from main import ParallelProcessingSystem

system = ParallelProcessingSystem(config_path="config.json")
await system.initialize()
```

#### Submit Job

```python
job_id = await system.submit_batch_job(
    job_type="ocr",
    documents=["doc1.pdf", "doc2.pdf", "doc3.pdf"],
    options={"language": "en", "preprocess": true},
    priority=5
)
```

#### Get Job Status

```python
status = await system.get_job_status(job_id)
print(f"Status: {status['status']}")
print(f"Progress: {status['progress']}")
print(f"Completed: {status['completed_tasks']}/{status['total_tasks']}")
```

#### Get Job Results

```python
results = await system.get_job_results(job_id)
if results:
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Results: {results['results']}")
```

#### Get Performance Metrics

```python
metrics = await system.get_performance_metrics()
print(f"Total Workers: {metrics['workers']['total_workers']}")
print(f"Queue Size: {metrics['queue']['current_queue_size']}")
```

### Job Queue Operations

#### Submit Job (Direct)

```python
from queue_handler import QueueHandler

queue = QueueHandler(redis_url="redis://localhost:6379")
await queue.initialize()

job_id = await queue.submit_job(
    job_type="nlp",
    documents=["doc1.txt", "doc2.txt"],
    options={"model": "bert-base"},
    priority=7
)
```

#### Cancel Job

```python
success = await queue.cancel_job(job_id)
if success:
    print("Job cancelled successfully")
```

#### Retry Job

```python
success = await queue.retry_job(job_id)
if success:
    print("Job queued for retry")
```

#### Get Next Job (Worker)

```python
job = await queue.get_next_job(worker_id="worker_123", worker_type="ocr")
if job:
    print(f"Processing job: {job.job_id}")
    # Process documents...
    await queue.complete_task(task_id, result=result)
```

## Performance Monitoring

### System Metrics

The system collects comprehensive metrics:

#### Worker Metrics
- Total workers by type
- Active workers
- Worker utilization
- Memory usage per worker
- CPU usage per worker
- Tasks completed
- Error rates

#### Queue Metrics
- Jobs submitted/completed/failed
- Queue sizes by priority
- Task processing rates
- Average processing time
- Retry rates

#### System Metrics
- Redis connection status
- Memory usage
- CPU usage
- Disk usage
- Network I/O

### Health Checks

The system performs regular health checks:

#### Worker Health
- Heartbeat monitoring
- Error rate thresholds
- Resource usage limits
- Timeout detection

#### Queue Health
- Redis connectivity
- Queue size limits
- Dead letter queue monitoring
- Expired job cleanup

### Alerting

Alerts are generated for:
- Worker failures
- High error rates
- Resource exhaustion
- Queue overflow
- Redis connection issues

## Deployment Guide

### Prerequisites

1. **Redis Server**: Redis 6.0+ installed and running
2. **Python**: Python 3.8+ with pip
3. **System Resources**: Sufficient CPU, memory, and disk space
4. **Dependencies**: All packages from requirements.txt installed

### Installation

1. **Clone/Copy the system files**:
   ```bash
   mkdir parallel_processing
   cp -r code/parallel_processing/* parallel_processing/
   ```

2. **Install dependencies**:
   ```bash
   cd parallel_processing
   pip install -r requirements.txt
   ```

3. **Install Tesseract** (for OCR workers):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr
   
   # macOS
   brew install tesseract
   
   # Windows
   # Download from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

### Configuration

1. **Set environment variables**:
   ```bash
   export REDIS_URL="redis://localhost:6379/0"
   export MAX_WORKERS="20"
   export ENVIRONMENT="production"
   ```

2. **Create configuration file**:
   ```python
   from config import create_default_config_file
   create_default_config_file("production_config.json")
   ```

### Running the System

#### Development Mode
```bash
python main.py
```

#### Production Mode
```bash
# Using Gunicorn (recommended)
gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app

# Or with custom config
python main.py config.json
```

#### Systemd Service
Create `/etc/systemd/system/parallel-processing.service`:

```ini
[Unit]
Description=Parallel Processing System
After=network.target redis.service

[Service]
Type=simple
User=processing
WorkingDirectory=/opt/parallel_processing
Environment=PATH=/opt/parallel_processing/venv/bin
ExecStart=/opt/parallel_processing/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable parallel-processing
sudo systemctl start parallel-processing
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t parallel-processing .
docker run -p 8000:8000 \
  -e REDIS_URL="redis://redis:6379/0" \
  parallel-processing
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    
  parallel-processing:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - MAX_WORKERS=20
    depends_on:
      - redis
    volumes:
      - ./logs:/app/logs
```

Run:
```bash
docker-compose up -d
```

## Best Practices

### Resource Management

1. **Worker Limits**: Set appropriate min/max workers for each pool
2. **Memory Monitoring**: Monitor memory usage and adjust limits
3. **Queue Sizes**: Set reasonable queue size limits
4. **Timeouts**: Configure appropriate timeouts for different job types

### Performance Optimization

1. **Batch Processing**: Process documents in batches for efficiency
2. **Caching**: Enable caching for frequently accessed data
3. **Resource Monitoring**: Regular monitoring and adjustment
4. **Load Testing**: Test with production-like loads

### Reliability

1. **Retry Logic**: Implement appropriate retry strategies
2. **Circuit Breakers**: Prevent cascading failures
3. **Monitoring**: Comprehensive monitoring and alerting
4. **Backup**: Regular backup of job state and results

### Security

1. **Input Validation**: Validate all inputs
2. **Resource Limits**: Set memory and CPU limits
3. **Authentication**: Implement authentication for API access
4. **Audit Logging**: Log all operations for audit trail

### Scaling

1. **Horizontal Scaling**: Scale workers across multiple machines
2. **Load Distribution**: Distribute load evenly
3. **Auto-scaling**: Enable auto-scaling for variable loads
4. **Resource Planning**: Plan for peak load scenarios

## Troubleshooting

### Common Issues

#### Workers Not Starting

**Symptoms**: No workers available, queue not processing

**Solutions**:
1. Check Redis connection
2. Verify system resources (CPU, memory)
3. Check configuration settings
4. Review logs for errors

#### High Memory Usage

**Symptoms**: System running out of memory

**Solutions**:
1. Reduce `max_memory_per_worker`
2. Decrease worker counts
3. Enable garbage collection
4. Monitor memory usage patterns

#### Queue Backlog

**Symptoms**: Jobs queuing up, slow processing

**Solutions**:
1. Increase worker counts
2. Enable auto-scaling
3. Optimize task processing time
4. Scale horizontally

#### Redis Connection Issues

**Symptoms**: Connection refused, timeout errors

**Solutions**:
1. Verify Redis server is running
2. Check Redis connection string
3. Increase connection timeout
4. Monitor Redis performance

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python main.py
```

### Monitoring Commands

Check system status:
```python
health = await system.get_health_status()
print(json.dumps(health, indent=2))
```

Check queue metrics:
```python
metrics = await queue.get_queue_metrics("ocr")
print(f"OCR Queue Size: {metrics['pending_jobs']}")
```

### Log Analysis

Common log patterns:
- Worker startup: `Worker.*started successfully`
- Job submission: `Job.*submitted`
- Errors: `ERROR.*Failed`
- Performance: `Performance metrics`

### Performance Tuning

#### Worker Configuration
- Start with conservative worker counts
- Monitor resource usage
- Adjust based on actual load
- Use auto-scaling for variable loads

#### Redis Configuration
- Use Redis clustering for high availability
- Optimize Redis memory settings
- Enable Redis persistence
- Monitor Redis performance

#### System Resources
- Monitor CPU and memory usage
- Use SSD storage for better I/O
- Ensure adequate network bandwidth
- Plan for peak load scenarios

## Maintenance

### Regular Tasks

1. **Log Rotation**: Rotate and archive logs regularly
2. **Metrics Cleanup**: Clean old metrics data
3. **Job Cleanup**: Remove completed/failed jobs
4. **Performance Review**: Review and adjust configurations

### Backup and Recovery

1. **Redis Backup**: Regular Redis snapshots
2. **Configuration Backup**: Backup configuration files
3. **State Recovery**: Procedures for state recovery
4. **Disaster Recovery**: Plan for complete system failure

### Updates and Upgrades

1. **Testing**: Test updates in staging environment
2. **Rolling Updates**: Update workers incrementally
3. **Feature Flags**: Use flags for gradual rollout
4. **Rollback**: Procedures for rollback if needed

## Conclusion

The Parallel Processing System provides a robust, scalable solution for bulk document operations. By following the guidelines in this documentation, you can effectively deploy, monitor, and maintain the system in production environments.

For additional support or questions, refer to the code comments and logging output for detailed troubleshooting information.