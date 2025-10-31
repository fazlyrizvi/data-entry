"""
Configuration settings for the NLP Processing Pipeline
"""

import os
from typing import Dict, Any, List

# API Configuration
API_CONFIG = {
    "host": os.getenv("API_HOST", "0.0.0.0"),
    "port": int(os.getenv("API_PORT", 8000)),
    "workers": int(os.getenv("API_WORKERS", 4)),
    "reload": os.getenv("API_RELOAD", "false").lower() == "true",
    "log_level": os.getenv("LOG_LEVEL", "info")
}

# Model Configuration
MODEL_CONFIG = {
    "spacy_models": {
        "en": "en_core_web_sm",
        "es": "es_core_news_sm", 
        "fr": "fr_core_news_sm",
        "de": "de_core_news_sm"
    },
    "transformers": {
        "text_classifier": {
            "model_name": os.getenv("TEXT_CLASSIFIER_MODEL", "distilbert-base-uncased"),
            "num_labels": int(os.getenv("NUM_LABELS", 2)),
            "max_length": int(os.getenv("MAX_SEQUENCE_LENGTH", 512))
        },
        "entity_classifier": {
            "model_name": os.getenv("ENTITY_CLASSIFIER_MODEL", "dbmdz/bert-large-cased-finetuned-conll03-english"),
            "aggregation_strategy": "simple"
        }
    },
    "batch_size": int(os.getenv("BATCH_SIZE", 32)),
    "device": os.getenv("DEVICE", "auto")  # auto, cpu, cuda
}

# Entity Extraction Configuration
ENTITY_CONFIG = {
    "supported_languages": ["en", "es", "fr", "de"],
    "confidence_threshold": 0.7,
    "enable_custom_patterns": True,
    "default_patterns": {
        "DATE": [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,4}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b'
        ],
        "MONEY": [
            r'\$\s*\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?',
            r'\d+(?:\.\d+)?\s*(?:USD|EUR|GBP|JPY|CNY|AUD|CAD)\b'
        ],
        "PHONE": [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',
            r'\+\d{1,3}[-.\s]?\d{8,12}'
        ],
        "EMAIL": [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ]
    }
}

# Classification Configuration
CLASSIFICATION_CONFIG = {
    "document_types": {
        "invoice": {
            "keywords": ["invoice", "bill", "total", "amount due", "itemized"],
            "min_score": 0.3
        },
        "contract": {
            "keywords": ["agreement", "contract", "terms", "conditions"],
            "min_score": 0.3
        },
        "resume": {
            "keywords": ["experience", "education", "skills", "employment"],
            "min_score": 0.3
        }
    },
    "sentiment": {
        "positive_words": ["good", "great", "excellent", "satisfied", "happy"],
        "negative_words": ["bad", "poor", "terrible", "dissatisfied", "unhappy"],
        "confidence_threshold": 0.1
    }
}

# Form Field Configuration
FORM_CONFIG = {
    "field_patterns": {
        "name": [
            r'(?:name|full.?name)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:name|full.?name)\s*(?:is|=|:)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ],
        "email": [
            r'(?:email|e-mail)\s*:?\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
        ],
        "phone": [
            r'(?:phone|tel|telephone|mobile)\s*:?\s*(\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4})'
        ]
    },
    "min_field_confidence": 0.8
}

# Security Configuration
SECURITY_CONFIG = {
    "max_text_length": int(os.getenv("MAX_TEXT_LENGTH", 50000)),
    "max_file_size": int(os.getenv("MAX_FILE_SIZE", 10485760)),  # 10MB
    "allowed_file_types": [".txt", ".csv", ".xlsx", ".xls"],
    "rate_limit": {
        "requests_per_minute": int(os.getenv("RATE_LIMIT_PER_MINUTE", 100)),
        "burst_size": int(os.getenv("RATE_LIMIT_BURST", 20))
    }
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": os.getenv("LOG_FILE", "nlp_pipeline.log"),
    "max_file_size": int(os.getenv("LOG_MAX_SIZE", 10485760)),  # 10MB
    "backup_count": int(os.getenv("LOG_BACKUP_COUNT", 5))
}

# Cache Configuration
CACHE_CONFIG = {
    "enabled": os.getenv("CACHE_ENABLED", "true").lower() == "true",
    "ttl": int(os.getenv("CACHE_TTL", 3600)),  # 1 hour
    "max_size": int(os.getenv("CACHE_MAX_SIZE", 1000)),
    "backend": os.getenv("CACHE_BACKEND", "memory")  # memory, redis
}

# Database Configuration (for future use)
DATABASE_CONFIG = {
    "url": os.getenv("DATABASE_URL", "sqlite:///nlp_pipeline.db"),
    "pool_size": int(os.getenv("DB_POOL_SIZE", 10)),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", 20))
}

# Export all configurations
ALL_CONFIGS = {
    "api": API_CONFIG,
    "models": MODEL_CONFIG,
    "entities": ENTITY_CONFIG,
    "classification": CLASSIFICATION_CONFIG,
    "forms": FORM_CONFIG,
    "security": SECURITY_CONFIG,
    "logging": LOGGING_CONFIG,
    "cache": CACHE_CONFIG,
    "database": DATABASE_CONFIG
}


def get_config(section: str = None) -> Dict[str, Any]:
    """
    Get configuration section(s).
    
    Args:
        section: Specific section to get, or None for all
        
    Returns:
        Configuration dictionary
    """
    if section:
        return ALL_CONFIGS.get(section, {})
    return ALL_CONFIGS


def validate_config() -> bool:
    """
    Validate configuration settings.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        # Check API configuration
        assert 1 <= API_CONFIG["port"] <= 65535
        
        # Check model paths exist (would check in real implementation)
        # assert os.path.exists(MODEL_CONFIG["spacy_models"]["en"])
        
        # Check security limits
        assert SECURITY_CONFIG["max_text_length"] > 0
        assert SECURITY_CONFIG["max_file_size"] > 0
        
        return True
        
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False


if __name__ == "__main__":
    # Test configuration
    print("NLP Pipeline Configuration Test")
    print("=" * 40)
    
    # Validate configuration
    is_valid = validate_config()
    print(f"Configuration valid: {is_valid}")
    
    # Print key settings
    print(f"\nAPI Port: {API_CONFIG['port']}")
    print(f"Default Model: {MODEL_CONFIG['transformers']['text_classifier']['model_name']}")
    print(f"Languages: {ENTITY_CONFIG['supported_languages']}")
    print(f"Max Text Length: {SECURITY_CONFIG['max_text_length']}")
    print(f"Cache Enabled: {CACHE_CONFIG['enabled']}")
    
    # Test getting specific section
    print(f"\nSecurity Config: {get_config('security')}")
