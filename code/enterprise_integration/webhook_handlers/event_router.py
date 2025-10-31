"""
Event Router Module

Handles routing and filtering of webhook events to appropriate handlers
based on event type, source, and custom rules.
"""

import json
import re
import logging
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
import queue


logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EventStatus(Enum):
    """Event processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    FILTERED = "filtered"


@dataclass
class EventFilter:
    """Event filter configuration"""
    field_path: str
    operator: str  # equals, contains, regex, range, in, not_in
    value: Any
    description: str = ""
    
    def matches(self, event_data: Dict[str, Any]) -> bool:
        """
        Check if event matches this filter
        
        Args:
            event_data: Event data to check
            
        Returns:
            True if event matches filter
        """
        try:
            # Extract value using dot notation
            value = self._get_nested_value(event_data, self.field_path)
            
            if value is None:
                return False
            
            # Apply operator
            if self.operator == 'equals':
                return value == self.value
            elif self.operator == 'contains':
                return str(self.value).lower() in str(value).lower()
            elif self.operator == 'regex':
                return bool(re.search(str(self.value), str(value), re.IGNORECASE))
            elif self.operator == 'in':
                return value in self.value if isinstance(self.value, list) else False
            elif self.operator == 'not_in':
                return value not in self.value if isinstance(self.value, list) else True
            elif self.operator == 'range':
                return self.value[0] <= value <= self.value[1]
            elif self.operator == 'greater_than':
                return value > self.value
            elif self.operator == 'less_than':
                return value < self.value
            elif self.operator == 'exists':
                return value is not None
            elif self.operator == 'not_exists':
                return value is None
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating filter: {e}")
            return False
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and key.isdigit():
                index = int(key)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                return None
        
        return current


@dataclass
class EventRoute:
    """Event routing configuration"""
    name: str
    event_types: List[str]
    source_filters: List[str]
    filters: List[EventFilter]
    handler: Callable
    priority: EventPriority = EventPriority.NORMAL
    retry_count: int = 3
    timeout: int = 30
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def should_handle(self, event_type: str, source: str, event_data: Dict[str, Any]) -> bool:
        """
        Check if this route should handle the event
        
        Args:
            event_type: Type of the event
            source: Source of the event
            event_data: Event data
            
        Returns:
            True if route should handle event
        """
        if not self.enabled:
            return False
        
        # Check event type
        if self.event_types and event_type not in self.event_types:
            return False
        
        # Check source filters
        if self.source_filters and source not in self.source_filters:
            return False
        
        # Apply custom filters
        for filter_rule in self.filters:
            if not filter_rule.matches(event_data):
                return False
        
        return True


@dataclass
class ProcessedEvent:
    """Processed event information"""
    id: str
    event_type: str
    source: str
    timestamp: datetime
    data: Dict[str, Any]
    status: EventStatus
    route_name: Optional[str] = None
    handler_result: Any = None
    error_message: Optional[str] = None
    retry_count: int = 0
    processing_time: Optional[float] = None


class EventRouter:
    """
    Routes events to appropriate handlers based on configuration
    """
    
    def __init__(self, max_queue_size: int = 10000):
        """
        Initialize event router
        
        Args:
            max_queue_size: Maximum queue size for async processing
        """
        self.routes: Dict[str, EventRoute] = {}
        self.event_queue = queue.PriorityQueue(maxsize=max_queue_size)
        self.processing_stats = {
            'total_events': 0,
            'processed_events': 0,
            'failed_events': 0,
            'filtered_events': 0,
            'average_processing_time': 0.0
        }
        self._lock = threading.Lock()
        
        # Start worker threads
        self.workers = []
        self._start_workers()
    
    def add_route(self, route: EventRoute) -> None:
        """
        Add event routing rule
        
        Args:
            route: Event route configuration
        """
        with self._lock:
            self.routes[route.name] = route
            logger.info(f"Added route: {route.name}")
    
    def remove_route(self, route_name: str) -> bool:
        """
        Remove event routing rule
        
        Args:
            route_name: Name of route to remove
            
        Returns:
            True if route was removed
        """
        with self._lock:
            if route_name in self.routes:
                del self.routes[route_name]
                logger.info(f"Removed route: {route_name}")
                return True
            return False
    
    def route_event(self, event_data: Dict[str, Any], source: str, 
                   event_type: str, event_id: str, 
                   async_processing: bool = True) -> Optional[ProcessedEvent]:
        """
        Route event to appropriate handler
        
        Args:
            event_data: Event data
            source: Event source
            event_type: Event type
            event_id: Unique event identifier
            async_processing: Whether to process asynchronously
            
        Returns:
            ProcessedEvent if processed synchronously, None if queued
        """
        event = ProcessedEvent(
            id=event_id,
            event_type=event_type,
            source=source,
            timestamp=datetime.utcnow(),
            data=event_data,
            status=EventStatus.PENDING
        )
        
        # Find matching routes
        matching_routes = []
        for route in self.routes.values():
            if route.should_handle(event_type, source, event_data):
                matching_routes.append(route)
        
        if not matching_routes:
            with self._lock:
                self.processing_stats['filtered_events'] += 1
            event.status = EventStatus.FILTERED
            logger.info(f"Event {event_id} filtered out - no matching routes")
            return event
        
        # Sort routes by priority (higher priority first)
        matching_routes.sort(key=lambda r: r.priority.value, reverse=True)
        
        # Process with highest priority route
        primary_route = matching_routes[0]
        event.route_name = primary_route.name
        
        if async_processing:
            # Add to queue for async processing
            try:
                priority = (5 - primary_route.priority.value, datetime.utcnow().timestamp())
                self.event_queue.put((priority, event, primary_route))
                logger.debug(f"Event {event_id} queued for route {primary_route.name}")
            except queue.Full:
                event.status = EventStatus.FAILED
                event.error_message = "Queue full"
                with self._lock:
                    self.processing_stats['failed_events'] += 1
                logger.error(f"Event {event_id} failed - queue full")
        else:
            # Process synchronously
            self._process_event(event, primary_route)
        
        with self._lock:
            self.processing_stats['total_events'] += 1
        
        return event
    
    def _process_event(self, event: ProcessedEvent, route: EventRoute) -> None:
        """
        Process event with specified route
        
        Args:
            event: Event to process
            route: Route to use for processing
        """
        start_time = datetime.utcnow()
        
        try:
            event.status = EventStatus.PROCESSING
            
            # Execute handler
            result = route.handler(event.data)
            
            # Update event with results
            event.handler_result = result
            event.status = EventStatus.COMPLETED
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            event.processing_time = processing_time
            
            # Update statistics
            with self._lock:
                self.processing_stats['processed_events'] += 1
                self._update_average_processing_time(processing_time)
            
            logger.info(f"Event {event.id} processed successfully by route {route.name}")
            
        except Exception as e:
            # Handle errors
            event.status = EventStatus.FAILED
            event.error_message = str(e)
            
            with self._lock:
                self.processing_stats['failed_events'] += 1
            
            logger.error(f"Event {event.id} failed processing by route {route.name}: {e}")
            
            # Retry logic
            if event.retry_count < route.retry_count:
                event.retry_count += 1
                event.status = EventStatus.RETRY
                
                # Schedule retry
                retry_delay = min(2 ** event.retry_count, 300)  # Exponential backoff, max 5 minutes
                retry_time = datetime.utcnow() + timedelta(seconds=retry_delay)
                
                logger.info(f"Event {event.id} scheduled for retry #{event.retry_count} at {retry_time}")
                
                # Add back to queue with lower priority
                priority = (10, retry_time.timestamp())
                try:
                    self.event_queue.put((priority, event, route))
                except queue.Full:
                    logger.error(f"Event {event.id} retry failed - queue full")
    
    def _update_average_processing_time(self, processing_time: float) -> None:
        """Update average processing time statistic"""
        current_avg = self.processing_stats['average_processing_time']
        processed_count = self.processing_stats['processed_events']
        
        if processed_count == 1:
            self.processing_stats['average_processing_time'] = processing_time
        else:
            # Calculate new average
            total_time = current_avg * (processed_count - 1) + processing_time
            self.processing_stats['average_processing_time'] = total_time / processed_count
    
    def _start_workers(self, num_workers: int = 3) -> None:
        """
        Start worker threads for async processing
        
        Args:
            num_workers: Number of worker threads
        """
        for i in range(num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(f"worker-{i}",),
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
            logger.info(f"Started worker thread: worker-{i}")
    
    def _worker_loop(self, worker_id: str) -> None:
        """
        Worker thread main loop
        
        Args:
            worker_id: Worker thread identifier
        """
        while True:
            try:
                # Get event from queue
                priority, event, route = self.event_queue.get(timeout=1)
                
                # Check if event is ready for processing (for retries)
                if isinstance(priority, tuple) and len(priority) == 2:
                    priority_score, timestamp = priority
                    if datetime.utcnow().timestamp() < timestamp:
                        # Not ready yet, put back
                        self.event_queue.put((priority, event, route))
                        continue
                
                logger.debug(f"Worker {worker_id} processing event {event.id}")
                self._process_event(event, route)
                
                # Mark task as done
                self.event_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get routing statistics
        
        Returns:
            Dictionary with routing statistics
        """
        with self._lock:
            queue_size = self.event_queue.qsize()
            return {
                **self.processing_stats,
                'queue_size': queue_size,
                'active_routes': len([r for r in self.routes.values() if r.enabled]),
                'total_routes': len(self.routes)
            }
    
    def get_routes(self) -> Dict[str, EventRoute]:
        """
        Get all configured routes
        
        Returns:
            Dictionary of route name to EventRoute
        """
        with self._lock:
            return self.routes.copy()
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.event_queue.qsize()
    
    def is_healthy(self) -> bool:
        """
        Check if router is healthy
        
        Returns:
            True if router is functioning properly
        """
        return all(worker.is_alive() for worker in self.workers) and self.event_queue.qsize() < self.event_queue.maxsize * 0.9
    
    def shutdown(self, timeout: int = 30) -> None:
        """
        Shutdown router and worker threads
        
        Args:
            timeout: Shutdown timeout in seconds
        """
        logger.info("Shutting down event router...")
        
        # Wait for queue to empty
        try:
            self.event_queue.join()
        except KeyboardInterrupt:
            pass
        
        logger.info("Event router shutdown complete")


def create_default_routes(router: EventRouter) -> None:
    """
    Create common webhook routes
    
    Args:
        router: EventRouter instance
    """
    
    # Stripe webhook route
    def handle_stripe_payment(event_data):
        """Handle Stripe payment events"""
        if event_data.get('type') == 'payment_intent.succeeded':
            # Process successful payment
            logger.info(f"Processing Stripe payment: {event_data['data']['object']['id']}")
            return {"status": "processed", "amount": event_data['data']['object']['amount']}
        return {"status": "ignored"}
    
    router.add_route(EventRoute(
        name="stripe_payments",
        event_types=["payment_intent.succeeded", "charge.succeeded"],
        source_filters=["stripe"],
        filters=[
            EventFilter("data.object.status", "equals", "succeeded", "Payment succeeded")
        ],
        handler=handle_stripe_payment,
        priority=EventPriority.HIGH
    ))
    
    # GitHub webhook route
    def handle_github_push(event_data):
        """Handle GitHub push events"""
        logger.info(f"Processing GitHub push: {event_data['repository']['name']}")
        return {"status": "processed", "commits": len(event_data.get('commits', []))}
    
    router.add_route(EventRoute(
        name="github_push",
        event_types=["push"],
        source_filters=["github"],
        filters=[
            EventFilter("ref", "regex", r"refs/heads/", "Branch push")
        ],
        handler=handle_github_push,
        priority=EventPriority.NORMAL
    ))
    
    # Generic webhook route
    def handle_generic_event(event_data):
        """Handle generic webhook events"""
        logger.info(f"Processing generic event: {event_data.get('type', 'unknown')}")
        return {"status": "processed"}
    
    router.add_route(EventRoute(
        name="generic_webhook",
        event_types=["*"],  # Match all events
        source_filters=["*"],  # Match all sources
        filters=[],  # No filters
        handler=handle_generic_event,
        priority=EventPriority.LOW
    ))
