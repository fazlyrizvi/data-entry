#!/usr/bin/env python3
"""
Performance Testing Launcher
============================

Simple launcher script for running performance tests.
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add testing module to path
sys.path.insert(0, str(Path(__file__).parent))

from performance_test_orchestrator import PerformanceTestOrchestrator


def main():
    """Main entry point for performance testing."""
    parser = argparse.ArgumentParser(description="Run performance tests for data automation system")
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to configuration file",
        default="performance_test_config.json"
    )
    parser.add_argument(
        "--smoke-test", 
        action="store_true", 
        help="Run quick smoke test only"
    )
    parser.add_argument(
        "--component", 
        type=str, 
        choices=["ocr", "nlp", "parallel", "all"],
        default="all",
        help="Run tests for specific component(s)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    import logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level)
    
    print("="*80)
    print("DATA AUTOMATION SYSTEM PERFORMANCE TESTING")
    print("="*80)
    print(f"Configuration: {args.config}")
    print(f"Component: {args.component}")
    print(f"Mode: {'Smoke Test' if args.smoke_test else 'Full Test'}")
    print("="*80)
    
    try:
        # Initialize orchestrator
        orchestrator = PerformanceTestOrchestrator(args.config)
        
        # Run tests based on arguments
        if args.smoke_test:
            print("Running smoke test...")
            results = asyncio.run(orchestrator.run_smoke_tests())
        else:
            print("Running comprehensive performance tests...")
            results = asyncio.run(orchestrator.run_comprehensive_tests())
        
        # Save results
        orchestrator.save_raw_results()
        
        print("\n" + "="*80)
        print("PERFORMANCE TESTING COMPLETED")
        print("="*80)
        print(f"Test Duration: {results['test_duration']}")
        print(f"Results saved to: testing/results/")
        print(f"Report generated: testing/performance_testing_report.md")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\nPerformance testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Performance testing failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()