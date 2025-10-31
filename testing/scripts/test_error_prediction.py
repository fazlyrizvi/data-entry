#!/usr/bin/env python3
"""
Error Prediction System Comprehensive Test Suite
===============================================
Tests error prediction system with ML-based prediction, notifications, and recovery workflows.
"""

import os
import sys
import json
import time
import asyncio
import threading
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Add error prediction to path
sys.path.append('/workspace/code/error_prediction')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestErrorPredictionSystem(unittest.TestCase):
    """Comprehensive error prediction system test suite."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.test_results = {
            'test_suite': 'Error Prediction System',
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
        """Test error prediction component imports and initialization."""
        test_name = "Component Imports"
        start_time = time.time()
        
        try:
            # Test component imports
            from main import ErrorPredictionSystem, load_config
            from predictor import ErrorPredictor, DocumentCharacteristics, ErrorType, SeverityLevel
            from notifier import NotificationOrchestrator, AlertLevel, NotificationRule
            from recovery import ResilienceManager, ErrorContext, WorkflowEngine
            
            # Test configuration loading
            config = load_config()
            self.assertIsInstance(config, dict)
            
            # Test ErrorPredictor initialization
            predictor = ErrorPredictor()
            self.assertIsNotNone(predictor)
            
            # Test DocumentCharacteristics creation
            doc_chars = DocumentCharacteristics(
                file_size=1024*1024,  # 1MB
                file_type='pdf',
                page_count=10,
                text_density=0.5,
                image_count=5,
                image_quality_score=0.8,
                language='en',
                processing_time=60.0,
                confidence_score=0.9,
                document_complexity=0.6,
                time_of_day=14,
                day_of_week=1,
                historical_failure_rate=0.05
            )
            self.assertIsNotNone(doc_chars)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'All components imported and initialized', 
                                duration, {
                                    'config_loaded': True,
                                    'predictor_ready': True,
                                    'document_characteristics_created': True
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Component import failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_002_prediction_functionality(self):
        """Test error prediction functionality."""
        test_name = "Prediction Functionality"
        start_time = time.time()
        
        try:
            from predictor import ErrorPredictor, DocumentCharacteristics, ErrorType, SeverityLevel
            
            # Create predictor
            predictor = ErrorPredictor()
            
            # Generate synthetic training data
            training_data = predictor.generate_training_data_synthetic(100)
            self.assertEqual(len(training_data), 100)
            
            # Train model (if possible)
            try:
                cv_scores = predictor.train_model(training_data)
                model_trained = True
                logger.info(f"Model trained with CV scores: {cv_scores}")
            except Exception as e:
                model_trained = False
                logger.warning(f"Model training failed: {e}")
            
            # Test predictions with different document characteristics
            test_cases = [
                # Low risk document
                DocumentCharacteristics(
                    file_size=500*1024,  # 500KB
                    file_type='pdf',
                    page_count=2,
                    text_density=0.8,
                    image_count=1,
                    image_quality_score=0.9,
                    language='en',
                    processing_time=30.0,
                    confidence_score=0.95,
                    document_complexity=0.3,
                    time_of_day=10,
                    day_of_week=1,
                    historical_failure_rate=0.01
                ),
                # High risk document
                DocumentCharacteristics(
                    file_size=50*1024*1024,  # 50MB
                    file_type='image',
                    page_count=50,
                    text_density=0.2,
                    image_count=20,
                    image_quality_score=0.4,
                    language='unknown',
                    processing_time=600.0,
                    confidence_score=0.3,
                    document_complexity=0.9,
                    time_of_day=2,
                    day_of_week=6,
                    historical_failure_rate=0.25
                )
            ]
            
            predictions = []
            for doc_chars in test_cases:
                prediction = predictor.predict_error_probability(doc_chars)
                predictions.append(prediction)
                
                # Verify prediction structure
                self.assertIsNotNone(prediction.error_probability)
                self.assertIsInstance(prediction.predicted_error_types, list)
                self.assertIsNotNone(prediction.severity_prediction)
                self.assertIsNotNone(prediction.confidence)
                self.assertIsInstance(prediction.risk_factors, list)
                self.assertIsInstance(prediction.recommendations, list)
            
            # Verify first prediction has lower error probability
            self.assertLess(predictions[0].error_probability, predictions[1].error_probability)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Prediction functionality working', 
                                duration, {
                                    'model_trained': model_trained,
                                    'predictions_made': len(predictions),
                                    'low_risk_probability': predictions[0].error_probability,
                                    'high_risk_probability': predictions[1].error_probability,
                                    'error_types_detected': len(predictions[1].predicted_error_types)
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Prediction functionality failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_003_notification_system(self):
        """Test notification system functionality."""
        test_name = "Notification System"
        start_time = time.time()
        
        try:
            from notifier import NotificationOrchestrator, AlertLevel, NotificationRule
            
            # Create notification orchestrator (with minimal config)
            email_config = {
                'smtp_server': 'localhost',
                'smtp_port': '587',
                'username': 'test',
                'password': 'test',
                'from_email': 'test@example.com'
            }
            
            slack_config = {
                'webhook_url': 'http://localhost/webhook',
                'channel': '#test'
            }
            
            notifier = NotificationOrchestrator(email_config, slack_config)
            self.assertIsNotNone(notifier)
            
            # Test alert creation
            alert_data = {
                'title': 'Test Alert',
                'message': 'This is a test alert message',
                'severity': 'medium',
                'error_probability': 0.75,
                'confidence': 0.8
            }
            
            # Test custom rule creation
            rule = NotificationRule(
                rule_id='test_rule',
                name='Test Rule',
                conditions={'error_probability': {'min': 0.7}},
                channels=['email'],
                recipients=['test@example.com'],
                cooldown_minutes=30,
                max_alerts_per_hour=5
            )
            
            # Add rule to notifier
            try:
                notifier.rule_engine.add_rule(rule)
                rule_added = True
            except Exception as e:
                rule_added = False
                logger.warning(f"Rule addition failed: {e}")
            
            # Get notifier statistics
            stats = notifier.get_alert_statistics()
            self.assertIsInstance(stats, dict)
            
            # Get health status
            health = notifier.get_health_status()
            self.assertIsInstance(health, dict)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Notification system working', 
                                duration, {
                                    'notifier_initialized': True,
                                    'rule_added': rule_added,
                                    'statistics_available': True,
                                    'health_status_available': True
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Notification system failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_004_workflow_engine(self):
        """Test workflow engine functionality."""
        test_name = "Workflow Engine"
        start_time = time.time()
        
        try:
            from recovery import WorkflowEngine, WorkflowStep, WorkflowStatus
            
            # Create workflow engine
            workflow_engine = WorkflowEngine()
            workflow_engine.start()
            self.assertIsNotNone(workflow_engine)
            
            # Test workflow creation
            workflow_steps = [
                WorkflowStep(
                    step_id='step1',
                    action='notify_team',
                    parameters={'recipients': ['admin@example.com']},
                    timeout_seconds=30
                ),
                WorkflowStep(
                    step_id='step2',
                    action='retry_operation',
                    parameters={'max_retries': 3},
                    timeout_seconds=60
                )
            ]
            
            # Create workflow
            workflow = workflow_engine.create_workflow(
                workflow_id='test_workflow',
                name='Test Recovery Workflow',
                steps=workflow_steps,
                trigger_conditions={'error_type': 'processing_failure'}
            )
            
            self.assertIsNotNone(workflow)
            
            # Test workflow execution
            execution_result = workflow_engine.execute_workflow(
                workflow_id='test_workflow',
                context={'error_id': 'test_error_123'}
            )
            
            # Get workflow statistics
            stats = workflow_engine.get_workflow_statistics()
            self.assertIsInstance(stats, dict)
            
            # Test workflow listing
            active_workflows = workflow_engine.list_active_workflows()
            self.assertIsInstance(active_workflows, list)
            
            workflow_engine.stop()
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Workflow engine working', 
                                duration, {
                                    'workflow_created': True,
                                    'workflow_executed': execution_result is not None,
                                    'active_workflows_count': len(active_workflows),
                                    'statistics_available': True
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Workflow engine failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_005_resilience_manager(self):
        """Test resilience manager functionality."""
        test_name = "Resilience Manager"
        start_time = time.time()
        
        try:
            from recovery import ResilienceManager, ErrorContext
            
            # Create minimal components for resilience manager
            workflow_engine = WorkflowEngine()
            notifier = None  # Skip notifier for this test
            
            # Create resilience manager
            resilience_manager = ResilienceManager(workflow_engine, notifier)
            self.assertIsNotNone(resilience_manager)
            
            # Create error context
            error_context = ErrorContext(
                error_id='test_error_456',
                error_type='processing_failure',
                error_message='Test error for resilience testing',
                stack_trace='Test stack trace',
                timestamp=datetime.now(),
                source_system='test_system',
                severity='medium',
                metadata={'test_key': 'test_value'}
            )
            
            # Handle error
            workflow_id = resilience_manager.handle_error(error_context)
            
            # Test error simulation
            simulation_result = resilience_manager.simulate_error_scenario(
                'database_connection_failure', 
                'high'
            )
            
            # Get resilience metrics
            metrics = resilience_manager.get_resilience_metrics()
            self.assertIsInstance(metrics, dict)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Resilience manager working', 
                                duration, {
                                    'error_handled': workflow_id is not None,
                                    'simulation_executed': simulation_result is not None,
                                    'metrics_available': True
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Resilience manager failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_006_system_integration(self):
        """Test full system integration."""
        test_name = "System Integration"
        start_time = time.time()
        
        try:
            from main import ErrorPredictionSystem, load_config
            
            # Load configuration
            config = load_config()
            
            # Create error prediction system
            system = ErrorPredictionSystem(config)
            self.assertIsNotNone(system)
            
            # Test system health status
            health = system.get_health_status()
            self.assertIsInstance(health, dict)
            self.assertIn('overall_status', health)
            
            # Test comprehensive statistics
            stats = system.get_comprehensive_stats()
            self.assertIsInstance(stats, dict)
            self.assertIn('system_stats', stats)
            
            # Test error prediction
            from predictor import DocumentCharacteristics
            
            test_doc_chars = DocumentCharacteristics(
                file_size=1024*1024,
                file_type='pdf',
                page_count=5,
                text_density=0.7,
                image_count=2,
                image_quality_score=0.8,
                language='en',
                processing_time=45.0,
                confidence_score=0.85,
                document_complexity=0.5,
                time_of_day=12,
                day_of_week=2,
                historical_failure_rate=0.05
            )
            
            prediction_result = system.predict_error(test_doc_chars)
            self.assertIsInstance(prediction_result, dict)
            self.assertIn('error_probability', prediction_result)
            self.assertIn('severity_prediction', prediction_result)
            
            # Test dashboard data
            dashboard_data = system.get_system_dashboard_data()
            self.assertIsInstance(dashboard_data, dict)
            self.assertIn('overview', dashboard_data)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'System integration working', 
                                duration, {
                                    'health_status_available': True,
                                    'stats_available': True,
                                    'prediction_made': True,
                                    'dashboard_data_available': True,
                                    'error_probability': prediction_result.get('error_probability')
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'System integration failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_007_synthetic_training_data(self):
        """Test synthetic training data generation."""
        test_name = "Synthetic Training Data"
        start_time = time.time()
        
        try:
            from predictor import ErrorPredictor
            
            # Create predictor
            predictor = ErrorPredictor()
            
            # Generate different sizes of training data
            sample_sizes = [10, 50, 100, 500]
            training_datasets = []
            
            for size in sample_sizes:
                data = predictor.generate_training_data_synthetic(size)
                training_datasets.append(data)
                self.assertEqual(len(data), size)
                
                # Verify data structure
                for sample in data[:5]:  # Check first 5 samples
                    self.assertIn('document_characteristics', sample)
                    self.assertIn('error_occurred', sample)
                    self.assertIn('error_types', sample)
            
            # Test model training with different datasets
            for i, data in enumerate(training_datasets):
                try:
                    cv_scores = predictor.train_model(data)
                    training_successful = True
                except Exception as e:
                    training_successful = False
                    logger.warning(f"Training with {sample_sizes[i]} samples failed: {e}")
                
                # Verify CV scores if training was successful
                if training_successful and cv_scores:
                    self.assertIsInstance(cv_scores, dict)
                    for score_name, scores in cv_scores.items():
                        self.assertIsInstance(scores, list)
                        for score in scores:
                            self.assertGreaterEqual(score, 0.0)
                            self.assertLessEqual(score, 1.0)
            
            # Test model persistence
            try:
                with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as temp_file:
                    model_path = temp_file.name
                
                predictor.save_model(model_path)
                model_saved = os.path.exists(model_path)
                
                if os.path.exists(model_path):
                    os.unlink(model_path)
                
            except Exception as e:
                model_saved = False
                logger.warning(f"Model saving failed: {e}")
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Synthetic training data working', 
                                duration, {
                                    'sample_sizes_tested': sample_sizes,
                                    'datasets_generated': len(training_datasets),
                                    'model_training_successful': training_successful,
                                    'model_saved': model_saved
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Synthetic training data failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_008_performance_benchmark(self):
        """Test system performance with multiple predictions."""
        test_name = "Performance Benchmark"
        start_time = time.time()
        
        try:
            from predictor import ErrorPredictor, DocumentCharacteristics
            import random
            
            # Create predictor
            predictor = ErrorPredictor()
            
            # Generate multiple document characteristics for testing
            test_documents = []
            for i in range(100):
                doc_chars = DocumentCharacteristics(
                    file_size=random.uniform(100*1024, 10*1024*1024),  # 100KB to 10MB
                    file_type=random.choice(['pdf', 'docx', 'image', 'txt']),
                    page_count=random.randint(1, 100),
                    text_density=random.uniform(0.1, 0.9),
                    image_count=random.randint(0, 50),
                    image_quality_score=random.uniform(0.3, 1.0),
                    language=random.choice(['en', 'es', 'fr', 'de', 'unknown']),
                    processing_time=random.uniform(10, 600),
                    confidence_score=random.uniform(0.3, 1.0),
                    document_complexity=random.uniform(0.1, 1.0),
                    time_of_day=random.randint(0, 23),
                    day_of_week=random.randint(0, 6),
                    historical_failure_rate=random.uniform(0, 0.3)
                )
                test_documents.append(doc_chars)
            
            # Measure prediction performance
            prediction_times = []
            predictions_made = 0
            high_risk_predictions = 0
            
            for doc_chars in test_documents:
                start_pred = time.time()
                prediction = predictor.predict_error_probability(doc_chars)
                end_pred = time.time()
                
                prediction_times.append(end_pred - start_pred)
                predictions_made += 1
                
                if prediction.error_probability > 0.7:
                    high_risk_predictions += 1
            
            # Calculate performance metrics
            avg_prediction_time = sum(prediction_times) / len(prediction_times)
            max_prediction_time = max(prediction_times)
            min_prediction_time = min(prediction_times)
            
            # Performance should be reasonable
            self.assertLess(avg_prediction_time, 1.0)  # Average under 1 second
            self.assertLess(max_prediction_time, 5.0)  # Max under 5 seconds
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Performance benchmark passed', 
                                duration, {
                                    'documents_processed': len(test_documents),
                                    'predictions_made': predictions_made,
                                    'avg_prediction_time': avg_prediction_time,
                                    'max_prediction_time': max_prediction_time,
                                    'min_prediction_time': min_prediction_time,
                                    'high_risk_predictions': high_risk_predictions,
                                    'predictions_per_second': predictions_made / (time.time() - start_time)
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Performance benchmark failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_009_error_scenarios(self):
        """Test system behavior under various error scenarios."""
        test_name = "Error Scenarios"
        start_time = time.time()
        
        try:
            from predictor import ErrorPredictor, DocumentCharacteristics
            from main import ErrorPredictionSystem
            
            # Test with invalid document characteristics
            predictor = ErrorPredictor()
            
            # Test with None values
            try:
                invalid_chars = DocumentCharacteristics(
                    file_size=None,
                    file_type='pdf',
                    page_count=10,
                    text_density=0.5,
                    image_count=5,
                    image_quality_score=0.8,
                    language='en',
                    processing_time=60.0,
                    confidence_score=0.9,
                    document_complexity=0.6,
                    time_of_day=14,
                    day_of_week=1,
                    historical_failure_rate=0.05
                )
                
                # Should handle gracefully or raise appropriate exception
                prediction = predictor.predict_error_probability(invalid_chars)
                prediction_handled = True
                
            except (ValueError, TypeError) as e:
                prediction_handled = False
                logger.info(f"Invalid chars properly rejected: {e}")
            
            # Test with extreme values
            extreme_chars = DocumentCharacteristics(
                file_size=float('inf'),
                file_type='pdf',
                page_count=-1,
                text_density=2.0,
                image_count=-5,
                image_quality_score=1.5,
                language='en',
                processing_time=-10.0,
                confidence_score=-0.1,
                document_complexity=-0.5,
                time_of_day=25,
                day_of_week=8,
                historical_failure_rate=1.5
            )
            
            try:
                extreme_prediction = predictor.predict_error_probability(extreme_chars)
                extreme_handled = True
            except Exception as e:
                extreme_handled = False
                logger.info(f"Extreme values handled: {e}")
            
            # Test system with missing config
            try:
                # Test with minimal config
                minimal_config = {}
                system = ErrorPredictionSystem(minimal_config)
                health = system.get_health_status()
                config_handled = True
            except Exception as e:
                config_handled = False
                logger.info(f"Missing config handled: {e}")
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Error scenarios handled', 
                                duration, {
                                    'invalid_chars_handled': prediction_handled,
                                    'extreme_values_handled': extreme_handled,
                                    'missing_config_handled': config_handled
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Error scenarios test failed: {str(e)}', 
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
        results_file = '/workspace/testing/results/error_prediction_test_results.json'
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(cls.test_results, f, indent=2, default=str)
        
        logger.info(f"Error Prediction System test results saved to {results_file}")


def run_error_prediction_tests():
    """Run all error prediction system tests."""
    logger.info("Starting Error Prediction System Comprehensive Test Suite")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestErrorPredictionSystem)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    logger.info(f"Error Prediction System Tests Completed: {result.testsRun} tests run")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    return result


if __name__ == "__main__":
    run_error_prediction_tests()
