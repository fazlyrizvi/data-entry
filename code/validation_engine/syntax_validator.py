"""
Syntax Validation Module
Handles validation of common data formats including email, phone, date, and custom patterns.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from enum import Enum

# Optional imports for enhanced functionality
try:
    import phonenumbers
    from phonenumbers import NumberParseException
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False
    phonenumbers = None
    NumberParseException = Exception


class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class SyntaxValidationResult:
    """Result of syntax validation."""
    
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []
        self.confidence_score = 1.0
        self.suggestions = []
        
    def add_error(self, message: str, suggestion: str = None):
        """Add error with optional suggestion."""
        self.is_valid = False
        self.errors.append(message)
        if suggestion:
            self.suggestions.append(suggestion)
            
    def add_warning(self, message: str, suggestion: str = None):
        """Add warning with optional suggestion."""
        self.warnings.append(message)
        if suggestion:
            self.suggestions.append(suggestion)
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'confidence_score': self.confidence_score,
            'suggestions': self.suggestions
        }


class EmailValidator:
    """Email format validator."""
    
    # Enhanced regex for email validation
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Common domain patterns
    COMMON_DOMAINS = [
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'aol.com', 'icloud.com', 'msn.com', 'yahoo.co.uk'
    ]
    
    @classmethod
    def validate(cls, email: str) -> SyntaxValidationResult:
        """Validate email format."""
        result = SyntaxValidationResult()
        
        if not email or not isinstance(email, str):
            result.add_error("Email is empty or not a string")
            return result
            
        email = email.strip().lower()
        
        # Check basic format
        if not cls.EMAIL_PATTERN.match(email):
            result.add_error(
                "Invalid email format",
                "Use format: username@domain.com"
            )
            return result
            
        # Check length
        if len(email) > 254:
            result.add_error(
                "Email too long",
                "Emails should be under 254 characters"
            )
            
        # Check for common issues
        if email.startswith('.') or email.endswith('.'):
            result.add_error(
                "Email cannot start or end with dot",
                "Remove leading/trailing dots"
            )
            
        if '..' in email:
            result.add_error(
                "Email contains consecutive dots",
                "Remove consecutive dots"
            )
            
        # Check domain format
        try:
            local_part, domain = email.split('@')
            
            if len(local_part) > 64:
                result.add_warning(
                    "Username part too long",
                    "Keep username under 64 characters"
                )
                
            if domain not in cls.COMMON_DOMAINS and '.' not in domain:
                result.add_warning(
                    "Domain might be invalid",
                    "Verify domain format"
                )
                
        except ValueError:
            result.add_error("Invalid email structure")
            
        return result


class PhoneValidator:
    """Phone number validator with international support."""
    
    @classmethod
    def validate(cls, phone: str, country_code: str = 'US') -> SyntaxValidationResult:
        """Validate phone number format."""
        result = SyntaxValidationResult()
        
        if not phone or not isinstance(phone, str):
            result.add_error("Phone number is empty or not a string")
            return result
            
        # Clean phone number
        clean_phone = re.sub(r'[^\d+]', '', phone.strip())
        
        if PHONENUMBERS_AVAILABLE:
            try:
                # Parse phone number
                parsed_phone = phonenumbers.parse(clean_phone, country_code)
                
                if not phonenumbers.is_valid_number(parsed_phone):
                    result.add_error(
                        "Invalid phone number format",
                        "Use format: +1234567890 or appropriate local format"
                    )
                    
                if phonenumbers.is_possible_number(parsed_phone):
                    # Number is possible but might not be assigned
                    result.add_warning(
                        "Phone number might not be assigned",
                        "Verify the phone number is active"
                    )
                    
            except NumberParseException:
                # Fallback to simple pattern matching
                if not re.match(r'^\+?[1-9]\d{1,14}$', clean_phone):
                    result.add_error(
                        "Invalid phone number format",
                        "Use international format: +[country_code][number]"
                    )
        else:
            # Fallback validation without phonenumbers library
            if not re.match(r'^\+?[1-9]\d{1,14}$', clean_phone):
                result.add_error(
                    "Invalid phone number format",
                    "Phone numbers should contain only digits and optional + sign, 2-15 digits total",
                    "Use format: +1234567890"
                )
                
            if len(clean_phone) < 7:
                result.add_warning(
                    "Phone number seems too short",
                    "Verify phone number is correct"
                )
                
        return result


class DateValidator:
    """Date format validator with multiple format support."""
    
    DATE_FORMATS = [
        '%Y-%m-%d',     # ISO format
        '%m/%d/%Y',     # US format
        '%d/%m/%Y',     # European format
        '%Y-%m-%d %H:%M:%S',  # ISO with time
        '%m/%d/%Y %H:%M:%S',  # US with time
        '%d/%m/%Y %H:%M:%S',  # European with time
        '%Y-%m-%dT%H:%M:%S',  # ISO 8601
        '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO 8601 UTC
    ]
    
    DATE_RANGE = {
        'min_year': 1900,
        'max_year': 2030
    }
    
    @classmethod
    def validate(cls, date_str: str, formats: List[str] = None) -> SyntaxValidationResult:
        """Validate date format."""
        result = SyntaxValidationResult()
        
        if not date_str or not isinstance(date_str, str):
            result.add_error("Date is empty or not a string")
            return result
            
        if formats is None:
            formats = cls.DATE_FORMATS
            
        parsed_date = None
        used_format = None
        
        # Try each format
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), fmt)
                used_format = fmt
                break
            except ValueError:
                continue
                
        if parsed_date is None:
            result.add_error(
                f"Invalid date format. Expected one of: {', '.join(formats)}",
                f"Try formatting as {formats[0] if formats else 'YYYY-MM-DD'}"
            )
            return result
            
        # Validate date range
        year = parsed_date.year
        if year < cls.DATE_RANGE['min_year']:
            result.add_error(
                f"Date too old (before {cls.DATE_RANGE['min_year']})",
                "Check if date is correct"
            )
        elif year > cls.DATE_RANGE['max_year']:
            result.add_error(
                f"Date too far in future (after {cls.DATE_RANGE['max_year']})",
                "Check if date is correct"
            )
            
        # Check for logical inconsistencies
        if year < 2000 and '20' in date_str:
            result.add_warning(
                "Date might have year format issue",
                "Ensure century is correct"
            )
            
        return result


class CustomPatternValidator:
    """Custom regex pattern validator."""
    
    @classmethod
    def validate(cls, value: str, pattern: str, description: str = "Custom pattern") -> SyntaxValidationResult:
        """Validate value against custom regex pattern."""
        result = SyntaxValidationResult()
        
        if not value or not isinstance(value, str):
            result.add_error(f"{description} is empty or not a string")
            return result
            
        if not re.match(pattern, value):
            result.add_error(
                f"Invalid {description.lower()}",
                f"Value must match pattern: {pattern}"
            )
            
        return result


class SyntaxValidator:
    """Main syntax validation orchestrator."""
    
    def __init__(self):
        self.email_validator = EmailValidator()
        self.phone_validator = PhoneValidator()
        self.date_validator = DateValidator()
        self.custom_validators = {}
        
    def add_custom_validator(self, name: str, validator):
        """Add custom validator."""
        self.custom_validators[name] = validator
        
    def validate_field(self, value: Any, field_type: str, **kwargs) -> SyntaxValidationResult:
        """Validate a single field based on its type."""
        result = SyntaxValidationResult()
        
        if value is None or value == "":
            # Allow empty values but warn
            result.add_warning("Empty value provided")
            return result
            
        # Convert to string for most validations
        str_value = str(value).strip()
        
        if field_type.lower() == 'email':
            result = self.email_validator.validate(str_value)
        elif field_type.lower() == 'phone':
            country_code = kwargs.get('country_code', 'US')
            result = self.phone_validator.validate(str_value, country_code)
        elif field_type.lower() in ['date', 'datetime']:
            formats = kwargs.get('formats')
            result = self.date_validator.validate(str_value, formats)
        elif field_type.lower() in self.custom_validators:
            validator = self.custom_validators[field_type.lower()]
            result = validator.validate(str_value, **kwargs)
        else:
            # Generic string validation
            if not isinstance(value, str):
                result.add_error(f"Expected string, got {type(value).__name__}")
            
        return result
        
    def validate_dataset(self, data: Dict[str, Any], field_types: Dict[str, str]) -> Dict[str, SyntaxValidationResult]:
        """Validate entire dataset."""
        results = {}
        
        for field, value in data.items():
            if field in field_types:
                field_type = field_types[field]
                results[field] = self.validate_field(value, field_type)
            else:
                # No specific type, skip validation
                continue
                
        return results
        
    def get_validation_summary(self, results: Dict[str, SyntaxValidationResult]) -> Dict[str, Any]:
        """Get summary of validation results."""
        total_fields = len(results)
        valid_fields = sum(1 for r in results.values() if r.is_valid)
        total_errors = sum(len(r.errors) for r in results.values())
        total_warnings = sum(len(r.warnings) for r in results.values())
        
        avg_confidence = sum(r.confidence_score for r in results.values()) / total_fields if total_fields > 0 else 1.0
        
        return {
            'total_fields': total_fields,
            'valid_fields': valid_fields,
            'invalid_fields': total_fields - valid_fields,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'average_confidence': avg_confidence,
            'validation_rate': valid_fields / total_fields if total_fields > 0 else 0.0
        }