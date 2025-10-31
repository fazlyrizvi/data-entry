#!/usr/bin/env python3
"""
Compliance Reporter
Generates automated compliance reports for GDPR, HIPAA, SOC2, ISO27001
Supports regulatory reporting workflows and audit trail validation
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict
import hashlib
import statistics

# Import audit integrator
try:
    from audit_integrator import SecureAuditLogger, AuditEvent
except ImportError:
    print("Warning: audit_integrator not found. Running in standalone mode.")

# Configuration
COMPLIANCE_REPORTS_DIR = Path(os.environ.get('COMPLIANCE_REPORTS_DIR', './reports/compliance'))
COMPLIANCE_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class ComplianceControl:
    """Represents a compliance control requirement"""
    control_id: str
    framework: str
    title: str
    description: str
    category: str
    implementation_required: bool = True
    evidence_required: bool = True

@dataclass
class ComplianceStatus:
    """Status of a compliance control"""
    control_id: str
    framework: str
    status: str  # COMPLIANT, NON_COMPLIANT, PARTIAL, NOT_APPLICABLE
    score: float
    last_assessment: str
    evidence_count: int
    findings: List[str]
    recommendations: List[str]

class ComplianceFrameworks:
    """Defines compliance requirements for different frameworks"""
    
    GDPR_CONTROLS = [
        ComplianceControl("GDPR-1", "GDPR", "Data Protection Policy", 
                         "Organization has documented data protection policy", "Governance"),
        ComplianceControl("GDPR-2", "GDPR", "Data Subject Rights", 
                         "Data subject rights are implemented", "Rights Management"),
        ComplianceControl("GDPR-3", "GDPR", "Consent Management", 
                         "Consent management system is in place", "Consent"),
        ComplianceControl("GDPR-4", "GDPR", "Data Breach Notification", 
                         "Data breach notification procedures are defined", "Security"),
        ComplianceControl("GDPR-5", "GDPR", "Privacy by Design", 
                         "Privacy by design principles are implemented", "Design"),
        ComplianceControl("GDPR-6", "GDPR", "Data Portability", 
                         "Data portability is supported", "Rights Management"),
        ComplianceControl("GDPR-7", "GDPR", "Right to be Forgotten", 
                         "Data deletion procedures are implemented", "Rights Management"),
        ComplianceControl("GDPR-8", "GDPR", "Data Minimization", 
                         "Data minimization principles are followed", "Collection"),
    ]
    
    HIPAA_CONTROLS = [
        ComplianceControl("HIPAA-1", "HIPAA", "Administrative Safeguards", 
                         "Administrative safeguards are implemented", "Administrative"),
        ComplianceControl("HIPAA-2", "HIPAA", "Physical Safeguards", 
                         "Physical safeguards are in place", "Physical"),
        ComplianceControl("HIPAA-3", "HIPAA", "Technical Safeguards", 
                         "Technical safeguards are implemented", "Technical"),
        ComplianceControl("HIPAA-4", "HIPAA", "Access Control", 
                         "Access control mechanisms are enforced", "Access Control"),
        ComplianceControl("HIPAA-5", "HIPAA", "Audit Controls", 
                         "Audit controls and logging are active", "Audit"),
        ComplianceControl("HIPAA-6", "HIPAA", "Integrity Controls", 
                         "Data integrity is maintained", "Integrity"),
        ComplianceControl("HIPAA-7", "HIPAA", "Transmission Security", 
                         "Secure transmission mechanisms are used", "Transmission"),
    ]
    
    SOC2_CONTROLS = [
        ComplianceControl("SOC2-CC1", "SOC2", "Control Environment", 
                         "Control environment is established", "Common Criteria"),
        ComplianceControl("SOC2-CC2", "SOC2", "Logical Access", 
                         "Logical access controls are implemented", "Common Criteria"),
        ComplianceControl("SOC2-CC3", "SOC2", "Risk Assessment", 
                         "Risk assessment processes are in place", "Common Criteria"),
        ComplianceControl("SOC2-CC4", "SOC2", "Monitoring", 
                         "Monitoring activities are conducted", "Common Criteria"),
        ComplianceControl("SOC2-CC5", "SOC2", "Control Activities", 
                         "Control activities are performed", "Common Criteria"),
        ComplianceControl("SOC2-CC6", "SOC2", "Communication", 
                         "Information is communicated effectively", "Common Criteria"),
        ComplianceControl("SOC2-CC7", "SOC2", "Information System", 
                         "Information system is properly managed", "Common Criteria"),
        ComplianceControl("SOC2-PI1", "SOC2", "Processing Integrity", 
                         "System processing is complete and accurate", "Processing Integrity"),
        ComplianceControl("SOC2-PA1", "SOC2", "Privacy", 
                         "Privacy commitments are met", "Privacy"),
        ComplianceControl("SOC2-SI1", "SOC2", "Security", 
                         "System security is maintained", "Security"),
    ]
    
    ISO27001_CONTROLS = [
        ComplianceControl("ISO-A5", "ISO27001", "Information Security Policies", 
                         "Information security policies are established", "Policy"),
        ComplianceControl("ISO-A6", "ISO27001", "Organization of Information Security", 
                         "Information security responsibilities are defined", "Organization"),
        ComplianceControl("ISO-A7", "ISO27001", "Human Resource Security", 
                         "Human resource security is managed", "Human Resources"),
        ComplianceControl("ISO-A8", "ISO27001", "Asset Management", 
                         "Information assets are managed", "Asset Management"),
        ComplianceControl("ISO-A9", "ISO27001", "Access Control", 
                         "Access control policy is implemented", "Access Control"),
        ComplianceControl("ISO-A10", "ISO27001", "Cryptography", 
                         "Cryptography is properly implemented", "Cryptography"),
        ComplianceControl("ISO-A11", "ISO27001", "Physical and Environmental Security", 
                         "Physical security controls are in place", "Physical Security"),
        ComplianceControl("ISO-A12", "ISO27001", "Operations Security", 
                         "Operations security is maintained", "Operations"),
        ComplianceControl("ISO-A13", "ISO27001", "Communications Security", 
                         "Network security controls are implemented", "Network Security"),
        ComplianceControl("ISO-A14", "ISO27001", "System Acquisition, Development", 
                         "System security is built-in", "Development"),
        ComplianceControl("ISO-A15", "ISO27001", "Supplier Relationships", 
                         "Supplier security is managed", "Supplier Management"),
        ComplianceControl("ISO-A16", "ISO27001", "Incident Management", 
                         "Information security incidents are managed", "Incident Management"),
    ]

class ComplianceReporter:
    """Main compliance reporting engine"""
    
    def __init__(self, audit_logger: Optional[SecureAuditLogger] = None):
        self.audit_logger = audit_logger
        self.frameworks = ComplianceFrameworks()
        self.reports_dir = COMPLIANCE_REPORTS_DIR
        
        # Initialize status tracking
        self.control_status = self._load_control_status()
    
    def _load_control_status(self) -> Dict[str, ComplianceStatus]:
        """Load existing control status from database"""
        # In a real implementation, this would load from a database
        # For now, return empty dict
        return {}
    
    def assess_gdpr_compliance(self, audit_events: List[Dict]) -> Dict[str, Any]:
        """Assess GDPR compliance based on audit events"""
        print("Assessing GDPR Compliance...")
        
        assessment = {
            'framework': 'GDPR',
            'assessment_date': datetime.now(timezone.utc).isoformat(),
            'overall_score': 0.0,
            'control_results': [],
            'data_subject_requests': [],
            'consent_tracking': [],
            'data_breaches': [],
            'retention_compliance': []
        }
        
        # Analyze audit events for GDPR-specific patterns
        for event in audit_events:
            event_details = event.get('details', {})
            
            # Data Subject Requests
            if 'DSR' in event.get('action', '').upper() or 'data_subject' in str(event_details).lower():
                assessment['data_subject_requests'].append(event)
            
            # Consent Events
            if 'consent' in event.get('action', '').lower():
                assessment['consent_tracking'].append(event)
            
            # Data Breaches
            if 'breach' in event.get('action', '').lower() or event.get('risk_level') == 'CRITICAL':
                assessment['data_breaches'].append(event)
            
            # Data Retention
            if 'retention' in event.get('action', '').lower() or 'deletion' in event.get('action', '').lower():
                assessment['retention_compliance'].append(event)
        
        # Assess each control
        for control in self.frameworks.GDPR_CONTROLS:
            result = self._assess_control(control, assessment)
            assessment['control_results'].append(result)
        
        # Calculate overall score
        if assessment['control_results']:
            assessment['overall_score'] = statistics.mean([
                r['score'] for r in assessment['control_results']
            ])
        
        return assessment
    
    def assess_hipaa_compliance(self, audit_events: List[Dict]) -> Dict[str, Any]:
        """Assess HIPAA compliance based on audit events"""
        print("Assessing HIPAA Compliance...")
        
        assessment = {
            'framework': 'HIPAA',
            'assessment_date': datetime.now(timezone.utc).isoformat(),
            'overall_score': 0.0,
            'control_results': [],
            'phi_access': [],
            'audit_logs': [],
            'security_incidents': [],
            'access_violations': []
        }
        
        # Analyze audit events for HIPAA-specific patterns
        for event in audit_events:
            event_details = event.get('details', {})
            resource = event.get('resource', '').lower()
            
            # PHI Access
            if 'phi' in resource or 'protected' in resource or 'medical' in resource:
                assessment['phi_access'].append(event)
            
            # Audit Log Events
            if 'audit' in event.get('action', '').lower():
                assessment['audit_logs'].append(event)
            
            # Security Incidents
            if event.get('risk_level') in ['HIGH', 'CRITICAL']:
                assessment['security_incidents'].append(event)
            
            # Access Violations
            if event.get('outcome') == 'FAILURE' and 'access' in event.get('action', '').lower():
                assessment['access_violations'].append(event)
        
        # Assess each control
        for control in self.frameworks.HIPAA_CONTROLS:
            result = self._assess_control(control, assessment)
            assessment['control_results'].append(result)
        
        # Calculate overall score
        if assessment['control_results']:
            assessment['overall_score'] = statistics.mean([
                r['score'] for r in assessment['control_results']
            ])
        
        return assessment
    
    def assess_soc2_compliance(self, audit_events: List[Dict]) -> Dict[str, Any]:
        """Assess SOC2 compliance based on audit events"""
        print("Assessing SOC2 Compliance...")
        
        assessment = {
            'framework': 'SOC2',
            'assessment_date': datetime.now(timezone.utc).isoformat(),
            'overall_score': 0.0,
            'control_results': [],
            'access_controls': [],
            'system_operations': [],
            'data_integrity': [],
            'security_events': []
        }
        
        # Analyze audit events for SOC2-specific patterns
        for event in audit_events:
            event_details = event.get('details', {})
            
            # Access Controls
            if 'login' in event.get('action', '').lower() or 'access' in event.get('action', '').lower():
                assessment['access_controls'].append(event)
            
            # System Operations
            if any(term in event.get('action', '').lower() for term in ['deploy', 'config', 'update']):
                assessment['system_operations'].append(event)
            
            # Data Integrity
            if 'data' in event.get('resource', '').lower() and event.get('outcome') == 'SUCCESS':
                assessment['data_integrity'].append(event)
            
            # Security Events
            if event.get('risk_level') in ['HIGH', 'CRITICAL']:
                assessment['security_events'].append(event)
        
        # Assess each control
        for control in self.frameworks.SOC2_CONTROLS:
            result = self._assess_control(control, assessment)
            assessment['control_results'].append(result)
        
        # Calculate overall score
        if assessment['control_results']:
            assessment['overall_score'] = statistics.mean([
                r['score'] for r in assessment['control_results']
            ])
        
        return assessment
    
    def assess_iso27001_compliance(self, audit_events: List[Dict]) -> Dict[str, Any]:
        """Assess ISO27001 compliance based on audit events"""
        print("Assessing ISO27001 Compliance...")
        
        assessment = {
            'framework': 'ISO27001',
            'assessment_date': datetime.now(timezone.utc).isoformat(),
            'overall_score': 0.0,
            'control_results': [],
            'policy_compliance': [],
            'security_controls': [],
            'incident_management': [],
            'risk_management': []
        }
        
        # Analyze audit events for ISO27001-specific patterns
        for event in audit_events:
            event_details = event.get('details', {})
            
            # Policy Compliance
            if 'policy' in event.get('action', '').lower() or 'compliance' in event.get('action', '').lower():
                assessment['policy_compliance'].append(event)
            
            # Security Controls
            if any(term in event.get('action', '').lower() for term in ['encrypt', 'backup', 'restore']):
                assessment['security_controls'].append(event)
            
            # Incident Management
            if event.get('risk_level') in ['HIGH', 'CRITICAL'] or 'incident' in event.get('action', '').lower():
                assessment['incident_management'].append(event)
            
            # Risk Management
            if 'risk' in event.get('action', '').lower() or 'assessment' in event.get('action', '').lower():
                assessment['risk_management'].append(event)
        
        # Assess each control
        for control in self.frameworks.ISO27001_CONTROLS:
            result = self._assess_control(control, assessment)
            assessment['control_results'].append(result)
        
        # Calculate overall score
        if assessment['control_results']:
            assessment['overall_score'] = statistics.mean([
                r['score'] for r in assessment['control_results']
            ])
        
        return assessment
    
    def _assess_control(self, control: ComplianceControl, assessment: Dict) -> Dict[str, Any]:
        """Assess a specific compliance control"""
        # Get relevant events for this control
        relevant_events = self._get_relevant_events(control, assessment)
        
        # Calculate score based on evidence
        score = self._calculate_control_score(control, relevant_events)
        
        # Generate findings
        findings = self._generate_findings(control, relevant_events)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(control, findings)
        
        return {
            'control_id': control.control_id,
            'framework': control.framework,
            'title': control.title,
            'description': control.description,
            'status': self._determine_status(score),
            'score': score,
            'evidence_count': len(relevant_events),
            'findings': findings,
            'recommendations': recommendations,
            'last_assessment': datetime.now(timezone.utc).isoformat()
        }
    
    def _get_relevant_events(self, control: ComplianceControl, assessment: Dict) -> List[Dict]:
        """Get events relevant to a specific control"""
        # This is a simplified implementation
        # In practice, this would use more sophisticated logic
        
        keywords = {
            'GDPR': {
                'DSR': ['dsr', 'data_subject', 'access_request'],
                'Consent': ['consent', 'opt_in', 'opt_out'],
                'Security': ['breach', 'incident'],
                'Rights Management': ['delete', 'export', 'portability']
            },
            'HIPAA': {
                'Administrative': ['admin', 'policy', 'training'],
                'Physical': ['physical', 'facility'],
                'Technical': ['encryption', 'access_control'],
                'Access Control': ['login', 'access', 'authentication']
            },
            'SOC2': {
                'Common Criteria': ['control', 'access', 'risk'],
                'Processing Integrity': ['data', 'processing', 'accuracy'],
                'Privacy': ['privacy', 'consent'],
                'Security': ['security', 'encryption', 'backup']
            },
            'ISO27001': {
                'Policy': ['policy', 'procedure'],
                'Organization': ['organization', 'responsibility'],
                'Asset Management': ['asset', 'inventory'],
                'Incident Management': ['incident', 'breach']
            }
        }
        
        framework_keywords = keywords.get(control.framework, {})
        category_keywords = framework_keywords.get(control.category, [])
        
        relevant_events = []
        for category, events in assessment.items():
            if isinstance(events, list):
                for event in events:
                    if any(keyword in str(event).lower() for keyword in category_keywords):
                        relevant_events.append(event)
        
        return relevant_events
    
    def _calculate_control_score(self, control: ComplianceControl, events: List[Dict]) -> float:
        """Calculate compliance score for a control"""
        if not events:
            return 0.0
        
        # Base score on evidence quality and recency
        score = 50.0  # Base score for having some evidence
        
        # Bonus for recent events (last 30 days)
        recent_events = 0
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        for event in events:
            event_time = datetime.fromisoformat(event.get('timestamp', ''))
            if event_time > cutoff_date:
                recent_events += 1
        
        if recent_events > 0:
            score += min(30, recent_events * 10)  # Max 30 points for recency
        
        # Bonus for successful outcomes
        successful_events = sum(1 for event in events if event.get('outcome') == 'SUCCESS')
        if successful_events > 0:
            score += min(20, successful_events * 5)  # Max 20 points for success rate
        
        return min(100.0, score)
    
    def _determine_status(self, score: float) -> str:
        """Determine compliance status from score"""
        if score >= 80:
            return 'COMPLIANT'
        elif score >= 60:
            return 'PARTIAL'
        elif score >= 30:
            return 'NON_COMPLIANT'
        else:
            return 'NOT_APPLICABLE'
    
    def _generate_findings(self, control: ComplianceControl, events: List[Dict]) -> List[str]:
        """Generate findings for a control"""
        findings = []
        
        if not events:
            findings.append(f"No evidence found for {control.control_id}")
            return findings
        
        # Analyze patterns in events
        failure_count = sum(1 for event in events if event.get('outcome') == 'FAILURE')
        critical_events = [e for e in events if e.get('risk_level') == 'CRITICAL']
        
        if failure_count > 0:
            findings.append(f"Found {failure_count} failed operations")
        
        if critical_events:
            findings.append(f"Found {len(critical_events)} critical security events")
        
        if not findings:
            findings.append("Control appears to be functioning properly")
        
        return findings
    
    def _generate_recommendations(self, control: ComplianceControl, findings: List[str]) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []
        
        if "No evidence found" in findings[0]:
            recommendations.append(f"Implement monitoring for {control.control_id}")
            recommendations.append(f"Document {control.control_id} procedures")
        
        if "failed operations" in findings[0]:
            recommendations.append("Review and address failed operations")
            recommendations.append("Implement additional error handling")
        
        if "critical security events" in findings[0]:
            recommendations.append("Investigate critical security events immediately")
            recommendations.append("Review security incident response procedures")
        
        if not recommendations:
            recommendations.append("Continue monitoring and maintenance")
        
        return recommendations
    
    def generate_compliance_report(self, 
                                   audit_db_path: str,
                                   frameworks: List[str] = None) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        
        print(f"\nGenerating Compliance Report...")
        print(f"Frameworks: {frameworks or ['GDPR', 'HIPAA', 'SOC2', 'ISO27001']}")
        
        # Load audit events
        audit_events = self._load_audit_events(audit_db_path)
        
        if not audit_events:
            print("No audit events found for compliance assessment")
            return {}
        
        # Initialize report
        report = {
            'report_id': hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:16],
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'audit_period': {
                'start': audit_events[-1].get('timestamp') if audit_events else None,
                'end': audit_events[0].get('timestamp') if audit_events else None
            },
            'frameworks': {},
            'summary': {},
            'recommendations': []
        }
        
        # Assess each framework
        frameworks_to_assess = frameworks or ['GDPR', 'HIPAA', 'SOC2', 'ISO27001']
        
        for framework in frameworks_to_assess:
            if framework == 'GDPR':
                report['frameworks']['GDPR'] = self.assess_gdpr_compliance(audit_events)
            elif framework == 'HIPAA':
                report['frameworks']['HIPAA'] = self.assess_hipaa_compliance(audit_events)
            elif framework == 'SOC2':
                report['frameworks']['SOC2'] = self.assess_soc2_compliance(audit_events)
            elif framework == 'ISO27001':
                report['frameworks']['ISO27001'] = self.assess_iso27001_compliance(audit_events)
        
        # Generate summary
        report['summary'] = self._generate_report_summary(report['frameworks'])
        
        # Generate overall recommendations
        report['recommendations'] = self._generate_overall_recommendations(report['frameworks'])
        
        # Save report
        report_path = self._save_report(report)
        print(f"Compliance report saved to: {report_path}")
        
        # Log report generation
        if self.audit_logger:
            self.audit_logger.log_event(
                action="COMPLIANCE_REPORT_GENERATED",
                resource="compliance_report",
                resource_type="REPORT",
                details={
                    'frameworks': list(report['frameworks'].keys()),
                    'report_path': str(report_path),
                    'overall_score': report['summary'].get('overall_score', 0)
                },
                risk_level="MEDIUM"
            )
        
        return report
    
    def _load_audit_events(self, db_path: str) -> List[Dict]:
        """Load audit events from database"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.execute(
                "SELECT * FROM audit_events ORDER BY timestamp DESC LIMIT 1000"
            )
            
            events = []
            for row in cursor.fetchall():
                event = dict(zip([desc[0] for desc in cursor.description], row))
                event['details'] = json.loads(event['details'])
                event['compliance_frameworks'] = json.loads(event['compliance_frameworks'])
                events.append(event)
            
            conn.close()
            return events
        
        except Exception as e:
            print(f"Error loading audit events: {e}")
            return []
    
    def _generate_report_summary(self, frameworks_data: Dict) -> Dict[str, Any]:
        """Generate executive summary of compliance report"""
        summary = {
            'overall_score': 0.0,
            'compliant_controls': 0,
            'non_compliant_controls': 0,
            'partial_controls': 0,
            'total_controls': 0,
            'high_risk_issues': 0,
            'frameworks_summary': {}
        }
        
        all_scores = []
        
        for framework, data in frameworks_data.items():
            framework_score = data.get('overall_score', 0)
            all_scores.append(framework_score)
            
            controls = data.get('control_results', [])
            compliant = sum(1 for c in controls if c['status'] == 'COMPLIANT')
            non_compliant = sum(1 for c in controls if c['status'] == 'NON_COMPLIANT')
            partial = sum(1 for c in controls if c['status'] == 'PARTIAL')
            high_risk = sum(1 for c in controls if c.get('findings', []) and 
                          any('critical' in f.lower() for f in c['findings']))
            
            summary['compliant_controls'] += compliant
            summary['non_compliant_controls'] += non_compliant
            summary['partial_controls'] += partial
            summary['high_risk_issues'] += high_risk
            summary['total_controls'] += len(controls)
            
            summary['frameworks_summary'][framework] = {
                'score': framework_score,
                'compliant': compliant,
                'non_compliant': non_compliant,
                'partial': partial,
                'total': len(controls)
            }
        
        if all_scores:
            summary['overall_score'] = statistics.mean(all_scores)
        
        return summary
    
    def _generate_overall_recommendations(self, frameworks_data: Dict) -> List[str]:
        """Generate overall recommendations"""
        recommendations = []
        
        # Collect all recommendations
        all_recommendations = []
        for framework, data in frameworks_data.items():
            for control in data.get('control_results', []):
                all_recommendations.extend(control.get('recommendations', []))
        
        # Deduplicate and prioritize
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        
        # Prioritize high-impact recommendations
        high_priority = [r for r in unique_recommendations if any(
            keyword in r.lower() for keyword in ['critical', 'immediate', 'high risk']
        )]
        
        recommendations.extend(high_priority)
        recommendations.extend([r for r in unique_recommendations if r not in high_priority])
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _save_report(self, report: Dict[str, Any]) -> Path:
        """Save report to file"""
        report_id = report['report_id']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        report_path = self.reports_dir / f"compliance_report_{timestamp}_{report_id}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report_path
    
    def generate_executive_summary(self, report: Dict[str, Any]) -> str:
        """Generate executive summary text"""
        summary = report.get('summary', {})
        frameworks = report.get('frameworks', {})
        
        text = f"""
COMPLIANCE ASSESSMENT EXECUTIVE SUMMARY
=====================================

Report ID: {report.get('report_id')}
Generated: {report.get('generated_at')}

OVERALL COMPLIANCE SCORE: {summary.get('overall_score', 0):.1f}%

FRAMEWORK SCORES:
"""
        
        for framework, data in frameworks.items():
            score = data.get('overall_score', 0)
            text += f"  {framework}: {score:.1f}%\n"
        
        text += f"""
CONTROLS STATUS:
  Compliant: {summary.get('compliant_controls', 0)}/{summary.get('total_controls', 0)}
  Non-Compliant: {summary.get('non_compliant_controls', 0)}
  Partial: {summary.get('partial_controls', 0)}
  High-Risk Issues: {summary.get('high_risk_issues', 0)}

TOP RECOMMENDATIONS:
"""
        
        for i, rec in enumerate(report.get('recommendations', [])[:5], 1):
            text += f"  {i}. {rec}\n"
        
        return text


def generate_regulatory_report(framework: str, 
                              audit_db_path: str,
                              report_type: str = "full") -> str:
    """Generate specific regulatory report"""
    reporter = ComplianceReporter()
    
    if report_type == "gdpr_dsr":
        return "GDPR Data Subject Request Report Template"
    elif report_type == "hipaa_safeguards":
        return "HIPAA Safeguards Assessment Report"
    elif report_type == "soc2_trust_services":
        return "SOC2 Trust Services Criteria Report"
    elif report_type == "iso27001_annex_a":
        return "ISO27001 Annex A Controls Assessment"
    else:
        return reporter.generate_compliance_report(audit_db_path, [framework])


if __name__ == "__main__":
    print("Compliance Reporter - Regulatory Reporting System")
    print("=" * 55)
    
    # Example usage
    reporter = ComplianceReporter()
    
    # Generate comprehensive compliance report
    report = reporter.generate_compliance_report(
        audit_db_path="./logs/audit.db",
        frameworks=['GDPR', 'HIPAA', 'SOC2', 'ISO27001']
    )
    
    print("\nReport Summary:")
    print(reporter.generate_executive_summary(report))
    
    print("\nCompliance reporting completed!")
