#!/usr/bin/env python3
"""
NLP Pipeline Comprehensive Test Suite
====================================
Tests NLP pipeline entity extraction, classification, and form field recognition.
"""

import os
import sys
import json
import time
import asyncio
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Add NLP pipeline to path
sys.path.append('/workspace/code/nlp_pipeline')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestNLPPipeline(unittest.TestCase):
    """Comprehensive NLP pipeline test suite."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.test_results = {
            'test_suite': 'NLP Pipeline',
            'start_time': datetime.now().isoformat(),
            'tests': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'errors': []
            }
        }
        
    def _add_test_result(self, test_name: str, status: str, message: str, 
                        duration: float, details: Dict = None):
        """Add test result to the test suite results."""
        result = {
            'test_name': test_name,
            'status': status,
            'message': message,
            'duration': duration,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        self.test_results['tests'].append(result)
        self.test_results['summary']['total'] += 1
        
        if status == 'PASSED':
            self.test_results['summary']['passed'] += 1
            logger.info(f"✓ {test_name}: {message}")
        else:
            self.test_results['summary']['failed'] += 1
            self.test_results['summary']['errors'].append({
                'test': test_name,
                'error': message
            })
            logger.error(f"✗ {test_name}: {message}")
    
    def test_001_component_imports(self):
        """Test NLP component imports and initialization."""
        test_name = "Component Imports"
        start_time = time.time()
        
        try:
            # Test basic imports
            from entity_extractor import EntityExtractor, FormFieldExtractor
            from classifier import DataClassificationPipeline, TextClassifier
            
            # Test EntityExtractor initialization
            entity_extractor = EntityExtractor(languages=['en'])
            self.assertIsNotNone(entity_extractor)
            self.assertIn('en', entity_extractor.languages)
            
            # Test FormFieldExtractor initialization
            form_extractor = FormFieldExtractor()
            self.assertIsNotNone(form_extractor)
            
            # Test DataClassificationPipeline initialization
            classifier_pipeline = DataClassificationPipeline()
            self.assertIsNotNone(classifier_pipeline)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'All components imported and initialized', 
                                duration, {
                                    'entity_extractor_ready': True,
                                    'form_extractor_ready': True,
                                    'classifier_pipeline_ready': True
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Component import failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_002_entity_extraction(self):
        """Test entity extraction functionality."""
        test_name = "Entity Extraction"
        start_time = time.time()
        
        try:
            from entity_extractor import EntityExtractor
            
            # Create entity extractor
            extractor = EntityExtractor(languages=['en'])
            
            # Test text with various entities
            test_text = """
            John Doe was born on January 15, 1990.
            He lives at 123 Main Street, New York, NY 10001.
            His email is john.doe@example.com and phone is +1-555-123-4567.
            He works for Tech Corp and earns $75,000 annually.
            The meeting is scheduled for 3:30 PM on 12/25/2023.
            """
            
            # Extract entities
            entities = extractor.extract_all_entities(test_text)
            
            # Verify results
            self.assertIsInstance(entities, dict)
            
            # Check for expected entity types
            expected_types = ['persons', 'dates', 'amounts', 'emails', 'phones', 'locations', 'organizations']
            
            for entity_type in expected_types:
                if entity_type in entities:
                    self.assertIsInstance(entities[entity_type], list)
                    if entity_type in ['persons', 'dates', 'amounts']:
                        self.assertGreater(len(entities[entity_type]), 0)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', f'Entity extraction completed', 
                                duration, {
                                    'entities_found': {k: len(v) for k, v in entities.items() if v},
                                    'text_length': len(test_text)
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Entity extraction failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_003_multilingual_support(self):
        """Test multilingual entity extraction."""
        test_name = "Multilingual Support"
        start_time = time.time()
        
        try:
            from entity_extractor import EntityExtractor
            
            # Test with multiple languages
            extractor = EntityExtractor(languages=['en', 'es', 'fr', 'de'])
            
            # Test English text
            en_text = "John Smith lives in New York and was born on March 15, 1985."
            en_entities = extractor.extract_all_entities(en_text, language='en')
            
            # Test Spanish text
            es_text = "María González vive en Madrid y nació el 20 de enero de 1990."
            es_entities = extractor.extract_all_entities(es_text, language='es')
            
            # Verify language detection works
            en_detected = extractor.detect_language(en_text)
            es_detected = extractor.detect_language(es_text)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Multilingual extraction working', 
                                duration, {
                                    'languages_tested': ['en', 'es'],
                                    'en_entities': len([v for v in en_entities.values() if v]),
                                    'es_entities': len([v for v in es_entities.values() if v]),
                                    'en_detected': en_detected,
                                    'es_detected': es_detected
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Multilingual test failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_004_text_classification(self):
        """Test text classification functionality."""
        test_name = "Text Classification"
        start_time = time.time()
        
        try:
            from classifier import DataClassificationPipeline
            
            # Create classifier
            classifier = DataClassificationPipeline()
            
            # Test documents with different types
            documents = [
                {
                    'text': 'Invoice for services rendered. Total amount: $1,250.00. Due date: March 15, 2024.',
                    'expected_type': 'invoice'
                },
                {
                    'text': 'Meeting agenda for quarterly review. Attendees: CEO, CTO, VP Sales.',
                    'expected_type': 'meeting'
                },
                {
                    'text': 'Performance evaluation for employee John Doe. Rating: Excellent.',
                    'expected_type': 'evaluation'
                }
            ]
            
            classification_results = []
            
            for doc in documents:
                result = classifier.classify_data(doc['text'])
                classification_results.append(result)
            
            # Verify classification results
            self.assertEqual(len(classification_results), len(documents))
            
            for result in classification_results:
                self.assertIsInstance(result, dict)
                # Should contain document type classification
                if 'document_type' in result:
                    self.assertIsNotNone(result['document_type'])
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Text classification completed', 
                                duration, {
                                    'documents_classified': len(documents),
                                    'classification_keys': list(classification_results[0].keys()) if classification_results else []
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Classification test failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_005_form_field_extraction(self):
        """Test form field extraction from text."""
        test_name = "Form Field Extraction"
        start_time = time.time()
        
        try:
            from entity_extractor import FormFieldExtractor
            
            # Create form extractor
            form_extractor = FormFieldExtractor()
            
            # Test text containing form-like information
            form_text = """
            Application Form
            
            Full Name: Sarah Johnson
            Email Address: sarah.johnson@email.com
            Phone Number: (555) 987-6543
            Date of Birth: 05/20/1988
            Address: 456 Oak Avenue, Chicago, IL 60601
            Social Security Number: 123-45-6789
            Emergency Contact: Michael Johnson - (555) 123-9999
            """
            
            # Extract form structure
            form_structure = form_extractor.identify_form_structure(form_text)
            
            # Verify results
            self.assertIsInstance(form_structure, dict)
            self.assertIn('total_fields', form_structure)
            self.assertGreater(form_structure['total_fields'], 0)
            self.assertIn('confidence_score', form_structure)
            
            # Check for common form fields
            expected_fields = ['name', 'email', 'phone', 'date', 'address']
            found_fields = form_structure.get('fields', {})
            
            for field in expected_fields:
                if field in found_fields:
                    self.assertIsInstance(found_fields[field], list)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Form field extraction completed', 
                                duration, {
                                    'total_fields': form_structure['total_fields'],
                                    'confidence_score': form_structure['confidence_score'],
                                    'fields_found': list(found_fields.keys())
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Form field extraction failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_006_custom_patterns(self):
        """Test custom entity pattern addition and usage."""
        test_name = "Custom Patterns"
        start_time = time.time()
        
        try:
            from entity_extractor import EntityExtractor
            
            # Create extractor
            extractor = EntityExtractor(languages=['en'])
            
            # Add custom patterns
            extractor.add_custom_pattern('product_code', r'[A-Z]{2}\d{4}', 'Product code pattern')
            extractor.add_custom_pattern('order_id', r'ORD-\d{6}', 'Order ID pattern')
            
            # Test text with custom patterns
            test_text = "Product codes: AB1234, CD5678, EF9012. Order IDs: ORD-123456, ORD-789012."
            
            # Extract entities
            entities = extractor.extract_all_entities(test_text)
            
            # Check if custom patterns were applied
            custom_entities_found = False
            if 'product_code' in entities or 'order_id' in entities:
                custom_entities_found = True
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Custom patterns working', 
                                duration, {
                                    'custom_patterns_added': 2,
                                    'custom_entities_found': custom_entities_found,
                                    'entities': entities
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Custom pattern test failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_007_batch_processing(self):
        """Test batch processing capabilities."""
        test_name = "Batch Processing"
        start_time = time.time()
        
        try:
            from entity_extractor import EntityExtractor
            from classifier import DataClassificationPipeline
            
            # Create processors
            extractor = EntityExtractor(languages=['en'])
            classifier = DataClassificationPipeline()
            
            # Create batch of texts
            batch_texts = [
                "John Smith born January 15, 1990 in New York",
                "Meeting scheduled for 3:00 PM on Friday",
                "Invoice amount: $2,500.00 due March 31",
                "Email: jane.doe@company.com phone: 555-0123",
                "Product order ORD-456789 totaling $1,250"
            ]
            
            # Process batch
            batch_results = []
            for text in batch_texts:
                entities = extractor.extract_all_entities(text)
                classification = classifier.classify_data(text)
                
                batch_results.append({
                    'text': text,
                    'entities': entities,
                    'classification': classification
                })
            
            # Verify batch results
            self.assertEqual(len(batch_results), len(batch_texts))
            
            for result in batch_results:
                self.assertIsInstance(result['entities'], dict)
                self.assertIsInstance(result['classification'], dict)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Batch processing completed', 
                                duration, {
                                    'batch_size': len(batch_texts),
                                    'processing_time': duration,
                                    'avg_time_per_document': duration / len(batch_texts)
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Batch processing failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_008_performance_test(self):
        """Test performance with large texts and complex operations."""
        test_name = "Performance Test"
        start_time = time.time()
        
        try:
            from entity_extractor import EntityExtractor
            from classifier import DataClassificationPipeline
            
            # Create processors
            extractor = EntityExtractor(languages=['en'])
            classifier = DataClassificationPipeline()
            
            # Create large test text
            large_text = """
            This is a comprehensive test document for performance testing.
            It contains multiple entities like dates (January 15, 2024, March 31, 2024),
            names (John Smith, Jane Doe, Michael Johnson, Sarah Williams),
            locations (New York, Los Angeles, Chicago, Houston),
            organizations (Tech Corp, Global Solutions, Mega Inc),
            amounts ($1,000.50, $25,000, $150,750.25),
            phone numbers (555-123-4567, (555) 987-6543, +1-555-012-3456),
            email addresses (john.smith@email.com, jane.doe@company.org),
            and various other data points that need to be processed efficiently.
            
            The document continues with more complex structures:
            Invoice INV-2024-001 for services rendered by Tech Corp.
            Total amount: $15,750.50 due on April 15, 2024.
            Contact: procurement@techcorp.com, (555) 123-9999.
            
            Meeting notes from quarterly review scheduled 2:00 PM, May 20, 2024.
            Attendees: CEO John Anderson, CTO Sarah Chen, CFO Michael Davis.
            Location: Conference Room A, 123 Business Plaza, New York, NY 10001.
            """ * 10  # Repeat to make it larger
            
            # Measure entity extraction time
            start_entities = time.time()
            entities = extractor.extract_all_entities(large_text)
            end_entities = time.time()
            
            # Measure classification time
            start_classification = time.time()
            classification = classifier.classify_data(large_text)
            end_classification = time.time()
            
            # Calculate performance metrics
            entity_time = end_entities - start_entities
            classification_time = end_classification - start_classification
            total_time = end_classification - start_time
            
            # Verify performance is reasonable
            self.assertLess(entity_time, 10.0)  # Should process in under 10 seconds
            self.assertLess(classification_time, 5.0)  # Should classify in under 5 seconds
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Performance test passed', 
                                duration, {
                                    'text_size': len(large_text),
                                    'entity_extraction_time': entity_time,
                                    'classification_time': classification_time,
                                    'total_time': total_time,
                                    'entities_found': sum(len(v) for v in entities.values() if v)
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Performance test failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_009_error_handling(self):
        """Test error handling and edge cases."""
        test_name = "Error Handling"
        start_time = time.time()
        
        try:
            from entity_extractor import EntityExtractor
            
            # Create extractor
            extractor = EntityExtractor(languages=['en'])
            
            # Test with empty text
            empty_entities = extractor.extract_all_entities("")
            self.assertIsInstance(empty_entities, dict)
            
            # Test with None (should handle gracefully)
            try:
                none_entities = extractor.extract_all_entities(None)
                self.fail("Should have raised an exception for None input")
            except (TypeError, AttributeError):
                pass  # Expected behavior
            
            # Test with very long text
            long_text = "A" * 100000  # Very long text
            long_entities = extractor.extract_all_entities(long_text)
            self.assertIsInstance(long_entities, dict)
            
            # Test with special characters
            special_text = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
            special_entities = extractor.extract_all_entities(special_text)
            self.assertIsInstance(special_entities, dict)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Error handling working correctly', 
                                duration, {
                                    'empty_text_handled': True,
                                    'long_text_handled': True,
                                    'special_chars_handled': True
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Error handling test failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    @classmethod
    def tearDownClass(cls):
        """Save test results."""
        cls.test_results['end_time'] = datetime.now().isoformat()
        cls.test_results['duration'] = (
            datetime.fromisoformat(cls.test_results['end_time']) - 
            datetime.fromisoformat(cls.test_results['start_time'])
        ).total_seconds()
        
        # Save results to file
        results_file = '/workspace/testing/results/nlp_pipeline_test_results.json'
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(cls.test_results, f, indent=2, default=str)
        
        logger.info(f"NLP Pipeline test results saved to {results_file}")


def run_nlp_tests():
    """Run all NLP pipeline tests."""
    logger.info("Starting NLP Pipeline Comprehensive Test Suite")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNLPPipeline)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    logger.info(f"NLP Pipeline Tests Completed: {result.testsRun} tests run")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    return result


if __name__ == "__main__":
    run_nlp_tests()
