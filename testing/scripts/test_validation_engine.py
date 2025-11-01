#!/usr/bin/env python3
"""
Validation Engine Comprehensive Test Suite
==========================================
Tests data validation engine with syntax, consistency, anomaly, and duplicate detection.
"""

import os
import sys
import json
import time
import pandas as pd
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Add validation engine to path
sys.path.append('/workspace/code/validation_engine')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestValidationEngine(unittest.TestCase):
    """Comprehensive validation engine test suite."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.test_results = {
            'test_suite': 'Validation Engine',
            'start_time': datetime.now().isoformat(),
            'tests': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'errors': []
            }
        }
        
    def _add_test_result(self, test_name: str, status: str, message: str, 
                        duration: float, details: Dict = None):
        """Add test result to the test suite results."""
        result = {
            'test_name': test_name,
            'status': status,
            'message': message,
            'duration': duration,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        self.test_results['tests'].append(result)
        self.test_results['summary']['total'] += 1
        
        if status == 'PASSED':
            self.test_results['summary']['passed'] += 1
            logger.info(f"✓ {test_name}: {message}")
        else:
            self.test_results['summary']['failed'] += 1
            self.test_results['summary']['errors'].append({
                'test': test_name,
                'error': message
            })
            logger.error(f"✗ {test_name}: {message}")
    
    def test_001_component_imports(self):
        """Test validation component imports and initialization."""
        test_name = "Component Imports"
        start_time = time.time()
        
        try:
            # Test component imports
            from main import ValidationEngine, ValidationRule, ValidationStage
            from syntax_validator import SyntaxValidator
            from consistency_checker import ConsistencyChecker
            from anomaly_detector import AnomalyDetector
            from duplicate_detector import DuplicateDetector
            
            # Test ValidationEngine initialization
            engine = ValidationEngine()
            self.assertIsNotNone(engine)
            
            # Test individual components
            syntax_validator = SyntaxValidator()
            self.assertIsNotNone(syntax_validator)
            
            consistency_checker = ConsistencyChecker()
            self.assertIsNotNone(consistency_checker)
            
            anomaly_detector = AnomalyDetector()
            self.assertIsNotNone(anomaly_detector)
            
            duplicate_detector = DuplicateDetector()
            self.assertIsNotNone(duplicate_detector)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'All components imported and initialized', 
                                duration, {
                                    'validation_engine_ready': True,
                                    'syntax_validator_ready': True,
                                    'consistency_checker_ready': True,
                                    'anomaly_detector_ready': True,
                                    'duplicate_detector_ready': True
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Component import failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_002_syntax_validation(self):
        """Test syntax validation functionality."""
        test_name = "Syntax Validation"
        start_time = time.time()
        
        try:
            from syntax_validator import SyntaxValidator
            
            # Create validator
            validator = SyntaxValidator()
            
            # Test data with various syntax issues
            test_record = {
                'email': 'invalid-email',  # Invalid email
                'phone': '123',           # Invalid phone
                'date_joined': '2023-13-45',  # Invalid date
                'age': -5,                # Invalid age
                'salary': 999999,         # Potential outlier
                'name': 'John Doe',       # Valid
                'status': 'active'        # Valid
            }
            
            # Define field types
            field_types = {
                'email': 'email',
                'phone': 'phone',
                'date_joined': 'date',
                'age': 'integer',
                'salary': 'decimal',
                'name': 'string',
                'status': 'string'
            }
            
            # Validate syntax
            results = validator.validate_dataset(test_record, field_types)
            
            # Verify results
            self.assertIsInstance(results, dict)
            
            # Check that invalid fields are detected
            invalid_fields = [field for field, result in results.items() if not result.is_valid]
            self.assertGreater(len(invalid_fields), 0)
            
            # Verify specific issues are found
            issues_found = []
            for field, result in results.items():
                if not result.is_valid:
                    issues_found.extend(result.errors)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Syntax validation working', 
                                duration, {
                                    'fields_validated': len(results),
                                    'invalid_fields': invalid_fields,
                                    'total_errors': len(issues_found)
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Syntax validation failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_003_consistency_checking(self):
        """Test data consistency checking."""
        test_name = "Consistency Checking"
        start_time = time.time()
        
        try:
            from consistency_checker import ConsistencyChecker, ConsistencyLevel
            
            # Create checker
            checker = ConsistencyChecker()
            
            # Add reference data
            reference_data = pd.DataFrame([
                {'department': 'Sales', 'manager': 'John Smith'},
                {'department': 'Engineering', 'manager': 'Jane Doe'},
                {'department': 'Marketing', 'manager': 'Mike Johnson'}
            ])
            
            checker.add_reference_data('departments', reference_data, 'department')
            
            # Test record with consistency issues
            test_record = {
                'name': 'Alice Brown',
                'email': 'alice@company.com',
                'department': 'NonExistentDept',  # Not in reference
                'manager': 'John Smith',  # Valid reference
                'start_date': '2023-01-15',
                'salary': 50000,
                'status': 'active'
            }
            
            # Check consistency
            violations = checker.validate_single_record(test_record)
            
            # Verify results
            self.assertIsInstance(violations, list)
            
            # Should find at least one violation
            dept_violations = [v for v in violations if 'department' in v.message.lower()]
            self.assertGreater(len(dept_violations), 0)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Consistency checking working', 
                                duration, {
                                    'violations_found': len(violations),
                                    'reference_data_loaded': len(reference_data),
                                    'department_violations': len(dept_violations)
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Consistency checking failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_004_anomaly_detection(self):
        """Test anomaly detection capabilities."""
        test_name = "Anomaly Detection"
        start_time = time.time()
        
        try:
            from anomaly_detector import AnomalyDetector
            
            # Create detector
            detector = AnomalyDetector()
            
            # Create test dataset
            test_data = pd.DataFrame([
                {'age': 25, 'salary': 45000, 'experience': 2},
                {'age': 30, 'salary': 55000, 'experience': 5},
                {'age': 28, 'salary': 50000, 'experience': 4},
                {'age': 35, 'salary': 75000, 'experience': 8},
                {'age': 200, 'salary': 10000000, 'experience': 150},  # Anomaly
                {'age': -5, 'salary': 25000, 'experience': 0}         # Another anomaly
            ])
            
            # Detect anomalies
            anomalies = detector.detect_dataset_anomalies(test_data)
            
            # Verify results
            self.assertIsInstance(anomalies, dict)
            self.assertIn('anomaly_score', anomalies)
            
            # Should detect anomalies
            self.assertGreater(anomalies['anomaly_score'], 0)
            
            # Test single record anomaly detection
            single_record = test_data.iloc[-1].to_dict()
            record_anomaly = detector.detect_record_anomaly(single_record, test_data)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Anomaly detection working', 
                                duration, {
                                    'anomaly_score': anomalies['anomaly_score'],
                                    'anomalies_detected': len(anomalies.get('anomalies', [])),
                                    'single_record_anomaly': record_anomaly
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Anomaly detection failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_005_duplicate_detection(self):
        """Test duplicate detection functionality."""
        test_name = "Duplicate Detection"
        start_time = time.time()
        
        try:
            from main import DuplicateDetector
            
            # Create detector
            detector = DuplicateDetector(similarity_threshold=0.8)
            
            # Create test dataset with duplicates
            test_data = pd.DataFrame([
                {'name': 'John Doe', 'email': 'john@example.com', 'phone': '555-1234'},
                {'name': 'Jane Smith', 'email': 'jane@example.com', 'phone': '555-5678'},
                {'name': 'John Doe', 'email': 'john@example.com', 'phone': '555-1234'},  # Exact duplicate
                {'name': 'Jon Doe', 'email': 'john@example.com', 'phone': '555-1234'},   # Near duplicate
                {'name': 'Bob Wilson', 'email': 'bob@example.com', 'phone': '555-9999'}
            ])
            
            # Detect exact duplicates
            exact_duplicates = detector.detect_exact_duplicates(test_data)
            
            # Verify exact duplicates
            self.assertEqual(exact_duplicates['count'], 1)  # Should find 1 duplicate
            self.assertEqual(exact_duplicates['indices'], [2])  # Index 2 is duplicate of index 0
            
            # Detect near duplicates
            near_duplicates = detector.detect_near_duplicates(test_data, ['name', 'email'])
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Duplicate detection working', 
                                duration, {
                                    'exact_duplicates_count': exact_duplicates['count'],
                                    'near_duplicates_count': near_duplicates['count'],
                                    'exact_duplicates_indices': exact_duplicates['indices']
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Duplicate detection failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_006_full_validation_pipeline(self):
        """Test complete validation pipeline."""
        test_name = "Full Validation Pipeline"
        start_time = time.time()
        
        try:
            from main import ValidationEngine, ValidationRule, ValidationStage
            
            # Create validation engine
            engine = ValidationEngine()
            
            # Add field types
            field_types = {
                'email': 'email',
                'phone': 'phone',
                'date_joined': 'date',
                'age': 'integer',
                'salary': 'decimal',
                'name': 'string',
                'department': 'string'
            }
            
            for field, field_type in field_types.items():
                engine.add_field_type(field, field_type)
            
            # Add business rules
            def validate_age_range(age):
                return 0 <= age <= 120, "Age must be between 0 and 120"
            
            engine.add_business_rule(validate_age_range, "age_range_validation")
            
            # Add reference data
            departments = pd.DataFrame([
                {'department': 'Sales'},
                {'department': 'Engineering'},
                {'department': 'Marketing'}
            ])
            engine.add_reference_data('departments', departments, 'department')
            
            # Test records
            test_records = [
                {
                    'name': 'John Doe',
                    'email': 'john@example.com',
                    'phone': '555-123-4567',
                    'date_joined': '2023-01-15',
                    'age': 30,
                    'salary': 50000,
                    'department': 'Sales'
                },
                {
                    'name': 'Jane Smith',
                    'email': 'invalid-email',  # Invalid
                    'phone': '123',           # Invalid
                    'date_joined': '2023-13-45',  # Invalid
                    'age': -5,                # Invalid
                    'salary': 999999,         # Outlier
                    'department': 'NonExistentDept'  # Not in reference
                }
            ]
            
            # Validate dataset
            results = engine.validate_dataset(test_records)
            
            # Verify results structure
            self.assertIsInstance(results, dict)
            self.assertIn('records', results)
            self.assertIn('summary', results)
            
            # Check summary statistics
            summary = results['summary']
            self.assertEqual(summary['total_records'], len(test_records))
            self.assertGreater(summary['total_issues'], 0)
            self.assertGreater(summary['invalid_records'], 0)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Full validation pipeline working', 
                                duration, {
                                    'records_validated': len(test_records),
                                    'valid_records': summary['valid_records'],
                                    'invalid_records': summary['invalid_records'],
                                    'total_issues': summary['total_issues'],
                                    'average_quality_score': summary['average_quality_score']
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Full validation pipeline failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_007_custom_validation_rules(self):
        """Test custom validation rules."""
        test_name = "Custom Validation Rules"
        start_time = time.time()
        
        try:
            from main import ValidationEngine, ValidationRule, ValidationStage
            
            # Create validation engine
            engine = ValidationEngine()
            
            # Create custom validation rule
            custom_rule = ValidationRule(
                name="salary_range_check",
                stage=ValidationStage.SYNTAX,
                field="salary",
                rule_type="range",
                parameters={"min": 20000, "max": 200000},
                weight=1.0,
                severity="high"
            )
            
            # Add rule
            engine.add_validation_rule(custom_rule)
            
            # Test records with different salary ranges
            test_records = [
                {'name': 'Valid Person', 'salary': 50000},  # Valid
                {'name': 'Low Salary', 'salary': 15000},    # Below minimum
                {'name': 'High Salary', 'salary': 250000}   # Above maximum
            ]
            
            # Validate each record
            for i, record in enumerate(test_records):
                result = engine.validate_single_record(record, f"record_{i}")
                # Should detect salary issues for records 1 and 2
                if i > 0:
                    self.assertFalse(result.is_valid)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Custom validation rules working', 
                                duration, {
                                    'custom_rules_added': 1,
                                    'rules_in_engine': len(engine.rules)
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Custom validation rules failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_008_data_quality_scoring(self):
        """Test data quality scoring system."""
        test_name = "Data Quality Scoring"
        start_time = time.time()
        
        try:
            from main import DataQualityScorer
            import pandas as pd
            
            # Create scorer
            scorer = DataQualityScorer()
            
            # Create test dataset
            test_data = pd.DataFrame([
                {'name': 'John', 'email': 'john@example.com', 'age': 30},
                {'name': 'Jane', 'email': None, 'age': 25},  # Missing email
                {'name': None, 'email': 'bob@example.com', 'age': 35},  # Missing name
                {'name': 'Alice', 'email': 'alice@example.com', 'age': None}  # Missing age
            ])
            
            # Test completeness calculation
            completeness = scorer.calculate_completeness(test_data)
            expected_completeness = 10 / 12  # 10 non-null values out of 12 total
            self.assertAlmostEqual(completeness, expected_completeness, places=2)
            
            # Test validity calculation with mock syntax results
            syntax_results = {
                'name': {'is_valid': True},
                'email': {'is_valid': False},
                'age': {'is_valid': True}
            }
            
            validity = scorer.calculate_validity(syntax_results)
            expected_validity = 2 / 3  # 2 valid out of 3 fields
            self.assertAlmostEqual(validity, expected_validity, places=2)
            
            # Test overall quality calculation
            overall_quality = scorer.calculate_overall_quality(
                completeness=0.8,
                validity=0.7,
                consistency=0.9,
                uniqueness=0.95,
                anomaly_score=0.1
            )
            
            # Overall quality should be reasonable
            self.assertGreaterEqual(overall_quality, 0.0)
            self.assertLessEqual(overall_quality, 1.0)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Data quality scoring working', 
                                duration, {
                                    'completeness_score': completeness,
                                    'validity_score': validity,
                                    'overall_quality_score': overall_quality
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Data quality scoring failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_009_report_generation(self):
        """Test validation report generation."""
        test_name = "Report Generation"
        start_time = time.time()
        
        try:
            from main import ValidationEngine
            
            # Create validation engine
            engine = ValidationEngine()
            
            # Add field types
            engine.add_field_type('email', 'email')
            engine.add_field_type('age', 'integer')
            
            # Test records
            test_records = [
                {'name': 'John', 'email': 'john@example.com', 'age': 30},
                {'name': 'Jane', 'email': 'invalid-email', 'age': -5}
            ]
            
            # Validate dataset
            results = engine.validate_dataset(test_records)
            
            # Test JSON report generation
            json_report = engine.generate_report(results, 'json')
            self.assertIsInstance(json_report, str)
            
            # Verify it's valid JSON
            import json
            parsed_json = json.loads(json_report)
            self.assertIsInstance(parsed_json, dict)
            
            # Test summary report generation
            summary_report = engine.generate_report(results, 'summary')
            self.assertIsInstance(summary_report, str)
            self.assertIn('Total Records:', summary_report)
            self.assertIn('Valid Records:', summary_report)
            
            # Test issues export
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as csv_file:
                csv_path = csv_file.name
            
            try:
                engine.export_issues(results, csv_path, 'csv')
                self.assertTrue(os.path.exists(csv_path))
                
                # Verify CSV content
                import pandas as pd
                exported_issues = pd.read_csv(csv_path)
                self.assertGreater(len(exported_issues), 0)
                
            finally:
                if os.path.exists(csv_path):
                    os.unlink(csv_path)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Report generation working', 
                                duration, {
                                    'json_report_generated': True,
                                    'summary_report_generated': True,
                                    'csv_export_working': True,
                                    'report_content_length': len(json_report)
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Report generation failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_010_performance_test(self):
        """Test validation engine performance with large datasets."""
        test_name = "Performance Test"
        start_time = time.time()
        
        try:
            from main import ValidationEngine
            
            # Create validation engine
            engine = ValidationEngine()
            
            # Add field types
            field_types = {
                'name': 'string',
                'email': 'email',
                'age': 'integer',
                'salary': 'decimal',
                'department': 'string'
            }
            
            for field, field_type in field_types.items():
                engine.add_field_type(field, field_type)
            
            # Create large test dataset
            import random
            import string
            
            large_dataset = []
            for i in range(1000):
                record = {
                    'name': f"Person_{i}",
                    'email': f"person_{i}@example.com",
                    'age': random.randint(18, 80),
                    'salary': random.randint(30000, 150000),
                    'department': random.choice(['Sales', 'Engineering', 'Marketing', 'HR'])
                }
                
                # Add some intentional issues
                if i % 20 == 0:  # 5% with email issues
                    record['email'] = 'invalid-email'
                if i % 25 == 0:  # 4% with age issues
                    record['age'] = -10
                
                large_dataset.append(record)
            
            # Measure validation time
            start_validation = time.time()
            results = engine.validate_dataset(large_dataset, batch_size=100)
            end_validation = time.time()
            
            validation_time = end_validation - start_validation
            
            # Verify results
            self.assertEqual(results['summary']['total_records'], 1000)
            self.assertGreater(results['summary']['total_issues'], 0)
            
            # Performance should be reasonable
            self.assertLess(validation_time, 30.0)  # Should validate 1000 records in under 30 seconds
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Performance test passed', 
                                duration, {
                                    'dataset_size': 1000,
                                    'validation_time': validation_time,
                                    'records_per_second': 1000 / validation_time,
                                    'total_issues_found': results['summary']['total_issues']
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Performance test failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    @classmethod
    def tearDownClass(cls):
        """Save test results."""
        cls.test_results['end_time'] = datetime.now().isoformat()
        cls.test_results['duration'] = (
            datetime.fromisoformat(cls.test_results['end_time']) - 
            datetime.fromisoformat(cls.test_results['start_time'])
        ).total_seconds()
        
        # Save results to file
        results_file = '/workspace/testing/results/validation_engine_test_results.json'
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(cls.test_results, f, indent=2, default=str)
        
        logger.info(f"Validation Engine test results saved to {results_file}")


def run_validation_tests():
    """Run all validation engine tests."""
    logger.info("Starting Validation Engine Comprehensive Test Suite")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestValidationEngine)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    logger.info(f"Validation Engine Tests Completed: {result.testsRun} tests run")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    return result


if __name__ == "__main__":
    run_validation_tests()
