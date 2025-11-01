"""
Data Classification and Labeling System
Handles classification of data sensitivity levels and privacy categories
"""

import enum
import json
import logging
from typing import Dict, List, Optional, Any, Set, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
import hashlib
import os


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SensitivityLevel(enum.Enum):
    """Data sensitivity classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class PrivacyCategory(enum.Enum):
    """Privacy categories for GDPR compliance"""
    PERSONAL_DATA = "personal_data"
    SENSITIVE_PERSONAL_DATA = "sensitive_personal_data"
    SPECIAL_CATEGORY = "special_category"
    COMMERCIAL_DATA = "commercial_data"
    TECHNICAL_DATA = "technical_data"
    ANONYMIZED_DATA = "anonymized_data"
    PSEUDONYMIZED_DATA = "pseudonymized_data"


class DataSubject(enum.Enum):
    """Types of data subjects"""
    EMPLOYEE = "employee"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    CONTRACTOR = "contractor"
    VISITOR = "visitor"


@dataclass
class DataClassification:
    """Data classification metadata"""
    id: str
    sensitivity_level: SensitivityLevel
    privacy_category: PrivacyCategory
    data_subject: Optional[DataSubject]
    created_at: datetime
    updated_at: datetime
    retention_period: Optional[timedelta]
    legal_basis: Optional[str]
    purpose: str
    location: str
    encryption_status: bool
    pseudonymized: bool
    anonymized: bool
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()
        if not self.created_at:
            self.created_at = datetime.utcnow()
        if not self.updated_at:
            self.updated_at = datetime.utcnow()
    
    def _generate_id(self) -> str:
        """Generate unique ID for classification"""
        timestamp = datetime.utcnow().timestamp()
        return hashlib.sha256(f"{timestamp}".encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        if self.retention_period:
            result['retention_period'] = self.retention_period.days
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataClassification':
        """Create from dictionary"""
        data = data.copy()
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if data.get('retention_period'):
            data['retention_period'] = timedelta(days=data['retention_period'])
        return cls(**data)


class DataClassifier:
    """
    Core data classification engine
    Implements privacy-by-design principles for automatic data classification
    """
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """Initialize classifier with encryption support"""
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        self.classifications: Dict[str, DataClassification] = {}
        self.patterns = self._load_classification_patterns()
        logger.info("Data classifier initialized")
    
    def _load_classification_patterns(self) -> Dict[str, Any]:
        """Load data classification patterns and rules"""
        return {
            "sensitivity_patterns": {
                "public": [
                    "press release", "public statement", "website", "marketing",
                    "blog post", "public announcement"
                ],
                "internal": [
                    "internal memo", "employee handbook", "company policy",
                    "meeting notes", "internal report"
                ],
                "confidential": [
                    "financial data", "customer information", "vendor details",
                    "contract information", "business strategy"
                ],
                "restricted": [
                    "personal data", "hr records", "medical information",
                    "legal documents", "audit findings"
                ],
                "top_secret": [
                    "security credentials", "encryption keys", "national security",
                    "classified information", "trade secrets"
                ]
            },
            "pii_patterns": {
                "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
                "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                "ip_address": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            },
            "privacy_categories": {
                "personal_data": ["name", "email", "phone", "address", "id_number"],
                "sensitive_personal_data": ["medical", "biometric", "genetic", "racial", "religious"],
                "special_category": ["health", "biometric", "genetic", "racial", "ethnic", "political", "religious"],
                "commercial_data": ["business_id", "tax_id", "commercial_register"],
                "technical_data": ["ip_address", "device_id", "browser_info", "system_logs"]
            }
        }
    
    def classify_data(
        self,
        data: Union[str, Dict[str, Any], List[Any]],
        data_type: str,
        purpose: str,
        data_subject: Optional[DataSubject] = None,
        legal_basis: Optional[str] = None,
        manual_classification: Optional[Dict[str, str]] = None
    ) -> DataClassification:
        """
        Classify data based on content and context
        
        Args:
            data: Data to classify (string, dict, or list)
            data_type: Type of data (email, document, database_record, etc.)
            purpose: Purpose for data processing
            data_subject: Type of data subject
            legal_basis: Legal basis for processing (GDPR Article 6)
            manual_classification: Manual classification override
            
        Returns:
            DataClassification object with metadata
        """
        try:
            # Convert data to string for pattern analysis
            data_str = self._serialize_data(data)
            
            # Auto-classify based on patterns
            auto_sensitivity = self._auto_classify_sensitivity(data_str, data_type)
            auto_privacy_category = self._auto_classify_privacy_category(data_str)
            
            # Use manual classification if provided
            sensitivity_level = SensitivityLevel(
                manual_classification.get('sensitivity') if manual_classification 
                else auto_sensitivity
            )
            privacy_category = PrivacyCategory(
                manual_classification.get('privacy_category') if manual_classification
                else auto_privacy_category
            )
            
            # Determine retention period based on data type and legal requirements
            retention_period = self._determine_retention_period(
                sensitivity_level, privacy_category, data_type, legal_basis
            )
            
            # Create classification
            classification = DataClassification(
                id="",  # Will be generated in __post_init__
                sensitivity_level=sensitivity_level,
                privacy_category=privacy_category,
                data_subject=data_subject,
                created_at=None,  # Will be set in __post_init__
                updated_at=None,  # Will be set in __post_init__
                retention_period=retention_period,
                legal_basis=legal_basis,
                purpose=purpose,
                location="unknown",  # Should be set by caller
                encryption_status=privacy_category in [
                    PrivacyCategory.PERSONAL_DATA,
                    PrivacyCategory.SENSITIVE_PERSONAL_DATA,
                    PrivacyCategory.SPECIAL_CATEGORY
                ],
                pseudonymized=False,
                anonymized=False,
                metadata={
                    "data_type": data_type,
                    "auto_classified": manual_classification is None,
                    "pattern_matches": self._find_pattern_matches(data_str)
                }
            )
            
            self.classifications[classification.id] = classification
            logger.info(f"Data classified as {sensitivity_level.value}/{privacy_category.value}")
            
            return classification
            
        except Exception as e:
            logger.error(f"Classification error: {str(e)}")
            raise
    
    def _serialize_data(self, data: Union[str, Dict[str, Any], List[Any]]) -> str:
        """Convert data to string for pattern analysis"""
        if isinstance(data, str):
            return data.lower()
        elif isinstance(data, dict):
            return " ".join([
                str(v).lower() for v in json.dumps(data, default=str).lower().split()
            ])
        elif isinstance(data, list):
            return " ".join([
                str(item).lower() for item in data
            ])
        else:
            return str(data).lower()
    
    def _auto_classify_sensitivity(self, data_str: str, data_type: str) -> str:
        """Automatically classify data sensitivity based on patterns"""
        score = {level.value: 0 for level in SensitivityLevel}
        
        # Pattern matching
        for level, patterns in self.patterns["sensitivity_patterns"].items():
            for pattern in patterns:
                if pattern.lower() in data_str:
                    score[level] += 1
        
        # Data type influence
        type_influence = {
            "database_record": "confidential",
            "email": "internal",
            "document": "internal",
            "log_file": "internal",
            "financial_record": "confidential",
            "hr_record": "restricted",
            "legal_document": "restricted",
            "audit_log": "restricted"
        }
        if data_type in type_influence:
            score[type_influence[data_type]] += 2
        
        # Return highest scoring level
        return max(score, key=score.get)
    
    def _auto_classify_privacy_category(self, data_str: str) -> str:
        """Automatically classify privacy category"""
        # Check for PII patterns
        for pattern_name, pattern in self.patterns["pii_patterns"].items():
            if pattern.lower() in data_str or pattern_name in data_str:
                return PrivacyCategory.PERSONAL_DATA.value
        
        # Check for sensitive data indicators
        for category, indicators in self.patterns["privacy_categories"].items():
            for indicator in indicators:
                if indicator.lower() in data_str:
                    return category
        
        return "technical_data"
    
    def _determine_retention_period(
        self,
        sensitivity: SensitivityLevel,
        category: PrivacyCategory,
        data_type: str,
        legal_basis: Optional[str]
    ) -> Optional[timedelta]:
        """Determine retention period based on classification and legal requirements"""
        # GDPR and legal requirements
        retention_rules = {
            (SensitivityLevel.PUBLIC, PrivacyCategory.TECHNICAL_DATA): timedelta(days=30),
            (SensitivityLevel.INTERNAL, PrivacyCategory.TECHNICAL_DATA): timedelta(days=90),
            (SensitivityLevel.CONFIDENTIAL, PrivacyCategory.COMMERCIAL_DATA): timedelta(days=365*7),
            (SensitivityLevel.RESTRICTED, PrivacyCategory.PERSONAL_DATA): timedelta(days=365*6),
            (SensitivityLevel.TOP_SECRET, PrivacyCategory.SPECIAL_CATEGORY): timedelta(days=365*10),
        }
        
        # Default retention based on category
        default_retention = {
            PrivacyCategory.PERSONAL_DATA: timedelta(days=365*6),
            PrivacyCategory.SENSITIVE_PERSONAL_DATA: timedelta(days=365*10),
            PrivacyCategory.SPECIAL_CATEGORY: timedelta(days=365*10),
            PrivacyCategory.COMMERCIAL_DATA: timedelta(days=365*7),
            PrivacyCategory.TECHNICAL_DATA: timedelta(days=365),
            PrivacyCategory.ANONYMIZED_DATA: None,  # Can be kept indefinitely
            PrivacyCategory.PSEUDONYMIZED_DATA: timedelta(days=365*6),
        }
        
        # Try specific rule first
        specific_rule = retention_rules.get((sensitivity, category))
        if specific_rule:
            return specific_rule
        
        # Fall back to category default
        return default_retention.get(category)
    
    def _find_pattern_matches(self, data_str: str) -> List[str]:
        """Find matching patterns in data"""
        matches = []
        for category, indicators in self.patterns["privacy_categories"].items():
            for indicator in indicators:
                if indicator.lower() in data_str:
                    matches.append(indicator)
        return matches
    
    def update_classification(
        self,
        classification_id: str,
        **kwargs
    ) -> Optional[DataClassification]:
        """Update existing classification"""
        if classification_id not in self.classifications:
            return None
        
        classification = self.classifications[classification_id]
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(classification, key):
                setattr(classification, key, value)
        
        classification.updated_at = datetime.utcnow()
        return classification
    
    def get_classification(self, classification_id: str) -> Optional[DataClassification]:
        """Get classification by ID"""
        return self.classifications.get(classification_id)
    
    def list_classifications(
        self,
        sensitivity_level: Optional[SensitivityLevel] = None,
        privacy_category: Optional[PrivacyCategory] = None,
        data_subject: Optional[DataSubject] = None
    ) -> List[DataClassification]:
        """List classifications with optional filters"""
        results = list(self.classifications.values())
        
        if sensitivity_level:
            results = [c for c in results if c.sensitivity_level == sensitivity_level]
        if privacy_category:
            results = [c for c in results if c.privacy_category == privacy_category]
        if data_subject:
            results = [c for c in results if c.data_subject == data_subject]
        
        return results
    
    def export_classifications(self, format: str = "json") -> str:
        """Export classifications to file"""
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "total_classifications": len(self.classifications),
            "classifications": [
                classification.to_dict() 
                for classification in self.classifications.values()
            ]
        }
        
        if format.lower() == "json":
            return json.dumps(data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def validate_classification(self, classification: DataClassification) -> List[str]:
        """Validate classification compliance"""
        issues = []
        
        # Check required fields
        if not classification.purpose:
            issues.append("Missing data processing purpose")
        
        # Check retention policy
        if not classification.retention_period and classification.privacy_category in [
            PrivacyCategory.PERSONAL_DATA,
            PrivacyCategory.SENSITIVE_PERSONAL_DATA,
            PrivacyCategory.SPECIAL_CATEGORY
        ]:
            issues.append("Personal data should have retention policy")
        
        # Check encryption for sensitive data
        if classification.privacy_category in [
            PrivacyCategory.SENSITIVE_PERSONAL_DATA,
            PrivacyCategory.SPECIAL_CATEGORY
        ] and not classification.encryption_status:
            issues.append("Sensitive data must be encrypted")
        
        # Check legal basis
        if classification.privacy_category in [
            PrivacyCategory.PERSONAL_DATA,
            PrivacyCategory.SENSITIVE_PERSONAL_DATA,
            PrivacyCategory.SPECIAL_CATEGORY
        ] and not classification.legal_basis:
            issues.append("Personal data processing requires legal basis")
        
        return issues
    
    def generate_privacy_labels(self, classification: DataClassification) -> Dict[str, str]:
        """Generate privacy labels for UI display"""
        labels = {
            "sensitivity": self._get_sensitivity_label(classification.sensitivity_level),
            "privacy_category": self._get_privacy_category_label(classification.privacy_category),
            "retention": self._get_retention_label(classification.retention_period),
            "encryption": "Encrypted" if classification.encryption_status else "Not Encrypted",
            "pseudonymization": "Pseudonymized" if classification.pseudonymized else "Not Pseudonymized",
            "anonymization": "Anonymized" if classification.anonymized else "Not Anonymized"
        }
        return labels
    
    def _get_sensitivity_label(self, level: SensitivityLevel) -> str:
        """Get user-friendly sensitivity label"""
        labels = {
            SensitivityLevel.PUBLIC: "🔓 Public",
            SensitivityLevel.INTERNAL: "🟡 Internal Use",
            SensitivityLevel.CONFIDENTIAL: "🟠 Confidential",
            SensitivityLevel.RESTRICTED: "🔴 Restricted",
            SensitivityLevel.TOP_SECRET: "⚫ Top Secret"
        }
        return labels.get(level, "Unknown")
    
    def _get_privacy_category_label(self, category: PrivacyCategory) -> str:
        """Get user-friendly privacy category label"""
        labels = {
            PrivacyCategory.PERSONAL_DATA: "Personal Data",
            PrivacyCategory.SENSITIVE_PERSONAL_DATA: "Sensitive Personal Data",
            PrivacyCategory.SPECIAL_CATEGORY: "Special Category Data",
            PrivacyCategory.COMMERCIAL_DATA: "Commercial Data",
            PrivacyCategory.TECHNICAL_DATA: "Technical Data",
            PrivacyCategory.ANONYMIZED_DATA: "Anonymized Data",
            PrivacyCategory.PSEUDONYMIZED_DATA: "Pseudonymized Data"
        }
        return labels.get(category, "Unknown")
    
    def _get_retention_label(self, period: Optional[timedelta]) -> str:
        """Get user-friendly retention label"""
        if not period:
            return "No Expiry"
        days = period.days
        if days < 30:
            return f"{days} days"
        elif days < 365:
            return f"{days // 30} months"
        else:
            return f"{days // 365} years"


# Example usage
if __name__ == "__main__":
    # Initialize classifier
    classifier = DataClassifier()
    
    # Example: Classify customer email data
    customer_email = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
        "address": "123 Main St, City, State"
    }
    
    classification = classifier.classify_data(
        data=customer_email,
        data_type="customer_record",
        purpose="customer_service",
        data_subject=DataSubject.CUSTOMER,
        legal_basis="consent"
    )
    
    print(f"Classification ID: {classification.id}")
    print(f"Sensitivity: {classification.sensitivity_level.value}")
    print(f"Privacy Category: {classification.privacy_category.value}")
    print(f"Retention Period: {classification.retention_period}")
    print(f"Privacy Labels: {classifier.generate_privacy_labels(classification)}")
    
    # Validate classification
    issues = classifier.validate_classification(classification)
    if issues:
        print(f"Classification Issues: {issues}")
    else:
        print("Classification is compliant")
