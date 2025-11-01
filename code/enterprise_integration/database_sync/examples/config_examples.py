"""
Configuration Examples for Database Synchronization

This file provides example configurations for various database synchronization scenarios.
"""

import os
from datetime import timedelta
from typing import Dict, Any

# Database configurations
POSTGRESQL_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "production_db",
    "username": "sync_user",
    "password": os.getenv("POSTGRESQL_PASSWORD", "secure_password"),
    "ssl_mode": "prefer",
    "timeout": 30,
    "max_connections": 20,
    "application_name": "database_sync_service",
    "server_settings": {
        "wal_level": "logical",
        "max_wal_senders": "10",
        "wal_keep_segments": "32",
        "max_replication_slots": "10"
    }
}

MONGODB_CONFIG = {
    "host": "localhost",
    "port": 27017,
    "database": "production_db",
    "username": "sync_user",
    "password": os.getenv("MONGODB_PASSWORD", "secure_password"),
    "auth_source": "admin",
    "ssl_mode": None,
    "timeout": 30,
    "max_connections": 50,
    "min_pool_size": 5,
    "retry_writes": True,
    "retry_reads": True,
    "read_preference": "secondaryPreferred",
    "write_concern": "majority",
    "read_concern": "local"
}

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "database": "production_db",
    "username": "sync_user",
    "password": os.getenv("MYSQL_PASSWORD", "secure_password"),
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
    "autocommit": False,
    "timeout": 30,
    "max_connections": 20,
    "connect_timeout": 10,
    "read_timeout": 30,
    "write_timeout": 30
}

# CDC Configuration
CDC_CONFIGS = {
    "postgresql_cdc": {
        "name": "PostgreSQL CDC",
        "cdc_type": "LOGICAL_DECODING",
        "tables": ["users", "orders", "products", "order_items"],
        "exclude_tables": ["audit_logs", "temp_tables"],
        "batch_size": 100,
        "poll_interval": 1.0,
        "max_lag_seconds": 60,
        "buffer_size": 1000,
        "retry_attempts": 3,
        "retry_delay": 5.0,
        "dead_letter_queue_enabled": True,
        "heartbeat_interval": 30,
        "metrics_enabled": True
    },
    
    "mongodb_cdc": {
        "name": "MongoDB CDC",
        "cdc_type": "CHANGE_STREAMS",
        "tables": ["users", "orders", "products"],
        "batch_size": 50,
        "poll_interval": 0.5,
        "max_lag_seconds": 30,
        "buffer_size": 500,
        "retry_attempts": 5,
        "retry_delay": 2.0,
        "dead_letter_queue_enabled": True
    },
    
    "mysql_cdc": {
        "name": "MySQL CDC",
        "cdc_type": "BINLOG_REPLICATION",
        "tables": ["users", "orders", "products"],
        "batch_size": 200,
        "poll_interval": 2.0,
        "max_lag_seconds": 120,
        "buffer_size": 2000,
        "retry_attempts": 3,
        "retry_delay": 10.0,
        "dead_letter_queue_enabled": True,
        "binlog_format": "ROW",
        "binlog_row_image": "FULL"
    }
}

# Synchronization Configuration
SYNC_CONFIGS = {
    "realtime_postgresql_mongodb": {
        "name": "Real-time PostgreSQL to MongoDB Sync",
        "sync_mode": "REAL_TIME",
        "sync_direction": "SOURCE_TO_TARGET",
        "source_database_id": "postgresql_source",
        "target_database_id": "mongodb_target",
        "sync_interval": 60,
        "batch_size": 100,
        "max_concurrent_operations": 10,
        "conflict_resolution_strategy": "TIMESTAMP_BASED",
        "conflict_threshold": 20,
        "max_retries": 3,
        "retry_delay": 1.0,
        "enable_dead_letter_queue": True,
        "connection_pool_size": 15,
        "operation_timeout": 30,
        "heartbeat_interval": 5,
        "include_tables": ["users", "orders", "products"],
        "exclude_tables": ["audit_logs", "system_logs"]
    },
    
    "batch_mysql_postgresql": {
        "name": "Batch MySQL to PostgreSQL Sync",
        "sync_mode": "BATCH",
        "sync_direction": "SOURCE_TO_TARGET",
        "source_database_id": "mysql_source",
        "target_database_id": "postgresql_target",
        "sync_interval": 3600,  # Every hour
        "batch_size": 1000,
        "max_concurrent_operations": 5,
        "conflict_resolution_strategy": "SOURCE_WINS",
        "conflict_threshold": 100,
        "max_retries": 5,
        "retry_delay": 5.0,
        "enable_dead_letter_queue": True,
        "connection_pool_size": 10,
        "operation_timeout": 60,
        "include_tables": ["customers", "orders", "products"],
        "exclude_tables": ["temp_data", "test_data"]
    },
    
    "bidirectional_inventory": {
        "name": "Bidirectional Inventory Sync",
        "sync_mode": "REAL_TIME",
        "sync_direction": "BIDIRECTIONAL",
        "source_database_id": "inventory_mysql",
        "target_database_id": "warehouse_postgresql",
        "sync_interval": 30,
        "batch_size": 50,
        "max_concurrent_operations": 8,
        "conflict_resolution_strategy": "TIMESTAMP_BASED",
        "conflict_threshold": 10,
        "max_retries": 3,
        "retry_delay": 2.0,
        "enable_dead_letter_queue": True,
        "connection_pool_size": 12,
        "operation_timeout": 30,
        "include_tables": ["products", "categories", "inventory", "suppliers"],
        "exclude_tables": ["audit_logs", "temp_tables"]
    }
}

# Transformation Pipeline Configurations
TRANSFORMATION_CONFIGS = {
    "user_data_sync": {
        "pipeline_id": "user_data_sync",
        "rules": [
            {
                "name": "Map user fields",
                "type": "FIELD_MAPPING",
                "priority": 1,
                "config": {
                    "field_mappings": {
                        "user_id": "_id",
                        "first_name": "firstName",
                        "last_name": "lastName",
                        "email_address": "email",
                        "created_at": "createdAt",
                        "updated_at": "updatedAt"
                    },
                    "default_values": {
                        "status": "active",
                        "source": "postgresql"
                    }
                }
            },
            {
                "name": "Convert data types",
                "type": "TYPE_CONVERSION",
                "priority": 2,
                "config": {
                    "type_conversions": {
                        "age": "integer",
                        "salary": "decimal",
                        "is_active": "boolean",
                        "created_at": "datetime",
                        "updated_at": "datetime"
                    }
                }
            },
            {
                "name": "Enrich user data",
                "type": "DATA_ENRICHMENT",
                "priority": 3,
                "config": {
                    "enrichment": {
                        "add_timestamps": True,
                        "calculated_fields": {
                            "fullName": {
                                "type": "concatenate",
                                "fields": ["first_name", "last_name"],
                                "separator": " "
                            },
                            "accountAge": {
                                "type": "count",
                                "fields": ["created_at"]
                            }
                        }
                    }
                }
            },
            {
                "name": "Validate user data",
                "type": "VALIDATION",
                "priority": 4,
                "config": {
                    "validation_rules": {
                        "required_fields": ["user_id", "email_address"],
                        "format_rules": {
                            "email_address": r"^[^@]+@[^@]+\.[^@]+$"
                        },
                        "range_rules": {
                            "age": {"min": 0, "max": 150}
                        }
                    }
                }
            }
        ]
    },
    
    "product_data_sync": {
        "pipeline_id": "product_data_sync",
        "rules": [
            {
                "name": "Map product fields",
                "type": "FIELD_MAPPING",
                "priority": 1,
                "config": {
                    "field_mappings": {
                        "product_id": "id",
                        "product_name": "name",
                        "description": "description",
                        "price": "price",
                        "category_id": "categoryId",
                        "created_at": "createdAt",
                        "updated_at": "updatedAt"
                    }
                }
            },
            {
                "name": "Price validation and formatting",
                "type": "VALUE_MODIFICATION",
                "priority": 2,
                "config": {
                    "modifications": {
                        "price": {
                            "type": "numeric_operations",
                            "operations": ["round"]
                        }
                    }
                }
            },
            {
                "name": "Product status enrichment",
                "type": "DATA_ENRICHMENT",
                "priority": 3,
                "config": {
                    "enrichment": {
                        "lookup_fields": {
                            "category_name": {
                                "source": "categories",
                                "field": "name",
                                "key_field": "category_id"
                            }
                        }
                    }
                }
            }
        ]
    }
}

# Monitoring and Alerting Configuration
MONITORING_CONFIG = {
    "retention_period_days": 7,
    "alerts": [
        {
            "name": "High Error Rate",
            "description": "Error rate exceeds threshold",
            "severity": "ERROR",
            "metric_name": "sync.errors_per_minute",
            "condition": ">",
            "threshold": 10.0,
            "duration_minutes": 5,
            "enabled": True
        },
        {
            "name": "CDC Lag Detected",
            "description": "Change data capture lag is too high",
            "severity": "WARNING",
            "metric_name": "cdc.lag_seconds",
            "condition": ">",
            "threshold": 60.0,
            "duration_minutes": 2,
            "enabled": True
        },
        {
            "name": "Database Connection Issues",
            "description": "Database connection problems detected",
            "severity": "CRITICAL",
            "metric_name": "database.connection_errors",
            "condition": ">",
            "threshold": 0.0,
            "duration_minutes": 0,
            "enabled": True
        },
        {
            "name": "High Sync Conflicts",
            "description": "Synchronization conflicts above threshold",
            "severity": "WARNING",
            "metric_name": "sync.conflicts_per_hour",
            "condition": ">",
            "threshold": 50.0,
            "duration_minutes": 10,
            "enabled": True
        },
        {
            "name": "Low Throughput",
            "description": "Synchronization throughput is low",
            "severity": "WARNING",
            "metric_name": "sync.throughput_events_per_second",
            "condition": "<",
            "threshold": 5.0,
            "duration_minutes": 15,
            "enabled": True
        }
    ],
    "alert_handlers": [
        {
            "type": "logging",
            "config": {}
        },
        {
            "type": "webhook",
            "config": {
                "webhook_url": os.getenv("ALERT_WEBHOOK_URL", "https://alerts.company.com/webhook"),
                "headers": {
                    "Authorization": f"Bearer {os.getenv('ALERT_WEBHOOK_TOKEN', 'token')}"
                }
            }
        }
    ]
}

# Error Recovery Configuration
ERROR_RECOVERY_CONFIG = {
    "max_retries": 3,
    "retry_delay_base": 1.0,
    "retry_delay_max": 300.0,
    "dead_letter_queue_enabled": True,
    "max_errors_per_hour": 1000,
    "custom_handlers": {
        "CONNECTION_ERROR": {
            "strategy": "RETRY",
            "max_attempts": 5,
            "backoff_multiplier": 2.0
        },
        "CONSTRAINT_VIOLATION": {
            "strategy": "SKIP",
            "log_level": "WARNING"
        },
        "SCHEMA_MISMATCH": {
            "strategy": "MANUAL_INTERVENTION",
            "notification": True
        },
        "TIMEOUT_ERROR": {
            "strategy": "RETRY",
            "max_attempts": 3,
            "backoff_multiplier": 1.5
        }
    }
}

# Transaction Management Configuration
TRANSACTION_CONFIG = {
    "max_transactions": 1000,
    "cleanup_interval": 3600,
    "default_timeout": 300,
    "two_phase_commit": True,
    "compensation_actions": {
        "INSERT": "DELETE",
        "UPDATE": "UPDATE",  # Would need original values
        "DELETE": "INSERT"   # Would need backup data
    }
}

# Connection Pool Configuration
CONNECTION_POOL_CONFIGS = {
    "postgresql_pool": {
        "min_connections": 5,
        "max_connections": 20,
        "max_idle_time_minutes": 30,
        "connection_timeout": 30,
        "health_check_interval": 300
    },
    "mongodb_pool": {
        "min_connections": 5,
        "max_connections": 50,
        "max_idle_time_minutes": 30,
        "connection_timeout": 30,
        "health_check_interval": 300
    },
    "mysql_pool": {
        "min_connections": 5,
        "max_connections": 20,
        "max_idle_time_minutes": 30,
        "connection_timeout": 30,
        "health_check_interval": 300
    }
}

# Security Configuration
SECURITY_CONFIG = {
    "encryption": {
        "enabled": True,
        "algorithm": "AES-256-GCM",
        "key_rotation_days": 90,
        "encrypted_fields": ["password", "ssn", "credit_card", "secret_token"]
    },
    "authentication": {
        "method": "oauth2",
        "token_refresh_minutes": 30,
        "session_timeout_minutes": 60
    },
    "audit_logging": {
        "enabled": True,
        "log_level": "INFO",
        "sensitive_operations": ["CREATE", "UPDATE", "DELETE"],
        "retention_days": 365
    }
}

# Performance Optimization Configuration
PERFORMANCE_CONFIG = {
    "caching": {
        "enabled": True,
        "cache_ttl_minutes": 10,
        "max_cache_size": 1000,
        "cache_strategies": ["schema", "reference_data", "query_results"]
    },
    "batch_processing": {
        "default_batch_size": 100,
        "max_batch_size": 1000,
        "parallel_processing": True,
        "max_workers": 10
    },
    "compression": {
        "enabled": True,
        "algorithm": "gzip",
        "compression_level": 6
    }
}

# Environment-specific configurations
ENVIRONMENT_CONFIGS = {
    "development": {
        "log_level": "DEBUG",
        "metrics_enabled": True,
        "cdc_enabled": False,
        "connection_pool_size": 5,
        "batch_size": 50,
        "health_checks_enabled": True
    },
    
    "staging": {
        "log_level": "INFO",
        "metrics_enabled": True,
        "cdc_enabled": True,
        "connection_pool_size": 10,
        "batch_size": 100,
        "health_checks_enabled": True,
        "alert_threshold_multiplier": 1.5
    },
    
    "production": {
        "log_level": "WARNING",
        "metrics_enabled": True,
        "cdc_enabled": True,
        "connection_pool_size": 20,
        "batch_size": 500,
        "health_checks_enabled": True,
        "alert_threshold_multiplier": 1.0,
        "security_audit_enabled": True,
        "backup_enabled": True
    }
}

# Example complete configuration for a production environment
PRODUCTION_CONFIG = {
    "databases": {
        "source": POSTGRESQL_CONFIG,
        "target": MONGODB_CONFIG
    },
    "cdc": CDC_CONFIGS["postgresql_cdc"],
    "sync": SYNC_CONFIGS["realtime_postgresql_mongodb"],
    "transformation": TRANSFORMATION_CONFIGS["user_data_sync"],
    "monitoring": MONITORING_CONFIG,
    "error_recovery": ERROR_RECOVERY_CONFIG,
    "transaction": TRANSACTION_CONFIG,
    "connection_pools": CONNECTION_POOL_CONFIGS,
    "security": SECURITY_CONFIG,
    "performance": PERFORMANCE_CONFIG,
    "environment": ENVIRONMENT_CONFIGS["production"]
}

# Utility functions for configuration loading
def load_config(environment: str = "development") -> Dict[str, Any]:
    """Load configuration for specified environment."""
    config = ENVIRONMENT_CONFIGS.get(environment, ENVIRONMENT_CONFIGS["development"])
    
    # Add environment-specific overrides
    if environment == "production":
        # Production-specific settings
        config.update({
            "ssl_enabled": True,
            "encryption_required": True,
            "audit_logging": True,
            "backup_enabled": True
        })
    
    return config

def create_config_file(output_path: str, config_type: str = "production"):
    """Create a configuration file."""
    config = PRODUCTION_CONFIG
    
    import json
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2, default=str)
    
    print(f"Configuration file created: {output_path}")

if __name__ == "__main__":
    # Create example configuration files
    create_config_file("config/production_config.json", "production")
    create_config_file("config/staging_config.json", "staging")
    create_config_file("config/development_config.json", "development")
    
    # Print example configuration
    print("Production Configuration Example:")
    print("=" * 50)
    import json
    print(json.dumps(PRODUCTION_CONFIG, indent=2, default=str))
