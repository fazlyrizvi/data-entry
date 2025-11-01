"""
Example usage of the Error Prediction and Notification System
Demonstrates key features and integration patterns
"""

import sys
import os
import time
import json
from datetime import datetime

# Add the error_prediction module to path
sys.path.append('/workspace/code/error_prediction')

from predictor import ErrorPredictor, DocumentCharacteristics, ErrorType, SeverityLevel
from notifier import NotificationOrchestrator
from recovery import ResilienceManager, ErrorContext, WorkflowEngine
from main import ErrorPredictionSystem, load_config

def example_basic_prediction():
    """Example 1: Basic error prediction"""
    print("\n=== Example 1: Basic Error Prediction ===")
    
    # Create predictor
    predictor = ErrorPredictor()
    
    # Create sample document characteristics
    doc_chars = DocumentCharacteristics(
        file_size=75 * 1024 * 1024,  # 75MB
        file_type="pdf",
        page_count=30,
        text_density=0.4,
        image_count=15,
        image_quality_score=0.6,
        language="en",
        processing_time=450,  # 7.5 minutes
        confidence_score=0.65,
        document_complexity=0.8,
        time_of_day=14,  # 2 PM (peak time)
        day_of_week=1,   # Tuesday
        historical_failure_rate=0.15
    )
    
    # Make prediction
    prediction = predictor.predict_error_probability(doc_chars)
    
    print(f"Error Probability: {prediction.error_probability:.2%}")
    print(f"Predicted Severity: {prediction.severity_prediction.value}")
    print(f"Confidence: {prediction.confidence:.2%}")
    print(f"Top Error Types:")
    for error_type, prob in prediction.predicted_error_types[:3]:
        print(f"  - {error_type.value}: {prob:.2%}")
    print(f"Risk Factors: {prediction.risk_factors}")
    print(f"Recommendations: {prediction.recommendations}")

def example_training_and_model_save():
    """Example 2: Training and saving model"""
    print("\n=== Example 2: Model Training ===")
    
    predictor = ErrorPredictor()
    
    # Generate synthetic training data
    print("Generating synthetic training data...")
    training_data = predictor.generate_training_data_synthetic(500)
    
    # Train model
    print("Training model...")
    cv_scores = predictor.train_model(training_data)
    
    print(f"Cross-validation scores:")
    for model, score in cv_scores.items():
        print(f"  - {model}: {score:.3f}")
    
    # Save model
    model_path = "/workspace/code/error_prediction/trained_model.pkl"
    predictor.save_model(model_path)
    print(f"Model saved to: {model_path}")
    
    # Get prediction statistics
    stats = predictor.get_prediction_statistics()
    print(f"Prediction statistics: {stats}")

def example_notification_system():
    """Example 3: Notification system (simulation)"""
    print("\n=== Example 3: Notification System ===")
    
    # Mock configuration for demonstration
    email_config = {
        'smtp_server': 'smtp.example.com',
        'smtp_port': '587',
        'username': 'test@example.com',
        'password': 'password',
        'from_email': 'alerts@example.com'
    }
    
    slack_config = {
        'webhook_url': 'https://hooks.slack.com/test',
        'channel': '#alerts'
    }
    
    # Initialize notification system
    notifier = NotificationOrchestrator(email_config, slack_config)
    
    # Create sample alert
    alert_data = {
        'title': 'High Error Risk Detected',
        'message': 'Document processing error probability exceeded threshold',
        'severity': 'high',
        'error_probability': 0.85,
        'document_size': '75MB',
        'processing_time': '450s'
    }
    
    print(f"Alert created: {alert_data['title']}")
    print(f"Triggering notification...")
    
    # Note: This would normally send actual notifications
    # For demo purposes, we'll just show the structure
    print(f"Alert would be sent to configured recipients")
    print(f"Alert data: {json.dumps(alert_data, indent=2)}")
    
    # Get statistics
    stats = notifier.get_alert_statistics()
    print(f"Notification statistics: {stats}")

def example_recovery_workflow():
    """Example 4: Recovery workflow"""
    print("\n=== Example 4: Recovery Workflow ===")
    
    # Create workflow engine
    workflow_engine = WorkflowEngine()
    
    # Create error context
    error_context = ErrorContext(
        error_id="err_001",
        error_type="processing_timeout",
        error_message="Document processing exceeded timeout threshold",
        stack_trace=None,
        timestamp=datetime.now(),
        source_system="document_processor",
        severity="high",
        metadata={'document_id': 'doc_123', 'timeout_seconds': 300}
    )
    
    # Create simple recovery workflow
    from recovery import RecoveryStep, RecoveryAction
    
    recovery_steps = [
        RecoveryStep(
            step_id="retry_with_extended_timeout",
            action=RecoveryAction.RETRY,
            description="Retry with extended timeout",
            parameters={'timeout': 600, 'max_retries': 2},
            max_retries=2
        ),
        RecoveryStep(
            step_id="fallback_processor",
            action=RecoveryAction.FALLBACK,
            description="Switch to backup processor",
            parameters={'backup_service': 'processor_b'}
        ),
        RecoveryStep(
            step_id="escalate_to_support",
            action=RecoveryAction.ESCALATE,
            description="Escalate to support team",
            parameters={'escalation_level': 'l2_support'}
        )
    ]
    
    # Create workflow
    workflow_id = workflow_engine.create_workflow(error_context, recovery_steps)
    print(f"Recovery workflow created: {workflow_id}")
    
    # Start workflow engine (in background)
    workflow_engine.start()
    
    # Simulate some processing time
    time.sleep(2)
    
    # Get workflow status
    status = workflow_engine.get_workflow_status(workflow_id)
    print(f"Workflow status: {status}")
    
    # Get statistics
    stats = workflow_engine.get_workflow_statistics()
    print(f"Workflow statistics: {stats}")
    
    # Stop workflow engine
    workflow_engine.stop()

def example_system_integration():
    """Example 5: Full system integration"""
    print("\n=== Example 5: Full System Integration ===")
    
    # Load configuration
    config = load_config()
    
    # Update config for demo (without real credentials)
    config['notifications']['email']['username'] = 'demo@example.com'
    config['notifications']['email']['password'] = 'demo'
    config['notifications']['slack']['webhook_url'] = 'https://hooks.slack.com/demo'
    
    # Create system
    system = ErrorPredictionSystem(config)
    
    print("System created. Starting components...")
    
    # Start system
    system.start()
    
    # Simulate some document processing
    time.sleep(5)
    
    # Get dashboard data
    dashboard_data = system.get_system_dashboard_data()
    print(f"System Dashboard Data:")
    print(f"  Status: {dashboard_data['overview']['status']}")
    print(f"  Total Predictions: {dashboard_data['overview']['total_predictions']}")
    print(f"  Errors Detected: {dashboard_data['overview']['errors_detected']}")
    print(f"  Active Workflows: {dashboard_data['active_workflows']}")
    
    # Get health status
    health = system.get_health_status()
    print(f"System Health: {health['overall_status']}")
    
    # Shutdown system
    print("Shutting down system...")
    system.shutdown()
    print("System stopped")

def example_document_processing_simulation():
    """Example 6: Simulate document processing pipeline"""
    print("\n=== Example 6: Document Processing Simulation ===")
    
    # Simulate processing various documents
    test_documents = [
        {
            'name': 'Small PDF',
            'chars': DocumentCharacteristics(
                file_size=2 * 1024 * 1024,  # 2MB
                file_type="pdf",
                page_count=5,
                text_density=0.8,
                image_count=2,
                image_quality_score=0.9,
                language="en",
                processing_time=45,
                confidence_score=0.95,
                document_complexity=0.3,
                time_of_day=10,
                day_of_week=1,
                historical_failure_rate=0.02
            )
        },
        {
            'name': 'Large Complex Document',
            'chars': DocumentCharacteristics(
                file_size=120 * 1024 * 1024,  # 120MB
                file_type="pdf",
                page_count=100,
                text_density=0.2,
                image_count=50,
                image_quality_score=0.4,
                language="en",
                processing_time=900,  # 15 minutes
                confidence_score=0.5,
                document_complexity=0.9,
                time_of_day=14,  # Peak time
                day_of_week=1,
                historical_failure_rate=0.25
            )
        },
        {
            'name': 'Image-Heavy Document',
            'chars': DocumentCharacteristics(
                file_size=80 * 1024 * 1024,  # 80MB
                file_type="pdf",
                page_count=20,
                text_density=0.1,
                image_count=80,
                image_quality_score=0.3,
                language="en",
                processing_time=600,  # 10 minutes
                confidence_score=0.6,
                document_complexity=0.8,
                time_of_day=16,
                day_of_week=2,
                historical_failure_rate=0.18
            )
        }
    ]
    
    predictor = ErrorPredictor()
    
    for doc in test_documents:
        print(f"\nProcessing: {doc['name']}")
        prediction = predictor.predict_error_probability(doc['chars'])
        
        print(f"  Error Probability: {prediction.error_probability:.2%}")
        print(f"  Severity: {prediction.severity_prediction.value}")
        print(f"  Risk Level: {'HIGH' if prediction.error_probability > 0.7 else 'MEDIUM' if prediction.error_probability > 0.4 else 'LOW'}")
        
        if prediction.risk_factors:
            print(f"  Risk Factors:")
            for factor in prediction.risk_factors:
                print(f"    - {factor}")
        
        if prediction.recommendations:
            print(f"  Recommendations:")
            for rec in prediction.recommendations:
                print(f"    - {rec}")

def main():
    """Run all examples"""
    print("Error Prediction and Notification System - Examples")
    print("=" * 60)
    
    try:
        # Run examples
        example_basic_prediction()
        example_training_and_model_save()
        example_notification_system()
        example_recovery_workflow()
        example_document_processing_simulation()
        example_system_integration()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("\nKey Features Demonstrated:")
        print("✓ Machine learning error prediction")
        print("✓ Model training and persistence")
        print("✓ Multi-channel notification system")
        print("✓ Automated recovery workflows")
        print("✓ System integration and monitoring")
        print("✓ Document processing simulation")
        
    except Exception as e:
        print(f"\nError running examples: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()