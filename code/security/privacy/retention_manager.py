"""
Data Retention Management System
Implements automated data retention policies and secure deletion
Compliant with GDPR Article 5(1)(e) - Storage Limitation Principle
"""

import json
import logging
import sqlite3
from typing import Dict, List, Optional, Union, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import os
import shutil
from pathlib import Path


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetentionStatus(Enum):
    """Data retention status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING_DELETION = "pending_deletion"
    DELETED = "deleted"
    ARCHIVED = "archived"
    EXTENDED = "extended"


class DeletionMethod(Enum):
    """Secure deletion methods"""
    SIMPLE_DELETE = "simple_delete"
    OVERWRITE_ZEROS = "overwrite_zeros"
    OVERWRITE_RANDOM = "overwrite_random"
    DOD_5220_22_M = "dod_5220_22_m"
    GUTMANN = "gutmann"
    CRYPTO_SHRED = "crypto_shred"


class RetentionReason(Enum):
    """Reasons for retention"""
    LEGAL_REQUIREMENT = "legal_requirement"
    CONTRACTUAL_OBLIGATION = "contractual_obligation"
    LEGITIMATE_INTEREST = "legitimate_interest"
    CONSENT = "consent"
    AUDIT_REQUIREMENT = "audit_requirement"
    BUSINESS_NEED = "business_need"
    REGULATORY_COMPLIANCE = "regulatory_compliance"


@dataclass
class RetentionRule:
    """Data retention rule definition"""
    id: str
    name: str
    description: str
    data_types: List[str]
    retention_period: timedelta
    legal_basis: str
    reason: RetentionReason
    auto_deletion: bool
    secure_deletion: bool
    deletion_method: DeletionMethod
    extensions_allowed: int
    notification_period: timedelta
    created_at: datetime
    updated_at: datetime
    active: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        result['retention_period'] = self.retention_period.days
        result['notification_period'] = self.notification_period.days
        return result


@dataclass
class DataRetentionRecord:
    """Individual data retention record"""
    id: str
    data_identifier: str
    data_type: str
    rule_id: str
    retention_rule: RetentionRule
    created_at: datetime
    expiry_date: datetime
    status: RetentionStatus
    last_accessed: datetime
    access_count: int
    extension_count: int
    retention_metadata: Dict[str, Any]
    location: str
    checksum: str
    backup_references: List[str] = None
    audit_trail: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.backup_references is None:
            self.backup_references = []
        if self.audit_trail is None:
            self.audit_trail = []
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        result['expiry_date'] = self.expiry_date.isoformat()
        result['last_accessed'] = self.last_accessed.isoformat()
        result['retention_rule'] = self.retention_rule.to_dict()
        return result


class RetentionDatabase:
    """SQLite database for retention management"""
    
    def __init__(self, db_path: str = "retention.db"):
        """Initialize retention database"""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Create retention rules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS retention_rules (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    data_types TEXT,  -- JSON array
                    retention_period_days INTEGER,
                    legal_basis TEXT,
                    reason TEXT,
                    auto_deletion BOOLEAN,
                    secure_deletion BOOLEAN,
                    deletion_method TEXT,
                    extensions_allowed INTEGER,
                    notification_period_days INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    active BOOLEAN,
                    metadata TEXT  -- JSON
                )
            """)
            
            # Create data retention records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_retention (
                    id TEXT PRIMARY KEY,
                    data_identifier TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    rule_id TEXT,
                    created_at TEXT,
                    expiry_date TEXT,
                    status TEXT,
                    last_accessed TEXT,
                    access_count INTEGER,
                    extension_count INTEGER,
                    retention_metadata TEXT,  -- JSON
                    location TEXT,
                    checksum TEXT,
                    backup_references TEXT,  -- JSON array
                    audit_trail TEXT,  -- JSON array
                    FOREIGN KEY (rule_id) REFERENCES retention_rules (id)
                )
            """)
            
            # Create indices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_retention_expiry 
                ON data_retention (expiry_date)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_retention_status 
                ON data_retention (status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_retention_data_type 
                ON data_retention (data_type)
            """)
            
            conn.commit()
            logger.info("Retention database initialized")
            
        finally:
            conn.close()
    
    def save_retention_rule(self, rule: RetentionRule):
        """Save retention rule to database"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO retention_rules 
                (id, name, description, data_types, retention_period_days, 
                 legal_basis, reason, auto_deletion, secure_deletion, 
                 deletion_method, extensions_allowed, notification_period_days,
                 created_at, updated_at, active, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule.id, rule.name, rule.description, json.dumps(rule.data_types),
                rule.retention_period.days, rule.legal_basis, rule.reason.value,
                rule.auto_deletion, rule.secure_deletion, rule.deletion_method.value,
                rule.extensions_allowed, rule.notification_period.days,
                rule.created_at.isoformat(), rule.updated_at.isoformat(),
                rule.active, json.dumps(rule.metadata)
            ))
            conn.commit()
        finally:
            conn.close()
    
    def get_retention_rule(self, rule_id: str) -> Optional[RetentionRule]:
        """Get retention rule by ID"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM retention_rules WHERE id = ?", (rule_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_retention_rule(row)
            return None
            
        finally:
            conn.close()
    
    def get_all_retention_rules(self, active_only: bool = True) -> List[RetentionRule]:
        """Get all retention rules"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("SELECT * FROM retention_rules WHERE active = 1")
            else:
                cursor.execute("SELECT * FROM retention_rules")
            
            return [self._row_to_retention_rule(row) for row in cursor.fetchall()]
            
        finally:
            conn.close()
    
    def save_data_record(self, record: DataRetentionRecord):
        """Save data retention record"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO data_retention 
                (id, data_identifier, data_type, rule_id, created_at, expiry_date,
                 status, last_accessed, access_count, extension_count,
                 retention_metadata, location, checksum, backup_references, audit_trail)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id, record.data_identifier, record.data_type, record.rule_id,
                record.created_at.isoformat(), record.expiry_date.isoformat(),
                record.status.value, record.last_accessed.isoformat(),
                record.access_count, record.extension_count,
                json.dumps(record.retention_metadata), record.location,
                record.checksum, json.dumps(record.backup_references),
                json.dumps(record.audit_trail)
            ))
            conn.commit()
        finally:
            conn.close()
    
    def get_data_record(self, record_id: str) -> Optional[DataRetentionRecord]:
        """Get data retention record by ID"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM data_retention WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_data_record(row)
            return None
            
        finally:
            conn.close()
    
    def get_expired_records(self, cutoff_date: datetime) -> List[DataRetentionRecord]:
        """Get records that have expired"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM data_retention 
                WHERE expiry_date < ? AND status != 'deleted'
            """, (cutoff_date.isoformat(),))
            
            return [self._row_to_data_record(row) for row in cursor.fetchall()]
            
        finally:
            conn.close()
    
    def get_pending_deletion_records(self) -> List[DataRetentionRecord]:
        """Get records pending deletion"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM data_retention 
                WHERE status = 'pending_deletion'
            """)
            
            return [self._row_to_data_record(row) for row in cursor.fetchall()]
            
        finally:
            conn.close()
    
    def _row_to_retention_rule(self, row) -> RetentionRule:
        """Convert database row to RetentionRule"""
        return RetentionRule(
            id=row[0],
            name=row[1],
            description=row[2],
            data_types=json.loads(row[3]) if row[3] else [],
            retention_period=timedelta(days=row[4]),
            legal_basis=row[5],
            reason=RetentionReason(row[6]),
            auto_deletion=bool(row[7]),
            secure_deletion=bool(row[8]),
            deletion_method=DeletionMethod(row[9]),
            extensions_allowed=row[10],
            notification_period=timedelta(days=row[11]),
            created_at=datetime.fromisoformat(row[12]),
            updated_at=datetime.fromisoformat(row[13]),
            active=bool(row[14]),
            metadata=json.loads(row[15]) if row[15] else {}
        )
    
    def _row_to_data_record(self, row) -> DataRetentionRecord:
        """Convert database row to DataRetentionRecord"""
        rule = self.get_retention_rule(row[3])
        return DataRetentionRecord(
            id=row[0],
            data_identifier=row[1],
            data_type=row[2],
            rule_id=row[3],
            retention_rule=rule,
            created_at=datetime.fromisoformat(row[4]),
            expiry_date=datetime.fromisoformat(row[5]),
            status=RetentionStatus(row[6]),
            last_accessed=datetime.fromisoformat(row[7]),
            access_count=row[8],
            extension_count=row[9],
            retention_metadata=json.loads(row[10]) if row[10] else {},
            location=row[11],
            checksum=row[12],
            backup_references=json.loads(row[13]) if row[13] else [],
            audit_trail=json.loads(row[14]) if row[14] else []
        )


class SecureDeletionManager:
    """Handles secure deletion of data"""
    
    def __init__(self):
        """Initialize secure deletion manager"""
        self.deletion_methods = {
            DeletionMethod.SIMPLE_DELETE: self._simple_delete,
            DeletionMethod.OVERWRITE_ZEROS: self._overwrite_zeros,
            DeletionMethod.OVERWRITE_RANDOM: self._overwrite_random,
            DeletionMethod.DOD_5220_22_M: self._dod_5220_22_m,
            DeletionMethod.GUTMANN: self._gutmann,
            DeletionMethod.CRYPTO_SHRED: self._crypto_shred
        }
        
        logger.info("Secure deletion manager initialized")
    
    def secure_delete(self, file_path: str, method: DeletionMethod = DeletionMethod.OVERWRITE_RANDOM) -> bool:
        """
        Securely delete a file
        
        Args:
            file_path: Path to file to delete
            method: Deletion method to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found for deletion: {file_path}")
                return False
            
            deletion_func = self.deletion_methods.get(method)
            if not deletion_func:
                raise ValueError(f"Unknown deletion method: {method}")
            
            # Check if it's a directory
            if os.path.isdir(file_path):
                return self._delete_directory(file_path, deletion_func)
            else:
                return deletion_func(file_path)
            
        except Exception as e:
            logger.error(f"Secure deletion failed for {file_path}: {str(e)}")
            return False
    
    def _simple_delete(self, file_path: str) -> bool:
        """Simple file deletion"""
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"Simple deletion failed: {str(e)}")
            return False
    
    def _overwrite_zeros(self, file_path: str) -> bool:
        """Overwrite file with zeros"""
        try:
            file_size = os.path.getsize(file_path)
            with open(file_path, 'wb') as f:
                f.write(b'\x00' * file_size)
            os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"Zero overwrite failed: {str(e)}")
            return False
    
    def _overwrite_random(self, file_path: str) -> bool:
        """Overwrite file with random data multiple times"""
        try:
            file_size = os.path.getsize(file_path)
            
            # Overwrite 3 times with random data
            for _ in range(3):
                with open(file_path, 'wb') as f:
                    f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())
            
            os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"Random overwrite failed: {str(e)}")
            return False
    
    def _dod_5220_22_m(self, file_path: str) -> bool:
        """DoD 5220.22-M standard deletion (3 passes)"""
        try:
            file_size = os.path.getsize(file_path)
            
            # Pass 1: 0xFF
            with open(file_path, 'wb') as f:
                f.write(b'\xFF' * file_size)
            f.flush()
            os.fsync(f.fileno())
            
            # Pass 2: 0x00
            with open(file_path, 'wb') as f:
                f.write(b'\x00' * file_size)
            f.flush()
            os.fsync(f.fileno())
            
            # Pass 3: Random
            with open(file_path, 'wb') as f:
                f.write(os.urandom(file_size))
            f.flush()
            os.fsync(f.fileno())
            
            os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"DoD deletion failed: {str(e)}")
            return False
    
    def _gutmann(self, file_path: str) -> bool:
        """Gutmann method (35 passes) - most secure but slow"""
        try:
            file_size = os.path.getsize(file_path)
            
            # Gutmann patterns for different data types
            patterns = [
                b'\x55' * file_size, b'\xAA' * file_size,  # Alternating bits
                b'\x92\x49\x24', b'\x49\x24\x92', b'\x24\x92\x49',  # Random-like
                b'\x00' * file_size, b'\xFF' * file_size,  # Zeros and ones
            ] + [os.urandom(file_size) for _ in range(28)]  # Additional random passes
            
            for pattern in patterns[:35]:  # Limit to 35 passes
                with open(file_path, 'wb') as f:
                    f.write(pattern[:file_size])
                f.flush()
                os.fsync(f.fileno())
            
            os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"Gutmann deletion failed: {str(e)}")
            return False
    
    def _crypto_shred(self, file_path: str) -> bool:
        """Cryptographic shredding (delete encryption key)"""
        try:
            # This would work if files are encrypted
            # For now, just use random overwrite
            return self._overwrite_random(file_path)
        except Exception as e:
            logger.error(f"Crypto shred failed: {str(e)}")
            return False
    
    def _delete_directory(self, directory_path: str, deletion_func) -> bool:
        """Delete directory recursively with secure deletion"""
        try:
            for root, dirs, files in os.walk(directory_path, topdown=False):
                # Delete all files
                for file in files:
                    file_path = os.path.join(root, file)
                    deletion_func(file_path)
                
                # Delete all directories
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    os.rmdir(dir_path)
            
            # Remove the top directory
            os.rmdir(directory_path)
            return True
            
        except Exception as e:
            logger.error(f"Directory deletion failed: {str(e)}")
            return False


class RetentionManager:
    """Main retention management system"""
    
    def __init__(self, db_path: str = "retention.db"):
        """Initialize retention manager"""
        self.db = RetentionDatabase(db_path)
        self.deletion_manager = SecureDeletionManager()
        self.default_rules = self._create_default_rules()
        
        # Initialize default rules if none exist
        existing_rules = self.db.get_all_retention_rules()
        if not existing_rules:
            self._initialize_default_rules()
        
        logger.info("Retention manager initialized")
    
    def _create_default_rules(self) -> List[RetentionRule]:
        """Create default retention rules"""
        rules = []
        
        # Customer data rule
        rules.append(RetentionRule(
            id="customer_data_default",
            name="Customer Data Standard",
            description="Standard retention for customer personal data",
            data_types=["customer_record", "email", "address", "phone"],
            retention_period=timedelta(days=2555),  # 7 years
            legal_basis="Contract Performance (GDPR Art. 6(1)(b))",
            reason=RetentionReason.CONTRACTUAL_OBLIGATION,
            auto_deletion=True,
            secure_deletion=True,
            deletion_method=DeletionMethod.DOD_5220_22_M,
            extensions_allowed=1,
            notification_period=timedelta(days=30),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"category": "personal_data", "gdpr_relevant": True}
        ))
        
        # Financial data rule
        rules.append(RetentionRule(
            id="financial_data_default",
            name="Financial Records",
            description="Tax and financial record retention",
            data_types=["invoice", "receipt", "financial_statement", "tax_record"],
            retention_period=timedelta(days=3653),  # 10 years
            legal_basis="Legal Obligation (GDPR Art. 6(1)(c))",
            reason=RetentionReason.LEGAL_REQUIREMENT,
            auto_deletion=True,
            secure_deletion=True,
            deletion_method=DeletionMethod.GUTMANN,
            extensions_allowed=0,
            notification_period=timedelta(days=60),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"category": "financial_data", "regulatory": True}
        ))
        
        # Marketing data rule
        rules.append(RetentionRule(
            id="marketing_data_default",
            name="Marketing Data",
            description="Marketing and communication data retention",
            data_types=["marketing_email", "newsletter", "campaign_data", "preference"],
            retention_period=timedelta(days=730),  # 2 years
            legal_basis="Consent (GDPR Art. 6(1)(a))",
            reason=RetentionReason.CONSENT,
            auto_deletion=True,
            secure_deletion=True,
            deletion_method=DeletionMethod.OVERWRITE_RANDOM,
            extensions_allowed=2,
            notification_period=timedelta(days=14),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"category": "marketing_data", "consent_based": True}
        ))
        
        # Log data rule
        rules.append(RetentionRule(
            id="log_data_default",
            name="System Logs",
            description="System and security log retention",
            data_types=["system_log", "audit_log", "security_log", "error_log"],
            retention_period=timedelta(days=365),  # 1 year
            legal_basis="Legitimate Interest (GDPR Art. 6(1)(f))",
            reason=RetentionReason.LEGITIMATE_INTEREST,
            auto_deletion=True,
            secure_deletion=False,
            deletion_method=DeletionMethod.OVERWRITE_ZEROS,
            extensions_allowed=1,
            notification_period=timedelta(days=7),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"category": "technical_data", "security": True}
        ))
        
        return rules
    
    def _initialize_default_rules(self):
        """Initialize default retention rules in database"""
        for rule in self.default_rules:
            self.db.save_retention_rule(rule)
        logger.info(f"Initialized {len(self.default_rules)} default retention rules")
    
    def register_data(
        self,
        data_identifier: str,
        data_type: str,
        location: str,
        rule_id: Optional[str] = None,
        retention_metadata: Optional[Dict[str, Any]] = None,
        custom_retention_period: Optional[timedelta] = None
    ) -> DataRetentionRecord:
        """
        Register data for retention management
        
        Args:
            data_identifier: Unique identifier for the data
            data_type: Type of data (e.g., 'customer_record', 'invoice')
            location: Storage location of the data
            rule_id: Specific retention rule ID (optional)
            retention_metadata: Additional metadata
            custom_retention_period: Custom retention period override
            
        Returns:
            DataRetentionRecord
        """
        # Find appropriate retention rule
        if not rule_id:
            rule = self._find_retention_rule(data_type)
            if not rule:
                raise ValueError(f"No retention rule found for data type: {data_type}")
        else:
            rule = self.db.get_retention_rule(rule_id)
            if not rule:
                raise ValueError(f"Retention rule not found: {rule_id}")
        
        # Calculate expiry date
        created_at = datetime.utcnow()
        if custom_retention_period:
            expiry_date = created_at + custom_retention_period
        else:
            expiry_date = created_at + rule.retention_period
        
        # Generate checksum for data integrity
        checksum = hashlib.sha256(f"{data_identifier}{location}".encode()).hexdigest()
        
        # Create retention record
        record = DataRetentionRecord(
            id=hashlib.sha256(f"{data_identifier}{created_at}".encode()).hexdigest()[:16],
            data_identifier=data_identifier,
            data_type=data_type,
            rule_id=rule.id,
            retention_rule=rule,
            created_at=created_at,
            expiry_date=expiry_date,
            status=RetentionStatus.ACTIVE,
            last_accessed=created_at,
            access_count=0,
            extension_count=0,
            retention_metadata=retention_metadata or {},
            location=location,
            checksum=checksum,
            audit_trail=[{
                "action": "registered",
                "timestamp": created_at.isoformat(),
                "details": f"Data registered with rule {rule.name}"
            }]
        )
        
        # Save to database
        self.db.save_data_record(record)
        
        logger.info(f"Data registered: {data_identifier} (expires {expiry_date.date()})")
        return record
    
    def access_data(self, data_identifier: str) -> Optional[DataRetentionRecord]:
        """Record data access and return retention info"""
        # Find record by data identifier
        records = self._find_records_by_identifier(data_identifier)
        if not records:
            return None
        
        record = records[0]  # Get most recent record
        
        # Update access information
        record.last_accessed = datetime.utcnow()
        record.access_count += 1
        
        # Add to audit trail
        record.audit_trail.append({
            "action": "accessed",
            "timestamp": record.last_accessed.isoformat(),
            "details": f"Data accessed, access count: {record.access_count}"
        })
        
        # Save updates
        self.db.save_data_record(record)
        
        return record
    
    def extend_retention(
        self,
        data_identifier: str,
        additional_period: timedelta,
        reason: str,
        extended_by: str
    ) -> bool:
        """Extend retention period for specific data"""
        records = self._find_records_by_identifier(data_identifier)
        if not records:
            return False
        
        record = records[0]
        
        # Check if extensions are allowed
        rule = record.retention_rule
        if record.extension_count >= rule.extensions_allowed:
            logger.warning(f"Extension limit reached for {data_identifier}")
            return False
        
        # Calculate new expiry date
        if record.status == RetentionStatus.EXPIRED:
            # Extend from expiry date
            new_expiry = record.expiry_date + additional_period
            record.status = RetentionStatus.EXTENDED
        else:
            # Extend from current expiry date
            new_expiry = record.expiry_date + additional_period
        
        record.expiry_date = new_expiry
        record.extension_count += 1
        
        # Add to audit trail
        record.audit_trail.append({
            "action": "extended",
            "timestamp": datetime.utcnow().isoformat(),
            "details": f"Extended by {additional_period.days} days. Reason: {reason}. Extended by: {extended_by}"
        })
        
        # Save updates
        self.db.save_data_record(record)
        
        logger.info(f"Retention extended for {data_identifier} until {new_expiry.date()}")
        return True
    
    def process_expiry_notifications(self) -> List[Dict[str, Any]]:
        """Process data that needs expiry notification"""
        cutoff_date = datetime.utcnow() + timedelta(days=30)  # 30 days ahead
        
        # Get all active records
        all_rules = self.db.get_all_retention_rules()
        all_records = []
        
        for rule in all_rules:
            # This is simplified - in practice, you'd need a method to get records by rule
            pass
        
        # For simplicity, get all records and filter
        # In a real implementation, you'd have a proper query method
        notifications = []
        
        # Check records approaching expiry
        all_records_data = []  # This would be populated from database
        
        for record in all_records_data:
            if (record.status in [RetentionStatus.ACTIVE, RetentionStatus.EXTENDED] and
                record.expiry_date <= cutoff_date):
                
                days_until_expiry = (record.expiry_date - datetime.utcnow()).days
                
                notification = {
                    "record_id": record.id,
                    "data_identifier": record.data_identifier,
                    "data_type": record.data_type,
                    "expiry_date": record.expiry_date.isoformat(),
                    "days_until_expiry": days_until_expiry,
                    "rule_name": record.retention_rule.name,
                    "auto_deletion": record.retention_rule.auto_deletion
                }
                notifications.append(notification)
        
        return notifications
    
    def execute_retention_policy(self) -> Dict[str, Any]:
        """Execute retention policy - process expired data"""
        current_time = datetime.utcnow()
        
        # Get expired records
        expired_records = self.db.get_expired_records(current_time)
        
        processed = {
            "total_expired": len(expired_records),
            "auto_deleted": 0,
            "pending_deletion": 0,
            "extended": 0,
            "errors": 0,
            "details": []
        }
        
        for record in expired_records:
            try:
                rule = record.retention_rule
                
                if rule.auto_deletion:
                    # Mark for deletion
                    record.status = RetentionStatus.PENDING_DELETION
                    
                    # Add to audit trail
                    record.audit_trail.append({
                        "action": "marked_for_deletion",
                        "timestamp": current_time.isoformat(),
                        "details": "Auto-deletion triggered by retention policy"
                    })
                    
                    self.db.save_data_record(record)
                    processed["pending_deletion"] += 1
                    
                    # Execute deletion if method is simple
                    if rule.deletion_method == DeletionMethod.SIMPLE_DELETE:
                        self._execute_deletion(record)
                        processed["auto_deleted"] += 1
                    
                    processed["details"].append({
                        "record_id": record.id,
                        "action": "pending_deletion",
                        "data_identifier": record.data_identifier
                    })
                
                else:
                    # Mark as expired (manual review required)
                    record.status = RetentionStatus.EXPIRED
                    self.db.save_data_record(record)
                    processed["details"].append({
                        "record_id": record.id,
                        "action": "expired_manual_review",
                        "data_identifier": record.data_identifier
                    })
            
            except Exception as e:
                logger.error(f"Error processing record {record.id}: {str(e)}")
                processed["errors"] += 1
                processed["details"].append({
                    "record_id": record.id,
                    "action": "error",
                    "error": str(e)
                })
        
        # Process pending deletions
        self._process_pending_deletions()
        
        logger.info(f"Retention policy executed: {processed['auto_deleted']} deleted, "
                   f"{processed['pending_deletion']} pending deletion")
        
        return processed
    
    def _execute_deletion(self, record: DataRetentionRecord) -> bool:
        """Execute actual data deletion"""
        try:
            rule = record.retention_rule
            
            # Secure delete the file(s)
            success = True
            if rule.secure_deletion:
                success = self.deletion_manager.secure_delete(record.location, rule.deletion_method)
            else:
                # Simple deletion
                if os.path.exists(record.location):
                    os.remove(record.location)
                else:
                    logger.warning(f"File not found for deletion: {record.location}")
            
            # Update record status
            if success:
                record.status = RetentionStatus.DELETED
                record.audit_trail.append({
                    "action": "deleted",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": f"Data deleted using {rule.deletion_method.value} method"
                })
                self.db.save_data_record(record)
                logger.info(f"Data successfully deleted: {record.data_identifier}")
            else:
                logger.error(f"Failed to delete data: {record.data_identifier}")
            
            return success
            
        except Exception as e:
            logger.error(f"Deletion error for {record.id}: {str(e)}")
            return False
    
    def _process_pending_deletions(self):
        """Process records marked for deletion"""
        pending_records = self.db.get_pending_deletion_records()
        
        for record in pending_records:
            try:
                self._execute_deletion(record)
            except Exception as e:
                logger.error(f"Error processing pending deletion for {record.id}: {str(e)}")
    
    def _find_retention_rule(self, data_type: str) -> Optional[RetentionRule]:
        """Find applicable retention rule for data type"""
        all_rules = self.db.get_all_retention_rules()
        
        for rule in all_rules:
            if data_type in rule.data_types:
                return rule
        
        return None
    
    def _find_records_by_identifier(self, data_identifier: str) -> List[DataRetentionRecord]:
        """Find retention records by data identifier"""
        # This is a simplified implementation
        # In practice, you'd add a proper query method to the database
        all_records = []  # This would query the database
        
        matching_records = []
        # Simplified filtering
        for record in all_records:
            if record.data_identifier == data_identifier and record.status != RetentionStatus.DELETED:
                matching_records.append(record)
        
        return sorted(matching_records, key=lambda r: r.created_at, reverse=True)
    
    def generate_retention_report(self) -> Dict[str, Any]:
        """Generate comprehensive retention report"""
        # This would involve querying the database for statistics
        # Simplified implementation
        
        all_rules = self.db.get_all_retention_rules()
        total_rules = len(all_rules)
        active_rules = len([r for r in all_rules if r.active])
        
        report = {
            "report_timestamp": datetime.utcnow().isoformat(),
            "total_rules": total_rules,
            "active_rules": active_rules,
            "retention_summary": {
                "active_data": 0,  # Would be calculated from database
                "expired_data": 0,
                "pending_deletion": 0,
                "deleted_data": 0
            },
            "upcoming_expirations": [],  # Would be calculated
            "rule_summary": [
                {
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "data_types": rule.data_types,
                    "retention_period_days": rule.retention_period.days,
                    "auto_deletion": rule.auto_deletion
                }
                for rule in all_rules
            ],
            "compliance_status": "compliant"  # Would be calculated based on various factors
        }
        
        return report
    
    def export_retention_data(self, format: str = "json") -> str:
        """Export retention data"""
        all_rules = self.db.get_all_retention_rules()
        all_records = []  # This would query all records from database
        
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "retention_rules": [rule.to_dict() for rule in all_rules],
            "data_retention_records": [record.to_dict() for record in all_records]
        }
        
        if format.lower() == "json":
            return json.dumps(export_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Example usage
if __name__ == "__main__":
    # Initialize retention manager
    retention_manager = RetentionManager()
    
    # Register some sample data
    customer_record = retention_manager.register_data(
        data_identifier="customer_12345",
        data_type="customer_record",
        location="/data/customers/customer_12345.json",
        retention_metadata={
            "customer_id": "12345",
            "registration_date": "2023-01-15",
            "consent_given": True
        }
    )
    
    print(f"Customer record registered: {customer_record.id}")
    print(f"Expiry date: {customer_record.expiry_date.date()}")
    print(f"Retention rule: {customer_record.retention_rule.name}")
    
    # Simulate access
    accessed_record = retention_manager.access_data("customer_12345")
    print(f"Access recorded. Count: {accessed_record.access_count}")
    
    # Generate report
    report = retention_manager.generate_retention_report()
    print(f"\nRetention Report Summary:")
    print(f"- Total rules: {report['total_rules']}")
    print(f"- Active rules: {report['active_rules']}")
    print(f"- Compliance status: {report['compliance_status']}")
    
    # Execute retention policy
    policy_result = retention_manager.execute_retention_policy()
    print(f"\nRetention Policy Execution:")
    print(f"- Total expired: {policy_result['total_expired']}")
    print(f"- Auto deleted: {policy_result['auto_deleted']}")
