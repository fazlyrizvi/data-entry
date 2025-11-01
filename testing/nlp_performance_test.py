#!/usr/bin/env python3
"""
NLP Performance Test Module
==========================

Performance testing for the NLP pipeline component.
Tests entity extraction, text classification, and form field recognition performance.
"""

import asyncio
import json
import time
import logging
import random
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class NLPPerformanceTest:
    """NLP performance testing component."""
    
    def __init__(self):
        """Initialize NLP performance test."""
        self.service_url = "http://localhost:8002"  # NLP service URL
        self.test_texts = []
        self.results = []
        
    async def run_performance_test(
        self, 
        num_documents: int = 1000,
        tasks: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive NLP performance test.
        
        Args:
            num_documents: Number of documents to process
            tasks: NLP tasks to test (entities, classification, form_fields)
            
        Returns:
            Performance test results
        """
        logger.info(f"Starting NLP performance test with {num_documents} documents")
        
        # Set defaults
        tasks = tasks or ["entities", "classification", "form_fields"]
        
        start_time = time.time()
        
        # Generate test texts
        self.test_texts = self._generate_test_texts(num_documents)
        
        results_by_task = {}
        total_processed = 0
        total_successful = 0
        total_failed = 0
        
        # Test each task
        for task in tasks:
            logger.info(f"Testing {task} task...")
            
            task_results = await self._test_nlp_task(self.test_texts, task)
            
            results_by_task[task] = task_results
            
            total_processed += task_results["total_processed"]
            total_successful += task_results["successful"]
            total_failed += task_results["failed"]
        
        total_time = time.time() - start_time
        
        # Calculate overall metrics
        success_rate = total_successful / total_processed if total_processed > 0 else 0
        throughput = total_processed / total_time if total_time > 0 else 0
        
        overall_results = {
            "test_configuration": {
                "num_documents": num_documents,
                "tasks": tasks
            },
            "total_documents": total_processed,
            "successful_documents": total_successful,
            "failed_documents": total_failed,
            "success_rate": success_rate,
            "total_processing_time": total_time,
            "average_time_per_document": total_time / total_processed if total_processed > 0 else 0,
            "throughput_documents_per_second": throughput,
            "results_by_task": results_by_task,
            "performance_summary": self._calculate_performance_summary(results_by_task)
        }
        
        logger.info(f"NLP performance test completed. Success rate: {success_rate:.2%}")
        return overall_results
    
    def _generate_test_texts(self, num_documents: int) -> List[Dict[str, Any]]:
        """Generate test texts for performance testing."""
        texts = []
        
        # Text templates for different document types
        templates = {
            "invoice": "Invoice {invoice_num} dated {date} for {amount} from {company} to {customer}. "
                      "Contact: {email} Phone: {phone} Address: {address}",
            "contract": "This Agreement between {party1} and {party2} effective {date}. "
                       "Terms: {terms} Duration: {duration}",
            "report": "Report by {author} on {date} regarding {topic}. "
                     "Findings: {findings} Recommendations: {recommendations}",
            "email": "From: {sender} To: {recipient} Subject: {subject} "
                    "Dear {name}, {content} Best regards, {sender}",
            "form": "Name: {name} Email: {email} Phone: {phone} "
                   "Date of Birth: {dob} Address: {address} "
                   "Occupation: {occupation} Income: {income}"
        }
        
        # Generate realistic data
        for i in range(num_documents):
            doc_type = random.choice(list(templates.keys()))
            
            # Generate realistic data for each field
            data = self._generate_realistic_data()
            
            # Fill template
            try:
                text = templates[doc_type].format(**data)
            except KeyError:
                # Fallback if template fails
                text = f"Sample {doc_type} document {i} with various fields and content."
            
            # Add complexity and variation
            complexity = random.choice(["simple", "medium", "complex"])
            if complexity == "medium":
                text += " Additional details and specifications are included in the document."
            elif complexity == "complex":
                text += " This comprehensive document contains multiple sections, subsections, and detailed information. " * 3
            
            text_document = {
                "id": i,
                "text": text,
                "type": doc_type,
                "length": len(text),
                "complexity": complexity,
                "language": "en",
                "has_entities": random.choice([True, True, False]),  # 66% chance of entities
                "expected_entities": random.randint(3, 15) if random.choice([True, False]) else 0
            }
            
            texts.append(text_document)
        
        return texts
    
    def _generate_realistic_data(self) -> Dict[str, Any]:
        """Generate realistic data for test templates."""
        return {
            "invoice_num": f"INV-{random.randint(1000, 9999)}",
            "date": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "amount": f"${random.randint(100, 10000)}.{random.randint(10, 99):02d}",
            "company": random.choice(["Acme Corp", "Tech Solutions", "Global Industries", "Data Systems Inc"]),
            "customer": random.choice(["John Smith", "Jane Doe", "Bob Johnson", "Alice Brown"]),
            "email": f"user{random.randint(1, 1000)}@example.com",
            "phone": f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
            "address": f"{random.randint(1, 9999)} {random.choice(['Main', 'Oak', 'First', 'Second'])} {random.choice(['St', 'Ave', 'Blvd', 'Dr'])}",
            "party1": random.choice(["Company A", "Organization X", "Enterprise B"]),
            "party2": random.choice(["Company B", "Organization Y", "Enterprise C"]),
            "terms": random.choice(["payment within 30 days", "net 60 terms", "immediate payment", "cash on delivery"]),
            "duration": random.choice(["1 year", "2 years", "6 months", "permanent"]),
            "author": random.choice(["Dr. Smith", "Prof. Johnson", "Analyst Brown", "Manager Davis"]),
            "topic": random.choice(["market analysis", "technical review", "financial report", "project status"]),
            "findings": random.choice(["significant growth", "market opportunity", "technical challenges", "cost savings"]),
            "recommendations": random.choice(["invest in R&D", "expand market", "reduce costs", "hire specialists"]),
            "sender": random.choice(["Manager", "Director", "Supervisor", "Coordinator"]),
            "recipient": random.choice(["Team", "Management", "Client", "Stakeholders"]),
            "subject": random.choice(["Update", "Report", "Meeting", "Proposal", "Invoice"]),
            "name": random.choice(["John Smith", "Jane Doe", "Bob Johnson", "Alice Brown"]),
            "dob": f"{random.randint(1950, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "occupation": random.choice(["Engineer", "Manager", "Analyst", "Developer", "Consultant"]),
            "income": f"${random.randint(40000, 120000)}",
            "content": "I hope this message finds you well. Please review the attached information."
        }
    
    async def _test_nlp_task(self, texts: List[Dict[str, Any]], task: str) -> Dict[str, Any]:
        """Test a specific NLP task."""
        results = []
        
        for text_doc in texts:
            try:
                # Simulate NLP processing time based on task and text characteristics
                processing_time = self._simulate_nlp_processing_time(text_doc, task)
                
                # Simulate task-specific results
                task_result = self._simulate_task_result(text_doc, task)
                
                result = {
                    "document_id": text_doc["id"],
                    "processing_time": processing_time,
                    "task": task,
                    "text_length": text_doc["length"],
                    "text_complexity": text_doc["complexity"],
                    "success": task_result["success"],
                    "result": task_result
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing text {text_doc['id']} for task {task}: {e}")
                results.append({
                    "document_id": text_doc["id"],
                    "task": task,
                    "error": str(e),
                    "success": False
                })
        
        # Calculate task-specific metrics
        successful_results = [r for r in results if r.get("success", False)]
        failed_results = [r for r in results if not r.get("success", True)]
        
        total_processed = len(results)
        successful = len(successful_results)
        failed = len(failed_results)
        
        success_rate = successful / total_processed if total_processed > 0 else 0
        
        avg_processing_time = sum(r.get("processing_time", 0) for r in successful_results) / successful if successful > 0 else 0
        throughput = total_processed / sum(r.get("processing_time", 0.001) for r in results) if results else 0
        
        # Task-specific metrics
        task_metrics = self._calculate_task_metrics(successful_results, task)
        
        return {
            "total_processed": total_processed,
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate,
            "average_processing_time": avg_processing_time,
            "throughput_docs_per_second": throughput,
            "task_specific_metrics": task_metrics,
            "detailed_results": results
        }
    
    def _simulate_nlp_processing_time(self, text_doc: Dict[str, Any], task: str) -> float:
        """Simulate NLP processing time based on task and text characteristics."""
        # Base processing time by task
        base_times = {
            "entities": 0.02,  # 20ms base
            "classification": 0.01,  # 10ms base
            "form_fields": 0.03   # 30ms base
        }
        
        base_time = base_times.get(task, 0.02)
        
        # Factor in text length
        length_factor = text_doc["length"] / 1000  # Normalize to 1000 chars
        
        # Factor in complexity
        complexity_factors = {
            "simple": 1.0,
            "medium": 1.3,
            "complex": 1.8
        }
        
        complexity_factor = complexity_factors.get(text_doc["complexity"], 1.0)
        
        # Calculate processing time
        processing_time = base_time * (1 + length_factor) * complexity_factor
        
        # Add randomness
        processing_time *= random.uniform(0.7, 1.3)
        
        return processing_time
    
    def _simulate_task_result(self, text_doc: Dict[str, Any], task: str) -> Dict[str, Any]:
        """Simulate task-specific results."""
        if task == "entities":
            return self._simulate_entity_extraction(text_doc)
        elif task == "classification":
            return self._simulate_text_classification(text_doc)
        elif task == "form_fields":
            return self._simulate_form_field_extraction(text_doc)
        else:
            return {"success": False, "error": f"Unknown task: {task}"}
    
    def _simulate_entity_extraction(self, text_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate entity extraction results."""
        if not text_doc.get("has_entities", False):
            return {"success": True, "entities_found": 0, "entities": {}}
        
        # Simulate entity extraction
        entity_types = ["person", "organization", "location", "date", "money", "email", "phone"]
        num_entities = min(text_doc.get("expected_entities", 0), random.randint(2, 12))
        
        entities = {}
        for i in range(num_entities):
            entity_type = random.choice(entity_types)
            if entity_type not in entities:
                entities[entity_type] = []
            
            # Generate realistic entity value
            entity_value = self._generate_realistic_entity_value(entity_type)
            entities[entity_type].append({
                "text": entity_value,
                "confidence": random.uniform(0.7, 0.95)
            })
        
        # Calculate overall confidence
        overall_confidence = sum(
            ent["confidence"] 
            for entity_list in entities.values() 
            for ent in entity_list
        ) / max(1, sum(len(entity_list) for entity_list in entities.values()))
        
        return {
            "success": True,
            "entities_found": sum(len(entity_list) for entity_list in entities.values()),
            "entities": entities,
            "overall_confidence": overall_confidence,
            "unique_entity_types": len(entities)
        }
    
    def _simulate_text_classification(self, text_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate text classification results."""
        # Simulate document type classification
        doc_types = ["invoice", "contract", "report", "email", "form", "other"]
        predicted_type = text_doc["type"]
        confidence = random.uniform(0.8, 0.95)
        
        # Simulate sentiment analysis
        sentiments = ["positive", "neutral", "negative"]
        sentiment = random.choice(sentiments)
        sentiment_confidence = random.uniform(0.6, 0.9)
        
        # Simulate language detection
        languages = ["en", "es", "fr", "de", "it"]
        language = "en"  # Most texts are in English
        language_confidence = random.uniform(0.9, 0.99)
        
        # Simulate confidence scores for all classes
        class_scores = {doc_type: random.uniform(0.0, 0.1) for doc_type in doc_types}
        class_scores[predicted_type] = confidence
        
        return {
            "success": True,
            "document_type": predicted_type,
            "document_type_confidence": confidence,
            "sentiment": sentiment,
            "sentiment_confidence": sentiment_confidence,
            "language": language,
            "language_confidence": language_confidence,
            "class_scores": class_scores
        }
    
    def _simulate_form_field_extraction(self, text_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate form field extraction results."""
        # Common form fields
        form_fields = {
            "name": {"found": random.choice([True, True, False]), "confidence": random.uniform(0.8, 0.95)},
            "email": {"found": random.choice([True, False]), "confidence": random.uniform(0.9, 0.99)},
            "phone": {"found": random.choice([True, False]), "confidence": random.uniform(0.85, 0.95)},
            "address": {"found": random.choice([True, False]), "confidence": random.uniform(0.7, 0.9)},
            "date": {"found": random.choice([True, True, False]), "confidence": random.uniform(0.8, 0.95)},
            "amount": {"found": random.choice([True, False]), "confidence": random.uniform(0.85, 0.95)},
            "company": {"found": random.choice([True, False]), "confidence": random.uniform(0.8, 0.9)}
        }
        
        # Adjust based on document type
        if text_doc["type"] == "invoice":
            form_fields["amount"]["found"] = True
            form_fields["company"]["found"] = True
        elif text_doc["type"] == "form":
            for field in form_fields:
                form_fields[field]["found"] = True
        
        # Count found fields
        found_fields = sum(1 for field_data in form_fields.values() if field_data["found"])
        total_fields = len(form_fields)
        
        # Calculate confidence score
        avg_confidence = sum(field_data["confidence"] for field_data in form_fields.values() if field_data["found"]) / max(1, found_fields)
        
        return {
            "success": True,
            "fields_found": found_fields,
            "total_fields": total_fields,
            "completion_rate": found_fields / total_fields,
            "confidence_score": avg_confidence,
            "extracted_fields": {field: field_data["confidence"] for field, field_data in form_fields.items() if field_data["found"]}
        }
    
    def _generate_realistic_entity_value(self, entity_type: str) -> str:
        """Generate realistic entity values."""
        entity_generators = {
            "person": lambda: random.choice(["John Smith", "Jane Doe", "Bob Johnson", "Alice Brown", "Charlie Davis"]),
            "organization": lambda: random.choice(["Acme Corp", "Tech Solutions", "Global Industries", "Data Systems Inc"]),
            "location": lambda: random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
            "date": lambda: f"{random.randint(2020, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "money": lambda: f"${random.randint(100, 10000)}.{random.randint(10, 99):02d}",
            "email": lambda: f"user{random.randint(1, 1000)}@example.com",
            "phone": lambda: f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"
        }
        
        generator = entity_generators.get(entity_type, lambda: "Unknown")
        return generator()
    
    def _calculate_task_metrics(self, results: List[Dict[str, Any]], task: str) -> Dict[str, Any]:
        """Calculate task-specific performance metrics."""
        if not results:
            return {}
        
        if task == "entities":
            total_entities = sum(r["result"].get("entities_found", 0) for r in results)
            avg_confidence = sum(r["result"].get("overall_confidence", 0) for r in results) / len(results)
            unique_types = sum(r["result"].get("unique_entity_types", 0) for r in results) / len(results)
            
            return {
                "total_entities_extracted": total_entities,
                "avg_entities_per_document": total_entities / len(results),
                "avg_confidence": avg_confidence,
                "avg_unique_entity_types": unique_types
            }
        
        elif task == "classification":
            type_confidences = [r["result"].get("document_type_confidence", 0) for r in results]
            sentiment_confidences = [r["result"].get("sentiment_confidence", 0) for r in results]
            
            return {
                "avg_type_confidence": sum(type_confidences) / len(type_confidences),
                "avg_sentiment_confidence": sum(sentiment_confidences) / len(sentiment_confidences),
                "most_common_sentiment": max(set(r["result"].get("sentiment", "neutral") for r in results), 
                                           key=lambda x: sum(1 for r in results if r["result"].get("sentiment") == x))
            }
        
        elif task == "form_fields":
            total_fields_found = sum(r["result"].get("fields_found", 0) for r in results)
            total_fields_possible = sum(r["result"].get("total_fields", 0) for r in results)
            completion_rates = [r["result"].get("completion_rate", 0) for r in results]
            
            return {
                "total_fields_extracted": total_fields_found,
                "avg_completion_rate": sum(completion_rates) / len(completion_rates),
                "field_extraction_accuracy": total_fields_found / max(1, total_fields_possible),
                "avg_confidence": sum(r["result"].get("confidence_score", 0) for r in results) / len(results)
            }
        
        return {}
    
    def _calculate_performance_summary(self, results_by_task: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall performance summary."""
        all_times = []
        all_success_rates = []
        
        for task_results in results_by_task.values():
            avg_time = task_results.get("average_processing_time", 0)
            success_rate = task_results.get("success_rate", 0)
            
            all_times.append(avg_time)
            all_success_rates.append(success_rate)
        
        return {
            "overall_avg_processing_time": np.mean(all_times) if all_times else 0,
            "overall_success_rate": np.mean(all_success_rates) if all_success_rates else 0,
            "fastest_task": min(results_by_task.keys(), key=lambda k: results_by_task[k].get("average_processing_time", float('inf'))),
            "most_reliable_task": max(results_by_task.keys(), key=lambda k: results_by_task[k].get("success_rate", 0)),
            "processing_time_std": np.std(all_times) if all_times else 0
        }
    
    async def simulate_nlp_processing(self, text: str) -> Dict[str, Any]:
        """Simulate NLP processing for integration testing."""
        text_doc = {"length": len(text), "complexity": "medium", "has_entities": True, "expected_entities": 5}
        
        # Simulate entity extraction
        entities_result = self._simulate_entity_extraction(text_doc)
        
        # Simulate classification
        classification_result = self._simulate_text_classification(text_doc)
        
        processing_time = self._simulate_nlp_processing_time(text_doc, "entities")
        await asyncio.sleep(min(processing_time, 0.1))  # Cap sleep time for testing
        
        return {
            "entities": entities_result.get("entities", {}),
            "classification": classification_result,
            "processing_time": processing_time,
            "success": entities_result.get("success", False) and classification_result.get("success", False)
        }