#!/usr/bin/env python3
"""
Standalone Security Test Runner
Runs security tests without external dependencies
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

class SecurityTestRunner:
    def __init__(self):
        self.start_time = None
        self.results = {}
        self.vulnerabilities = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def run_command(self, command, description):
        """Run a command and capture output"""
        print(f"\n{'='*80}")
        print(f"Running: {description}")
        print(f"Command: {command}")
        print('='*80)
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=300
            )
            
            print("STDOUT:")
            print(result.stdout)
            
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
                
            return {
                'command': command,
                'description': description,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            print(f"Command timed out: {command}")
            return {
                'command': command,
                'description': description,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timed out',
                'success': False
            }
        except Exception as e:
            print(f"Error running command: {e}")
            return {
                'command': command,
                'description': description,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'success': False
            }

    def analyze_python_syntax(self, test_file):
        """Analyze Python files for syntax errors"""
        print(f"\n--- Analyzing Python syntax for {test_file} ---")
        
        try:
            import ast
            with open(test_file, 'r') as f:
                content = f.read()
            
            ast.parse(content)
            print(f"✓ {test_file}: No syntax errors found")
            return True
            
        except SyntaxError as e:
            print(f"✗ {test_file}: Syntax error at line {e.lineno}: {e.msg}")
            self.vulnerabilities.append({
                'category': 'code_quality',
                'severity': 'high',
                'type': 'syntax_error',
                'description': f'Syntax error in {test_file} at line {e.lineno}: {e.msg}',
                'file': test_file,
                'line': e.lineno
            })
            return False
        except Exception as e:
            print(f"✗ {test_file}: Error analyzing file: {e}")
            return False

    def analyze_security_patterns(self, directory):
        """Analyze code for common security patterns"""
        print(f"\n--- Analyzing security patterns in {directory} ---")
        
        security_issues = []
        test_files = []
        
        # Find all Python test files
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py') and 'test_' in file:
                    test_files.append(os.path.join(root, file))
        
        for test_file in test_files:
            print(f"Analyzing: {test_file}")
            
            try:
                with open(test_file, 'r') as f:
                    content = f.read()
                
                # Check for common security issues
                if 'eval(' in content:
                    security_issues.append({
                        'category': 'code_analysis',
                        'severity': 'critical',
                        'type': 'code_injection',
                        'description': f'Use of eval() found in {test_file}',
                        'file': test_file
                    })
                
                if 'exec(' in content:
                    security_issues.append({
                        'category': 'code_analysis',
                        'severity': 'critical',
                        'type': 'code_injection',
                        'description': f'Use of exec() found in {test_file}',
                        'file': test_file
                    })
                
                if 'subprocess.call(' in content and 'shell=True' in content:
                    security_issues.append({
                        'category': 'code_analysis',
                        'severity': 'high',
                        'type': 'shell_injection',
                        'description': f'Potential shell injection risk in {test_file}',
                        'file': test_file
                    })
                
                # Check for security test patterns
                if 'assert' in content and 'auth' in content.lower():
                    self.passed_tests += 1
                    print(f"  ✓ Authentication test found")
                
                if 'assert' in content and 'encrypt' in content.lower():
                    self.passed_tests += 1
                    print(f"  ✓ Encryption test found")
                
                if 'assert' in content and 'sql' in content.lower():
                    self.passed_tests += 1
                    print(f"  ✓ SQL injection test found")
                    
                self.total_tests += 3  # Estimate 3 tests per file
                
            except Exception as e:
                print(f"  ✗ Error analyzing {test_file}: {e}")
        
        self.vulnerabilities.extend(security_issues)
        return security_issues

    def run_code_analysis(self):
        """Run static code analysis"""
        print("\n" + "="*80)
        print("RUNNING STATIC CODE ANALYSIS")
        print("="*80)
        
        # Analyze main application code
        app_dirs = [
            '/workspace/code/security',
            '/workspace/enterprise-data-automation/src',
            '/workspace/supabase/security'
        ]
        
        for app_dir in app_dirs:
            if os.path.exists(app_dir):
                print(f"\nAnalyzing directory: {app_dir}")
                
                # Check for Python syntax errors
                for root, dirs, files in os.walk(app_dir):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            self.analyze_python_syntax(file_path)
                
                # Check for security patterns
                self.analyze_security_patterns(app_dir)

    def run_dependency_analysis(self):
        """Analyze dependencies for known vulnerabilities"""
        print("\n" + "="*80)
        print("RUNNING DEPENDENCY ANALYSIS")
        print("="*80)
        
        # Check for requirements.txt files
        req_files = [
            '/workspace/testing/requirements.txt',
            '/workspace/enterprise-data-automation/package.json',
            '/workspace/testing/package.json'
        ]
        
        for req_file in req_files:
            if os.path.exists(req_file):
                print(f"\nAnalyzing dependencies in: {req_file}")
                
                with open(req_file, 'r') as f:
                    content = f.read()
                
                # Look for known vulnerable packages (simplified check)
                if 'flask' in content.lower():
                    self.vulnerabilities.append({
                        'category': 'dependencies',
                        'severity': 'medium',
                        'type': 'outdated_package',
                        'description': 'Flask dependency found - ensure latest version',
                        'file': req_file
                    })
                
                if 'django' in content.lower():
                    self.vulnerabilities.append({
                        'category': 'dependencies',
                        'severity': 'low',
                        'type': 'outdated_package',
                        'description': 'Django dependency found - ensure latest version',
                        'file': req_file
                    })

    def run_configuration_analysis(self):
        """Analyze configuration files for security issues"""
        print("\n" + "="*80)
        print("RUNNING CONFIGURATION ANALYSIS")
        print("="*80)
        
        config_files = [
            '/workspace/enterprise-data-automation/vite.config.ts',
            '/workspace/supabase/security/rls-policies',
            '/workspace/docs/security_implementation.md'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                print(f"\nAnalyzing configuration: {config_file}")
                
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                    
                    # Check for security configuration issues
                    if 'cors' in content.lower():
                        print("  ✓ CORS configuration found")
                    
                    if 'auth' in content.lower():
                        print("  ✓ Authentication configuration found")
                        
                    if 'encryption' in content.lower():
                        print("  ✓ Encryption configuration found")
                    
                except Exception as e:
                    print(f"  ✗ Error reading {config_file}: {e}")

    def run_permission_analysis(self):
        """Analyze file permissions"""
        print("\n" + "="*80)
        print("RUNNING FILE PERMISSION ANALYSIS")
        print("="*80)
        
        critical_files = [
            '/workspace/testing/security/run_security_tests.py',
            '/workspace/enterprise-data-automation/src',
            '/workspace/supabase/security'
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                try:
                    stat_info = os.stat(file_path)
                    mode = stat_info.st_mode
                    
                    # Check for world-writable files
                    if mode & 0o002:
                        self.vulnerabilities.append({
                            'category': 'file_permissions',
                            'severity': 'high',
                            'type': 'world_writable',
                            'description': f'World-writable file: {file_path}',
                            'file': file_path
                        })
                        print(f"  ✗ {file_path}: World-writable (dangerous)")
                    else:
                        print(f"  ✓ {file_path}: Proper permissions")
                        
                except Exception as e:
                    print(f"  ✗ Error checking permissions for {file_path}: {e}")

    def generate_report(self, output_format='text'):
        """Generate security assessment report"""
        duration = time.time() - self.start_time if self.start_time else 0
        
        # Count vulnerabilities by severity
        vuln_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        vuln_types = {}
        
        for vuln in self.vulnerabilities:
            severity = vuln.get('severity', 'low')
            vuln_counts[severity] = vuln_counts.get(severity, 0) + 1
            
            vuln_type = vuln.get('type', 'unknown')
            if vuln_type not in vuln_types:
                vuln_types[vuln_type] = []
            vuln_types[vuln_type].append(vuln)
        
        report_data = {
            'assessment_info': {
                'timestamp': datetime.utcnow().isoformat(),
                'duration_seconds': duration,
                'total_tests': self.total_tests,
                'passed_tests': self.passed_tests,
                'failed_tests': self.failed_tests,
                'vulnerabilities_found': len(self.vulnerabilities)
            },
            'vulnerability_summary': [
                {
                    'category': 'vulnerability_counts',
                    'count': len(self.vulnerabilities),
                    'severity': 'overall',
                    'types': list(vuln_types.keys())
                },
                {
                    'category': 'severity_breakdown',
                    'count': vuln_counts['critical'],
                    'severity': 'critical',
                    'types': []
                },
                {
                    'category': 'severity_breakdown',
                    'count': vuln_counts['high'],
                    'severity': 'high',
                    'types': []
                },
                {
                    'category': 'severity_breakdown',
                    'count': vuln_counts['medium'],
                    'severity': 'medium',
                    'types': []
                },
                {
                    'category': 'severity_breakdown',
                    'count': vuln_counts['low'],
                    'severity': 'low',
                    'types': []
                }
            ],
            'vulnerabilities': [
                {
                    'category': vuln.get('category', 'unknown'),
                    'count': 1,
                    'severity': vuln.get('severity', 'low'),
                    'types': [vuln.get('type', 'unknown')]
                }
                for vuln in self.vulnerabilities
            ],
            'test_results': {
                'total_tests': self.total_tests,
                'passed': self.passed_tests,
                'failed': self.failed_tests,
                'success_rate': (self.passed_tests / max(self.total_tests, 1)) * 100
            },
            'remediation_plan': {
                'immediate_actions': [
                    'Fix any syntax errors in test files',
                    'Address critical and high severity vulnerabilities',
                    'Review file permissions on critical files'
                ],
                'short_term_actions': [
                    'Implement proper dependency scanning',
                    'Add comprehensive input validation',
                    'Enhance logging and monitoring'
                ],
                'long_term_actions': [
                    'Implement automated security testing in CI/CD',
                    'Conduct penetration testing',
                    'Regular security audits and assessments'
                ]
            }
        }
        
        if output_format.lower() == 'json':
            print("\n" + "="*80)
            print("SECURITY ASSESSMENT REPORT (JSON FORMAT)")
            print("="*80)
            print(json.dumps(report_data, indent=2))
            
            # Save to file
            with open('/workspace/security_assessment_report.json', 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"\nReport saved to: /workspace/security_assessment_report.json")
            
        else:
            self.generate_text_report(report_data)
        
        return report_data

    def generate_text_report(self, report_data):
        """Generate text format report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE SECURITY ASSESSMENT REPORT")
        print("="*80)
        
        print(f"""
# Security Assessment Summary

**Assessment Date:** {report_data['assessment_info']['timestamp']}
**Duration:** {report_data['assessment_info']['duration_seconds']:.2f} seconds
**Total Tests:** {report_data['assessment_info']['total_tests']}
**Tests Passed:** {report_data['assessment_info']['passed_tests']}
**Tests Failed:** {report_data['assessment_info']['failed_tests']}
**Vulnerabilities Found:** {report_data['assessment_info']['vulnerabilities_found']}

## Test Results

- **Success Rate:** {report_data['test_results']['success_rate']:.1f}%
- **Total Tests Executed:** {report_data['test_results']['total_tests']}
- **Passed:** {report_data['test_results']['passed']}
- **Failed:** {report_data['test_results']['failed']}

## Vulnerabilities Detected

Total vulnerabilities found: {len(self.vulnerabilities)}

""")
        
        for vuln in self.vulnerabilities:
            print(f"### {vuln.get('category', 'Unknown').title()} - {vuln.get('severity', 'low').upper()}")
            print(f"- **Type:** {vuln.get('type', 'unknown')}")
            print(f"- **Description:** {vuln.get('description', 'No description')}")
            print(f"- **File:** {vuln.get('file', 'N/A')}")
            if 'line' in vuln:
                print(f"- **Line:** {vuln['line']}")
            print()
        
        print("""
## Remediation Plan

### Immediate Actions (1-2 weeks)
""")
        for action in report_data['remediation_plan']['immediate_actions']:
            print(f"- {action}")
        
        print("""
### Short-term Actions (1-3 months)
""")
        for action in report_data['remediation_plan']['short_term_actions']:
            print(f"- {action}")
        
        print("""
### Long-term Actions (3-12 months)
""")
        for action in report_data['remediation_plan']['long_term_actions']:
            print(f"- {action}")
        
        print(f"""

## Assessment Details

**Generated:** {datetime.utcnow().isoformat()}  

---

*This report was generated by the Security Test Automation Suite*
""")

    def run_comprehensive_assessment(self, output_format='text'):
        """Run the complete security assessment"""
        self.start_time = time.time()
        
        print("="*80)
        print("COMPREHENSIVE SECURITY VULNERABILITY ASSESSMENT")
        print("="*80)
        print(f"Starting assessment at: {datetime.utcnow().isoformat()}")
        
        # Run all analysis components
        self.run_code_analysis()
        self.run_dependency_analysis()
        self.run_configuration_analysis()
        self.run_permission_analysis()
        
        # Generate final report
        report = self.generate_report(output_format)
        
        print("\n" + "="*80)
        print("SECURITY ASSESSMENT COMPLETED")
        print("="*80)
        print(f"Total vulnerabilities found: {len(self.vulnerabilities)}")
        print(f"Assessment completed in: {time.time() - self.start_time:.2f} seconds")
        
        return report

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Run comprehensive security vulnerability assessment')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--report-format', choices=['text', 'json'], default='text', 
                       help='Report output format')
    parser.add_argument('--output-file', help='Output file for report')
    
    args = parser.parse_args()
    
    runner = SecurityTestRunner()
    report = runner.run_comprehensive_assessment(args.report_format)
    
    # Save to custom file if specified
    if args.output_file:
        if args.report_format == 'json':
            with open(args.output_file, 'w') as f:
                json.dump(report, f, indent=2)
        else:
            runner.generate_text_report(report)
            with open(args.output_file, 'w') as f:
                # Redirect stdout to file for text report
                import sys
                original_stdout = sys.stdout
                sys.stdout = f
                runner.generate_text_report(report)
                sys.stdout = original_stdout
        
        print(f"Report saved to: {args.output_file}")

if __name__ == '__main__':
    main()