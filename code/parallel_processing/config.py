#!/usr/bin/env python3
"""
Configuration Management
========================

Configuration settings for the parallel processing system.
Handles environment variables, configuration files, and system settings.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ProcessingConfig:
    """Configuration class for the parallel processing system."""
    
    # System Configuration
    max_workers: int = field(default_factory=lambda: int(os.getenv('MAX_WORKERS', '50')))
    max_queue_size: int = field(default_factory=lambda: int(os.getenv('MAX_QUEUE_SIZE', '10000')))
    worker_timeout: int = field(default_factory=lambda: int(os.getenv('WORKER_TIMEOUT', '300')))
    max_memory_per_worker: int = field(default_factory=lambda: int(os.getenv('MAX_MEMORY_PER_WORKER', '1024')))
    max_error_rate: float = field(default_factory=lambda: float(os.getenv('MAX_ERROR_RATE', '0.1')))
    
    # Redis Configuration
    redis_url: str = field(default_factory=lambda: os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    redis_max_connections: int = field(default_factory=lambda: int(os.getenv('REDIS_MAX_CONNECTIONS', '20')))
    redis_timeout: int = field(default_factory=lambda: int(os.getenv('REDIS_TIMEOUT', '30')))
    
    # Job Processing Configuration
    default_job_timeout: int = field(default_factory=lambda: int(os.getenv('DEFAULT_JOB_TIMEOUT', '3600')))
    max_retries: int = field(default_factory=lambda: int(os.getenv('MAX_RETRIES', '3')))
    retry_delay: int = field(default_factory=lambda: int(os.getenv('RETRY_DELAY', '60')))
    
    # Monitoring Configuration
    health_check_interval: int = field(default_factory=lambda: int(os.getenv('HEALTH_CHECK_INTERVAL', '30')))
    autoscaling_interval: int = field(default_factory=lambda: int(os.getenv('AUTOSCALING_INTERVAL', '60')))
    metrics_retention_hours: int = field(default_factory=lambda: int(os.getenv('METRICS_RETENTION_HOURS', '24')))
    
    # Worker Pool Configuration
    worker_pools: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'ocr': {
            'min_workers': int(os.getenv('OCR_MIN_WORKERS', '2')),
            'max_workers': int(os.getenv('OCR_MAX_WORKERS', '8')),
            'memory_limit': int(os.getenv('OCR_MEMORY_LIMIT', '1024')),
            'cpu_limit': float(os.getenv('OCR_CPU_LIMIT', '0.8')),
            'timeout': int(os.getenv('OCR_TIMEOUT', '300'))
        },
        'nlp': {
            'min_workers': int(os.getenv('NLP_MIN_WORKERS', '1')),
            'max_workers': int(os.getenv('NLP_MAX_WORKERS', '4')),
            'memory_limit': int(os.getenv('NLP_MEMORY_LIMIT', '2048')),
            'cpu_limit': float(os.getenv('NLP_CPU_LIMIT', '0.6')),
            'timeout': int(os.getenv('NLP_TIMEOUT', '180'))
        },
        'validation': {
            'min_workers': int(os.getenv('VALIDATION_MIN_WORKERS', '1')),
            'max_workers': int(os.getenv('VALIDATION_MAX_WORKERS', '6')),
            'memory_limit': int(os.getenv('VALIDATION_MEMORY_LIMIT', '512')),
            'cpu_limit': float(os.getenv('VALIDATION_CPU_LIMIT', '0.4')),
            'timeout': int(os.getenv('VALIDATION_TIMEOUT', '120'))
        },
        'preprocessing': {
            'min_workers': int(os.getenv('PREPROCESSING_MIN_WORKERS', '3')),
            'max_workers': int(os.getenv('PREPROCESSING_MAX_WORKERS', '12')),
            'memory_limit': int(os.getenv('PREPROCESSING_MEMORY_LIMIT', '768')),
            'cpu_limit': float(os.getenv('PREPROCESSING_CPU_LIMIT', '0.5')),
            'timeout': int(os.getenv('PREPROCESSING_TIMEOUT', '200'))
        }
    })
    
    # Database Configuration (Optional)
    database_url: Optional[str] = field(default_factory=lambda: os.getenv('DATABASE_URL'))
    
    # Logging Configuration
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    log_format: str = field(default_factory=lambda: os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log_file: str = field(default_factory=lambda: os.getenv('LOG_FILE', 'parallel_processing.log'))
    
    # Performance Configuration
    batch_size: int = field(default_factory=lambda: int(os.getenv('BATCH_SIZE', '100')))
    chunk_size: int = field(default_factory=lambda: int(os.getenv('CHUNK_SIZE', '1000')))
    compression_enabled: bool = field(default_factory=lambda: os.getenv('COMPRESSION_ENABLED', 'true').lower() == 'true')
    
    # Security Configuration
    encryption_enabled: bool = field(default_factory=lambda: os.getenv('ENCRYPTION_ENABLED', 'false').lower() == 'true')
    api_key_required: bool = field(default_factory=lambda: os.getenv('API_KEY_REQUIRED', 'false').lower() == 'true')
    max_file_size_mb: int = field(default_factory=lambda: int(os.getenv('MAX_FILE_SIZE_MB', '100')))
    
    # Feature Flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        'autoscaling': os.getenv('ENABLE_AUTOSCALING', 'true').lower() == 'true',
        'monitoring': os.getenv('ENABLE_MONITORING', 'true').lower() == 'true',
        'metrics': os.getenv('ENABLE_METRICS', 'true').lower() == 'true',
        'alerts': os.getenv('ENABLE_ALERTS', 'false').lower() == 'true',
        'load_balancing': os.getenv('ENABLE_LOAD_BALANCING', 'true').lower() == 'true',
        'failover': os.getenv('ENABLE_FAILOVER', 'true').lower() == 'true',
        'caching': os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
    })
    
    # Scalability Configuration
    auto_scaling: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': os.getenv('ENABLE_AUTO_SCALING', 'true').lower() == 'true',
        'min_instances': int(os.getenv('MIN_INSTANCES', '1')),
        'max_instances': int(os.getenv('MAX_INSTANCES', '20')),
        'scale_up_threshold': float(os.getenv('SCALE_UP_THRESHOLD', '0.8')),
        'scale_down_threshold': float(os.getenv('SCALE_DOWN_THRESHOLD', '0.3')),
        'scale_up_delay': int(os.getenv('SCALE_UP_DELAY', '60')),
        'scale_down_delay': int(os.getenv('SCALE_DOWN_DELAY', '300'))
    })
    
    # Backup and Recovery Configuration
    backup: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': os.getenv('ENABLE_BACKUP', 'false').lower() == 'true',
        'interval_hours': int(os.getenv('BACKUP_INTERVAL_HOURS', '6')),
        'retention_days': int(os.getenv('BACKUP_RETENTION_DAYS', '7')),
        'location': os.getenv('BACKUP_LOCATION', './backups')
    })
    
    @classmethod
    def load_from_file(cls, config_path: Optional[str]) -> 'ProcessingConfig':
        """Load configuration from file."""
        config = cls()
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    if config_path.endswith('.json'):
                        file_config = json.load(f)
                    else:
                        # Assume YAML if .yml or .yaml
                        import yaml
                        file_config = yaml.safe_load(f)
                
                # Update config values from file
                for key, value in file_config.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                
                logger.info(f"Configuration loaded from {config_path}")
                
            except Exception as e:
                logger.warning(f"Failed to load configuration from {config_path}: {e}")
        
        return config
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to file."""
        try:
            config_dict = {}
            for key, value in self.__dict__.items():
                # Skip complex objects
                if isinstance(value, (str, int, float, bool, list, dict)):
                    config_dict[key] = value
            
            with open(config_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {config_path}: {e}")
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate worker configuration
        if self.max_workers <= 0:
            errors.append("max_workers must be positive")
        
        if self.max_queue_size <= 0:
            errors.append("max_queue_size must be positive")
        
        if self.worker_timeout <= 0:
            errors.append("worker_timeout must be positive")
        
        # Validate Redis URL
        if not self.redis_url or not self.redis_url.startswith(('redis://', 'rediss://')):
            errors.append("redis_url must be a valid Redis URL")
        
        # Validate worker pool configurations
        for pool_name, pool_config in self.worker_pools.items():
            if pool_config['min_workers'] < 0:
                errors.append(f"Worker pool {pool_name}: min_workers cannot be negative")
            
            if pool_config['max_workers'] < pool_config['min_workers']:
                errors.append(f"Worker pool {pool_name}: max_workers must be >= min_workers")
            
            if pool_config['memory_limit'] <= 0:
                errors.append(f"Worker pool {pool_name}: memory_limit must be positive")
            
            if not 0 < pool_config['cpu_limit'] <= 1:
                errors.append(f"Worker pool {pool_name}: cpu_limit must be between 0 and 1")
        
        # Validate auto scaling configuration
        if self.auto_scaling['min_instances'] > self.auto_scaling['max_instances']:
            errors.append("auto_scaling.min_instances cannot be greater than max_instances")
        
        if self.auto_scaling['scale_up_threshold'] <= self.auto_scaling['scale_down_threshold']:
            errors.append("auto_scaling.scale_up_threshold must be greater than scale_down_threshold")
        
        # Validate performance settings
        if self.batch_size <= 0:
            errors.append("batch_size must be positive")
        
        if self.chunk_size <= 0:
            errors.append("chunk_size must be positive")
        
        if self.max_file_size_mb <= 0:
            errors.append("max_file_size_mb must be positive")
        
        return errors
    
    def get_worker_config(self, worker_type: str) -> Dict[str, Any]:
        """Get configuration for specific worker type."""
        return self.worker_pools.get(worker_type, {
            'min_workers': 1,
            'max_workers': 4,
            'memory_limit': 1024,
            'cpu_limit': 0.5,
            'timeout': 300
        })
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        return self.features.get(feature, False)
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration."""
        return {
            'url': self.redis_url,
            'max_connections': self.redis_max_connections,
            'timeout': self.redis_timeout
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            'level': self.log_level,
            'format': self.log_format,
            'file': self.log_file
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }


# Environment-specific configurations

class DevelopmentConfig(ProcessingConfig):
    """Development environment configuration."""
    
    def __init__(self):
        super().__init__()
        self.log_level = 'DEBUG'
        self.max_workers = 10
        self.worker_pools['ocr']['max_workers'] = 2
        self.worker_pools['nlp']['max_workers'] = 2
        self.features['monitoring'] = True
        self.features['metrics'] = True


class ProductionConfig(ProcessingConfig):
    """Production environment configuration."""
    
    def __init__(self):
        super().__init__()
        self.max_workers = 100
        self.worker_pools['ocr']['max_workers'] = 20
        self.worker_pools['nlp']['max_workers'] = 15
        self.features['alerts'] = True
        self.features['backup'] = True
        self.security['encryption_enabled'] = True


class TestingConfig(ProcessingConfig):
    """Testing environment configuration."""
    
    def __init__(self):
        super().__init__()
        self.log_level = 'WARNING'
        self.max_workers = 4
        self.redis_url = 'redis://localhost:6379/1'  # Different DB for testing
        self.worker_pools['ocr']['max_workers'] = 1
        self.worker_pools['nlp']['max_workers'] = 1


def get_config(environment: Optional[str] = None) -> ProcessingConfig:
    """Get configuration based on environment."""
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'development')
    
    environment = environment.lower()
    
    if environment == 'production':
        return ProductionConfig()
    elif environment == 'testing':
        return TestingConfig()
    else:
        return DevelopmentConfig()


def create_default_config_file(file_path: str) -> None:
    """Create a default configuration file."""
    default_config = DevelopmentConfig()
    default_config.save_to_file(file_path)
    logger.info(f"Default configuration file created at {file_path}")


# Configuration utility functions

def validate_environment() -> List[str]:
    """Validate environment variables and return warnings."""
    warnings = []
    
    # Check required environment variables
    required_vars = ['REDIS_URL']
    for var in required_vars:
        if not os.getenv(var):
            warnings.append(f"Required environment variable {var} is not set")
    
    # Check Redis connectivity
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    if 'localhost' in redis_url:
        warnings.append("Using localhost Redis - ensure Redis is running")
    
    # Check worker limits
    max_workers = int(os.getenv('MAX_WORKERS', '50'))
    if max_workers > 200:
        warnings.append(f"High worker count ({max_workers}) may cause performance issues")
    
    return warnings


def get_system_info() -> Dict[str, Any]:
    """Get system information for configuration."""
    import platform
    import psutil
    
    return {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_total_gb': psutil.virtual_memory().total / (1024**3),
        'disk_free_gb': psutil.disk_usage('/').free / (1024**3),
        'hostname': platform.node()
    }


if __name__ == "__main__":
    # Example usage
    config = get_config()
    errors = config.validate()
    
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid")
        print(f"Max workers: {config.max_workers}")
        print(f"Redis URL: {config.redis_url}")
        print(f"Features enabled: {config.features}")