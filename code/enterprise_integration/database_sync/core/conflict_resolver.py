"""
Conflict Resolution

Provides conflict resolution strategies for database synchronization.
"""

import logging
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid


class ConflictType(Enum):
    """Types of data conflicts."""
    VERSION_CONFLICT = "VERSION_CONFLICT"
    TIMESTAMP_CONFLICT = "TIMESTAMP_CONFLICT"
    VALUE_CONFLICT = "VALUE_CONFLICT"
    DELETION_CONFLICT = "DELETION_CONFLICT"
    INSERT_CONFLICT = "INSERT_CONFLICT"
    UPDATE_CONFLICT = "UPDATE_CONFLICT"
    SCHEMA_CONFLICT = "SCHEMA_CONFLICT"


class ConflictStrategy(Enum):
    """Conflict resolution strategies."""
    SOURCE_WINS = "SOURCE_WINS"
    TARGET_WINS = "TARGET_WINS"
    MANUAL_RESOLUTION = "MANUAL_RESOLUTION"
    TIMESTAMP_BASED = "TIMESTAMP_BASED"
    VERSION_BASED = "VERSION_BASED"
    FIELD_LEVEL_RESOLUTION = "FIELD_LEVEL_RESOLUTION"
    MERGE_VALUES = "MERGE_VALUES"
    CUSTOM_LOGIC = "CUSTOM_LOGIC"


@dataclass
class ConflictInfo:
    """Information about a data conflict."""
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conflict_type: ConflictType = ConflictType.VALUE_CONFLICT
    table_name: str = ""
    primary_key: Optional[Dict[str, Any]] = None
    
    # Source and target data
    source_data: Optional[Dict[str, Any]] = None
    target_data: Optional[Dict[str, Any]] = None
    
    # Conflict details
    conflicting_fields: List[str] = field(default_factory=list)
    source_timestamp: Optional[datetime] = None
    target_timestamp: Optional[datetime] = None
    source_version: Optional[int] = None
    target_version: Optional[int] = None
    
    # Resolution information
    strategy: ConflictStrategy = ConflictStrategy.SOURCE_WINS
    resolution_data: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    # Metadata
    detected_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'conflict_id': self.conflict_id,
            'conflict_type': self.conflict_type.value,
            'table_name': self.table_name,
            'primary_key': self.primary_key,
            'source_data': self.source_data,
            'target_data': self.target_data,
            'conflicting_fields': self.conflicting_fields,
            'source_timestamp': self.source_timestamp.isoformat() if self.source_timestamp else None,
            'target_timestamp': self.target_timestamp.isoformat() if self.target_timestamp else None,
            'source_version': self.source_version,
            'target_version': self.target_version,
            'strategy': self.strategy.value,
            'resolution_data': self.resolution_data,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'detected_at': self.detected_at.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class ResolutionResult:
    """Result of conflict resolution."""
    conflict_id: str
    resolved: bool
    strategy: ConflictStrategy
    resolved_data: Dict[str, Any]
    resolution_details: str = ""
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'conflict_id': self.conflict_id,
            'resolved': self.resolved,
            'strategy': self.strategy.value,
            'resolved_data': self.resolved_data,
            'resolution_details': self.resolution_details,
            'error_message': self.error_message
        }


class ConflictResolver:
    """Base conflict resolver with various resolution strategies."""
    
    def __init__(self, 
                 default_strategy: ConflictStrategy = ConflictStrategy.SOURCE_WINS,
                 timestamp_field: str = "updated_at",
                 version_field: str = "version"):
        
        self.default_strategy = default_strategy
        self.timestamp_field = timestamp_field
        self.version_field = version_field
        
        self.custom_resolvers: Dict[str, Callable] = {}
        self.field_resolvers: Dict[str, Callable] = {}
        self.logger = logging.getLogger(__name__)
        
        # Register default resolvers
        self._register_default_resolvers()
    
    def _register_default_resolvers(self):
        """Register default resolution strategies."""
        self.custom_resolvers = {
            ConflictStrategy.SOURCE_WINS.value: self._resolve_source_wins,
            ConflictStrategy.TARGET_WINS.value: self._resolve_target_wins,
            ConflictStrategy.TIMESTAMP_BASED.value: self._resolve_timestamp_based,
            ConflictStrategy.VERSION_BASED.value: self._resolve_version_based,
            ConflictStrategy.MERGE_VALUES.value: self._resolve_merge_values,
            ConflictStrategy.FIELD_LEVEL_RESOLUTION.value: self._resolve_field_level,
            ConflictStrategy.CUSTOM_LOGIC.value: self._resolve_custom_logic
        }
    
    def register_custom_resolver(self, resolver_func: Callable[[ConflictInfo], ResolutionResult]) -> None:
        """Register a custom conflict resolver."""
        self.custom_resolvers[ConflictStrategy.CUSTOM_LOGIC.value] = resolver_func
    
    def register_field_resolver(self, field_name: str, resolver_func: Callable[[Any, Any], Any]) -> None:
        """Register a field-specific resolver."""
        self.field_resolvers[field_name] = resolver_func
    
    async def detect_conflicts(self, 
                             source_data: Dict[str, Any], 
                             target_data: Dict[str, Any],
                             table_name: str,
                             primary_key: Optional[Dict[str, Any]] = None,
                             timestamp_fields: Optional[List[str]] = None,
                             version_fields: Optional[List[str]] = None) -> List[ConflictInfo]:
        """Detect conflicts between source and target data."""
        conflicts = []
        
        timestamp_fields = timestamp_fields or [self.timestamp_field]
        version_fields = version_fields or [self.version_field]
        
        # Check for exact match
        if source_data == target_data:
            return conflicts
        
        # Detect value conflicts
        conflicting_fields = []
        for field_name in source_data.keys() | target_data.keys():
            source_value = source_data.get(field_name)
            target_value = target_data.get(field_name)
            
            if source_value != target_value:
                conflicting_fields.append(field_name)
        
        if conflicting_fields:
            # Determine conflict type
            conflict_type = self._determine_conflict_type(
                source_data, target_data, conflicting_fields, timestamp_fields, version_fields
            )
            
            conflict = ConflictInfo(
                conflict_type=conflict_type,
                table_name=table_name,
                primary_key=primary_key,
                source_data=source_data.copy(),
                target_data=target_data.copy(),
                conflicting_fields=conflicting_fields,
                source_timestamp=source_data.get(self.timestamp_field),
                target_timestamp=target_data.get(self.timestamp_field),
                source_version=source_data.get(self.version_field),
                target_version=target_data.get(self.version_field)
            )
            
            conflicts.append(conflict)
        
        return conflicts
    
    async def resolve_conflict(self, conflict: ConflictInfo) -> ResolutionResult:
        """Resolve a data conflict."""
        try:
            strategy = conflict.strategy or self.default_strategy
            resolver_func = self.custom_resolvers.get(strategy.value)
            
            if not resolver_func:
                self.logger.warning(f"No resolver found for strategy {strategy.value}, using SOURCE_WINS")
                strategy = ConflictStrategy.SOURCE_WINS
                resolver_func = self.custom_resolvers[strategy.value]
            
            result = await resolver_func(conflict)
            self.logger.info(f"Resolved conflict {conflict.conflict_id} using {strategy.value}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to resolve conflict {conflict.conflict_id}: {e}")
            return ResolutionResult(
                conflict_id=conflict.conflict_id,
                resolved=False,
                strategy=conflict.strategy,
                resolved_data={},
                error_message=str(e)
            )
    
    async def resolve_conflicts(self, conflicts: List[ConflictInfo]) -> List[ResolutionResult]:
        """Resolve multiple conflicts."""
        results = []
        for conflict in conflicts:
            result = await self.resolve_conflict(conflict)
            results.append(result)
        return results
    
    def _determine_conflict_type(self, 
                               source_data: Dict[str, Any], 
                               target_data: Dict[str, Any],
                               conflicting_fields: List[str],
                               timestamp_fields: List[str],
                               version_fields: List[str]) -> ConflictType:
        """Determine the type of conflict."""
        # Check for deletion conflicts
        if self._is_deletion_conflict(source_data, target_data):
            return ConflictType.DELETION_CONFLICT
        
        # Check for timestamp conflicts
        has_timestamp_conflict = any(
            source_data.get(field) != target_data.get(field) 
            for field in timestamp_fields if field in conflicting_fields
        )
        if has_timestamp_conflict:
            return ConflictType.TIMESTAMP_CONFLICT
        
        # Check for version conflicts
        has_version_conflict = any(
            source_data.get(field) != target_data.get(field) 
            for field in version_fields if field in conflicting_fields
        )
        if has_version_conflict:
            return ConflictType.VERSION_CONFLICT
        
        return ConflictType.VALUE_CONFLICT
    
    def _is_deletion_conflict(self, source_data: Dict[str, Any], target_data: Dict[str, Any]) -> bool:
        """Check if this is a deletion conflict."""
        # If source has data but target doesn't, or vice versa
        source_has_data = bool(source_data)
        target_has_data = bool(target_data)
        
        return source_has_data != target_has_data
    
    async def _resolve_source_wins(self, conflict: ConflictInfo) -> ResolutionResult:
        """Resolve by taking source data."""
        return ResolutionResult(
            conflict_id=conflict.conflict_id,
            resolved=True,
            strategy=ConflictStrategy.SOURCE_WINS,
            resolved_data=conflict.source_data.copy(),
            resolution_details="Source data wins"
        )
    
    async def _resolve_target_wins(self, conflict: ConflictInfo) -> ResolutionResult:
        """Resolve by taking target data."""
        return ResolutionResult(
            conflict_id=conflict.conflict_id,
            resolved=True,
            strategy=ConflictStrategy.TARGET_WINS,
            resolved_data=conflict.target_data.copy(),
            resolution_details="Target data wins"
        )
    
    async def _resolve_timestamp_based(self, conflict: ConflictInfo) -> ResolutionResult:
        """Resolve based on timestamps."""
        source_timestamp = conflict.source_timestamp
        target_timestamp = conflict.target_timestamp
        
        if not source_timestamp and not target_timestamp:
            # No timestamps, use source as default
            return await self._resolve_source_wins(conflict)
        elif not source_timestamp:
            return await self._resolve_target_wins(conflict)
        elif not target_timestamp:
            return await self._resolve_source_wins(conflict)
        elif source_timestamp > target_timestamp:
            return await self._resolve_source_wins(conflict)
        else:
            return await self._resolve_target_wins(conflict)
    
    async def _resolve_version_based(self, conflict: ConflictInfo) -> ResolutionResult:
        """Resolve based on version numbers."""
        source_version = conflict.source_version
        target_version = conflict.target_version
        
        if not source_version and not target_version:
            return await self._resolve_source_wins(conflict)
        elif not source_version:
            return await self._resolve_target_wins(conflict)
        elif not target_version:
            return await self._resolve_source_wins(conflict)
        elif source_version > target_version:
            return await self._resolve_source_wins(conflict)
        else:
            return await self._resolve_target_wins(conflict)
    
    async def _resolve_merge_values(self, conflict: ConflictInfo) -> ResolutionResult:
        """Merge values from source and target."""
        merged_data = conflict.target_data.copy()
        
        for field in conflict.conflicting_fields:
            source_value = conflict.source_data.get(field)
            target_value = conflict.target_data.get(field)
            
            merged_value = await self._merge_field_values(field, source_value, target_value)
            merged_data[field] = merged_value
        
        return ResolutionResult(
            conflict_id=conflict.conflict_id,
            resolved=True,
            strategy=ConflictStrategy.MERGE_VALUES,
            resolved_data=merged_data,
            resolution_details="Values merged from source and target"
        )
    
    async def _resolve_field_level(self, conflict: ConflictInfo) -> ResolutionResult:
        """Resolve conflicts at field level."""
        resolved_data = conflict.target_data.copy()
        
        for field in conflict.conflicting_fields:
            source_value = conflict.source_data.get(field)
            target_value = conflict.target_data.get(field)
            
            # Check for field-specific resolver
            if field in self.field_resolvers:
                resolved_value = await self.field_resolvers[field](source_value, target_value)
            else:
                # Use timestamp-based as default for fields
                resolved_value = await self._resolve_field_timestamp_based(field, source_value, target_value)
            
            resolved_data[field] = resolved_value
        
        return ResolutionResult(
            conflict_id=conflict.conflict_id,
            resolved=True,
            strategy=ConflictStrategy.FIELD_LEVEL_RESOLUTION,
            resolved_data=resolved_data,
            resolution_details="Field-level resolution applied"
        )
    
    async def _resolve_custom_logic(self, conflict: ConflictInfo) -> ResolutionResult:
        """Resolve using custom logic."""
        if ConflictStrategy.CUSTOM_LOGIC.value not in self.custom_resolvers:
            return await self._resolve_source_wins(conflict)
        
        resolver_func = self.custom_resolvers[ConflictStrategy.CUSTOM_LOGIC.value]
        return await resolver_func(conflict)
    
    async def _merge_field_values(self, field_name: str, source_value: Any, target_value: Any) -> Any:
        """Merge values for a specific field."""
        # Simple merge strategy - could be customized based on field type
        if isinstance(source_value, (int, float)) and isinstance(target_value, (int, float)):
            return max(source_value, target_value)
        elif isinstance(source_value, str) and isinstance(target_value, str):
            # For strings, prefer the longer one (often contains more information)
            return source_value if len(source_value) >= len(target_value) else target_value
        else:
            # Default to source value
            return source_value
    
    async def _resolve_field_timestamp_based(self, field_name: str, source_value: Any, target_value: Any) -> Any:
        """Resolve field based on timestamps (placeholder implementation)."""
        # This would need more context about field timestamps
        return source_value  # Default to source
    
    def create_manual_resolution(self, 
                               conflict: ConflictInfo,
                               resolved_data: Dict[str, Any],
                               resolved_by: str,
                               details: str = "") -> ResolutionResult:
        """Create a manual resolution result."""
        conflict.resolved = True
        conflict.resolved_at = datetime.now()
        conflict.resolved_by = resolved_by
        conflict.resolution_data = resolved_data
        
        return ResolutionResult(
            conflict_id=conflict.conflict_id,
            resolved=True,
            strategy=ConflictStrategy.MANUAL_RESOLUTION,
            resolved_data=resolved_data,
            resolution_details=details or f"Manually resolved by {resolved_by}"
        )


class AdvancedConflictResolver(ConflictResolver):
    """Advanced conflict resolver with additional features."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conflict_history: List[ConflictInfo] = []
        self.learning_enabled = True
    
    async def detect_and_resolve_conflicts(self, 
                                         source_data: Dict[str, Any], 
                                         target_data: Dict[str, Any],
                                         table_name: str,
                                         primary_key: Optional[Dict[str, Any]] = None) -> List[ResolutionResult]:
        """Detect and resolve conflicts in one step."""
        conflicts = await self.detect_conflicts(source_data, target_data, table_name, primary_key)
        
        if not conflicts:
            return []
        
        # Use learning to improve future resolutions
        if self.learning_enabled:
            await self._learn_from_conflicts(conflicts)
        
        return await self.resolve_conflicts(conflicts)
    
    async def _learn_from_conflicts(self, conflicts: List[ConflictInfo]) -> None:
        """Learn from conflict patterns to improve future resolutions."""
        # Analyze conflicts and adjust strategies
        for conflict in conflicts:
            self.conflict_history.append(conflict)
        
        # Keep only recent conflicts for learning
        if len(self.conflict_history) > 1000:
            self.conflict_history = self.conflict_history[-500:]
    
    def get_conflict_statistics(self) -> Dict[str, Any]:
        """Get statistics about conflicts."""
        if not self.conflict_history:
            return {'total_conflicts': 0}
        
        conflict_types = {}
        strategies_used = {}
        resolution_times = []
        
        for conflict in self.conflict_history:
            conflict_type = conflict.conflict_type.value
            conflict_types[conflict_type] = conflict_types.get(conflict_type, 0) + 1
            
            strategy = conflict.strategy.value
            strategies_used[strategy] = strategies_used.get(strategy, 0) + 1
            
            if conflict.resolved_at:
                resolution_time = (conflict.resolved_at - conflict.detected_at).total_seconds()
                resolution_times.append(resolution_time)
        
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        
        return {
            'total_conflicts': len(self.conflict_history),
            'conflict_types': conflict_types,
            'strategies_used': strategies_used,
            'average_resolution_time_seconds': avg_resolution_time,
            'most_common_conflict_type': max(conflict_types.items(), key=lambda x: x[1])[0] if conflict_types else None,
            'most_used_strategy': max(strategies_used.items(), key=lambda x: x[1])[0] if strategies_used else None
        }


class DatabaseSpecificResolver(ConflictResolver):
    """Database-specific conflict resolver."""
    
    def __init__(self, database_type: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.database_type = database_type.lower()
        self._configure_database_specific_resolvers()
    
    def _configure_database_specific_resolvers(self):
        """Configure resolvers specific to the database type."""
        if self.database_type == 'postgresql':
            self._configure_postgresql_resolvers()
        elif self.database_type == 'mongodb':
            self._configure_mongodb_resolvers()
        elif self.database_type == 'mysql':
            self._configure_mysql_resolvers()
    
    def _configure_postgresql_resolvers(self):
        """Configure PostgreSQL-specific resolvers."""
        # PostgreSQL-specific conflict resolution logic
        pass
    
    def _configure_mongodb_resolvers(self):
        """Configure MongoDB-specific resolvers."""
        # MongoDB-specific conflict resolution logic
        self.version_field = "_version"  # MongoDB often uses _version
        self.timestamp_field = "_updated_at"  # MongoDB often uses _updated_at
    
    def _configure_mysql_resolvers(self):
        """Configure MySQL-specific resolvers."""
        # MySQL-specific conflict resolution logic
        pass


class BatchConflictResolver:
    """Resolver for handling conflicts in batches."""
    
    def __init__(self, base_resolver: ConflictResolver):
        self.base_resolver = base_resolver
        self.logger = logging.getLogger(__name__)
    
    async def resolve_batch(self, 
                          data_pairs: List[tuple],
                          table_name: str,
                          primary_keys: Optional[List[Dict[str, Any]]] = None) -> List[ResolutionResult]:
        """Resolve conflicts in a batch."""
        results = []
        
        for i, (source_data, target_data) in enumerate(data_pairs):
            primary_key = primary_keys[i] if primary_keys and i < len(primary_keys) else None
            
            try:
                resolution_results = await self.base_resolver.detect_and_resolve_conflicts(
                    source_data, target_data, table_name, primary_key
                )
                results.extend(resolution_results)
            except Exception as e:
                self.logger.error(f"Failed to resolve conflict in batch: {e}")
                # Add failure result
                results.append(ResolutionResult(
                    conflict_id=f"batch_error_{i}",
                    resolved=False,
                    strategy=self.base_resolver.default_strategy,
                    resolved_data={},
                    error_message=str(e)
                ))
        
        return results
