"""
PII Detection and Masking System
Detects and masks Personally Identifiable Information in data
Implements GDPR Article 25 - Data Protection by Design
"""

import re
import json
import hashlib
import logging
from typing import Dict, List, Optional, Union, Tuple, Set, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from cryptography.fernet import Fernet
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PIIType(Enum):
    """Types of PII that can be detected"""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "social_security_number"
    CREDIT_CARD = "credit_card"
    BANK_ACCOUNT = "bank_account"
    DRIVER_LICENSE = "driver_license"
    PASSPORT = "passport"
    IP_ADDRESS = "ip_address"
    MAC_ADDRESS = "mac_address"
    DATE_OF_BIRTH = "date_of_birth"
    NAME = "name"
    ADDRESS = "address"
    ZIP_CODE = "zip_code"
    MEDICAL_RECORD = "medical_record"
    BIOMETRIC_DATA = "biometric_data"
    LOCATION_DATA = "location_data"
    DEVICE_ID = "device_id"
    COOKIE_ID = "cookie_id"


class MaskingStrategy(Enum):
    """Strategies for masking PII"""
    HASH = "hash"
    PARTIAL_MASK = "partial_mask"
    FULL_MASK = "full_mask"
    TOKENIZATION = "tokenization"
    PSEUDONYMIZATION = "pseudonymization"
    GENERALIZATION = "generalization"
    SUPPRESSION = "suppression"


@dataclass
class PIIMatch:
    """Represents a detected PII match"""
    pii_type: PIIType
    value: str
    start_position: int
    end_position: int
    confidence: float
    context: str = ""
    masked_value: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pii_type": self.pii_type.value,
            "value": self.value,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "confidence": self.confidence,
            "context": self.context,
            "masked_value": self.masked_value
        }


@dataclass
class PIIAnalysis:
    """Results of PII analysis"""
    matches: List[PIIMatch] = field(default_factory=list)
    total_pii_count: int = 0
    risk_score: float = 0.0
    categories_found: Set[PIIType] = field(default_factory=set)
    anonymized: bool = False
    pseudonymized: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "matches": [match.to_dict() for match in self.matches],
            "total_pii_count": self.total_pii_count,
            "risk_score": self.risk_score,
            "categories_found": [cat.value for cat in self.categories_found],
            "anonymized": self.anonymized,
            "pseudonymized": self.pseudonymized,
            "timestamp": self.timestamp.isoformat()
        }


class PIIPatterns:
    """Collection of PII detection patterns"""
    
    # Regex patterns for different PII types
    PATTERNS = {
        PIIType.EMAIL: re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            re.IGNORECASE
        ),
        PIIType.PHONE: re.compile(
            r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            re.IGNORECASE
        ),
        PIIType.SSN: re.compile(
            r'\b\d{3}-\d{2}-\d{4}\b',
            re.IGNORECASE
        ),
        PIIType.CREDIT_CARD: re.compile(
            r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            re.IGNORECASE
        ),
        PIIType.IP_ADDRESS: re.compile(
            r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            re.IGNORECASE
        ),
        PIIType.MAC_ADDRESS: re.compile(
            r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b'
        ),
        PIIType.ZIP_CODE: re.compile(
            r'\b\d{5}(?:-\d{4})?\b',
            re.IGNORECASE
        ),
        PIIType.DATE_OF_BIRTH: re.compile(
            r'\b(?:0?[1-9]|1[0-2])[/\-](?:0?[1-9]|[12][0-9]|3[01])[/\-](?:19|20)\d{2}\b',
            re.IGNORECASE
        ),
        PIIType.DRIVER_LICENSE: re.compile(
            r'\b[A-Z]{1,2}\d{6,8}\b',
            re.IGNORECASE
        )
    }
    
    # Keywords for contextual PII detection
    KEYWORDS = {
        PIIType.NAME: [
            "name", "first name", "last name", "full name", "surname", "given name",
            "first", "last", "mr", "mrs", "ms", "dr", "prof"
        ],
        PIIType.ADDRESS: [
            "address", "street", "avenue", "road", "boulevard", "lane", "drive",
            "suite", "apartment", "apt", "city", "state", "province", "country"
        ],
        PIIType.MEDICAL_RECORD: [
            "medical", "diagnosis", "treatment", "medication", "prescription",
            "patient", "doctor", "hospital", "clinic", "insurance"
        ],
        PIIType.BIOMETRIC_DATA: [
            "fingerprint", "retina", "iris", "facial", "voice", "biometric",
            "dna", "genetic"
        ],
        PIIType.LOCATION_DATA: [
            "gps", "location", "coordinates", "latitude", "longitude",
            "tracking", "geo", "location-based"
        ]
    }


class PIIExtractor:
    """Advanced PII extraction using ML and pattern matching"""
    
    def __init__(self):
        """Initialize the PII extractor"""
        self.patterns = PIIPatterns.PATTERNS
        self.keywords = PIIPatterns.KEYWORDS
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        
        # Predefined name lists for higher accuracy
        self.common_names = self._load_common_names()
        self.address_patterns = self._load_address_patterns()
        
        logger.info("PII extractor initialized")
    
    def _load_common_names(self) -> Set[str]:
        """Load common names for better name detection"""
        # In a real implementation, this would load from a comprehensive database
        return {
            "john", "jane", "michael", "sarah", "david", "emma", "james", "olivia",
            "robert", "ava", "william", "isabella", "richard", "sophia", "thomas", "charlotte"
        }
    
    def _load_address_patterns(self) -> List[str]:
        """Load address patterns for better address detection"""
        return [
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)',
            r'P\.?\s*O\.?\s*Box\s+\d+',
            r'\d+\s+[A-Za-z\s]+(?:Apartment| Apt|Unit)\s*[#]?\s*\d+'
        ]
    
    def detect_pii(self, text: str, context: Optional[str] = None) -> PIIAnalysis:
        """
        Detect PII in text
        
        Args:
            text: Text to analyze for PII
            context: Additional context for better detection
            
        Returns:
            PIIAnalysis with detected PII matches
        """
        analysis = PIIAnalysis()
        
        if not text or not text.strip():
            return analysis
        
        # Pattern-based detection
        pattern_matches = self._detect_with_patterns(text, context)
        analysis.matches.extend(pattern_matches)
        
        # Contextual detection
        contextual_matches = self._detect_contextual_pii(text, context)
        analysis.matches.extend(contextual_matches)
        
        # ML-based detection for complex cases
        ml_matches = self._detect_with_ml(text, context)
        analysis.matches.extend(ml_matches)
        
        # Remove duplicates and calculate statistics
        analysis.matches = self._remove_duplicates(analysis.matches)
        analysis.total_pii_count = len(analysis.matches)
        analysis.categories_found = {match.pii_type for match in analysis.matches}
        analysis.risk_score = self._calculate_risk_score(analysis)
        
        return analysis
    
    def _detect_with_patterns(self, text: str, context: Optional[str]) -> List[PIIMatch]:
        """Detect PII using regex patterns"""
        matches = []
        
        for pii_type, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                confidence = self._calculate_pattern_confidence(pii_type, match.group(), context)
                
                matches.append(PIIMatch(
                    pii_type=pii_type,
                    value=match.group(),
                    start_position=match.start(),
                    end_position=match.end(),
                    confidence=confidence,
                    context=context or ""
                ))
        
        return matches
    
    def _detect_contextual_pii(self, text: str, context: Optional[str]) -> List[PIIMatch]:
        """Detect PII using contextual keywords and ML"""
        matches = []
        text_lower = text.lower()
        
        # Check for contextual keywords
        for pii_type, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Look for nearby values that could be PII
                    nearby_matches = self._find_nearby_pii(text, keyword, pii_type)
                    matches.extend(nearby_matches)
        
        # Special handling for names
        name_matches = self._detect_names(text, context)
        matches.extend(name_matches)
        
        # Special handling for addresses
        address_matches = self._detect_addresses(text, context)
        matches.extend(address_matches)
        
        return matches
    
    def _detect_with_ml(self, text: str, context: Optional[str]) -> List[PIIMatch]:
        """Detect PII using machine learning techniques"""
        matches = []
        
        # This is a simplified ML approach
        # In practice, you would use a trained NER model
        text_lower = text.lower()
        
        # Look for patterns that might indicate PII
        if any(word in text_lower for word in ["patient", "customer", "user", "client"]):
            # Look for numbers or codes that might be IDs
            id_patterns = re.findall(r'\b[A-Z0-9]{6,12}\b', text)
            for id_val in id_patterns:
                matches.append(PIIMatch(
                    pii_type=PIIType.DEVICE_ID,
                    value=id_val,
                    start_position=text.find(id_val),
                    end_position=text.find(id_val) + len(id_val),
                    confidence=0.6,
                    context="detected near user identifier"
                ))
        
        return matches
    
    def _find_nearby_pii(self, text: str, keyword: str, pii_type: PIIType) -> List[PIIMatch]:
        """Find PII values near contextual keywords"""
        matches = []
        text_lower = text.lower()
        keyword_pos = text_lower.find(keyword.lower())
        
        if keyword_pos != -1:
            # Look in a window around the keyword
            window_start = max(0, keyword_pos - 20)
            window_end = min(len(text), keyword_pos + len(keyword) + 20)
            window_text = text[window_start:window_end]
            
            # Try to extract relevant patterns
            if pii_type == PIIType.PHONE:
                phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', window_text)
                if phone_match:
                    matches.append(PIIMatch(
                        pii_type=pii_type,
                        value=phone_match.group(),
                        start_position=window_start + phone_match.start(),
                        end_position=window_start + phone_match.end(),
                        confidence=0.8,
                        context=f"found near '{keyword}'"
                    ))
        
        return matches
    
    def _detect_names(self, text: str, context: Optional[str]) -> List[PIIMatch]:
        """Detect personal names in text"""
        matches = []
        
        # Common name patterns
        name_patterns = [
            r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b',  # First Last
            r'\b(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+([A-Z][a-z]+)\b',  # Title First
        ]
        
        for pattern in name_patterns:
            for match in re.finditer(pattern, text):
                full_name = match.group()
                words = full_name.split()
                
                # Check if it's likely a real name (not all uppercase/lowercase)
                if len(words) >= 2:
                    first_name = words[0].strip('.:')
                    last_name = words[-1]
                    
                    # Simple heuristic: check if names are in common names list
                    if (first_name.lower() in self.common_names or 
                        len(first_name) > 2 and first_name[0].isupper()):
                        
                        matches.append(PIIMatch(
                            pii_type=PIIType.NAME,
                            value=full_name,
                            start_position=match.start(),
                            end_position=match.end(),
                            confidence=0.7,
                            context=context or ""
                        ))
        
        return matches
    
    def _detect_addresses(self, text: str, context: Optional[str]) -> List[PIIMatch]:
        """Detect addresses in text"""
        matches = []
        
        for pattern_str in self.address_patterns:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            for match in pattern.finditer(text):
                matches.append(PIIMatch(
                    pii_type=PIIType.ADDRESS,
                    value=match.group(),
                    start_position=match.start(),
                    end_position=match.end(),
                    confidence=0.8,
                    context=context or ""
                ))
        
        return matches
    
    def _calculate_pattern_confidence(
        self, 
        pii_type: PIIType, 
        value: str, 
        context: Optional[str]
    ) -> float:
        """Calculate confidence score for pattern match"""
        base_confidence = 0.9  # High confidence for regex patterns
        
        # Adjust based on value complexity
        if len(value) < 3:
            base_confidence *= 0.5
        elif len(value) > 20:
            base_confidence *= 0.7
        
        # Adjust based on context
        if context:
            context_lower = context.lower()
            if any(keyword in context_lower for keyword in ["email", "phone", "address"]):
                base_confidence *= 1.1
        
        return min(base_confidence, 1.0)
    
    def _remove_duplicates(self, matches: List[PIIMatch]) -> List[PIIMatch]:
        """Remove duplicate matches"""
        seen = set()
        unique_matches = []
        
        for match in matches:
            key = (match.pii_type, match.start_position, match.end_position)
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        return unique_matches
    
    def _calculate_risk_score(self, analysis: PIIAnalysis) -> float:
        """Calculate overall PII risk score"""
        if not analysis.matches:
            return 0.0
        
        # Risk weights for different PII types
        risk_weights = {
            PIIType.CREDIT_CARD: 1.0,
            PIIType.SSN: 1.0,
            PIIType.DRIVER_LICENSE: 0.9,
            PIIType.PASSPORT: 0.9,
            PIIType.BANK_ACCOUNT: 0.9,
            PIIType.MEDICAL_RECORD: 0.8,
            PIIType.BIOMETRIC_DATA: 0.8,
            PIIType.DATE_OF_BIRTH: 0.7,
            PIIType.EMAIL: 0.6,
            PIIType.PHONE: 0.6,
            PIIType.NAME: 0.5,
            PIIType.ADDRESS: 0.5,
            PIIType.IP_ADDRESS: 0.4,
            PIIType.ZIP_CODE: 0.3
        }
        
        # Calculate weighted average
        total_weight = 0.0
        weighted_score = 0.0
        
        for match in analysis.matches:
            weight = risk_weights.get(match.pii_type, 0.5)
            total_weight += weight
            weighted_score += match.confidence * weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0


class PIIDetector:
    """Main PII detection and masking system"""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """Initialize PII detector"""
        self.extractor = PIIExtractor()
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        self.token_map: Dict[str, str] = {}  # For tokenization
        self.analysis_history: List[PIIAnalysis] = []
        
        logger.info("PII detector initialized")
    
    def analyze_data(
        self,
        data: Union[str, Dict[str, Any], List[Any]],
        context: Optional[str] = None
    ) -> PIIAnalysis:
        """
        Analyze data for PII
        
        Args:
            data: Data to analyze (string, dict, or list)
            context: Additional context for better detection
            
        Returns:
            PIIAnalysis with detection results
        """
        # Convert data to text for analysis
        text_data = self._convert_to_text(data)
        
        # Analyze for PII
        analysis = self.extractor.detect_pii(text_data, context)
        
        # Store in history
        self.analysis_history.append(analysis)
        
        logger.info(f"Analysis completed: {analysis.total_pii_count} PII items found")
        return analysis
    
    def mask_pii(
        self,
        data: Union[str, Dict[str, Any], List[Any]],
        strategy: MaskingStrategy = MaskingStrategy.PARTIAL_MASK,
        preserve_format: bool = True
    ) -> Tuple[Union[str, Dict[str, Any], List[Any]], PIIAnalysis]:
        """
        Mask PII in data
        
        Args:
            data: Data to mask
            strategy: Masking strategy to use
            preserve_format: Whether to preserve original format
            
        Returns:
            Tuple of (masked_data, analysis)
        """
        # Analyze first
        analysis = self.analyze_data(data)
        
        # Convert data to text for masking
        original_data = self._convert_to_text(data)
        masked_text = original_data
        
        # Apply masking to each match
        for match in sorted(analysis.matches, key=lambda m: m.start_position, reverse=True):
            masked_value = self._apply_masking_strategy(
                match.value, 
                strategy, 
                preserve_format
            )
            match.masked_value = masked_value
            
            # Replace in text
            masked_text = (
                masked_text[:match.start_position] + 
                masked_value + 
                masked_text[match.end_position:]
            )
        
        # Convert back to original format if needed
        masked_data = self._convert_back_to_original_format(
            masked_text, 
            original_data, 
            data
        )
        
        # Update analysis with masked values
        for match in analysis.matches:
            if match.masked_value:
                match.value = match.masked_value
        
        logger.info(f"PII masked using {strategy.value} strategy")
        return masked_data, analysis
    
    def _apply_masking_strategy(
        self,
        value: str,
        strategy: MaskingStrategy,
        preserve_format: bool = True
    ) -> str:
        """Apply specific masking strategy to a value"""
        if not value:
            return value
        
        if strategy == MaskingStrategy.HASH:
            return hashlib.sha256(value.encode()).hexdigest()[:16]
        
        elif strategy == MaskingStrategy.FULL_MASK:
            return "*" * len(value)
        
        elif strategy == MaskingStrategy.PARTIAL_MASK:
            return self._partial_mask(value, preserve_format)
        
        elif strategy == MaskingStrategy.TOKENIZATION:
            token = self._get_or_create_token(value)
            return token
        
        elif strategy == MaskingStrategy.PSEUDONYMIZATION:
            return self._pseudonymize(value)
        
        elif strategy == MaskingStrategy.GENERALIZATION:
            return self._generalize(value)
        
        elif strategy == MaskingStrategy.SUPPRESSION:
            return "[REDACTED]"
        
        else:
            return value
    
    def _partial_mask(self, value: str, preserve_format: bool) -> str:
        """Apply partial masking (show first/last characters)"""
        if len(value) <= 2:
            return "*" * len(value)
        
        if preserve_format and "@" in value:  # Email
            parts = value.split("@")
            username = parts[0]
            domain = parts[1]
            masked_username = username[0] + "*" * (len(username) - 2) + username[-1] if len(username) > 2 else "*" * len(username)
            return f"{masked_username}@{domain}"
        
        elif preserve_format and "-" in value and len(value.replace("-", "")) == 9:  # Phone
            digits = value.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
            if len(digits) >= 10:
                return f"{digits[:3]}-***-*{digits[-2:]}"
        
        # Generic partial masking
        if len(value) <= 4:
            return value[0] + "*" * (len(value) - 1)
        else:
            return value[:2] + "*" * (len(value) - 4) + value[-2:]
    
    def _get_or_create_token(self, value: str) -> str:
        """Get or create token for value"""
        if value in self.token_map:
            return self.token_map[value]
        
        token = f"TOK_{len(self.token_map):06d}"
        self.token_map[value] = token
        return token
    
    def _pseudonymize(self, value: str) -> str:
        """Pseudonymize value (consistent but not reversible)"""
        # Create a hash that includes the value and a salt
        salt = "privacy_pseudo_salt"
        hash_value = hashlib.sha256((value + salt).encode()).hexdigest()
        return f"PSEUD_{hash_value[:12]}"
    
    def _generalize(self, value: str) -> str:
        """Generalize value to reduce specificity"""
        # Simple generalization rules
        if re.match(r'\d{4}-\d{2}-\d{2}', value):  # Date
            year = value.split('-')[0]
            return f"{year}-**-**"
        elif re.match(r'\d{5}(-\d{4})?', value):  # ZIP code
            return value[:3] + "**"
        elif re.match(r'\d{3}-\d{2}-\d{4}', value):  # SSN
            return f"***-**-{value[-4:]}"
        else:
            # General case: keep first few characters
            return value[:2] + "***"
    
    def _convert_to_text(self, data: Union[str, Dict[str, Any], List[Any]]) -> str:
        """Convert various data types to text for analysis"""
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            return json.dumps(data, default=str)
        elif isinstance(data, list):
            return " ".join(str(item) for item in data)
        else:
            return str(data)
    
    def _convert_back_to_original_format(
        self,
        masked_text: str,
        original_text: str,
        original_data: Union[str, Dict[str, Any], List[Any]]
    ) -> Union[str, Dict[str, Any], List[Any]]:
        """Convert masked text back to original format if possible"""
        if isinstance(original_data, str):
            return masked_text
        elif isinstance(original_data, dict):
            try:
                return json.loads(masked_text)
            except json.JSONDecodeError:
                return original_data
        elif isinstance(original_data, list):
            # Split back into list items (simplified)
            return masked_text.split()
        else:
            return masked_text
    
    def anonymize_data(
        self,
        data: Union[str, Dict[str, Any], List[Any]],
        irreversible: bool = True
    ) -> Tuple[Union[str, Dict[str, Any], List[Any]], PIIAnalysis]:
        """
        Anonymize data (make re-identification impossible)
        
        Args:
            data: Data to anonymize
            irreversible: Whether to make anonymization irreversible
            
        Returns:
            Tuple of (anonymized_data, analysis)
        """
        # Use full masking or hashing strategy for anonymization
        strategy = MaskingStrategy.HASH if irreversible else MaskingStrategy.PSEUDONYMIZATION
        
        # First mask PII
        masked_data, analysis = self.mask_pii(data, strategy, preserve_format=False)
        
        # Mark as anonymized
        analysis.anonymized = True
        analysis.pseudonymized = not irreversible
        
        logger.info(f"Data {'anonymized' if irreversible else 'pseudonymized'}")
        return masked_data, analysis
    
    def export_analysis(self, analysis: PIIAnalysis, format: str = "json") -> str:
        """Export PII analysis results"""
        if format.lower() == "json":
            return json.dumps(analysis.to_dict(), indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_privacy_report(self) -> Dict[str, Any]:
        """Generate comprehensive privacy report"""
        total_analyses = len(self.analysis_history)
        total_pii_items = sum(a.total_pii_count for a in self.analysis_history)
        avg_risk_score = np.mean([a.risk_score for a in self.analysis_history]) if self.analysis_history else 0.0
        
        pii_type_counts = {}
        for analysis in self.analysis_history:
            for pii_type in analysis.categories_found:
                pii_type_counts[pii_type.value] = pii_type_counts.get(pii_type.value, 0) + 1
        
        return {
            "report_timestamp": datetime.utcnow().isoformat(),
            "total_analyses": total_analyses,
            "total_pii_items_detected": total_pii_items,
            "average_risk_score": round(avg_risk_score, 2),
            "pii_type_distribution": pii_type_counts,
            "token_map_size": len(self.token_map),
            "compliance_status": "compliant" if avg_risk_score < 0.5 else "requires_review"
        }


# Example usage
if __name__ == "__main__":
    # Initialize PII detector
    detector = PIIDetector()
    
    # Example data with PII
    sample_data = """
    Contact: John Smith
    Email: john.smith@company.com
    Phone: 555-123-4567
    SSN: 123-45-6789
    Address: 123 Main Street, Anytown, NY 12345
    """
    
    # Analyze data
    analysis = detector.analyze_data(sample_data, "contact information")
    print(f"PII Analysis Results:")
    print(f"- Total PII items: {analysis.total_pii_count}")
    print(f"- Risk score: {analysis.risk_score:.2f}")
    print(f"- Categories found: {[cat.value for cat in analysis.categories_found]}")
    
    # Show matches
    for match in analysis.matches:
        print(f"- {match.pii_type.value}: '{match.value}' (confidence: {match.confidence:.2f})")
    
    # Mask PII
    masked_data, _ = detector.mask_pii(sample_data, MaskingStrategy.PARTIAL_MASK)
    print(f"\nMasked Data:\n{masked_data}")
    
    # Anonymize data
    anonymized_data, anon_analysis = detector.anonymize_data(sample_data)
    print(f"\nAnonymized Data:\n{anonymized_data}")
    print(f"Anonymization successful: {anon_analysis.anonymized}")
    
    # Generate privacy report
    report = detector.get_privacy_report()
    print(f"\nPrivacy Report: {json.dumps(report, indent=2)}")
