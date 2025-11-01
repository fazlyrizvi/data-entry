"""
Entity Extraction Module
Handles named entity recognition using spaCy and custom patterns.
Supports dates, amounts, names, addresses, and custom entities.
"""

import re
import spacy
import nltk
import pandas as pd
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from collections import defaultdict
import dateparser
from langdetect import detect, LangDetectError
import logging

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('stopwords', quiet=True)
except:
    pass

logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    Advanced entity extraction using spaCy, NLTK, and custom patterns.
    Supports multiple languages and custom entity definitions.
    """
    
    def __init__(self, languages: List[str] = None):
        """
        Initialize the EntityExtractor.
        
        Args:
            languages: List of language codes to load spaCy models for
        """
        self.languages = languages or ['en']
        self.nlp_models = {}
        self.custom_patterns = defaultdict(list)
        self.entity_mappings = {}
        
        # Initialize spaCy models
        self._load_spacy_models()
        
        # Define default entity patterns
        self._setup_default_patterns()
    
    def _load_spacy_models(self):
        """Load spaCy models for supported languages."""
        for lang in self.languages:
            try:
                model_name = f"{lang}_core_web_sm"
                nlp = spacy.load(model_name)
                self.nlp_models[lang] = nlp
                logger.info(f"Loaded spaCy model: {model_name}")
            except OSError:
                logger.warning(f"spaCy model '{model_name}' not found. Using English fallback.")
                try:
                    self.nlp_models[lang] = spacy.load("en_core_web_sm")
                except OSError:
                    logger.error("Could not load any spaCy model!")
    
    def _setup_default_patterns(self):
        """Setup default entity patterns for common entities."""
        # Date patterns
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',
            r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
        ]
        
        # Amount patterns
        amount_patterns = [
            r'\$\s*\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?',  # Currency
            r'\d+(?:\.\d+)?\s*(?:USD|EUR|GBP|JPY|CNY|AUD|CAD)\b',  # With currency
            r'(?:USD|EUR|GBP|JPY|CNY|AUD|CAD)\s*\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?',  # Currency prefix
            r'\d+(?:\.\d+)?\s*(?:million|billion|thousand|k|M|B)\b',  # Large numbers
        ]
        
        # Phone number patterns
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # XXX-XXX-XXXX
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',    # (XXX) XXX-XXXX
            r'\+\d{1,3}[-.\s]?\d{8,12}',       # International
        ]
        
        # Email patterns
        email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        ]
        
        # Address patterns
        address_patterns = [
            r'\b\d+\s+[A-Za-z0-9\s.-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b',
            r'\b\d+\s+[A-Za-z0-9\s.-]+(?:Suite|Ste|Unit|Apt|Building|Bldg)\s*[A-Za-z0-9-]*\b',
        ]
        
        # Store patterns
        self.custom_patterns['DATE'] = date_patterns
        self.custom_patterns['MONEY'] = amount_patterns
        self.custom_patterns['PHONE'] = phone_patterns
        self.custom_patterns['EMAIL'] = email_patterns
        self.custom_patterns['ADDRESS'] = address_patterns
    
    def add_custom_pattern(self, entity_type: str, pattern: str, description: str = ""):
        """
        Add custom entity pattern.
        
        Args:
            entity_type: Type of entity (e.g., 'CUSTOM_FIELD')
            pattern: Regular expression pattern
            description: Description of the pattern
        """
        self.custom_patterns[entity_type].append(pattern)
        logger.info(f"Added custom pattern for {entity_type}: {description}")
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the input text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Language code (e.g., 'en', 'es', 'fr')
        """
        try:
            return detect(text)
        except LangDetectError:
            logger.warning("Could not detect language. Defaulting to English.")
            return 'en'
    
    def extract_entities_spacy(self, text: str, language: str = None) -> List[Dict[str, Any]]:
        """
        Extract entities using spaCy NER.
        
        Args:
            text: Input text
            language: Language code (auto-detect if None)
            
        Returns:
            List of extracted entities
        """
        if not language:
            language = self.detect_language(text)
        
        if language not in self.nlp_models:
            language = 'en'  # fallback
        
        nlp = self.nlp_models[language]
        doc = nlp(text)
        
        entities = []
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': 1.0,  # spaCy doesn't provide confidence scores
                'source': 'spacy'
            })
        
        return entities
    
    def extract_entities_patterns(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities using custom regex patterns.
        
        Args:
            text: Input text
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        for entity_type, patterns in self.custom_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Validate the match to reduce false positives
                    if self._validate_entity(match.group(), entity_type):
                        entities.append({
                            'text': match.group(),
                            'label': entity_type,
                            'start': match.start(),
                            'end': match.end(),
                            'confidence': 0.9,
                            'source': 'pattern'
                        })
        
        return entities
    
    def _validate_entity(self, text: str, entity_type: str) -> bool:
        """
        Validate extracted entity to reduce false positives.
        
        Args:
            text: Extracted text
            entity_type: Type of entity
            
        Returns:
            True if valid, False otherwise
        """
        if entity_type == 'EMAIL':
            return '@' in text and '.' in text.split('@')[1]
        
        if entity_type == 'PHONE':
            # Should have at least 10 digits
            digits = re.findall(r'\d', text)
            return len(digits) >= 10
        
        if entity_type == 'MONEY':
            # Should have currency symbol or code
            return bool(re.search(r'[\$€£¥]|USD|EUR|GBP', text, re.IGNORECASE))
        
        if entity_type == 'ADDRESS':
            # Should contain street indicators
            return bool(re.search(r'\b(?:St|Rd|Ave|Blvd|Ln|Dr)\b', text, re.IGNORECASE))
        
        return True  # Default validation
    
    def extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract and normalize dates from text.
        
        Args:
            text: Input text
            
        Returns:
            List of extracted and normalized dates
        """
        date_entities = []
        
        # Get date entities from patterns
        for ent in self.extract_entities_patterns(text):
            if ent['label'] == 'DATE':
                parsed_date = dateparser.parse(ent['text'])
                if parsed_date:
                    date_entities.append({
                        'original_text': ent['text'],
                        'parsed_date': parsed_date.isoformat(),
                        'date_format': parsed_date.strftime('%Y-%m-%d'),
                        'confidence': ent['confidence'],
                        'start': ent['start'],
                        'end': ent['end']
                    })
        
        return date_entities
    
    def extract_amounts(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract and normalize monetary amounts from text.
        
        Args:
            text: Input text
            
        Returns:
            List of extracted and normalized amounts
        """
        amount_entities = []
        
        for ent in self.extract_entities_patterns(text):
            if ent['label'] == 'MONEY':
                # Extract numeric value
                numeric_match = re.search(r'[\d,]+(?:\.\d{2})?', ent['text'])
                if numeric_match:
                    numeric_value = float(numeric_match.group().replace(',', ''))
                    
                    # Detect currency
                    currency = 'USD'  # default
                    currency_match = re.search(r'(USD|EUR|GBP|JPY|CNY|AUD|CAD|\$)', ent['text'], re.IGNORECASE)
                    if currency_match:
                        currency_symbol = currency_match.group()
                        if currency_symbol == '$':
                            currency = 'USD'
                        else:
                            currency = currency_match.group().upper()
                    
                    amount_entities.append({
                        'original_text': ent['text'],
                        'amount': numeric_value,
                        'currency': currency,
                        'normalized': f"{numeric_value:.2f} {currency}",
                        'confidence': ent['confidence'],
                        'start': ent['start'],
                        'end': ent['end']
                    })
        
        return amount_entities
    
    def extract_all_entities(self, text: str, language: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract all entities from text using multiple methods.
        
        Args:
            text: Input text
            language: Language code (auto-detect if None)
            
        Returns:
            Dictionary with entity types as keys and lists of entities as values
        """
        if not text.strip():
            return {}
        
        # Detect language if not provided
        if not language:
            language = self.detect_language(text)
        
        results = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': self.extract_dates(text),
            'amounts': self.extract_amounts(text),
            'phones': [],
            'emails': [],
            'addresses': [],
            'other': []
        }
        
        # Extract using spaCy
        spacy_entities = self.extract_entities_spacy(text, language)
        
        # Extract using patterns
        pattern_entities = self.extract_entities_patterns(text)
        
        # Categorize spaCy entities
        for ent in spacy_entities:
            if ent['label'] in ['PERSON', 'PER']:
                results['persons'].append(ent)
            elif ent['label'] in ['ORG', 'ORGANIZATION']:
                results['organizations'].append(ent)
            elif ent['label'] in ['GPE', 'LOC', 'LOCATION']:
                results['locations'].append(ent)
            else:
                results['other'].append(ent)
        
        # Categorize pattern entities
        for ent in pattern_entities:
            if ent['label'] == 'PHONE':
                results['phones'].append(ent)
            elif ent['label'] == 'EMAIL':
                results['emails'].append(ent)
            elif ent['label'] == 'ADDRESS':
                results['addresses'].append(ent)
            elif ent['label'] == 'DATE':
                # Already handled in extract_dates
                pass
            elif ent['label'] == 'MONEY':
                # Already handled in extract_amounts
                pass
            else:
                results['other'].append(ent)
        
        return results
    
    def extract_from_dataframe(self, df: pd.DataFrame, text_column: str) -> pd.DataFrame:
        """
        Extract entities from a DataFrame.
        
        Args:
            df: Input DataFrame
            text_column: Name of the column containing text
            
        Returns:
            DataFrame with extracted entities added as new columns
        """
        results = []
        
        for idx, row in df.iterrows():
            text = str(row[text_column])
            entities = self.extract_all_entities(text)
            
            result_row = row.to_dict()
            
            # Add entity counts
            for entity_type, entity_list in entities.items():
                result_row[f'{entity_type}_count'] = len(entity_list)
                result_row[f'{entity_type}_text'] = ', '.join([e['text'] for e in entity_list])
            
            results.append(result_row)
        
        return pd.DataFrame(results)


# Form Field Recognition Module
class FormFieldExtractor(EntityExtractor):
    """
    Specialized extractor for form field recognition.
    Identifies common form fields like name, email, phone, address, etc.
    """
    
    def __init__(self):
        super().__init__()
        self.field_patterns = {
            'name_field': [
                r'(?:name|full.?name|first.?name|last.?name)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'(?:name|full.?name)\s*(?:is|=|:)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            ],
            'email_field': [
                r'(?:email|e-mail)\s*:?\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
                r'(?:email|e-mail)\s*(?:is|=|:)\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            ],
            'phone_field': [
                r'(?:phone|tel|telephone|mobile|cell)\s*:?\s*(\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4})',
                r'(?:phone|tel|telephone)\s*(?:is|=|:)\s*(\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4})',
            ],
            'address_field': [
                r'(?:address|addr)\s*:?\s*(\d+\s+[A-Za-z0-9\s.-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd))',
                r'(?:address|addr)\s*:?\s*(\d+\s+[A-Za-z0-9\s.-]+\s*(?:Suite|Ste|Unit|Apt)\s*[A-Za-z0-9-]*)',
            ],
            'date_field': [
                r'(?:date| dob| birth.?date)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:date| dob)\s*(?:is|=|:)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ]
        }
    
    def extract_form_fields(self, text: str) -> Dict[str, Any]:
        """
        Extract form field values from structured text.
        
        Args:
            text: Input text that may contain form data
            
        Returns:
            Dictionary with field names and extracted values
        """
        fields = {}
        
        for field_type, patterns in self.field_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    value = match.group(1).strip()
                    if value and len(value) > 2:  # Basic validation
                        field_name = field_type.replace('_field', '')
                        fields[field_name] = {
                            'value': value,
                            'confidence': 0.9,
                            'position': {'start': match.start(), 'end': match.end()}
                        }
        
        return fields
    
    def identify_form_structure(self, text: str) -> Dict[str, Any]:
        """
        Identify form structure and extract all fields.
        
        Args:
            text: Form text
            
        Returns:
            Complete form structure with all fields
        """
        # First, try to extract structured form fields
        form_fields = self.extract_form_fields(text)
        
        # Also extract general entities
        general_entities = self.extract_all_entities(text)
        
        # Combine results
        return {
            'form_fields': form_fields,
            'entities': general_entities,
            'total_fields': len(form_fields),
            'confidence_score': sum(field['confidence'] for field in form_fields.values()) / len(form_fields) if form_fields else 0
        }


if __name__ == "__main__":
    # Example usage
    extractor = EntityExtractor()
    
    sample_text = """
    John Smith
    123 Main Street
    New York, NY 10001
    Email: john.smith@example.com
    Phone: (555) 123-4567
    Date of Birth: 01/15/1985
    Salary: $75,000
    """
    
    entities = extractor.extract_all_entities(sample_text)
    print("Extracted Entities:")
    for entity_type, entity_list in entities.items():
        if entity_list:
            print(f"\n{entity_type.upper()}:")
            for entity in entity_list:
                print(f"  - {entity['text']} (confidence: {entity['confidence']})")
