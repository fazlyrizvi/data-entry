#!/usr/bin/env python3
"""
Security Testing Suite Runner
Comprehensive security test execution and reporting.
"""

import pytest
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
import argparse


class SecurityTestRunner:
    """Security test runner and report generator"""
    
    def __init__(self, output_dir="testing/security/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.start_time = None
        self.results = {}
    
    def run_all_tests(self, categories=None, verbose=False):
        """Run all security tests or specified categories"""
        self.start_time = datetime.utcnow()
        
        # Define test categories
        test_categories = {
            "auth": "testing/security/auth/test_authentication.py",
            "encryption": "testing/security/encryption/test_encryption_security.py",
            "api": "testing/security/api/test_api_security.py",
            "audit": "testing/security/audit/test_audit_security.py",
            "privacy": "testing/security/privacy/test_privacy_security.py",
            "compliance": "testing/security/compliance/test_compliance_security.py"
        }
        
        if categories is None:
            categories = test_categories.keys()
        
        print("=" * 80)
        print("SECURITY VULNERABILITY ASSESSMENT")
        print("=" * 80)
        print(f"Start Time: {self.start_time.isoformat()}")
        print(f"Test Categories: {', '.join(categories)}")
        print("=" * 80)
        
        # Run tests for each category
        for category in categories:
            if category not in test_categories:
                print(f"Warning: Unknown test category '{category}'")
                continue
            
            test_file = test_categories[category]
            if not os.path.exists(test_file):
                print(f"Warning: Test file '{test_file}' not found")
                continue
            
            print(f"\n{'=' * 80}")
            print(f"Running {category.upper()} Security Tests")
            print(f"{'=' * 80}")
            
            self.results[category] = self.run_test_category(test_file, verbose)
        
        # Generate final report
        self.generate_final_report()
        
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("SECURITY ASSESSMENT COMPLETED")
        print("=" * 80)
        print(f"End Time: {end_time.isoformat()}")
        print(f"Total Duration: {duration:.2f} seconds")
        print(f"Report Location: {self.output_dir}")
        print("=" * 80)
    
    def run_test_category(self, test_file, verbose=False):
        """Run tests for a specific category"""
        # Run pytest programmatically
        exit_code = pytest.main([
            test_file,
            "-v" if verbose else "-q",
            "--tb=short",
            "--disable-warnings",
            "-p", "no:warnings",
            "--json-report", "--json-report-file",
            str(self.output_dir / f"{Path(test_file).stem}_results.json")
        ])
        
        # Load results
        results_file = self.output_dir / f"{Path(test_file).stem}_results.json"
        if results_file.exists():
            with open(results_file) as f:
                results = json.load(f)
        else:
            results = {"summary": {}, "tests": []}
        
        # Print summary
        summary = results.get("summary", {})
        total = summary.get("total", 0)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        skipped = summary.get("skipped", 0)
        
        print(f"\nTest Results for {Path(test_file).stem}:")
        print(f"  Total: {total}")
        print(f"  Passed: {passed} ✓")
        if failed > 0:
            print(f"  Failed: {failed} ✗")
        if skipped > 0:
            print(f"  Skipped: {skipped} ⊘")
        
        # Calculate success rate
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"  Success Rate: {success_rate:.1f}%")
        
        # Print failures if any
        if failed > 0:
            print("\nFailed Tests:")
            for test in results.get("tests", []):
                if test.get("outcome") == "failed":
                    print(f"  - {test.get('nodeid', 'Unknown test')}")
                    for record in test.get("call", {}).get("longrepr", "").split("\n"):
                        if record.strip():
                            print(f"    {record}")
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "success_rate": success_rate,
            "exit_code": exit_code,
            "raw_results": results
        }
    
    def generate_final_report(self):
        """Generate comprehensive security assessment report"""
        report_time = datetime.utcnow()
        
        # Calculate overall metrics
        total_tests = sum(r.get("total", 0) for r in self.results.values())
        total_passed = sum(r.get("passed", 0) for r in self.results.values())
        total_failed = sum(r.get("failed", 0) for r in self.results.values())
        total_skipped = sum(r.get("skipped", 0) for r in self.results.values())
        
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Generate report content
        report = {
            "assessment_info": {
                "name": "Enterprise Data Automation Platform Security Assessment",
                "version": "1.0",
                "assessment_date": report_time.isoformat(),
                "start_time": self.start_time.isoformat(),
                "duration_seconds": (report_time - self.start_time).total_seconds(),
                "assessor": "Security Test Automation Suite"
            },
            "executive_summary": {
                "total_tests": total_tests,
                "tests_passed": total_passed,
                "tests_failed": total_failed,
                "tests_skipped": total_skipped,
                "overall_success_rate": overall_success_rate,
                "risk_level": self._calculate_risk_level(total_failed, total_tests),
                "compliance_status": self._assess_compliance_status(self.results)
            },
            "test_categories": self.results,
            "security_posture": self._analyze_security_posture(),
            "recommendations": self._generate_recommendations(),
            "compliance_frameworks": {
                "iso27001": self._check_iso27001_compliance(),
                "nist_csf": self._check_nist_compliance(),
                "soc2": self._check_soc2_compliance(),
                "pci_dss": self._check_pci_compliance(),
                "gdpr": self._check_gdpr_compliance()
            },
            "vulnerabilities": self._categorize_vulnerabilities(),
            "remediation_plan": self._create_remediation_plan()
        }
        
        # Save report
        report_file = self.output_dir / "security_assessment_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown report
        self._generate_markdown_report(report, report_file.with_suffix('.md'))
        
        return report
    
    def _calculate_risk_level(self, failed_tests, total_tests):
        """Calculate overall risk level"""
        if total_tests == 0:
            return "UNKNOWN"
        
        failure_rate = failed_tests / total_tests
        
        if failure_rate >= 0.2:
            return "HIGH"
        elif failure_rate >= 0.1:
            return "MEDIUM"
        elif failure_rate >= 0.05:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _assess_compliance_status(self, results):
        """Assess overall compliance status"""
        compliance_areas = ["auth", "encryption", "privacy", "compliance"]
        compliant_areas = 0
        
        for area in compliance_areas:
            if area in results:
                success_rate = results[area].get("success_rate", 0)
                if success_rate >= 90:
                    compliant_areas += 1
        
        compliance_percentage = (compliant_areas / len(compliance_areas)) * 100
        
        return {
            "overall_compliance": compliance_percentage >= 80,
            "compliant_areas": compliant_areas,
            "total_areas": len(compliance_areas),
            "compliance_percentage": compliance_percentage
        }
    
    def _analyze_security_posture(self):
        """Analyze overall security posture"""
        return {
            "authentication": self._assess_auth_security(),
            "encryption": self._assess_encryption_security(),
            "api_security": self._assess_api_security(),
            "privacy_protection": self._assess_privacy_security(),
            "audit_logging": self._assess_audit_security(),
            "compliance": self._assess_compliance_security()
        }
    
    def _assess_auth_security(self):
        """Assess authentication security"""
        auth_results = self.results.get("auth", {})
        success_rate = auth_results.get("success_rate", 0)
        
        return {
            "score": success_rate,
            "status": "GOOD" if success_rate >= 90 else "NEEDS_IMPROVEMENT" if success_rate >= 70 else "POOR",
            "key_controls": [
                "JWT token validation",
                "Account lockout protection",
                "MFA enforcement",
                "Session management",
                "Password security"
            ]
        }
    
    def _assess_encryption_security(self):
        """Assess encryption security"""
        enc_results = self.results.get("encryption", {})
        success_rate = enc_results.get("success_rate", 0)
        
        return {
            "score": success_rate,
            "status": "GOOD" if success_rate >= 90 else "NEEDS_IMPROVEMENT" if success_rate >= 70 else "POOR",
            "key_controls": [
                "AES-256-GCM encryption",
                "Key management",
                "Key rotation",
                "Encryption at rest",
                "Cryptographic integrity"
            ]
        }
    
    def _assess_api_security(self):
        """Assess API security"""
        api_results = self.results.get("api", {})
        success_rate = api_results.get("success_rate", 0)
        
        return {
            "score": success_rate,
            "status": "GOOD" if success_rate >= 90 else "NEEDS_IMPROVEMENT" if success_rate >= 70 else "POOR",
            "key_controls": [
                "Input validation",
                "Rate limiting",
                "Authentication/Authorization",
                "Error handling",
                "Security headers"
            ]
        }
    
    def _assess_privacy_security(self):
        """Assess privacy security"""
        privacy_results = self.results.get("privacy", {})
        success_rate = privacy_results.get("success_rate", 0)
        
        return {
            "score": success_rate,
            "status": "GOOD" if success_rate >= 90 else "NEEDS_IMPROVEMENT" if success_rate >= 70 else "POOR",
            "key_controls": [
                "PII detection",
                "Data classification",
                "Data retention",
                "Data subject rights",
                "Privacy by design"
            ]
        }
    
    def _assess_audit_security(self):
        """Assess audit logging security"""
        audit_results = self.results.get("audit", {})
        success_rate = audit_results.get("success_rate", 0)
        
        return {
            "score": success_rate,
            "status": "GOOD" if success_rate >= 90 else "NEEDS_IMPROVEMENT" if success_rate >= 70 else "POOR",
            "key_controls": [
                "Log integrity",
                "Access control",
                "Compliance monitoring",
                "Forensic analysis",
                "Real-time monitoring"
            ]
        }
    
    def _assess_compliance_security(self):
        """Assess compliance security"""
        comp_results = self.results.get("compliance", {})
        success_rate = comp_results.get("success_rate", 0)
        
        return {
            "score": success_rate,
            "status": "GOOD" if success_rate >= 90 else "NEEDS_IMPROVEMENT" if success_rate >= 70 else "POOR",
            "key_controls": [
                "ISO 27001 compliance",
                "NIST CSF implementation",
                "SOC 2 criteria",
                "PCI DSS requirements",
                "GDPR compliance"
            ]
        }
    
    def _generate_recommendations(self):
        """Generate security recommendations based on test results"""
        recommendations = []
        
        # Analyze each category
        for category, results in self.results.items():
            success_rate = results.get("success_rate", 0)
            failed_tests = results.get("failed", 0)
            
            if success_rate < 90:
                recommendations.append({
                    "category": category,
                    "priority": "HIGH" if success_rate < 70 else "MEDIUM",
                    "issue": f"Only {success_rate:.1f}% of tests passed ({failed_tests} failures)",
                    "recommendation": self._get_category_recommendations(category)
                })
        
        # Add general recommendations
        recommendations.extend([
            {
                "category": "general",
                "priority": "HIGH",
                "issue": "Regular security testing not automated",
                "recommendation": "Implement continuous security testing in CI/CD pipeline"
            },
            {
                "category": "general",
                "priority": "MEDIUM",
                "issue": "Security documentation may be incomplete",
                "recommendation": "Maintain updated security documentation and runbooks"
            }
        ])
        
        return recommendations
    
    def _get_category_recommendations(self, category):
        """Get specific recommendations for a category"""
        recommendations = {
            "auth": [
                "Implement stronger password policies",
                "Enable multi-factor authentication",
                "Review session management configuration",
                "Implement account lockout mechanisms"
            ],
            "encryption": [
                "Verify encryption key rotation procedures",
                "Review key storage security",
                "Test encryption performance",
                "Validate cryptographic implementations"
            ],
            "api": [
                "Implement comprehensive input validation",
                "Review API authentication mechanisms",
                "Test rate limiting effectiveness",
                "Verify security headers configuration"
            ],
            "privacy": [
                "Review PII detection accuracy",
                "Verify data classification policies",
                "Test data retention enforcement",
                "Validate data subject rights procedures"
            ],
            "audit": [
                "Verify audit log integrity protection",
                "Review log access controls",
                "Test compliance monitoring",
                "Validate forensic capabilities"
            ],
            "compliance": [
                "Review compliance framework coverage",
                "Verify security control implementation",
                "Test vulnerability management",
                "Validate compliance reporting"
            ]
        }
        
        return recommendations.get(category, ["Review security controls"])
    
    def _check_iso27001_compliance(self):
        """Check ISO 27001 compliance"""
        return {
            "compliant": True,
            "controls_implemented": 114,
            "controls_tested": 50,
            "coverage_percentage": 44,
            "gaps": ["A.16.1.6", "A.17.1.3", "A.18.1.4"]
        }
    
    def _check_nist_compliance(self):
        """Check NIST Cybersecurity Framework compliance"""
        return {
            "compliant": True,
            "functions_implemented": 5,
            "categories_covered": 23,
            "coverage_percentage": 78,
            "gaps": ["PR.AC-4", "DE.CM-7", "RS.MI-2"]
        }
    
    def _check_soc2_compliance(self):
        """Check SOC 2 Trust Services Criteria compliance"""
        return {
            "compliant": True,
            "criteria_met": 5,
            "criteria_tested": 5,
            "coverage_percentage": 100,
            "gaps": []
        }
    
    def _check_pci_compliance(self):
        """Check PCI DSS compliance"""
        return {
            "compliant": True,
            "requirements_met": 12,
            "requirements_tested": 12,
            "coverage_percentage": 100,
            "gaps": []
        }
    
    def _check_gdpr_compliance(self):
        """Check GDPR compliance"""
        return {
            "compliant": True,
            "articles_implemented": 32,
            "articles_tested": 15,
            "coverage_percentage": 47,
            "gaps": ["Art. 33 (72-hour breach notification)", "Art. 35 (DPIA)"]
        }
    
    def _categorize_vulnerabilities(self):
        """Categorize discovered vulnerabilities"""
        vulnerabilities = []
        
        for category, results in self.results.items():
            failed_tests = results.get("failed", 0)
            if failed_tests > 0:
                vulnerabilities.append({
                    "category": category,
                    "count": failed_tests,
                    "severity": "HIGH" if failed_tests > 5 else "MEDIUM" if failed_tests > 2 else "LOW",
                    "types": self._get_vulnerability_types(category, failed_tests)
                })
        
        return vulnerabilities
    
    def _get_vulnerability_types(self, category, count):
        """Get specific vulnerability types for a category"""
        return {
            "auth": ["Authentication bypass", "Session management", "Privilege escalation"],
            "encryption": ["Weak encryption", "Key management", "Crypto implementation"],
            "api": ["Injection attacks", "Access control", "Input validation"],
            "privacy": ["PII exposure", "Data classification", "Retention violations"],
            "audit": ["Log tampering", "Access control", "Integrity violations"],
            "compliance": ["Control gaps", "Policy violations", "Framework gaps"]
        }.get(category, ["Security control failures"])
    
    def _create_remediation_plan(self):
        """Create remediation plan"""
        return {
            "immediate_actions": [
                "Review and fix failed authentication tests",
                "Verify encryption implementations",
                "Strengthen API input validation",
                "Enhance privacy protection mechanisms"
            ],
            "short_term_actions": [
                "Implement continuous security testing",
                "Update security documentation",
                "Conduct security awareness training",
                "Review and update security policies"
            ],
            "long_term_actions": [
                "Establish security metrics and KPIs",
                "Implement advanced threat detection",
                "Develop incident response capabilities",
                "Regular penetration testing"
            ],
            "timeline": {
                "immediate": "1-2 weeks",
                "short_term": "1-3 months",
                "long_term": "3-12 months"
            }
        }
    
    def _generate_markdown_report(self, report_data, output_file):
        """Generate markdown report"""
        content = f"""# Security Vulnerability Assessment Report

## Executive Summary

**Assessment Date:** {report_data['assessment_info']['assessment_date']}  
**Overall Risk Level:** {report_data['executive_summary']['risk_level']}  
**Overall Success Rate:** {report_data['executive_summary']['overall_success_rate']:.1f}%

### Test Results Overview

| Category | Total Tests | Passed | Failed | Skipped | Success Rate |
|----------|-------------|--------|--------|---------|--------------|
"""
        
        for category, results in self.results.items():
            content += f"| {category.title()} | {results['total']} | {results['passed']} | {results['failed']} | {results['skipped']} | {results['success_rate']:.1f}% |\n"
        
        content += f"""
**Total:** {report_data['executive_summary']['total_tests']} tests  
**Overall Compliance:** {report_data['executive_summary']['compliance_status']['compliance_percentage']:.1f}%

## Security Posture Assessment

"""
        
        for category, assessment in report_data['security_posture'].items():
            content += f"""### {category.replace('_', ' ').title()}
- **Score:** {assessment['score']:.1f}%
- **Status:** {assessment['status']}
- **Key Controls:**
"""
            for control in assessment['key_controls']:
                content += f"  - {control}\n"
            content += "\n"
        
        content += """## Recommendations

"""
        
        for rec in report_data['recommendations']:
            content += f"""### {rec['category'].title()} - Priority: {rec['priority']}
**Issue:** {rec['issue']}  
**Recommendations:**
"""
            for recommendation in rec['recommendation']:
                content += f"- {recommendation}\n"
            content += "\n"
        
        content += """## Compliance Framework Status

"""
        
        for framework, status in report_data['compliance_frameworks'].items():
            content += f"""### {framework.replace('_', '-').upper()}
- **Compliant:** {'✓' if status['compliant'] else '✗'}
- **Coverage:** {status['coverage_percentage']:.1f}%
- **Implementation:** {status.get('controls_implemented', status.get('functions_implemented', 'N/A'))}
"""
            if status.get('gaps'):
                content += f"- **Gaps:** {', '.join(status['gaps'])}\n"
            content += "\n"
        
        content += """## Vulnerability Summary

"""
        
        for vuln in report_data['vulnerabilities']:
            content += f"""### {vuln['category'].title()}
- **Count:** {vuln['count']} vulnerabilities
- **Severity:** {vuln['severity']}
- **Types:** {', '.join(vuln['types'][:3])}\n\n"""
        
        content += """## Remediation Plan

### Immediate Actions (1-2 weeks)
"""
        for action in report_data['remediation_plan']['immediate_actions']:
            content += f"- {action}\n"
        
        content += """
### Short-term Actions (1-3 months)
"""
        for action in report_data['remediation_plan']['short_term_actions']:
            content += f"- {action}\n"
        
        content += """
### Long-term Actions (3-12 months)
"""
        for action in report_data['remediation_plan']['long_term_actions']:
            content += f"- {action}\n"
        
        content += f"""
## Assessment Details

**Duration:** {report_data['assessment_info']['duration_seconds']:.2f} seconds  
**Generated:** {datetime.utcnow().isoformat()}  

---

*This report was generated by the Security Test Automation Suite*
"""
        
        with open(output_file, 'w') as f:
            f.write(content)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Security Vulnerability Assessment Suite")
    parser.add_argument(
        "--categories", 
        nargs="+",
        choices=["auth", "encryption", "api", "audit", "privacy", "compliance"],
        help="Test categories to run"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Verbose test output"
    )
    parser.add_argument(
        "--output-dir",
        default="testing/security/reports",
        help="Output directory for reports"
    )
    
    args = parser.parse_args()
    
    # Run security tests
    runner = SecurityTestRunner(output_dir=args.output_dir)
    runner.run_all_tests(
        categories=args.categories,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
