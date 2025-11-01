"""
Change Event Representation

Defines the structure of change events for database synchronization.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime
import uuid


class ChangeType(Enum):
    """Types of change events."""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    BULK_INSERT = "BULK_INSERT"
    BULK_UPDATE = "BULK_UPDATE"
    BULK_DELETE = "BULK_DELETE"
    SCHEMA_CHANGE = "SCHEMA_CHANGE"
    TRANSACTION = "TRANSACTION"


class EventStatus(Enum):
    """Status of change events."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    SKIPPED = "SKIPPED"


class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    SOURCE_WINS = "SOURCE_WINS"
    TARGET_WINS = "TARGET_WINS"
    MANUAL_RESOLUTION = "MANUAL_RESOLUTION"
    TIMESTAMP_BASED = "TIMESTAMP_BASED"
    VERSION_BASED = "VERSION_BASED"
    CUSTOM_LOGIC = "CUSTOM_LOGIC"


@dataclass
class ChangeEvent:
    """Represents a database change event."""
    
    # Core event information
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: ChangeType = ChangeType.INSERT
    event_status: EventStatus = EventStatus.PENDING
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Source information
    source_table: str = ""
    source_database: str = ""
    source_schema: str = ""
    
    # Target information
    target_table: str = ""
    target_database: str = ""
    target_schema: str = ""
    
    # Data information
    primary_key: Optional[Dict[str, Any]] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None
    
    # Metadata
    user_id: Optional[str] = None
    application_id: Optional[str] = None
    correlation_id: Optional[str] = None
    transaction_id: Optional[str] = None
    
    # Processing information
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None
    processing_time_ms: Optional[float] = None
    
    # Conflict resolution
    conflict_resolution: ConflictResolution = ConflictResolution.SOURCE_WINS
    conflict_resolved: bool = False
    conflict_resolution_details: Optional[Dict[str, Any]] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the change event after initialization."""
        if not self.source_table and not self.target_table:
            raise ValueError("Either source_table or target_table must be specified")
        
        if self.event_type in [ChangeType.UPDATE, ChangeType.DELETE] and not self.primary_key:
            raise ValueError(f"Primary key is required for {self.event_type} operations")
        
        if self.event_type == ChangeType.INSERT and not self.new_values:
            raise ValueError("New values are required for INSERT operations")
        
        if self.event_type == ChangeType.UPDATE and not (self.old_values or self.new_values):
            raise ValueError("Old or new values are required for UPDATE operations")
    
    def is_conflict(self, other_event: 'ChangeEvent') -> bool:
        """Check if this event conflicts with another event."""
        if self.primary_key != other_event.primary_key:
            return False
        
        if self.source_table != other_event.source_table:
            return False
        
        if self.timestamp == other_event.timestamp:
            return False
        
        return True
    
    def should_merge(self, other_event: 'ChangeEvent') -> bool:
        """Check if this event should be merged with another event."""
        if not self.is_conflict(other_event):
            return False
        
        # Same primary key, same table, but different timestamps
        # Could be a merge scenario
        return True
    
    def merge_with(self, other_event: 'ChangeEvent') -> 'ChangeEvent':
        """Merge this event with another event."""
        if not self.should_merge(other_event):
            raise ValueError("Events cannot be merged")
        
        # Create a new merged event
        merged = ChangeEvent(
            event_type=ChangeType.UPDATE,
            source_table=self.source_table,
            target_table=self.target_table,
            primary_key=self.primary_key,
            old_values=self.old_values or other_event.old_values,
            new_values=self.new_values or other_event.new_values,
            changed_fields=list(set((self.changed_fields or []) + (other_event.changed_fields or []))),
            user_id=self.user_id or other_event.user_id,
            correlation_id=self.correlation_id or other_event.correlation_id,
            transaction_id=self.transaction_id or other_event.transaction_id,
            timestamp=max(self.timestamp, other_event.timestamp)
        )
        
        return merged
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'event_status': self.event_status.value,
            'timestamp': self.timestamp.isoformat(),
            'source_table': self.source_table,
            'source_database': self.source_database,
            'source_schema': self.source_schema,
            'target_table': self.target_table,
            'target_database': self.target_database,
            'target_schema': self.target_schema,
            'primary_key': self.primary_key,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'changed_fields': self.changed_fields,
            'user_id': self.user_id,
            'application_id': self.application_id,
            'correlation_id': self.correlation_id,
            'transaction_id': self.transaction_id,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'error_message': self.error_message,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'processing_time_ms': self.processing_time_ms,
            'conflict_resolution': self.conflict_resolution.value,
            'conflict_resolved': self.conflict_resolved,
            'conflict_resolution_details': self.conflict_resolution_details,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChangeEvent':
        """Create event from dictionary."""
        data['event_type'] = ChangeType(data['event_type'])
        data['event_status'] = EventStatus(data['event_status'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        if data.get('processed_at'):
            data['processed_at'] = datetime.fromisoformat(data['processed_at'])
        
        data['conflict_resolution'] = ConflictResolution(data['conflict_resolution'])
        
        return cls(**data)
    
    def __repr__(self):
        return (f"ChangeEvent(id={self.event_id[:8]}, "
                f"type={self.event_type.value}, "
                f"table={self.source_table or self.target_table}, "
                f"status={self.event_status.value})")


@dataclass
class EventBatch:
    """A batch of change events for efficient processing."""
    
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    events: List[ChangeEvent] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    status: EventStatus = EventStatus.PENDING
    
    # Batch metadata
    source_tables: List[str] = field(default_factory=list)
    target_tables: List[str] = field(default_factory=list)
    event_types: List[ChangeType] = field(default_factory=list)
    
    def add_event(self, event: ChangeEvent) -> None:
        """Add an event to the batch."""
        self.events.append(event)
        
        # Update batch metadata
        if event.source_table and event.source_table not in self.source_tables:
            self.source_tables.append(event.source_table)
        
        if event.target_table and event.target_table not in self.target_tables:
            self.target_tables.append(event.target_table)
        
        if event.event_type not in self.event_types:
            self.event_types.append(event.event_type)
    
    def remove_event(self, event_id: str) -> Optional[ChangeEvent]:
        """Remove an event from the batch."""
        for i, event in enumerate(self.events):
            if event.event_id == event_id:
                return self.events.pop(i)
        return None
    
    def get_events_by_type(self, event_type: ChangeType) -> List[ChangeEvent]:
        """Get events of a specific type."""
        return [event for event in self.events if event.event_type == event_type]
    
    def get_events_by_table(self, table_name: str) -> List[ChangeEvent]:
        """Get events for a specific table."""
        return [event for event in self.events 
                if event.source_table == table_name or event.target_table == table_name]
    
    def get_failed_events(self) -> List[ChangeEvent]:
        """Get events that have failed."""
        return [event for event in self.events if event.event_status == EventStatus.FAILED]
    
    def mark_as_processing(self) -> None:
        """Mark all events in the batch as processing."""
        for event in self.events:
            if event.event_status == EventStatus.PENDING:
                event.event_status = EventStatus.PROCESSING
    
    def mark_as_completed(self) -> None:
        """Mark all events in the batch as completed."""
        for event in self.events:
            if event.event_status in [EventStatus.PROCESSING, EventStatus.RETRYING]:
                event.event_status = EventStatus.COMPLETED
                event.processed_at = datetime.now()
        
        self.processed_at = datetime.now()
        self.status = EventStatus.COMPLETED
    
    def mark_as_failed(self, error_message: str) -> None:
        """Mark all pending events as failed."""
        for event in self.events:
            if event.event_status in [EventStatus.PENDING, EventStatus.PROCESSING]:
                event.event_status = EventStatus.FAILED
                event.error_message = error_message
    
    def __len__(self):
        return len(self.events)
    
    def __repr__(self):
        return f"EventBatch(id={self.batch_id[:8]}, events={len(self.events)}, status={self.status.value})"
