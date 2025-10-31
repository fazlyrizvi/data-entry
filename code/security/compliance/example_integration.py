#!/usr/bin/env python3
"""
Example Integration Script
Demonstrates how to use the Compliance Audit Trail System
"""

import os
import sys
import json
import time
from datetime import datetime, timezone

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from audit_integrator import SecureAuditLogger, AuditMiddleware
from compliance_reporter import ComplianceReporter
from incident_detector import IncidentDetector

def main():
    print("=" * 70)
    print("Compliance Audit Trail System - Example Integration")
    print("=" * 70)
    print()
    
    # Initialize components
    print("1. Initializing Audit Logger...")
    logger = SecureAuditLogger(
        app_name="example_app",
        compliance_frameworks=['GDPR', 'HIPAA', 'SOC2', 'ISO27001']
    )
    
    print("2. Initializing Compliance Reporter...")
    reporter = ComplianceReporter(audit_logger=logger)
    
    print("3. Initializing Incident Detector...")
    detector = IncidentDetector(audit_logger=logger)
    print()
    
    # Demonstrate audit logging
    print("=" * 70)
    print("DEMONSTRATION: Audit Logging")
    print("=" * 70)
    print()
    
    # Log various types of events
    print("Logging user authentication events...")
    logger.log_event(
        action="USER_LOGIN",
        resource="user:12345",
        resource_type="AUTH",
        user_id="user12345",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        outcome="SUCCESS",
        risk_level="MEDIUM"
    )
    
    time.sleep(0.5)
    
    logger.log_event(
        action="USER_LOGIN",
        resource="user:12346",
        resource_type="AUTH",
        user_id="user12346",
        ip_address="192.168.1.100",
        outcome="FAILURE",
        details={'reason': 'invalid_credentials'},
        risk_level="HIGH"
    )
    
    time.sleep(0.5)
    
    print("Logging data access events...")
    logger.log_event(
        action="DATA_ACCESS",
        resource="customer_data",
        resource_type="DATA",
        user_id="user12345",
        outcome="SUCCESS",
        risk_level="HIGH",
        details={
            'records_accessed': 150,
            'query_type': 'SELECT',
            'fields': ['name', 'email', 'phone']
        },
        compliance_frameworks=['GDPR', 'HIPAA']
    )
    
    time.sleep(0.5)
    
    logger.log_event(
        action="DATA_EXPORT",
        resource="customer_data",
        resource_type="DATA",
        user_id="admin",
        outcome="SUCCESS",
        risk_level="CRITICAL",
        details={
            'export_format': 'CSV',
            'record_count': 1500,
            'exported_fields': ['all'],
            'purpose': 'business_analysis'
        },
        compliance_frameworks=['GDPR']
    )
    
    time.sleep(0.5)
    
    print("Logging system administration events...")
    logger.log_event(
        action="PRIVILEGE_ESCALATION",
        resource="system:admin",
        resource_type="SECURITY",
        user_id="admin",
        outcome="SUCCESS",
        risk_level="CRITICAL",
        details={
            'method': 'sudo',
            'command': 'systemctl restart service',
            'justification': 'emergency_fix'
        },
        compliance_frameworks=['SOC2', 'ISO27001']
    )
    
    time.sleep(0.5)
    
    print("Logging security events...")
    logger.log_event(
        action="SECURITY_INCIDENT",
        resource="security:malware_detection",
        resource_type="SECURITY",
        user_id="system",
        outcome="ALERT",
        risk_level="CRITICAL",
        details={
            'threat_type': 'malware',
            'file_path': '/tmp/suspicious.exe',
            'action_taken': 'quarantined'
        },
        compliance_frameworks=['SOC2', 'ISO27001']
    )
    
    time.sleep(0.5)
    
    print("Logging GDPR-specific events...")
    logger.log_event(
        action="DATA_SUBJECT_REQUEST",
        resource="dsr:right_to_be_forgotten",
        resource_type="GDPR_REQUEST",
        user_id="data_subject_001",
        outcome="SUCCESS",
        risk_level="MEDIUM",
        details={
            'request_type': 'erasure',
            'affected_records': 25,
            'retention_basis': 'consent_withdrawn',
            'verification_method': 'email_confirmation'
        },
        compliance_frameworks=['GDPR']
    )
    
    time.sleep(0.5)
    
    print("Logging HIPAA-specific events...")
    logger.log_event(
        action="PHI_ACCESS",
        resource="phi:patient_records",
        resource_type="HEALTHCARE_DATA",
        user_id="doctor_001",
        outcome="SUCCESS",
        risk_level="HIGH",
        details={
            'patient_count': 5,
            'access_purpose': 'treatment',
            'minimum_necessary': True,
            'authorized_by': 'patient_consent'
        },
        compliance_frameworks=['HIPAA']
    )
    
    time.sleep(0.5)
    
    print("Logging failed login attempts (for brute force detection)...")
    for i in range(5):
        logger.log_event(
            action="LOGIN_ATTEMPT",
            resource="auth:login",
            resource_type="AUTH",
            user_id="unknown_user",
            ip_address="192.168.1.200",
            outcome="FAILURE",
            details={'reason': 'invalid_password', 'attempt': i+1},
            risk_level="HIGH"
        )
        time.sleep(0.1)
    
    # Wait for events to be written
    time.sleep(2)
    
    print()
    print("✓ Audit events logged successfully!")
    print()
    
    # Demonstrate incident detection
    print("=" * 70)
    print("DEMONSTRATION: Security Incident Detection")
    print("=" * 70)
    print()
    
    print("Scanning for security incidents...")
    incidents = detector.scan_for_incidents()
    
    if incidents:
        print(f"\nFound {len(incidents)} security incidents:")
        print()
        
        for incident in incidents:
            print(f"  Incident ID: {incident.incident_id}")
            print(f"  Title: {incident.title}")
            print(f"  Severity: {incident.severity}")
            print(f"  Category: {incident.category}")
            print(f"  Status: {incident.status}")
            print(f"  Description: {incident.description}")
            print()
    else:
        print("No security incidents detected.")
    
    # Demonstrate compliance reporting
    print("=" * 70)
    print("DEMONSTRATION: Compliance Reporting")
    print("=" * 70)
    print()
    
    print("Generating compliance report...")
    report = reporter.generate_compliance_report(
        audit_db_path="./logs/audit.db",
        frameworks=['GDPR', 'HIPAA', 'SOC2', 'ISO27001']
    )
    
    print()
    print("Compliance Report Generated!")
    print()
    print("Executive Summary:")
    print("-" * 50)
    summary_text = reporter.generate_executive_summary(report)
    print(summary_text)
    
    # Display framework scores
    print()
    print("Framework Scores:")
    print("-" * 50)
    for framework, data in report.get('frameworks', {}).items():
        score = data.get('overall_score', 0)
        controls = data.get('control_results', [])
        compliant = sum(1 for c in controls if c['status'] == 'COMPLIANT')
        total = len(controls)
        print(f"  {framework:12}: {score:6.1f}% ({compliant}/{total} controls compliant)")
    
    # Demonstrate audit log retrieval
    print()
    print("=" * 70)
    print("DEMONSTRATION: Audit Log Retrieval")
    print("=" * 70)
    print()
    
    print("Retrieving recent audit events...")
    events = logger.get_events(limit=10)
    
    print(f"\nFound {len(events)} recent events:")
    print()
    
    for event in events:
        print(f"  {event['timestamp'][:19]} | {event['action']:25} | "
              f"{event['resource']:20} | {event['outcome']:8} | "
              f"{event['risk_level']:8}")
    
    # Demonstrate integrity verification
    print()
    print("=" * 70)
    print("DEMONSTRATION: Integrity Verification")
    print("=" * 70)
    print()
    
    print("Verifying audit log integrity...")
    integrity_result = logger.verify_integrity()
    
    print(f"  Total Events: {integrity_result['total_events']}")
    print(f"  Verified Events: {integrity_result['verified_events']}")
    print(f"  Tampered Events: {integrity_result['tampered_events']}")
    print(f"  Integrity Score: {integrity_result['integrity_score']:.1f}%")
    
    if integrity_result['integrity_score'] == 100.0:
        print("  ✓ All events verified - no tampering detected")
    else:
        print("  ⚠ Potential integrity issues detected")
    
    # Demonstrate middleware integration
    print()
    print("=" * 70)
    print("DEMONSTRATION: Audit Middleware")
    print("=" * 70)
    print()
    
    print("Creating audit middleware...")
    middleware = AuditMiddleware(logger)
    
    # Simulate HTTP request logging
    print("Simulating HTTP request logging...")
    request_data = {
        'path': '/api/v1/customers',
        'method': 'GET',
        'ip': '192.168.1.150',
        'user_agent': 'Mozilla/5.0',
        'status_code': 200
    }
    
    middleware.log_request(
        request_data=request_data,
        user_id="user12345",
        session_id="session_abc123"
    )
    
    print("✓ Request logged successfully")
    
    # Simulate data access logging
    print("Simulating data access logging...")
    middleware.log_data_access(
        data_type="customer_records",
        operation="read",
        user_id="user12345",
        success=True
    )
    
    print("✓ Data access logged successfully")
    
    # Final summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("✓ Audit Logger: Configured and operational")
    print("✓ Incident Detector: Configured and operational")
    print("✓ Compliance Reporter: Configured and operational")
    print("✓ Middleware Integration: Configured and operational")
    print("✓ Encryption: Enabled with tamper detection")
    print("✓ Real-time Monitoring: Started")
    print()
    print("System Status: ACTIVE")
    print()
    print("Next Steps:")
    print("  1. Review compliance report in ./reports/compliance/")
    print("  2. Monitor incidents in ./logs/incidents.db")
    print("  3. Check audit logs in ./logs/audit.db")
    print("  4. Configure alerting for production use")
    print()
    print("=" * 70)
    print("Integration demonstration completed successfully!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemonstration interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
