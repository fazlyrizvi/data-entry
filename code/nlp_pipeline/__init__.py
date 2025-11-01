"""
NLP Processing Pipeline Package
"""

__version__ = "1.0.0"
__author__ = "NLP Pipeline Team"

# Import main components
from .entity_extractor import EntityExtractor, FormFieldExtractor
from .classifier import DataClassificationPipeline, TextClassifier, AdvancedEntityClassifier
from .main import app

__all__ = [
    'EntityExtractor',
    'FormFieldExtractor', 
    'DataClassificationPipeline',
    'TextClassifier',
    'AdvancedEntityClassifier',
    'app'
]
