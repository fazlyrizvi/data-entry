#!/usr/bin/env python3
"""
Comprehensive Module Testing Suite Runner
=========================================
Runs all module test suites and compiles comprehensive results.
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/testing/testing_execution.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveTestRunner:
    """Comprehensive test runner for all modules."""
    
    def __init__(self):
        self.test_suites = [
            {
                'name': 'OCR Service',
                'script': '/workspace/testing/scripts/test_ocr_service.py',
                'module_path': '/workspace/code/ocr_service'
            },
            {
                'name': 'NLP Pipeline',
                'script': '/workspace/testing/scripts/test_nlp_pipeline.py',
                'module_path': '/workspace/code/nlp_pipeline'
            },
            {
                'name': 'Validation Engine',
                'script': '/workspace/testing/scripts/test_validation_engine.py',
                'module_path': '/workspace/code/validation_engine'
            },
            {
                'name': 'Error Prediction System',
                'script': '/workspace/testing/scripts/test_error_prediction.py',
                'module_path': '/workspace/code/error_prediction'
            },
            {
                'name': 'Parallel Processing System',
                'script': '/workspace/testing/scripts/test_parallel_processing.py',
                'module_path': '/workspace/code/parallel_processing'
            }
        ]
        
        self.results = {
            'test_execution': {
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'duration_seconds': 0,
                'total_suites': len(self.test_suites),
                'completed_suites': 0,
                'failed_suites': 0
            },
            'module_results': {},
            'summary': {
                'total_tests': 0,
                'total_passed': 0,
                'total_failed': 0,
                'total_errors': 0,
                'success_rate': 0.0,
                'average_duration': 0.0
            },
            'issues_found': [],
            'recommendations': []
        }
    
    def run_all_tests(self):
        """Run all test suites."""
        logger.info("Starting Comprehensive Module Testing Suite")
        logger.info(f"Total test suites to run: {len(self.test_suites)}")
        
        start_time = time.time()
        
        for suite in self.test_suites:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running test suite: {suite['name']}")
            logger.info(f"{'='*60}")
            
            try:
                result = self._run_test_suite(suite)
                self.results['module_results'][suite['name']] = result
                self.results['test_execution']['completed_suites'] += 1
                
                logger.info(f"✓ {suite['name']} completed successfully")
                
            except Exception as e:
                logger.error(f"✗ {suite['name']} failed with error: {str(e)}")
                logger.error(f"Error details: {traceback.format_exc()}")
                
                self.results['module_results'][suite['name']] = {
                    'status': 'FAILED',
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
                self.results['test_execution']['failed_suites'] += 1
        
        # Calculate final results
        end_time = time.time()
        self._calculate_final_results(start_time, end_time)
        
        # Generate recommendations
        self._generate_recommendations()
        
        # Save comprehensive results
        self._save_results()
        
        logger.info(f"\n{'='*60}")
        logger.info("COMPREHENSIVE TESTING COMPLETED")
        logger.info(f"{'='*60}")
        logger.info(f"Total suites: {self.results['test_execution']['total_suites']}")
        logger.info(f"Completed: {self.results['test_execution']['completed_suites']}")
        logger.info(f"Failed: {self.results['test_execution']['failed_suites']}")
        logger.info(f"Total tests: {self.results['summary']['total_tests']}")
        logger.info(f"Passed: {self.results['summary']['total_passed']}")
        logger.info(f"Failed: {self.results['summary']['total_failed']}")
        logger.info(f"Success rate: {self.results['summary']['success_rate']:.2%}")
        
        return self.results
    
    def _run_test_suite(self, suite: Dict[str, str]) -> Dict[str, Any]:
        """Run a single test suite."""
        try:
            # Check if test script exists
            if not os.path.exists(suite['script']):
                raise FileNotFoundError(f"Test script not found: {suite['script']}")
            
            # Import and run the test module
            import importlib.util
            
            # Load the module
            spec = importlib.util.spec_from_file_location("test_module", suite['script'])
            test_module = importlib.util.module_from_spec(spec)
            
            # Add module path to sys.path for imports
            original_path = sys.path.copy()
            sys.path.insert(0, suite['module_path'])
            
            try:
                spec.loader.exec_module(test_module)
                
                # Run the test function
                if hasattr(test_module, f'run_{suite["name"].lower().replace(" ", "_")}_tests'):
                    test_func = getattr(test_module, f'run_{suite["name"].lower().replace(" ", "_")}_tests')
                    result = test_func()
                    
                    # Load the results file
                    result_file = f'/workspace/testing/results/{suite["name"].lower().replace(" ", "_")}_test_results.json'
                    if os.path.exists(result_file):
                        with open(result_file, 'r') as f:
                            return json.load(f)
                    else:
                        return {
                            'status': 'COMPLETED',
                            'message': 'Tests executed but results file not found',
                            'summary': {}
                        }
                else:
                    return {
                        'status': 'COMPLETED',
                        'message': 'Test function not found, manual verification required',
                        'summary': {}
                    }
                    
            finally:
                # Restore original path
                sys.path = original_path
                
        except Exception as e:
            return {
                'status': 'FAILED',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def _calculate_final_results(self, start_time: float, end_time: float):
        """Calculate final aggregated results."""
        self.results['test_execution']['end_time'] = datetime.now().isoformat()
        self.results['test_execution']['duration_seconds'] = end_time - start_time
        
        # Aggregate all test results
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_duration = 0
        
        for module_name, module_result in self.results['module_results'].items():
            if 'summary' in module_result:
                summary = module_result['summary']
                total_tests += summary.get('total', 0)
                total_passed += summary.get('passed', 0)
                total_failed += summary.get('failed', 0)
                
                # Get duration from test results
                if 'duration' in module_result:
                    total_duration += module_result['duration']
            
            # Collect issues
            if 'errors' in module_result and module_result['errors']:
                self.results['issues_found'].extend(module_result['errors'])
        
        self.results['summary']['total_tests'] = total_tests
        self.results['summary']['total_passed'] = total_passed
        self.results['summary']['total_failed'] = total_failed
        self.results['summary']['total_errors'] = len(self.results['issues_found'])
        
        if total_tests > 0:
            self.results['summary']['success_rate'] = total_passed / total_tests
        
        if total_tests > 0:
            self.results['summary']['average_duration'] = total_duration / total_tests
    
    def _generate_recommendations(self):
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Check overall success rate
        success_rate = self.results['summary']['success_rate']
        if success_rate < 0.8:
            recommendations.append({
                'category': 'Overall Quality',
                'priority': 'High',
                'recommendation': f'Overall test success rate is {success_rate:.2%}, which is below the 80% threshold. Review failing tests and improve code quality.',
                'impact': 'Critical system reliability issues'
            })
        
        # Check for specific module issues
        for module_name, module_result in self.results['module_results'].items():
            if module_result.get('status') == 'FAILED':
                recommendations.append({
                    'category': 'Module Reliability',
                    'priority': 'High',
                    'recommendation': f'{module_name} test suite failed completely. Investigate module initialization and dependencies.',
                    'impact': 'Module is non-functional'
                })
            
            elif 'summary' in module_result:
                summary = module_result['summary']
                module_success_rate = summary.get('passed', 0) / max(1, summary.get('total', 1))
                
                if module_success_rate < 0.7:
                    recommendations.append({
                        'category': 'Module Quality',
                        'priority': 'Medium',
                        'recommendation': f'{module_name} has low test success rate ({module_success_rate:.2%}). Review failing tests and improve reliability.',
                        'impact': f'{module_name} functionality may be compromised'
                    })
        
        # Check for performance issues
        avg_duration = self.results['summary']['average_duration']
        if avg_duration > 10.0:
            recommendations.append({
                'category': 'Performance',
                'priority': 'Medium',
                'recommendation': f'Average test execution time ({avg_duration:.2f}s) is high. Consider optimizing test efficiency.',
                'impact': 'Long testing cycles and deployment delays'
            })
        
        # Check for common errors
        error_patterns = {}
        for issue in self.results['issues_found']:
            error_type = issue.get('error', 'Unknown')
            error_patterns[error_type] = error_patterns.get(error_type, 0) + 1
        
        frequent_errors = [error for error, count in error_patterns.items() if count > 2]
        if frequent_errors:
            recommendations.append({
                'category': 'Common Issues',
                'priority': 'Medium',
                'recommendation': f'Multiple tests failed with similar errors: {", ".join(frequent_errors)}. Address root causes.',
                'impact': 'Systematic issues affecting multiple components'
            })
        
        # Performance monitoring recommendations
        recommendations.append({
            'category': 'Monitoring',
            'priority': 'Low',
            'recommendation': 'Implement automated performance monitoring for all modules to track degradation over time.',
            'impact': 'Early detection of performance issues'
        })
        
        # Security recommendations
        recommendations.append({
            'category': 'Security',
            'priority': 'Medium',
            'recommendation': 'Add security testing to the test suite, including input validation and access control tests.',
            'impact': 'Security vulnerabilities may go undetected'
        })
        
        self.results['recommendations'] = recommendations
    
    def _save_results(self):
        """Save comprehensive test results."""
        # Save comprehensive report
        report_file = '/workspace/testing/module_testing_report.json'
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Comprehensive test results saved to {report_file}")
        
        # Generate and save markdown report
        self._generate_markdown_report()
    
    def _generate_markdown_report(self):
        """Generate a markdown report from the test results."""
        md_content = f"""# Comprehensive Module Testing Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

- **Total Test Suites:** {self.results['test_execution']['total_suites']}
- **Completed Suites:** {self.results['test_execution']['completed_suites']}
- **Failed Suites:** {self.results['test_execution']['failed_suites']}
- **Total Tests:** {self.results['summary']['total_tests']}
- **Tests Passed:** {self.results['summary']['total_passed']}
- **Tests Failed:** {self.results['summary']['total_failed']}
- **Success Rate:** {self.results['summary']['success_rate']:.2%}
- **Total Duration:** {self.results['test_execution']['duration_seconds']:.2f} seconds

## Module Test Results

"""
        
        for module_name, module_result in self.results['module_results'].items():
            md_content += f"### {module_name}\n\n"
            
            if 'status' in module_result:
                status = module_result['status']
                md_content += f"**Status:** {status}\n"
                
                if status == 'FAILED':
                    md_content += f"**Error:** {module_result.get('error', 'Unknown error')}\n\n"
                elif 'summary' in module_result:
                    summary = module_result['summary']
                    md_content += f"- **Tests Run:** {summary.get('total', 0)}\n"
                    md_content += f"- **Passed:** {summary.get('passed', 0)}\n"
                    md_content += f"- **Failed:** {summary.get('failed', 0)}\n"
                    if summary.get('total', 0) > 0:
                        success_rate = summary.get('passed', 0) / summary.get('total', 1)
                        md_content += f"- **Success Rate:** {success_rate:.2%}\n"
                    md_content += "\n"
            else:
                md_content += "No detailed results available.\n\n"
        
        # Add issues section
        if self.results['issues_found']:
            md_content += "## Issues Found\n\n"
            for i, issue in enumerate(self.results['issues_found'], 1):
                md_content += f"{i}. **{issue.get('test', 'Unknown Test')}** - {issue.get('error', 'Unknown error')}\n"
            md_content += "\n"
        
        # Add recommendations section
        if self.results['recommendations']:
            md_content += "## Recommendations\n\n"
            for rec in self.results['recommendations']:
                md_content += f"### {rec['category']} (Priority: {rec['priority']})\n"
                md_content += f"{rec['recommendation']}\n"
                md_content += f"*Impact:* {rec['impact']}\n\n"
        
        # Add detailed test results
        md_content += "## Detailed Test Results\n\n"
        for module_name, module_result in self.results['module_results'].items():
            if 'tests' in module_result:
                md_content += f"### {module_name} - Detailed Results\n\n"
                for test in module_result['tests']:
                    status_icon = "✅" if test['status'] == 'PASSED' else "❌"
                    md_content += f"- {status_icon} **{test['test_name']}** ({test['duration']:.2f}s)\n"
                    md_content += f"  - {test['message']}\n\n"
        
        # Save markdown report
        md_file = '/workspace/testing/module_testing_report.md'
        with open(md_file, 'w') as f:
            f.write(md_content)
        
        logger.info(f"Markdown report saved to {md_file}")


def main():
    """Main execution function."""
    runner = ComprehensiveTestRunner()
    
    try:
        results = runner.run_all_tests()
        return results
    except Exception as e:
        logger.error(f"Comprehensive test execution failed: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        raise


if __name__ == "__main__":
    main()
