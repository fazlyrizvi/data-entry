"""
Cross-Dataset Consistency Validation Module
Validates relationships and consistency between different datasets and fields.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any, Set, Union
from collections import defaultdict, Counter
from enum import Enum
import numpy as np
import pandas as pd


class ConsistencyLevel(Enum):
    """Consistency validation levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConsistencyViolation:
    """Represents a consistency violation."""
    
    def __init__(self, level: ConsistencyLevel, message: str, 
                 affected_fields: List[str], suggestion: str = None):
        self.level = level
        self.message = message
        self.affected_fields = affected_fields
        self.suggestion = suggestion
        self.timestamp = pd.Timestamp.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'level': self.level.value,
            'message': self.message,
            'affected_fields': self.affected_fields,
            'suggestion': self.suggestion,
            'timestamp': self.timestamp.isoformat()
        }


class ReferenceDataValidator:
    """Validates data against reference datasets."""
    
    def __init__(self):
        self.reference_datasets = {}
        self.reference_mappings = {}
        
    def add_reference_dataset(self, name: str, data: Union[pd.DataFrame, List, Dict], 
                            key_field: str = None):
        """Add reference dataset for validation."""
        if isinstance(data, (list, dict)):
            data = pd.DataFrame(data)
        self.reference_datasets[name] = data
        if key_field:
            self.reference_mappings[name] = key_field
            
    def validate_against_reference(self, field_name: str, field_values: List[Any], 
                                 reference_name: str, reference_field: str = None) -> List[ConsistencyViolation]:
        """Validate field values against reference dataset."""
        violations = []
        
        if reference_name not in self.reference_datasets:
            violations.append(ConsistencyViolation(
                ConsistencyLevel.CRITICAL,
                f"Reference dataset '{reference_name}' not found",
                [field_name],
                "Add reference dataset or check name"
            ))
            return violations
            
        ref_data = self.reference_datasets[reference_name]
        
        if reference_field is None:
            reference_field = self.reference_mappings.get(reference_name)
            
        if reference_field is None or reference_field not in ref_data.columns:
            violations.append(ConsistencyViolation(
                ConsistencyLevel.CRITICAL,
                f"Reference field '{reference_field}' not found in '{reference_name}'",
                [field_name],
                "Check reference field name"
            ))
            return violations
            
        # Get reference values
        ref_values = set(ref_data[reference_field].dropna().astype(str))
        invalid_values = []
        
        for value in field_values:
            if pd.isna(value) or str(value).strip() == '':
                continue
            if str(value) not in ref_values:
                invalid_values.append(value)
                
        if invalid_values:
            violations.append(ConsistencyViolation(
                ConsistencyLevel.HIGH,
                f"Found {len(invalid_values)} invalid values not in reference dataset",
                [field_name],
                f"Valid values: {list(ref_values)[:10]}..."  # Show first 10
            ))
            
        return violations


class BusinessRuleValidator:
    """Validates business rules and constraints."""
    
    def __init__(self):
        self.rules = []
        
    def add_rule(self, rule_func, rule_name: str, level: ConsistencyLevel = ConsistencyLevel.MEDIUM):
        """Add custom business rule."""
        self.rules.append({
            'func': rule_func,
            'name': rule_name,
            'level': level
        })
        
    def validate_rules(self, data: Dict[str, Any]) -> List[ConsistencyViolation]:
        """Validate data against all business rules."""
        violations = []
        
        for rule in self.rules:
            try:
                result = rule['func'](data)
                if isinstance(result, tuple):
                    is_valid, message = result
                elif isinstance(result, bool):
                    is_valid, message = result, f"Rule '{rule['name']}' failed"
                else:
                    continue
                    
                if not is_valid:
                    violations.append(ConsistencyViolation(
                        rule['level'],
                        message,
                        list(data.keys()),
                        f"Check rule: {rule['name']}"
                    ))
            except Exception as e:
                violations.append(ConsistencyViolation(
                    ConsistencyLevel.MEDIUM,
                    f"Error evaluating rule '{rule['name']}': {str(e)}",
                    list(data.keys()),
                    "Check rule implementation"
                ))
                
        return violations


class ReferentialIntegrityValidator:
    """Validates referential integrity between related fields."""
    
    def __init__(self):
        self.relationships = {}
        self.conditional_rules = {}
        
    def add_relationship(self, parent_field: str, child_field: str, 
                        relationship_type: str = 'mandatory'):
        """Add field relationship."""
        self.relationships[f"{parent_field}->{child_field}"] = {
            'parent': parent_field,
            'child': child_field,
            'type': relationship_type
        }
        
    def add_conditional_rule(self, condition_field: str, condition_value: Any,
                           required_field: str):
        """Add conditional requirement rule."""
        key = f"{condition_field}=={condition_value}"
        if key not in self.conditional_rules:
            self.conditional_rules[key] = []
        self.conditional_rules[key].append(required_field)
        
    def validate_referential_integrity(self, data: Dict[str, Any]) -> List[ConsistencyViolation]:
        """Validate referential integrity."""
        violations = []
        
        # Check relationships
        for rel_key, relationship in self.relationships.items():
            parent_field = relationship['parent']
            child_field = relationship['child']
            rel_type = relationship['type']
            
            if parent_field in data and child_field in data:
                parent_value = data[parent_field]
                child_value = data[child_field]
                
                # Mandatory relationship check
                if rel_type == 'mandatory':
                    if pd.isna(parent_value) and not pd.isna(child_value):
                        violations.append(ConsistencyViolation(
                            ConsistencyLevel.HIGH,
                            f"Child field '{child_field}' has value but parent '{parent_field}' is empty",
                            [parent_field, child_field],
                            "Provide value for parent field"
                        ))
                        
        # Check conditional rules
        for condition_key, required_fields in self.conditional_rules.items():
            condition_field, condition_value = condition_key.split('==')
            
            if condition_field in data:
                field_value = data[condition_field]
                if str(field_value) == str(condition_value):
                    # Condition met, check required fields
                    for req_field in required_fields:
                        if req_field in data and (pd.isna(data[req_field]) or str(data[req_field]).strip() == ''):
                            violations.append(ConsistencyViolation(
                                ConsistencyLevel.MEDIUM,
                                f"Field '{req_field}' is required when '{condition_field}' is '{condition_value}'",
                                [req_field],
                                f"Provide value for {req_field}"
                            ))
                            
        return violations


class DataTypeConsistencyValidator:
    """Validates data type consistency within fields."""
    
    @staticmethod
    def detect_type_inconsistencies(values: List[Any]) -> List[ConsistencyViolation]:
        """Detect type inconsistencies in a list of values."""
        violations = []
        
        # Remove None/NaN values for type detection
        valid_values = [v for v in values if v is not None and not pd.isna(v)]
        
        if len(valid_values) < 2:
            return violations
            
        # Detect types
        type_counts = Counter(type(v).__name__ for v in valid_values)
        most_common_type = type_counts.most_common(1)[0][0]
        
        # Find inconsistent types
        inconsistent_types = [t for t, count in type_counts.items() if t != most_common_type]
        
        if len(inconsistent_types) > 0:
            violations.append(ConsistencyViolation(
                ConsistencyLevel.MEDIUM,
                f"Found multiple data types in field: {list(type_counts.keys())}",
                ['field'],
                f"Standardize all values to {most_common_type}"
            ))
            
        return violations
        
    @staticmethod
    def detect_format_inconsistencies(values: List[str]) -> List[ConsistencyViolation]:
        """Detect format inconsistencies in string values."""
        violations = []
        
        valid_values = [v for v in values if v is not None and not pd.isna(v) and isinstance(v, str)]
        
        if len(valid_values) < 2:
            return violations
            
        # Analyze string patterns
        patterns = []
        for value in valid_values:
            # Simple pattern detection
            pattern = ''
            for char in value:
                if char.isdigit():
                    pattern += 'D'
                elif char.isalpha():
                    pattern += 'A'
                elif char.isspace():
                    pattern += 'S'
                else:
                    pattern += 'S'
            patterns.append(pattern)
            
        pattern_counts = Counter(patterns)
        
        if len(pattern_counts) > 2:  # Allow some variation
            violations.append(ConsistencyViolation(
                ConsistencyLevel.MEDIUM,
                f"Found {len(pattern_counts)} different string patterns",
                ['field'],
                "Standardize string format"
            ))
            
        return violations


class ConsistencyChecker:
    """Main consistency checking orchestrator."""
    
    def __init__(self):
        self.reference_validator = ReferenceDataValidator()
        self.business_validator = BusinessRuleValidator()
        self.referential_validator = ReferentialIntegrityValidator()
        self.type_validator = DataTypeConsistencyValidator()
        self.logger = logging.getLogger(__name__)
        
    def add_reference_data(self, name: str, data: Union[pd.DataFrame, List, Dict], 
                          key_field: str = None):
        """Add reference dataset."""
        self.reference_validator.add_reference_dataset(name, data, key_field)
        
    def add_business_rule(self, rule_func, rule_name: str, 
                         level: ConsistencyLevel = ConsistencyLevel.MEDIUM):
        """Add business rule."""
        self.business_validator.add_rule(rule_func, rule_name, level)
        
    def add_field_relationship(self, parent_field: str, child_field: str):
        """Add field relationship."""
        self.referential_validator.add_relationship(parent_field, child_field)
        
    def add_conditional_rule(self, condition_field: str, condition_value: Any,
                           required_field: str):
        """Add conditional requirement."""
        self.referential_validator.add_conditional_rule(condition_field, condition_value, required_field)
        
    def validate_single_record(self, record: Dict[str, Any]) -> List[ConsistencyViolation]:
        """Validate a single record for consistency."""
        all_violations = []
        
        # Validate business rules
        all_violations.extend(self.business_validator.validate_rules(record))
        
        # Validate referential integrity
        all_violations.extend(self.referential_validator.validate_referential_integrity(record))
        
        return all_violations
        
    def validate_dataset_consistency(self, dataset: Union[pd.DataFrame, List[Dict]]) -> Dict[str, Any]:
        """Validate entire dataset for consistency."""
        if isinstance(dataset, list):
            dataset = pd.DataFrame(dataset)
            
        violations = []
        field_analysis = {}
        
        # Analyze each field for type consistency
        for column in dataset.columns:
            values = dataset[column].tolist()
            type_violations = self.type_validator.detect_type_inconsistencies(values)
            
            # Add column name to violations
            for violation in type_violations:
                violation.affected_fields = [column]
                
            violations.extend(type_violations)
            
            # Format consistency for string fields
            if dataset[column].dtype == 'object':
                string_values = [v for v in values if isinstance(v, str)]
                format_violations = self.type_validator.detect_format_inconsistencies(string_values)
                
                for violation in format_violations:
                    violation.affected_fields = [column]
                    
                violations.extend(format_violations)
                
        # Check for null patterns
        null_patterns = self._analyze_null_patterns(dataset)
        violations.extend(null_patterns)
        
        # Check for duplicate patterns
        duplicate_patterns = self._analyze_duplicate_patterns(dataset)
        violations.extend(duplicate_patterns)
        
        return {
            'total_violations': len(violations),
            'violations_by_level': self._group_violations_by_level(violations),
            'violations': [v.to_dict() for v in violations],
            'field_analysis': field_analysis,
            'consistency_score': self._calculate_consistency_score(violations, dataset.shape[0])
        }
        
    def _analyze_null_patterns(self, dataset: pd.DataFrame) -> List[ConsistencyViolation]:
        """Analyze null value patterns."""
        violations = []
        
        # Check for too many nulls
        null_ratios = dataset.isnull().sum() / len(dataset)
        high_null_fields = null_ratios[null_ratios > 0.5]
        
        for field, ratio in high_null_fields.items():
            violations.append(ConsistencyViolation(
                ConsistencyLevel.MEDIUM,
                f"Field '{field}' has {ratio:.1%} null values",
                [field],
                "Consider data imputation or field removal"
            ))
            
        return violations
        
    def _analyze_duplicate_patterns(self, dataset: pd.DataFrame) -> List[ConsistencyViolation]:
        """Analyze duplicate value patterns."""
        violations = []
        
        # Check for duplicate values in each field
        for column in dataset.columns:
            value_counts = dataset[column].value_counts()
            duplicates = value_counts[value_counts > 1]
            
            if len(duplicates) > 0:
                violations.append(ConsistencyViolation(
                    ConsistencyLevel.LOW,
                    f"Field '{column}' has {len(duplicates)} duplicate values",
                    [column],
                    "Check if duplicates are intentional"
                ))
                
        return violations
        
    def _group_violations_by_level(self, violations: List[ConsistencyViolation]) -> Dict[str, int]:
        """Group violations by severity level."""
        levels = defaultdict(int)
        for violation in violations:
            levels[violation.level.value] += 1
        return dict(levels)
        
    def _calculate_consistency_score(self, violations: List[ConsistencyViolation], 
                                   total_records: int) -> float:
        """Calculate overall consistency score."""
        if total_records == 0:
            return 1.0
            
        # Weight violations by level
        weights = {
            ConsistencyLevel.CRITICAL: 1.0,
            ConsistencyLevel.HIGH: 0.7,
            ConsistencyLevel.MEDIUM: 0.4,
            ConsistencyLevel.LOW: 0.1
        }
        
        weighted_violations = sum(
            weights.get(v.level, 0.5) for v in violations
        )
        
        # Calculate score (0-1, higher is better)
        max_possible_violations = total_records * 0.1  # Assume 10% tolerance
        score = max(0, 1 - (weighted_violations / max_possible_violations))
        
        return min(1.0, score)