"""
CRM Integration Utilities

Common utilities for CRM integration including:
- Data validation
- Field mapping helpers
- Error handling
- Logging configuration
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, date
import json


class DataValidator:
    """Data validation utilities for CRM integration"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str, region: str = 'US') -> bool:
        """Validate phone number format"""
        # Simple validation - in production, use a library like phonenumbers
        pattern = r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Validate required fields are present and not None"""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                missing_fields.append(field)
        return missing_fields
    
    @staticmethod
    def validate_data_type(data: Dict[str, Any], field_types: Dict[str, type]) -> List[str]:
        """Validate field data types"""
        type_errors = []
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    type_errors.append(
                        f"Field '{field}' should be {expected_type.__name__}, "
                        f"got {type(data[field]).__name__}"
                    )
        return type_errors
    
    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """Sanitize string value"""
        if not isinstance(value, str):
            value = str(value)
        
        # Remove or replace problematic characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', value)
        
        # Trim to max length if specified
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_date_format(date_str: str, formats: List[str] = None) -> bool:
        """Validate date string format"""
        if formats is None:
            formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S']
        
        for fmt in formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        return False


class FieldMappingHelper:
    """Helper for field mapping operations"""
    
    # Common field mapping dictionaries for different CRMs
    SALESFORCE_MAPPINGS = {
        # Contacts
        'first_name': 'FirstName',
        'last_name': 'LastName',
        'email': 'Email',
        'phone': 'Phone',
        'company': 'Account.Name',
        
        # Accounts
        'account_name': 'Name',
        'website': 'Website',
        'industry': 'Industry',
        'phone_number': 'Phone',
        
        # Leads
        'company_name': 'Company',
        'lead_status': 'Status',
        'lead_source': 'LeadSource',
        'title': 'Title'
    }
    
    HUBSPOT_MAPPINGS = {
        # Contacts
        'firstname': 'firstname',
        'lastname': 'lastname',
        'email': 'email',
        'phone': 'phone',
        'company': 'company',
        
        # Companies
        'name': 'name',
        'domain': 'domain',
        'industry': 'industry',
        'phone_number': 'phone_number',
        
        # Deals
        'deal_name': 'dealname',
        'amount': 'amount',
        'stage': 'dealstage',
        'close_date': 'closedate'
    }
    
    DYNAMICS365_MAPPINGS = {
        # Contacts
        'first_name': 'firstname',
        'last_name': 'lastname',
        'email': 'emailaddress1',
        'phone': 'telephone1',
        'company': 'parentcustomerid.name',
        
        # Accounts
        'account_name': 'name',
        'website': 'websiteurl',
        'industry': 'industrycode',
        'phone_number': 'telephone1'
    }
    
    @classmethod
    def get_crm_mappings(cls, crm_type: str) -> Dict[str, str]:
        """Get standard field mappings for a CRM type"""
        mappings_map = {
            'salesforce': cls.SALESFORCE_MAPPINGS,
            'hubspot': cls.HUBSPOT_MAPPINGS,
            'dynamics365': cls.DYNAMICS365_MAPPINGS
        }
        return mappings_map.get(crm_type.lower(), {})
    
    @classmethod
    def create_mapping_function(cls, mappings: Dict[str, str]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        """Create a mapping function based on field mappings"""
        def map_fields(data: Dict[str, Any]) -> Dict[str, Any]:
            mapped_data = {}
            for internal_field, external_field in mappings.items():
                if internal_field in data:
                    mapped_data[external_field] = data[internal_field]
            
            # Add unmapped fields
            for field, value in data.items():
                if field not in mappings:
                    mapped_data[field] = value
            
            return mapped_data
        
        return map_fields
    
    @classmethod
    def reverse_mapping(cls, mappings: Dict[str, str]) -> Dict[str, str]:
        """Reverse field mappings"""
        return {v: k for k, v in mappings.items()}


class ErrorHandler:
    """Error handling utilities for CRM integration"""
    
    @staticmethod
    def handle_api_error(response_status: int, response_text: str, context: str = "") -> Exception:
        """Create appropriate exception based on API error response"""
        error_message = f"API Error ({response_status}): {response_text}"
        if context:
            error_message = f"{context}: {error_message}"
        
        if response_status == 400:
            return ValueError(error_message)
        elif response_status == 401:
            return PermissionError(error_message)
        elif response_status == 403:
            return PermissionError(error_message)
        elif response_status == 404:
            return FileNotFoundError(error_message)
        elif response_status == 429:
            return Exception(f"Rate limit exceeded: {error_message}")
        elif response_status >= 500:
            return ConnectionError(error_message)
        else:
            return Exception(error_message)
    
    @staticmethod
    def retry_on_failure(max_retries: int = 3, delay: float = 1.0, 
                        backoff_factor: float = 2.0):
        """Decorator for retrying failed operations"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt == max_retries:
                            break
                        wait_time = delay * (backoff_factor ** attempt)
                        logging.warning(f"Attempt {attempt + 1} failed. Retrying in {wait_time}s: {str(e)}")
                        await asyncio.sleep(wait_time)
                
                raise last_exception
            return wrapper
        return decorator
    
    @staticmethod
    def safe_get_nested(data: Dict[str, Any], path: str, default: Any = None) -> Any:
        """Safely get nested dictionary value using dot notation"""
        try:
            keys = path.split('.')
            result = data
            for key in keys:
                result = result[key]
            return result
        except (KeyError, TypeError):
            return default
    
    @staticmethod
    def validate_response_structure(response: Dict[str, Any], 
                                  required_fields: List[str]) -> bool:
        """Validate that response contains required fields"""
        for field in required_fields:
            if field not in response:
                return False
        return True


class LoggingConfig:
    """Logging configuration for CRM integration"""
    
    @staticmethod
    def setup_logging(level: str = 'INFO', log_file: Optional[str] = None,
                     format_string: Optional[str] = None):
        """Setup logging configuration"""
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        handlers = [logging.StreamHandler()]
        
        if log_file:
            handlers.append(logging.FileHandler(log_file))
        
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format=format_string,
            handlers=handlers,
            force=True
        )
        
        # Set specific logger levels
        logging.getLogger('aiohttp').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)


class ConversionHelper:
    """Helper utilities for data conversion"""
    
    @staticmethod
    def to_string(value: Any) -> str:
        """Convert value to string"""
        if value is None:
            return ''
        return str(value)
    
    @staticmethod
    def to_number(value: Any, default: Optional[float] = None) -> Optional[float]:
        """Convert value to number"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            return float(str(value))
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def to_boolean(value: Any, default: Optional[bool] = None) -> Optional[bool]:
        """Convert value to boolean"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        if isinstance(value, (int, float)):
            return bool(value)
        return default
    
    @staticmethod
    def to_date(value: Any, formats: List[str] = None) -> Optional[date]:
        """Convert value to date"""
        if formats is None:
            formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']
        
        if isinstance(value, date):
            return value
        
        if isinstance(value, str):
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        
        return None
    
    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Normalize phone number format"""
        if not phone:
            return ''
        
        # Remove all non-digits
        digits_only = re.sub(r'[^\d]', '', phone)
        
        # Add country code if missing (US assumed)
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f"+{digits_only}"
        else:
            return f"+{digits_only}"
    
    @staticmethod
    def normalize_email(email: str) -> str:
        """Normalize email address"""
        if not email:
            return ''
        
        email = email.strip().lower()
        
        # Validate email format
        if DataValidator.validate_email(email):
            return email
        
        return email
    
    @staticmethod
    def transform_data(data: Dict[str, Any], transformations: Dict[str, Callable]) -> Dict[str, Any]:
        """Apply transformations to data"""
        result = data.copy()
        
        for field, transform_func in transformations.items():
            if field in result:
                try:
                    result[field] = transform_func(result[field])
                except Exception as e:
                    logging.warning(f"Transformation failed for field '{field}': {str(e)}")
        
        return result


class ConfigValidator:
    """Configuration validation utilities"""
    
    @staticmethod
    def validate_config(config: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Validate configuration has required fields"""
        missing_fields = []
        for field in required_fields:
            if field not in config:
                missing_fields.append(field)
        return missing_fields
    
    @staticmethod
    def validate_salesforce_config(config: Dict[str, Any]) -> List[str]:
        """Validate Salesforce-specific configuration"""
        errors = []
        
        # Check required fields
        required = ['client_id', 'client_secret', 'instance_url']
        errors.extend(ConfigValidator.validate_config(config, required))
        
        # Check authentication method
        auth_method = config.get('auth_method', 'password')
        if auth_method == 'password':
            if 'username' not in config:
                errors.append("username is required for password authentication")
            if 'password' not in config:
                errors.append("password is required for password authentication")
        elif auth_method == 'oauth':
            # OAuth-specific validation would go here
            pass
        
        return errors
    
    @staticmethod
    def validate_hubspot_config(config: Dict[str, Any]) -> List[str]:
        """Validate HubSpot-specific configuration"""
        errors = []
        
        # Check required fields
        has_tokens = 'access_token' in config or 'refresh_token' in config
        has_credentials = 'client_id' in config and 'client_secret' in config
        
        if not (has_tokens or has_credentials):
            errors.append("Either access_token/refresh_token or client_id/client_secret must be provided")
        
        return errors
    
    @staticmethod
    def validate_dynamics_config(config: Dict[str, Any]) -> List[str]:
        """Validate Dynamics 365-specific configuration"""
        errors = []
        
        # Check required fields
        required = ['tenant_id', 'client_id', 'client_secret', 'resource_url']
        errors.extend(ConfigValidator.validate_config(config, required))
        
        return errors


# Initialize logging with default configuration
LoggingConfig.setup_logging()
