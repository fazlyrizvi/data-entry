"""
Webhook Signature Verification Module

Handles secure signature verification for webhook requests with support for
multiple signature algorithms and webhook providers.
"""

import hashlib
import hmac
import json
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import re


class SignatureVerificationError(Exception):
    """Exception raised when signature verification fails"""
    pass


class SignatureVerifier:
    """
    Handles webhook signature verification using various algorithms.
    Supports HMAC-SHA256, HMAC-SHA1, and RSA signatures.
    """
    
    # Supported signature algorithms
    SUPPORTED_ALGORITHMS = ['hmac-sha256', 'hmac-sha1', 'rsa-sha256', 'rsa-sha1']
    
    # Default timestamp tolerance (5 minutes)
    DEFAULT_TIMESTAMP_TOLERANCE = 300
    
    def __init__(self, secret_key: str, algorithm: str = 'hmac-sha256', 
                 timestamp_tolerance: Optional[int] = None):
        """
        Initialize signature verifier
        
        Args:
            secret_key: Secret key for HMAC or private key for RSA
            algorithm: Signature algorithm to use
            timestamp_tolerance: Tolerance for timestamp verification in seconds
        """
        self.secret_key = secret_key
        self.algorithm = algorithm.lower()
        self.timestamp_tolerance = timestamp_tolerance or self.DEFAULT_TIMESTAMP_TOLERANCE
        
        if self.algorithm not in self.SUPPORTED_ALGORITHMS:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    def verify_signature(self, payload: str, signature: str, 
                        headers: Optional[Dict[str, str]] = None,
                        timestamp: Optional[str] = None) -> Tuple[bool, str]:
        """
        Verify webhook signature
        
        Args:
            payload: Raw request payload
            signature: Signature from webhook request
            headers: Request headers for timestamp extraction
            timestamp: Optional timestamp header
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Extract timestamp if available
            webhook_timestamp = timestamp
            if headers and not timestamp:
                webhook_timestamp = headers.get('X-Webhook-Timestamp') or \
                                 headers.get('X-Timestamp') or \
                                 headers.get('X-Signature-Timestamp')
            
            if webhook_timestamp:
                if not self._verify_timestamp(webhook_timestamp):
                    return False, "Timestamp verification failed"
            
            # Verify signature based on algorithm
            if self.algorithm in ['hmac-sha256', 'hmac-sha1']:
                return self._verify_hmac_signature(payload, signature)
            elif self.algorithm in ['rsa-sha256', 'rsa-sha1']:
                return self._verify_rsa_signature(payload, signature)
            else:
                return False, f"Unsupported algorithm: {self.algorithm}"
                
        except Exception as e:
            return False, f"Signature verification error: {str(e)}"
    
    def _verify_timestamp(self, timestamp: str) -> bool:
        """
        Verify timestamp is within acceptable range
        
        Args:
            timestamp: Timestamp string
            
        Returns:
            True if timestamp is valid, False otherwise
        """
        try:
            # Try multiple timestamp formats
            formats = ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', 
                      '%Y-%m-%d %H:%M:%S', '%s']
            
            webhook_time = None
            for fmt in formats:
                try:
                    webhook_time = datetime.strptime(timestamp, fmt)
                    break
                except ValueError:
                    continue
            
            if webhook_time is None:
                return False
            
            # Check if timestamp is within tolerance
            now = datetime.utcnow()
            time_diff = abs((now - webhook_time).total_seconds())
            
            return time_diff <= self.timestamp_tolerance
            
        except Exception:
            return False
    
    def _verify_hmac_signature(self, payload: str, signature: str) -> Tuple[bool, str]:
        """
        Verify HMAC signature
        
        Args:
            payload: Request payload
            signature: Expected signature
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Compute expected signature
            if self.algorithm == 'hmac-sha256':
                expected_signature = hmac.new(
                    self.secret_key.encode('utf-8'),
                    payload.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
            elif self.algorithm == 'hmac-sha1':
                expected_signature = hmac.new(
                    self.secret_key.encode('utf-8'),
                    payload.encode('utf-8'),
                    hashlib.sha1
                ).hexdigest()
            else:
                return False, f"Unsupported HMAC algorithm: {self.algorithm}"
            
            # Compare signatures
            if self._constant_time_compare(signature, expected_signature):
                return True, "Signature verified successfully"
            else:
                return False, "Signature mismatch"
                
        except Exception as e:
            return False, f"HMAC verification error: {str(e)}"
    
    def _verify_rsa_signature(self, payload: str, signature: str) -> Tuple[bool, str]:
        """
        Verify RSA signature
        
        Args:
            payload: Request payload
            signature: Base64 encoded signature
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # For RSA verification, we would need the public key
            # This is a simplified implementation
            # In production, use proper RSA verification with cryptography library
            
            import base64
            from cryptography import x509
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            
            # Decode signature
            signature_bytes = base64.b64decode(signature)
            
            # Load public key (in practice, this would be loaded from configuration)
            public_key = serialization.load_pem_public_key(
                self.secret_key.encode('utf-8')
            )
            
            # Verify signature
            if self.algorithm == 'rsa-sha256':
                public_key.verify(
                    signature_bytes,
                    payload.encode('utf-8'),
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
            elif self.algorithm == 'rsa-sha1':
                public_key.verify(
                    signature_bytes,
                    payload.encode('utf-8'),
                    padding.PKCS1v15(),
                    hashes.SHA1()
                )
            
            return True, "RSA signature verified successfully"
            
        except ImportError:
            return False, "cryptography library required for RSA verification"
        except Exception as e:
            return False, f"RSA verification error: {str(e)}"
    
    def _constant_time_compare(self, a: str, b: str) -> bool:
        """
        Constant time string comparison to prevent timing attacks
        
        Args:
            a: First string
            b: Second string
            
        Returns:
            True if strings are equal, False otherwise
        """
        if len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        
        return result == 0
    
    def generate_signature(self, payload: str) -> str:
        """
        Generate signature for testing purposes
        
        Args:
            payload: Payload to sign
            
        Returns:
            Generated signature
        """
        if self.algorithm in ['hmac-sha256', 'hmac-sha1']:
            if self.algorithm == 'hmac-sha256':
                return hmac.new(
                    self.secret_key.encode('utf-8'),
                    payload.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
            elif self.algorithm == 'hmac-sha1':
                return hmac.new(
                    self.secret_key.encode('utf-8'),
                    payload.encode('utf-8'),
                    hashlib.sha1
                ).hexdigest()
        else:
            raise ValueError(f"Signature generation not implemented for {self.algorithm}")


class ProviderSignatureHandler:
    """
    Handles signature verification for different webhook providers
    """
    
    # Provider-specific configurations
    PROVIDER_CONFIGS = {
        'stripe': {
            'algorithm': 'hmac-sha256',
            'signature_header': 'Stripe-Signature',
            'timestamp_header': 'Stripe-Timestamp',
            'secret_prefix': 'whsec_'
        },
        'github': {
            'algorithm': 'hmac-sha256',
            'signature_header': 'X-Hub-Signature-256',
            'timestamp_header': 'X-GitHub-Delivery',
            'secret_prefix': ''
        },
        'slack': {
            'algorithm': 'hmac-sha256',
            'signature_header': 'X-Slack-Signature',
            'timestamp_header': 'X-Slack-Request-Timestamp',
            'secret_prefix': ''
        },
        'custom': {
            'algorithm': 'hmac-sha256',
            'signature_header': 'X-Webhook-Signature',
            'timestamp_header': 'X-Webhook-Timestamp',
            'secret_prefix': ''
        }
    }
    
    def __init__(self, provider: str, secret_key: str):
        """
        Initialize provider signature handler
        
        Args:
            provider: Webhook provider name
            secret_key: Secret key for verification
        """
        if provider not in self.PROVIDER_CONFIGS:
            raise ValueError(f"Unsupported provider: {provider}")
        
        self.provider = provider
        self.config = self.PROVIDER_CONFIGS[provider]
        
        # Handle secret key prefixes (e.g., Stripe's whsec_ prefix)
        if self.config.get('secret_prefix') and secret_key.startswith(self.config['secret_prefix']):
            secret_key = secret_key[len(self.config['secret_prefix']):]
        
        self.verifier = SignatureVerifier(
            secret_key=secret_key,
            algorithm=self.config['algorithm']
        )
    
    def verify_webhook(self, payload: str, headers: Dict[str, str]) -> Tuple[bool, str]:
        """
        Verify webhook using provider-specific configuration
        
        Args:
            payload: Request payload
            headers: Request headers
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Extract signature and timestamp
        signature = headers.get(self.config['signature_header'])
        timestamp = headers.get(self.config['timestamp_header'])
        
        if not signature:
            return False, f"Missing signature header: {self.config['signature_header']}"
        
        # Handle different signature formats
        if self.provider == 'stripe':
            signature = self._parse_stripe_signature(signature)
        elif self.provider == 'github':
            signature = signature.replace('sha256=', '')
        elif self.provider == 'slack':
            timestamp, signature = self._parse_slack_signature(signature, headers)
        
        # Verify signature
        return self.verifier.verify_signature(
            payload=payload,
            signature=signature,
            headers=headers,
            timestamp=timestamp
        )
    
    def _parse_stripe_signature(self, signature: str) -> str:
        """
        Parse Stripe signature header
        
        Args:
            signature: Stripe signature header
            
        Returns:
            Extracted signature
        """
        # Stripe signature format: t=timestamp,v1=signature
        parts = signature.split(',')
        for part in parts:
            if part.startswith('v1='):
                return part[3:]
        return signature
    
    def _parse_slack_signature(self, signature: str, headers: Dict[str, str]) -> Tuple[str, str]:
        """
        Parse Slack signature and timestamp
        
        Args:
            signature: Slack signature
            headers: Request headers
            
        Returns:
            Tuple of (timestamp, signature)
        """
        timestamp = headers.get('X-Slack-Request-Timestamp', '')
        # Slack signature format is already just the hash
        return timestamp, signature


def create_verifier(provider: str, secret_key: str) -> ProviderSignatureHandler:
    """
    Factory function to create signature verifier for a provider
    
    Args:
        provider: Webhook provider name
        secret_key: Secret key for verification
        
    Returns:
        ProviderSignatureHandler instance
    """
    return ProviderSignatureHandler(provider, secret_key)
