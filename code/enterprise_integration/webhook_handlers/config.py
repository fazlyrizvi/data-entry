"""
Configuration Management

Centralized configuration for webhook handlers with environment variable support.
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = "sqlite:///webhooks.db"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    echo: bool = False


@dataclass
class CacheConfig:
    """Cache configuration"""
    type: str = "simple"  # simple, redis, memcached
    url: Optional[str] = None
    default_timeout: int = 300
    key_prefix: str = "webhook:"


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    max_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_json: bool = False


@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = "change-me-in-production"
    jwt_secret: str = "change-me-in-production"
    jwt_expiration: int = 3600
    signature_timeout: int = 300
    max_request_size: int = 1024 * 1024  # 1MB
    trusted_proxies: list = field(default_factory=list)


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enabled: bool = True
    prometheus_port: int = 9090
    health_check_interval: int = 30
    metrics_retention: int = 86400  # 24 hours
    alert_webhook_url: Optional[str] = None
    alert_threshold: float = 0.95  # 95% error rate


@dataclass
class AppConfig:
    """Main application configuration"""
    name: str = "WebhookHandler"
    version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 5000
    workers: int = 4
    timeout: int = 30
    keep_alive: int = 2
    
    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)


class ConfigManager:
    """Configuration manager with environment variable support"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_file: Path to JSON configuration file
        """
        self.config_file = config_file
        self.config = AppConfig()
        
        if config_file and Path(config_file).exists():
            self.load_from_file(config_file)
        
        self.load_from_environment()
    
    def load_from_file(self, config_file: str) -> None:
        """
        Load configuration from JSON file
        
        Args:
            config_file: Path to configuration file
        """
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            self._merge_config(config_data)
            print(f"Configuration loaded from {config_file}")
        except Exception as e:
            print(f"Warning: Failed to load config from {config_file}: {e}")
    
    def load_from_environment(self) -> None:
        """Load configuration from environment variables"""
        # App settings
        if os.getenv('APP_NAME'):
            self.config.name = os.getenv('APP_NAME')
        if os.getenv('APP_DEBUG'):
            self.config.debug = os.getenv('APP_DEBUG').lower() in ('true', '1', 'yes', 'on')
        if os.getenv('APP_HOST'):
            self.config.host = os.getenv('APP_HOST')
        if os.getenv('APP_PORT'):
            self.config.port = int(os.getenv('APP_PORT'))
        if os.getenv('APP_WORKERS'):
            self.config.workers = int(os.getenv('APP_WORKERS'))
        
        # Database settings
        if os.getenv('DATABASE_URL'):
            self.config.database.url = os.getenv('DATABASE_URL')
        if os.getenv('DATABASE_POOL_SIZE'):
            self.config.database.pool_size = int(os.getenv('DATABASE_POOL_SIZE'))
        if os.getenv('DATABASE_ECHO'):
            self.config.database.echo = os.getenv('DATABASE_ECHO').lower() in ('true', '1', 'yes', 'on')
        
        # Cache settings
        if os.getenv('CACHE_TYPE'):
            self.config.cache.type = os.getenv('CACHE_TYPE')
        if os.getenv('CACHE_URL'):
            self.config.cache.url = os.getenv('CACHE_URL')
        
        # Security settings
        if os.getenv('SECRET_KEY'):
            self.config.security.secret_key = os.getenv('SECRET_KEY')
        if os.getenv('JWT_SECRET'):
            self.config.security.jwt_secret = os.getenv('JWT_SECRET')
        if os.getenv('MAX_REQUEST_SIZE'):
            self.config.security.max_request_size = int(os.getenv('MAX_REQUEST_SIZE'))
        
        # Monitoring settings
        if os.getenv('MONITORING_ENABLED'):
            self.config.monitoring.enabled = os.getenv('MONITORING_ENABLED').lower() in ('true', '1', 'yes', 'on')
        if os.getenv('PROMETHEUS_PORT'):
            self.config.monitoring.prometheus_port = int(os.getenv('PROMETHEUS_PORT'))
    
    def _merge_config(self, config_data: Dict[str, Any]) -> None:
        """
        Merge configuration data into existing config
        
        Args:
            config_data: Configuration dictionary
        """
        for section, values in config_data.items():
            if hasattr(self.config, section):
                section_obj = getattr(self.config, section)
                if isinstance(section_obj, (DatabaseConfig, CacheConfig, LoggingConfig, SecurityConfig, MonitoringConfig)):
                    for key, value in values.items():
                        if hasattr(section_obj, key):
                            setattr(section_obj, key, value)
                else:
                    setattr(self.config, section, values)
    
    def save_to_file(self, config_file: str) -> None:
        """
        Save current configuration to JSON file
        
        Args:
            config_file: Path to save configuration
        """
        config_dict = asdict(self.config)
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            print(f"Configuration saved to {config_file}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., 'database.url', 'security.secret_key')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        current = self.config
        
        for k in keys:
            if hasattr(current, k):
                current = getattr(current, k)
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation
        
        Args:
            key: Configuration key
            value: Value to set
        """
        keys = key.split('.')
        current = self.config
        
        for k in keys[:-1]:
            if hasattr(current, k):
                current = getattr(current, k)
            else:
                raise KeyError(f"Configuration path not found: {key}")
        
        if hasattr(current, keys[-1]):
            setattr(current, keys[-1], value)
        else:
            raise KeyError(f"Configuration key not found: {key}")
    
    def validate(self) -> Dict[str, list]:
        """
        Validate configuration
        
        Returns:
            Dictionary with validation errors (empty if valid)
        """
        errors = {
            'critical': [],
            'warnings': []
        }
        
        # Critical validations
        if self.config.security.secret_key == "change-me-in-production":
            errors['critical'].append("SECRET_KEY must be changed from default")
        
        if self.config.security.jwt_secret == "change-me-in-production":
            errors['critical'].append("JWT_SECRET must be changed from default")
        
        if self.config.port < 1 or self.config.port > 65535:
            errors['critical'].append(f"Invalid port number: {self.config.port}")
        
        # Warning validations
        if self.config.debug:
            errors['warnings'].append("Debug mode enabled - not suitable for production")
        
        if not self.config.monitoring.enabled:
            errors['warnings'].append("Monitoring disabled - recommended to enable")
        
        if self.config.database.url.startswith('sqlite') and self.config.database.echo:
            errors['warnings'].append("Database echo enabled - may log sensitive data")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary
        
        Returns:
            Configuration dictionary
        """
        return asdict(self.config)


# Environment-specific configurations
def get_development_config() -> AppConfig:
    """Get development configuration"""
    config = AppConfig()
    config.debug = True
    config.logging.level = "DEBUG"
    config.database.echo = True
    config.cache.type = "simple"
    return config


def get_production_config() -> AppConfig:
    """Get production configuration"""
    config = AppConfig()
    config.debug = False
    config.logging.level = "INFO"
    config.database.echo = False
    config.cache.type = "redis"
    config.workers = max(4, os.cpu_count() * 2 + 1)
    
    # Security hardening
    config.security.secret_key = os.getenv('SECRET_KEY', config.security.secret_key)
    config.security.jwt_secret = os.getenv('JWT_SECRET', config.security.jwt_secret)
    config.security.max_request_size = 5 * 1024 * 1024  # 5MB
    
    return config


def get_testing_config() -> AppConfig:
    """Get testing configuration"""
    config = AppConfig()
    config.debug = False
    config.logging.level = "WARNING"
    config.database.url = "sqlite:///:memory:"
    config.cache.type = "simple"
    config.monitoring.enabled = False
    return config


# Default configuration instances
default_config = ConfigManager()
development_config = get_development_config()
production_config = get_production_config()
testing_config = get_testing_config()


if __name__ == '__main__':
    # Example usage
    config_manager = ConfigManager()
    
    # Load from environment
    config_manager.load_from_environment()
    
    # Validate configuration
    validation_errors = config_manager.validate()
    
    if validation_errors['critical']:
        print("❌ Critical configuration errors:")
        for error in validation_errors['critical']:
            print(f"  - {error}")
    
    if validation_errors['warnings']:
        print("⚠️  Configuration warnings:")
        for warning in validation_errors['warnings']:
            print(f"  - {warning}")
    
    if not validation_errors['critical'] and not validation_errors['warnings']:
        print("✅ Configuration is valid")
    
    # Show configuration
    print("\nCurrent Configuration:")
    print(json.dumps(config_manager.to_dict(), indent=2, default=str))
