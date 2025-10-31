#!/usr/bin/env python3
"""
Monitoring Integration Example
Demonstrates how to integrate the monitoring system with automation applications
"""

import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor


class MonitoringClient:
    """Client for integrating with the monitoring system"""
    
    def __init__(self, database_url: str):
        """Initialize the monitoring client with database connection"""
        self.conn = psycopg2.connect(database_url)
        self.conn.autocommit = True
    
    def start_task(self, task_type: str, input_size: Optional[int] = None, 
                   worker_id: Optional[str] = None, batch_id: Optional[str] = None,
                   metadata: Optional[Dict] = None) -> str:
        """Start tracking a new task"""
        task_id = str(uuid.uuid4())
        
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT start_task_tracking(
                    %s, %s, %s, %s, %s, %s, %s
                )
            """, (task_id, task_type, input_size, 0, worker_id, batch_id, 
                  json.dumps(metadata) if metadata else None))
        
        print(f"Started tracking task: {task_id}")
        return task_id
    
    def complete_task(self, task_id: str, status: str, 
                     output_size: Optional[int] = None,
                     processing_steps: Optional[Dict] = None,
                     resource_usage: Optional[Dict] = None):
        """Complete task tracking"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT complete_task_tracking(
                    %s, %s, %s, %s, %s
                )
            """, (task_id, status, output_size, 
                  json.dumps(processing_steps) if processing_steps else None,
                  json.dumps(resource_usage) if resource_usage else None))
        
        print(f"Completed task: {task_id} with status: {status}")
    
    def record_error(self, task_id: Optional[str], error_type: str,
                    error_category: str, error_message: str,
                    component: str, user_impact: str = 'minor',
                    error_details: Optional[Dict] = None) -> str:
        """Record an error in the monitoring system"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT record_error(
                    %s, %s, %s, %s, %s, %s, %s
                )
            """, (task_id, error_type, error_category, error_message,
                  component, json.dumps(error_details) if error_details else None,
                  user_impact))
            error_id = cur.fetchone()[0]
        
        print(f"Recorded error: {error_id}")
        return error_id
    
    def update_system_health(self, component: str, service_name: str,
                           health_status: str, response_time_ms: Optional[int] = None,
                           failure_reason: Optional[str] = None):
        """Update system health status"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT update_system_health(
                    %s, %s, NULL, %s, %s, NULL, %s
                )
            """, (component, service_name, health_status, response_time_ms, failure_reason))
    
    def record_performance_metric(self, metric_name: str, metric_type: str,
                                metric_value: float, metric_unit: str,
                                component: str, tags: Optional[Dict] = None):
        """Record a performance metric"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT record_performance_metrics(
                    %s, %s, %s, %s, %s, NULL, %s
                )
            """, (metric_name, metric_type, metric_value, metric_unit, component,
                  json.dumps(tags) if tags else None))
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary data"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT get_dashboard_summary()")
            return cur.fetchone()[0]
    
    def run_health_checks(self):
        """Run automated health checks"""
        try:
            # Check database connection
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
                self.update_system_health('database', 'postgres', 'healthy', 10)
        except Exception as e:
            self.update_system_health('database', 'postgres', 'unhealthy', 
                                    failure_reason=str(e))
            self.record_error(None, 'connection_error', 'critical',
                            f'Database connection failed: {str(e)}',
                            'database', 'critical')
        
        # Add other health checks as needed
        self.update_system_health('api', 'main_api', 'healthy', 50)
    
    def run_alert_checks(self):
        """Run automated alert checks"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT check_error_rate_alerts()")
            cur.execute("SELECT check_processing_performance_alerts()")
            cur.execute("SELECT check_system_health_alerts()")
            cur.execute("SELECT check_queue_backlog_alerts()")
            cur.execute("SELECT resolve_resolved_alerts()")
    
    def cleanup_old_data(self):
        """Clean up old monitoring data"""
        with self.conn.cursor() as cur:
            cur.execute("SELECT cleanup_old_monitoring_data()")
    
    def close(self):
        """Close database connection"""
        self.conn.close()


class TaskProcessor:
    """Example task processor using the monitoring system"""
    
    def __init__(self, database_url: str, worker_id: str):
        self.monitor = MonitoringClient(database_url)
        self.worker_id = worker_id
    
    def process_document(self, document_data: Dict) -> Dict:
        """Process a document with monitoring"""
        task_id = None
        try:
            # Start task monitoring
            task_id = self.monitor.start_task(
                task_type='document_processing',
                input_size=len(json.dumps(document_data)),
                worker_id=self.worker_id,
                metadata={'document_type': document_data.get('type')}
            )
            
            # Record processing start time
            start_time = time.time()
            processing_steps = {}
            
            # Simulate processing steps
            time.sleep(1)  # Step 1: Preprocessing
            processing_steps['preprocessing'] = time.time() - start_time
            
            time.sleep(2)  # Step 2: Analysis
            processing_steps['analysis'] = time.time() - start_time
            
            time.sleep(1)  # Step 3: Post-processing
            processing_steps['postprocessing'] = time.time() - start_time
            
            # Complete task successfully
            self.monitor.complete_task(
                task_id=task_id,
                status='completed',
                output_size=1024,  # Example output size
                processing_steps=processing_steps,
                resource_usage={
                    'cpu_percent': 45.2,
                    'memory_mb': 128.5,
                    'disk_io_mb': 12.3
                }
            )
            
            return {'status': 'success', 'task_id': task_id}
            
        except Exception as e:
            # Record error and fail task
            if task_id:
                self.monitor.complete_task(task_id, 'failed')
            
            error_id = self.monitor.record_error(
                task_id=task_id,
                error_type='processing_error',
                error_category='medium',
                error_message=f'Document processing failed: {str(e)}',
                component='processor',
                user_impact='minor',
                error_details={
                    'document_type': document_data.get('type'),
                    'worker_id': self.worker_id,
                    'stack_trace': str(e)
                }
            )
            
            return {'status': 'error', 'error_id': error_id, 'message': str(e)}


def main():
    """Main function demonstrating monitoring usage"""
    # Database connection (replace with your actual connection string)
    database_url = "postgresql://user:password@localhost:5432/automation_db"
    
    # Initialize monitoring client
    monitor = MonitoringClient(database_url)
    
    # Example: Run health checks
    print("Running health checks...")
    monitor.run_health_checks()
    
    # Example: Get dashboard summary
    summary = monitor.get_dashboard_summary()
    print(f"Dashboard Summary: {json.dumps(summary, indent=2)}")
    
    # Example: Record performance metrics
    monitor.record_performance_metric(
        metric_name='cpu_usage',
        metric_type='cpu',
        metric_value=45.2,
        metric_unit='%',
        component='system',
        tags={'host': 'server-01', 'core': 'all'}
    )
    
    # Example: Task processor
    processor = TaskProcessor(database_url, 'worker-001')
    result = processor.process_document({'type': 'pdf', 'size': 1024})
    print(f"Processing result: {result}")
    
    # Run alert checks
    print("Running alert checks...")
    monitor.run_alert_checks()
    
    # Clean up
    monitor.close()
    print("Monitoring integration demo complete!")


if __name__ == '__main__':
    main()