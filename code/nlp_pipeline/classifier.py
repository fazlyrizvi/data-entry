"""
Data Classification Module
Handles intelligent data classification and advanced extraction using Transformers.
Supports multiple classification tasks and custom models.
"""

import torch
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    AutoModelForTokenClassification, pipeline,
    BertTokenizer, BertForSequenceClassification
)
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
import logging
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)


class TextClassifier:
    """
    Advanced text classification using pre-trained Transformers models.
    Supports custom classification tasks and fine-tuning.
    """
    
    def __init__(self, model_name: str = "distilbert-base-uncased", num_labels: int = 2):
        """
        Initialize the TextClassifier.
        
        Args:
            model_name: Pre-trained model name or path
            num_labels: Number of classification labels
        """
        self.model_name = model_name
        self.num_labels = num_labels
        self.tokenizer = None
        self.model = None
        self.classifier_pipeline = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        logger.info(f"Initializing classifier with model: {model_name}")
        self._load_model()
    
    def _load_model(self):
        """Load the pre-trained model and tokenizer."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name, num_labels=self.num_labels
            )
            self.model.to(self.device)
            
            # Create pipeline for easy inference
            self.classifier_pipeline = pipeline(
                "text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info(f"Model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def classify_text(self, text: str) -> Dict[str, Any]:
        """
        Classify a single text.
        
        Args:
            text: Input text to classify
            
        Returns:
            Classification result with labels and probabilities
        """
        if not self.classifier_pipeline:
            raise ValueError("Model not loaded. Call _load_model() first.")
        
        try:
            result = self.classifier_pipeline(text)
            
            # Handle single result
            if isinstance(result, list):
                result = result[0]
            
            return {
                'text': text,
                'predicted_label': result['label'],
                'confidence': result['score'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {
                'text': text,
                'predicted_label': 'ERROR',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def classify_batch(self, texts: List[str], batch_size: int = 32) -> List[Dict[str, Any]]:
        """
        Classify multiple texts in batches.
        
        Args:
            texts: List of texts to classify
            batch_size: Batch size for processing
            
        Returns:
            List of classification results
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                batch_results = self.classifier_pipeline(batch)
                
                for text, result in zip(batch, batch_results):
                    if isinstance(result, list):
                        result = result[0]
                    
                    results.append({
                        'text': text,
                        'predicted_label': result['label'],
                        'confidence': result['score'],
                        'timestamp': datetime.now().isoformat()
                    })
                    
            except Exception as e:
                logger.error(f"Batch classification error: {e}")
                # Add error entries for failed classifications
                for text in batch:
                    results.append({
                        'text': text,
                        'predicted_label': 'ERROR',
                        'confidence': 0.0,
                        'error': str(e)
                    })
        
        return results
    
    def classify_document_type(self, text: str) -> Dict[str, Any]:
        """
        Classify the type of document (invoice, contract, form, etc.).
        
        Args:
            text: Input text to analyze
            
        Returns:
            Document type classification
        """
        # Define document type keywords
        doc_types = {
            'invoice': {
                'keywords': ['invoice', 'bill', 'total', 'amount due', 'itemized', 'qty', 'quantity'],
                'patterns': [r'invoice\s*#?:?\s*\d+', r'amount\s+due', r'total\s*:?\s*\$']
            },
            'contract': {
                'keywords': ['agreement', 'contract', 'terms', 'conditions', 'parties', 'whereas'],
                'patterns': [r'agreement\s+between', r'contract\s+agreement', r'terms\s+and\s+conditions']
            },
            'resume': {
                'keywords': ['experience', 'education', 'skills', 'employment', 'qualifications'],
                'patterns': [r'work\s+experience', r'educational\s+background', r'professional\s+summary']
            },
            'form': {
                'keywords': ['name', 'address', 'date', 'signature', 'form', 'application'],
                'patterns': [r'name\s*:', r'signature\s*:', r'application\s+form']
            },
            'report': {
                'keywords': ['report', 'analysis', 'findings', 'summary', 'conclusion'],
                'patterns': [r'executive\s+summary', r'findings\s+indicate', r'recommendation']
            }
        }
        
        scores = {}
        text_lower = text.lower()
        
        for doc_type, criteria in doc_types.items():
            score = 0
            
            # Keyword matching
            for keyword in criteria['keywords']:
                score += text_lower.count(keyword.lower()) * 2
            
            # Pattern matching
            for pattern in criteria['patterns']:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                score += matches * 5
            
            scores[doc_type] = score
        
        # Normalize scores
        max_score = max(scores.values()) if scores else 1
        normalized_scores = {k: v / max_score for k, v in scores.items()}
        
        # Get predicted type
        predicted_type = max(normalized_scores, key=normalized_scores.get)
        
        return {
            'document_type': predicted_type,
            'confidence': normalized_scores[predicted_type],
            'scores': normalized_scores,
            'classification_method': 'rule-based'
        }
    
    def extract_document_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extract metadata from documents (dates, authors, organizations, etc.).
        
        Args:
            text: Input document text
            
        Returns:
            Document metadata
        """
        metadata = {
            'word_count': len(text.split()),
            'character_count': len(text),
            'sentence_count': len(re.findall(r'[.!?]+', text)),
            'paragraph_count': len(text.split('\n\n')),
            'language': 'unknown',
            'has_dates': bool(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text)),
            'has_numbers': bool(re.search(r'\d+', text)),
            'has_emails': bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)),
            'has_phones': bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text))
        }
        
        # Language detection (simple heuristic)
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        english_count = sum(1 for word in english_words if word in text.lower())
        metadata['language'] = 'en' if english_count >= 3 else 'unknown'
        
        return metadata


class AdvancedEntityClassifier:
    """
    Advanced entity classification using Named Entity Recognition models.
    """
    
    def __init__(self, model_name: str = "dbmdz/bert-large-cased-finetuned-conll03-english"):
        """
        Initialize the AdvancedEntityClassifier.
        
        Args:
            model_name: Pre-trained NER model name
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.ner_pipeline = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        self._load_model()
    
    def _load_model(self):
        """Load the NER model and tokenizer."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            
            self.ner_pipeline = pipeline(
                "ner",
                model=self.model,
                tokenizer=self.tokenizer,
                aggregation_strategy="simple",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info(f"NER model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading NER model: {e}")
            # Fallback to simple pipeline
            try:
                self.ner_pipeline = pipeline("ner", aggregation_strategy="simple")
                logger.info("Loaded fallback NER pipeline")
            except Exception as e2:
                logger.error(f"Could not load any NER model: {e2}")
                raise
    
    def classify_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Classify entities in the text.
        
        Args:
            text: Input text
            
        Returns:
            List of classified entities with confidence scores
        """
        if not self.ner_pipeline:
            raise ValueError("NER model not loaded")
        
        try:
            entities = self.ner_pipeline(text)
            
            results = []
            for entity in entities:
                results.append({
                    'word': entity['word'],
                    'entity_group': entity['entity_group'],
                    'score': entity['score'],
                    'start': entity['start'],
                    'end': entity['end']
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Entity classification error: {e}")
            return []
    
    def extract_sensitive_information(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract sensitive information types (PII, financial, etc.).
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with sensitive information categories
        """
        sensitive_info = {
            'personal_info': [],
            'financial_info': [],
            'contact_info': [],
            'identification': []
        }
        
        entities = self.classify_entities(text)
        
        for entity in entities:
            entity_group = entity['entity_group'].upper()
            score = entity['score']
            
            if score > 0.7:  # Confidence threshold
                sensitive_entity = {
                    'text': entity['word'],
                    'confidence': score,
                    'position': {'start': entity['start'], 'end': entity['end']}
                }
                
                if entity_group in ['PER', 'PERSON', 'NAME']:
                    sensitive_info['personal_info'].append(sensitive_entity)
                elif entity_group in ['ORG', 'ORGANIZATION']:
                    sensitive_info['financial_info'].append(sensitive_entity)
                elif entity_group in ['PHONE', 'EMAIL', 'CONTACT']:
                    sensitive_info['contact_info'].append(sensitive_entity)
                elif entity_group in ['ID', 'IDENTIFICATION', 'SSN', 'PASSPORT']:
                    sensitive_info['identification'].append(sensitive_entity)
        
        return sensitive_info


class DataClassificationPipeline:
    """
    Complete data classification pipeline combining multiple models and methods.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the classification pipeline.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Initialize components
        self.text_classifier = TextClassifier(
            model_name=self.config.get('text_model', 'distilbert-base-uncased'),
            num_labels=self.config.get('num_labels', 2)
        )
        
        self.entity_classifier = AdvancedEntityClassifier(
            model_name=self.config.get('entity_model', 'dbmdz/bert-large-cased-finetuned-conll03-english')
        )
        
        logger.info("DataClassificationPipeline initialized")
    
    def classify_data(self, text: str, classification_tasks: List[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive data classification.
        
        Args:
            text: Input text to classify
            classification_tasks: List of tasks to perform
            
        Returns:
            Complete classification results
        """
        if classification_tasks is None:
            classification_tasks = ['document_type', 'sentiment', 'entities', 'metadata']
        
        results = {
            'input_text': text,
            'timestamp': datetime.now().isoformat(),
            'classification_tasks': {}
        }
        
        try:
            if 'document_type' in classification_tasks:
                results['classification_tasks']['document_type'] = \
                    self.text_classifier.classify_document_type(text)
            
            if 'sentiment' in classification_tasks:
                # Simple sentiment analysis using keywords
                positive_words = ['good', 'great', 'excellent', 'positive', 'satisfied', 'happy']
                negative_words = ['bad', 'poor', 'negative', 'dissatisfied', 'unhappy', 'terrible']
                
                text_lower = text.lower()
                pos_score = sum(1 for word in positive_words if word in text_lower)
                neg_score = sum(1 for word in negative_words if word in text_lower)
                
                sentiment = 'POSITIVE' if pos_score > neg_score else 'NEGATIVE' if neg_score > pos_score else 'NEUTRAL'
                confidence = abs(pos_score - neg_score) / max(pos_score + neg_score, 1)
                
                results['classification_tasks']['sentiment'] = {
                    'label': sentiment,
                    'confidence': confidence,
                    'positive_score': pos_score,
                    'negative_score': neg_score
                }
            
            if 'entities' in classification_tasks:
                results['classification_tasks']['entities'] = \
                    self.entity_classifier.classify_entities(text)
            
            if 'metadata' in classification_tasks:
                results['classification_tasks']['metadata'] = \
                    self.text_classifier.extract_document_metadata(text)
            
            if 'sensitive_info' in classification_tasks:
                results['classification_tasks']['sensitive_info'] = \
                    self.entity_classifier.extract_sensitive_information(text)
            
        except Exception as e:
            logger.error(f"Classification pipeline error: {e}")
            results['error'] = str(e)
        
        return results
    
    def classify_batch_dataframe(self, df: pd.DataFrame, text_column: str, 
                                output_column: str = None) -> pd.DataFrame:
        """
        Classify data in a DataFrame.
        
        Args:
            df: Input DataFrame
            text_column: Name of text column
            output_column: Name for output column (optional)
            
        Returns:
            DataFrame with classification results
        """
        output_column = output_column or 'classification_results'
        
        results = []
        
        for idx, row in df.iterrows():
            text = str(row[text_column])
            classification = self.classify_data(text)
            
            result_row = row.to_dict()
            result_row[output_column] = classification
            
            results.append(result_row)
        
        return pd.DataFrame(results)
    
    def generate_classification_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive classification report.
        
        Args:
            results: List of classification results
            
        Returns:
            Classification report with statistics
        """
        if not results:
            return {'error': 'No results to analyze'}
        
        report = {
            'total_documents': len(results),
            'timestamp': datetime.now().isoformat(),
            'document_types': {},
            'sentiment_distribution': {},
            'average_confidence': {},
            'common_entities': {},
            'errors': 0
        }
        
        entity_counts = {}
        confidence_scores = {task: [] for task in ['document_type', 'sentiment']}
        
        for result in results:
            if 'error' in result:
                report['errors'] += 1
                continue
            
            # Document type distribution
            doc_type = result.get('classification_tasks', {}).get('document_type', {}).get('document_type', 'unknown')
            report['document_types'][doc_type] = report['document_types'].get(doc_type, 0) + 1
            
            # Sentiment distribution
            sentiment = result.get('classification_tasks', {}).get('sentiment', {}).get('label', 'unknown')
            report['sentiment_distribution'][sentiment] = report['sentiment_distribution'].get(sentiment, 0) + 1
            
            # Collect confidence scores
            for task in confidence_scores:
                task_result = result.get('classification_tasks', {}).get(task, {})
                if 'confidence' in task_result:
                    confidence_scores[task].append(task_result['confidence'])
            
            # Entity frequency
            entities = result.get('classification_tasks', {}).get('entities', [])
            for entity in entities:
                entity_type = entity.get('entity_group', 'unknown')
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
        
        # Calculate averages
        for task, scores in confidence_scores.items():
            if scores:
                report['average_confidence'][task] = np.mean(scores)
        
        # Top entities
        sorted_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
        report['common_entities'] = dict(sorted_entities[:10])
        
        return report


if __name__ == "__main__":
    # Example usage
    classifier = DataClassificationPipeline()
    
    sample_texts = [
        "Invoice #12345: Total amount due is $1,500.00 for services rendered.",
        "Employment contract between John Doe and ABC Corporation.",
        "Thank you for your excellent service! I am very satisfied."
    ]
    
    print("Classifying sample texts...")
    for text in sample_texts:
        result = classifier.classify_data(text)
        print(f"\nText: {text}")
        print(f"Document Type: {result['classification_tasks'].get('document_type', {}).get('document_type', 'unknown')}")
        print(f"Sentiment: {result['classification_tasks'].get('sentiment', {}).get('label', 'unknown')}")
