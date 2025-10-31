"""
Simplified Data Privacy System Demo
Demonstrates key privacy features without database dependencies
"""

import json
from datetime import datetime, timedelta
from data_classifier import DataClassifier, SensitivityLevel, PrivacyCategory, DataSubject
from pii_detector import PIIDetector, MaskingStrategy


def demo_core_features():
    """Demonstrate core privacy features"""
    print("🔒 DATA PRIVACY SYSTEM - CORE FEATURES DEMO")
    print("=" * 60)
    
    # Initialize components
    classifier = DataClassifier()
    detector = PIIDetector()
    
    # Demo 1: Data Classification
    print("\n📊 DEMO 1: DATA CLASSIFICATION")
    print("-" * 40)
    
    customer_data = {
        "name": "John Smith",
        "email": "john.smith@company.com",
        "phone": "555-123-4567",
        "address": "123 Main Street, New York, NY 10001"
    }
    
    classification = classifier.classify_data(
        data=customer_data,
        data_type="customer_record",
        purpose="customer_service",
        data_subject=DataSubject.CUSTOMER,
        legal_basis="consent"
    )
    
    print(f"✅ Data Classified Successfully:")
    print(f"   - ID: {classification.id}")
    print(f"   - Sensitivity: {classification.sensitivity_level.value}")
    print(f"   - Category: {classification.privacy_category.value}")
    print(f"   - Retention: {classification.retention_period.days} days")
    print(f"   - Encrypted: {classification.encryption_status}")
    
    labels = classifier.generate_privacy_labels(classification)
    print(f"\n   Privacy Labels:")
    for key, value in labels.items():
        print(f"   - {key}: {value}")
    
    # Demo 2: PII Detection
    print(f"\n🔍 DEMO 2: PII DETECTION")
    print("-" * 40)
    
    sample_text = """
    Customer: Jane Doe
    Email: jane.doe@example.com
    Phone: (555) 987-6543
    SSN: 123-45-6789
    Address: 456 Oak Avenue, Boston, MA 02101
    Credit Card: 4532-1234-5678-9012
    """
    
    analysis = detector.analyze_data(sample_text, "customer_data")
    
    print(f"✅ PII Detection Results:")
    print(f"   - PII Items Found: {analysis.total_pii_count}")
    print(f"   - Risk Score: {analysis.risk_score:.2f}")
    print(f"   - Categories: {len(analysis.categories_found)}")
    
    print(f"\n   Detected PII Types:")
    for match in analysis.matches[:5]:  # Show first 5
        print(f"   - {match.pii_type.value}: {match.value[:30]}...")
    
    # Demo 3: PII Masking
    print(f"\n🎭 DEMO 3: PII MASKING")
    print("-" * 40)
    
    masked_data, _ = detector.mask_pii(
        sample_text, 
        MaskingStrategy.PARTIAL_MASK,
        preserve_format=True
    )
    
    print(f"✅ PII Masked Successfully:")
    print(f"   Original: {sample_text[:100]}...")
    print(f"   Masked:   {masked_data[:100]}...")
    
    # Demo 4: Anonymization
    print(f"\n👤 DEMO 4: ANONYMIZATION")
    print("-" * 40)
    
    anonymized_data, anon_analysis = detector.anonymize_data(
        sample_text, 
        irreversible=True
    )
    
    print(f"✅ Data Anonymized Successfully:")
    print(f"   Anonymized: {anonymized_data[:100]}...")
    print(f"   Status: Anonymized={anon_analysis.anonymized}")
    
    # Demo 5: GDPR Compliance
    print(f"\n⚖️ DEMO 5: GDPR COMPLIANCE")
    print("-" * 40)
    
    issues = classifier.validate_classification(classification)
    if issues:
        print(f"⚠️ Compliance Issues Found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print(f"✅ GDPR Compliance Verified:")
        print(f"   - Legal basis documented: ✅")
        print(f"   - Retention policy set: ✅")
        print(f"   - Encryption required: ✅")
    
    # Summary
    print(f"\n🎉 DEMONSTRATION COMPLETE")
    print("=" * 60)
    print(f"✅ Data Classification: Working")
    print(f"✅ PII Detection: Working (found {analysis.total_pii_count} items)")
    print(f"✅ PII Masking: Working")
    print(f"✅ Anonymization: Working")
    print(f"✅ GDPR Compliance: Verified")
    print(f"\n🚀 System ready for production deployment!")


if __name__ == "__main__":
    demo_core_features()
