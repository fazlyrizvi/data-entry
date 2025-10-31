# Data Validation Engine Implementation Guide

## Overview

This document provides a comprehensive guide to the multi-stage data validation engine, which implements syntax validation, cross-dataset consistency checks, and AI-powered anomaly detection using statistical methods and basic ML approaches.

## Architecture

The validation engine follows a modular architecture with five main components:

1. **Syntax Validator** - Validates data format and structure
2. **Consistency Checker** - Ensures cross-dataset and business rule compliance
3. **Anomaly Detector** - Identifies unusual patterns using statistical and ML methods
4. **Duplicate Detector** - Finds exact and near-duplicate records
5. **Main Orchestrator** - Coordinates all validation stages and provides unified interface

## Component Details

### 1. Syntax Validator (`syntax_validator.py`)

The syntax validator handles format validation for common data types:

#### Features:
- **Email Validation**: RFC-compliant regex patterns with domain checking
- **Phone Validation**: International phone number support using `phonenumbers` library
- **Date Validation**: Multiple format support with logical date range checking
- **Custom Pattern Validation**: Regex-based validation for custom formats

#### Key Classes:
- `EmailValidator`: Comprehensive email format validation
- `PhoneValidator`: International phone number parsing and validation
- `DateValidator`: Multiple date format support with range validation
- `CustomPatternValidator`: Generic regex pattern matching
- `SyntaxValidationResult`: Standardized validation result format

#### Usage Example:
```python
from syntax_validator import SyntaxValidator

validator = SyntaxValidator()

# Validate email
result = validator.validate_field("user@example.com", "email")
print(result.is_valid)  # True

# Validate phone with country code
result = validator.validate_field("+1234567890", "phone", country_code="US")
print(result.is_valid)  # True

# Validate date
result = validator.validate_field("2023-01-15", "date")
print(result.is_valid)  # True
```

### 2. Consistency Checker (`consistency_checker.py`)

The consistency checker ensures data integrity across datasets and validates business rules:

#### Features:
- **Reference Data Validation**: Validates against external reference datasets
- **Business Rule Engine**: Configurable custom validation rules
- **Referential Integrity**: Validates relationships between fields
- **Data Type Consistency**: Detects mixed data types within fields

#### Key Classes:
- `ReferenceDataValidator`: Validates against reference datasets
- `BusinessRuleValidator`: Custom business rule execution
- `ReferentialIntegrityValidator`: Field relationship validation
- `DataTypeConsistencyValidator`: Type consistency checking
- `ConsistencyViolation`: Standardized violation reporting

#### Business Rules Example:
```python
def validate_age_range(data):
    age = data.get('age')
    if age is not None and (age < 0 or age > 120):
        return False, "Age must be between 0 and 120"
    return True, ""

def validate_salary_range(data):
    salary = data.get('salary')
    if salary is not None and salary < 0:
        return False, "Salary cannot be negative"
    return True, ""

checker = ConsistencyChecker()
checker.add_business_rule(validate_age_range, "age_range")
checker.add_business_rule(validate_salary_range, "salary_range")
```

### 3. Anomaly Detector (`anomaly_detector.py`)

The anomaly detector uses statistical methods and ML algorithms to identify unusual patterns:

#### Detection Methods:

##### Statistical Methods:
- **Z-Score Analysis**: Identifies values far from mean
- **Interquartile Range (IQR)**: Detects outliers using quartile analysis
- **Median Absolute Deviation (MAD)**: Robust outlier detection

##### Machine Learning Methods:
- **Isolation Forest**: Tree-based anomaly detection
- **DBSCAN Clustering**: Density-based outlier identification
- **Correlation Analysis**: Identifies breaks in expected relationships

#### Key Classes:
- `StatisticalAnomalyDetector`: Z-score, IQR, and MAD methods
- `IsolationForestDetector`: ML-based anomaly detection
- `ClusteringAnomalyDetector`: DBSCAN-based outlier detection
- `PatternAnomalyDetector`: Sequential and categorical anomaly detection
- `CorrelationAnomalyDetector`: Relationship-based anomaly detection
- `TemporalAnomalyDetector`: Time series anomaly detection

#### Usage Example:
```python
from anomaly_detector import AnomalyDetector

detector = AnomalyDetector()

# Detect numerical outliers
data = [1, 2, 3, 4, 5, 100, 7, 8, 9]  # 100 is an outlier
results = detector.detect_numerical_outliers(data)

# Detect correlation anomalies
import pandas as pd
df = pd.DataFrame({
    'x': [1, 2, 3, 4, 5],
    'y': [2, 4, 6, 8, 10]  # Perfect correlation
})
anomalies = detector.detect_correlation_anomalies(df)
```

### 4. Duplicate Detector (`duplicate_detector.py`)

The duplicate detector identifies both exact and near-duplicate records:

#### Detection Methods:
- **Exact Duplicates**: Identical records across all fields
- **Near Duplicates**: Fuzzy matching for similar records
- **Similarity Scoring**: Character-based similarity calculation

#### Usage Example:
```python
from duplicate_detector import DuplicateDetector

detector = DuplicateDetector(similarity_threshold=0.85)

# Detect exact duplicates
exact_dups = detector.detect_exact_duplicates(dataframe)

# Detect near duplicates using specific fields
near_dups = detector.detect_near_duplicates(dataframe, ['name', 'email'])
```

### 5. Main Orchestrator (`main.py`)

The main orchestrator provides a unified interface to all validation components:

#### Features:
- **Multi-stage Validation**: Coordinates all validation stages
- **Configurable Rules**: Flexible rule configuration system
- **Quality Scoring**: Comprehensive data quality metrics
- **Batch Processing**: Efficient processing of large datasets
- **Reporting**: JSON and summary report generation

#### Key Classes:
- `ValidationEngine`: Main orchestrator class
- `ValidationRule`: Rule configuration
- `ValidationIssue`: Issue reporting format
- `ValidationResult`: Complete validation result
- `DataQualityScorer`: Quality score calculation

#### Usage Example:
```python
from main import ValidationEngine, ValidationRule, ValidationStage

# Initialize engine
engine = ValidationEngine()

# Configure field types
engine.add_field_type('email', 'email')
engine.add_field_type('phone', 'phone')

# Add validation rules
rule = ValidationRule(
    name="email_syntax",
    stage=ValidationStage.SYNTAX,
    field="email",
    severity="high"
)
engine.add_validation_rule(rule)

# Add reference data
reference_data = pd.DataFrame({'country_code': ['US', 'UK', 'CA']})
engine.add_reference_data('countries', reference_data, 'country_code')

# Validate single record
record = {
    'email': 'user@example.com',
    'phone': '+1234567890',
    'country_code': 'US'
}
result = engine.validate_single_record(record)

# Validate dataset
dataset_results = engine.validate_dataset(dataframe)

# Generate report
report = engine.generate_report(dataset_results, 'summary')
print(report)
```

## Data Quality Scoring

The engine calculates comprehensive quality scores across multiple dimensions:

### Quality Dimensions:

1. **Completeness**: Percentage of non-null values
2. **Validity**: Percentage of syntactically valid values
3. **Consistency**: Cross-field and business rule compliance
4. **Uniqueness**: Absence of duplicate records
5. **Anomaly Score**: Measure of unusual patterns (inverse of quality)

### Scoring Formula:
```
Overall Quality = (
    0.25 × Completeness +
    0.25 × Validity +
    0.25 × Consistency +
    0.15 × Uniqueness +
    0.10 × (1 - Anomaly_Score)
)
```

### Score Interpretation:
- **0.9-1.0**: Excellent data quality
- **0.7-0.9**: Good data quality
- **0.5-0.7**: Acceptable data quality
- **0.3-0.5**: Poor data quality
- **0.0-0.3**: Very poor data quality

## Configuration

### Engine Configuration:
```python
config = {
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

engine = ValidationEngine(config)
```

### Field Type Configuration:
```python
engine.add_field_type('email', 'email')
engine.add_field_type('phone', 'phone')
engine.add_field_type('birth_date', 'date', formats=['%Y-%m-%d', '%m/%d/%Y'])
engine.add_field_type('custom_field', 'custom', pattern=r'^[A-Z]{3}\d{3}$')
```

### Business Rules:
```python
def validate_business_rules(data):
    issues = []
    
    # Age validation
    if data.get('age') and data['age'] < 18:
        issues.append("Person must be 18 or older")
    
    # Email domain validation
    if data.get('email') and '@company.com' not in data['email']:
        issues.append("Must use company email domain")
    
    return len(issues) == 0, "; ".join(issues)

engine.add_business_rule(validate_business_rules, "business_rules")
```

## Advanced Features

### 1. Custom Validators

Create custom validation logic:
```python
class CustomEmailValidator:
    @classmethod
    def validate(cls, email):
        result = SyntaxValidationResult()
        
        # Custom business logic
        if '@temp-mail' in email:
            result.add_error("Temporary emails not allowed")
            
        return result

# Register custom validator
syntax_validator.add_custom_validator('enterprise_email', CustomEmailValidator)
```

### 2. Conditional Rules

Define field relationships:
```python
# If country is 'US', state field is required
checker.add_conditional_rule('country', 'US', 'state')

# If employment_type is 'fulltime', salary is required
checker.add_conditional_rule('employment_type', 'fulltime', 'salary')
```

### 3. Reference Data Integration

Validate against external datasets:
```python
# Add country codes reference
countries_df = pd.read_csv('countries.csv')
engine.add_reference_data('countries', countries_df, 'code')

# Add valid email domains
domains = ['company.com', 'subsidiary.com']
engine.add_reference_data('domains', domains, 'domain')
```

## Performance Considerations

### Batch Processing:
- Process large datasets in chunks (default: 1000 records)
- Memory-efficient for datasets exceeding RAM
- Parallel processing support (future enhancement)

### Optimization Tips:
1. **Selective Validation**: Only validate necessary fields
2. **Caching**: Cache reference datasets
3. **Early Termination**: Stop processing on critical errors
4. **Incremental Validation**: Process only changed records

### Scalability:
- **Small datasets** (< 10K records): Direct processing
- **Medium datasets** (10K-1M records): Batch processing
- **Large datasets** (> 1M records): Distributed processing (future)

## Error Handling and Troubleshooting

### Common Issues:

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Memory Issues**: Process large datasets in smaller batches
   ```python
   results = engine.validate_dataset(large_df, batch_size=500)
   ```

3. **Performance Issues**: Disable unnecessary validation stages
   ```python
   config = {
       'validation_stages': {
           'anomaly': {'enabled': False}  # Disable for speed
       }
   }
   ```

### Debugging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging
engine = ValidationEngine()
```

## API Reference

### ValidationEngine Methods:
- `validate_single_record(record, record_id=None)`: Validate one record
- `validate_dataset(data, batch_size=1000)`: Validate entire dataset
- `add_field_type(field, field_type)`: Configure field types
- `add_business_rule(rule_func, rule_name, level)`: Add business rules
- `generate_report(results, output_format='json')`: Generate reports
- `export_issues(results, file_path, format='csv')`: Export issues

### Result Objects:
- `ValidationResult`: Complete validation results
- `ValidationIssue`: Individual issue details
- `ValidationRule`: Rule configuration

## Examples

### Complete Validation Example:
```python
import pandas as pd
from main import ValidationEngine, ValidationRule, ValidationStage

# Sample data
data = pd.DataFrame([
    {
        'id': 1,
        'name': 'John Doe',
        'email': 'john@company.com',
        'phone': '+1-555-123-4567',
        'age': 30,
        'salary': 50000
    },
    {
        'id': 2,
        'name': 'Jane Smith',
        'email': 'invalid-email',
        'phone': '12345',
        'age': 150,  # Invalid
        'salary': -1000  # Invalid
    }
])

# Initialize engine
engine = ValidationEngine()

# Configure validation
engine.add_field_type('email', 'email')
engine.add_field_type('phone', 'phone')

# Add custom rule
def validate_salary(data):
    salary = data.get('salary')
    if salary is not None and salary < 0:
        return False, "Salary cannot be negative"
    return True, ""

engine.add_business_rule(validate_salary, "salary_validation")

# Validate dataset
results = engine.validate_dataset(data)

# Generate and print report
report = engine.generate_report(results, 'summary')
print(report)

# Export issues
engine.export_issues(results, 'validation_issues.csv', 'csv')
```

## Integration Patterns

### 1. Data Pipeline Integration:
```python
def validate_data_pipeline(raw_data):
    engine = ValidationEngine()
    results = engine.validate_dataset(raw_data)
    
    if results['summary']['average_quality_score'] < 0.7:
        # Trigger data quality alert
        send_alert(results)
        return None
    
    return clean_data
```

### 2. Database Integration:
```python
def validate_database_records():
    engine = ValidationEngine()
    
    # Fetch records from database
    records = db.fetch_all_records()
    
    # Validate
    results = engine.validate_dataset(records)
    
    # Update records with validation results
    for result in results['records']:
        db.update_validation_status(result['record_id'], result)
```

### 3. Real-time Validation:
```python
def validate_realtime(record):
    engine = ValidationEngine()
    result = engine.validate_single_record(record)
    
    if not result.is_valid:
        # Log invalid record
        logger.warning(f"Invalid record: {result.issues}")
        
        # Apply correction suggestions
        corrected_record = apply_suggestions(record, result)
        return corrected_record
    
    return record
```

## Future Enhancements

### Planned Features:
1. **Distributed Processing**: Support for Spark/Dask integration
2. **Real-time Streaming**: Kafka/Pulsar integration
3. **Advanced ML Models**: Custom anomaly detection models
4. **Visualization**: Interactive validation dashboards
5. **API Gateway**: RESTful API for validation services
6. **Data Profiling**: Automated data discovery and profiling
7. **Auto-correction**: Automatic issue resolution where possible

### Extension Points:
- Custom detection algorithms
- Additional data sources
- Integration with monitoring systems
- Custom reporting formats

## Conclusion

This validation engine provides a comprehensive, configurable, and scalable solution for data quality assurance. Its modular architecture allows for easy extension and customization while maintaining high performance and reliability standards.

For additional support or feature requests, please refer to the project documentation or contact the development team.