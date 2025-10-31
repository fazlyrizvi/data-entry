"""
Audit Logging System - Main Module
Comprehensive audit trail logging system for enterprise compliance and security
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from log_collector import LogCollector, AuditEvent, AuditEventType, ComplianceLevel
from compliance_reporter import ComplianceReporter, ComplianceFramework, ReportType


class AuditLoggingSystem:
    """Main audit logging system orchestrator"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._setup_logging()
        
        # Initialize components
        self.log_collector = LogCollector(config)
        self.compliance_reporter = ComplianceReporter(self.log_collector)
        
        # Start monitoring services
        self._start_real_time_monitoring()
        
        self.logger.info("Audit Logging System initialized successfully")
    
    def _setup_logging(self):
        """Setup system logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('audit_system.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('audit_system')
    
    def _start_real_time_monitoring(self):
        """Start real-time audit monitoring services"""
        
        def monitor_high_risk_events():
            """Monitor for high-risk events in real-time"""
            while True:
                try:
                    # Get recent high-risk events
                    recent_events = self.log_collector.get_events(
                        filters={'risk_score_min': 80},
                        limit=50
                    )
                    
                    # Check for patterns
                    self._analyze_risk_patterns(recent_events)
                    
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    self.logger.error(f"Error in risk monitoring: {e}")
                    time.sleep(60)
        
        def monitor_compliance_events():
            """Monitor for compliance violations"""
            compliance_frameworks = [
                ComplianceFramework.GDPR,
                ComplianceFramework.HIPAA,
                ComplianceFramework.SOX
            ]
            
            while True:
                try:
                    for framework in compliance_frameworks:
                        self._check_compliance_violations(framework)
                    
                    time.sleep(300)  # Check every 5 minutes
                    
                except Exception as e:
                    self.logger.error(f"Error in compliance monitoring: {e}")
                    time.sleep(300)
        
        def monitor_user_behavior():
            """Monitor for suspicious user behavior"""
            while True:
                try:
                    self._analyze_user_behavior_patterns()
                    time.sleep(600)  # Check every 10 minutes
                    
                except Exception as e:
                    self.logger.error(f"Error in user behavior monitoring: {e}")
                    time.sleep(600)
        
        # Start monitoring threads
        monitoring_threads = [
            threading.Thread(target=monitor_high_risk_events, daemon=True),
            threading.Thread(target=monitor_compliance_events, daemon=True),
            threading.Thread(target=monitor_user_behavior, daemon=True)
        ]
        
        for thread in monitoring_threads:
            thread.start()
        
        self.logger.info("Real-time monitoring services started")
    
    def _analyze_risk_patterns(self, events: List[Dict[str, Any]]):
        """Analyze patterns in high-risk events"""
        
        if not events:
            return
        
        # Check for rapid escalation attempts
        recent_time = datetime.now() - timedelta(minutes=5)
        recent_high_risk = [
            e for e in events 
            if datetime.fromisoformat(e['timestamp']) > recent_time
        ]
        
        if len(recent_high_risk) > 10:
            self.logger.warning(
                f"HIGH RISK: {len(recent_high_risk)} high-risk events detected in last 5 minutes"
            )
            self._trigger_alert('high_risk_pattern', {
                'event_count': len(recent_high_risk),
                'time_window': '5_minutes',
                'events': recent_high_risk[-5:]  # Last 5 events for context
            })
        
        # Check for privilege escalation patterns
        privilege_events = [
            e for e in recent_high_risk 
            if 'privilege' in e.get('action', '').lower()
        ]
        
        if privilege_events:
            self.logger.warning(
                f"PRIVILEGE ESCALATION: {len(privilege_events)} privilege-related events detected"
            )
            self._trigger_alert('privilege_escalation', {
                'event_count': len(privilege_events),
                'events': privilege_events
            })
    
    def _check_compliance_violations(self, framework: ComplianceFramework):
        """Check for compliance framework violations"""
        
        # Get recent events for the framework
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        report = self.compliance_reporter.generate_compliance_report(
            framework=framework,
            start_date=start_time,
            end_date=end_time,
            report_type=ReportType.EXECUTIVE_SUMMARY
        )
        
        compliance_assessment = report.get('compliance_assessment', {})
        findings = report.get('findings', [])
        
        # Check for critical findings
        critical_findings = [
            f for f in findings 
            if f.get('severity') == 'CRITICAL'
        ]
        
        if critical_findings:
            self.logger.warning(
                f"{framework.value.upper()} CRITICAL FINDINGS: {len(critical_findings)} detected"
            )
            self._trigger_alert(f'{framework.value}_critical_findings', {
                'framework': framework.value,
                'findings': critical_findings
            })
        
        # Check compliance score
        compliance_score = compliance_assessment.get('overall_score', 0)
        if compliance_score < 70:
            self.logger.warning(
                f"{framework.value.upper()} LOW COMPLIANCE SCORE: {compliance_score}%"
            )
            self._trigger_alert(f'{framework.value}_low_compliance', {
                'framework': framework.value,
                'score': compliance_score
            })
    
    def _analyze_user_behavior_patterns(self):
        """Analyze user behavior for anomalies"""
        
        # Get user activity for analysis
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        filters = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        events = self.log_collector.get_events(filters, limit=1000)
        
        if not events:
            return
        
        # Group events by user
        user_events = {}
        for event in events:
            user_id = event.get('user_id', 'unknown')
            if user_id not in user_events:
                user_events[user_id] = []
            user_events[user_id].append(event)
        
        # Analyze behavior patterns
        for user_id, user_event_list in user_events.items():
            if user_id == 'unknown':
                continue
            
            # Check for unusual activity hours
            unusual_hours = self._check_unusual_activity_hours(user_event_list)
            if unusual_hours:
                self._trigger_alert('unusual_user_activity', {
                    'user_id': user_id,
                    'unusual_hours': unusual_hours,
                    'event_count': len(user_event_list)
                })
            
            # Check for failed login patterns
            failed_attempts = [
                e for e in user_event_list 
                if e.get('outcome') == 'FAILURE'
            ]
            
            if len(failed_attempts) > 5:
                self.logger.warning(
                    f"USER BEHAVIOR: {user_id} has {len(failed_attempts)} failed attempts in 24h"
                )
                self._trigger_alert('excessive_failed_logins', {
                    'user_id': user_id,
                    'failed_attempts': len(failed_attempts),
                    'events': failed_attempts[-3:]  # Last 3 failed attempts
                })
    
    def _check_unusual_activity_hours(self, events: List[Dict[str, Any]]) -> List[int]:
        """Check for activity during unusual hours (outside business hours)"""
        
        unusual_hours = []
        business_start = 8   # 8 AM
        business_end = 18    # 6 PM
        
        for event in events:
            event_time = datetime.fromisoformat(event['timestamp'])
            hour = event_time.hour
            
            # Check if activity outside business hours
            if hour < business_start or hour > business_end:
                if hour not in unusual_hours:
                    unusual_hours.append(hour)
        
        return unusual_hours
    
    def _trigger_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """Trigger security alert"""
        
        alert = {
            'alert_id': f"{alert_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'alert_type': alert_type,
            'timestamp': datetime.now().isoformat(),
            'severity': self._get_alert_severity(alert_type),
            'data': alert_data,
            'status': 'ACTIVE'
        }
        
        # Log the alert
        self.logger.warning(f"SECURITY ALERT [{alert['severity']}]: {alert_type}")
        
        # Store alert (you could also send to SIEM, email, etc.)
        self._store_alert(alert)
    
    def _get_alert_severity(self, alert_type: str) -> str:
        """Determine alert severity based on type"""
        
        severity_map = {
            'high_risk_pattern': 'HIGH',
            'privilege_escalation': 'CRITICAL',
            'gdpr_critical_findings': 'CRITICAL',
            'hipaa_critical_findings': 'CRITICAL',
            'sox_critical_findings': 'HIGH',
            'unusual_user_activity': 'MEDIUM',
            'excessive_failed_logins': 'HIGH'
        }
        
        return severity_map.get(alert_type, 'MEDIUM')
    
    def _store_alert(self, alert: Dict[str, Any]):
        """Store alert (implement your preferred storage mechanism)"""
        
        alert_file = Path('security_alerts.jsonl')
        with open(alert_file, 'a') as f:
            f.write(f"{alert}\n")
        
        self.logger.info(f"Alert stored: {alert['alert_id']}")
    
    # Public API methods
    
    def log_user_activity(self, user_id: str, action: str, session_id: str = None,
                         source_ip: str = None, details: Dict[str, Any] = None) -> bool:
        """Log user activity events"""
        return self.log_collector.collect_user_activity(
            user_id=user_id,
            action=action,
            session_id=session_id,
            source_ip=source_ip,
            details=details
        )
    
    def log_data_access(self, user_id: str, resource: str, action: str,
                       compliance_level: ComplianceLevel = ComplianceLevel.STANDARD,
                       details: Dict[str, Any] = None) -> bool:
        """Log data access events"""
        return self.log_collector.collect_data_access(
            user_id=user_id,
            resource=resource,
            action=action,
            compliance_level=compliance_level,
            details=details
        )
    
    def log_system_change(self, user_id: str, action: str, resource: str,
                         details: Dict[str, Any] = None) -> bool:
        """Log system configuration changes"""
        return self.log_collector.collect_system_change(
            user_id=user_id,
            action=action,
            resource=resource,
            details=details
        )
    
    def generate_compliance_report(self, framework: ComplianceFramework, 
                                 start_date: datetime = None, end_date: datetime = None,
                                 report_type: ReportType = ReportType.EXECUTIVE_SUMMARY) -> Dict[str, Any]:
        """Generate compliance report"""
        
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
        
        return self.compliance_reporter.generate_compliance_report(
            framework=framework,
            start_date=start_date,
            end_date=end_date,
            report_type=report_type
        )
    
    def export_compliance_report(self, framework: ComplianceFramework, 
                               start_date: datetime = None, end_date: datetime = None,
                               format: str = 'json', output_path: str = None) -> str:
        """Export compliance report to file"""
        
        report = self.generate_compliance_report(framework, start_date, end_date)
        return self.compliance_reporter.export_report(report, format, output_path)
    
    def get_audit_events(self, filters: Dict[str, Any] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get audit events with filters"""
        return self.log_collector.get_events(filters, limit)
    
    def verify_log_integrity(self) -> Dict[str, Any]:
        """Verify log integrity"""
        return self.log_collector.verify_integrity()
    
    def get_security_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent security alerts"""
        
        alert_file = Path('security_alerts.jsonl')
        if not alert_file.exists():
            return []
        
        alerts = []
        try:
            with open(alert_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    if line.strip():
                        alerts.append(eval(line))  # In production, use json.loads
        except Exception as e:
            self.logger.error(f"Error reading security alerts: {e}")
        
        return alerts
    
    def create_forensic_timeline(self, user_id: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Create forensic timeline for a specific user and time period"""
        
        filters = {
            'user_id': user_id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        events = self.log_collector.get_events(filters, limit=10000)
        
        # Sort events by timestamp
        events.sort(key=lambda x: x['timestamp'])
        
        timeline = {
            'user_id': user_id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'total_events': len(events),
            'event_timeline': [],
            'risk_analysis': self._analyze_user_risk_timeline(events),
            'behavior_patterns': self._analyze_user_behavior_timeline(events)
        }
        
        # Create detailed timeline
        for event in events:
            timeline['event_timeline'].append({
                'timestamp': event['timestamp'],
                'event_type': event['event_type'],
                'action': event['action'],
                'resource': event.get('resource'),
                'outcome': event['outcome'],
                'risk_score': event.get('risk_score'),
                'correlation_id': event.get('correlation_id')
            })
        
        return timeline
    
    def _analyze_user_risk_timeline(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze risk patterns in user timeline"""
        
        risk_scores = [e.get('risk_score', 0) for e in events]
        
        return {
            'average_risk_score': sum(risk_scores) / len(risk_scores) if risk_scores else 0,
            'highest_risk_score': max(risk_scores) if risk_scores else 0,
            'risk_trend': 'increasing' if len(risk_scores) > 1 and risk_scores[-1] > risk_scores[0] else 'stable',
            'high_risk_events': len([e for e in events if e.get('risk_score', 0) >= 70])
        }
    
    def _analyze_user_behavior_timeline(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze behavior patterns in user timeline"""
        
        actions = [e.get('action', '') for e in events]
        outcomes = [e.get('outcome', '') for e in events]
        
        return {
            'unique_actions': len(set(actions)),
            'success_rate': len([o for o in outcomes if o == 'SUCCESS']) / len(outcomes) * 100 if outcomes else 0,
            'most_common_action': max(set(actions), key=actions.count) if actions else None,
            'failed_events': len([o for o in outcomes if o == 'FAILURE'])
        }
    
    def archive_old_logs(self, days_to_keep: int = 2555) -> Dict[str, Any]:
        """Archive logs older than specified days"""
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Export old logs
        filters = {
            'end_time': cutoff_date.isoformat()
        }
        
        old_logs = self.log_collector.get_events(filters, limit=100000)
        
        if old_logs:
            archive_path = f"audit_logs_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(archive_path, 'w') as f:
                import json
                json.dump(old_logs, f, indent=2, default=str)
            
            self.logger.info(f"Archived {len(old_logs)} logs to {archive_path}")
            
            return {
                'archived_events': len(old_logs),
                'archive_file': archive_path,
                'cutoff_date': cutoff_date.isoformat()
            }
        
        return {'archived_events': 0}
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get audit system health status"""
        
        # Get log integrity status
        integrity_status = self.verify_log_integrity()
        
        # Get recent event counts
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        
        recent_events = self.log_collector.get_events({
            'start_time': last_hour.isoformat()
        }, limit=1000)
        
        return {
            'system_status': 'HEALTHY',
            'log_integrity': integrity_status,
            'events_last_hour': len(recent_events),
            'monitoring_services': 'ACTIVE',
            'last_health_check': now.isoformat(),
            'disk_usage': self._get_disk_usage(),
            'database_size': self._get_database_size()
        }
    
    def _get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage information"""
        
        import shutil
        total, used, free = shutil.disk_usage(".")
        return {
            'total_gb': total // (1024**3),
            'used_gb': used // (1024**3),
            'free_gb': free // (1024**3),
            'usage_percent': (used / total) * 100
        }
    
    def _get_database_size(self) -> int:
        """Get database file size in bytes"""
        
        db_path = Path(self.config.get('database_path', 'audit_logs.db'))
        return db_path.stat().st_size if db_path.exists() else 0


# Example usage and demonstration

def demo_audit_logging_system():
    """Demonstrate audit logging system capabilities"""
    
    # Configuration
    config = {
        'database_path': 'demo_audit_logs.db',
        'key_file': 'demo_encryption.key',
        'retention_days': 2555
    }
    
    # Initialize system
    audit_system = AuditLoggingSystem(config)
    
    # Simulate user activities
    print("=== Audit Logging System Demo ===\n")
    
    # User login events
    audit_system.log_user_activity(
        user_id='user123',
        action='login',
        session_id='sess_abc123',
        source_ip='192.168.1.100',
        details={'browser': 'Chrome', 'location': 'Office'}
    )
    
    # Data access events
    audit_system.log_data_access(
        user_id='user123',
        resource='customer_database/personal_info',
        action='read',
        compliance_level=ComplianceLevel.GDPR,
        details={'query': 'SELECT * FROM customers WHERE email LIKE "%@example.com"'}
    )
    
    # System change events
    audit_system.log_system_change(
        user_id='admin456',
        action='modify_config',
        resource='database/connection_pool',
        details={'max_connections': 100, 'old_value': 50}
    )
    
    # Failed login attempt
    audit_system.log_user_activity(
        user_id='user789',
        action='login',
        session_id=None,
        source_ip='10.0.0.50',
        details={'password_attempts': 3}
    )
    
    print("Sample events logged successfully!")
    print("\n=== Generating Compliance Report ===")
    
    # Generate GDPR compliance report
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    gdpr_report = audit_system.generate_compliance_report(
        framework=ComplianceFramework.GDPR,
        start_date=start_time,
        end_date=end_time
    )
    
    print(f"GDPR Compliance Score: {gdpr_report['compliance_assessment']['overall_score']:.1f}%")
    print(f"Compliance Status: {gdpr_report['compliance_assessment']['compliance_status']}")
    print(f"Total Requirements Assessed: {gdpr_report['compliance_assessment']['total_requirements']}")
    
    # Export report
    report_path = audit_system.export_compliance_report(
        framework=ComplianceFramework.GDPR,
        start_date=start_time,
        end_date=end_time,
        format='json'
    )
    
    print(f"\nReport exported to: {report_path}")
    
    # Get system health
    health = audit_system.get_system_health()
    print(f"\n=== System Health Status ===")
    print(f"Status: {health['system_status']}")
    print(f"Events last hour: {health['events_last_hour']}")
    print(f"Database size: {health['database_size']} bytes")
    
    print("\nDemo completed successfully!")


if __name__ == "__main__":
    demo_audit_logging_system()
