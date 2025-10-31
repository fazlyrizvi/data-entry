#!/usr/bin/env python3
"""
Resource Monitor Module
======================

Monitors system resource usage during performance testing.
Tracks CPU, memory, disk, and network utilization.
"""

import asyncio
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import deque

# Try to import psutil, fall back to mock if not available
try:
    import psutil
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    import mock_psutil as psutil

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """System resource monitoring during performance tests."""
    
    def __init__(self, monitoring_interval: float = 1.0):
        """Initialize resource monitor.
        
        Args:
            monitoring_interval: Time interval between measurements in seconds
        """
        self.monitoring_interval = monitoring_interval
        self.monitoring = False
        self.monitor_thread = None
        self.resource_data = []
        self.start_time = None
        
        # Initialize monitoring data structures
        self.cpu_data = deque(maxlen=1000)
        self.memory_data = deque(maxlen=1000)
        self.disk_data = deque(maxlen=1000)
        self.network_data = deque(maxlen=1000)
        
        # Get initial network stats
        self.initial_network = psutil.net_io_counters()
    
    def start_monitoring(self):
        """Start resource monitoring."""
        if self.monitoring:
            logger.warning("Resource monitoring is already running")
            return
        
        logger.info("Starting resource monitoring")
        self.monitoring = True
        self.start_time = time.time()
        self.resource_data = []
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop resource monitoring and return statistics."""
        if not self.monitoring:
            logger.warning("Resource monitoring is not running")
            return self._get_empty_stats()
        
        logger.info("Stopping resource monitoring")
        self.monitoring = False
        
        # Wait for monitor thread to finish
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        
        # Calculate final statistics
        return self._calculate_statistics()
    
    def _monitor_loop(self):
        """Main monitoring loop (runs in separate thread)."""
        while self.monitoring:
            try:
                timestamp = time.time()
                elapsed_time = timestamp - self.start_time
                
                # Collect system metrics
                metrics = self._collect_system_metrics()
                metrics["timestamp"] = timestamp
                metrics["elapsed_time"] = elapsed_time
                
                # Store metrics
                self.resource_data.append(metrics)
                
                # Update individual data deques
                self.cpu_data.append(metrics["cpu_percent"])
                self.memory_data.append(metrics["memory_percent"])
                self.disk_data.append(metrics["disk_percent"])
                
                # Update network data
                current_network = psutil.net_io_counters()
                network_delta = self._calculate_network_delta(current_network)
                self.network_data.append(network_delta)
                self.initial_network = current_network
                
                # Sleep for monitoring interval
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                time.sleep(1)  # Brief pause before retrying
    
    def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect current system metrics."""
        metrics = {}
        
        try:
            # CPU metrics
            metrics["cpu_percent"] = psutil.cpu_percent(interval=None)
            metrics["cpu_count"] = psutil.cpu_count()
            metrics["cpu_freq"] = psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {}
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics["memory_percent"] = memory.percent
            metrics["memory_used_gb"] = memory.used / (1024**3)
            metrics["memory_available_gb"] = memory.available / (1024**3)
            metrics["memory_total_gb"] = memory.total / (1024**3)
            
            # Swap metrics
            swap = psutil.swap_memory()
            metrics["swap_percent"] = swap.percent
            metrics["swap_used_gb"] = swap.used / (1024**3)
            metrics["swap_total_gb"] = swap.total / (1024**3)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            metrics["disk_percent"] = (disk.used / disk.total) * 100
            metrics["disk_used_gb"] = disk.used / (1024**3)
            metrics["disk_free_gb"] = disk.free / (1024**3)
            metrics["disk_total_gb"] = disk.total / (1024**3)
            
            # Process metrics
            process = psutil.Process()
            metrics["process_cpu_percent"] = process.cpu_percent()
            metrics["process_memory_mb"] = process.memory_info().rss / (1024**2)
            metrics["process_memory_percent"] = process.memory_percent()
            metrics["process_threads"] = process.num_threads()
            
            # System load average (Unix-like systems)
            try:
                metrics["load_average"] = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            except:
                metrics["load_average"] = 0
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            # Fill with default values if collection fails
            metrics = {k: 0.0 for k in [
                "cpu_percent", "memory_percent", "disk_percent", "process_cpu_percent",
                "process_memory_mb", "process_memory_percent"
            ]}
            metrics["cpu_count"] = psutil.cpu_count() if hasattr(psutil, 'cpu_count') else 1
            
            # Ensure all expected memory metrics are present
            try:
                memory = psutil.virtual_memory()
                metrics["memory_used_gb"] = memory.used / (1024**3) if hasattr(memory, 'used') else 0
                metrics["memory_available_gb"] = memory.available / (1024**3) if hasattr(memory, 'available') else 0
                metrics["memory_total_gb"] = memory.total / (1024**3) if hasattr(memory, 'total') else 0
            except:
                metrics["memory_used_gb"] = 0
                metrics["memory_available_gb"] = 0
                metrics["memory_total_gb"] = 0
        
        return metrics
    
    def _calculate_network_delta(self, current_network) -> Dict[str, float]:
        """Calculate network usage delta since last measurement."""
        if self.initial_network is None:
            return {"bytes_sent_per_sec": 0, "bytes_recv_per_sec": 0}
        
        # Calculate deltas
        bytes_sent_delta = current_network.bytes_sent - self.initial_network.bytes_sent
        bytes_recv_delta = current_network.bytes_recv - self.initial_network.bytes_recv
        
        # Convert to per-second rates
        time_delta = self.monitoring_interval
        network_delta = {
            "bytes_sent_per_sec": bytes_sent_delta / time_delta if time_delta > 0 else 0,
            "bytes_recv_per_sec": bytes_recv_delta / time_delta if time_delta > 0 else 0
        }
        
        return network_delta
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistics from collected data."""
        if not self.resource_data:
            return self._get_empty_stats()
        
        # Extract data for statistics
        cpu_values = [m["cpu_percent"] for m in self.resource_data]
        memory_values = [m["memory_percent"] for m in self.resource_data]
        disk_values = [m["disk_percent"] for m in self.resource_data]
        process_cpu_values = [m["process_cpu_percent"] for m in self.resource_data]
        process_memory_values = [m["process_memory_mb"] for m in self.resource_data]
        
        # Peak memory usage
        peak_memory = max(m.get("memory_used_gb", 0) for m in self.resource_data)
        
        # Calculate statistics
        stats = {
            "monitoring_duration": self.resource_data[-1]["elapsed_time"],
            "total_measurements": len(self.resource_data),
            "cpu": {
                "average": sum(cpu_values) / len(cpu_values),
                "peak": max(cpu_values),
                "minimum": min(cpu_values),
                "std_dev": self._calculate_std_dev(cpu_values)
            },
            "memory": {
                "average": sum(memory_values) / len(memory_values),
                "peak": max(memory_values),
                "minimum": min(memory_values),
                "std_dev": self._calculate_std_dev(memory_values),
                "peak_usage_gb": peak_memory
            },
            "disk": {
                "average": sum(disk_values) / len(disk_values),
                "peak": max(disk_values),
                "minimum": min(disk_values),
                "std_dev": self._calculate_std_dev(disk_values)
            },
            "process": {
                "cpu_average": sum(process_cpu_values) / len(process_cpu_values),
                "cpu_peak": max(process_cpu_values),
                "memory_average_mb": sum(process_memory_values) / len(process_memory_values),
                "memory_peak_mb": max(process_memory_values)
            },
            "system_info": {
                "cpu_count": self.resource_data[0]["cpu_count"],
                "total_memory_gb": self.resource_data[0]["memory_total_gb"],
                "total_disk_gb": self.resource_data[0]["disk_total_gb"]
            },
            "detailed_data": self.resource_data
        }
        
        return stats
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation of a list of values."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def _get_empty_stats(self) -> Dict[str, Any]:
        """Return empty statistics when no monitoring data is available."""
        return {
            "monitoring_duration": 0.0,
            "total_measurements": 0,
            "cpu": {"average": 0.0, "peak": 0.0, "minimum": 0.0, "std_dev": 0.0},
            "memory": {"average": 0.0, "peak": 0.0, "minimum": 0.0, "std_dev": 0.0, "peak_usage_gb": 0.0},
            "disk": {"average": 0.0, "peak": 0.0, "minimum": 0.0, "std_dev": 0.0},
            "process": {"cpu_average": 0.0, "cpu_peak": 0.0, "memory_average_mb": 0.0, "memory_peak_mb": 0.0},
            "system_info": {"cpu_count": 1, "total_memory_gb": 0.0, "total_disk_gb": 0.0},
            "detailed_data": []
        }
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time system statistics without stopping monitoring."""
        if not self.monitoring:
            return self._get_empty_stats()
        
        # Collect current metrics
        current_metrics = self._collect_system_metrics()
        current_metrics["timestamp"] = time.time()
        current_metrics["elapsed_time"] = current_metrics["timestamp"] - self.start_time
        
        return current_metrics
    
    def export_data(self, filename: str):
        """Export monitoring data to JSON file."""
        if not self.resource_data:
            logger.warning("No monitoring data to export")
            return
        
        import json
        from datetime import datetime
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "monitoring_duration": self.resource_data[-1]["elapsed_time"],
            "statistics": self._calculate_statistics(),
            "raw_data": self.resource_data
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Monitoring data exported to {filename}")
    
    def reset(self):
        """Reset monitoring data."""
        self.resource_data = []
        self.cpu_data.clear()
        self.memory_data.clear()
        self.disk_data.clear()
        self.network_data.clear()
        self.initial_network = psutil.net_io_counters()
        logger.info("Resource monitoring data reset")