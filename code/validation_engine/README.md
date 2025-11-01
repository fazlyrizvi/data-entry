# Multi-Stage Data Validation Engine

A comprehensive, AI-powered data validation engine that provides multi-stage validation including syntax validation, cross-dataset consistency checks, and anomaly detection using statistical methods and machine learning.

## Features

### 🔍 Syntax Validation
- **Email Validation**: RFC-compliant email format checking with domain validation
- **Phone Validation**: International phone number support with country code handling
- **Date Validation**: Multiple format support (ISO, US, European) with logical range checking
- **Custom Patterns**: Regex-based validation for custom data formats

### 🔗 Consistency Checking
- **Reference Data Validation**: Validate against external datasets
- **Business Rules Engine**: Configurable custom validation rules
- **Referential Integrity**: Field relationship validation
- **Data Type Consistency**: Detect mixed data types within fields

### 🤖 AI-Powered Anomaly Detection
- **Statistical Methods**: Z-score, IQR, and Median Absolute Deviation (MAD)
- **Machine Learning**: Isolation Forest, DBSCAN clustering
- **Pattern Detection**: Sequential and categorical anomaly identification
- **Correlation Analysis**: Detect breaks in expected variable relationships
- **Temporal Anomalies**: Time series outlier detection

### 🔄 Duplicate Detection
- **Exact Duplicates**: Identical record detection
- **Near Duplicates**: Fuzzy matching for similar records
- **Similarity Scoring**: Character-based similarity calculation

### 📊 Quality Scoring
- **Multi-dimensional Scoring**: Completeness, Validity, Consistency, Uniqueness, Anomaly Score
- **Weighted Quality Metrics**: Configurable importance weights
- **Overall Quality Score**: Comprehensive data quality assessment

## Quick Start

### Installation

```bash
# Install core dependencies
pip install pandas numpy scipy

# Install ML dependencies (optional, for enhanced anomaly detection)
pip install scikit-learn

# Install phone validation (optional, for enhanced phone validation)
pip install phonenumbers
```

### Basic Usage

```python
from main import ValidationEngine
import pandas as pd

# Create validation engine
engine = ValidationEngine()

# Configure field types
engine.add_field_type('email', 'email')
engine.add_field_type('phone', 'phone')
engine.add_field_type('birth_date', 'date')

# Add business rules
def validate_age(data):
    age = data.get('age')
    if age and (age < 18 or age > 120):
        return False, "Age must be between 18 and 120"
    return True, ""

engine.add_business_rule(validate_age, "age_validation")

# Sample data
data = pd.DataFrame([
    {
        'name': 'John Doe',
        'email': 'john@company.com',
        'phone': '+1-555-123-4567',
        'birth_date': '1985-06-15',
        'age': 38
    },
    {
        'name': 'Jane Smith',
        'email': 'invalid-email',  # Invalid
        'phone': '12345',  # Invalid
        'birth_date': '1990-13-45',  # Invalid
        'age': 33
    }
])

# Validate dataset
results = engine.validate_dataset(data)

# Generate report
report = engine.generate_report(results, 'summary')
print(report)
```

### Single Record Validation

```python
record = {
    'email': 'user@company.com',
    'phone': '+1-555-123-4567',
    'birth_date': '1990-01-15',
    'age': 30
}

result = engine.validate_single_record(record, 'record_001')
print(f"Valid: {result.is_valid}")
print(f"Quality Score: {result.quality_score:.2%}")
print(f"Issues: {len(result.issues)}")
```

## Project Structure

```
code/validation_engine/
├── main.py                 # Main validation orchestrator
├── syntax_validator.py     # Syntax validation components
├── consistency_checker.py  # Cross-dataset consistency checking
├── anomaly_detector.py     # AI-powered anomaly detection
├── demo.py                 # Comprehensive demo script
└── requirements.txt        # Project dependencies

docs/
└── validation_implementation.md  # Detailed documentation
```

## Architecture

The validation engine follows a modular architecture:

1. **Syntax Validator** (`syntax_validator.py`)
   - Email, phone, date format validation
   - Custom regex pattern support
   - Standardized validation results

2. **Consistency Checker** (`consistency_checker.py`)
   - Reference data validation
   - Business rule execution
   - Referential integrity checking
   - Type consistency detection

3. **Anomaly Detector** (`anomaly_detector.py`)
   - Statistical outlier detection
   - ML-based anomaly detection
   - Pattern and correlation analysis
   - Temporal anomaly detection

4. **Main Orchestrator** (`main.py`)
   - Multi-stage validation coordination
   - Quality score calculation
   - Report generation
   - Issue export capabilities

## Configuration

### Engine Configuration

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
    }
}

engine = ValidationEngine(config)
```

### Business Rules

```python
def custom_validation_rule(data):
    """Custom business logic validation."""
    issues = []
    
    # Example: Age and experience consistency
    age = data.get('age')
    years_experience = data.get('years_experience')
    
    if age and years_experience and years_experience > age - 15:
        issues.append("Years of experience exceeds reasonable limit for age")
    
    return len(issues) == 0, "; ".join(issues)

engine.add_business_rule(custom_validation_rule, "experience_validation")
```

### Reference Data Integration

```python
# Add reference datasets
countries_df = pd.read_csv('countries.csv')
engine.add_reference_data('countries', countries_df, 'country_code')

# Add conditional rules
engine.add_conditional_rule('country', 'US', 'state')  # US requires state
engine.add_conditional_rule('employment_type', 'fulltime', 'salary')
```

## Quality Scoring

The engine calculates a comprehensive quality score across multiple dimensions:

- **Completeness**: Percentage of non-null values
- **Validity**: Percentage of syntactically valid values  
- **Consistency**: Cross-field and business rule compliance
- **Uniqueness**: Absence of duplicate records
- **Anomaly Score**: Measure of unusual patterns

### Score Interpretation

| Score Range | Quality Level |
|-------------|---------------|
| 0.9 - 1.0   | Excellent     |
| 0.7 - 0.9   | Good          |
| 0.5 - 0.7   | Acceptable    |
| 0.3 - 0.5   | Poor          |
| 0.0 - 0.3   | Very Poor     |

## Advanced Features

### Conditional Validation Rules

```python
# Require salary for full-time employees
engine.add_conditional_rule('employment_type', 'fulltime', 'salary')

# Require state for US addresses
engine.add_conditional_rule('country', 'US', 'state')
```

### Custom Validators

```python
class CustomEmailValidator:
    @classmethod
    def validate(cls, email):
        result = SyntaxValidationResult()
        
        # Custom business logic
        if '@temp-mail' in email:
            result.add_error("Temporary emails not allowed")
            
        return result

syntax_validator.add_custom_validator('enterprise_email', CustomEmailValidator)
```

### Batch Processing

```python
# Process large datasets efficiently
results = engine.validate_dataset(large_dataframe, batch_size=1000)

# Export issues for analysis
engine.export_issues(results, 'validation_issues.csv', 'csv')
```

## Running the Demo

```bash
cd code/validation_engine
python demo.py
```

The demo showcases:
- Comprehensive validation workflow
- Individual component testing
- Syntax validation examples
- Anomaly detection demonstrations
- Report generation
- Issue export functionality

## API Reference

### ValidationEngine

Main orchestrator class for data validation.

**Methods:**
- `validate_single_record(record, record_id=None)`: Validate one record
- `validate_dataset(data, batch_size=1000)`: Validate entire dataset
- `add_field_type(field, field_type)`: Configure field types
- `add_business_rule(rule_func, rule_name, level)`: Add business rules
- `generate_report(results, output_format='json')`: Generate reports
- `export_issues(results, file_path, format='csv')`: Export issues

### Result Objects

- `ValidationResult`: Complete validation results
- `ValidationIssue`: Individual issue details
- `ValidationRule`: Rule configuration

## Dependencies

### Required
- pandas >= 1.5.0
- numpy >= 1.21.0
- scipy >= 1.9.0

### Optional (for enhanced features)
- scikit-learn >= 1.1.0 (ML-based anomaly detection)
- phonenumbers >= 8.12.0 (enhanced phone validation)
- fuzzywuzzy >= 0.18.0 (advanced string similarity)

## Performance

### Scalability
- **Small datasets** (< 10K records): Direct processing
- **Medium datasets** (10K-1M records): Batch processing
- **Large datasets** (> 1M records): Distributed processing

### Optimization Tips
1. Disable unnecessary validation stages for speed
2. Process large datasets in smaller batches
3. Cache reference datasets
4. Use incremental validation for changing data

## Documentation

For detailed documentation, see [docs/validation_implementation.md](docs/validation_implementation.md)

## License

This project is provided as-is for educational and development purposes.

## Support

For issues, feature requests, or questions, please refer to the documentation or create an issue in the project repository.