#!/usr/bin/env python3
"""
Audit Trail Security Testing Suite
Tests audit logging security, integrity verification, compliance monitoring,
and forensic analysis capabilities.
"""

import pytest
import json
import hashlib
import hmac
import sqlite3
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
import tempfile
import shutil

# Add the security module to the path
sys.path.append('/workspace/code/enterprise_integration/audit_logging')

from main import AuditLoggingSystem, ComplianceLevel, ComplianceFramework
from log_collector import LogCollector
from compliance_reporter import ComplianceReporter


class TestAuditLogIntegrity:
    """Test suite for audit log integrity protection"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp(prefix="audit_test_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def audit_system(self, temp_dir):
        """Create audit system instance"""
        config = {
            'database_path': os.path.join(temp_dir, 'audit_test.db'),
            'key_file': os.path.join(temp_dir, 'audit.key'),
            'retention_days': 2555,
            'alert_thresholds': {
                'high_risk_events': 10,
                'failed_logins': 5
            }
        }
        return AuditLoggingSystem(config)
    
    @pytest.mark.security
    def test_log_tamper_detection(self, audit_system):
        """Test detection of log tampering"""
        # Log some events
        audit_system.log_user_activity(
            user_id='test-user-123',
            action='login',
            session_id='sess-123',
            source_ip='192.168.1.100'
        )
        
        # Verify initial integrity
        integrity_valid = audit_system.verify_log_integrity()
        assert integrity_valid is True
        
        # Tamper with the database directly
        db_path = audit_system.config['database_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Modify a log entry
        cursor.execute("UPDATE audit_events SET details = 'tampered' WHERE id = 1")
        conn.commit()
        conn.close()
        
        # Verify integrity should fail
        integrity_broken = audit_system.verify_log_integrity()
        assert integrity_broken is False
    
    @pytest.mark.security
    def test_hash_chain_verification(self, audit_system):
        """Test cryptographic hash chain for log entries"""
        # Log multiple events to create a chain
        for i in range(5):
            audit_system.log_user_activity(
                user_id=f'test-user-{i}',
                action=f'action-{i}',
                session_id=f'sess-{i}',
                source_ip=f'192.168.1.{i}'
            )
        
        # Verify hash chain integrity
        integrity_result = audit_system.verify_hash_chain()
        assert integrity_result['is_valid'] is True
        
        # Tamper with a middle entry
        db_path = audit_system.config['database_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE audit_events SET action = 'tampered' WHERE id = 3")
        conn.commit()
        conn.close()
        
        # Hash chain should be broken
        broken_result = audit_system.verify_hash_chain()
        assert broken_result['is_valid'] is False
        assert len(broken_result['tampered_entries']) > 0
    
    @pytest.mark.security
    def test_log_entry_digital_signatures(self, audit_system):
        """Test digital signatures for log entries"""
        # Log an event
        event_id = audit_system.log_user_activity(
            user_id='test-user',
            action='login',
            session_id='sess-123',
            source_ip='192.168.1.100'
        )
        
        # Verify signature
        signature_valid = audit_system.verify_event_signature(event_id)
        assert signature_valid is True
        
        # Modify the event
        db_path = audit_system.config['database_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE audit_events SET action = 'tampered' WHERE id = ?", (event_id,))
        conn.commit()
        conn.close()
        
        # Signature should no longer be valid
        signature_invalid = audit_system.verify_event_signature(event_id)
        assert signature_invalid is False
    
    @pytest.mark.security
    def test_log_encryption_security(self, audit_system):
        """Test log encryption at rest"""
        # Log sensitive event
        audit_system.log_user_activity(
            user_id='test-user',
            action='view_sensitive_data',
            session_id='sess-123',
            source_ip='192.168.1.100',
            details={'ssn': '123-45-6789', 'credit_card': '4111-1111-1111-1111'}
        )
        
        # Check database file directly
        db_path = audit_system.config['database_path']
        with open(db_path, 'rb') as f:
            db_content = f.read()
        
        # Sensitive data should not be in plaintext
        sensitive_strings = ['123-45-6789', '4111-1111-1111-1111', 'ssn', 'credit_card']
        for sensitive in sensitive_strings:
            assert sensitive.encode() not in db_content, \
                f"Sensitive data '{sensitive}' found in plaintext"
    
    @pytest.mark.security
    def test_log_append_only_protection(self, audit_system):
        """Test append-only protection for logs"""
        # Log initial event
        initial_event_id = audit_system.log_user_activity(
            user_id='test-user',
            action='login',
            session_id='sess-123',
            source_ip='192.168.1.100'
        )
        
        # Attempt to modify existing entry
        db_path = audit_system.config['database_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE audit_events SET action = 'modified' WHERE id = ?",
                (initial_event_id,)
            )
            conn.commit()
            update_allowed = True
        except Exception:
            update_allowed = False
        finally:
            conn.close()
        
        # Update should be prevented or logged
        if update_allowed:
            # Should have audit trail of the change
            audit_system.log_system_change(
                user_id='system',
                action='log_modification',
                resource='audit_events',
                details={'event_id': initial_event_id, 'modified_by': 'test'}
            )
    
    @pytest.mark.security
    def test_log_worm_implementation(self, audit_system):
        """Test Write Once Read Many (WORM) log implementation"""
        # Log events
        event_ids = []
        for i in range(3):
            event_id = audit_system.log_user_activity(
                user_id=f'test-user-{i}',
                action=f'action-{i}',
                session_id=f'sess-{i}',
                source_ip=f'192.168.1.{i}'
            )
            event_ids.append(event_id)
        
        # Attempt to delete log entries
        db_path = audit_system.config['database_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        deletion_prevented = True
        try:
            cursor.execute("DELETE FROM audit_events WHERE id = ?", (event_ids[0],))
            conn.commit()
            deletion_prevented = False
        except Exception:
            pass
        finally:
            conn.close()
        
        assert deletion_prevented is True, "WORM protection not working"
    
    @pytest.mark.security
    def test_log_compression_security(self, audit_system):
        """Test secure log compression"""
        # Create large log entries
        large_details = {"data": "X" * 10000}  # 10KB of data
        
        audit_system.log_user_activity(
            user_id='test-user',
            action='large_data_operation',
            session_id='sess-123',
            source_ip='192.168.1.100',
            details=large_details
        )
        
        # Compress old logs
        audit_system.compress_old_logs(days_to_keep=0)
        
        # Check if compression preserves integrity
        integrity_valid = audit_system.verify_log_integrity()
        assert integrity_valid is True
    
    @pytest.mark.security
    def test_log_backward_compatibility(self, audit_system):
        """Test log format backward compatibility"""
        # Log events in current format
        event_id = audit_system.log_user_activity(
            user_id='test-user',
            action='login',
            session_id='sess-123',
            source_ip='192.168.1.100'
        )
        
        # Export logs
        export_path = os.path.join(audit_system.config['database_path'] + '.export')
        audit_system.export_logs(export_path)
        
        # Should be readable and valid
        assert os.path.exists(export_path)
        
        with open(export_path, 'r') as f:
            exported_data = json.load(f)
        
        assert 'events' in exported_data
        assert len(exported_data['events']) > 0


class TestAuditLogAccessControl:
    """Test suite for audit log access control"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp(prefix="audit_access_test_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def audit_system(self, temp_dir):
        """Create audit system instance"""
        config = {
            'database_path': os.path.join(temp_dir, 'audit_test.db'),
            'key_file': os.path.join(temp_dir, 'audit.key'),
            'retention_days': 2555
        }
        return AuditLoggingSystem(config)
    
    @pytest.mark.security
    def test_audit_log_permissions(self, audit_system):
        """Test audit log file permissions"""
        # Log an event to create database file
        audit_system.log_user_activity(
            user_id='test-user',
            action='login',
            session_id='sess-123',
            source_ip='192.168.1.100'
        )
        
        # Check file permissions
        db_path = audit_system.config['database_path']
        key_path = audit_system.config['key_file']
        
        # Files should have restrictive permissions (600 = rw-------)
        db_stat = os.stat(db_path)
        key_stat = os.stat(key_path)
        
        # Extract permission bits
        db_perms = oct(db_stat.st_mode)[-3:]
        key_perms = oct(key_stat.st_mode)[-3:]
        
        # Should be 600 (owner read/write only)
        assert db_perms in ['600', '000'], f"Database permissions too open: {db_perms}"
        assert key_perms in ['600', '000'], f"Key permissions too open: {key_perms}"
    
    @pytest.mark.security
    def test_log_access_logging(self, audit_system):
        """Test that log access is itself audited"""
        # Attempt to access logs
        events = audit_system.get_audit_events(limit=10)
        
        # Should create audit log of the access
        access_events = [e for e in events if e.get('event_type') == 'log_access']
        assert len(access_events) > 0, "Log access not audited"
        
        # Verify access event has proper details
        access_event = access_events[0]
        assert 'accessed_by' in access_event
        assert 'access_type' in access_event
    
    @pytest.mark.security
    def test_role_based_log_access(self, audit_system):
        """Test role-based access to audit logs"""
        # Test different user roles
        test_roles = ['VIEWER', 'OPERATOR', 'MANAGER', 'ADMIN']
        
        for role in test_roles:
            # Attempt to access audit logs with different permissions
            try:
                if role in ['VIEWER', 'OPERATOR']:
                    # Limited access
                    events = audit_system.get_audit_events(
                        limit=10,
                        user_id='test-user',
                        role=role
                    )
                elif role == 'MANAGER':
                    # More access
                    events = audit_system.get_audit_events(
                        limit=100,
                        include_system_events=True,
                        role=role
                    )
                else:  # ADMIN
                    # Full access
                    events = audit_system.get_audit_events(
                        limit=1000,
                        include_system_events=True,
                        include_security_events=True,
                        role=role
                    )
                
                # All roles should have some access
                assert events is not None
            except Exception as e:
                # Lower roles might be denied
                assert role in ['VIEWER', 'OPERATOR']
    
    @pytest.mark.security
    def test_log_data_classification(self, audit_system):
        """Test log data classification and protection"""
        # Log events with different sensitivity levels
        sensitive_event_id = audit_system.log_data_access(
            user_id='test-user',
            resource='customer_database/personal_info',
            action='read',
            compliance_level=ComplianceLevel.HIPAA,
            details={'sensitive_data': True}
        )
        
        public_event_id = audit_system.log_user_activity(
            user_id='test-user',
            action='view_public_page',
            session_id='sess-123',
            source_ip='192.168.1.100'
        )
        
        # Check database for classification
        db_path = audit_system.config['database_path']
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT classification FROM audit_events WHERE id = ?",
            (sensitive_event_id,)
        )
        sensitive_classification = cursor.fetchone()[0]
        
        cursor.execute(
            "SELECT classification FROM audit_events WHERE id = ?",
            (public_event_id,)
        )
        public_classification = cursor.fetchone()[0]
        
        conn.close()
        
        # Sensitive event should be classified appropriately
        assert sensitive_classification in ['CONFIDENTIAL', 'RESTRICTED']
        
        # Public event should have lower classification
        assert public_classification in ['PUBLIC', 'INTERNAL']


class TestComplianceMonitoring:
    """Test suite for compliance monitoring and reporting"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp(prefix="audit_compliance_test_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def audit_system(self, temp_dir):
        """Create audit system instance"""
        config = {
            'database_path': os.path.join(temp_dir, 'audit_test.db'),
            'key_file': os.path.join(temp_dir, 'audit.key'),
            'retention_days': 2555
        }
        return AuditLoggingSystem(config)
    
    @pytest.mark.security
    def test_gdpr_compliance_monitoring(self, audit_system):
        """Test GDPR compliance monitoring"""
        # Log GDPR-relevant events
        audit_system.log_data_access(
            user_id='test-user',
            resource='customer_database/personal_info',
            action='read',
            compliance_level=ComplianceLevel.GDPR,
            details={'data_subject': 'customer_123', 'legal_basis': 'consent'}
        )
        
        # Generate GDPR compliance report
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        report = audit_system.generate_compliance_report(
            framework=ComplianceFramework.GDPR,
            start_date=start_date,
            end_date=end_date,
            report_type='detailed'
        )
        
        assert 'gdpr_compliance' in report
        assert 'data_subject_rights' in report['gdpr_compliance']
        assert 'retention_compliance' in report['gdpr_compliance']
    
    @pytest.mark.security
    def test_hipaa_compliance_monitoring(self, audit_system):
        """Test HIPAA compliance monitoring"""
        # Log HIPAA-relevant events
        audit_system.log_data_access(
            user_id='test-user',
            resource='medical_records/patient_data',
            action='read',
            compliance_level=ComplianceLevel.HIPAA,
            details={'phi_accessed': True}
        )
        
        # Generate HIPAA compliance report
        report = audit_system.generate_compliance_report(
            framework=ComplianceFramework.HIPAA,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )
        
        assert 'hipaa_compliance' in report
        assert 'phi_access_controls' in report['hipaa_compliance']
        assert 'audit_controls' in report['hipaa_compliance']
    
    @pytest.mark.security
    def test_sox_compliance_monitoring(self, audit_system):
        """Test SOX compliance monitoring"""
        # Log SOX-relevant events
        audit_system.log_system_change(
            user_id='admin',
            action='modify_financial_config',
            resource='database/financial_settings',
            details={'change_approved_by': 'cfo'}
        )
        
        report = audit_system.generate_compliance_report(
            framework=ComplianceFramework.SOX,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )
        
        assert 'sox_compliance' in report
        assert 'internal_controls' in report['sox_compliance']
        assert 'segregation_of_duties' in report['sox_compliance']
    
    @pytest.mark.security
    def test_pci_dss_compliance_monitoring(self, audit_system):
        """Test PCI DSS compliance monitoring"""
        # Log PCI DSS-relevant events
        audit_system.log_data_access(
            user_id='test-user',
            resource='payment_system/cardholder_data',
            action='read',
            compliance_level=ComplianceLevel.PCI_DSS,
            details={'card_number_masked': True}
        )
        
        report = audit_system.generate_compliance_report(
            framework=ComplianceFramework.PCI_DSS,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )
        
        assert 'pci_dss_compliance' in report
        assert 'cardholder_data_protection' in report['pci_dss_compliance']
        assert 'access_controls' in report['pci_dss_compliance']
    
    @pytest.mark.security
    def test_compliance_score_calculation(self, audit_system):
        """Test compliance score calculation"""
        # Log various compliance events
        for i in range(10):
            audit_system.log_user_activity(
                user_id=f'user-{i}',
                action='login',
                session_id=f'sess-{i}',
                source_ip=f'192.168.1.{i}'
            )
        
        # Generate compliance report
        report = audit_system.generate_compliance_report(
            framework=ComplianceFramework.GDPR,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )
        
        # Check compliance score
        assert 'compliance_score' in report
        compliance_score = report['compliance_score']
        
        # Score should be between 0 and 100
        assert 0 <= compliance_score <= 100
    
    @pytest.mark.security
    def test_compliance_violation_detection(self, audit_system):
        """Test automatic compliance violation detection"""
        # Log events that violate compliance
        audit_system.log_data_access(
            user_id='unauthorized-user',
            resource='sensitive_data',
            action='read',
            compliance_level=ComplianceLevel.GDPR,
            details={'unauthorized_access': True}
        )
        
        # Check for violations
        violations = audit_system.detect_compliance_violations()
        
        assert len(violations) > 0, "Compliance violations not detected"
        
        violation = violations[0]
        assert violation['framework'] == 'GDPR'
        assert violation['severity'] in ['low', 'medium', 'high', 'critical']
    
    @pytest.mark.security
    def test_data_subject_rights_tracking(self, audit_system):
        """Test data subject rights tracking (GDPR)"""
        # Log data subject rights requests
        audit_system.log_user_activity(
            user_id='privacy-team',
            action='process_data_subject_request',
            session_id='sess-privacy',
            source_ip='192.168.1.100',
            details={
                'request_type': 'access',
                'data_subject_id': 'customer-123',
                'fulfilled': True
            }
        )
        
        # Track data subject rights
        rights_requests = audit_system.track_data_subject_rights()
        
        assert len(rights_requests) > 0
        assert rights_requests[0]['request_type'] == 'access'
    
    @pytest.mark.security
    def test_retention_policy_compliance(self, audit_system):
        """Test data retention policy compliance"""
        # Register data with retention policy
        audit_system.register_data_for_retention(
            data_identifier='test-data-123',
            data_type='customer_record',
            retention_period_days=365,
            legal_basis='contractual_obligation'
        )
        
        # Check retention compliance
        retention_status = audit_system.check_retention_compliance()
        
        assert 'compliant_items' in retention_status
        assert 'expired_items' in retention_status
        assert 'pending_deletion' in retention_status


class TestAuditForensicAnalysis:
    """Test suite for forensic analysis capabilities"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp(prefix="audit_forensic_test_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def audit_system(self, temp_dir):
        """Create audit system instance"""
        config = {
            'database_path': os.path.join(temp_dir, 'audit_test.db'),
            'key_file': os.path.join(temp_dir, 'audit.key'),
            'retention_days': 2555
        }
        return AuditLoggingSystem(config)
    
    @pytest.mark.security
    def test_user_behavior_analysis(self, audit_system):
        """Test user behavior analysis for anomalies"""
        # Log normal user behavior
        for i in range(10):
            audit_system.log_user_activity(
                user_id='normal-user',
                action='view_dashboard',
                session_id=f'sess-{i}',
                source_ip='192.168.1.100'
            )
        
        # Log anomalous behavior
        for i in range(5):
            audit_system.log_user_activity(
                user_id='normal-user',
                action='access_admin_panel',
                session_id=f'anomalous-sess-{i}',
                source_ip='10.0.0.1'  # Different IP
            )
        
        # Analyze user behavior
        behavior_analysis = audit_system.analyze_user_behavior('normal-user')
        
        assert 'normal_patterns' in behavior_analysis
        assert 'anomalies' in behavior_analysis
        assert len(behavior_analysis['anomalies']) > 0
    
    @pytest.mark.security
    def test_security_incident_timeline(self, audit_system):
        """Test security incident timeline generation"""
        # Simulate a security incident
        incident_events = [
            {'action': 'failed_login', 'source_ip': '192.168.1.100'},
            {'action': 'failed_login', 'source_ip': '192.168.1.100'},
            {'action': 'successful_login', 'source_ip': '192.168.1.100'},
            {'action': 'privilege_escalation', 'source_ip': '192.168.1.100'},
            {'action': 'data_exfiltration', 'source_ip': '192.168.1.100'},
        ]
        
        for i, event in enumerate(incident_events):
            audit_system.log_security_event(
                event_type='incident',
                severity='high',
                user_id='suspicious-user',
                details=event,
                source_ip=event['source_ip']
            )
            time.sleep(0.1)  # Small delay between events
        
        # Generate incident timeline
        timeline = audit_system.create_incident_timeline()
        
        assert len(timeline) >= len(incident_events)
        assert any('incident' in str(event).lower() for event in timeline)
    
    @pytest.mark.security
    def test_forensic_timeline_creation(self, audit_system):
        """Test forensic timeline creation for investigation"""
        # Log events for a specific time period
        start_time = datetime.utcnow() - timedelta(hours=2)
        end_time = datetime.utcnow()
        
        for i in range(20):
            event_time = start_time + timedelta(minutes=i * 6)
            audit_system.log_user_activity(
                user_id='investigation-target',
                action=f'action-{i}',
                session_id=f'sess-{i}',
                source_ip='192.168.1.100',
                timestamp=event_time
            )
        
        # Create forensic timeline
        timeline = audit_system.create_forensic_timeline(
            user_id='investigation-target',
            start_time=start_time,
            end_time=end_time
        )
        
        assert 'timeline' in timeline
        assert 'events' in timeline['timeline']
        assert len(timeline['timeline']['events']) == 20
        
        # Check timeline order
        events = timeline['timeline']['events']
        timestamps = [event.get('timestamp') for event in events]
        assert timestamps == sorted(timestamps)  # Should be chronologically ordered
    
    @pytest.mark.security
    def test_data_flow_analysis(self, audit_system):
        """Test data flow analysis for investigation"""
        # Log data access events showing flow
        data_flow = [
            {'user': 'user-a', 'resource': 'source-db', 'action': 'read'},
            {'user': 'user-a', 'resource': 'intermediate-storage', 'action': 'write'},
            {'user': 'user-b', 'resource': 'intermediate-storage', 'action': 'read'},
            {'user': 'user-b', 'resource': 'destination-db', 'action': 'write'},
        ]
        
        for flow in data_flow:
            audit_system.log_data_access(
                user_id=flow['user'],
                resource=flow['resource'],
                action=flow['action'],
                compliance_level=ComplianceLevel.INTERNAL
            )
        
        # Analyze data flow
        flow_analysis = audit_system.analyze_data_flow()
        
        assert 'flows' in flow_analysis
        assert len(flow_analysis['flows']) > 0
    
    @pytest.mark.security
    def test_attribution_analysis(self, audit_system):
        """Test attribution analysis for attacks"""
        # Log attack from multiple sources
        attack_sources = ['192.168.1.100', '10.0.0.1', '172.16.0.1']
        
        for source in attack_sources:
            for i in range(3):
                audit_system.log_security_event(
                    event_type='attack',
                    severity='critical',
                    details={'attack_type': 'sql_injection', 'attempt': i},
                    source_ip=source
                )
        
        # Analyze attribution
        attribution = audit_system.analyze_attribution()
        
        assert 'threat_actors' in attribution
        assert len(attribution['threat_actors']) > 0
        
        # Check if sources are correlated
        for actor in attribution['threat_actors']:
            if actor.get('threat_level') == 'high':
                assert len(actor.get('associated_ips', [])) >= 2
    
    @pytest.mark.security
    def test_threat_intelligence_integration(self, audit_system):
        """Test threat intelligence integration"""
        # Log events that match threat indicators
        threat_indicators = [
            {'source_ip': '192.168.1.100', 'threat_type': 'known_malicious'},
            {'user_agent': 'MaliciousBot/1.0', 'threat_type': 'malicious_bot'},
        ]
        
        for indicator in threat_indicators:
            audit_system.log_user_activity(
                user_id='unknown-user',
                action='suspicious_activity',
                source_ip=indicator.get('source_ip', '192.168.1.100'),
                user_agent=indicator.get('user_agent', 'NormalBot/1.0')
            )
        
        # Check threat intelligence match
        threats = audit_system.check_threat_intelligence()
        
        assert len(threats) > 0
        
        # Verify threat details
        threat = threats[0]
        assert 'threat_type' in threat
        assert 'confidence' in threat
        assert 0 <= threat['confidence'] <= 1


class TestAuditLogPerformance:
    """Test suite for audit log performance and scalability"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp(prefix="audit_perf_test_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def audit_system(self, temp_dir):
        """Create audit system instance"""
        config = {
            'database_path': os.path.join(temp_dir, 'audit_test.db'),
            'key_file': os.path.join(temp_dir, 'audit.key'),
            'retention_days': 2555
        }
        return AuditLoggingSystem(config)
    
    @pytest.mark.security
    def test_high_volume_logging(self, audit_system):
        """Test logging under high volume"""
        import time
        
        # Log events rapidly
        start_time = time.time()
        num_events = 1000
        
        for i in range(num_events):
            audit_system.log_user_activity(
                user_id=f'user-{i % 10}',
                action=f'action-{i}',
                session_id=f'sess-{i}',
                source_ip=f'192.168.1.{i % 255}'
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should handle 1000 events in reasonable time
        events_per_second = num_events / duration
        assert events_per_second > 100, f"Performance too slow: {events_per_second} events/sec"
    
    @pytest.mark.security
    def test_concurrent_logging(self, audit_system):
        """Test concurrent logging from multiple sources"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def log_events(thread_id, num_events):
            try:
                for i in range(num_events):
                    audit_system.log_user_activity(
                        user_id=f'user-{thread_id}',
                        action=f'action-{i}',
                        session_id=f'sess-{thread_id}-{i}',
                        source_ip=f'10.0.{thread_id}.100'
                    )
                results.put(('success', thread_id))
            except Exception as e:
                results.put(('error', thread_id, str(e)))
        
        # Create multiple threads
        num_threads = 5
        events_per_thread = 100
        
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=log_events, args=(i, events_per_thread))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = 0
        while not results.empty():
            result = results.get()
            if result[0] == 'success':
                success_count += 1
        
        assert success_count == num_threads, "Some threads failed"
    
    @pytest.mark.security
    def test_log_query_performance(self, audit_system):
        """Test log query performance"""
        import time
        
        # Log many events
        num_events = 10000
        for i in range(num_events):
            audit_system.log_user_activity(
                user_id=f'user-{i % 100}',
                action=f'action-{i}',
                session_id=f'sess-{i}',
                source_ip=f'192.168.1.{i % 255}'
            )
        
        # Test various queries
        queries = [
            {'limit': 100},
            {'user_id': 'user-1', 'limit': 50},
            {'start_date': datetime.utcnow() - timedelta(hours=1), 'limit': 100},
            {'event_type': 'user_activity', 'limit': 200},
        ]
        
        for query in queries:
            start_time = time.time()
            results = audit_system.get_audit_events(**query)
            end_time = time.time()
            
            query_time = end_time - start_time
            # Query should complete in reasonable time
            assert query_time < 1.0, f"Query too slow: {query_time}s for {query}"
    
    @pytest.mark.security
    def test_log_archive_performance(self, audit_system):
        """Test log archiving performance"""
        import time
        
        # Log many events
        num_events = 5000
        for i in range(num_events):
            # Log old events
            old_time = datetime.utcnow() - timedelta(days=100)
            audit_system.log_user_activity(
                user_id=f'user-{i}',
                action=f'action-{i}',
                session_id=f'sess-{i}',
                source_ip='192.168.1.100',
                timestamp=old_time
            )
        
        # Test archiving
        start_time = time.time()
        audit_system.archive_old_logs(days_to_keep=30)
        end_time = time.time()
        
        archive_time = end_time - start_time
        
        # Archiving should complete in reasonable time
        assert archive_time < 10.0, f"Archiving too slow: {archive_time}s"


class TestAuditRealTimeMonitoring:
    """Test suite for real-time audit monitoring"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp(prefix="audit_monitoring_test_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def audit_system(self, temp_dir):
        """Create audit system instance"""
        config = {
            'database_path': os.path.join(temp_dir, 'audit_test.db'),
            'key_file': os.path.join(temp_dir, 'audit.key'),
            'retention_days': 2555,
            'alert_thresholds': {
                'high_risk_events': 5,
                'failed_logins': 3
            }
        }
        return AuditLoggingSystem(config)
    
    @pytest.mark.security
    def test_real_time_alert_generation(self, audit_system):
        """Test real-time alert generation"""
        # Generate high-risk events
        for i in range(6):  # Above threshold
            audit_system.log_security_event(
                event_type='high_risk',
                severity='high',
                details={'risk_score': 0.9},
                source_ip='192.168.1.100'
            )
        
        # Check for generated alerts
        alerts = audit_system.get_security_alerts(limit=10)
        
        # Should have generated alerts
        high_risk_alerts = [a for a in alerts if a.get('alert_type') == 'high_risk_events']
        assert len(high_risk_alerts) > 0
    
    @pytest.mark.security
    def test_suspicious_activity_detection(self, audit_system):
        """Test suspicious activity detection"""
        # Generate suspicious activity pattern
        for i in range(20):  # Rapid failed logins
            audit_system.log_user_activity(
                user_id='suspicious-user',
                action='failed_login',
                session_id=f'sess-{i}',
                source_ip='192.168.1.100',
                outcome='failure'
            )
        
        # Check for suspicious activity detection
        suspicious_activities = audit_system.detect_suspicious_activities()
        
        assert len(suspicious_activities) > 0
        
        # Verify detection details
        activity = suspicious_activities[0]
        assert activity['user_id'] == 'suspicious-user'
        assert activity['pattern_type'] == 'rapid_failures'
    
    @pytest.mark.security
    def test_anomaly_detection(self, audit_system):
        """Test anomaly detection in audit logs"""
        # Normal user activity
        for i in range(10):
            audit_system.log_user_activity(
                user_id='normal-user',
                action='view_dashboard',
                session_id=f'sess-{i}',
                source_ip='192.168.1.100'
            )
        
        # Anomalous activity
        audit_system.log_user_activity(
            user_id='normal-user',
            action='mass_delete',
            session_id='anomalous-sess',
            source_ip='10.0.0.1'  # Different location
        )
        
        # Detect anomalies
        anomalies = audit_system.detect_anomalies()
        
        assert len(anomalies) > 0
        
        # Verify anomaly details
        anomaly = anomalies[0]
        assert anomaly['user_id'] == 'normal-user'
        assert 'anomaly_score' in anomaly
        assert anomaly['anomaly_score'] > 0.5
    
    @pytest.mark.security
    def test_compliance_violation_alerts(self, audit_system):
        """Test compliance violation alerts"""
        # Trigger compliance violations
        audit_system.log_data_access(
            user_id='unauthorized-user',
            resource='restricted_data',
            action='read',
            compliance_level=ComplianceLevel.HIPAA,
            details={'unauthorized': True}
        )
        
        # Check for compliance alerts
        compliance_alerts = audit_system.get_compliance_alerts()
        
        assert len(compliance_alerts) > 0
        
        # Verify alert details
        alert = compliance_alerts[0]
        assert alert['framework'] in ['GDPR', 'HIPAA', 'SOX', 'PCI_DSS']
        assert alert['severity'] in ['low', 'medium', 'high', 'critical']
    
    @pytest.mark.security
    def test_system_health_monitoring(self, audit_system):
        """Test audit system health monitoring"""
        # Check system health
        health_status = audit_system.get_system_health()
        
        assert 'system_status' in health_status
        assert health_status['system_status'] in ['HEALTHY', 'WARNING', 'CRITICAL']
        
        # Check individual components
        assert 'database' in health_status
        assert 'encryption' in health_status
        assert 'alert_system' in health_status


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "security"])
