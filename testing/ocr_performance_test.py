#!/usr/bin/env python3
"""
OCR Performance Test Module
==========================

Performance testing for the OCR service component.
Tests throughput, accuracy, and processing times across different document types and qualities.
"""

import asyncio
import json
import time
import logging
import random
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class OCRPerformanceTest:
    """OCR performance testing component."""
    
    def __init__(self):
        """Initialize OCR performance test."""
        self.service_url = "http://localhost:8001"  # OCR service URL
        self.test_documents = []
        self.results = []
        
    async def run_performance_test(
        self, 
        num_documents: int = 1000,
        document_types: List[str] = None,
        document_qualities: List[str] = None,
        languages: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive OCR performance test.
        
        Args:
            num_documents: Number of documents to process
            document_types: Types of documents to test
            document_qualities: Quality levels to test
            languages: Languages to test
            
        Returns:
            Performance test results
        """
        logger.info(f"Starting OCR performance test with {num_documents} documents")
        
        # Set defaults
        document_types = document_types or ["image", "pdf", "spreadsheet"]
        document_qualities = document_qualities or ["high", "medium", "low"]
        languages = languages or ["eng"]
        
        start_time = time.time()
        
        # Generate test documents
        self.test_documents = self._generate_test_documents(
            num_documents, document_types, document_qualities
        )
        
        results_by_type = {}
        total_processed = 0
        total_successful = 0
        total_failed = 0
        
        # Test each document type
        for doc_type in document_types:
            logger.info(f"Testing {doc_type} documents...")
            
            type_docs = [doc for doc in self.test_documents if doc["type"] == doc_type]
            if not type_docs:
                continue
            
            type_results = await self._test_document_type(
                type_docs, languages, doc_type
            )
            
            results_by_type[doc_type] = type_results
            
            total_processed += type_results["total_processed"]
            total_successful += type_results["successful"]
            total_failed += type_results["failed"]
        
        total_time = time.time() - start_time
        
        # Calculate overall metrics
        success_rate = total_successful / total_processed if total_processed > 0 else 0
        throughput = total_processed / total_time if total_time > 0 else 0
        
        overall_results = {
            "test_configuration": {
                "num_documents": num_documents,
                "document_types": document_types,
                "document_qualities": document_qualities,
                "languages": languages
            },
            "total_documents": total_processed,
            "successful_documents": total_successful,
            "failed_documents": total_failed,
            "success_rate": success_rate,
            "total_processing_time": total_time,
            "average_time_per_document": total_time / total_processed if total_processed > 0 else 0,
            "throughput_documents_per_second": throughput,
            "results_by_type": results_by_type,
            "performance_summary": self._calculate_performance_summary(results_by_type)
        }
        
        logger.info(f"OCR performance test completed. Success rate: {success_rate:.2%}")
        return overall_results
    
    def _generate_test_documents(
        self, 
        num_documents: int, 
        document_types: List[str], 
        document_qualities: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate test documents for performance testing."""
        documents = []
        
        for i in range(num_documents):
            doc_type = random.choice(document_types)
            quality = random.choice(document_qualities)
            
            # Generate document with realistic characteristics
            document = {
                "id": i,
                "type": doc_type,
                "quality": quality,
                "size": self._get_realistic_file_size(doc_type, quality),
                "complexity": random.choice(["simple", "medium", "complex"]),
                "language": "eng"
            }
            
            # Add type-specific properties
            if doc_type == "image":
                document.update({
                    "resolution": self._get_image_resolution(quality),
                    "format": random.choice(["png", "jpg", "tiff"]),
                    "has_noise": quality == "low",
                    "has_skew": quality in ["medium", "low"]
                })
            elif doc_type == "pdf":
                document.update({
                    "pages": random.randint(1, 10),
                    "has_images": random.choice([True, False]),
                    "text_density": random.choice(["low", "medium", "high"])
                })
            elif doc_type == "spreadsheet":
                document.update({
                    "rows": random.randint(10, 1000),
                    "columns": random.randint(5, 50),
                    "format": random.choice(["xlsx", "csv"]),
                    "has_formulas": random.choice([True, False])
                })
            
            documents.append(document)
        
        return documents
    
    def _get_realistic_file_size(self, doc_type: str, quality: str) -> int:
        """Get realistic file size based on type and quality."""
        base_sizes = {
            "image": {"high": 2048000, "medium": 512000, "low": 128000},
            "pdf": {"high": 5120000, "medium": 1024000, "low": 256000},
            "spreadsheet": {"high": 1024000, "medium": 256000, "low": 64000}
        }
        
        base_size = base_sizes.get(doc_type, {}).get(quality, 100000)
        
        # Add some randomness
        size_variance = random.uniform(0.5, 1.5)
        return int(base_size * size_variance)
    
    def _get_image_resolution(self, quality: str) -> tuple:
        """Get realistic image resolution based on quality."""
        resolutions = {
            "high": (1920, 1080),
            "medium": (1024, 768),
            "low": (640, 480)
        }
        return resolutions.get(quality, (1024, 768))
    
    async def _test_document_type(
        self, 
        documents: List[Dict[str, Any]], 
        languages: List[str], 
        doc_type: str
    ) -> Dict[str, Any]:
        """Test a specific document type."""
        results = []
        
        for document in documents:
            try:
                # Simulate OCR processing time based on document characteristics
                processing_time = self._simulate_ocr_processing_time(document)
                
                # Simulate OCR accuracy based on quality and type
                accuracy = self._simulate_ocr_accuracy(document)
                
                # Simulate confidence score
                confidence = random.uniform(70, 95) if document["quality"] == "high" else \
                           random.uniform(50, 80) if document["quality"] == "medium" else \
                           random.uniform(30, 60)
                
                # Simulate whether processing succeeds
                success = confidence > 40 or random.random() > 0.05  # 95% success rate
                
                result = {
                    "document_id": document["id"],
                    "processing_time": processing_time,
                    "accuracy": accuracy,
                    "confidence": confidence,
                    "success": success,
                    "document_type": doc_type,
                    "document_quality": document["quality"],
                    "file_size": document["size"],
                    "language": document["language"]
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing document {document['id']}: {e}")
                results.append({
                    "document_id": document["id"],
                    "error": str(e),
                    "success": False
                })
        
        # Calculate type-specific metrics
        successful_results = [r for r in results if r.get("success", False)]
        failed_results = [r for r in results if not r.get("success", True)]
        
        total_processed = len(results)
        successful = len(successful_results)
        failed = len(failed_results)
        
        success_rate = successful / total_processed if total_processed > 0 else 0
        
        avg_processing_time = sum(r.get("processing_time", 0) for r in successful_results) / successful if successful > 0 else 0
        avg_accuracy = sum(r.get("accuracy", 0) for r in successful_results) / successful if successful > 0 else 0
        avg_confidence = sum(r.get("confidence", 0) for r in successful_results) / successful if successful > 0 else 0
        
        throughput = total_processed / sum(r.get("processing_time", 0.001) for r in results) if results else 0
        
        return {
            "total_processed": total_processed,
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate,
            "average_processing_time": avg_processing_time,
            "average_accuracy": avg_accuracy,
            "average_confidence": avg_confidence,
            "throughput_docs_per_second": throughput,
            "detailed_results": results,
            "quality_breakdown": self._analyze_quality_breakdown(successful_results)
        }
    
    def _simulate_ocr_processing_time(self, document: Dict[str, Any]) -> float:
        """Simulate OCR processing time based on document characteristics."""
        # Base processing time
        base_time = 0.5  # seconds
        
        # Factor in file size
        size_factor = document["size"] / 1000000  # Normalize to MB
        
        # Factor in document type
        type_multipliers = {
            "image": 1.0,
            "pdf": 2.0,  # PDF processing is slower
            "spreadsheet": 0.5  # Faster for direct text extraction
        }
        
        type_factor = type_multipliers.get(document["type"], 1.0)
        
        # Factor in quality (lower quality takes longer due to preprocessing)
        quality_multipliers = {
            "high": 1.0,
            "medium": 1.2,
            "low": 1.5
        }
        quality_factor = quality_multipliers.get(document["quality"], 1.0)
        
        # Add some randomness
        processing_time = base_time * (1 + size_factor) * type_factor * quality_factor
        processing_time *= random.uniform(0.8, 1.2)  # Add 20% variance
        
        return processing_time
    
    def _simulate_ocr_accuracy(self, document: Dict[str, Any]) -> float:
        """Simulate OCR accuracy based on document characteristics."""
        # Base accuracy
        base_accuracy = 0.85
        
        # Quality factor
        quality_factors = {
            "high": 1.0,
            "medium": 0.85,
            "low": 0.65
        }
        
        quality_factor = quality_factors.get(document["quality"], 1.0)
        
        # Type factor
        type_factors = {
            "image": 0.95,
            "pdf": 0.90,
            "spreadsheet": 0.98
        }
        
        type_factor = type_factors.get(document["type"], 1.0)
        
        # Calculate accuracy
        accuracy = base_accuracy * quality_factor * type_factor
        
        # Add some randomness
        accuracy += random.uniform(-0.05, 0.05)
        
        # Ensure within bounds
        return max(0.0, min(1.0, accuracy))
    
    def _analyze_quality_breakdown(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance breakdown by document quality."""
        quality_groups = {}
        
        for result in results:
            quality = result.get("document_quality", "unknown")
            if quality not in quality_groups:
                quality_groups[quality] = []
            quality_groups[quality].append(result)
        
        breakdown = {}
        for quality, quality_results in quality_groups.items():
            breakdown[quality] = {
                "count": len(quality_results),
                "avg_processing_time": sum(r.get("processing_time", 0) for r in quality_results) / len(quality_results),
                "avg_accuracy": sum(r.get("accuracy", 0) for r in quality_results) / len(quality_results),
                "avg_confidence": sum(r.get("confidence", 0) for r in quality_results) / len(quality_results)
            }
        
        return breakdown
    
    def _calculate_performance_summary(self, results_by_type: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall performance summary."""
        all_times = []
        all_accuracies = []
        all_confidences = []
        
        for type_results in results_by_type.values():
            if "detailed_results" in type_results:
                for result in type_results["detailed_results"]:
                    if result.get("success", False):
                        all_times.append(result.get("processing_time", 0))
                        all_accuracies.append(result.get("accuracy", 0))
                        all_confidences.append(result.get("confidence", 0))
        
        return {
            "overall_avg_processing_time": np.mean(all_times) if all_times else 0,
            "overall_avg_accuracy": np.mean(all_accuracies) if all_accuracies else 0,
            "overall_avg_confidence": np.mean(all_confidences) if all_confidences else 0,
            "processing_time_std": np.std(all_times) if all_times else 0,
            "min_processing_time": min(all_times) if all_times else 0,
            "max_processing_time": max(all_times) if all_times else 0
        }
    
    async def simulate_ocr_processing(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate OCR processing for integration testing."""
        processing_time = self._simulate_ocr_processing_time(document)
        await asyncio.sleep(min(processing_time, 0.1))  # Cap sleep time for testing
        
        accuracy = self._simulate_ocr_accuracy(document)
        confidence = random.uniform(70, 95) if document.get("quality") == "high" else \
                    random.uniform(50, 80) if document.get("quality") == "medium" else \
                    random.uniform(30, 60)
        
        # Generate simulated extracted text
        text_length = int(processing_time * 500)  # 500 chars per second
        extracted_text = "Lorem ipsum dolor sit amet " * (text_length // 27 + 1)
        
        return {
            "text": extracted_text[:text_length],
            "confidence": confidence,
            "accuracy": accuracy,
            "processing_time": processing_time,
            "success": confidence > 40
        }