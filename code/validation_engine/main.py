"""
Main Validation Engine
Unified interface for multi-stage data validation with configurable rules and scoring.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
from enum import Enum

from syntax_validator import SyntaxValidator, ValidationLevel
from consistency_checker import ConsistencyChecker, ConsistencyLevel, ConsistencyViolation
from anomaly_detector import AnomalyDetector, AnomalyScore


class ValidationStage(Enum):
    """Validation stages."""
    SYNTAX = "syntax"
    CONSISTENCY = "consistency"
    ANOMALY = "anomaly"
    DUPLICATE = "duplicate"
    QUALITY = "quality"


@dataclass
class ValidationRule:
    """Validation rule configuration."""
    name: str
    stage: ValidationStage
    field: Optional[str] = None
    rule_type: str = "custom"
    parameters: Dict[str, Any] = None
    enabled: bool = True
    weight: float = 1.0
    severity: str = "medium"
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class ValidationIssue:
    """Validation issue result."""
    rule_name: str
    stage: ValidationStage
    severity: str
    field: Optional[str]
    message: str
    suggestion: Optional[str]
    confidence: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['stage'] = self.stage.value
        return data


@dataclass
class ValidationResult:
    """Complete validation result."""
    record_id: Optional[str]
    is_valid: bool
    overall_score: float
    issues: List[ValidationIssue]
    syntax_results: Dict[str, Any]
    consistency_results: Dict[str, Any]
    anomaly_results: Dict[str, Any]
    duplicate_results: Dict[str, Any]
    quality_score: float
    validation_summary: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['issues'] = [issue.to_dict() for issue in self.issues]
        return {**data, **{"validation_summary": self.validation_summary}}


class DuplicateDetector:
    """Duplicate detection using multiple methods."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        
    def detect_exact_duplicates(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect exact duplicates."""
        duplicate_mask = data.duplicated(keep='first')
        duplicate_indices = data.index[duplicate_mask].tolist()
        
        return {
            'type': 'exact_duplicates',
            'count': len(duplicate_indices),
            'indices': duplicate_indices,
            'percentage': len(duplicate_indices) / len(data) * 100,
            'severity': 'high' if len(duplicate_indices) / len(data) > 0.1 else 'medium'
        }
        
    def detect_near_duplicates(self, data: pd.DataFrame, fields: List[str]) -> Dict[str, Any]:
        """Detect near duplicates using fuzzy matching."""
        # Simple implementation - in practice, use libraries like fuzzywuzzy
        near_duplicates = []
        
        for i in range(len(data)):
            for j in range(i + 1, len(data)):
                similarity = self._calculate_similarity(data.iloc[i], data.iloc[j], fields)
                if similarity >= self.similarity_threshold:
                    near_duplicates.append({
                        'index1': i,
                        'index2': j,
                        'similarity': similarity
                    })
                    
        return {
            'type': 'near_duplicates',
            'count': len(near_duplicates),
            'pairs': near_duplicates,
            'percentage': len(near_duplicates) / (len(data) * (len(data) - 1) / 2) * 100,
            'severity': 'medium' if len(near_duplicates) > 0 else 'low'
        }
        
    def _calculate_similarity(self, row1: pd.Series, row2: pd.Series, fields: List[str]) -> float:
        """Calculate similarity between two rows."""
        if not fields:
            return 0.0
            
        similarities = []
        
        for field in fields:
            if field in row1.index and field in row2.index:
                val1, val2 = str(row1[field]), str(row2[field])
                if val1 == val2:
                    similarities.append(1.0)
                elif val1.lower() == val2.lower():
                    similarities.append(0.8)
                else:
                    # Simple character-based similarity
                    similarity = self._character_similarity(val1, val2)
                    similarities.append(similarity)
                    
        return np.mean(similarities) if similarities else 0.0
        
    def _character_similarity(self, str1: str, str2: str) -> float:
        """Calculate character-based similarity."""
        if not str1 or not str2:
            return 0.0
            
        # Simple Levenshtein-like distance
        max_len = max(len(str1), len(str2))
        if max_len == 0:
            return 1.0
            
        matches = sum(1 for c1, c2 in zip(str1, str2) if c1 == c2)
        return matches / max_len


class DataQualityScorer:
    """Calculate overall data quality scores."""
    
    @staticmethod
    def calculate_completeness(data: pd.DataFrame) -> float:
        """Calculate data completeness score."""
        total_cells = data.shape[0] * data.shape[1]
        non_null_cells = data.count().sum()
        return non_null_cells / total_cells if total_cells > 0 else 0.0
        
    @staticmethod
    def calculate_validity(syntax_results: Dict[str, Any]) -> float:
        """Calculate validity score from syntax validation."""
        if not syntax_results:
            return 1.0
            
        total_valid = sum(1 for result in syntax_results.values() if result.get('is_valid', True))
        total_fields = len(syntax_results)
        return total_valid / total_fields if total_fields > 0 else 1.0
        
    @staticmethod
    def calculate_consistency(consistency_results: Dict[str, Any]) -> float:
        """Calculate consistency score."""
        if not consistency_results:
            return 1.0
            
        score = consistency_results.get('consistency_score', 1.0)
        return max(0.0, min(1.0, score))
        
    @staticmethod
    def calculate_uniqueness(duplicate_results: Dict[str, Any]) -> float:
        """Calculate uniqueness score from duplicate detection."""
        if not duplicate_results:
            return 1.0
            
        exact_dup_pct = duplicate_results.get('exact_duplicates', {}).get('percentage', 0)
        near_dup_pct = duplicate_results.get('near_duplicates', {}).get('percentage', 0)
        
        # Deduct from 1.0 based on duplicate percentages
        penalty = (exact_dup_pct + near_dup_pct) / 100
        return max(0.0, 1.0 - penalty)
        
    @staticmethod
    def calculate_anomaly_score(anomaly_results: Dict[str, Any]) -> float:
        """Calculate anomaly score (inverse of data quality)."""
        if not anomaly_results:
            return 1.0
            
        overall_score = anomaly_results.get('overall_anomaly_score', 0.0)
        return max(0.0, 1.0 - overall_score)
        
    @staticmethod
    def calculate_overall_quality(completeness: float, validity: float, 
                                consistency: float, uniqueness: float, 
                                anomaly_score: float, weights: Dict[str, float] = None) -> float:
        """Calculate weighted overall quality score."""
        if weights is None:
            weights = {
                'completeness': 0.25,
                'validity': 0.25,
                'consistency': 0.25,
                'uniqueness': 0.15,
                'anomaly_score': 0.10
            }
            
        score = (
            weights['completeness'] * completeness +
            weights['validity'] * validity +
            weights['consistency'] * consistency +
            weights['uniqueness'] * uniqueness +
            weights['anomaly_score'] * anomaly_score
        )
        
        return max(0.0, min(1.0, score))


class ValidationEngine:
    """Main validation engine orchestrator."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.syntax_validator = SyntaxValidator()
        self.consistency_checker = ConsistencyChecker()
        self.anomaly_detector = AnomalyDetector()
        self.duplicate_detector = DuplicateDetector()
        self.quality_scorer = DataQualityScorer()
        
        self.rules = []
        self.field_types = {}
        self.business_rules = []
        self.reference_datasets = {}
        
        self.logger = logging.getLogger(__name__)
        
        # Load default configuration
        self._load_default_config()
        
    def _load_default_config(self):
        """Load default validation configuration."""
        default_config = {
            'validation_stages': {
                'syntax': {'enabled': True},
                'consistency': {'enabled': True},
                'anomaly': {'enabled': True},
                'duplicate': {'enabled': True},
                'quality': {'enabled': True}
            },
            'scoring': {
                'weights': {
                    'completeness': 0.25,
                    'validity': 0.25,
                    'consistency': 0.25,
                    'uniqueness': 0.15,
                    'anomaly_score': 0.10
                }
            },
            'thresholds': {
                'anomaly_score': 0.8,
                'duplicate_threshold': 0.85,
                'quality_threshold': 0.7
            }
        }
        
        # Update with user config
        for key, value in self.config.items():
            if key in default_config:
                default_config[key].update(value)
                
        self.config = default_config
        
    def add_validation_rule(self, rule: ValidationRule):
        """Add validation rule."""
        self.rules.append(rule)
        
    def add_field_type(self, field: str, field_type: str):
        """Add field type mapping."""
        self.field_types[field] = field_type
        
    def add_reference_data(self, name: str, data: Union[pd.DataFrame, List, Dict], key_field: str = None):
        """Add reference dataset."""
        if isinstance(data, (list, dict)):
            data = pd.DataFrame(data)
        self.reference_datasets[name] = {'data': data, 'key_field': key_field}
        self.consistency_checker.add_reference_data(name, data, key_field)
        
    def add_business_rule(self, rule_func, rule_name: str, level: ConsistencyLevel = ConsistencyLevel.MEDIUM):
        """Add business rule."""
        self.business_rules.append((rule_func, rule_name, level))
        self.consistency_checker.add_business_rule(rule_func, rule_name, level)
        
    def validate_single_record(self, record: Dict[str, Any], record_id: Optional[str] = None) -> ValidationResult:
        """Validate a single record."""
        issues = []
        timestamp = datetime.now()
        
        # Convert record to DataFrame for consistency
        record_df = pd.DataFrame([record])
        
        results = {
            'syntax_results': {},
            'consistency_results': {},
            'anomaly_results': {},
            'duplicate_results': {}
        }
        
        # Stage 1: Syntax Validation
        if self.config['validation_stages']['syntax']['enabled']:
            syntax_results = self.syntax_validator.validate_dataset(record, self.field_types)
            results['syntax_results'] = {k: v.to_dict() for k, v in syntax_results.items()}
            
            # Convert syntax issues to ValidationIssue format
            for field, result in syntax_results.items():
                if not result.is_valid:
                    for error in result.errors:
                        issues.append(ValidationIssue(
                            rule_name=f"syntax_validation_{field}",
                            stage=ValidationStage.SYNTAX,
                            severity="high",
                            field=field,
                            message=error,
                            suggestion=None,
                            confidence=1.0,
                            timestamp=timestamp
                        ))
                        
                for warning in result.warnings:
                    issues.append(ValidationIssue(
                        rule_name=f"syntax_validation_{field}",
                        stage=ValidationStage.SYNTAX,
                        severity="medium",
                        field=field,
                        message=warning,
                        suggestion=None,
                        confidence=0.8,
                        timestamp=timestamp
                    ))
                    
        # Stage 2: Consistency Validation
        if self.config['validation_stages']['consistency']['enabled']:
            consistency_violations = self.consistency_checker.validate_single_record(record)
            
            for violation in consistency_violations:
                issues.append(ValidationIssue(
                    rule_name=f"consistency_{violation.level.value}",
                    stage=ValidationStage.CONSISTENCY,
                    severity=violation.level.value,
                    field=",".join(violation.affected_fields),
                    message=violation.message,
                    suggestion=violation.suggestion,
                    confidence=0.9,
                    timestamp=timestamp
                ))
                
            # Prepare consistency results
            results['consistency_results'] = {
                'violations': [v.to_dict() for v in consistency_violations],
                'consistency_score': 1.0 - (len(consistency_violations) * 0.1)
            }
            
        # Stage 3: Anomaly Detection
        if self.config['validation_stages']['anomaly']['enabled']:
            # For single record, detect anomalies in context of dataset
            # This is simplified - in practice, you'd pass the full dataset
            anomaly_results = self._detect_record_anomalies(record)
            results['anomaly_results'] = anomaly_results
            
            # Add anomaly issues
            for anomaly in anomaly_results.get('explanations', []):
                issues.append(ValidationIssue(
                    rule_name="anomaly_detection",
                    stage=ValidationStage.ANOMALY,
                    severity="medium",
                    field=None,
                    message=anomaly,
                    suggestion="Review data for unusual patterns",
                    confidence=0.7,
                    timestamp=timestamp
                ))
                
        # Stage 4: Duplicate Detection (simplified for single record)
        if self.config['validation_stages']['duplicate']['enabled']:
            results['duplicate_results'] = {
                'exact_duplicates': {'count': 0, 'percentage': 0},
                'near_duplicates': {'count': 0, 'percentage': 0}
            }
            
        # Calculate scores
        completeness = DataQualityScorer.calculate_completeness(record_df)
        validity = DataQualityScorer.calculate_validity(results['syntax_results'])
        consistency = DataQualityScorer.calculate_consistency(results['consistency_results'])
        uniqueness = DataQualityScorer.calculate_uniqueness(results['duplicate_results'])
        anomaly_score = DataQualityScorer.calculate_anomaly_score(results['anomaly_results'])
        
        quality_score = DataQualityScorer.calculate_overall_quality(
            completeness, validity, consistency, uniqueness, anomaly_score,
            self.config['scoring']['weights']
        )
        
        # Determine overall validity
        critical_issues = [i for i in issues if i.severity == 'high']
        is_valid = len(critical_issues) == 0
        
        # Calculate overall score
        overall_score = quality_score
        
        validation_summary = {
            'completeness': completeness,
            'validity': validity,
            'consistency': consistency,
            'uniqueness': uniqueness,
            'anomaly_score': anomaly_score,
            'quality_score': quality_score,
            'total_issues': len(issues),
            'critical_issues': len(critical_issues)
        }
        
        return ValidationResult(
            record_id=record_id,
            is_valid=is_valid,
            overall_score=overall_score,
            issues=issues,
            syntax_results=results['syntax_results'],
            consistency_results=results['consistency_results'],
            anomaly_results=results['anomaly_results'],
            duplicate_results=results['duplicate_results'],
            quality_score=quality_score,
            validation_summary=validation_summary,
            timestamp=timestamp
        )
        
    def validate_dataset(self, data: Union[pd.DataFrame, List[Dict]], batch_size: int = 1000) -> Dict[str, Any]:
        """Validate entire dataset."""
        if isinstance(data, list):
            data = pd.DataFrame(data)
            
        timestamp = datetime.now()
        results = []
        summary_stats = {
            'total_records': len(data),
            'valid_records': 0,
            'invalid_records': 0,
            'average_quality_score': 0.0,
            'total_issues': 0,
            'issues_by_stage': {stage.value: 0 for stage in ValidationStage},
            'issues_by_severity': {'high': 0, 'medium': 0, 'low': 0}
        }
        
        # Process in batches
        for i in range(0, len(data), batch_size):
            batch = data.iloc[i:i+batch_size]
            
            for idx, row in batch.iterrows():
                record_id = str(idx)
                record_dict = row.to_dict()
                
                result = self.validate_single_record(record_dict, record_id)
                results.append(result)
                
                # Update summary statistics
                if result.is_valid:
                    summary_stats['valid_records'] += 1
                else:
                    summary_stats['invalid_records'] += 1
                    
                summary_stats['total_issues'] += len(result.issues)
                summary_stats['average_quality_score'] += result.quality_score
                
                for issue in result.issues:
                    summary_stats['issues_by_stage'][issue.stage.value] += 1
                    summary_stats['issues_by_severity'][issue.severity] += 1
                    
        # Calculate final averages
        if len(results) > 0:
            summary_stats['average_quality_score'] /= len(results)
            
        # Overall dataset validation results
        dataset_results = {
            'records': [r.to_dict() for r in results],
            'summary': summary_stats,
            'timestamp': timestamp.isoformat()
        }
        
        # Add dataset-level results
        if self.config['validation_stages']['anomaly']['enabled']:
            dataset_results['dataset_anomalies'] = self.anomaly_detector.detect_dataset_anomalies(data)
            
        if self.config['validation_stages']['duplicate']['enabled']:
            dataset_results['duplicates'] = self._detect_dataset_duplicates(data)
            
        return dataset_results
        
    def _detect_record_anomalies(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies for a single record."""
        # This is a simplified version - in practice, you'd need context
        # For now, return empty results
        return {
            'overall_anomaly_score': 0.0,
            'explanations': []
        }
        
    def _detect_dataset_duplicates(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect duplicates in dataset."""
        results = {}
        
        if self.config['validation_stages']['duplicate']['enabled']:
            results['exact_duplicates'] = self.duplicate_detector.detect_exact_duplicates(data)
            
            # For near duplicates, use string columns
            string_columns = data.select_dtypes(include=['object']).columns.tolist()
            if string_columns:
                results['near_duplicates'] = self.duplicate_detector.detect_near_duplicates(
                    data, string_columns
                )
                
        return results
        
    def generate_report(self, results: Dict[str, Any], output_format: str = 'json') -> str:
        """Generate validation report."""
        if output_format.lower() == 'json':
            return json.dumps(results, indent=2, default=str)
        elif output_format.lower() == 'summary':
            summary = results['summary']
            report = f"""
Data Validation Report
======================

Total Records: {summary['total_records']}
Valid Records: {summary['valid_records']}
Invalid Records: {summary['invalid_records']}
Average Quality Score: {summary['average_quality_score']:.2%}

Issues by Stage:
{chr(10).join(f"  {stage}: {count}" for stage, count in summary['issues_by_stage'].items())}

Issues by Severity:
{chr(10).join(f"  {severity}: {count}" for severity, count in summary['issues_by_severity'].items())}

Quality Dimensions:
  Completeness: {summary.get('completeness', 0):.2%}
  Validity: {summary.get('validity', 0):.2%}
  Consistency: {summary.get('consistency', 0):.2%}
  Uniqueness: {summary.get('uniqueness', 0):.2%}
  Anomaly Score: {summary.get('anomaly_score', 0):.2%}
            """
            return report.strip()
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
            
    def export_issues(self, results: Dict[str, Any], file_path: str, format: str = 'csv'):
        """Export validation issues to file."""
        issues_data = []
        
        for record_result in results['records']:
            for issue in record_result['issues']:
                issue_data = issue.copy()
                issue_data['record_id'] = record_result['record_id']
                issue_data['record_valid'] = record_result['is_valid']
                issue_data['record_quality_score'] = record_result['quality_score']
                issues_data.append(issue_data)
                
        if format.lower() == 'csv':
            df = pd.DataFrame(issues_data)
            df.to_csv(file_path, index=False)
        elif format.lower() == 'json':
            with open(file_path, 'w') as f:
                json.dump(issues_data, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Example usage and demonstration
def demo_validation_engine():
    """Demonstration of validation engine usage."""
    
    # Sample data
    sample_data = [
        {
            'id': 1,
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '+1234567890',
            'date_joined': '2023-01-15',
            'age': 30,
            'salary': 50000
        },
        {
            'id': 2,
            'name': 'Jane Smith',
            'email': 'invalid-email',
            'phone': '12345',  # Invalid phone
            'date_joined': '2023-13-45',  # Invalid date
            'age': -5,  # Invalid age
            'salary': 999999  # Potential outlier
        }
    ]
    
    # Initialize validation engine
    engine = ValidationEngine()
    
    # Configure field types
    engine.add_field_type('email', 'email')
    engine.add_field_type('phone', 'phone')
    engine.add_field_type('date_joined', 'date')
    
    # Add business rules
    def validate_age(age):
        return 0 <= age <= 120, "Age must be between 0 and 120"
        
    engine.add_business_rule(validate_age, "age_validation")
    
    # Validate dataset
    results = engine.validate_dataset(sample_data)
    
    # Generate report
    report = engine.generate_report(results, 'summary')
    print(report)
    
    return results


if __name__ == "__main__":
    demo_validation_engine()