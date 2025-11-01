"""
Error Prediction and Notification System
Main orchestration module that integrates prediction, notification, and recovery components.
"""

import asyncio
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import logging
import signal
import sys

from predictor import ErrorPredictor, DocumentCharacteristics, ErrorType, SeverityLevel
from notifier import NotificationOrchestrator, AlertLevel, NotificationRule
from recovery import ResilienceManager, ErrorContext, WorkflowEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ErrorPredictionSystem:
    """Main system orchestrator"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_running = False
        self.start_time = None
        
        # Initialize components
        self.predictor = ErrorPredictor()
        self.notifier = None
        self.workflow_engine = None
        self.resilience_manager = None
        
        # Statistics tracking
        self.system_stats = {
            'predictions_made': 0,
            'errors_detected': 0,
            'alerts_sent': 0,
            'workflows_executed': 0,
            'workflows_successful': 0,
            'uptime_seconds': 0
        }
        
        # Control flags
        self.should_stop = False
        
        # Initialize the system
        self._initialize_components()
        self._setup_signal_handlers()
    
    def _initialize_components(self):
        """Initialize all system components"""
        try:
            # Initialize notification system
            if self.config.get('notifications'):
                email_config = self.config['notifications'].get('email', {})
                slack_config = self.config['notifications'].get('slack', {})
                
                self.notifier = NotificationOrchestrator(email_config, slack_config)
                self.notifier.start()
                logger.info("Notification system initialized")
            
            # Initialize workflow engine
            self.workflow_engine = WorkflowEngine(notifier=self.notifier)
            self.workflow_engine.start()
            logger.info("Workflow engine initialized")
            
            # Initialize resilience manager
            self.resilience_manager = ResilienceManager(
                self.workflow_engine, 
                notifier=self.notifier
            )
            logger.info("Resilience manager initialized")
            
            # Initialize predictor
            if self.config.get('training_data_path'):
                self._initialize_predictor()
            else:
                logger.info("Using heuristic prediction (no training data)")
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {str(e)}")
            raise
    
    def _initialize_predictor(self):
        """Initialize ML predictor with training data"""
        try:
            # Load training data from file or generate synthetic data
            if self.config.get('generate_synthetic_training', True):
                logger.info("Generating synthetic training data")
                training_data = self.predictor.generate_training_data_synthetic(1000)
            else:
                logger.info("Loading training data from file")
                # In a real implementation, load from file
                training_data = []
            
            # Train the model
            if training_data:
                cv_scores = self.predictor.train_model(training_data)
                logger.info(f"Model trained successfully. CV scores: {cv_scores}")
                
                # Save model if path specified
                if self.config.get('model_save_path'):
                    self.predictor.save_model(self.config['model_save_path'])
                    logger.info(f"Model saved to {self.config['model_save_path']}")
            else:
                logger.warning("No training data available")
                
        except Exception as e:
            logger.error(f"Failed to initialize predictor: {str(e)}")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown()
    
    def start(self):
        """Start the error prediction system"""
        if self.is_running:
            logger.warning("System is already running")
            return
        
        logger.info("Starting Error Prediction and Notification System...")
        self.is_running = True
        self.start_time = datetime.now()
        
        # Start monitoring tasks
        self._start_monitoring_tasks()
        
        logger.info("Error Prediction System started successfully")
    
    def _start_monitoring_tasks(self):
        """Start background monitoring tasks"""
        
        # Start prediction monitoring
        prediction_thread = threading.Thread(target=self._prediction_monitor, daemon=True)
        prediction_thread.start()
        
        # Start health check monitoring
        health_thread = threading.Thread(target=self._health_monitor, daemon=True)
        health_thread.start()
        
        # Start stats reporting
        stats_thread = threading.Thread(target=self._stats_reporter, daemon=True)
        stats_thread.start()
        
        logger.info("Monitoring tasks started")
    
    def _prediction_monitor(self):
        """Monitor and process predictions"""
        while self.is_running and not self.should_stop:
            try:
                # Simulate processing documents and making predictions
                # In a real implementation, this would:
                # 1. Get documents from processing queue
                # 2. Extract characteristics
                # 3. Make predictions
                # 4. Take appropriate actions
                
                time.sleep(10)  # Check every 10 seconds
                
                # Simulate a prediction
                self._simulate_document_processing()
                
            except Exception as e:
                logger.error(f"Prediction monitor error: {str(e)}")
                time.sleep(30)  # Wait longer on error
    
    def _simulate_document_processing(self):
        """Simulate document processing for demonstration"""
        try:
            # Generate realistic document characteristics
            import random
            import numpy as np
            
            doc_chars = DocumentCharacteristics(
                file_size=random.uniform(1, 100) * 1024 * 1024,  # 1-100 MB
                file_type=random.choice(['pdf', 'docx', 'txt', 'image']),
                page_count=random.randint(1, 50),
                text_density=random.uniform(0.1, 0.9),
                image_count=random.randint(0, 20),
                image_quality_score=random.uniform(0.3, 1.0),
                language=random.choice(['en', 'es', 'fr', 'de']),
                processing_time=random.uniform(30, 600),  # 30s to 10min
                confidence_score=random.uniform(0.5, 1.0),
                document_complexity=random.uniform(0.1, 1.0),
                time_of_day=datetime.now().hour,
                day_of_week=datetime.now().weekday(),
                historical_failure_rate=random.uniform(0, 0.2)
            )
            
            # Make prediction
            prediction = self.predictor.predict_error_probability(doc_chars)
            self.system_stats['predictions_made'] += 1
            
            # If high risk, trigger notifications
            if prediction.error_probability > 0.7:
                self.system_stats['errors_detected'] += 1
                self._handle_high_risk_prediction(prediction, doc_chars)
            
        except Exception as e:
            logger.error(f"Document processing simulation error: {str(e)}")
    
    def _handle_high_risk_prediction(self, prediction, doc_chars: DocumentCharacteristics):
        """Handle high-risk predictions"""
        try:
            # Create alert data
            alert_data = {
                'title': f"High Error Risk Predicted ({prediction.severity_prediction.value})",
                'message': f"Error probability: {prediction.error_probability:.2f}",
                'severity': prediction.severity_prediction.value,
                'error_probability': prediction.error_probability,
                'confidence': prediction.confidence,
                'predicted_error_types': [(t.value, p) for t, p in prediction.predicted_error_types[:3]],
                'risk_factors': prediction.risk_factors,
                'recommendations': prediction.recommendations,
                'document_size': doc_chars.file_size,
                'processing_time': doc_chars.processing_time
            }
            
            # Trigger notifications
            if self.notifier:
                alert_ids = self.notifier.trigger_alert(alert_data, source="predictor")
                self.system_stats['alerts_sent'] += len(alert_ids)
                logger.info(f"Alerts triggered: {alert_ids}")
            
            # Create recovery workflow if critical
            if prediction.severity_prediction == SeverityLevel.CRITICAL:
                self._create_recovery_workflow(alert_data)
            
        except Exception as e:
            logger.error(f"High-risk prediction handling error: {str(e)}")
    
    def _create_recovery_workflow(self, alert_data: Dict[str, Any]):
        """Create recovery workflow for critical predictions"""
        try:
            # Create error context
            error_context = ErrorContext(
                error_id=f"predicted_{int(time.time())}",
                error_type="predicted_error",
                error_message=alert_data['message'],
                stack_trace=None,
                timestamp=datetime.now(),
                source_system="error_prediction_system",
                severity=alert_data['severity'],
                metadata=alert_data
            )
            
            # Create recovery workflow
            workflow_id = self.resilience_manager.handle_error(error_context)
            
            logger.info(f"Recovery workflow created: {workflow_id}")
            self.system_stats['workflows_executed'] += 1
            
        except Exception as e:
            logger.error(f"Recovery workflow creation error: {str(e)}")
    
    def _health_monitor(self):
        """Monitor system health"""
        while self.is_running and not self.should_stop:
            try:
                health_status = self.get_health_status()
                
                # Check for critical health issues
                if health_status.get('overall_status') == 'critical':
                    if self.notifier:
                        self.notifier.trigger_alert({
                            'title': 'Critical System Health Issue',
                            'message': 'System health has degraded to critical',
                            'severity': 'critical',
                            'health_status': health_status
                        }, source="health_monitor")
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Health monitor error: {str(e)}")
                time.sleep(120)  # Wait longer on error
    
    def _stats_reporter(self):
        """Report system statistics periodically"""
        while self.is_running and not self.should_stop:
            try:
                # Update uptime
                if self.start_time:
                    self.system_stats['uptime_seconds'] = (datetime.now() - self.start_time).total_seconds()
                
                # Log statistics
                self._log_system_stats()
                
                # Report to external monitoring if configured
                if self.config.get('monitoring_endpoint'):
                    self._report_to_monitoring()
                
                time.sleep(300)  # Report every 5 minutes
                
            except Exception as e:
                logger.error(f"Stats reporter error: {str(e)}")
                time.sleep(600)  # Wait longer on error
    
    def _log_system_stats(self):
        """Log current system statistics"""
        stats = self.get_comprehensive_stats()
        logger.info(f"System Stats: {json.dumps(stats, indent=2, default=str)}")
    
    def _report_to_monitoring(self):
        """Report statistics to external monitoring system"""
        try:
            stats = self.get_comprehensive_stats()
            
            # In a real implementation, send to monitoring system
            # e.g., Prometheus, DataDog, etc.
            logger.debug(f"Reported stats to monitoring: {stats}")
            
        except Exception as e:
            logger.error(f"Monitoring report error: {str(e)}")
    
    def shutdown(self):
        """Gracefully shutdown the system"""
        logger.info("Shutting down Error Prediction System...")
        
        self.should_stop = True
        self.is_running = False
        
        # Shutdown components
        if self.notifier:
            self.notifier.stop()
        
        if self.workflow_engine:
            self.workflow_engine.stop()
        
        # Log final statistics
        final_stats = self.get_comprehensive_stats()
        logger.info(f"Final system statistics: {json.dumps(final_stats, indent=2, default=str)}")
        
        logger.info("Error Prediction System shutdown complete")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        health_status = {
            'overall_status': 'healthy',
            'components': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Check predictor health
            predictor_stats = self.predictor.get_prediction_statistics()
            health_status['components']['predictor'] = {
                'status': 'healthy',
                'statistics': predictor_stats
            }
            
            # Check notification health
            if self.notifier:
                notification_health = self.notifier.get_health_status()
                health_status['components']['notifier'] = notification_health
            
            # Check workflow health
            if self.workflow_engine:
                workflow_stats = self.workflow_engine.get_workflow_statistics()
                health_status['components']['workflow_engine'] = {
                    'status': 'healthy',
                    'statistics': workflow_stats
                }
            
            # Check resilience health
            if self.resilience_manager:
                resilience_metrics = self.resilience_manager.get_resilience_metrics()
                health_status['components']['resilience'] = {
                    'status': 'healthy',
                    'metrics': resilience_metrics
                }
            
            # Determine overall health
            critical_issues = []
            for component, status in health_status['components'].items():
                if status.get('status') != 'healthy':
                    critical_issues.append(component)
            
            if critical_issues:
                health_status['overall_status'] = 'degraded' if len(critical_issues) < 2 else 'critical'
            
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            health_status['overall_status'] = 'error'
            health_status['error'] = str(e)
        
        return health_status
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        
        # Basic system stats
        stats = {
            'system_stats': self.system_stats.copy(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add component statistics
        if self.predictor:
            stats['predictor_stats'] = self.predictor.get_prediction_statistics()
        
        if self.notifier:
            stats['notification_stats'] = self.notifier.get_alert_statistics()
        
        if self.workflow_engine:
            stats['workflow_stats'] = self.workflow_engine.get_workflow_statistics()
        
        if self.resilience_manager:
            stats['resilience_stats'] = self.resilience_manager.get_resilience_metrics()
        
        # Add health status
        stats['health_status'] = self.get_health_status()
        
        # Calculate derived metrics
        total_operations = self.system_stats['predictions_made']
        if total_operations > 0:
            stats['derived_metrics'] = {
                'error_detection_rate': self.system_stats['errors_detected'] / total_operations,
                'alert_rate': self.system_stats['alerts_sent'] / total_operations,
                'workflow_success_rate': (
                    self.system_stats['workflows_successful'] / 
                    max(1, self.system_stats['workflows_executed'])
                )
            }
        
        return stats
    
    def predict_error(self, doc_chars: DocumentCharacteristics) -> Dict[str, Any]:
        """Public method to predict errors for given document characteristics"""
        prediction = self.predictor.predict_error_probability(doc_chars)
        
        return {
            'error_probability': prediction.error_probability,
            'predicted_error_types': [(t.value, p) for t, p in prediction.predicted_error_types],
            'severity_prediction': prediction.severity_prediction.value,
            'confidence': prediction.confidence,
            'risk_factors': prediction.risk_factors,
            'recommendations': prediction.recommendations,
            'timestamp': datetime.now().isoformat()
        }
    
    def create_custom_rule(self, rule_config: Dict[str, Any]) -> str:
        """Create custom notification rule"""
        if not self.notifier:
            raise ValueError("Notification system not available")
        
        rule = NotificationRule(
            rule_id=rule_config['rule_id'],
            name=rule_config['name'],
            conditions=rule_config['conditions'],
            channels=[channel.value for channel in rule_config['channels']],
            recipients=rule_config['recipients'],
            cooldown_minutes=rule_config.get('cooldown_minutes', 60),
            max_alerts_per_hour=rule_config.get('max_alerts_per_hour', 10)
        )
        
        self.notifier.rule_engine.add_rule(rule)
        return rule.rule_id
    
    def simulate_error(self, error_type: str, severity: str = "medium") -> str:
        """Simulate an error for testing recovery workflows"""
        if not self.resilience_manager:
            raise ValueError("Resilience manager not available")
        
        return self.resilience_manager.simulate_error_scenario(error_type, severity)
    
    def get_system_dashboard_data(self) -> Dict[str, Any]:
        """Get data for system dashboard"""
        dashboard_data = {
            'overview': {
                'status': self.get_health_status()['overall_status'],
                'uptime_hours': self.system_stats['uptime_seconds'] / 3600,
                'total_predictions': self.system_stats['predictions_made'],
                'errors_detected': self.system_stats['errors_detected'],
                'alerts_sent': self.system_stats['alerts_sent']
            },
            'recent_predictions': [],
            'active_workflows': 0,
            'recent_alerts': []
        }
        
        # Add recent predictions (last 10)
        if self.predictor.prediction_history:
            recent_predictions = self.predictor.prediction_history[-10:]
            dashboard_data['recent_predictions'] = [
                {
                    'timestamp': pred['timestamp'].isoformat(),
                    'error_probability': pred['result'].error_probability,
                    'severity': pred['result'].severity_prediction.value,
                    'confidence': pred['result'].confidence
                }
                for pred in recent_predictions
            ]
        
        # Add active workflows count
        if self.workflow_engine:
            dashboard_data['active_workflows'] = len(self.workflow_engine.active_workflows)
        
        # Add recent alerts
        if self.notifier and self.notifier.rule_engine.alert_history:
            recent_alerts = self.notifier.rule_engine.alert_history[-5:]
            dashboard_data['recent_alerts'] = [
                {
                    'alert_id': alert.alert_id,
                    'title': alert.title,
                    'level': alert.level.value,
                    'timestamp': alert.timestamp.isoformat(),
                    'status': alert.status
                }
                for alert in recent_alerts
            ]
        
        return dashboard_data

def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load system configuration"""
    default_config = {
        'notifications': {
            'email': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': '587',
                'username': 'your-email@gmail.com',
                'password': 'your-app-password',
                'from_email': 'your-email@gmail.com'
            },
            'slack': {
                'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL',
                'channel': '#alerts'
            }
        },
        'model_save_path': 'error_prediction_model.pkl',
        'training_data_path': None,
        'generate_synthetic_training': True,
        'monitoring_endpoint': None,
        'system_settings': {
            'prediction_threshold': 0.7,
            'max_concurrent_workflows': 100,
            'health_check_interval': 60
        }
    }
    
    if config_path:
        try:
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                # Merge with default config
                default_config.update(loaded_config)
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {str(e)}")
    
    return default_config

def main():
    """Main entry point"""
    try:
        # Load configuration
        config = load_config('error_prediction_config.json')
        
        # Create and start system
        system = ErrorPredictionSystem(config)
        system.start()
        
        # Keep running until interrupted
        logger.info("System running. Press Ctrl+C to stop.")
        while system.is_running and not system.should_stop:
            time.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"System error: {str(e)}")
        raise
    finally:
        if 'system' in locals():
            system.shutdown()

if __name__ == "__main__":
    main()