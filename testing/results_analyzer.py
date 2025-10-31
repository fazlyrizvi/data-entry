#!/usr/bin/env python3
"""
Results Analyzer Module
======================

Analyzes performance test results and generates insights.
Creates reports and visualizations from test data.
"""

import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import statistics

logger = logging.getLogger(__name__)


class ResultsAnalyzer:
    """Analyzes performance test results and generates reports."""
    
    def __init__(self, results_dir: str = "testing/results"):
        """Initialize results analyzer.
        
        Args:
            results_dir: Directory containing test results
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"Results analyzer initialized with results dir: {self.results_dir}")
    
    async def analyze_all_results(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze all test results and generate comprehensive report.
        
        Args:
            test_results: Dictionary containing all test results
            
        Returns:
            Analysis results with insights and recommendations
        """
        logger.info("Starting comprehensive results analysis...")
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "executive_summary": self._generate_executive_summary(test_results),
            "key_findings": self._generate_key_findings(test_results),
            "ocr_benchmarks": self._analyze_ocr_performance(test_results),
            "nlp_benchmarks": self._analyze_nlp_performance(test_results),
            "parallel_benchmarks": self._analyze_parallel_performance(test_results),
            "resource_utilization": self._analyze_resource_utilization(test_results),
            "recommendations": self._generate_recommendations(test_results),
            "detailed_analysis": self._detailed_component_analysis(test_results)
        }
        
        logger.info("Results analysis completed")
        return analysis
    
    def _generate_executive_summary(self, test_results: Dict[str, Any]) -> str:
        """Generate executive summary of test results."""
        
        # Calculate overall metrics
        total_tests = len(test_results)
        successful_tests = len([r for r in test_results.values() 
                               if r.get("test_result", {}).get("success_rate", 0) > 0.8])
        
        # Extract key performance indicators
        processing_times = []
        throughputs = []
        success_rates = []
        
        for test_name, test_data in test_results.items():
            result = test_data.get("test_result", {})
            processing_times.append(result.get("total_processing_time", 0))
            throughputs.append(result.get("throughput_documents_per_second", 0))
            success_rates.append(result.get("success_rate", 0))
        
        avg_processing_time = statistics.mean(processing_times) if processing_times else 0
        avg_throughput = statistics.mean(throughputs) if throughputs else 0
        avg_success_rate = statistics.mean(success_rates) if success_rates else 0
        
        summary = f"""
## Performance Testing Summary

The data automation system underwent comprehensive performance testing across {total_tests} test scenarios. 

### Key Performance Indicators:
- **Average Success Rate**: {avg_success_rate:.1%}
- **Average Processing Time**: {avg_processing_time:.2f} seconds
- **Average Throughput**: {avg_throughput:.2f} documents/second
- **Tests Exceeding 80% Success Rate**: {successful_tests}/{total_tests}

### System Performance:
The system demonstrates {'excellent' if avg_success_rate > 0.9 else 'good' if avg_success_rate > 0.8 else 'acceptable'} 
reliability with {avg_success_rate:.1%} success rate across all test scenarios. 
{'Strong' if avg_throughput > 10 else 'Adequate' if avg_throughput > 5 else 'Moderate'} throughput capabilities 
at {avg_throughput:.2f} documents per second.

### Test Coverage:
- OCR processing across multiple document types and qualities
- NLP entity extraction and text classification
- Parallel processing with varying worker configurations
- System resource utilization and stress testing
"""
        
        return summary
    
    def _generate_key_findings(self, test_results: Dict[str, Any]) -> str:
        """Generate key findings from test results."""
        
        findings = []
        
        # Analyze OCR performance
        ocr_tests = {k: v for k, v in test_results.items() if k.startswith("ocr_")}
        if ocr_tests:
            ocr_by_type = {}
            for test_name, test_data in ocr_tests.items():
                result = test_data.get("test_result", {})
                results_by_type = result.get("results_by_type", {})
                for doc_type, metrics in results_by_type.items():
                    if doc_type not in ocr_by_type:
                        ocr_by_type[doc_type] = []
                    ocr_by_type[doc_type].append(metrics.get("success_rate", 0))
            
            for doc_type, success_rates in ocr_by_type.items():
                avg_rate = statistics.mean(success_rates) if success_rates else 0
                findings.append(f"- OCR {doc_type} processing shows {avg_rate:.1%} average success rate")
        
        # Analyze NLP performance
        nlp_tests = {k: v for k, v in test_results.items() if k.startswith("nlp_")}
        if nlp_tests:
            fastest_task = None
            fastest_time = float('inf')
            for test_name, test_data in nlp_tests.items():
                result = test_data.get("test_result", {})
                results_by_task = result.get("results_by_task", {})
                for task, metrics in results_by_task.items():
                    avg_time = metrics.get("average_processing_time", float('inf'))
                    if avg_time < fastest_time:
                        fastest_time = avg_time
                        fastest_task = task
            
            if fastest_task:
                findings.append(f"- NLP {fastest_task} processing is fastest at {fastest_time:.3f}s average")
        
        # Analyze parallel processing
        parallel_tests = {k: v for k, v in test_results.items() if k.startswith("parallel_")}
        if parallel_tests:
            best_efficiency = 0
            best_workers = 0
            for test_name, test_data in parallel_tests.items():
                efficiency = test_data.get("parallel_efficiency", 0)
                if efficiency > best_efficiency:
                    best_efficiency = efficiency
                    # Extract worker count from test name
                    try:
                        best_workers = int(test_name.split('_')[1])
                    except:
                        pass
            
            findings.append(f"- Optimal parallel processing with {best_workers} workers achieves {best_efficiency:.1%} efficiency")
        
        # Analyze resource utilization
        avg_cpu = []
        avg_memory = []
        for test_data in test_results.values():
            resource_stats = test_data.get("resource_stats", {})
            if resource_stats:
                avg_cpu.append(resource_stats.get("cpu", {}).get("average", 0))
                avg_memory.append(resource_stats.get("memory", {}).get("average", 0))
        
        if avg_cpu and avg_memory:
            findings.append(f"- System uses {statistics.mean(avg_cpu):.1f}% CPU and {statistics.mean(avg_memory):.1f}% memory on average")
        
        if not findings:
            findings.append("- Performance testing completed successfully across all test scenarios")
        
        return "\n".join(findings)
    
    def _analyze_ocr_performance(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze OCR performance across different scenarios."""
        
        ocr_tests = {k: v for k, v in test_results.items() if k.startswith("ocr_")}
        benchmarks = {}
        
        for test_name, test_data in ocr_tests.items():
            result = test_data.get("test_result", {})
            results_by_type = result.get("results_by_type", {})
            
            for doc_type, metrics in results_by_type.items():
                if doc_type not in benchmarks:
                    benchmarks[doc_type] = {
                        "avg_time": [],
                        "throughput": [],
                        "success_rate": [],
                        "accuracy": [],
                        "confidence": []
                    }
                
                benchmarks[doc_type]["avg_time"].append(metrics.get("average_processing_time", 0))
                benchmarks[doc_type]["throughput"].append(metrics.get("throughput_docs_per_second", 0))
                benchmarks[doc_type]["success_rate"].append(metrics.get("success_rate", 0))
                benchmarks[doc_type]["accuracy"].append(metrics.get("average_accuracy", 0))
                benchmarks[doc_type]["confidence"].append(metrics.get("average_confidence", 0))
        
        # Calculate averages for each document type
        final_benchmarks = {}
        for doc_type, values in benchmarks.items():
            final_benchmarks[doc_type] = {
                "avg_time": statistics.mean(values["avg_time"]) if values["avg_time"] else 0,
                "throughput": statistics.mean(values["throughput"]) if values["throughput"] else 0,
                "success_rate": statistics.mean(values["success_rate"]) if values["success_rate"] else 0,
                "accuracy": statistics.mean(values["accuracy"]) if values["accuracy"] else 0,
                "confidence": statistics.mean(values["confidence"]) if values["confidence"] else 0
            }
        
        return final_benchmarks
    
    def _analyze_nlp_performance(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze NLP performance across different tasks."""
        
        nlp_tests = {k: v for k, v in test_results.items() if k.startswith("nlp_")}
        benchmarks = {}
        
        for test_name, test_data in nlp_tests.items():
            result = test_data.get("test_result", {})
            results_by_task = result.get("results_by_task", {})
            
            for task, metrics in results_by_task.items():
                if task not in benchmarks:
                    benchmarks[task] = {
                        "avg_time": [],
                        "success_rate": [],
                        "accuracy": [],
                        "avg_entities": []
                    }
                
                benchmarks[task]["avg_time"].append(metrics.get("average_processing_time", 0))
                benchmarks[task]["success_rate"].append(metrics.get("success_rate", 0))
                
                # Get task-specific metrics
                task_metrics = metrics.get("task_specific_metrics", {})
                if task == "entities":
                    benchmarks[task]["avg_entities"].append(task_metrics.get("avg_entities_per_document", 0))
                    benchmarks[task]["accuracy"].append(task_metrics.get("avg_confidence", 0))
                elif task == "form_fields":
                    benchmarks[task]["accuracy"].append(task_metrics.get("avg_confidence", 0))
                else:
                    benchmarks[task]["accuracy"].append(task_metrics.get("avg_type_confidence", 0))
        
        # Calculate averages for each task
        final_benchmarks = {}
        for task, values in benchmarks.items():
            final_benchmarks[task] = {
                "avg_time": statistics.mean(values["avg_time"]) if values["avg_time"] else 0,
                "success_rate": statistics.mean(values["success_rate"]) if values["success_rate"] else 0,
                "accuracy": statistics.mean(values["accuracy"]) if values["accuracy"] else 0,
                "avg_entities": statistics.mean(values["avg_entities"]) if values["avg_entities"] else 0
            }
        
        return final_benchmarks
    
    def _analyze_parallel_performance(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze parallel processing performance."""
        
        parallel_tests = {k: v for k, v in test_results.items() if k.startswith("parallel_")}
        benchmarks = {}
        
        for test_name, test_data in parallel_tests.items():
            # Extract worker count from test name
            try:
                worker_count = int(test_name.split('_')[1])
            except:
                worker_count = 1
            
            result = test_data.get("test_result", {})
            
            benchmarks[f"{worker_count} workers"] = {
                "time": result.get("total_processing_time", 0),
                "throughput": result.get("throughput_documents_per_second", 0),
                "efficiency": test_data.get("parallel_efficiency", 0)
            }
        
        return benchmarks
    
    def _analyze_resource_utilization(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system resource utilization across tests."""
        
        all_cpu = []
        all_memory = []
        peak_memory_gb = []
        
        for test_data in test_results.values():
            resource_stats = test_data.get("resource_stats", {})
            if resource_stats:
                cpu_stats = resource_stats.get("cpu", {})
                memory_stats = resource_stats.get("memory", {})
                
                all_cpu.append(cpu_stats.get("average", 0))
                all_memory.append(memory_stats.get("average", 0))
                peak_memory_gb.append(memory_stats.get("peak_usage_gb", 0))
        
        return {
            "cpu_avg": statistics.mean(all_cpu) if all_cpu else 0,
            "cpu_peak": max(all_cpu) if all_cpu else 0,
            "memory_avg": statistics.mean(all_memory) if all_memory else 0,
            "memory_peak": max(all_memory) if all_memory else 0,
            "peak_memory_mb": statistics.mean(peak_memory_gb) * 1024 if peak_memory_gb else 0
        }
    
    def _generate_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on test results."""
        
        recommendations = []
        
        # Analyze performance patterns
        low_performance_tests = []
        high_resource_usage = []
        
        for test_name, test_data in test_results.items():
            result = test_data.get("test_result", {})
            resource_stats = test_data.get("resource_stats", {})
            
            # Identify low performance tests
            success_rate = result.get("success_rate", 1.0)
            if success_rate < 0.8:
                low_performance_tests.append(test_name)
            
            # Identify high resource usage
            if resource_stats:
                cpu_avg = resource_stats.get("cpu", {}).get("average", 0)
                memory_avg = resource_stats.get("memory", {}).get("average", 0)
                if cpu_avg > 80 or memory_avg > 80:
                    high_resource_usage.append(test_name)
        
        # Generate specific recommendations
        if low_performance_tests:
            recommendations.append("Investigate and optimize low-performing test scenarios to improve overall system reliability")
        
        if high_resource_usage:
            recommendations.append("Consider implementing resource optimization strategies to reduce CPU and memory consumption")
        
        # OCR-specific recommendations
        ocr_tests = {k: v for k, v in test_results.items() if k.startswith("ocr_")}
        if ocr_tests:
            pdf_slow = False
            image_quality_issues = False
            
            for test_name, test_data in ocr_tests.items():
                result = test_data.get("test_result", {})
                results_by_type = result.get("results_by_type", {})
                
                for doc_type, metrics in results_by_type.items():
                    if doc_type == "pdf" and metrics.get("average_processing_time", 0) > 5:
                        pdf_slow = True
                    if doc_type == "image" and metrics.get("average_accuracy", 0) < 0.8:
                        image_quality_issues = True
            
            if pdf_slow:
                recommendations.append("Optimize PDF processing pipeline - consider PDF preprocessing improvements or specialized PDF OCR models")
            if image_quality_issues:
                recommendations.append("Implement image preprocessing pipeline to improve OCR accuracy on lower quality images")
        
        # NLP-specific recommendations
        nlp_tests = {k: v for k, v in test_results.items() if k.startswith("nlp_")}
        if nlp_tests:
            slow_tasks = []
            for test_name, test_data in nlp_tests.items():
                result = test_data.get("test_result", {})
                results_by_task = result.get("results_by_task", {})
                
                for task, metrics in results_by_task.items():
                    if metrics.get("average_processing_time", 0) > 0.1:  # 100ms threshold
                        slow_tasks.append(task)
            
            if slow_tasks:
                recommendations.append(f"Consider optimizing NLP processing for {', '.join(set(slow_tasks))} tasks - implement caching or model optimization")
        
        # Parallel processing recommendations
        parallel_tests = {k: v for k, v in test_results.items() if k.startswith("parallel_")}
        if parallel_tests:
            best_efficiency = 0
            optimal_workers = 1
            
            for test_name, test_data in parallel_tests.items():
                efficiency = test_data.get("parallel_efficiency", 0)
                if efficiency > best_efficiency:
                    best_efficiency = efficiency
                    try:
                        optimal_workers = int(test_name.split('_')[1])
                    except:
                        pass
            
            if best_efficiency < 0.7:
                recommendations.append("Review parallel processing configuration - current efficiency suggests potential for better load balancing")
            else:
                recommendations.append(f"System shows good parallelization efficiency with {optimal_workers} workers - consider this as optimal configuration")
        
        # General recommendations
        recommendations.extend([
            "Implement monitoring and alerting for performance degradation",
            "Consider implementing circuit breakers for fault tolerance",
            "Establish baseline performance metrics and set up continuous performance monitoring",
            "Plan for horizontal scaling based on projected load increases"
        ])
        
        return recommendations
    
    def _detailed_component_analysis(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Provide detailed analysis of each component."""
        
        detailed_analysis = {}
        
        # Analyze each component
        for component in ["ocr", "nlp", "parallel"]:
            component_tests = {k: v for k, v in test_results.items() if k.startswith(component)}
            
            if not component_tests:
                continue
            
            component_analysis = {
                "total_tests": len(component_tests),
                "performance_trends": self._analyze_performance_trends(component_tests),
                "bottlenecks": self._identify_bottlenecks(component_tests),
                "consistency": self._analyze_consistency(component_tests)
            }
            
            detailed_analysis[component] = component_analysis
        
        return detailed_analysis
    
    def _analyze_performance_trends(self, component_tests: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance trends for a component."""
        
        processing_times = []
        throughputs = []
        
        for test_data in component_tests.values():
            result = test_data.get("test_result", {})
            processing_times.append(result.get("total_processing_time", 0))
            throughputs.append(result.get("throughput_documents_per_second", 0))
        
        return {
            "avg_processing_time": statistics.mean(processing_times) if processing_times else 0,
            "avg_throughput": statistics.mean(throughputs) if throughputs else 0,
            "time_variance": statistics.stdev(processing_times) if len(processing_times) > 1 else 0,
            "throughput_variance": statistics.stdev(throughputs) if len(throughputs) > 1 else 0
        }
    
    def _identify_bottlenecks(self, component_tests: Dict[str, Any]) -> List[str]:
        """Identify performance bottlenecks in component tests."""
        
        bottlenecks = []
        
        for test_name, test_data in component_tests.items():
            result = test_data.get("test_result", {})
            
            # Check for long processing times
            if result.get("total_processing_time", 0) > 60:  # 1 minute threshold
                bottlenecks.append(f"{test_name}: Long processing time ({result.get('total_processing_time', 0):.2f}s)")
            
            # Check for low throughput
            if result.get("throughput_documents_per_second", float('inf')) < 1:  # Less than 1 doc/sec
                bottlenecks.append(f"{test_name}: Low throughput ({result.get('throughput_documents_per_second', 0):.2f} docs/sec)")
            
            # Check for high resource usage
            resource_stats = test_data.get("resource_stats", {})
            if resource_stats:
                cpu_peak = resource_stats.get("cpu", {}).get("peak", 0)
                memory_peak = resource_stats.get("memory", {}).get("peak", 0)
                
                if cpu_peak > 90:
                    bottlenecks.append(f"{test_name}: High CPU usage ({cpu_peak:.1f}%)")
                if memory_peak > 90:
                    bottlenecks.append(f"{test_name}: High memory usage ({memory_peak:.1f}%)")
        
        return bottlenecks
    
    def _analyze_consistency(self, component_tests: Dict[str, Any]) -> Dict[str, float]:
        """Analyze performance consistency across tests."""
        
        success_rates = []
        processing_times = []
        
        for test_data in component_tests.values():
            result = test_data.get("test_result", {})
            success_rates.append(result.get("success_rate", 0))
            processing_times.append(result.get("total_processing_time", 0))
        
        return {
            "success_rate_consistency": 1.0 - (statistics.stdev(success_rates) if len(success_rates) > 1 else 0),
            "processing_time_consistency": 1.0 - (statistics.stdev(processing_times) / statistics.mean(processing_times) if processing_times and statistics.mean(processing_times) > 0 else 0)
        }
    
    def save_analysis_report(self, analysis: Dict[str, Any], filename: str):
        """Save analysis report to file."""
        report_path = self.results_dir / filename
        
        with open(report_path, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        logger.info(f"Analysis report saved to {report_path}")
    
    def export_benchmarks(self, benchmarks: Dict[str, Any], filename: str):
        """Export benchmarks to CSV format."""
        benchmark_path = self.results_dir / filename
        
        # Convert to DataFrame for easy export
        data_rows = []
        
        for component, component_benchmarks in benchmarks.items():
            if isinstance(component_benchmarks, dict):
                for metric, value in component_benchmarks.items():
                    data_rows.append({
                        "component": component,
                        "metric": metric,
                        "value": value
                    })
        
        if data_rows:
            df = pd.DataFrame(data_rows)
            df.to_csv(benchmark_path, index=False)
            logger.info(f"Benchmarks exported to {benchmark_path}")
        else:
            logger.warning("No benchmark data to export")