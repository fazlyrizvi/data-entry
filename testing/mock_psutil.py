#!/usr/bin/env python3
"""
Mock psutil module for performance testing when system monitoring is not available.
"""

import random
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Mock CPU functions
def cpu_percent(interval=None):
    """Mock CPU percentage."""
    return random.uniform(20, 80)

def cpu_count():
    """Mock CPU count."""
    return 4  # Assume 4 cores

def cpu_freq():
    """Mock CPU frequency."""
    class MockCPUFreq:
        def __init__(self):
            self.current = 2400.0
            self.min = 1200.0
            self.max = 3600.0
        
        def _asdict(self):
            return {
                'current': self.current,
                'min': self.min,
                'max': self.max
            }
    
    return MockCPUFreq()

# Mock Memory functions
def virtual_memory():
    """Mock virtual memory."""
    class MockMemory:
        def __init__(self):
            self.percent = random.uniform(30, 70)
            self.used = 8 * 1024**3  # 8GB
            self.available = 16 * 1024**3  # 16GB
            self.total = 24 * 1024**3  # 24GB
    
    return MockMemory()

def swap_memory():
    """Mock swap memory."""
    class MockSwap:
        def __init__(self):
            self.percent = random.uniform(0, 10)
            self.used = 2 * 1024**3  # 2GB
            self.total = 8 * 1024**3  # 8GB
    
    return MockSwap()

# Mock Disk functions
def disk_usage(path):
    """Mock disk usage."""
    class MockDisk:
        def __init__(self):
            self.used = 500 * 1024**3  # 500GB
            self.free = 1500 * 1024**3  # 1.5TB
            self.total = 2000 * 1024**3  # 2TB
    
    return MockDisk()

# Mock Network functions
def net_io_counters():
    """Mock network I/O counters."""
    class MockNetIOCounters:
        def __init__(self):
            self.bytes_sent = random.randint(1000000, 10000000)
            self.bytes_recv = random.randint(1000000, 10000000)
            self.packets_sent = random.randint(1000, 10000)
            self.packets_recv = random.randint(1000, 10000)
    
    return MockNetIOCounters()

# Mock Process functions
def getloadavg():
    """Mock load average (Unix-like systems)."""
    return (1.5, 1.2, 1.1)

# Mock Process class
class Process:
    def __init__(self, pid=None):
        self.pid = pid or 1234
    
    def cpu_percent(self, interval=None):
        return random.uniform(10, 50)
    
    def memory_info(self):
        class MockMemoryInfo:
            def __init__(self):
                self.rss = 256 * 1024**2  # 256MB RSS
        return MockMemoryInfo()
    
    def memory_percent(self):
        return random.uniform(5, 15)
    
    def num_threads(self):
        return random.randint(4, 16)