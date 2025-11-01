#!/usr/bin/env python3
"""
Security Incident Detector
Real-time security incident detection, monitoring, and alerting
Supports threat intelligence, anomaly detection, and automated response
"""

import os
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import hashlib
import re
import statistics
from enum import Enum

# Import audit integrator
try:
    from audit_integrator import SecureAuditLogger
except ImportError:
    print("Warning: audit_integrator not found. Running in standalone mode.")

# Configuration
INCIDENT_DB_PATH = Path(os.environ.get('INCIDENT_DB_PATH', './logs/incidents.db'))
INCIDENTS_DIR = Path(os.environ.get('INCIDENTS_DIR', './incidents'))
INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
ALERT_THRESHOLD_SECONDS = int(os.environ.get('ALERT_THRESHOLD_SECONDS', '300'))  # 5 minutes
MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', '3'))

class IncidentSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"

class IncidentStatus(Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    CONTAINED = "CONTAINED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

@dataclass
class SecurityIncident:
    """Security incident data structure"""
    incident_id: str
    title: str
    description: str
    severity: str
    status: str
    category: str
    affected_systems: List[str]
    affected_users: List[str]
    indicators: List[Dict[str, Any]]
    timeline: List[Dict[str, str]]
    assigned_to: Optional[str]
    created_at: str
    updated_at: str
    resolved_at: Optional[str]
    false_positive: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'incident_id': self.incident_id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'status': self.status,
            'category': self.category,
            'affected_systems': self.affected_systems,
            'affected_users': self.affected_users,
            'indicators': self.indicators,
            'timeline': self.timeline,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'resolved_at': self.resolved_at,
            'false_positive': self.false_positive
        }

@dataclass
class ThreatIndicator:
    """Threat indicator for detection"""
    indicator_type: str  # IP, URL, HASH, PATTERN
    value: str
    severity: str
    source: str
    confidence: float
    first_seen: str
    last_seen: str

class ThreatIntelligence:
    """Manages threat intelligence data"""
    
    def __init__(self):
        self.known_threats = self._load_threat_intelligence()
    
    def _load_threat_intelligence(self) -> List[ThreatIndicator]:
        """Load known threat indicators"""
        # This would normally load from threat intelligence feeds
        # For demo purposes, we'll create some sample threats
        
        threats = []
        
        # Sample malicious IPs
        malicious_ips = [
            "192.0.2.1",  # Example malicious IP
            "198.51.100.1"  # Example malicious IP
        ]
        
        for ip in malicious_ips:
            threats.append(ThreatIndicator(
                indicator_type="IP",
                value=ip,
                severity="HIGH",
                source="internal",
                confidence=0.9,
                first_seen=datetime.now(timezone.utc).isoformat(),
                last_seen=datetime.now(timezone.utc).isoformat()
            ))
        
        # Sample suspicious patterns
        patterns = [
            r"\.exe$",  # Suspicious file extensions
            r"\.php$",  # Web shell patterns
            r"eval\s*\(",  # Code injection
            r"<script>",  # XSS patterns
        ]
        
        for pattern in patterns:
            threats.append(ThreatIndicator(
                indicator_type="PATTERN",
                value=pattern,
                severity="MEDIUM",
                source="internal",
                confidence=0.7,
                first_seen=datetime.now(timezone.utc).isoformat(),
                last_seen=datetime.now(timezone.utc).isoformat()
            ))
        
        return threats
    
    def check_indicator(self, indicator_type: str, value: str) -> Optional[ThreatIndicator]:
        """Check if an indicator matches known threats"""
        for threat in self.known_threats:
            if threat.indicator_type == indicator_type and threat.value == value:
                return threat
        return None

class AnomalyDetector:
    """Detects anomalies in audit logs"""
    
    def __init__(self):
        self.event_history = defaultdict(deque)
        self.thresholds = {
            'failed_logins': 5,
            'unusual_hours': (22, 6),  # 10 PM to 6 AM
            'geographic_anomaly': True,
            'volume_anomaly': True
        }
    
    def detect_login_anomalies(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """Detect anomalous login patterns"""
        anomalies = []
        
        # Group events by IP
        ip_events = defaultdict(list)
        for event in events:
            if 'LOGIN' in event.get('action', '').upper():
                ip_events[event.get('ip_address', 'unknown')].append(event)
        
        # Check for brute force attempts
        for ip, login_events in ip_events.items():
            failed_logins = [
                e for e in login_events 
                if e.get('outcome') == 'FAILURE'
            ]
            
            if len(failed_logins) >= self.thresholds['failed_logins']:
                # Check if failures occurred within a short time window
                recent_failures = [
                    e for e in failed_logins
                    if datetime.fromisoformat(e.get('timestamp', '')) > 
                       datetime.now(timezone.utc) - timedelta(minutes=15)
                ]
                
                if len(recent_failures) >= self.thresholds['failed_logins']:
                    anomalies.append({
                        'type': 'BRUTE_FORCE',
                        'ip_address': ip,
                        'count': len(recent_failures),
                        'time_window': '15_minutes',
                        'severity': 'HIGH',
                        'events': recent_failures
                    })
        
        # Check for unusual login hours
        for event in events:
            if 'LOGIN' in event.get('action', '').upper():
                event_time = datetime.fromisoformat(event.get('timestamp', ''))
                hour = event_time.hour
                
                if hour >= self.thresholds['unusual_hours'][0] or hour < self.thresholds['unusual_hours'][1]:
                    anomalies.append({
                        'type': 'UNUSUAL_HOURS',
                        'user_id': event.get('user_id'),
                        'time': event.get('timestamp'),
                        'hour': hour,
                        'severity': 'MEDIUM',
                        'event': event
                    })
        
        return anomalies
    
    def detect_data_access_anomalies(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """Detect anomalous data access patterns"""
        anomalies = []
        
        # Group events by user and resource type
        user_data_access = defaultdict(lambda: defaultdict(list))
        
        for event in events:
            if event.get('resource_type') == 'DATA':
                user_data_access[event.get('user_id', 'unknown')][
                    event.get('resource', 'unknown')
                ].append(event)
        
        # Check for unusual volume
        for user, resources in user_data_access.items():
            for resource, access_events in resources.items():
                if len(access_events) > 50:  # Threshold for unusual volume
                    anomalies.append({
                        'type': 'HIGH_VOLUME_ACCESS',
                        'user_id': user,
                        'resource': resource,
                        'count': len(access_events),
                        'time_window': '1_hour',
                        'severity': 'HIGH',
                        'events': access_events
                    })
        
        return anomalies
    
    def detect_geographic_anomalies(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """Detect geographic anomalies (simplified implementation)"""
        # This would normally use IP geolocation
        # For demo, we'll check for multiple different IPs from same user
        
        anomalies = []
        user_ips = defaultdict(set)
        
        for event in events:
            user_id = event.get('user_id')
            ip = event.get('ip_address')
            
            if user_id and ip:
                user_ips[user_id].add(ip)
        
        # Check for users with IPs from different countries/regions
        for user, ips in user_ips.items():
            if len(ips) > 1:  # Multiple IPs could indicate geographic anomaly
                anomalies.append({
                    'type': 'GEOGRAPHIC_ANOMALY',
                    'user_id': user,
                    'ip_count': len(ips),
                    'ips': list(ips),
                    'severity': 'MEDIUM',
                    'description': f'User {user} accessed from {len(ips)} different IP addresses'
                })
        
        return anomalies

class IncidentDetector:
    """Main incident detection engine"""
    
    def __init__(self, audit_logger: Optional[SecureAuditLogger] = None):
        self.audit_logger = audit_logger
        self.threat_intel = ThreatIntelligence()
        self.anomaly_detector = AnomalyDetector()
        self.incident_db = self._init_incident_db()
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Alert configuration
        self.alert_rules = self._load_alert_rules()
        
        # In-memory incident cache
        self.active_incidents = {}
    
    def _init_incident_db(self) -> sqlite3.Connection:
        """Initialize incident database"""
        conn = sqlite3.connect(str(INCIDENT_DB_PATH), check_same_thread=False)
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS security_incidents (
                incident_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                category TEXT NOT NULL,
                affected_systems TEXT NOT NULL,
                affected_users TEXT NOT NULL,
                indicators TEXT NOT NULL,
                timeline TEXT NOT NULL,
                assigned_to TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                resolved_at TEXT,
                false_positive BOOLEAN DEFAULT FALSE
            )
        ''')
        
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_severity ON security_incidents(severity)
        ''')
        
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_status ON security_incidents(status)
        ''')
        
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON security_incidents(created_at)
        ''')
        
        conn.commit()
        return conn
    
    def _load_alert_rules(self) -> Dict[str, Any]:
        """Load alert rules and thresholds"""
        return {
            'brute_force_threshold': 5,
            'data_exfiltration_threshold': 1000,
            'privilege_escalation_keywords': ['admin', 'root', 'sudo', 'elevate'],
            'malware_indicators': ['malware', 'virus', 'trojan', 'ransomware'],
            'suspicious_user_agents': ['bot', 'scanner', 'crawler'],
            'geographic_restrictions': True
        }
    
    def start_monitoring(self, poll_interval: int = 60):
        """Start real-time incident monitoring"""
        if self.monitoring_active:
            print("Incident monitoring is already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_worker,
            args=(poll_interval,),
            daemon=True
        )
        self.monitor_thread.start()
        print(f"Started incident monitoring (poll interval: {poll_interval}s)")
    
    def stop_monitoring(self):
        """Stop real-time incident monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("Stopped incident monitoring")
    
    def _monitoring_worker(self, poll_interval: int):
        """Background monitoring worker"""
        while self.monitoring_active:
            try:
                self.scan_for_incidents()
                time.sleep(poll_interval)
            except Exception as e:
                print(f"Error in monitoring worker: {e}")
                time.sleep(5)
    
    def scan_for_incidents(self) -> List[SecurityIncident]:
        """Scan for security incidents"""
        incidents = []
        
        # Load recent audit events
        events = self._get_recent_audit_events(3600)  # Last hour
        
        if not events:
            return incidents
        
        # Run detection algorithms
        incidents.extend(self.detect_brute_force_attacks(events))
        incidents.extend(self.detect_data_exfiltration(events))
        incidents.extend(self.detect_privilege_escalation(events))
        incidents.extend(self.detect_malware_activity(events))
        incidents.extend(self.detect_suspicious_activity(events))
        
        # Check threat intelligence
        incidents.extend(self.check_threat_intelligence(events))
        
        # Check anomalies
        incidents.extend(self.check_anomalies(events))
        
        # Save incidents
        for incident in incidents:
            self._save_incident(incident)
        
        # Send alerts
        self._process_alerts(incidents)
        
        return incidents
    
    def detect_brute_force_attacks(self, events: List[Dict]) -> List[SecurityIncident]:
        """Detect brute force attacks"""
        incidents = []
        
        # Group by IP
        ip_events = defaultdict(list)
        for event in events:
            if 'LOGIN' in event.get('action', '').upper():
                ip_events[event.get('ip_address', 'unknown')].append(event)
        
        for ip, login_events in ip_events.items():
            failed_logins = [
                e for e in login_events 
                if e.get('outcome') == 'FAILURE'
            ]
            
            if len(failed_logins) >= self.alert_rules['brute_force_threshold']:
                incident = SecurityIncident(
                    incident_id=self._generate_incident_id(),
                    title=f"Brute Force Attack Detected from {ip}",
                    description=f"Detected {len(failed_logins)} failed login attempts from {ip}",
                    severity=IncidentSeverity.HIGH.value,
                    status=IncidentStatus.OPEN.value,
                    category="AUTHENTICATION",
                    affected_systems=[event.get('resource', 'unknown') for event in failed_logins],
                    affected_users=list(set(e.get('user_id') for e in failed_logins if e.get('user_id'))),
                    indicators=[{'type': 'IP', 'value': ip, 'confidence': 0.9}],
                    timeline=[{
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'event': 'BRUTE_FORCE_DETECTED',
                        'details': f'{len(failed_logins)} failed attempts'
                    }],
                    assigned_to=None,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    updated_at=datetime.now(timezone.utc).isoformat(),
                    resolved_at=None
                )
                incidents.append(incident)
        
        return incidents
    
    def detect_data_exfiltration(self, events: List[Dict]) -> List[SecurityIncident]:
        """Detect data exfiltration attempts"""
        incidents = []
        
        # Look for bulk data access/export
        data_access_events = [
            e for e in events
            if e.get('resource_type') == 'DATA' and 
               e.get('outcome') == 'SUCCESS' and
               any(keyword in e.get('action', '').lower() for keyword in 
                   ['export', 'download', 'bulk', 'massive'])
        ]
        
        # Group by user and timeframe
        user_bulk_access = defaultdict(list)
        for event in data_access_events:
            user_bulk_access[event.get('user_id', 'unknown')].append(event)
        
        for user, access_events in user_bulk_access.items():
            if len(access_events) >= self.alert_rules['data_exfiltration_threshold']:
                incident = SecurityIncident(
                    incident_id=self._generate_incident_id(),
                    title=f"Potential Data Exfiltration by User {user}",
                    description=f"User {user} accessed {len(access_events)} data records",
                    severity=IncidentSeverity.CRITICAL.value,
                    status=IncidentStatus.OPEN.value,
                    category="DATA_LEAK",
                    affected_systems=[e.get('resource', 'unknown') for e in access_events],
                    affected_users=[user],
                    indicators=[{'type': 'VOLUME', 'value': len(access_events), 'confidence': 0.8}],
                    timeline=[{
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'event': 'DATA_EXFILTRATION_DETECTED',
                        'details': f'Bulk access: {len(access_events)} records'
                    }],
                    assigned_to=None,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    updated_at=datetime.now(timezone.utc).isoformat(),
                    resolved_at=None
                )
                incidents.append(incident)
        
        return incidents
    
    def detect_privilege_escalation(self, events: List[Dict]) -> List[SecurityIncident]:
        """Detect privilege escalation attempts"""
        incidents = []
        
        for event in events:
            action = event.get('action', '').lower()
            
            # Check for privilege escalation keywords
            if any(keyword in action for keyword in self.alert_rules['privilege_escalation_keywords']):
                incident = SecurityIncident(
                    incident_id=self._generate_incident_id(),
                    title=f"Potential Privilege Escalation: {event.get('action')}",
                    description=f"Privilege escalation attempt detected: {event.get('action')}",
                    severity=IncidentSeverity.HIGH.value,
                    status=IncidentStatus.OPEN.value,
                    category="PRIVILEGE_ESCALATION",
                    affected_systems=[event.get('resource', 'unknown')],
                    affected_users=[event.get('user_id', 'unknown')],
                    indicators=[{
                        'type': 'KEYWORD_MATCH',
                        'value': event.get('action'),
                        'confidence': 0.7
                    }],
                    timeline=[{
                        'timestamp': event.get('timestamp', ''),
                        'event': 'PRIVILEGE_ESCALATION_ATTEMPT',
                        'details': event.get('action')
                    }],
                    assigned_to=None,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    updated_at=datetime.now(timezone.utc).isoformat(),
                    resolved_at=None
                )
                incidents.append(incident)
        
        return incidents
    
    def detect_malware_activity(self, events: List[Dict]) -> List[SecurityIncident]:
        """Detect malware-related activity"""
        incidents = []
        
        for event in events:
            details_str = str(event.get('details', {})).lower()
            
            # Check for malware indicators
            if any(indicator in details_str for indicator in self.alert_rules['malware_indicators']):
                incident = SecurityIncident(
                    incident_id=self._generate_incident_id(),
                    title=f"Malware Activity Detected: {event.get('action')}",
                    description=f"Malware indicator found in event: {event.get('action')}",
                    severity=IncidentSeverity.CRITICAL.value,
                    status=IncidentStatus.OPEN.value,
                    category="MALWARE",
                    affected_systems=[event.get('resource', 'unknown')],
                    affected_users=[event.get('user_id', 'unknown')],
                    indicators=[{
                        'type': 'MALWARE_INDICATOR',
                        'value': str(event.get('details', {})),
                        'confidence': 0.6
                    }],
                    timeline=[{
                        'timestamp': event.get('timestamp', ''),
                        'event': 'MALWARE_ACTIVITY',
                        'details': str(event.get('details', {}))
                    }],
                    assigned_to=None,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    updated_at=datetime.now(timezone.utc).isoformat(),
                    resolved_at=None
                )
                incidents.append(incident)
        
        return incidents
    
    def detect_suspicious_activity(self, events: List[Dict]) -> List[SecurityIncident]:
        """Detect other suspicious activity patterns"""
        incidents = []
        
        for event in events:
            user_agent = event.get('user_agent', '').lower()
            
            # Check for suspicious user agents
            if any(indicator in user_agent for indicator in self.alert_rules['suspicious_user_agents']):
                incident = SecurityIncident(
                    incident_id=self._generate_incident_id(),
                    title=f"Suspicious User Agent: {user_agent[:50]}...",
                    description=f"Suspicious user agent detected: {user_agent}",
                    severity=IncidentSeverity.MEDIUM.value,
                    status=IncidentStatus.OPEN.value,
                    category="SUSPICIOUS_ACTIVITY",
                    affected_systems=[event.get('resource', 'unknown')],
                    affected_users=[event.get('user_id', 'unknown')],
                    indicators=[{
                        'type': 'SUSPICIOUS_USER_AGENT',
                        'value': user_agent,
                        'confidence': 0.5
                    }],
                    timeline=[{
                        'timestamp': event.get('timestamp', ''),
                        'event': 'SUSPICIOUS_ACTIVITY',
                        'details': user_agent
                    }],
                    assigned_to=None,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    updated_at=datetime.now(timezone.utc).isoformat(),
                    resolved_at=None
                )
                incidents.append(incident)
        
        return incidents
    
    def check_threat_intelligence(self, events: List[Dict]) -> List[SecurityIncident]:
        """Check events against threat intelligence"""
        incidents = []
        
        for event in events:
            # Check IP addresses
            ip = event.get('ip_address')
            if ip:
                threat = self.threat_intel.check_indicator('IP', ip)
                if threat:
                    incident = SecurityIncident(
                        incident_id=self._generate_incident_id(),
                        title=f"Threat Intelligence Match: {ip}",
                        description=f"Known malicious IP detected: {ip}",
                        severity=threat.severity,
                        status=IncidentStatus.OPEN.value,
                        category="THREAT_INTELLIGENCE",
                        affected_systems=[event.get('resource', 'unknown')],
                        affected_users=[event.get('user_id', 'unknown')],
                        indicators=[{
                            'type': 'IP',
                            'value': ip,
                            'source': threat.source,
                            'confidence': threat.confidence
                        }],
                        timeline=[{
                            'timestamp': event.get('timestamp', ''),
                            'event': 'THREAT_INTEL_MATCH',
                            'details': f"Matched threat from {threat.source}"
                        }],
                        assigned_to=None,
                        created_at=datetime.now(timezone.utc).isoformat(),
                        updated_at=datetime.now(timezone.utc).isoformat(),
                        resolved_at=None
                    )
                    incidents.append(incident)
        
        return incidents
    
    def check_anomalies(self, events: List[Dict]) -> List[SecurityIncident]:
        """Check for anomalous patterns"""
        incidents = []
        
        # Get anomalies from detector
        login_anomalies = self.anomaly_detector.detect_login_anomalies(events)
        data_anomalies = self.anomaly_detector.detect_data_access_anomalies(events)
        geo_anomalies = self.anomaly_detector.detect_geographic_anomalies(events)
        
        # Convert anomalies to incidents
        for anomaly in login_anomalies + data_anomalies + geo_anomalies:
            incident = SecurityIncident(
                incident_id=self._generate_incident_id(),
                title=f"Anomaly Detected: {anomaly['type']}",
                description=anomaly.get('description', f"Detected {anomaly['type']}"),
                severity=anomaly.get('severity', 'MEDIUM'),
                status=IncidentStatus.OPEN.value,
                category="ANOMALY",
                affected_systems=[],
                affected_users=[anomaly.get('user_id', 'unknown')],
                indicators=[{
                    'type': 'ANOMALY',
                    'value': anomaly['type'],
                    'confidence': 0.7
                }],
                timeline=[{
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'event': 'ANOMALY_DETECTED',
                    'details': str(anomaly)
                }],
                assigned_to=None,
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
                resolved_at=None
            )
            incidents.append(incident)
        
        return incidents
    
    def _get_recent_audit_events(self, seconds: int) -> List[Dict]:
        """Get recent audit events from database"""
        try:
            # This would connect to the audit database
            # For now, return empty list
            return []
        except Exception as e:
            print(f"Error getting audit events: {e}")
            return []
    
    def _generate_incident_id(self) -> str:
        """Generate unique incident ID"""
        timestamp = int(time.time())
        random_part = hashlib.md5(str(timestamp).encode()).hexdigest()[:8]
        return f"INC-{timestamp}-{random_part}"
    
    def _save_incident(self, incident: SecurityIncident):
        """Save incident to database"""
        self.incident_db.execute('''
            INSERT OR REPLACE INTO security_incidents
            (incident_id, title, description, severity, status, category,
             affected_systems, affected_users, indicators, timeline,
             assigned_to, created_at, updated_at, resolved_at, false_positive)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            incident.incident_id,
            incident.title,
            incident.description,
            incident.severity,
            incident.status,
            incident.category,
            json.dumps(incident.affected_systems),
            json.dumps(incident.affected_users),
            json.dumps(incident.indicators),
            json.dumps(incident.timeline),
            incident.assigned_to,
            incident.created_at,
            incident.updated_at,
            incident.resolved_at,
            incident.false_positive
        ))
        self.incident_db.commit()
        
        # Log incident creation
        if self.audit_logger:
            self.audit_logger.log_event(
                action="SECURITY_INCIDENT_CREATED",
                resource=f"incident:{incident.incident_id}",
                resource_type="INCIDENT",
                details={
                    'incident_id': incident.incident_id,
                    'severity': incident.severity,
                    'category': incident.category
                },
                risk_level=incident.severity
            )
    
    def _process_alerts(self, incidents: List[SecurityIncident]):
        """Process alerts for incidents"""
        for incident in incidents:
            if incident.severity in [IncidentSeverity.HIGH.value, 
                                   IncidentSeverity.CRITICAL.value,
                                   IncidentSeverity.EMERGENCY.value]:
                self._send_alert(incident)
    
    def _send_alert(self, incident: SecurityIncident):
        """Send security alert"""
        alert_message = f"""
SECURITY ALERT - {incident.severity}
Incident ID: {incident.incident_id}
Title: {incident.title}
Description: {incident.description}
Category: {incident.category}
Time: {incident.created_at}

Immediate action required!
"""
        
        print(f"\n🚨 SECURITY ALERT 🚨\n{alert_message}")
        
        # In a real implementation, this would send email, SMS, Slack, etc.
        # For now, we'll log it
        if self.audit_logger:
            self.audit_logger.log_event(
                action="SECURITY_ALERT_SENT",
                resource=f"incident:{incident.incident_id}",
                resource_type="ALERT",
                details={
                    'alert_type': incident.severity,
                    'message': alert_message
                },
                risk_level=incident.severity
            )
    
    def get_incidents(self, 
                     status: Optional[str] = None,
                     severity: Optional[str] = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """Get incidents with filters"""
        query = "SELECT * FROM security_incidents WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor = self.incident_db.execute(query, params)
        incidents = []
        
        for row in cursor.fetchall():
            columns = [desc[0] for desc in cursor.description]
            incident_dict = dict(zip(columns, row))
            
            # Parse JSON fields
            incident_dict['affected_systems'] = json.loads(incident_dict['affected_systems'])
            incident_dict['affected_users'] = json.loads(incident_dict['affected_users'])
            incident_dict['indicators'] = json.loads(incident_dict['indicators'])
            incident_dict['timeline'] = json.loads(incident_dict['timeline'])
            
            incidents.append(incident_dict)
        
        return incidents
    
    def update_incident_status(self, 
                              incident_id: str,
                              status: str,
                              notes: Optional[str] = None):
        """Update incident status"""
        self.incident_db.execute('''
            UPDATE security_incidents 
            SET status = ?, updated_at = ?
            WHERE incident_id = ?
        ''', (status, datetime.now(timezone.utc).isoformat(), incident_id))
        
        if notes:
            # Add note to timeline
            cursor = self.incident_db.execute(
                'SELECT timeline FROM security_incidents WHERE incident_id = ?',
                (incident_id,)
            )
            result = cursor.fetchone()
            if result:
                timeline = json.loads(result[0])
                timeline.append({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'event': 'STATUS_UPDATE',
                    'details': f'Status changed to {status}: {notes}'
                })
                
                self.incident_db.execute('''
                    UPDATE security_incidents 
                    SET timeline = ?, updated_at = ?
                    WHERE incident_id = ?
                ''', (json.dumps(timeline), datetime.now(timezone.utc).isoformat(), incident_id))
        
        self.incident_db.commit()
        
        # Log status update
        if self.audit_logger:
            self.audit_logger.log_event(
                action="INCIDENT_STATUS_UPDATED",
                resource=f"incident:{incident_id}",
                resource_type="INCIDENT",
                details={
                    'new_status': status,
                    'notes': notes
                },
                risk_level="MEDIUM"
            )
    
    def generate_incident_report(self, 
                                start_date: str,
                                end_date: str) -> Dict[str, Any]:
        """Generate incident report for date range"""
        cursor = self.incident_db.execute('''
            SELECT * FROM security_incidents 
            WHERE created_at >= ? AND created_at <= ?
            ORDER BY created_at DESC
        ''', (start_date, end_date))
        
        incidents = []
        for row in cursor.fetchall():
            columns = [desc[0] for desc in cursor.description]
            incident_dict = dict(zip(columns, row))
            incident_dict['affected_systems'] = json.loads(incident_dict['affected_systems'])
            incident_dict['affected_users'] = json.loads(incident_dict['affected_users'])
            incident_dict['indicators'] = json.loads(incident_dict['indicators'])
            incident_dict['timeline'] = json.loads(incident_dict['timeline'])
            incidents.append(incident_dict)
        
        # Generate statistics
        stats = {
            'total_incidents': len(incidents),
            'by_severity': defaultdict(int),
            'by_category': defaultdict(int),
            'by_status': defaultdict(int),
            'resolution_times': [],
            'false_positive_count': 0
        }
        
        for incident in incidents:
            stats['by_severity'][incident['severity']] += 1
            stats['by_category'][incident['category']] += 1
            stats['by_status'][incident['status']] += 1
            
            if incident['resolved_at']:
                created = datetime.fromisoformat(incident['created_at'])
                resolved = datetime.fromisoformat(incident['resolved_at'])
                resolution_time = (resolved - created).total_seconds() / 3600  # hours
                stats['resolution_times'].append(resolution_time)
            
            if incident['false_positive']:
                stats['false_positive_count'] += 1
        
        # Calculate averages
        if stats['resolution_times']:
            stats['avg_resolution_time_hours'] = statistics.mean(stats['resolution_times'])
            stats['median_resolution_time_hours'] = statistics.median(stats['resolution_times'])
        else:
            stats['avg_resolution_time_hours'] = 0
            stats['median_resolution_time_hours'] = 0
        
        return {
            'report_id': self._generate_incident_id(),
            'period': {'start': start_date, 'end': end_date},
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'statistics': dict(stats),
            'incidents': incidents
        }


if __name__ == "__main__":
    print("Security Incident Detector - Real-time Threat Detection")
    print("=" * 60)
    
    # Example usage
    detector = IncidentDetector()
    
    # Start monitoring
    detector.start_monitoring(poll_interval=30)  # Check every 30 seconds
    
    try:
        print("Incident detector is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nStopping incident detector...")
        detector.stop_monitoring()
    
    print("Incident detection completed!")
