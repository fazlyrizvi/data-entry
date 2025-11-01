#!/usr/bin/env python3
"""
Parallel Processing Performance Test Module
==========================================

Performance testing for the parallel processing system.
Tests throughput, worker efficiency, and queue management.
"""

import asyncio
import json
import time
import logging
import random
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class ParallelProcessingTest:
    """Parallel processing performance testing component."""
    
    def __init__(self):
        """Initialize parallel processing performance test."""
        self.test_documents = []
        self.results = []
        
    async def run_performance_test(
        self, 
        num_documents: int = 1000,
        num_workers: int = 4,
        test_type: str = "throughput"
    ) -> Dict[str, Any]:
        """
        Run comprehensive parallel processing performance test.
        
        Args:
            num_documents: Number of documents to process
            num_workers: Number of worker processes
            test_type: Type of test (throughput, efficiency, scalability)
            
        Returns:
            Performance test results
        """
        logger.info(f"Starting parallel processing test with {num_documents} documents and {num_workers} workers")
        
        start_time = time.time()
        
        # Generate test documents
        self.test_documents = self._generate_test_documents(num_documents)
        
        # Run the specified test
        if test_type == "throughput":
            results = await self._test_throughput(num_workers)
        elif test_type == "efficiency":
            results = await self._test_worker_efficiency(num_workers)
        elif test_type == "scalability":
            results = await self._test_scalability(num_workers)
        else:
            results = await self._test_throughput(num_workers)
        
        total_time = time.time() - start_time
        
        # Calculate performance metrics
        processed_docs = len([r for r in results["detailed_results"] if r.get("success", False)])
        successful_docs = sum(1 for r in results["detailed_results"] if r.get("success", False))
        
        success_rate = successful_docs / processed_docs if processed_docs > 0 else 0
        throughput = processed_docs / total_time if total_time > 0 else 0
        
        overall_results = {
            "test_configuration": {
                "num_documents": num_documents,
                "num_workers": num_workers,
                "test_type": test_type
            },
            "total_documents": num_documents,
            "processed_documents": processed_docs,
            "successful_documents": successful_docs,
            "failed_documents": processed_docs - successful_docs,
            "success_rate": success_rate,
            "total_processing_time": total_time,
            "average_time_per_document": total_time / processed_docs if processed_docs > 0 else 0,
            "throughput_documents_per_second": throughput,
            "parallel_efficiency": self._calculate_parallel_efficiency(results, num_workers),
            "worker_utilization": self._calculate_worker_utilization(results),
            "queue_performance": self._calculate_queue_performance(results),
            "detailed_results": results["detailed_results"],
            "performance_metrics": results.get("performance_metrics", {})
        }
        
        logger.info(f"Parallel processing test completed. Success rate: {success_rate:.2%}")
        return overall_results
    
    def _generate_test_documents(self, num_documents: int) -> List[Dict[str, Any]]:
        """Generate test documents for parallel processing."""
        documents = []
        
        for i in range(num_documents):
            # Vary processing complexity
            complexity = random.choices(
                population=["simple", "medium", "complex"],
                weights=[0.6, 0.3, 0.1]  # 60% simple, 30% medium, 10% complex
            )[0]
            
            # Base processing time by complexity
            base_times = {
                "simple": 0.1,
                "medium": 0.5,
                "complex": 1.5
            }
            
            # Document characteristics
            document = {
                "id": i,
                "complexity": complexity,
                "base_processing_time": base_times[complexity],
                "has_dependencies": random.choice([False, False, True]),  # 33% chance
                "requires_special_handling": random.choice([False, False, False, True]),  # 25% chance
                "data_size": random.randint(1000, 50000),  # bytes
                "priority": random.choice(["low", "normal", "high"])
            }
            
            documents.append(document)
        
        return documents
    
    async def _test_throughput(self, num_workers: int) -> Dict[str, Any]:
        """Test processing throughput with multiple workers."""
        logger.info(f"Testing throughput with {num_workers} workers")
        
        start_time = time.time()
        detailed_results = []
        worker_metrics = {i: {"documents_processed": 0, "total_time": 0, "errors": 0} for i in range(num_workers)}
        
        # Create worker tasks
        worker_tasks = []
        for i in range(num_workers):
            worker_docs = self.test_documents[i::num_workers]  # Distribute documents evenly
            task = asyncio.create_task(self._process_worker_batch(i, worker_docs))
            worker_tasks.append(task)
        
        # Wait for all workers to complete
        worker_results = await asyncio.gather(*worker_tasks, return_exceptions=True)
        
        # Collect results
        for worker_id, result in enumerate(worker_results):
            if isinstance(result, Exception):
                logger.error(f"Worker {worker_id} failed: {result}")
                worker_metrics[worker_id]["errors"] += 1
            else:
                detailed_results.extend(result["processed_documents"])
                worker_metrics[worker_id]["documents_processed"] = result["count"]
                worker_metrics[worker_id]["total_time"] = result["total_time"]
        
        processing_time = time.time() - start_time
        
        # Calculate performance metrics
        successful_docs = len([r for r in detailed_results if r.get("success", False)])
        failed_docs = len([r for r in detailed_results if not r.get("success", True)])
        
        return {
            "test_type": "throughput",
            "processing_time": processing_time,
            "detailed_results": detailed_results,
            "worker_metrics": worker_metrics,
            "performance_metrics": {
                "total_processed": len(detailed_results),
                "successful": successful_docs,
                "failed": failed_docs,
                "success_rate": successful_docs / len(detailed_results) if detailed_results else 0,
                "avg_processing_time_per_document": processing_time / len(self.test_documents) if self.test_documents else 0,
                "workers_active": len([w for w in worker_metrics.values() if w["documents_processed"] > 0])
            }
        }
    
    async def _test_worker_efficiency(self, num_workers: int) -> Dict[str, Any]:
        """Test worker efficiency and load balancing."""
        logger.info(f"Testing worker efficiency with {num_workers} workers")
        
        start_time = time.time()
        detailed_results = []
        worker_loads = {i: 0 for i in range(num_workers)}
        
        # Process documents with load balancing
        semaphore = asyncio.Semaphore(num_workers)
        
        async def process_document_with_worker(doc):
            worker_id = min(worker_loads.keys(), key=lambda k: worker_loads[k])
            worker_loads[worker_id] += 1
            
            async with semaphore:
                result = await self._process_single_document(doc, worker_id)
                return result
        
        # Process all documents concurrently
        tasks = [process_document_with_worker(doc) for doc in self.test_documents]
        detailed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        detailed_results = [r for r in detailed_results if not isinstance(r, Exception)]
        
        processing_time = time.time() - start_time
        
        # Calculate efficiency metrics
        worker_efficiencies = []
        for worker_id, load in worker_loads.items():
            if load > 0:
                worker_docs = [r for r in detailed_results if r.get("assigned_worker") == worker_id]
                avg_time = sum(r.get("processing_time", 0) for r in worker_docs) / len(worker_docs)
                efficiency = load / avg_time if avg_time > 0 else 0
                worker_efficiencies.append(efficiency)
        
        return {
            "test_type": "efficiency",
            "processing_time": processing_time,
            "detailed_results": detailed_results,
            "worker_loads": worker_loads,
            "performance_metrics": {
                "total_processed": len(detailed_results),
                "load_balance_variance": np.var(list(worker_loads.values())),
                "worker_efficiency_avg": np.mean(worker_efficiencies) if worker_efficiencies else 0,
                "utilization_rate": sum(worker_loads.values()) / (num_workers * len(self.test_documents))
            }
        }
    
    async def _test_scalability(self, num_workers: int) -> Dict[str, Any]:
        """Test system scalability with different worker counts."""
        logger.info(f"Testing scalability from 1 to {num_workers} workers")
        
        scalability_results = []
        
        for worker_count in range(1, num_workers + 1):
            logger.info(f"Testing with {worker_count} workers")
            
            # Test with current worker count
            test_docs = self.test_documents[:1000]  # Use subset for scalability test
            worker_docs = test_docs[worker_count:]  # Adjust for worker count
            
            start_time = time.time()
            
            worker_tasks = []
            for i in range(worker_count):
                docs = test_docs[i::worker_count]
                task = asyncio.create_task(self._process_worker_batch(i, docs))
                worker_tasks.append(task)
            
            results = await asyncio.gather(*worker_tasks, return_exceptions=True)
            
            processing_time = time.time() - start_time
            processed_count = sum(
                len(r["processed_documents"]) if not isinstance(r, Exception) else 0 
                for r in results
            )
            
            throughput = processed_count / processing_time if processing_time > 0 else 0
            
            scalability_results.append({
                "worker_count": worker_count,
                "processing_time": processing_time,
                "documents_processed": processed_count,
                "throughput": throughput,
                "efficiency": throughput / worker_count  # Throughput per worker
            })
        
        return {
            "test_type": "scalability",
            "scalability_results": scalability_results,
            "detailed_results": [],
            "performance_metrics": {
                "scalability_curve": "Tested from 1 to {} workers".format(num_workers),
                "optimal_workers": max(scalability_results, key=lambda x: x["efficiency"])["worker_count"]
            }
        }
    
    async def _process_worker_batch(self, worker_id: int, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a batch of documents with a specific worker."""
        start_time = time.time()
        processed_docs = []
        
        for doc in documents:
            result = await self._process_single_document(doc, worker_id)
            processed_docs.append(result)
            
            # Simulate some processing delay
            await asyncio.sleep(0.001)
        
        total_time = time.time() - start_time
        
        return {
            "worker_id": worker_id,
            "processed_documents": processed_docs,
            "count": len(documents),
            "total_time": total_time
        }
    
    async def _process_single_document(self, document: Dict[str, Any], worker_id: int) -> Dict[str, Any]:
        """Process a single document."""
        start_time = time.time()
        
        try:
            # Simulate document processing
            processing_time = self._simulate_processing_time(document)
            
            # Add some randomness and potential failures
            if random.random() < 0.02:  # 2% failure rate
                raise Exception("Simulated processing error")
            
            # Add dependency handling
            if document.get("has_dependencies", False):
                await asyncio.sleep(0.05)  # Additional time for dependency resolution
            
            # Add special handling time
            if document.get("requires_special_handling", False):
                await asyncio.sleep(0.1)  # Additional time for special handling
            
            processing_time = time.time() - start_time
            
            return {
                "document_id": document["id"],
                "worker_id": worker_id,
                "assigned_worker": worker_id,
                "processing_time": processing_time,
                "success": True,
                "complexity": document["complexity"],
                "data_size": document["data_size"]
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                "document_id": document["id"],
                "worker_id": worker_id,
                "assigned_worker": worker_id,
                "processing_time": processing_time,
                "success": False,
                "error": str(e),
                "complexity": document["complexity"]
            }
    
    def _simulate_processing_time(self, document: Dict[str, Any]) -> float:
        """Simulate processing time for a document."""
        base_time = document["base_processing_time"]
        
        # Factor in data size
        size_factor = document["data_size"] / 10000  # Normalize to 10KB units
        
        # Factor in complexity
        complexity_multipliers = {
            "simple": 1.0,
            "medium": 1.5,
            "complex": 2.5
        }
        
        complexity_factor = complexity_multipliers.get(document["complexity"], 1.0)
        
        # Calculate processing time
        processing_time = base_time * (1 + size_factor * 0.1) * complexity_factor
        
        # Add randomness
        processing_time *= random.uniform(0.8, 1.2)
        
        return processing_time
    
    def _calculate_parallel_efficiency(self, results: Dict[str, Any], num_workers: int) -> float:
        """Calculate parallel processing efficiency."""
        detailed_results = results.get("detailed_results", [])
        if not detailed_results:
            return 0.0
        
        # Calculate theoretical vs actual processing time
        total_sequential_time = sum(
            self._simulate_processing_time(doc) 
            for doc in self.test_documents
        )
        
        actual_time = results.get("processing_time", 0)
        theoretical_minimum_time = total_sequential_time / num_workers
        
        if theoretical_minimum_time == 0:
            return 0.0
        
        efficiency = actual_time / theoretical_minimum_time
        return max(0.0, min(1.0, 1.0 / efficiency))  # Convert to 0-1 scale
    
    def _calculate_worker_utilization(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate worker utilization metrics."""
        worker_metrics = results.get("worker_metrics", {})
        detailed_results = results.get("detailed_results", [])
        
        if not worker_metrics or not detailed_results:
            return {"avg_utilization": 0.0, "utilization_std": 0.0}
        
        # Calculate utilization rates
        utilizations = []
        for worker_id, metrics in worker_metrics.items():
            if metrics["total_time"] > 0:
                utilization = metrics["documents_processed"] / metrics["total_time"]
                utilizations.append(utilization)
        
        avg_utilization = np.mean(utilizations) if utilizations else 0.0
        utilization_std = np.std(utilizations) if utilizations else 0.0
        
        return {
            "avg_utilization": avg_utilization,
            "utilization_std": utilization_std,
            "min_utilization": min(utilizations) if utilizations else 0.0,
            "max_utilization": max(utilizations) if utilizations else 0.0,
            "worker_count": len(worker_metrics)
        }
    
    def _calculate_queue_performance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate queue performance metrics."""
        detailed_results = results.get("detailed_results", [])
        if not detailed_results:
            return {"avg_queue_time": 0.0, "queue_efficiency": 0.0}
        
        # Calculate queue times (time from submission to start processing)
        # In a real system, this would come from actual queue metrics
        processing_times = [r.get("processing_time", 0) for r in detailed_results]
        
        avg_processing_time = np.mean(processing_times)
        max_processing_time = max(processing_times)
        
        # Simulate queue time as a percentage of processing time
        queue_times = [pt * random.uniform(0.05, 0.15) for pt in processing_times]
        avg_queue_time = np.mean(queue_times)
        
        queue_efficiency = 1.0 - (avg_queue_time / (avg_processing_time + avg_queue_time)) if avg_processing_time + avg_queue_time > 0 else 0
        
        return {
            "avg_queue_time": avg_queue_time,
            "max_queue_time": max(queue_times),
            "queue_efficiency": queue_efficiency,
            "avg_processing_time": avg_processing_time
        }