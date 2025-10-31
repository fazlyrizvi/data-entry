#!/usr/bin/env python3
"""
Performance Test Orchestrator
============================

Main orchestrator for comprehensive performance testing of the data automation system.
Manages all test components, collects metrics, and generates reports.
"""

import asyncio
import json
import logging
import time
import gc
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Try to import optional dependencies, fall back gracefully
try:
    import psutil
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    import mock_psutil as psutil

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError:
    plt = None
    sns = None

from ocr_performance_test import OCRPerformanceTest
from nlp_performance_test import NLPPerformanceTest
from parallel_processing_test import ParallelProcessingTest
from resource_monitor import ResourceMonitor
from benchmark_data_generator import BenchmarkDataGenerator
from results_analyzer import ResultsAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PerformanceTestOrchestrator:
    """Main orchestrator for performance testing."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the performance test orchestrator."""
        self.config = self._load_config(config_path)
        self.start_time = None
        self.end_time = None
        self.results = {}
        self.resource_monitor = ResourceMonitor()
        self.data_generator = BenchmarkDataGenerator()
        self.results_analyzer = ResultsAnalyzer()
        
        # Initialize test components
        self.ocr_test = OCRPerformanceTest()
        self.nlp_test = NLPPerformanceTest()
        self.parallel_test = ParallelProcessingTest()
        
        logger.info("Performance Test Orchestrator initialized")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load test configuration."""
        default_config = {
            "test_scenarios": {
                "small_batch": {"documents": 100, "description": "Small batch test"},
                "medium_batch": {"documents": 500, "description": "Medium batch test"},
                "large_batch": {"documents": 1000, "description": "Large batch test"},
                "stress_test": {"documents": 2000, "description": "Stress test"},
                "endurance_test": {"documents": 5000, "description": "Endurance test"}
            },
            "test_parameters": {
                "resource_monitoring_interval": 1,  # seconds
                "timeout_per_test": 3600,  # seconds
                "parallel_workers": [1, 2, 4, 8, 16],
                "ocr_languages": ["eng"],
                "nlp_tasks": ["entities", "classification", "form_fields"],
                "document_types": ["image", "pdf", "spreadsheet"],
                "document_qualities": ["high", "medium", "low"]
            },
            "output": {
                "results_dir": "testing/results",
                "benchmarks_dir": "testing/benchmarks",
                "report_file": "testing/performance_testing_report.md",
                "save_raw_data": True,
                "generate_charts": True
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive performance tests."""
        logger.info("Starting comprehensive performance testing...")
        self.start_time = datetime.now()
        
        try:
            # Generate test data
            logger.info("Generating benchmark test data...")
            await self.data_generator.generate_all_test_data()
            
            # Run individual component tests
            await self._run_ocr_performance_tests()
            await self._run_nlp_performance_tests()
            await self._run_parallel_processing_tests()
            await self._run_integration_tests()
            await self._run_stress_tests()
            
            self.end_time = datetime.now()
            
            # Analyze results
            logger.info("Analyzing test results...")
            analysis_results = await self.results_analyzer.analyze_all_results(self.results)
            
            # Generate report
            logger.info("Generating performance report...")
            await self._generate_performance_report(analysis_results)
            
            logger.info(f"Performance testing completed in {self.end_time - self.start_time}")
            return {
                "test_duration": str(self.end_time - self.start_time),
                "results": self.results,
                "analysis": analysis_results
            }
            
        except Exception as e:
            logger.error(f"Performance testing failed: {e}")
            raise
    
    async def _run_ocr_performance_tests(self):
        """Run OCR performance tests."""
        logger.info("Running OCR performance tests...")
        
        for scenario_name, scenario_config in self.config["test_scenarios"].items():
            logger.info(f"Running OCR test scenario: {scenario_name}")
            
            # Start resource monitoring
            self.resource_monitor.start_monitoring()
            
            # Run OCR test
            test_result = await self.ocr_test.run_performance_test(
                num_documents=scenario_config["documents"],
                document_types=self.config["test_parameters"]["document_types"],
                document_qualities=self.config["test_parameters"]["document_qualities"],
                languages=self.config["test_parameters"]["ocr_languages"]
            )
            
            # Stop resource monitoring
            resource_stats = self.resource_monitor.stop_monitoring()
            
            # Store results
            self.results[f"ocr_{scenario_name}"] = {
                "scenario": scenario_name,
                "test_result": test_result,
                "resource_stats": resource_stats,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"OCR test scenario {scenario_name} completed")
            gc.collect()  # Force garbage collection
    
    async def _run_nlp_performance_tests(self):
        """Run NLP performance tests."""
        logger.info("Running NLP performance tests...")
        
        for scenario_name, scenario_config in self.config["test_scenarios"].items():
            logger.info(f"Running NLP test scenario: {scenario_name}")
            
            # Start resource monitoring
            self.resource_monitor.start_monitoring()
            
            # Run NLP test
            test_result = await self.nlp_test.run_performance_test(
                num_documents=scenario_config["documents"],
                tasks=self.config["test_parameters"]["nlp_tasks"]
            )
            
            # Stop resource monitoring
            resource_stats = self.resource_monitor.stop_monitoring()
            
            # Store results
            self.results[f"nlp_{scenario_name}"] = {
                "scenario": scenario_name,
                "test_result": test_result,
                "resource_stats": resource_stats,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"NLP test scenario {scenario_name} completed")
            gc.collect()
    
    async def _run_parallel_processing_tests(self):
        """Run parallel processing performance tests."""
        logger.info("Running parallel processing tests...")
        
        for worker_count in self.config["test_parameters"]["parallel_workers"]:
            logger.info(f"Running parallel processing test with {worker_count} workers")
            
            # Start resource monitoring
            self.resource_monitor.start_monitoring()
            
            # Run parallel processing test
            test_result = await self.parallel_test.run_performance_test(
                num_documents=1000,
                num_workers=worker_count
            )
            
            # Stop resource monitoring
            resource_stats = self.resource_monitor.stop_monitoring()
            
            # Store results
            self.results[f"parallel_{worker_count}_workers"] = {
                "num_workers": worker_count,
                "test_result": test_result,
                "resource_stats": resource_stats,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Parallel processing test with {worker_count} workers completed")
            gc.collect()
    
    async def _run_integration_tests(self):
        """Run end-to-end integration tests."""
        logger.info("Running integration tests...")
        
        logger.info("Running OCR + NLP integration test")
        
        # Start resource monitoring
        self.resource_monitor.start_monitoring()
        
        # Run integrated OCR + NLP processing
        test_result = await self._run_ocr_nlp_integration_test(500)
        
        # Stop resource monitoring
        resource_stats = self.resource_monitor.stop_monitoring()
        
        # Store results
        self.results["integration_ocr_nlp"] = {
            "test_result": test_result,
            "resource_stats": resource_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Integration tests completed")
        gc.collect()
    
    async def _run_stress_tests(self):
        """Run stress tests."""
        logger.info("Running stress tests...")
        
        # System limits test
        logger.info("Running system limits test")
        self.resource_monitor.start_monitoring()
        
        stress_result = await self._run_system_limits_test()
        
        resource_stats = self.resource_monitor.stop_monitoring()
        
        self.results["stress_test"] = {
            "test_result": stress_result,
            "resource_stats": resource_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Stress tests completed")
        gc.collect()
    
    async def _run_ocr_nlp_integration_test(self, num_documents: int) -> Dict[str, Any]:
        """Run integrated OCR + NLP processing test."""
        start_time = time.time()
        
        # Generate test documents
        documents = self.data_generator.generate_test_documents(
            num_documents, 
            ["image", "pdf"], 
            ["high", "medium"]
        )
        
        results = []
        
        # Process each document through OCR + NLP pipeline
        for i, document in enumerate(documents):
            try:
                # Simulate OCR processing
                ocr_start = time.time()
                ocr_result = await self.ocr_test.simulate_ocr_processing(document)
                ocr_time = time.time() - ocr_start
                
                # Simulate NLP processing
                nlp_start = time.time()
                nlp_result = await self.nlp_test.simulate_nlp_processing(ocr_result["text"])
                nlp_time = time.time() - nlp_start
                
                results.append({
                    "document_id": i,
                    "document_size": document.get("size", 0),
                    "ocr_time": ocr_time,
                    "nlp_time": nlp_time,
                    "total_time": ocr_time + nlp_time,
                    "ocr_confidence": ocr_result.get("confidence", 0),
                    "nlp_entities_found": len(nlp_result.get("entities", {}))
                })
                
            except Exception as e:
                results.append({
                    "document_id": i,
                    "error": str(e)
                })
        
        total_time = time.time() - start_time
        
        return {
            "total_documents": num_documents,
            "successful_documents": len([r for r in results if "error" not in r]),
            "total_processing_time": total_time,
            "average_time_per_document": total_time / num_documents,
            "throughput_documents_per_second": num_documents / total_time,
            "results": results,
            "performance_summary": {
                "avg_ocr_time": sum(r.get("ocr_time", 0) for r in results) / len(results),
                "avg_nlp_time": sum(r.get("nlp_time", 0) for r in results) / len(results),
                "avg_confidence": sum(r.get("ocr_confidence", 0) for r in results) / len(results),
                "total_entities_extracted": sum(r.get("nlp_entities_found", 0) for r in results)
            }
        }
    
    async def _run_system_limits_test(self) -> Dict[str, Any]:
        """Run system limits stress test."""
        start_time = time.time()
        
        # Get system limits
        cpu_count = psutil.cpu_count()
        memory = psutil.virtual_memory()
        
        logger.info(f"System limits test - CPU cores: {cpu_count}, Memory: {memory.total // (1024**3)} GB")
        
        # Test with maximum reasonable load
        max_workers = min(cpu_count * 2, 32)  # Don't exceed 32 workers
        test_documents = [f"stress_doc_{i}" for i in range(10000)]
        
        results = []
        
        try:
            # Test with increasing load
            for worker_count in [max_workers//4, max_workers//2, max_workers]:
                logger.info(f"Testing with {worker_count} workers")
                
                test_start = time.time()
                test_result = await self.parallel_test.run_performance_test(
                    num_documents=2000,
                    num_workers=worker_count
                )
                test_time = time.time() - test_start
                
                results.append({
                    "worker_count": worker_count,
                    "processing_time": test_time,
                    "throughput": 2000 / test_time,
                    "success_rate": test_result.get("success_rate", 0)
                })
        
        except Exception as e:
            logger.warning(f"System limits test encountered error: {e}")
        
        total_time = time.time() - start_time
        
        return {
            "system_info": {
                "cpu_cores": cpu_count,
                "total_memory_gb": memory.total // (1024**3),
                "available_memory_gb": memory.available // (1024**3)
            },
            "max_workers_tested": max_workers,
            "total_test_time": total_time,
            "load_test_results": results
        }
    
    async def _generate_performance_report(self, analysis_results: Dict[str, Any]):
        """Generate comprehensive performance report."""
        report_path = Path(self.config["output"]["report_file"])
        
        with open(report_path, 'w') as f:
            f.write("# Data Automation System Performance Testing Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Test Duration:** {self.end_time - self.start_time}\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            f.write(analysis_results.get("executive_summary", "No summary available"))
            f.write("\n\n")
            
            # Key Findings
            f.write("## Key Findings\n\n")
            f.write(analysis_results.get("key_findings", "No key findings available"))
            f.write("\n\n")
            
            # Performance Benchmarks
            f.write("## Performance Benchmarks\n\n")
            self._write_benchmark_section(f, analysis_results)
            
            # Resource Utilization
            f.write("\n## Resource Utilization\n\n")
            self._write_resource_section(f, analysis_results)
            
            # Optimization Recommendations
            f.write("\n## Optimization Recommendations\n\n")
            self._write_recommendations_section(f, analysis_results)
            
            # Detailed Test Results
            f.write("\n## Detailed Test Results\n\n")
            self._write_detailed_results(f)
            
        logger.info(f"Performance report generated: {report_path}")
    
    def _write_benchmark_section(self, f, analysis_results: Dict[str, Any]):
        """Write benchmark section to report."""
        f.write("### OCR Performance\n\n")
        benchmark_data = analysis_results.get("ocr_benchmarks", {})
        if benchmark_data:
            f.write("| Document Type | Avg Processing Time | Throughput (docs/sec) | Success Rate |\n")
            f.write("|---------------|-------------------|---------------------|-------------|\n")
            for doc_type, metrics in benchmark_data.items():
                f.write(f"| {doc_type} | {metrics.get('avg_time', 0):.3f}s | {metrics.get('throughput', 0):.2f} | {metrics.get('success_rate', 0):.2%} |\n")
        
        f.write("\n### NLP Performance\n\n")
        nlp_data = analysis_results.get("nlp_benchmarks", {})
        if nlp_data:
            f.write("| Task | Avg Processing Time | Entities Found | Accuracy |\n")
            f.write("|------|-------------------|---------------|----------|\n")
            for task, metrics in nlp_data.items():
                f.write(f"| {task} | {metrics.get('avg_time', 0):.3f}s | {metrics.get('avg_entities', 0)} | {metrics.get('accuracy', 0):.2%} |\n")
        
        f.write("\n### Parallel Processing Performance\n\n")
        parallel_data = analysis_results.get("parallel_benchmarks", {})
        if parallel_data:
            f.write("| Workers | Processing Time | Throughput | Efficiency |\n")
            f.write("|---------|----------------|-----------|------------|\n")
            for workers, metrics in parallel_data.items():
                f.write(f"| {workers} | {metrics.get('time', 0):.3f}s | {metrics.get('throughput', 0):.2f} | {metrics.get('efficiency', 0):.2%} |\n")
    
    def _write_resource_section(self, f, analysis_results: Dict[str, Any]):
        """Write resource utilization section to report."""
        resource_data = analysis_results.get("resource_utilization", {})
        if resource_data:
            f.write(f"**CPU Usage:** {resource_data.get('cpu_avg', 0):.1f}% (peak: {resource_data.get('cpu_peak', 0):.1f}%)\n\n")
            f.write(f"**Memory Usage:** {resource_data.get('memory_avg', 0):.1f}% (peak: {resource_data.get('memory_peak', 0):.1f}%)\n\n")
            f.write(f"**Peak Memory Usage:** {resource_data.get('peak_memory_mb', 0):.1f} MB\n\n")
    
    def _write_recommendations_section(self, f, analysis_results: Dict[str, Any]):
        """Write recommendations section to report."""
        recommendations = analysis_results.get("recommendations", [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                f.write(f"{i}. {rec}\n\n")
        else:
            f.write("No specific recommendations available.\n\n")
    
    def _write_detailed_results(self, f):
        """Write detailed test results to report."""
        for test_name, test_data in self.results.items():
            f.write(f"### {test_name.replace('_', ' ').title()}\n\n")
            
            if "test_result" in test_data:
                result = test_data["test_result"]
                f.write(f"- **Documents Processed:** {result.get('total_documents', 'N/A')}\n")
                f.write(f"- **Success Rate:** {result.get('success_rate', 0):.2%}\n")
                f.write(f"- **Total Processing Time:** {result.get('total_processing_time', 0):.3f}s\n")
                f.write(f"- **Average Time per Document:** {result.get('average_time_per_document', 0):.3f}s\n")
                
            f.write("\n")
    
    def save_raw_results(self):
        """Save raw test results to JSON files."""
        results_dir = Path(self.config["output"]["results_dir"])
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save comprehensive results
        all_results_file = results_dir / f"performance_test_results_{timestamp}.json"
        with open(all_results_file, 'w') as f:
            json.dump({
                "test_configuration": self.config,
                "test_duration": str(self.end_time - self.start_time) if self.end_time and self.start_time else None,
                "results": self.results
            }, f, indent=2, default=str)
        
        logger.info(f"Raw results saved to: {all_results_file}")

    async def run_smoke_tests(self) -> Dict[str, Any]:
        """Run quick smoke tests for basic functionality verification."""
        logger.info("Starting smoke tests...")
        self.start_time = datetime.now()
        
        try:
            # Quick test with small dataset
            smoke_config = {
                "documents": 50,
                "document_types": ["image"],
                "document_qualities": ["high"],
                "languages": ["eng"],
                "tasks": ["entities"]
            }
            
            # Test OCR
            logger.info("Running OCR smoke test...")
            ocr_result = await self.ocr_test.run_performance_test(
                num_documents=smoke_config["documents"],
                document_types=smoke_config["document_types"],
                document_qualities=smoke_config["document_qualities"],
                languages=smoke_config["languages"]
            )
            
            # Test NLP
            logger.info("Running NLP smoke test...")
            nlp_result = await self.nlp_test.run_performance_test(
                num_documents=smoke_config["documents"],
                tasks=smoke_config["tasks"]
            )
            
            self.end_time = datetime.now()
            
            smoke_results = {
                "test_duration": str(self.end_time - self.start_time),
                "ocr_test": ocr_result,
                "nlp_test": nlp_result,
                "smoke_test": True
            }
            
            logger.info("Smoke tests completed successfully")
            return smoke_results
            
        except Exception as e:
            logger.error(f"Smoke tests failed: {e}")
            raise


async def main():
    """Main entry point."""
    import sys
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    orchestrator = PerformanceTestOrchestrator(config_path)
    
    try:
        results = await orchestrator.run_comprehensive_tests()
        orchestrator.save_raw_results()
        
        print("\n" + "="*80)
        print("PERFORMANCE TESTING COMPLETED")
        print("="*80)
        print(f"Test Duration: {results['test_duration']}")
        print(f"Total Test Scenarios: {len(orchestrator.results)}")
        print(f"Report Generated: {orchestrator.config['output']['report_file']}")
        print("="*80)
        
    except KeyboardInterrupt:
        logger.info("Performance testing interrupted by user")
    except Exception as e:
        logger.error(f"Performance testing failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())