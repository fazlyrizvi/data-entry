"""
Data Transformation Pipelines

Provides data transformation capabilities for database synchronization.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid
import json
import re
from abc import ABC, abstractmethod

from ..core.change_event import ChangeEvent, EventBatch


class TransformationType(Enum):
    """Types of data transformations."""
    FIELD_MAPPING = "FIELD_MAPPING"
    TYPE_CONVERSION = "TYPE_CONVERSION"
    VALUE_MODIFICATION = "VALUE_MODIFICATION"
    DATA_ENRICHMENT = "DATA_ENRICHMENT"
    VALIDATION = "VALIDATION"
    FILTERING = "FILTERING"
    AGGREGATION = "AGGREGATION"
    CUSTOM = "CUSTOM"


class PipelineStatus(Enum):
    """Transformation pipeline status."""
    IDLE = "IDLE"
    PROCESSING = "PROCESSING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    COMPLETED = "COMPLETED"


@dataclass
class TransformationRule:
    """Rule for data transformation."""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    transformation_type: TransformationType = TransformationType.CUSTOM
    enabled: bool = True
    priority: int = 0
    
    # Rule configuration
    source_fields: List[str] = field(default_factory=list)
    target_fields: List[str] = field(default_factory=list)
    condition: Optional[Callable] = None
    transformation_func: Optional[Callable] = None
    
    # Validation rules
    validation_rules: List[Callable] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'transformation_type': self.transformation_type.value,
            'enabled': self.enabled,
            'priority': self.priority,
            'source_fields': self.source_fields,
            'target_fields': self.target_fields,
            'condition': str(self.condition) if self.condition else None,
            'transformation_func': str(self.transformation_func) if self.transformation_func else None,
            'validation_rules': [str(rule) for rule in self.validation_rules],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class TransformationResult:
    """Result of a transformation."""
    success: bool
    original_data: Dict[str, Any]
    transformed_data: Dict[str, Any]
    applied_rules: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'original_data': self.original_data,
            'transformed_data': self.transformed_data,
            'applied_rules': self.applied_rules,
            'errors': self.errors,
            'warnings': self.warnings
        }


@dataclass
class PipelineStatistics:
    """Statistics for transformation pipeline."""
    pipeline_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Processing statistics
    total_records_processed: int = 0
    records_transformed: int = 0
    records_filtered: int = 0
    records_failed: int = 0
    
    # Rule statistics
    rules_executed: int = 0
    rules_failed: int = 0
    
    # Performance statistics
    average_processing_time_ms: float = 0.0
    throughput_records_per_second: float = 0.0
    
    # Status
    status: PipelineStatus = PipelineStatus.PROCESSING
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pipeline_id': self.pipeline_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_records_processed': self.total_records_processed,
            'records_transformed': self.records_transformed,
            'records_filtered': self.records_filtered,
            'records_failed': self.records_failed,
            'rules_executed': self.rules_executed,
            'rules_failed': self.rules_failed,
            'average_processing_time_ms': self.average_processing_time_ms,
            'throughput_records_per_second': self.throughput_records_per_second,
            'status': self.status.value
        }


class BaseTransformation(ABC):
    """Abstract base class for transformations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def transform(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Transform data."""
        pass
    
    @abstractmethod
    async def validate(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Validate data."""
        pass


class FieldMappingTransformation(BaseTransformation):
    """Field mapping transformation."""
    
    async def transform(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Transform data using field mappings."""
        mappings = self.config.get('field_mappings', {})
        transformed_data = {}
        
        for source_field, target_field in mappings.items():
            if source_field in data:
                transformed_data[target_field] = data[source_field]
            elif target_field in self.config.get('default_values', {}):
                transformed_data[target_field] = self.config['default_values'][target_field]
        
        # Include unmapped fields if configured
        if self.config.get('include_unmapped', True):
            for field_name, value in data.items():
                if field_name not in mappings:
                    transformed_data[field_name] = value
        
        return transformed_data
    
    async def validate(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Validate field mapping."""
        mappings = self.config.get('field_mappings', {})
        errors = []
        
        for source_field in mappings.keys():
            if source_field not in data and source_field not in self.config.get('optional_fields', []):
                errors.append(f"Required field '{source_field}' is missing")
        
        return errors


class TypeConversionTransformation(BaseTransformation):
    """Type conversion transformation."""
    
    async def transform(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Transform data using type conversions."""
        type_conversions = self.config.get('type_conversions', {})
        transformed_data = {}
        
        for field_name, value in data.items():
            if field_name in type_conversions:
                target_type = type_conversions[field_name]
                try:
                    transformed_data[field_name] = self._convert_type(value, target_type)
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Type conversion failed for {field_name}: {e}")
                    transformed_data[field_name] = value  # Keep original value
            else:
                transformed_data[field_name] = value
        
        return transformed_data
    
    def _convert_type(self, value: Any, target_type: str) -> Any:
        """Convert value to target type."""
        if target_type == 'string':
            return str(value)
        elif target_type == 'integer':
            return int(value)
        elif target_type == 'float':
            return float(value)
        elif target_type == 'boolean':
            return bool(value)
        elif target_type == 'datetime':
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            elif isinstance(value, (int, float)):
                return datetime.fromtimestamp(value, tz=timezone.utc)
            else:
                return value
        elif target_type == 'json':
            if isinstance(value, str):
                return json.loads(value)
            else:
                return value
        else:
            return value
    
    async def validate(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Validate type conversions."""
        type_conversions = self.config.get('type_conversions', {})
        errors = []
        
        for field_name, target_type in type_conversions.items():
            if field_name in data:
                value = data[field_name]
                try:
                    self._convert_type(value, target_type)
                except (ValueError, TypeError) as e:
                    errors.append(f"Cannot convert {field_name} to {target_type}: {e}")
        
        return errors


class ValueModificationTransformation(BaseTransformation):
    """Value modification transformation."""
    
    async def transform(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Transform data using value modifications."""
        modifications = self.config.get('modifications', {})
        transformed_data = data.copy()
        
        for field_name, modification_config in modifications.items():
            if field_name in transformed_data:
                value = transformed_data[field_name]
                modified_value = await self._apply_modification(value, modification_config)
                transformed_data[field_name] = modified_value
        
        return transformed_data
    
    async def _apply_modification(self, value: Any, config: Dict[str, Any]) -> Any:
        """Apply a single modification."""
        modification_type = config.get('type')
        
        if modification_type == 'string_operations':
            operations = config.get('operations', [])
            for operation in operations:
                if operation == 'uppercase':
                    value = str(value).upper()
                elif operation == 'lowercase':
                    value = str(value).lower()
                elif operation == 'strip':
                    value = str(value).strip()
                elif operation == 'title_case':
                    value = str(value).title()
        
        elif modification_type == 'numeric_operations':
            operations = config.get('operations', [])
            for operation in operations:
                if operation == 'round':
                    value = round(float(value))
                elif operation == 'floor':
                    value = int(float(value))
                elif operation == 'abs':
                    value = abs(float(value))
        
        elif modification_type == 'regex_replace':
            pattern = config.get('pattern')
            replacement = config.get('replacement', '')
            if pattern:
                value = re.sub(pattern, replacement, str(value))
        
        elif modification_type == 'format_string':
            template = config.get('template')
            if template:
                value = template.format(value=value, **config.get('variables', {}))
        
        return value
    
    async def validate(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Validate value modifications."""
        # Basic validation - could be extended
        return []


class DataEnrichmentTransformation(BaseTransformation):
    """Data enrichment transformation."""
    
    async def transform(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Enrich data with additional information."""
        enrichment_config = self.config.get('enrichment', {})
        transformed_data = data.copy()
        
        # Add calculated fields
        calculated_fields = enrichment_config.get('calculated_fields', {})
        for field_name, calculation_config in calculated_fields.items():
            try:
                value = await self._calculate_field_value(data, calculation_config)
                transformed_data[field_name] = value
            except Exception as e:
                self.logger.warning(f"Failed to calculate field {field_name}: {e}")
        
        # Add lookup fields
        lookup_fields = enrichment_config.get('lookup_fields', {})
        for field_name, lookup_config in lookup_fields.items():
            try:
                value = await self._lookup_field_value(data, lookup_config)
                transformed_data[field_name] = value
            except Exception as e:
                self.logger.warning(f"Failed to lookup field {field_name}: {e}")
        
        # Add timestamp information
        if enrichment_config.get('add_timestamps', False):
            transformed_data['created_at'] = datetime.now(timezone.utc)
            transformed_data['updated_at'] = datetime.now(timezone.utc)
        
        return transformed_data
    
    async def _calculate_field_value(self, data: Dict[str, Any], config: Dict[str, Any]) -> Any:
        """Calculate field value based on configuration."""
        calculation_type = config.get('type')
        
        if calculation_type == 'concatenate':
            fields = config.get('fields', [])
            separator = config.get('separator', ' ')
            values = [str(data.get(field, '')) for field in fields]
            return separator.join(values)
        
        elif calculation_type == 'sum':
            fields = config.get('fields', [])
            return sum(float(data.get(field, 0)) for field in fields)
        
        elif calculation_type == 'count':
            fields = config.get('fields', [])
            return len([field for field in fields if data.get(field) is not None])
        
        elif calculation_type == 'format_date':
            source_field = config.get('source_field')
            format_string = config.get('format', '%Y-%m-%d')
            if source_field in data:
                date_value = data[source_field]
                if isinstance(date_value, str):
                    date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return date_value.strftime(format_string)
        
        return None
    
    async def _lookup_field_value(self, data: Dict[str, Any], config: Dict[str, Any]) -> Any:
        """Lookup field value from external source."""
        # This would implement lookup from external sources
        # For now, return None as placeholder
        return None
    
    async def validate(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Validate data enrichment."""
        errors = []
        
        # Check if required source fields exist
        enrichment_config = self.config.get('enrichment', {})
        calculated_fields = enrichment_config.get('calculated_fields', {})
        
        for field_name, calc_config in calculated_fields.items():
            calculation_type = calc_config.get('type')
            if calculation_type in ['concatenate', 'sum', 'count']:
                source_fields = calc_config.get('fields', [])
                for source_field in source_fields:
                    if source_field not in data:
                        errors.append(f"Required field '{source_field}' for calculation missing")
        
        return errors


class ValidationTransformation(BaseTransformation):
    """Data validation transformation."""
    
    async def transform(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate data (pass-through transformation)."""
        return data
    
    async def validate(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Validate data against rules."""
        validation_rules = self.config.get('validation_rules', {})
        errors = []
        
        # Field existence validation
        required_fields = validation_rules.get('required_fields', [])
        for field_name in required_fields:
            if field_name not in data or data[field_name] is None:
                errors.append(f"Required field '{field_name}' is missing or null")
        
        # Field format validation
        format_rules = validation_rules.get('format_rules', {})
        for field_name, pattern in format_rules.items():
            if field_name in data and data[field_name]:
                if not re.match(pattern, str(data[field_name])):
                    errors.append(f"Field '{field_name}' does not match required format")
        
        # Range validation
        range_rules = validation_rules.get('range_rules', {})
        for field_name, range_config in range_rules.items():
            if field_name in data and data[field_name] is not None:
                value = float(data[field_name])
                min_value = range_config.get('min')
                max_value = range_config.get('max')
                
                if min_value is not None and value < min_value:
                    errors.append(f"Field '{field_name}' value {value} is below minimum {min_value}")
                
                if max_value is not None and value > max_value:
                    errors.append(f"Field '{field_name}' value {value} is above maximum {max_value}")
        
        # Custom validation functions
        custom_validations = validation_rules.get('custom_validations', [])
        for validation_func in custom_validations:
            try:
                if asyncio.iscoroutinefunction(validation_func):
                    await validation_func(data)
                else:
                    validation_func(data)
            except Exception as e:
                errors.append(f"Custom validation failed: {e}")
        
        return errors


class FilteringTransformation(BaseTransformation):
    """Data filtering transformation."""
    
    async def transform(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Filter data based on rules."""
        filter_rules = self.config.get('filter_rules', {})
        
        # Field inclusion/exclusion
        included_fields = filter_rules.get('include_fields')
        excluded_fields = filter_rules.get('exclude_fields', [])
        
        if included_fields:
            # Only include specified fields
            return {field: data[field] for field in included_fields if field in data}
        else:
            # Exclude specified fields
            return {field: value for field, value in data.items() if field not in excluded_fields}
    
    async def validate(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Validate filtering rules."""
        filter_rules = self.config.get('filter_rules', {})
        errors = []
        
        included_fields = filter_rules.get('include_fields')
        excluded_fields = filter_rules.get('exclude_fields', [])
        
        if included_fields and excluded_fields:
            overlapping = set(included_fields) & set(excluded_fields)
            if overlapping:
                errors.append(f"Fields cannot be both included and excluded: {overlapping}")
        
        return errors


class CustomTransformation(BaseTransformation):
    """Custom transformation using provided function."""
    
    async def transform(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Transform data using custom function."""
        transform_func = self.config.get('transform_func')
        if not transform_func:
            return data
        
        try:
            if asyncio.iscoroutinefunction(transform_func):
                return await transform_func(data, context or {})
            else:
                return transform_func(data, context or {})
        except Exception as e:
            self.logger.error(f"Custom transformation failed: {e}")
            return data
    
    async def validate(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Validate custom transformation."""
        # Custom validation would be implemented in the transformation function
        return []


class TransformationPipeline:
    """Data transformation pipeline."""
    
    def __init__(self, pipeline_id: str, name: str = ""):
        self.pipeline_id = pipeline_id
        self.name = name or pipeline_id
        self.rules: List[TransformationRule] = []
        self.status = PipelineStatus.IDLE
        self.statistics = PipelineStatistics(
            pipeline_id=pipeline_id,
            start_time=datetime.now()
        )
        
        self.logger = logging.getLogger(f"{__name__}.{pipeline_id}")
        
        # Transformation cache
        self._transformation_cache = {}
    
    def add_rule(self, rule: TransformationRule):
        """Add a transformation rule."""
        self.rules.append(rule)
        # Sort by priority
        self.rules.sort(key=lambda r: r.priority)
    
    def remove_rule(self, rule_id: str):
        """Remove a transformation rule."""
        self.rules = [rule for rule in self.rules if rule.rule_id != rule_id]
    
    def enable_rule(self, rule_id: str):
        """Enable a transformation rule."""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                rule.enabled = True
                break
    
    def disable_rule(self, rule_id: str):
        """Disable a transformation rule."""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                rule.enabled = False
                break
    
    async def transform_record(self, 
                             record: Dict[str, Any], 
                             context: Optional[Dict[str, Any]] = None) -> TransformationResult:
        """Transform a single record."""
        start_time = datetime.now()
        original_data = record.copy()
        transformed_data = record.copy()
        applied_rules = []
        errors = []
        warnings = []
        
        self.statistics.total_records_processed += 1
        
        # Apply enabled rules in priority order
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            try:
                # Check condition if specified
                if rule.condition and not await self._evaluate_condition(rule.condition, transformed_data, context):
                    continue
                
                # Apply transformation
                transformation = self._get_transformation(rule)
                if transformation:
                    result_data = await transformation.transform(transformed_data, context)
                    
                    # Validate transformation result
                    validation_errors = await transformation.validate(result_data, context)
                    if validation_errors:
                        errors.extend(validation_errors)
                    else:
                        transformed_data = result_data
                        applied_rules.append(rule.rule_id)
                        self.statistics.rules_executed += 1
                
            except Exception as e:
                error_msg = f"Rule '{rule.name}' failed: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)
                self.statistics.rules_failed += 1
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        self._update_processing_statistics(processing_time)
        
        # Determine success
        success = len(errors) == 0
        
        if success and transformed_data != original_data:
            self.statistics.records_transformed += 1
        elif success:
            # No transformation applied but no errors
            pass
        else:
            self.statistics.records_failed += 1
        
        return TransformationResult(
            success=success,
            original_data=original_data,
            transformed_data=transformed_data,
            applied_rules=applied_rules,
            errors=errors,
            warnings=warnings
        )
    
    async def transform_batch(self, 
                            records: List[Dict[str, Any]], 
                            context: Optional[Dict[str, Any]] = None) -> List[TransformationResult]:
        """Transform a batch of records."""
        self.status = PipelineStatus.PROCESSING
        
        try:
            results = []
            
            # Process records in parallel for better performance
            semaphore = asyncio.Semaphore(10)  # Limit concurrent transformations
            
            async def transform_single_record(record):
                async with semaphore:
                    return await self.transform_record(record, context)
            
            # Create tasks for parallel processing
            tasks = [transform_single_record(record) for record in records]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    final_results.append(TransformationResult(
                        success=False,
                        original_data=records[i],
                        transformed_data=records[i],
                        errors=[str(result)]
                    ))
                else:
                    final_results.append(result)
            
            self.status = PipelineStatus.COMPLETED
            return final_results
            
        except Exception as e:
            self.status = PipelineStatus.ERROR
            self.logger.error(f"Batch transformation failed: {e}")
            raise
    
    async def transform_event_batch(self, 
                                  event_batch: EventBatch, 
                                  context: Optional[Dict[str, Any]] = None) -> EventBatch:
        """Transform an event batch."""
        transformed_batch = EventBatch(
            batch_id=event_batch.batch_id,
            created_at=datetime.now(),
            source_tables=event_batch.source_tables.copy(),
            target_tables=event_batch.target_tables.copy(),
            event_types=event_batch.event_types.copy()
        )
        
        for event in event_batch.events:
            if event.new_values:
                result = await self.transform_record(event.new_values, context)
                
                # Update event with transformed data
                event.new_values = result.transformed_data
                
                # Add validation errors to event metadata
                if result.errors:
                    event.metadata['transformation_errors'] = result.errors
            
            transformed_batch.add_event(event)
        
        return transformed_batch
    
    def _get_transformation(self, rule: TransformationRule) -> Optional[BaseTransformation]:
        """Get transformation instance for a rule."""
        cache_key = f"{rule.transformation_type.value}_{rule.rule_id}"
        
        if cache_key in self._transformation_cache:
            return self._transformation_cache[cache_key]
        
        # Create transformation based on type
        transformation_config = rule.metadata.get('config', {})
        
        if rule.transformation_type == TransformationType.FIELD_MAPPING:
            transformation = FieldMappingTransformation(transformation_config)
        elif rule.transformation_type == TransformationType.TYPE_CONVERSION:
            transformation = TypeConversionTransformation(transformation_config)
        elif rule.transformation_type == TransformationType.VALUE_MODIFICATION:
            transformation = ValueModificationTransformation(transformation_config)
        elif rule.transformation_type == TransformationType.DATA_ENRICHMENT:
            transformation = DataEnrichmentTransformation(transformation_config)
        elif rule.transformation_type == TransformationType.VALIDATION:
            transformation = ValidationTransformation(transformation_config)
        elif rule.transformation_type == TransformationType.FILTERING:
            transformation = FilteringTransformation(transformation_config)
        elif rule.transformation_type == TransformationType.CUSTOM:
            transformation = CustomTransformation(transformation_config)
        else:
            self.logger.warning(f"Unknown transformation type: {rule.transformation_type}")
            return None
        
        self._transformation_cache[cache_key] = transformation
        return transformation
    
    async def _evaluate_condition(self, 
                                 condition: Callable, 
                                 data: Dict[str, Any], 
                                 context: Optional[Dict[str, Any]] = None) -> bool:
        """Evaluate a condition function."""
        try:
            if asyncio.iscoroutinefunction(condition):
                return await condition(data, context or {})
            else:
                return condition(data, context or {})
        except Exception as e:
            self.logger.warning(f"Condition evaluation failed: {e}")
            return False
    
    def _update_processing_statistics(self, processing_time_ms: float):
        """Update processing statistics."""
        # Update average processing time
        current_avg = self.statistics.average_processing_time_ms
        total_records = self.statistics.total_records_processed
        
        if total_records == 1:
            self.statistics.average_processing_time_ms = processing_time_ms
        else:
            # Running average
            self.statistics.average_processing_time_ms = (
                (current_avg * (total_records - 1) + processing_time_ms) / total_records
            )
        
        # Calculate throughput
        elapsed_time = (datetime.now() - self.statistics.start_time).total_seconds()
        if elapsed_time > 0:
            self.statistics.throughput_records_per_second = (
                self.statistics.total_records_processed / elapsed_time
            )
    
    def get_statistics(self) -> PipelineStatistics:
        """Get pipeline statistics."""
        self.statistics.end_time = datetime.now()
        return self.statistics
    
    def get_rules(self) -> List[TransformationRule]:
        """Get all transformation rules."""
        return self.rules.copy()


class AdvancedTransformationPipeline(TransformationPipeline):
    """Advanced transformation pipeline with additional features."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Performance optimization
        self._batch_cache = {}
        self._parallel_processing = True
        
        # Error handling
        self.error_threshold = 0.1  # Stop if error rate exceeds 10%
        self.max_retry_attempts = 3
        
        # Monitoring
        self.performance_metrics = {}
    
    async def transform_with_error_handling(self, 
                                          records: List[Dict[str, Any]], 
                                          context: Optional[Dict[str, Any]] = None) -> List[TransformationResult]:
        """Transform records with error handling and retry logic."""
        results = []
        error_count = 0
        
        for record in records:
            attempt = 0
            while attempt < self.max_retry_attempts:
                try:
                    result = await self.transform_record(record, context)
                    results.append(result)
                    
                    if not result.success:
                        error_count += 1
                    
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    attempt += 1
                    if attempt >= self.max_retry_attempts:
                        # Final failure
                        results.append(TransformationResult(
                            success=False,
                            original_data=record,
                            transformed_data=record,
                            errors=[f"Max retry attempts exceeded: {str(e)}"]
                        ))
                        error_count += 1
                    else:
                        # Wait before retry
                        await asyncio.sleep(0.1 * attempt)
            
            # Check error threshold
            if len(results) > 0:
                current_error_rate = error_count / len(results)
                if current_error_rate > self.error_threshold:
                    self.logger.warning(f"Error threshold exceeded: {current_error_rate:.2%}")
                    # Could pause or stop processing here
        
        return results
    
    async def optimize_performance(self):
        """Optimize pipeline performance."""
        # Analyze rule performance
        rule_performance = {}
        
        for rule in self.rules:
            if rule.enabled:
                # Simulate performance analysis
                rule_performance[rule.rule_id] = {
                    'execution_time': 0.1,  # Placeholder
                    'success_rate': 0.95
                }
        
        # Optimize rule order based on performance
        self.rules.sort(key=lambda r: (
            -rule_performance.get(r.rule_id, {}).get('success_rate', 0),
            rule_performance.get(r.rule_id, {}).get('execution_time', 0)
        ))
        
        self.performance_metrics = {
            'optimization_applied': True,
            'rule_performance': rule_performance,
            'optimized_order': [rule.name for rule in self.rules]
        }
    
    def enable_parallel_processing(self, max_workers: int = 10):
        """Enable parallel processing for batch operations."""
        self._parallel_processing = True
        self._max_workers = max_workers
    
    def disable_parallel_processing(self):
        """Disable parallel processing."""
        self._parallel_processing = False
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics."""
        metrics = {
            'pipeline_id': self.pipeline_id,
            'status': self.status.value,
            'statistics': self.statistics.to_dict(),
            'rules_count': len(self.rules),
            'enabled_rules_count': len([r for r in self.rules if r.enabled]),
            'cache_size': len(self._transformation_cache),
            'parallel_processing': self._parallel_processing
        }
        
        if hasattr(self, 'performance_metrics'):
            metrics.update(self.performance_metrics)
        
        return metrics
