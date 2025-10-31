"""
Validation Engine Demo Script
Demonstrates all features of the multi-stage data validation engine.
"""

import sys
sys.path.insert(0, '/workspace/code/validation_engine')

import pandas as pd
from main import ValidationEngine, ValidationRule, ValidationStage, ConsistencyLevel

def demo_comprehensive_validation():
    """Comprehensive demonstration of validation engine features."""
    
    print("="*60)
    print("COMPREHENSIVE DATA VALIDATION ENGINE DEMO")
    print("="*60)
    
    # Sample dataset with various data quality issues
    sample_data = [
        {
            'id': 1,
            'name': 'John Doe',
            'email': 'john.doe@company.com',
            'phone': '+1-555-123-4567',
            'birth_date': '1985-06-15',
            'age': 38,
            'salary': 75000,
            'department': 'Engineering'
        },
        {
            'id': 2,
            'name': 'Jane Smith',
            'email': 'invalid-email-format',  # Invalid email
            'phone': '12345',  # Invalid phone
            'birth_date': '1990-13-45',  # Invalid date
            'age': 33,
            'salary': -5000,  # Invalid salary
            'department': 'Marketing'
        },
        {
            'id': 3,
            'name': 'Bob Johnson',
            'email': 'bob@subsidiary.com',
            'phone': '+44-20-7946-0958',
            'birth_date': '1978-03-22',
            'age': 45,
            'salary': 82000,
            'department': 'Sales'
        },
        {
            'id': 4,
            'name': 'Alice Brown',
            'email': 'alice.brown@company.com',
            'phone': '+1-555-123-4567',  # Duplicate phone
            'birth_date': '1992-11-08',
            'age': 31,
            'salary': 68000,
            'department': 'Engineering'
        }
    ]
    
    df = pd.DataFrame(sample_data)
    print(f"\nDataset: {len(df)} records")
    print(f"Columns: {list(df.columns)}")
    
    # Initialize validation engine
    print("\n" + "="*60)
    print("INITIALIZING VALIDATION ENGINE")
    print("="*60)
    
    engine = ValidationEngine({
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
    })
    
    # Configure field types
    print("\nConfiguring field types...")
    engine.add_field_type('email', 'email')
    engine.add_field_type('phone', 'phone')
    engine.add_field_type('birth_date', 'date')
    
    # Add validation rules
    print("\nAdding validation rules...")
    
    # Age validation rule
    def validate_age_range(data):
        age = data.get('age')
        if age is not None and (age < 18 or age > 100):
            return False, f"Age {age} is outside valid range (18-100)"
        return True, ""
    
    engine.add_business_rule(validate_age_range, "age_range_validation", ConsistencyLevel.HIGH)
    
    # Salary validation rule
    def validate_salary(data):
        salary = data.get('salary')
        if salary is not None and salary < 0:
            return False, f"Salary cannot be negative: {salary}"
        return True, ""
    
    engine.add_business_rule(validate_salary, "salary_validation", ConsistencyLevel.HIGH)
    
    # Email domain rule (must be company.com or subsidiary.com)
    def validate_email_domain(data):
        email = data.get('email')
        if email and '@company.com' not in email and '@subsidiary.com' not in email:
            return False, "Must use company email domain"
        return True, ""
    
    engine.add_business_rule(validate_email_domain, "email_domain_validation", ConsistencyLevel.MEDIUM)
    
    # Add referential integrity rules
    print("\nAdding referential integrity rules...")
    # Email requires name (through consistency checker)
    engine.consistency_checker.add_relationship('email', 'name')
    # Engineering employees need salary
    engine.consistency_checker.add_conditional_rule('department', 'Engineering', 'salary')
    
    # Run validation
    print("\n" + "="*60)
    print("RUNNING VALIDATION")
    print("="*60)
    
    results = engine.validate_dataset(df)
    
    # Display results
    print("\nVALIDATION RESULTS:")
    print(f"Total Records: {results['summary']['total_records']}")
    print(f"Valid Records: {results['summary']['valid_records']}")
    print(f"Invalid Records: {results['summary']['invalid_records']}")
    print(f"Average Quality Score: {results['summary']['average_quality_score']:.2%}")
    
    print("\nISSUES BY STAGE:")
    for stage, count in results['summary']['issues_by_stage'].items():
        if count > 0:
            print(f"  {stage.title()}: {count}")
    
    print("\nISSUES BY SEVERITY:")
    for severity, count in results['summary']['issues_by_severity'].items():
        if count > 0:
            print(f"  {severity.title()}: {count}")
    
    # Show individual record issues
    print("\n" + "="*60)
    print("INDIVIDUAL RECORD ANALYSIS")
    print("="*60)
    
    for record in results['records']:
        record_id = record['record_id']
        is_valid = record['is_valid']
        quality_score = record['quality_score']
        issues_count = len(record['issues'])
        
        status = "✓ VALID" if is_valid else "✗ INVALID"
        print(f"\nRecord {record_id}: {status}")
        print(f"  Quality Score: {quality_score:.2%}")
        print(f"  Issues Found: {issues_count}")
        
        if issues_count > 0:
            print("  Issues:")
            for issue in record['issues'][:3]:  # Show first 3 issues
                severity = issue['severity'].upper()
                field = issue['field'] or 'N/A'
                message = issue['message'][:60] + "..." if len(issue['message']) > 60 else issue['message']
                print(f"    [{severity}] {field}: {message}")
    
    # Generate detailed report
    print("\n" + "="*60)
    print("DETAILED REPORT")
    print("="*60)
    
    report = engine.generate_report(results, 'summary')
    print(report)
    
    # Export issues
    print("\n" + "="*60)
    print("EXPORTING ISSUES")
    print("="*60)
    
    try:
        engine.export_issues(results, '/tmp/validation_issues.csv', 'csv')
        print("✓ Issues exported to /tmp/validation_issues.csv")
    except Exception as e:
        print(f"✗ Export failed: {e}")
    
    # Demonstrate single record validation
    print("\n" + "="*60)
    print("SINGLE RECORD VALIDATION EXAMPLE")
    print("="*60)
    
    new_record = {
        'name': 'Test User',
        'email': 'test@company.com',
        'phone': '+1-555-999-8888',
        'birth_date': '1995-01-01',
        'age': 28,
        'salary': 55000,
        'department': 'HR'
    }
    
    single_result = engine.validate_single_record(new_record, 'test_001')
    
    print(f"\nSingle Record Validation Result:")
    print(f"  Valid: {single_result.is_valid}")
    print(f"  Quality Score: {single_result.quality_score:.2%}")
    print(f"  Issues: {len(single_result.issues)}")
    
    if single_result.issues:
        print("  Issues:")
        for issue in single_result.issues:
            print(f"    [{issue.severity}] {issue.message}")
    
    # Show quality breakdown
    print("\n" + "="*60)
    print("QUALITY SCORE BREAKDOWN")
    print("="*60)
    
    summary = results['summary']
    print(f"Completeness: {summary.get('completeness', 0):.2%}")
    print(f"Validity: {summary.get('validity', 0):.2%}")
    print(f"Consistency: {summary.get('consistency', 0):.2%}")
    print(f"Uniqueness: {summary.get('uniqueness', 0):.2%}")
    print(f"Anomaly Score: {summary.get('anomaly_score', 0):.2%}")
    
    print("\n" + "="*60)
    print("DEMO COMPLETED SUCCESSFULLY!")
    print("="*60)
    
    return results


def demo_syntax_validation_only():
    """Demonstrate syntax validation in isolation."""
    
    print("\n" + "="*60)
    print("SYNTAX VALIDATION DEMO")
    print("="*60)
    
    from syntax_validator import SyntaxValidator
    
    validator = SyntaxValidator()
    
    # Test cases
    test_cases = [
        ('user@example.com', 'email'),
        ('invalid-email', 'email'),
        ('+1-555-123-4567', 'phone'),
        ('12345', 'phone'),
        ('2023-01-15', 'date'),
        ('2023-13-45', 'date'),
        ('custom_value', 'custom', {'pattern': r'^[A-Z]{3}\d{3}$'})
    ]
    
    for value, field_type, *args in test_cases:
        kwargs = args[0] if args else {}
        result = validator.validate_field(value, field_type, **kwargs)
        
        status = "✓ VALID" if result.is_valid else "✗ INVALID"
        print(f"\n{field_type.upper()}: '{value}' -> {status}")
        
        if result.errors:
            print("  Errors:")
            for error in result.errors:
                print(f"    - {error}")
        
        if result.warnings:
            print("  Warnings:")
            for warning in result.warnings:
                print(f"    - {warning}")
        
        if result.suggestions:
            print("  Suggestions:")
            for suggestion in result.suggestions:
                print(f"    - {suggestion}")


def demo_anomaly_detection():
    """Demonstrate anomaly detection capabilities."""
    
    print("\n" + "="*60)
    print("ANOMALY DETECTION DEMO")
    print("="*60)
    
    from anomaly_detector import AnomalyDetector
    import numpy as np
    
    detector = AnomalyDetector()
    
    # Create test data with outliers
    normal_data = np.random.normal(50, 10, 100)  # Normal distribution
    outliers = np.array([10, 150, 200])  # Clear outliers
    test_data = np.concatenate([normal_data, outliers])
    
    print(f"Test data: {len(test_data)} points")
    print(f"Expected outliers: {len(outliers)}")
    
    # Detect numerical outliers
    results = detector.detect_numerical_outliers(test_data)
    
    print("\nOutlier Detection Results:")
    print(f"Z-Score outliers: {results.get('zscore', {}).get('count', 'N/A')}")
    print(f"IQR outliers: {results.get('iqr', {}).get('count', 'N/A')}")
    
    if 'isolation_forest' in results and 'error' not in results['isolation_forest']:
        print(f"Isolation Forest outliers: {results['isolation_forest'].get('count', 'N/A')}")
    else:
        print("Isolation Forest: Not available (scikit-learn required)")
    
    # Test categorical anomalies
    print("\nCategorical Anomaly Detection:")
    categories = ['A', 'B', 'C', 'A', 'B', 'A', 'X', 'Y']  # X, Y are rare
    cat_results = detector.detect_categorical_anomalies(categories)
    
    print(f"Categorical anomalies found: {cat_results['count']}")
    print(f"Anomaly indices: {cat_results['anomaly_indices']}")
    
    print("\n✓ Anomaly detection demo completed!")


if __name__ == "__main__":
    # Run comprehensive demo
    results = demo_comprehensive_validation()
    
    # Run individual component demos
    demo_syntax_validation_only()
    demo_anomaly_detection()
    
    print("\n" + "="*60)
    print("ALL DEMOS COMPLETED SUCCESSFULLY!")
    print("="*60)