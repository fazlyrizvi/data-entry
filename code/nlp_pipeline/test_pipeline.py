#!/usr/bin/env python3
"""
Test script for NLP Processing Pipeline
Demonstrates entity extraction, classification, and form field recognition.
"""

import sys
import os
import time
import json
from typing import Dict, Any

# Add the package to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from entity_extractor import EntityExtractor, FormFieldExtractor
    from classifier import DataClassificationPipeline
    from config import get_config
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install required dependencies: pip install -r requirements.txt")
    sys.exit(1)


class NLPPipelineTester:
    """Test suite for NLP pipeline components."""
    
    def __init__(self):
        self.entity_extractor = None
        self.form_extractor = None
        self.classifier = None
        self.test_results = []
    
    def setup(self):
        """Initialize pipeline components."""
        print("Setting up NLP pipeline components...")
        
        try:
            self.entity_extractor = EntityExtractor(languages=['en'])
            print("✓ Entity extractor initialized")
            
            self.form_extractor = FormFieldExtractor()
            print("✓ Form field extractor initialized")
            
            self.classifier = DataClassificationPipeline()
            print("✓ Classifier initialized")
            
            print("All components ready!\n")
            return True
            
        except Exception as e:
            print(f"✗ Setup failed: {e}")
            return False
    
    def test_entity_extraction(self):
        """Test entity extraction functionality."""
        print("Testing Entity Extraction")
        print("-" * 30)
        
        test_texts = [
            "John Smith lives at 123 Main Street, New York, NY 10001. Email: john.smith@example.com, Phone: (555) 123-4567. Born on 01/15/1985. Salary: $75,000.",
            "Microsoft Corporation, located at 1 Microsoft Way, Redmond, WA 98052, reported revenue of $168.088 billion in 2022.",
            "The meeting is scheduled for December 15, 2023, at 2:00 PM in Conference Room A."
        ]
        
        for i, text in enumerate(test_texts, 1):
            print(f"\nTest {i}: {text[:50]}...")
            
            try:
                start_time = time.time()
                entities = self.entity_extractor.extract_all_entities(text)
                end_time = time.time()
                
                # Count entities found
                total_entities = sum(len(entity_list) for entity_list in entities.values())
                
                print(f"  Processing time: {end_time - start_time:.3f}s")
                print(f"  Total entities found: {total_entities}")
                
                # Show sample entities
                for entity_type, entity_list in entities.items():
                    if entity_list:
                        print(f"  {entity_type}: {len(entity_list)} found")
                        for entity in entity_list[:2]:  # Show first 2
                            print(f"    - {entity['text']} (confidence: {entity['confidence']:.2f})")
                
                self.test_results.append({
                    'test': 'entity_extraction',
                    'text_index': i,
                    'entities_found': total_entities,
                    'processing_time': end_time - start_time,
                    'success': True
                })
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                self.test_results.append({
                    'test': 'entity_extraction',
                    'text_index': i,
                    'error': str(e),
                    'success': False
                })
        
        print()
    
    def test_date_extraction(self):
        """Test date extraction and normalization."""
        print("Testing Date Extraction")
        print("-" * 30)
        
        date_texts = [
            "The meeting is on 12/25/2023",
            "Born on January 15th, 1985",
            "Deadline is 2024-03-15",
            "Payment due next Friday",
            "Contract signed on 15 Feb 2023"
        ]
        
        for i, text in enumerate(date_texts, 1):
            print(f"\nTest {i}: {text}")
            
            try:
                dates = self.entity_extractor.extract_dates(text)
                
                if dates:
                    for date_info in dates:
                        print(f"  Found: {date_info['original_text']}")
                        print(f"  Parsed: {date_info['date_format']}")
                        print(f"  ISO: {date_info['parsed_date']}")
                else:
                    print("  No dates found")
                
                self.test_results.append({
                    'test': 'date_extraction',
                    'text_index': i,
                    'dates_found': len(dates),
                    'success': True
                })
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                self.test_results.append({
                    'test': 'date_extraction',
                    'text_index': i,
                    'error': str(e),
                    'success': False
                })
        
        print()
    
    def test_amount_extraction(self):
        """Test monetary amount extraction and normalization."""
        print("Testing Amount Extraction")
        print("-" * 30)
        
        amount_texts = [
            "Total: $1,500.00",
            "Salary of 75000 USD per year",
            "Payment of €2,500 for services",
            "Budget allocation: 1.5 million dollars",
            "Invoice amount: £3,200.50"
        ]
        
        for i, text in enumerate(amount_texts, 1):
            print(f"\nTest {i}: {text}")
            
            try:
                amounts = self.entity_extractor.extract_amounts(text)
                
                if amounts:
                    for amount_info in amounts:
                        print(f"  Found: {amount_info['original_text']}")
                        print(f"  Amount: {amount_info['amount']}")
                        print(f"  Currency: {amount_info['currency']}")
                        print(f"  Normalized: {amount_info['normalized']}")
                else:
                    print("  No amounts found")
                
                self.test_results.append({
                    'test': 'amount_extraction',
                    'text_index': i,
                    'amounts_found': len(amounts),
                    'success': True
                })
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                self.test_results.append({
                    'test': 'amount_extraction',
                    'text_index': i,
                    'error': str(e),
                    'success': False
                })
        
        print()
    
    def test_form_field_extraction(self):
        """Test form field recognition."""
        print("Testing Form Field Extraction")
        print("-" * 30)
        
        form_texts = [
            """Name: John Smith
            Email: john.smith@example.com
            Phone: (555) 123-4567
            Address: 123 Main Street, New York, NY 10001""",
            
            """Applicant Information:
            Full Name: Jane Doe
            Contact Email: jane.doe@company.com
            Telephone: +1-555-987-6543
            Residential Address: 456 Oak Avenue, Los Angeles, CA 90210""",
            
            """Employee Details:
            Name: Robert Johnson
            Email: robert.johnson@corp.com
            Phone: 555.456.7890
            Home Address: 789 Pine Street, Chicago, IL 60601"""
        ]
        
        for i, text in enumerate(form_texts, 1):
            print(f"\nTest {i}: Form data")
            
            try:
                form_structure = self.form_extractor.identify_form_structure(text)
                
                print(f"  Total fields: {form_structure['total_fields']}")
                print(f"  Confidence score: {form_structure['confidence_score']:.2f}")
                
                if form_structure['form_fields']:
                    for field_name, field_info in form_structure['form_fields'].items():
                        print(f"  {field_name}: {field_info['value']} (confidence: {field_info['confidence']:.2f})")
                
                self.test_results.append({
                    'test': 'form_field_extraction',
                    'text_index': i,
                    'fields_extracted': form_structure['total_fields'],
                    'confidence': form_structure['confidence_score'],
                    'success': True
                })
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                self.test_results.append({
                    'test': 'form_field_extraction',
                    'text_index': i,
                    'error': str(e),
                    'success': False
                })
        
        print()
    
    def test_classification(self):
        """Test document classification."""
        print("Testing Document Classification")
        print("-" * 30)
        
        classification_texts = [
            "Invoice #12345: Total amount due is $1,500.00 for services rendered on December 15, 2023.",
            "This agreement is between ABC Corporation and John Doe, effective January 1, 2024.",
            "Employment application for Jane Smith. Experience: 5 years in software development.",
            "Thank you for your excellent service! I am very satisfied with the results.",
            "Financial report showing poor performance in Q4 2023. Revenue declined significantly."
        ]
        
        for i, text in enumerate(classification_texts, 1):
            print(f"\nTest {i}: {text[:50]}...")
            
            try:
                start_time = time.time()
                result = self.classifier.classify_data(text)
                end_time = time.time()
                
                # Document type
                doc_type = result.get('classification_tasks', {}).get('document_type', {})
                print(f"  Document type: {doc_type.get('document_type', 'unknown')} (confidence: {doc_type.get('confidence', 0):.2f})")
                
                # Sentiment
                sentiment = result.get('classification_tasks', {}).get('sentiment', {})
                print(f"  Sentiment: {sentiment.get('label', 'unknown')} (confidence: {sentiment.get('confidence', 0):.2f})")
                
                # Metadata
                metadata = result.get('classification_tasks', {}).get('metadata', {})
                print(f"  Word count: {metadata.get('word_count', 0)}")
                
                print(f"  Processing time: {end_time - start_time:.3f}s")
                
                self.test_results.append({
                    'test': 'classification',
                    'text_index': i,
                    'document_type': doc_type.get('document_type'),
                    'sentiment': sentiment.get('label'),
                    'processing_time': end_time - start_time,
                    'success': True
                })
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                self.test_results.append({
                    'test': 'classification',
                    'text_index': i,
                    'error': str(e),
                    'success': False
                })
        
        print()
    
    def test_custom_patterns(self):
        """Test custom entity pattern addition."""
        print("Testing Custom Patterns")
        print("-" * 30)
        
        try:
            # Add custom pattern for product codes
            self.entity_extractor.add_custom_pattern(
                'PRODUCT_CODE',
                r'[A-Z]{2}\d{4}',
                'Product codes like AB1234'
            )
            print("✓ Added custom PRODUCT_CODE pattern")
            
            # Test with sample text
            test_text = "Product codes: AB1234, CD5678, EF9012 are available."
            entities = self.entity_extractor.extract_all_entities(test_text)
            
            custom_entities = entities.get('other', [])
            product_codes = [e for e in custom_entities if e['label'] == 'PRODUCT_CODE']
            
            print(f"Found {len(product_codes)} product codes:")
            for code in product_codes:
                print(f"  - {code['text']}")
            
            self.test_results.append({
                'test': 'custom_patterns',
                'patterns_found': len(product_codes),
                'success': True
            })
            
        except Exception as e:
            print(f"✗ Error: {e}")
            self.test_results.append({
                'test': 'custom_patterns',
                'error': str(e),
                'success': False
            })
        
        print()
    
    def run_all_tests(self):
        """Run all test suites."""
        print("=" * 60)
        print("NLP PROCESSING PIPELINE TEST SUITE")
        print("=" * 60)
        
        if not self.setup():
            print("Setup failed. Exiting.")
            return
        
        # Run individual tests
        self.test_entity_extraction()
        self.test_date_extraction()
        self.test_amount_extraction()
        self.test_form_field_extraction()
        self.test_classification()
        self.test_custom_patterns()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary."""
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - successful_tests
        
        print(f"Total tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")
        
        # Test by category
        test_categories = {}
        for result in self.test_results:
            category = result['test']
            if category not in test_categories:
                test_categories[category] = {'total': 0, 'successful': 0}
            
            test_categories[category]['total'] += 1
            if result['success']:
                test_categories[category]['successful'] += 1
        
        print("\nTest Categories:")
        for category, stats in test_categories.items():
            rate = (stats['successful'] / stats['total']) * 100
            print(f"  {category}: {stats['successful']}/{stats['total']} ({rate:.1f}%)")
        
        # Performance metrics
        successful_results = [r for r in self.test_results if r['success'] and 'processing_time' in r]
        if successful_results:
            avg_time = sum(r['processing_time'] for r in successful_results) / len(successful_results)
            print(f"\nAverage processing time: {avg_time:.3f}s")
        
        # Save results to file
        self.save_results()
        
        print(f"\nTest results saved to: test_results.json")
        print("=" * 60)
    
    def save_results(self):
        """Save test results to JSON file."""
        try:
            results_file = os.path.join(os.path.dirname(__file__), 'test_results.json')
            with open(results_file, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving results: {e}")


def main():
    """Main test function."""
    tester = NLPPipelineTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
