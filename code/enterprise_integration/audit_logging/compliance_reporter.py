"""
Compliance Reporter - Automated compliance reporting for GDPR, HIPAA, SOX, PCI-DSS
Generates comprehensive audit reports and compliance assessments
"""

import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter

from log_collector import LogCollector, AuditEvent, AuditEventType, ComplianceLevel


class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"
    NIST = "nist"


class ReportType(Enum):
    """Types of compliance reports"""
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_AUDIT = "detailed_audit"
    INCIDENT_REPORT = "incident_report"
    USER_ACTIVITY = "user_activity"
    DATA_ACCESS = "data_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_GAP = "compliance_gap"


@dataclass
class ComplianceMetric:
    """Compliance metric data structure"""
    framework: ComplianceFramework
    requirement: str
    status: str  # COMPLIANT, NON_COMPLIANT, PARTIAL, NOT_ASSESSED
    score: float  # 0-100
    evidence_count: int
    last_assessment: datetime
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    details: Dict[str, Any]


class ComplianceReporter:
    """Generate comprehensive compliance reports"""
    
    def __init__(self, log_collector: LogCollector):
        self.log_collector = log_collector
        self.logger = logging.getLogger('compliance_reporter')
        
        # Compliance framework mappings
        self.framework_requirements = {
            ComplianceFramework.GDPR: {
                'personal_data_processing': self._check_gdpr_personal_data,
                'consent_management': self._check_gdpr_consent,
                'data_retention': self._check_gdpr_retention,
                'data_subject_rights': self._check_gdpr_subject_rights,
                'breach_notification': self._check_gdpr_breach_notification,
                'privacy_by_design': self._check_gdpr_privacy_by_design,
                'data_protection_officer': self._check_gdpr_dpo,
                'cross_border_transfer': self._check_gdpr_transfer
            },
            ComplianceFramework.HIPAA: {
                'access_controls': self._check_hipaa_access_controls,
                'audit_controls': self._check_hipaa_audit_controls,
                'integrity': self._check_hipaa_integrity,
                'person_or_entity_auth': self._check_hipaa_authentication,
                'transmission_security': self._check_hipaa_transmission,
                'security_incidents': self._check_hipaa_incidents,
                'risk_analysis': self._check_hipaa_risk_analysis,
                'workforce_training': self._check_hipaa_training
            },
            ComplianceFramework.SOX: {
                'internal_controls': self._check_sox_controls,
                'segregation_of_duties': self._check_sox_segregation,
                'change_management': self._check_sox_change_mgmt,
                'financial_data_access': self._check_sox_financial_access,
                'transaction_monitoring': self._check_sox_monitoring,
                'audit_trail': self._check_sox_audit_trail,
                'management_certification': self._check_sox_certification
            },
            ComplianceFramework.PCI_DSS: {
                'cardholder_data_protection': self._check_pci_data_protection,
                'vulnerability_management': self._check_pci_vulnerability,
                'access_control': self._check_pci_access_control,
                'network_security': self._check_pci_network_security,
                'monitoring_and_testing': self._check_pci_monitoring,
                'security_policy': self._check_pci_policy
            }
        }
    
    def generate_compliance_report(self, framework: ComplianceFramework, 
                                 start_date: datetime, end_date: datetime,
                                 report_type: ReportType = ReportType.EXECUTIVE_SUMMARY) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        
        self.logger.info(f"Generating {report_type.value} report for {framework.value}")
        
        # Get relevant audit events
        events = self._get_compliance_events(framework, start_date, end_date)
        
        # Generate base report
        report = {
            'report_id': f"{framework.value}_{report_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'framework': framework.value,
            'report_type': report_type.value,
            'generated_at': datetime.now().isoformat(),
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'duration_days': (end_date - start_date).days
            },
            'summary': self._generate_summary(framework, events),
            'metrics': self._calculate_metrics(framework, events),
            'compliance_assessment': self._assess_compliance(framework, events),
            'findings': self._identify_findings(framework, events),
            'recommendations': self._generate_recommendations(framework, events),
            'data_analysis': self._analyze_data(events),
            'visualizations': self._create_visualizations(events, framework),
            'supporting_evidence': self._gather_evidence(events)
        }
        
        return report
    
    def _get_compliance_events(self, framework: ComplianceFramework, 
                             start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get relevant audit events for compliance framework"""
        
        filters = {
            'start_time': start_date.isoformat(),
            'end_time': end_date.isoformat()
        }
        
        events = self.log_collector.get_events(filters, limit=10000)
        
        # Filter by compliance level
        if framework == ComplianceFramework.GDPR:
            compliance_levels = [ComplianceLevel.GDPR.value, ComplianceLevel.STANDARD.value]
        elif framework == ComplianceFramework.HIPAA:
            compliance_levels = [ComplianceLevel.HIPAA.value, ComplianceLevel.STANDARD.value]
        elif framework == ComplianceFramework.SOX:
            compliance_levels = [ComplianceLevel.SOX.value, ComplianceLevel.STANDARD.value]
        else:
            compliance_levels = [ComplianceLevel.STANDARD.value]
            
        filtered_events = [event for event in events if event.get('compliance_level') in compliance_levels]
        
        return filtered_events
    
    def _generate_summary(self, framework: ComplianceFramework, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate executive summary"""
        
        total_events = len(events)
        event_types = Counter(event.get('event_type', 'unknown') for event in events)
        compliance_events = [e for e in events if e.get('compliance_level') == framework.value]
        
        # Calculate key metrics
        high_risk_events = [e for e in events if e.get('risk_score', 0) >= 70]
        failed_events = [e for e in events if e.get('outcome') == 'FAILURE']
        
        return {
            'total_audit_events': total_events,
            'compliance_specific_events': len(compliance_events),
            'event_types': dict(event_types),
            'high_risk_events': len(high_risk_events),
            'failed_events': len(failed_events),
            'compliance_rate': len(compliance_events) / total_events * 100 if total_events > 0 else 0,
            'risk_distribution': {
                'critical': len([e for e in events if e.get('risk_score', 0) >= 90]),
                'high': len([e for e in events if 70 <= e.get('risk_score', 0) < 90]),
                'medium': len([e for e in events if 40 <= e.get('risk_score', 0) < 70]),
                'low': len([e for e in events if e.get('risk_score', 0) < 40])
            },
            'top_event_types': dict(event_types.most_common(5))
        }
    
    def _calculate_metrics(self, framework: ComplianceFramework, events: List[Dict[str, Any]]) -> List[ComplianceMetric]:
        """Calculate compliance metrics for framework"""
        
        metrics = []
        
        if framework in self.framework_requirements:
            for requirement, check_function in self.framework_requirements[framework].items():
                metric = check_function(events)
                metrics.append(metric)
        
        return metrics
    
    def _calculate_safe_correlation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate correlation safely for mixed data types"""
        try:
            # Select only numeric columns for correlation
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 1:
                return df[numeric_cols].corr().to_dict()
            else:
                return {}
        except Exception:
            return {}
    
    def _assess_compliance(self, framework: ComplianceFramework, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall compliance status"""
        
        metrics = self._calculate_metrics(framework, events)
        
        total_score = sum(metric.score for metric in metrics) / len(metrics) if metrics else 0
        
        compliant_count = len([m for m in metrics if m.status == 'COMPLIANT'])
        non_compliant_count = len([m for m in metrics if m.status == 'NON_COMPLIANT'])
        
        compliance_status = 'NON_COMPLIANT' if non_compliant_count > len(metrics) * 0.2 else 'COMPLIANT'
        
        return {
            'overall_score': total_score,
            'compliance_status': compliance_status,
            'compliant_requirements': compliant_count,
            'non_compliant_requirements': non_compliant_count,
            'total_requirements': len(metrics),
            'compliance_percentage': (compliant_count / len(metrics)) * 100 if metrics else 0,
            'risk_summary': {
                'critical_risks': len([m for m in metrics if m.risk_level == 'CRITICAL']),
                'high_risks': len([m for m in metrics if m.risk_level == 'HIGH']),
                'medium_risks': len([m for m in metrics if m.risk_level == 'MEDIUM']),
                'low_risks': len([m for m in metrics if m.risk_level == 'LOW'])
            }
        }
    
    def _identify_findings(self, framework: ComplianceFramework, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify compliance findings and issues"""
        
        findings = []
        
        # High-risk events
        high_risk_events = [e for e in events if e.get('risk_score', 0) >= 80]
        for event in high_risk_events:
            findings.append({
                'type': 'HIGH_RISK_EVENT',
                'severity': 'HIGH',
                'description': f"High-risk event detected: {event.get('event_type', 'Unknown')} by user {event.get('user_id', 'Unknown')}",
                'event_id': event.get('event_id'),
                'timestamp': event.get('timestamp'),
                'recommendation': 'Review and investigate immediately'
            })
        
        # Failed authentication attempts
        failed_logins = [e for e in events if e.get('event_type') == 'user_login_failed']
        if len(failed_logins) > 10:
            findings.append({
                'type': 'EXCESSIVE_FAILED_LOGINS',
                'severity': 'MEDIUM',
                'description': f"Excessive failed login attempts: {len(failed_logins)}",
                'recommendation': 'Review access controls and consider account lockout policies'
            })
        
        # Privilege escalation attempts
        privilege_events = [e for e in events if 'privilege' in (e.get('action') or '').lower()]
        for event in privilege_events:
            findings.append({
                'type': 'PRIVILEGE_ACTIVITY',
                'severity': 'HIGH' if event.get('outcome') == 'FAILURE' else 'MEDIUM',
                'description': f"Privilege-related activity: {event.get('action')}",
                'event_id': event.get('event_id'),
                'recommendation': 'Verify proper authorization and document business justification'
            })
        
        # GDPR specific findings
        if framework == ComplianceFramework.GDPR:
            gdpr_findings = self._identify_gdpr_findings(events)
            findings.extend(gdpr_findings)
        
        return findings
    
    def _identify_gdpr_findings(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify GDPR-specific findings"""
        
        findings = []
        
        # Check for personal data access without consent
        personal_data_events = [e for e in events 
                              if any(keyword in (e.get('resource') or '').lower() 
                                   for keyword in ['personal', 'customer', 'client'])]
        
        consent_missing = [e for e in personal_data_events 
                         if not e.get('details', {}).get('consent_given', True)]
        
        if consent_missing:
            findings.append({
                'type': 'GDPR_DATA_PROCESSING_WITHOUT_CONSENT',
                'severity': 'CRITICAL',
                'description': f"Found {len(consent_missing)} personal data accesses without documented consent",
                'recommendation': 'Implement consent management and document all consent records'
            })
        
        return findings
    
    def _generate_recommendations(self, framework: ComplianceFramework, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate compliance recommendations"""
        
        recommendations = []
        
        # Framework-specific recommendations
        if framework == ComplianceFramework.GDPR:
            recommendations.extend([
                {
                    'priority': 'HIGH',
                    'category': 'Consent Management',
                    'recommendation': 'Implement comprehensive consent tracking system',
                    'rationale': 'GDPR Article 7 requires demonstrable consent',
                    'implementation': 'Deploy consent management platform and integrate with audit system'
                },
                {
                    'priority': 'MEDIUM',
                    'category': 'Data Retention',
                    'recommendation': 'Automate data retention and deletion processes',
                    'rationale': 'GDPR Article 5(1)(e) - storage limitation principle',
                    'implementation': 'Set up automated retention policies and deletion workflows'
                }
            ])
        
        elif framework == ComplianceFramework.HIPAA:
            recommendations.extend([
                {
                    'priority': 'HIGH',
                    'category': 'Access Controls',
                    'recommendation': 'Implement principle of least privilege for PHI access',
                    'rationale': 'HIPAA Security Rule requires appropriate access controls',
                    'implementation': 'Review user permissions and implement role-based access control'
                },
                {
                    'priority': 'HIGH',
                    'category': 'Audit Logging',
                    'recommendation': 'Enable real-time audit monitoring for PHI access',
                    'rationale': 'HIPAA requires audit controls and activity review',
                    'implementation': 'Set up automated alerts for PHI access patterns'
                }
            ])
        
        elif framework == ComplianceFramework.SOX:
            recommendations.extend([
                {
                    'priority': 'HIGH',
                    'category': 'Segregation of Duties',
                    'recommendation': 'Implement segregation of duties controls',
                    'rationale': 'SOX Section 404 requires internal controls',
                    'implementation': 'Separate transaction initiation, authorization, and recording functions'
                }
            ])
        
        return recommendations
    
    def _analyze_data(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform data analysis on audit events"""
        
        if not events:
            return {}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(events)
        
        analysis = {
            'temporal_analysis': self._analyze_temporal_patterns(df),
            'user_analysis': self._analyze_user_behavior(df),
            'risk_analysis': self._analyze_risk_patterns(df),
            'resource_analysis': self._analyze_resource_access(df)
        }
        
        return analysis
    
    def _analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze temporal patterns in audit events"""
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        
        return {
            'events_by_hour': df['hour'].value_counts().to_dict(),
            'events_by_day': df['day_of_week'].value_counts().to_dict(),
            'peak_activity_hour': df['hour'].mode().iloc[0] if not df['hour'].empty else None,
            'low_activity_hours': df['hour'].value_counts().tail(3).to_dict()
        }
    
    def _analyze_user_behavior(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        
        user_stats = df.groupby('user_id').agg({
            'event_id': 'count',
            'risk_score': ['mean', 'max'],
            'outcome': lambda x: (x == 'FAILURE').sum()
        }).round(2)
        
        user_stats.columns = ['total_events', 'avg_risk_score', 'max_risk_score', 'failed_events']
        
        return {
            'active_users': len(user_stats),
            'top_users_by_activity': user_stats.sort_values('total_events', ascending=False).head(10).to_dict(),
            'high_risk_users': user_stats[user_stats['max_risk_score'] >= 80].to_dict(),
            'users_with_failures': user_stats[user_stats['failed_events'] > 0].to_dict()
        }
    
    def _analyze_risk_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze risk patterns in audit events"""
        
        risk_analysis = {
            'average_risk_score': df['risk_score'].mean(),
            'risk_distribution': df['risk_score'].value_counts().to_dict(),
            'high_risk_events_by_type': df[df['risk_score'] >= 70]['event_type'].value_counts().to_dict(),
            'risk_correlation': self._calculate_safe_correlation(df)
        }
        
        return risk_analysis
    
    def _analyze_resource_access(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze resource access patterns"""
        
        resource_stats = df.groupby('resource').agg({
            'event_id': 'count',
            'user_id': 'nunique',
            'risk_score': 'mean'
        }).round(2)
        
        resource_stats.columns = ['access_count', 'unique_users', 'avg_risk_score']
        
        return {
            'most_accessed_resources': resource_stats.sort_values('access_count', ascending=False).head(10).to_dict(),
            'high_risk_resources': resource_stats[resource_stats['avg_risk_score'] >= 70].to_dict(),
            'resources_by_unique_users': resource_stats.sort_values('unique_users', ascending=False).head(10).to_dict()
        }
    
    def _create_visualizations(self, events: List[Dict[str, Any]], framework: ComplianceFramework) -> Dict[str, str]:
        """Create visualization charts for the report"""
        
        if not events:
            return {}
        
        # Use non-interactive backend for headless environments
        import matplotlib
        matplotlib.use('Agg')
        
        import matplotlib.pyplot as plt
        
        df = pd.DataFrame(events)
        
        visualizations = {}
        
        # Event type distribution
        plt.figure(figsize=(10, 6))
        event_counts = df['event_type'].value_counts().head(10)
        plt.pie(event_counts.values, labels=event_counts.index, autopct='%1.1f%%')
        plt.title(f'{framework.value.upper()} Event Type Distribution')
        plt.tight_layout()
        
        viz_path = Path('compliance_visuals')
        viz_path.mkdir(exist_ok=True)
        
        event_type_chart = viz_path / f"{framework.value}_event_types.png"
        plt.savefig(event_type_chart)
        plt.close()
        visualizations['event_type_distribution'] = str(event_type_chart)
        
        # Risk score histogram
        plt.figure(figsize=(10, 6))
        plt.hist(df['risk_score'].dropna(), bins=20, edgecolor='black')
        plt.xlabel('Risk Score')
        plt.ylabel('Frequency')
        plt.title(f'{framework.value.upper()} Risk Score Distribution')
        plt.tight_layout()
        
        risk_chart = viz_path / f"{framework.value}_risk_distribution.png"
        plt.savefig(risk_chart)
        plt.close()
        visualizations['risk_distribution'] = str(risk_chart)
        
        return visualizations
    
    def _gather_evidence(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Gather supporting evidence for compliance claims"""
        
        evidence = {
            'sample_events': [],
            'log_integrity': self.log_collector.verify_integrity(),
            'event_statistics': {}
        }
        
        # Sample events for evidence
        sample_events = events[:10]  # First 10 events
        for event in sample_events:
            evidence['sample_events'].append({
                'event_id': event.get('event_id'),
                'timestamp': event.get('timestamp'),
                'event_type': event.get('event_type'),
                'user_id': event.get('user_id'),
                'action': event.get('action'),
                'outcome': event.get('outcome'),
                'risk_score': event.get('risk_score'),
                'compliance_level': event.get('compliance_level')
            })
        
        # Event statistics
        if events:
            evidence['event_statistics'] = {
                'total_events': len(events),
                'unique_users': len(set(event.get('user_id') for event in events if event.get('user_id'))),
                'event_types': len(set(event.get('event_type') for event in events)),
                'time_range': {
                    'earliest': min(event.get('timestamp') for event in events),
                    'latest': max(event.get('timestamp') for event in events)
                }
            }
        
        return evidence
    
    # Compliance requirement checkers
    
    def _check_gdpr_personal_data(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check GDPR personal data processing requirements"""
        
        personal_data_events = [e for e in events 
                              if any(keyword in (e.get('resource') or '').lower() 
                                   for keyword in ['personal', 'customer', 'client', 'email', 'phone'])]
        
        compliance_score = 100 if personal_data_events else 80
        
        return ComplianceMetric(
            framework=ComplianceFramework.GDPR,
            requirement='Personal Data Processing',
            status='COMPLIANT' if compliance_score >= 80 else 'NON_COMPLIANT',
            score=compliance_score,
            evidence_count=len(personal_data_events),
            last_assessment=datetime.now(),
            risk_level='MEDIUM' if compliance_score < 90 else 'LOW',
            details={'personal_data_events': len(personal_data_events)}
        )
    
    def _check_gdpr_consent(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check GDPR consent management requirements"""
        
        personal_data_events = [e for e in events 
                              if any(keyword in (e.get('resource') or '').lower() 
                                   for keyword in ['personal', 'customer', 'client'])]
        
        events_with_consent = [e for e in personal_data_events 
                             if e.get('details', {}).get('consent_given', False)]
        
        consent_rate = len(events_with_consent) / len(personal_data_events) * 100 if personal_data_events else 100
        
        return ComplianceMetric(
            framework=ComplianceFramework.GDPR,
            requirement='Consent Management',
            status='COMPLIANT' if consent_rate >= 95 else 'NON_COMPLIANT',
            score=consent_rate,
            evidence_count=len(events_with_consent),
            last_assessment=datetime.now(),
            risk_level='CRITICAL' if consent_rate < 80 else 'HIGH',
            details={'consent_rate': consent_rate, 'total_processing': len(personal_data_events)}
        )
    
    def _check_gdpr_retention(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check GDPR data retention requirements"""
        
        retention_events = [e for e in events if 'retention' in (e.get('action') or '').lower()]
        
        return ComplianceMetric(
            framework=ComplianceFramework.GDPR,
            requirement='Data Retention',
            status='COMPLIANT' if len(retention_events) > 0 else 'PARTIAL',
            score=80,
            evidence_count=len(retention_events),
            last_assessment=datetime.now(),
            risk_level='MEDIUM',
            details={'retention_events': len(retention_events)}
        )
    
    def _check_gdpr_subject_rights(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check GDPR data subject rights"""
        
        subject_rights_events = [e for e in events 
                               if any(action in (e.get('action') or '').lower() 
                                    for action in ['access', 'rectification', 'erasure', 'portability'])]
        
        return ComplianceMetric(
            framework=ComplianceFramework.GDPR,
            requirement='Data Subject Rights',
            status='COMPLIANT' if len(subject_rights_events) > 0 else 'PARTIAL',
            score=75,
            evidence_count=len(subject_rights_events),
            last_assessment=datetime.now(),
            risk_level='MEDIUM',
            details={'subject_rights_events': len(subject_rights_events)}
        )
    
    def _check_gdpr_breach_notification(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check GDPR breach notification requirements"""
        
        security_incidents = [e for e in events if e.get('event_type') == 'security_event']
        
        return ComplianceMetric(
            framework=ComplianceFramework.GDPR,
            requirement='Breach Notification',
            status='COMPLIANT' if len(security_incidents) > 0 else 'COMPLIANT',
            score=100,
            evidence_count=len(security_incidents),
            last_assessment=datetime.now(),
            risk_level='LOW',
            details={'security_incidents': len(security_incidents)}
        )
    
    def _check_gdpr_privacy_by_design(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check GDPR privacy by design requirements"""
        
        privacy_events = [e for e in events if 'privacy' in (e.get('action') or '').lower()]
        
        return ComplianceMetric(
            framework=ComplianceFramework.GDPR,
            requirement='Privacy by Design',
            status='COMPLIANT' if len(privacy_events) > 0 else 'PARTIAL',
            score=70,
            evidence_count=len(privacy_events),
            last_assessment=datetime.now(),
            risk_level='MEDIUM',
            details={'privacy_events': len(privacy_events)}
        )
    
    def _check_gdpr_dpo(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check GDPR Data Protection Officer requirements"""
        
        dpo_events = [e for e in events if 'dpo' in (e.get('action') or '').lower()]
        
        return ComplianceMetric(
            framework=ComplianceFramework.GDPR,
            requirement='Data Protection Officer',
            status='COMPLIANT' if len(dpo_events) > 0 else 'NOT_ASSESSED',
            score=80,
            evidence_count=len(dpo_events),
            last_assessment=datetime.now(),
            risk_level='LOW',
            details={'dpo_events': len(dpo_events)}
        )
    
    def _check_gdpr_transfer(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check GDPR cross-border data transfer requirements"""
        
        transfer_events = [e for e in events if 'transfer' in (e.get('action') or '').lower()]
        
        return ComplianceMetric(
            framework=ComplianceFramework.GDPR,
            requirement='Cross-Border Transfer',
            status='COMPLIANT' if len(transfer_events) > 0 else 'NOT_ASSESSED',
            score=75,
            evidence_count=len(transfer_events),
            last_assessment=datetime.now(),
            risk_level='MEDIUM',
            details={'transfer_events': len(transfer_events)}
        )
    
    # HIPAA compliance checkers (simplified implementations)
    
    def _check_hipaa_access_controls(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check HIPAA access controls"""
        
        access_events = [e for e in events if e.get('event_type') == 'data_access']
        
        return ComplianceMetric(
            framework=ComplianceFramework.HIPAA,
            requirement='Access Controls',
            status='COMPLIANT' if len(access_events) > 0 else 'PARTIAL',
            score=90,
            evidence_count=len(access_events),
            last_assessment=datetime.now(),
            risk_level='MEDIUM',
            details={'access_events': len(access_events)}
        )
    
    def _check_hipaa_audit_controls(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check HIPAA audit controls"""
        
        return ComplianceMetric(
            framework=ComplianceFramework.HIPAA,
            requirement='Audit Controls',
            status='COMPLIANT',
            score=95,
            evidence_count=len(events),
            last_assessment=datetime.now(),
            risk_level='LOW',
            details={'total_events': len(events)}
        )
    
    def _check_hipaa_integrity(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check HIPAA integrity requirements"""
        
        modify_events = [e for e in events if 'modify' in (e.get('action') or '').lower()]
        
        return ComplianceMetric(
            framework=ComplianceFramework.HIPAA,
            requirement='Integrity',
            status='COMPLIANT' if len(modify_events) > 0 else 'COMPLIANT',
            score=85,
            evidence_count=len(modify_events),
            last_assessment=datetime.now(),
            risk_level='LOW',
            details={'modify_events': len(modify_events)}
        )
    
    def _check_hipaa_authentication(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check HIPAA authentication requirements"""
        
        auth_events = [e for e in events if 'login' in e.get('event_type', '')]
        
        return ComplianceMetric(
            framework=ComplianceFramework.HIPAA,
            requirement='Person or Entity Authentication',
            status='COMPLIANT' if len(auth_events) > 0 else 'PARTIAL',
            score=90,
            evidence_count=len(auth_events),
            last_assessment=datetime.now(),
            risk_level='MEDIUM',
            details={'auth_events': len(auth_events)}
        )
    
    def _check_hipaa_transmission(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check HIPAA transmission security"""
        
        network_events = [e for e in events if e.get('event_type') == 'network_access']
        
        return ComplianceMetric(
            framework=ComplianceFramework.HIPAA,
            requirement='Transmission Security',
            status='COMPLIANT' if len(network_events) > 0 else 'PARTIAL',
            score=80,
            evidence_count=len(network_events),
            last_assessment=datetime.now(),
            risk_level='MEDIUM',
            details={'network_events': len(network_events)}
        )
    
    def _check_hipaa_incidents(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check HIPAA security incidents"""
        
        security_events = [e for e in events if e.get('event_type') == 'security_event']
        
        return ComplianceMetric(
            framework=ComplianceFramework.HIPAA,
            requirement='Security Incidents',
            status='COMPLIANT',
            score=100,
            evidence_count=len(security_events),
            last_assessment=datetime.now(),
            risk_level='LOW',
            details={'security_events': len(security_events)}
        )
    
    def _check_hipaa_risk_analysis(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check HIPAA risk analysis"""
        
        high_risk_events = [e for e in events if e.get('risk_score', 0) >= 70]
        
        return ComplianceMetric(
            framework=ComplianceFramework.HIPAA,
            requirement='Risk Analysis',
            status='COMPLIANT',
            score=90,
            evidence_count=len(high_risk_events),
            last_assessment=datetime.now(),
            risk_level='MEDIUM',
            details={'high_risk_events': len(high_risk_events)}
        )
    
    def _check_hipaa_training(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check HIPAA workforce training"""
        
        training_events = [e for e in events if 'training' in (e.get('action') or '').lower()]
        
        return ComplianceMetric(
            framework=ComplianceFramework.HIPAA,
            requirement='Workforce Training',
            status='PARTIAL' if len(training_events) == 0 else 'COMPLIANT',
            score=70 if len(training_events) == 0 else 90,
            evidence_count=len(training_events),
            last_assessment=datetime.now(),
            risk_level='MEDIUM',
            details={'training_events': len(training_events)}
        )
    
    # SOX compliance checkers (simplified implementations)
    
    def _check_sox_controls(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check SOX internal controls"""
        
        config_events = [e for e in events if e.get('event_type') == 'system_config_change']
        
        return ComplianceMetric(
            framework=ComplianceFramework.SOX,
            requirement='Internal Controls',
            status='COMPLIANT' if len(config_events) > 0 else 'PARTIAL',
            score=85,
            evidence_count=len(config_events),
            last_assessment=datetime.now(),
            risk_level='MEDIUM',
            details={'config_events': len(config_events)}
        )
    
    def _check_sox_segregation(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check SOX segregation of duties"""
        
        return ComplianceMetric(
            framework=ComplianceFramework.SOX,
            requirement='Segregation of Duties',
            status='COMPLIANT',
            score=80,
            evidence_count=0,
            last_assessment=datetime.now(),
            risk_level='MEDIUM',
            details={}
        )
    
    def _check_sox_change_mgmt(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check SOX change management"""
        
        change_events = [e for e in events if any(word in (e.get('action') or '').lower() 
                                                for word in ['create', 'modify', 'delete'])]
        
        return ComplianceMetric(
            framework=ComplianceFramework.SOX,
            requirement='Change Management',
            status='COMPLIANT' if len(change_events) > 0 else 'PARTIAL',
            score=90,
            evidence_count=len(change_events),
            last_assessment=datetime.now(),
            risk_level='LOW',
            details={'change_events': len(change_events)}
        )
    
    def _check_sox_financial_access(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check SOX financial data access"""
        
        financial_events = [e for e in events 
                          if any(keyword in (e.get('resource') or '').lower() 
                               for keyword in ['financial', 'transaction', 'payment'])]
        
        return ComplianceMetric(
            framework=ComplianceFramework.SOX,
            requirement='Financial Data Access',
            status='COMPLIANT' if len(financial_events) > 0 else 'PARTIAL',
            score=85,
            evidence_count=len(financial_events),
            last_assessment=datetime.now(),
            risk_level='HIGH',
            details={'financial_events': len(financial_events)}
        )
    
    def _check_sox_monitoring(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check SOX transaction monitoring"""
        
        return ComplianceMetric(
            framework=ComplianceFramework.SOX,
            requirement='Transaction Monitoring',
            status='COMPLIANT',
            score=95,
            evidence_count=len(events),
            last_assessment=datetime.now(),
            risk_level='LOW',
            details={'total_events': len(events)}
        )
    
    def _check_sox_audit_trail(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check SOX audit trail"""
        
        return ComplianceMetric(
            framework=ComplianceFramework.SOX,
            requirement='Audit Trail',
            status='COMPLIANT',
            score=100,
            evidence_count=len(events),
            last_assessment=datetime.now(),
            risk_level='LOW',
            details={'total_events': len(events)}
        )
    
    def _check_sox_certification(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check SOX management certification"""
        
        cert_events = [e for e in events if 'certification' in (e.get('action') or '').lower()]
        
        return ComplianceMetric(
            framework=ComplianceFramework.SOX,
            requirement='Management Certification',
            status='NOT_ASSESSED' if len(cert_events) == 0 else 'COMPLIANT',
            score=75,
            evidence_count=len(cert_events),
            last_assessment=datetime.now(),
            risk_level='MEDIUM',
            details={'cert_events': len(cert_events)}
        )
    
    # PCI-DSS checkers (simplified implementations)
    
    def _check_pci_data_protection(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check PCI-DSS cardholder data protection"""
        
        card_data_events = [e for e in events 
                          if any(keyword in (e.get('resource') or '').lower() 
                               for keyword in ['card', 'payment', 'credit'])]
        
        return ComplianceMetric(
            framework=ComplianceFramework.PCI_DSS,
            requirement='Cardholder Data Protection',
            status='COMPLIANT' if len(card_data_events) == 0 else 'PARTIAL',
            score=90 if len(card_data_events) == 0 else 60,
            evidence_count=len(card_data_events),
            last_assessment=datetime.now(),
            risk_level='HIGH' if len(card_data_events) > 0 else 'LOW',
            details={'card_data_events': len(card_data_events)}
        )
    
    def _check_pci_vulnerability(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check PCI-DSS vulnerability management"""
        
        security_events = [e for e in events if e.get('event_type') == 'security_event']
        
        return ComplianceMetric(
            framework=ComplianceFramework.PCI_DSS,
            requirement='Vulnerability Management',
            status='COMPLIANT',
            score=85,
            evidence_count=len(security_events),
            last_assessment=datetime.now(),
            risk_level='MEDIUM',
            details={'security_events': len(security_events)}
        )
    
    def _check_pci_access_control(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check PCI-DSS access control"""
        
        access_events = [e for e in events if e.get('event_type') == 'data_access']
        
        return ComplianceMetric(
            framework=ComplianceFramework.PCI_DSS,
            requirement='Access Control',
            status='COMPLIANT' if len(access_events) > 0 else 'PARTIAL',
            score=90,
            evidence_count=len(access_events),
            last_assessment=datetime.now(),
            risk_level='MEDIUM',
            details={'access_events': len(access_events)}
        )
    
    def _check_pci_network_security(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check PCI-DSS network security"""
        
        network_events = [e for e in events if e.get('event_type') == 'network_access']
        
        return ComplianceMetric(
            framework=ComplianceFramework.PCI_DSS,
            requirement='Network Security',
            status='COMPLIANT' if len(network_events) > 0 else 'PARTIAL',
            score=85,
            evidence_count=len(network_events),
            last_assessment=datetime.now(),
            risk_level='MEDIUM',
            details={'network_events': len(network_events)}
        )
    
    def _check_pci_monitoring(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check PCI-DSS monitoring and testing"""
        
        return ComplianceMetric(
            framework=ComplianceFramework.PCI_DSS,
            requirement='Monitoring and Testing',
            status='COMPLIANT',
            score=95,
            evidence_count=len(events),
            last_assessment=datetime.now(),
            risk_level='LOW',
            details={'total_events': len(events)}
        )
    
    def _check_pci_policy(self, events: List[Dict[str, Any]]) -> ComplianceMetric:
        """Check PCI-DSS security policy"""
        
        policy_events = [e for e in events if 'policy' in (e.get('action') or '').lower()]
        
        return ComplianceMetric(
            framework=ComplianceFramework.PCI_DSS,
            requirement='Security Policy',
            status='PARTIAL' if len(policy_events) == 0 else 'COMPLIANT',
            score=70 if len(policy_events) == 0 else 85,
            evidence_count=len(policy_events),
            last_assessment=datetime.now(),
            risk_level='MEDIUM',
            details={'policy_events': len(policy_events)}
        )
    
    def export_report(self, report: Dict[str, Any], format: str = 'json', 
                     output_path: str = None) -> str:
        """Export compliance report to file"""
        
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"compliance_report_{report['framework']}_{timestamp}.{format}"
        
        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
        
        elif format == 'csv':
            # Export summary metrics to CSV
            metrics_data = []
            for metric in report.get('metrics', []):
                metrics_data.append({
                    'Framework': metric.framework.value,
                    'Requirement': metric.requirement,
                    'Status': metric.status,
                    'Score': metric.score,
                    'Evidence Count': metric.evidence_count,
                    'Risk Level': metric.risk_level
                })
            
            with open(output_path, 'w', newline='') as f:
                if metrics_data:
                    writer = csv.DictWriter(f, fieldnames=metrics_data[0].keys())
                    writer.writeheader()
                    writer.writerows(metrics_data)
        
        self.logger.info(f"Report exported to {output_path}")
        return output_path
