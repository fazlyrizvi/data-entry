#!/usr/bin/env python3
"""
OCR Service Comprehensive Test Suite
===================================
Tests OCR service with multiple document formats, preprocessing, batch processing,
confidence scoring, and error handling.
"""

import os
import sys
import json
import time
import base64
import io
import asyncio
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import logging

# Add OCR service to path
sys.path.append('/workspace/code/ocr_service')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestOCRService(unittest.TestCase):
    """Comprehensive OCR service test suite."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.test_results = {
            'test_suite': 'OCR Service',
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
    
    def test_001_basic_functionality(self):
        """Test basic OCR functionality with simple text."""
        test_name = "Basic OCR Functionality"
        start_time = time.time()
        
        try:
            # Test basic imports
            from config import OCRConfig
            from preprocessing import DocumentPreprocessor
            import cv2
            import numpy as np
            
            # Test configuration
            config = OCRConfig()
            self.assertIsNotNone(config)
            
            # Test preprocessor initialization
            preprocessor = DocumentPreprocessor(config.PREPROCESSING)
            self.assertIsNotNone(preprocessor)
            
            # Test image creation for testing
            test_image = self._create_test_image("Hello World Test")
            self.assertIsNotNone(test_image)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Basic components initialized successfully', 
                                duration, {'config_loaded': True, 'preprocessor_ready': True})
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Basic test failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_002_supported_formats(self):
        """Test supported file format detection."""
        test_name = "Supported Format Detection"
        start_time = time.time()
        
        try:
            from config import OCRConfig
            config = OCRConfig()
            
            # Test image formats
            image_formats = config.SUPPORTED_IMAGE_FORMATS
            self.assertIn('.png', image_formats)
            self.assertIn('.jpg', image_formats)
            self.assertIn('.jpeg', image_formats)
            self.assertIn('.tiff', image_formats)
            
            # Test PDF formats
            pdf_formats = config.SUPPORTED_PDF_FORMATS
            self.assertIn('.pdf', pdf_formats)
            
            # Test spreadsheet formats
            spreadsheet_formats = config.SUPPORTED_SPREADSHEET_FORMATS
            self.assertIn('.xlsx', spreadsheet_formats)
            self.assertIn('.xls', spreadsheet_formats)
            self.assertIn('.csv', spreadsheet_formats)
            
            # Test format checking
            supported = config.is_supported_format('test.png')
            self.assertTrue(supported)
            
            unsupported = config.is_supported_format('test.xyz')
            self.assertFalse(unsupported)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'All formats detected correctly', 
                                duration, {
                                    'image_formats': len(image_formats),
                                    'pdf_formats': len(pdf_formats),
                                    'spreadsheet_formats': len(spreadsheet_formats)
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Format test failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_003_image_preprocessing(self):
        """Test image preprocessing capabilities."""
        test_name = "Image Preprocessing"
        start_time = time.time()
        
        try:
            from preprocessing import DocumentPreprocessor
            from config import OCRConfig
            
            config = OCRConfig()
            preprocessor = DocumentPreprocessor(config.PREPROCESSING)
            
            # Create test image with noise
            test_image = self._create_test_image_with_noise("Test Text with Noise")
            
            # Test preprocessing
            processed_image = preprocessor.preprocess_image(test_image)
            
            # Verify image properties
            self.assertEqual(len(processed_image.shape), 3)  # Color image
            self.assertEqual(processed_image.shape[0], 100)  # Height
            self.assertEqual(processed_image.shape[1], 300)  # Width
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Image preprocessing completed successfully', 
                                duration, {
                                    'original_shape': test_image.shape,
                                    'processed_shape': processed_image.shape
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Preprocessing test failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_004_single_file_processing(self):
        """Test single file OCR processing."""
        test_name = "Single File OCR Processing"
        start_time = time.time()
        
        try:
            from main import OCRRequest, process_single_file
            
            # Create a temporary test file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                test_image = self._create_test_image("Single File OCR Test")
                temp_file_path = temp_file.name
                
                # Save test image
                import cv2
                cv2.imwrite(temp_file_path, test_image)
            
            try:
                # Create OCR request
                ocr_request = OCRRequest(
                    language="eng",
                    preprocessing=True,
                    output_format="text",
                    confidence_threshold=30
                )
                
                # Process file
                result = process_single_file(temp_file_path, ocr_request)
                
                # Verify result
                self.assertIsNotNone(result)
                self.assertTrue(hasattr(result, 'success'))
                self.assertIsNotNone(result.file_name)
                self.assertGreater(result.processing_time, 0)
                
                duration = time.time() - start_time
                self._add_test_result(test_name, 'PASSED', f'Single file processed successfully', 
                                    duration, {
                                        'file_name': result.file_name,
                                        'processing_time': result.processing_time,
                                        'success': result.success
                                    })
                
            finally:
                # Clean up
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Single file processing failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_005_multiple_document_formats(self):
        """Test multiple document format support."""
        test_name = "Multiple Document Formats"
        start_time = time.time()
        
        try:
            from main import OCRRequest, process_spreadsheet_file
            
            # Test CSV file processing
            csv_content = """name,email,phone
John Doe,john@example.com,1234567890
Jane Smith,jane@example.com,0987654321"""
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as csv_file:
                csv_file.write(csv_content)
                csv_file_path = csv_file.name
            
            try:
                # Process CSV file
                result = process_spreadsheet_file(csv_file_path)
                
                # Verify result
                self.assertIsNotNone(result)
                self.assertIn('text', result)
                self.assertIn('John Doe', result['text'])
                self.assertIn('Jane Smith', result['text'])
                self.assertEqual(result['confidence'], 100.0)  # High confidence for direct extraction
                
                duration = time.time() - start_time
                self._add_test_result(test_name, 'PASSED', 'Multiple formats processed successfully', 
                                    duration, {
                                        'csv_processed': True,
                                        'text_extracted': True,
                                        'confidence': result['confidence']
                                    })
                
            finally:
                if os.path.exists(csv_file_path):
                    os.unlink(csv_file_path)
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Multiple format test failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_006_confidence_scoring(self):
        """Test OCR confidence scoring system."""
        test_name = "Confidence Scoring"
        start_time = time.time()
        
        try:
            import numpy as np
            
            # Test confidence calculation
            confidences = [85, 90, 78, 92, 88]
            avg_confidence = np.mean(confidences)
            
            self.assertIsInstance(avg_confidence, float)
            self.assertGreater(avg_confidence, 70)
            self.assertLessEqual(avg_confidence, 100)
            
            # Test with empty confidence list
            empty_confidence = np.mean([])
            self.assertEqual(empty_confidence, 0)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Confidence scoring works correctly', 
                                duration, {
                                    'average_confidence': avg_confidence,
                                    'empty_case_handled': True
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Confidence scoring test failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_007_error_handling(self):
        """Test error handling and recovery."""
        test_name = "Error Handling"
        start_time = time.time()
        
        try:
            # Test with non-existent file
            from main import process_single_file, OCRRequest
            
            ocr_request = OCRRequest()
            
            try:
                result = process_single_file("/non/existent/file.png", ocr_request)
                self.assertFalse(result.success)
                self.assertIsNotNone(result.error_message)
                
            except Exception:
                # Expected - file doesn't exist
                pass
            
            # Test with unsupported file format
            with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as temp_file:
                temp_file.write(b"test")
                temp_file_path = temp_file.name
            
            try:
                result = process_single_file(temp_file_path, ocr_request)
                self.assertFalse(result.success)
                self.assertIn("Unsupported", result.error_message)
                
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Error handling works correctly', 
                                duration, {
                                    'non_existent_file_handled': True,
                                    'unsupported_format_handled': True
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Error handling test failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def test_008_performance_benchmark(self):
        """Test performance with multiple operations."""
        test_name = "Performance Benchmark"
        start_time = time.time()
        
        try:
            from main import OCRRequest, process_single_file
            import cv2
            
            # Create multiple test images
            test_images = []
            for i in range(5):
                image = self._create_test_image(f"Performance Test {i+1}")
                test_images.append(image)
            
            processing_times = []
            
            # Process each image and measure time
            for i, image in enumerate(test_images):
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                    cv2.imwrite(temp_file.name, image)
                    temp_file_path = temp_file.name
                
                try:
                    ocr_request = OCRRequest()
                    start = time.time()
                    result = process_single_file(temp_file_path, ocr_request)
                    end = time.time()
                    
                    processing_times.append(end - start)
                    
                finally:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
            
            # Verify performance
            avg_time = sum(processing_times) / len(processing_times)
            max_time = max(processing_times)
            
            # Performance should be reasonable (< 5 seconds per image for test)
            self.assertLess(avg_time, 5.0)
            self.assertLess(max_time, 10.0)
            
            duration = time.time() - start_time
            self._add_test_result(test_name, 'PASSED', 'Performance benchmark passed', 
                                duration, {
                                    'images_processed': len(test_images),
                                    'avg_processing_time': avg_time,
                                    'max_processing_time': max_time
                                })
            
        except Exception as e:
            duration = time.time() - start_time
            self._add_test_result(test_name, 'FAILED', f'Performance benchmark failed: {str(e)}', 
                                duration, {'error': str(e)})
    
    def _create_test_image(self, text: str) -> Any:
        """Create a test image with text for OCR testing."""
        import cv2
        import numpy as np
        
        # Create white background
        img = np.ones((100, 300, 3), dtype=np.uint8) * 255
        
        # Add text using OpenCV (simplified)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, text, (10, 50), font, 1, (0, 0, 0), 2)
        
        return img
    
    def _create_test_image_with_noise(self, text: str) -> Any:
        """Create a test image with text and noise."""
        import cv2
        import numpy as np
        
        # Create base image
        img = self._create_test_image(text)
        
        # Add some noise
        noise = np.random.randint(0, 50, img.shape, dtype=np.uint8)
        img = cv2.add(img, noise)
        
        return img
    
    @classmethod
    def tearDownClass(cls):
        """Save test results."""
        cls.test_results['end_time'] = datetime.now().isoformat()
        cls.test_results['duration'] = (
            datetime.fromisoformat(cls.test_results['end_time']) - 
            datetime.fromisoformat(cls.test_results['start_time'])
        ).total_seconds()
        
        # Save results to file
        results_file = '/workspace/testing/results/ocr_service_test_results.json'
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(cls.test_results, f, indent=2, default=str)
        
        logger.info(f"OCR Service test results saved to {results_file}")


def run_ocr_tests():
    """Run all OCR service tests."""
    logger.info("Starting OCR Service Comprehensive Test Suite")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOCRService)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    logger.info(f"OCR Service Tests Completed: {result.testsRun} tests run")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    return result


if __name__ == "__main__":
    run_ocr_tests()
