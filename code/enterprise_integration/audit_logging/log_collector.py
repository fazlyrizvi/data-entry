"""
Audit Log Collector - Centralized audit event collection with security features
Handles user activities, data access, system changes, and compliance events
"""

import json
import hashlib
import hmac
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import sqlite3
import threading
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os


class AuditEventType(Enum):
    """Types of audit events"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_LOGIN_FAILED = "user_login_failed"
    DATA_ACCESS = "data_access"
    DATA_CREATED = "data_created"
    DATA_MODIFIED = "data_modified"
    DATA_DELETED = "data_deleted"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    FILE_ACCESS = "file_access"
    NETWORK_ACCESS = "network_access"
    API_CALL = "api_call"
    PERMISSION_CHANGE = "permission_change"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_EVENT = "compliance_event"
    GDPR_REQUEST = "gdpr_request"
    HIPAA_ACCESS = "hipaa_access"
    SOX_TRANSACTION = "sox_transaction"


class ComplianceLevel(Enum):
    """Compliance levels for events"""
    STANDARD = "standard"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"


@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: Optional[str]
    session_id: Optional[str]
    source_ip: Optional[str]
    source_host: Optional[str]
    resource: Optional[str]
    action: str
    outcome: str  # SUCCESS, FAILURE, WARNING
    details: Dict[str, Any]
    compliance_level: ComplianceLevel
    risk_score: int  # 0-100
    correlation_id: Optional[str]
    parent_event_id: Optional[str]
    tags: List[str]
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.correlation_id:
            self.correlation_id = str(uuid.uuid4())


class LogCollector:
    """Centralized audit log collector with encryption and integrity"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logger()
        self.db_path = config.get('database_path', 'audit_logs.db')
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self._setup_database()
        self._start_background_tasks()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('audit_collector')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for secure log storage"""
        key_file = Path(self.config.get('key_file', 'audit_encryption.key'))
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            key_file.chmod(0o600)
            return key
    
    def _setup_database(self):
        """Initialize SQLite database for audit logs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    source_ip TEXT,
                    source_host TEXT,
                    resource TEXT,
                    action TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    encrypted_details TEXT,
                    compliance_level TEXT NOT NULL,
                    risk_score INTEGER,
                    correlation_id TEXT,
                    parent_event_id TEXT,
                    tags TEXT,
                    hash_chain TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS log_integrity (
                    log_id INTEGER PRIMARY KEY,
                    hash TEXT NOT NULL,
                    previous_hash TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (log_id) REFERENCES audit_logs (id)
                )
            ''')
            
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_logs(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON audit_logs(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON audit_logs(event_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_compliance ON audit_logs(compliance_level)')
            
            conn.commit()
    
    def log_event(self, event: AuditEvent) -> bool:
        """Log an audit event with encryption and integrity verification"""
        try:
            # Encrypt sensitive details
            encrypted_details = self._encrypt_details(event.details)
            
            # Calculate hash chain for integrity
            hash_chain = self._calculate_hash_chain(event)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO audit_logs (
                        event_id, timestamp, event_type, user_id, session_id,
                        source_ip, source_host, resource, action, outcome,
                        encrypted_details, compliance_level, risk_score,
                        correlation_id, parent_event_id, tags, hash_chain
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_id, event.timestamp.isoformat(), event.event_type.value,
                    event.user_id, event.session_id, event.source_ip, event.source_host,
                    event.resource, event.action, event.outcome, encrypted_details,
                    event.compliance_level.value, event.risk_score, event.correlation_id,
                    event.parent_event_id, json.dumps(event.tags), hash_chain
                ))
                
                log_id = cursor.lastrowid
                
                # Store integrity hash
                cursor.execute('''
                    INSERT INTO log_integrity (log_id, hash, previous_hash, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (log_id, hash_chain, self._get_previous_hash(), datetime.now().isoformat()))
                
                conn.commit()
                
            self.logger.info(f"Audit event logged: {event.event_type.value} - {event.event_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
            return False
    
    def _encrypt_details(self, details: Dict[str, Any]) -> str:
        """Encrypt sensitive details"""
        try:
            details_json = json.dumps(details)
            encrypted = self.fernet.encrypt(details_json.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            return json.dumps(details)  # Fallback to plain text
    
    def _decrypt_details(self, encrypted_details: str) -> Dict[str, Any]:
        """Decrypt sensitive details"""
        try:
            encrypted = base64.b64decode(encrypted_details.encode())
            decrypted = self.fernet.decrypt(encrypted)
            return json.loads(decrypted.decode())
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            return {}
    
    def _calculate_hash_chain(self, event: AuditEvent) -> str:
        """Calculate hash chain for log integrity"""
        # Get previous hash for chain
        previous_hash = self._get_previous_hash()
        
        # Create hash of event data
        event_data = f"{event.event_id}{event.timestamp.isoformat()}{event.event_type.value}{event.action}{previous_hash}"
        return hashlib.sha256(event_data.encode()).hexdigest()
    
    def _get_previous_hash(self) -> str:
        """Get the previous hash in the chain"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT hash FROM log_integrity ORDER BY log_id DESC LIMIT 1')
                result = cursor.fetchone()
                return result[0] if result else "0" * 64
        except Exception:
            return "0" * 64
    
    def collect_user_activity(self, user_id: str, action: str, outcome: str = "SUCCESS",
                            session_id: str = None, source_ip: str = None,
                            details: Dict[str, Any] = None) -> bool:
        """Collect user activity events"""
        event = AuditEvent(
            event_id="",
            timestamp=datetime.now(),
            event_type=AuditEventType.USER_LOGIN if action in ['login', 'authenticate'] else AuditEventType.USER_LOGOUT,
            user_id=user_id,
            session_id=session_id,
            source_ip=source_ip,
            source_host=None,
            resource=None,
            action=action,
            outcome=outcome,
            details=details or {},
            compliance_level=ComplianceLevel.STANDARD,
            risk_score=self._calculate_risk_score(user_id, action, outcome),
            correlation_id=None,
            parent_event_id=None,
            tags=['user_activity']
        )
        return self.log_event(event)
    
    def collect_data_access(self, user_id: str, resource: str, action: str,
                          outcome: str = "SUCCESS", details: Dict[str, Any] = None,
                          compliance_level: ComplianceLevel = ComplianceLevel.STANDARD) -> bool:
        """Collect data access events"""
        event = AuditEvent(
            event_id="",
            timestamp=datetime.now(),
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            session_id=None,
            source_ip=None,
            source_host=None,
            resource=resource,
            action=action,
            outcome=outcome,
            details=details or {},
            compliance_level=compliance_level,
            risk_score=self._calculate_data_access_risk(resource, action),
            correlation_id=None,
            parent_event_id=None,
            tags=['data_access', compliance_level.value]
        )
        return self.log_event(event)
    
    def collect_system_change(self, user_id: str, action: str, resource: str,
                            outcome: str = "SUCCESS", details: Dict[str, Any] = None) -> bool:
        """Collect system configuration changes"""
        event = AuditEvent(
            event_id="",
            timestamp=datetime.now(),
            event_type=AuditEventType.SYSTEM_CONFIG_CHANGE,
            user_id=user_id,
            session_id=None,
            source_ip=None,
            source_host=None,
            resource=resource,
            action=action,
            outcome=outcome,
            details=details or {},
            compliance_level=ComplianceLevel.STANDARD,
            risk_score=80 if action in ['delete', 'modify_config'] else 30,
            correlation_id=None,
            parent_event_id=None,
            tags=['system_change', 'configuration']
        )
        return self.log_event(event)
    
    def _calculate_risk_score(self, user_id: str, action: str, outcome: str) -> int:
        """Calculate risk score for events"""
        base_score = 10
        
        if action in ['admin', 'elevate', 'sudo']:
            base_score += 40
        if outcome == 'FAILURE':
            base_score += 20
        if user_id == 'unknown' or user_id is None:
            base_score += 30
            
        return min(base_score, 100)
    
    def _calculate_data_access_risk(self, resource: str, action: str) -> int:
        """Calculate risk score for data access"""
        base_score = 20
        
        sensitive_patterns = ['customer', 'financial', 'personal', 'medical', 'password']
        if any(pattern in resource.lower() for pattern in sensitive_patterns):
            base_score += 30
            
        high_risk_actions = ['delete', 'export', 'download', 'bulk']
        if action in high_risk_actions:
            base_score += 30
            
        return min(base_score, 100)
    
    def get_events(self, filters: Dict[str, Any] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """Retrieve audit events with filters"""
        if filters is None:
            filters = {}
            
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if filters.get('user_id'):
            query += " AND user_id = ?"
            params.append(filters['user_id'])
            
        if filters.get('event_type'):
            query += " AND event_type = ?"
            params.append(filters['event_type'])
            
        if filters.get('start_time'):
            query += " AND timestamp >= ?"
            params.append(filters['start_time'])
            
        if filters.get('end_time'):
            query += " AND timestamp <= ?"
            params.append(filters['end_time'])
            
        if filters.get('compliance_level'):
            query += " AND compliance_level = ?"
            params.append(filters['compliance_level'])
            
        if filters.get('risk_score_min'):
            query += " AND risk_score >= ?"
            params.append(filters['risk_score_min'])
            
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            events = []
            for row in cursor.fetchall():
                event = dict(row)
                # Decrypt details if present
                if event.get('encrypted_details'):
                    event['details'] = self._decrypt_details(event['encrypted_details'])
                    del event['encrypted_details']
                events.append(event)
                
        return events
    
    def verify_integrity(self) -> Dict[str, Any]:
        """Verify log integrity using hash chain"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT al.id, li.hash, li.previous_hash, al.hash_chain
                    FROM audit_logs al
                    JOIN log_integrity li ON al.id = li.log_id
                    ORDER BY al.id
                ''')
                
                logs = cursor.fetchall()
                issues = []
                
                for log in logs:
                    log_id, stored_hash, previous_hash, expected_hash = log
                    if stored_hash != expected_hash:
                        issues.append(f"Log ID {log_id}: Hash mismatch")
                
                return {
                    'is_valid': len(issues) == 0,
                    'total_logs': len(logs),
                    'issues': issues
                }
        except Exception as e:
            return {
                'is_valid': False,
                'error': str(e)
            }
    
    def _start_background_tasks(self):
        """Start background tasks for maintenance"""
        def cleanup_old_logs():
            """Cleanup old logs based on retention policy"""
            retention_days = self.config.get('retention_days', 2555)  # 7 years default
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM audit_logs WHERE timestamp < ?', (cutoff_date.isoformat(),))
                cursor.execute('DELETE FROM log_integrity WHERE log_id NOT IN (SELECT id FROM audit_logs)')
                conn.commit()
                
            self.logger.info(f"Cleaned up logs older than {retention_days} days")
        
        # Schedule cleanup every day at midnight
        def schedule_cleanup():
            while True:
                now = datetime.now()
                tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                sleep_seconds = (tomorrow - now).total_seconds()
                time.sleep(sleep_seconds)
                cleanup_old_logs()
        
        cleanup_thread = threading.Thread(target=schedule_cleanup, daemon=True)
        cleanup_thread.start()
    
    def export_logs(self, filters: Dict[str, Any] = None, 
                   format: str = 'json') -> Union[str, bytes]:
        """Export audit logs for external analysis"""
        events = self.get_events(filters, limit=10000)
        
        if format == 'json':
            return json.dumps(events, indent=2, default=str)
        elif format == 'csv':
            import csv
            import io
            output = io.StringIO()
            if events:
                writer = csv.DictWriter(output, fieldnames=events[0].keys())
                writer.writeheader()
                for event in events:
                    # Convert datetime objects to strings
                    event_copy = {k: v.isoformat() if isinstance(v, datetime) else v 
                                for k, v in event.items()}
                    writer.writerow(event_copy)
            return output.getvalue()
        
        return str(events)
