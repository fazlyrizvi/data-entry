#!/usr/bin/env python3
"""
Privacy Protection Security Testing Suite
Tests data privacy mechanisms, PII detection and protection, anonymization,
data subject rights, and privacy compliance.
"""

import pytest
import re
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Union
import sys
import os
import tempfile
import shutil

# Add the security module to the path
sys.path.append('/workspace/code/security/privacy')

from data_classifier import DataClassifier, SensitivityLevel, PrivacyCategory, DataSubject
from pii_detector import PIIDetector, PIIType, MaskingStrategy, PIIAnalysis
from retention_manager import RetentionManager, RetentionRule, DeletionMethod, RetentionReason


class TestPIIProtection:
    """Test suite for PII detection and protection"""
    
    @pytest.fixture
    def pii_detector(self):
        """Create PII detector instance"""
        return PIIDetector()
    
    @pytest.mark.security
    def test_email_detection(self, pii_detector):
        """Test email address PII detection"""
        test_cases = [
            {"text": "Contact: user@example.com", "expected": True},
            {"text": "john.doe@company.co.uk", "expected": True},
            {"text": "test.email+tag@domain.org", "expected": True},
            {"text": "invalid.email@", "expected": False},
            {"text": "notanemail", "expected": False},
        ]
        
        for case in test_cases:
            analysis = pii_detector.analyze_data(case["text"], "contact_info")
            emails_found = [m for m in analysis.matches if m.pii_type == PIIType.EMAIL]
            
            if case["expected"]:
                assert len(emails_found) > 0, f"Email not detected in: {case['text']}"
            else:
                assert len(emails_found) == 0, f"False positive email in: {case['text']}"
    
    @pytest.mark.security
    def test_ssn_detection(self, pii_detector):
        """Test SSN PII detection"""
        test_cases = [
            {"text": "SSN: 123-45-6789", "expected": True},
            {"text": "Social Security Number: 987654321", "expected": True},
            {"text": "SSN123456789", "expected": True},
            {"text": "123-45-678", "expected": False},  # Too short
            {"text": "123-45-67890", "expected": False},  # Too long
        ]
        
        for case in test_cases:
            analysis = pii_detector.analyze_data(case["text"], "personal_info")
            ssns_found = [m for m in analysis.matches if m.pii_type == PIIType.SSN]
            
            if case["expected"]:
                assert len(ssns_found) > 0, f"SSN not detected in: {case['text']}"
            else:
                assert len(ssns_found) == 0, f"False positive SSN in: {case['text']}"
    
    @pytest.mark.security
    def test_credit_card_detection(self, pii_detector):
        """Test credit card PII detection"""
        test_cases = [
            {"text": "Credit Card: 4111-1111-1111-1111", "expected": True},
            {"text": "Card: 5500-0000-0000-0004", "expected": True},
            {"text": "4111111111111111", "expected": True},
            {"text": "1234-5678-9012-3456", "expected": True},
            {"text": "1234-5678-9012", "expected": False},  # Too short
            {"text": "not a credit card", "expected": False},
        ]
        
        for case in test_cases:
            analysis = pii_detector.analyze_data(case["text"], "financial_info")
            cards_found = [m for m in analysis.matches if m.pii_type == PIIType.CREDIT_CARD]
            
            if case["expected"]:
                assert len(cards_found) > 0, f"Credit card not detected in: {case['text']}"
            else:
                assert len(cards_found) == 0, f"False positive credit card in: {case['text']}"
    
    @pytest.mark.security
    def test_phone_number_detection(self, pii_detector):
        """Test phone number PII detection"""
        test_cases = [
            {"text": "Phone: (555) 123-4567", "expected": True},
            {"text": "Mobile: +1-555-123-4567", "expected": True},
            {"text": "Call me at 5551234567", "expected": True},
            {"text": "Contact: +44 20 7946 0958", "expected": True},
            {"text": "123", "expected": False},  # Too short
        ]
        
        for case in test_cases:
            analysis = pii_detector.analyze_data(case["text"], "contact_info")
            phones_found = [m for m in analysis.matches if m.pii_type == PIIType.PHONE]
            
            if case["expected"]:
                assert len(phones_found) > 0, f"Phone number not detected in: {case['text']}"
            else:
                assert len(phones_found) == 0, f"False positive phone in: {case['text']}"
    
    @pytest.mark.security
    def test_ip_address_detection(self, pii_detector):
        """Test IP address detection"""
        test_cases = [
            {"text": "IP Address: 192.168.1.100", "expected": True},
            {"text": "Server: 10.0.0.1", "expected": True},
            {"text": "IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334", "expected": True},
            {"text": "Invalid IP: 999.999.999.999", "expected": False},
        ]
        
        for case in test_cases:
            analysis = pii_detector.analyze_data(case["text"], "network_info")
            ips_found = [m for m in analysis.matches if m.pii_type == PIIType.IP_ADDRESS]
            
            if case["expected"]:
                assert len(ips_found) > 0, f"IP address not detected in: {case['text']}"
            else:
                assert len(ips_found) == 0, f"False positive IP in: {case['text']}"
    
    @pytest.mark.security
    def test_address_detection(self, pii_detector):
        """Test physical address detection"""
        test_cases = [
            {"text": "Address: 123 Main Street, New York, NY 10001", "expected": True},
            {"text": "Lives at 456 Oak Ave, Los Angeles, CA", "expected": True},
            {"text": "1234 Elm Street, Suite 100", "expected": True},
            {"text": "No address here", "expected": False},
        ]
        
        for case in test_cases:
            analysis = pii_detector.analyze_data(case["text"], "address_info")
            addresses_found = [m for m in analysis.matches if m.pii_type == PIIType.ADDRESS]
            
            if case["expected"]:
                assert len(addresses_found) > 0, f"Address not detected in: {case['text']}"
            else:
                assert len(addresses_found) == 0, f"False positive address in: {case['text']}"
    
    @pytest.mark.security
    def test_pii_masking_strategies(self, pii_detector):
        """Test different PII masking strategies"""
        sensitive_text = "John Smith, email: john.smith@example.com, phone: 555-123-4567"
        
        # Test partial masking
        partially_masked = pii_detector.mask_pii(
            sensitive_text,
            strategy=MaskingStrategy.PARTIAL_MASK,
            preserve_format=True
        )
        
        assert "john.smith@example.com" not in partially_masked[0]
        assert "555-123-4567" not in partially_masked[0]
        
        # Test full masking
        fully_masked = pii_detector.mask_pii(
            sensitive_text,
            strategy=MaskingStrategy.FULL_MASK
        )
        
        # Should be completely different
        assert fully_masked[0] != sensitive_text
        assert "PII" in fully_masked[0] or "REDACTED" in fully_masked[0]
        
        # Test hashing
        hashed = pii_detector.mask_pii(
            sensitive_text,
            strategy=MaskingStrategy.HASHING
        )
        
        # Should produce consistent hashes
        hashed2 = pii_detector.mask_pii(
            sensitive_text,
            strategy=MaskingStrategy.HASHING
        )
        
        assert hashed[0] == hashed2[0]
    
    @pytest.mark.security
    def test_pii_anonymization(self, pii_detector):
        """Test irreversible PII anonymization"""
        sensitive_text = "Contact John Smith at john.smith@example.com, SSN: 123-45-6789"
        
        # Anonymize
        anonymized, analysis = pii_detector.anonymize_data(
            sensitive_text,
            irreversible=True
        )
        
        assert analysis.anonymized is True
        assert anonymized != sensitive_text
        
        # Original data should not be recoverable
        assert "john.smith@example.com" not in anonymized
        assert "123-45-6789" not in anonymized
        assert "John Smith" not in anonymized
    
    @pytest.mark.security
    def test_tokenization(self, pii_detector):
        """Test PII tokenization"""
        original_text = "John Smith, email: john.smith@example.com"
        
        # Create tokens
        tokenized, mapping = pii_detector.tokenize_pii(original_text)
        
        # Should replace PII with tokens
        assert "john.smith@example.com" not in tokenized
        assert "TOKEN_" in tokenized
        
        # Should have mapping
        assert len(mapping) > 0
        
        # Should be reversible
        restored = pii_detector.restore_from_tokens(tokenized, mapping)
        assert restored == original_text
    
    @pytest.mark.security
    def test_structured_data_pii_detection(self, pii_detector):
        """Test PII detection in structured data (JSON, dict)"""
        structured_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "age": 30,
            "phone": "+1-555-123-4567",
            "address": {
                "street": "123 Main St",
                "city": "New York"
            }
        }
        
        analysis = pii_detector.analyze_data(structured_data, "customer_record")
        
        # Should detect PII in nested structures
        assert analysis.total_pii_count > 0
        
        # Check specific PII types found
        pii_types = [match.pii_type for match in analysis.matches]
        assert PIIType.EMAIL in pii_types
        assert PIIType.PHONE in pii_types
    
    @pytest.mark.security
    def test_pii_risk_assessment(self, pii_detector):
        """Test PII risk assessment"""
        high_risk_data = "SSN: 123-45-6789, Credit Card: 4111-1111-1111-1111"
        low_risk_data = "Name: John Doe, Age: 30"
        
        high_risk_analysis = pii_detector.analyze_data(high_risk_data, "sensitive_info")
        low_risk_analysis = pii_detector.analyze_data(low_risk_data, "general_info")
        
        assert high_risk_analysis.risk_score > low_risk_analysis.risk_score
        assert high_risk_analysis.risk_score > 0.7
        assert low_risk_analysis.risk_score < 0.5
    
    @pytest.mark.security
    def test_false_positive_rate(self, pii_detector):
        """Test PII detection false positive rate"""
        # Test with non-PII data
        safe_texts = [
            "The email protocol uses @ symbol",
            "Phone numbers are 10 digits",
            "Credit card validation algorithms exist",
            "Social security numbers have format XXX-XX-XXXX",
            "IP addresses identify network devices"
        ]
        
        false_positives = 0
        total_tests = 0
        
        for text in safe_texts:
            analysis = pii_detector.analyze_data(text, "educational_content")
            total_tests += 1
            
            # Check if any PII was incorrectly detected
            for match in analysis.matches:
                if match.pii_type in [PIIType.EMAIL, PIIType.SSN, PIIType.CREDIT_CARD]:
                    false_positives += 1
        
        false_positive_rate = false_positives / total_tests
        assert false_positive_rate < 0.1, f"High false positive rate: {false_positive_rate}"


class TestDataClassification:
    """Test suite for data classification security"""
    
    @pytest.fixture
    def data_classifier(self):
        """Create data classifier instance"""
        return DataClassifier()
    
    @pytest.mark.security
    def test_automatic_data_classification(self, data_classifier):
        """Test automatic data sensitivity classification"""
        # Test customer data classification
        customer_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "555-123-4567"
        }
        
        classification = data_classifier.classify_data(
            data=customer_data,
            data_type="customer_record",
            purpose="customer_service",
            data_subject=DataSubject.CUSTOMER,
            legal_basis="consent"
        )
        
        assert classification.sensitivity_level in [
            SensitivityLevel.CONFIDENTIAL,
            SensitivityLevel.RESTRICTED
        ]
        
        assert classification.privacy_category == PrivacyCategory.PERSONAL_DATA
    
    @pytest.mark.security
    def test_classification_validation(self, data_classifier):
        """Test classification validation"""
        # Create invalid classification
        invalid_classification = {
            "sensitivity": "invalid_level",
            "privacy_category": "invalid_category"
        }
        
        try:
            classification = data_classifier.classify_data(
                data={"test": "data"},
                data_type="test",
                purpose="test",
                manual_classification=invalid_classification
            )
            assert False, "Should have rejected invalid classification"
        except ValueError:
            pass  # Expected
    
    @pytest.mark.security
    def test_privacy_label_generation(self, data_classifier):
        """Test privacy label generation"""
        classification = data_classifier.classify_data(
            data={"name": "John Doe", "ssn": "123-45-6789"},
            data_type="medical_record",
            purpose="healthcare",
            data_subject=DataSubject.PATIENT,
            legal_basis="medical_necessity"
        )
        
        labels = data_classifier.generate_privacy_labels(classification)
        
        assert "sensitivity_level" in labels
        assert "privacy_category" in labels
        assert "legal_basis" in labels
        assert "data_subject" in labels
    
    @pytest.mark.security
    def test_classification_enforcement(self, data_classifier):
        """Test classification-based access control"""
        # Classify data with different sensitivity levels
        public_data = data_classifier.classify_data(
            data={"public_info": "general announcement"},
            data_type="announcement",
            purpose="information_sharing",
            data_subject=DataSubject.PUBLIC,
            legal_basis="legitimate_interest"
        )
        
        confidential_data = data_classifier.classify_data(
            data={"customer_info": "personal details"},
            data_type="customer_record",
            purpose="customer_service",
            data_subject=DataSubject.CUSTOMER,
            legal_basis="consent"
        )
        
        # Test access control based on classification
        can_access_public = data_classifier.check_access_permission(
            classification=public_data,
            user_role="ANONYMOUS",
            action="read"
        )
        
        can_access_confidential = data_classifier.check_access_permission(
            classification=confidential_data,
            user_role="ANONYMOUS",
            action="read"
        )
        
        assert can_access_public is True
        assert can_access_confidential is False
    
    @pytest.mark.security
    def test_classification_audit_trail(self, data_classifier):
        """Test classification change audit trail"""
        # Classify data
        classification = data_classifier.classify_data(
            data={"test": "data"},
            data_type="test_type",
            purpose="testing"
        )
        
        classification_id = classification.id
        
        # Update classification
        updated = data_classifier.update_classification(
            classification_id=classification_id,
            sensitivity_level=SensitivityLevel.CONFIDENTIAL
        )
        
        # Should log the change
        audit_logs = data_classifier.get_classification_audit_logs(classification_id)
        assert len(audit_logs) > 0
        
        # Verify audit log details
        audit_log = audit_logs[0]
        assert audit_log["action"] == "classification_update"
        assert "timestamp" in audit_log


class TestDataRetentionManagement:
    """Test suite for data retention management"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp(prefix="retention_test_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def retention_manager(self, temp_dir):
        """Create retention manager instance"""
        return RetentionManager(os.path.join(temp_dir, "retention.db"))
    
    @pytest.mark.security
    def test_data_retention_policy(self, retention_manager):
        """Test data retention policy enforcement"""
        # Register data with retention policy
        record = retention_manager.register_data(
            data_identifier="customer_123",
            data_type="customer_record",
            location="/data/customers/customer_123.json"
        )
        
        assert record.status == "ACTIVE"
        assert record.expiry_date is not None
        
        # Access data (should update access count)
        accessed = retention_manager.access_data("customer_123")
        assert accessed.access_count == 1
    
    @pytest.mark.security
    def test_automatic_retention_enforcement(self, retention_manager):
        """Test automatic retention policy enforcement"""
        # Create custom rule with short retention
        custom_rule = RetentionRule(
            id="short_retention",
            name="Short Retention Test",
            description="Test rule with 1 second retention",
            data_types=["test_data"],
            retention_period=timedelta(seconds=1),
            legal_basis="testing",
            reason=RetentionReason.TESTING,
            auto_deletion=True,
            secure_deletion=True,
            deletion_method=DeletionMethod.SIMPLE_DELETE
        )
        
        retention_manager.db.save_retention_rule(custom_rule)
        
        # Register data with short retention
        record = retention_manager.register_data(
            data_identifier="test_data_123",
            data_type="test_data",
            location="/tmp/test_data.txt",
            rule_id="short_retention"
        )
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Execute retention policy
        result = retention_manager.execute_retention_policy()
        
        # Should have processed expired data
        assert result["total_expired"] > 0
        assert result["auto_deleted"] >= 0
    
    @pytest.mark.security
    def test_secure_deletion(self, retention_manager):
        """Test secure data deletion methods"""
        # Create test file
        test_file = "/tmp/secure_delete_test.txt"
        with open(test_file, "w") as f:
            f.write("Sensitive data that needs secure deletion" * 100)
        
        # Register for retention
        record = retention_manager.register_data(
            data_identifier="secure_delete_test",
            data_type="test_data",
            location=test_file,
            retention_period=timedelta(seconds=0)
        )
        
        # Delete with different methods
        deletion_methods = [
            DeletionMethod.SIMPLE_DELETE,
            DeletionMethod.ZERO_OVERWRITE,
            DeletionMethod.DOD_5220_22_M
        ]
        
        for method in deletion_methods:
            # Create new test file for each method
            test_file_method = f"/tmp/secure_delete_test_{method.value}.txt"
            with open(test_file_method, "w") as f:
                f.write("Sensitive data" * 100)
            
            # Perform secure deletion
            success = retention_manager.secure_delete_data(
                data_identifier=f"test_{method.value}",
                location=test_file_method,
                deletion_method=method
            )
            
            assert success is True
            
            # Verify file is deleted
            assert not os.path.exists(test_file_method)
    
    @pytest.mark.security
    def test_retention_extensions(self, retention_manager):
        """Test retention period extensions"""
        # Register data
        record = retention_manager.register_data(
            data_identifier="extend_test",
            data_type="test_data",
            location="/tmp/extend_test.txt"
        )
        
        original_expiry = record.expiry_date
        
        # Extend retention
        success = retention_manager.extend_retention(
            data_identifier="extend_test",
            additional_period=timedelta(days=30),
            reason="Legal investigation",
            extended_by="legal_team"
        )
        
        assert success is True
        
        # Check updated expiry date
        updated_record = retention_manager.db.get_retention_record("extend_test")
        new_expiry = updated_record.expiry_date
        
        # Expiry should be later
        assert new_expiry > original_expiry
    
    @pytest.mark.security
    def test_retention_legal_holds(self, retention_manager):
        """Test legal hold functionality"""
        # Register data
        record = retention_manager.register_data(
            data_identifier="legal_hold_test",
            data_type="test_data",
            location="/tmp/legal_hold_test.txt"
        )
        
        # Apply legal hold
        success = retention_manager.apply_legal_hold(
            data_identifier="legal_hold_test",
            hold_reason="Litigation hold",
            held_by="legal_team",
            hold_until=datetime.utcnow() + timedelta(days=90)
        )
        
        assert success is True
        
        # Check hold status
        hold_status = retention_manager.get_legal_hold_status("legal_hold_test")
        assert hold_status["is_on_hold"] is True
        assert hold_status["hold_reason"] == "Litigation hold"
    
    @pytest.mark.security
    def test_retention_compliance_reporting(self, retention_manager):
        """Test retention compliance reporting"""
        # Register multiple data items
        for i in range(10):
            retention_manager.register_data(
                data_identifier=f"compliance_test_{i}",
                data_type="customer_data",
                location=f"/tmp/compliance_test_{i}.txt"
            )
        
        # Generate compliance report
        report = retention_manager.generate_compliance_report()
        
        assert "total_registered" in report
        assert "expired_items" in report
        assert "compliance_status" in report
        assert report["total_registered"] == 10


class TestDataSubjectRights:
    """Test suite for data subject rights (GDPR)"""
    
    @pytest.fixture
    def privacy_system(self, tmp_path):
        """Create privacy system components"""
        classifier = DataClassifier()
        detector = PIIDetector()
        retention_manager = RetentionManager(str(tmp_path / "privacy.db"))
        return {
            "classifier": classifier,
            "detector": detector,
            "retention": retention_manager
        }
    
    @pytest.mark.security
    def test_right_of_access(self, privacy_system):
        """Test data subject right of access"""
        # Simulate user requesting their data
        user_id = "user_123"
        
        # Register user data
        privacy_system["retention"].register_data(
            data_identifier=f"{user_id}_profile",
            data_type="user_profile",
            location=f"/data/users/{user_id}/profile.json",
            retention_metadata={"user_id": user_id, "data_type": "profile"}
        )
        
        privacy_system["retention"].register_data(
            data_identifier=f"{user_id}_activity",
            data_type="user_activity",
            location=f"/data/users/{user_id}/activity.json",
            retention_metadata={"user_id": user_id, "data_type": "activity"}
        )
        
        # Process access request
        access_result = privacy_system["detector"].process_data_subject_request(
            request_type="access",
            user_id=user_id
        )
        
        assert access_result["success"] is True
        assert "data_items" in access_result
        assert len(access_result["data_items"]) > 0
    
    @pytest.mark.security
    def test_right_to_rectification(self, privacy_system):
        """Test data subject right to rectification"""
        user_id = "user_123"
        
        # Register data
        privacy_system["retention"].register_data(
            data_identifier=f"{user_id}_profile",
            data_type="user_profile",
            location=f"/data/users/{user_id}/profile.json",
            retention_metadata={"user_id": user_id, "correct": False}
        )
        
        # Process rectification request
        rectification_result = privacy_system["detector"].process_data_subject_request(
            request_type="rectification",
            user_id=user_id,
            corrections={"name": "John Doe", "email": "john.doe@example.com"}
        )
        
        assert rectification_result["success"] is True
        assert "corrected_data" in rectification_result
    
    @pytest.mark.security
    def test_right_to_erasure(self, privacy_system):
        """Test data subject right to erasure (right to be forgotten)"""
        user_id = "user_123"
        
        # Register user data
        for i in range(3):
            privacy_system["retention"].register_data(
                data_identifier=f"{user_id}_data_{i}",
                data_type="user_data",
                location=f"/data/users/{user_id}/data_{i}.json",
                retention_metadata={"user_id": user_id, "index": i}
            )
        
        # Process erasure request
        erasure_result = privacy_system["detector"].process_data_subject_request(
            request_type="erasure",
            user_id=user_id,
            legal_basis="user_consent_withdrawn"
        )
        
        assert erasure_result["success"] is True
        assert "deleted_items" in erasure_result
        assert erasure_result["deleted_items"] == 3
    
    @pytest.mark.security
    def test_right_to_data_portability(self, privacy_system):
        """Test data subject right to data portability"""
        user_id = "user_123"
        
        # Register structured data
        privacy_system["retention"].register_data(
            data_identifier=f"{user_id}_structured",
            data_type="user_profile",
            location=f"/data/users/{user_id}/profile.json",
            retention_metadata={"user_id": user_id, "structured": True}
        )
        
        # Process portability request
        portability_result = privacy_system["detector"].process_data_subject_request(
            request_type="portability",
            user_id=user_id,
            format="json"
        )
        
        assert portability_result["success"] is True
        assert "exported_data" in portability_result
        assert portability_result["format"] == "json"
    
    @pytest.mark.security
    def test_right_to_object(self, privacy_system):
        """Test data subject right to object"""
        user_id = "user_123"
        
        # Process objection request
        objection_result = privacy_system["detector"].process_data_subject_request(
            request_type="object",
            user_id=user_id,
            objection_basis="legitimate_interest",
            processing_type="marketing"
        )
        
        assert objection_result["success"] is True
        assert "objection_registered" in objection_result
    
    @pytest.mark.security
    def test_automated_decision_making_rights(self, privacy_system):
        """Test rights related to automated decision making"""
        user_id = "user_123"
        
        # Check automated decision making
        adm_check = privacy_system["detector"].check_automated_decision_making(
            user_id=user_id,
            decision_type="credit_scoring"
        )
        
        assert "has_adm" in adm_check
        assert "human_review_available" in adm_check
        assert "explanation_available" in adm_check


class TestPrivacyByDesign:
    """Test suite for privacy by design implementation"""
    
    @pytest.fixture
    def privacy_system(self):
        """Create privacy system"""
        return {
            "classifier": DataClassifier(),
            "detector": PIIDetector(),
            "retention": RetentionManager()
        }
    
    @pytest.mark.security
    def test_data_minimization(self, privacy_system):
        """Test data minimization principle"""
        # Request data with minimization
        full_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "555-123-4567",
            "address": "123 Main St",
            "ssn": "123-45-6789",
            "age": 30,
            "gender": "M",
            "occupation": "Engineer"
        }
        
        required_fields = ["name", "email"]
        
        minimized_data = privacy_system["classifier"].minimize_data(
            full_data, required_fields
        )
        
        assert len(minimized_data) == 2
        assert "name" in minimized_data
        assert "email" in minimized_data
        assert "ssn" not in minimized_data
        assert "phone" not in minimized_data
    
    @pytest.mark.security
    def test_purpose_limitation(self, privacy_system):
        """Test purpose limitation principle"""
        customer_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "order_history": ["order1", "order2"]
        }
        
        # Classify for specific purpose
        classification = privacy_system["classifier"].classify_data(
            data=customer_data,
            data_type="customer_data",
            purpose="order_fulfillment",
            data_subject=DataSubject.CUSTOMER,
            legal_basis="contract_performance"
        )
        
        # Check if purpose is enforced
        can_use_for_marketing = privacy_system["classifier"].check_purpose_compatibility(
            classification=classification,
            requested_purpose="direct_marketing"
        )
        
        assert can_use_for_marketing is False
        
        can_use_for_fulfillment = privacy_system["classifier"].check_purpose_compatibility(
            classification=classification,
            requested_purpose="order_fulfillment"
        )
        
        assert can_use_for_fulfillment is True
    
    @pytest.mark.security
    def test_storage_limitation(self, privacy_system):
        """Test storage limitation principle"""
        # Test with short retention period
        short_retention = RetentionRule(
            id="short_storage",
            name="Short Storage Test",
            data_types=["test"],
            retention_period=timedelta(days=1),
            legal_basis="consent",
            reason=RetentionReason.CONSENT_WITHDRAWN,
            auto_deletion=True,
            secure_deletion=True
        )
        
        retention_manager = privacy_system["retention"]
        retention_manager.db.save_retention_rule(short_retention)
        
        # Data should be automatically deleted
        assert short_retention.auto_deletion is True
    
    @pytest.mark.security
    def test_default_privacy_settings(self, privacy_system):
        """Test default privacy settings"""
        # Most restrictive defaults should be applied
        default_config = privacy_system["classifier"].get_default_config()
        
        assert default_config["default_sensitivity"] in [
            SensitivityLevel.CONFIDENTIAL,
            SensitivityLevel.RESTRICTED
        ]
        assert default_config["default_encryption"] is True
        assert default_config["default_retention_days"] <= 365
    
    @pytest.mark.security
    def test_integrity_and_confidentiality(self, privacy_system):
        """Test integrity and confidentiality measures"""
        sensitive_data = {"ssn": "123-45-6789", "credit_card": "4111-1111-1111-1111"}
        
        # Data should be encrypted when classified as sensitive
        classification = privacy_system["classifier"].classify_data(
            data=sensitive_data,
            data_type="sensitive_record",
            purpose="storage",
            data_subject=DataSubject.CUSTOMER,
            legal_basis="consent"
        )
        
        assert classification.requires_encryption is True
        assert classification.sensitivity_level in [
            SensitivityLevel.CONFIDENTIAL,
            SensitivityLevel.RESTRICTED,
            SensitivityLevel.TOP_SECRET
        ]


class TestPrivacyCompliance:
    """Test suite for privacy compliance monitoring"""
    
    @pytest.mark.security
    def test_gdpr_compliance_check(self, privacy_system):
        """Test GDPR compliance checking"""
        # Test various GDPR requirements
        compliance_checks = {
            "data_classification": True,
            "consent_management": True,
            "retention_policies": True,
            "data_subject_rights": True,
            "breach_notification": True,
            "dpo_appointed": True,
            "privacy_impact_assessment": True
        }
        
        gdpr_score = privacy_system["detector"].calculate_gdpr_compliance_score(
            compliance_checks
        )
        
        assert 0 <= gdpr_score <= 100
        assert gdpr_score == 100  # All checks passed
    
    @pytest.mark.security
    def test_ccpa_compliance_check(self, privacy_system):
        """Test CCPA compliance checking"""
        ccpa_checks = {
            "privacy_notice": True,
            "opt_out_mechanism": True,
            "data_disclosure_records": True,
            "consumer_rights_processing": True,
            "third_party_contracts": True
        }
        
        ccpa_score = privacy_system["detector"].calculate_ccpa_compliance_score(
            ccpa_checks
        )
        
        assert 0 <= ccpa_score <= 100
        assert ccpa_score == 100
    
    @pytest.mark.security
    def test_privacy_impact_assessment(self, privacy_system):
        """Test Privacy Impact Assessment (PIA)"""
        processing_activity = {
            "data_types": ["personal_data", "sensitive_data"],
            "data_subjects": ["customers", "employees"],
            "processing_purposes": ["marketing", "analytics"],
            "data_sources": ["website", "mobile_app", "third_party"],
            "retention_period": timedelta(days=730),
            "international_transfers": True,
            "automated_decision_making": True
        }
        
        pia_result = privacy_system["detector"].conduct_privacy_impact_assessment(
            processing_activity
        )
        
        assert "risk_score" in pia_result
        assert "risks_identified" in pia_result
        assert "mitigation_measures" in pia_result
        assert 0 <= pia_result["risk_score"] <= 1
    
    @pytest.mark.security
    def test_breach_notification_assessment(self, privacy_system):
        """Test data breach notification requirements"""
        breach_scenario = {
            "data_types": ["personal_data"],
            "affected_individuals": 1000,
            "likelihood_of_harm": "medium",
            "data_encrypted": True,
            "breach_contained": True
        }
        
        notification_assessment = privacy_system["detector"].assess_breach_notification_requirements(
            breach_scenario
        )
        
        assert "notification_required" in notification_assessment
        assert "authority_notification_deadline" in notification_assessment
        assert "individual_notification_required" in notification_assessment


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "security"])
