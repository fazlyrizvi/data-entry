"""
Error Prediction Module
Implements machine learning models to predict processing errors based on
document characteristics, confidence scores, and historical patterns.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Enumeration of error types for classification"""
    PROCESSING_TIMEOUT = "processing_timeout"
    INVALID_FORMAT = "invalid_format"
    CORRUPTED_DATA = "corrupted_data"
    EXTRACTION_FAILURE = "extraction_failure"
    VALIDATION_ERROR = "validation_error"
    SYSTEM_OVERLOAD = "system_overload"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_FAILURE = "authentication_failure"
    QUOTA_EXCEEDED = "quota_exceeded"
    UNKNOWN_ERROR = "unknown_error"

class SeverityLevel(Enum):
    """Error severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class DocumentCharacteristics:
    """Represents document characteristics for prediction"""
    file_size: float
    file_type: str
    page_count: int
    text_density: float
    image_count: int
    image_quality_score: float
    language: str
    processing_time: float
    confidence_score: float
    document_complexity: float
    time_of_day: int  # 0-23
    day_of_week: int  # 0-6
    historical_failure_rate: float

@dataclass
class PredictionResult:
    """Contains prediction results"""
    error_probability: float
    predicted_error_types: List[Tuple[ErrorType, float]]
    severity_prediction: SeverityLevel
    confidence: float
    risk_factors: List[str]
    recommendations: List[str]

class ErrorPredictor:
    """Main error prediction engine"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}
        self.prediction_history = []
        self.model_threshold = 0.7
        self.is_trained = False
        
        # Initialize models
        self._init_models()
        
        if model_path:
            self.load_model(model_path)
    
    def _init_models(self):
        """Initialize ML models"""
        self.models = {
            'error_classifier': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            ),
            'severity_classifier': GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                random_state=42
            ),
            'probability_estimator': LogisticRegression(
                random_state=42,
                max_iter=1000
            )
        }
        
        self.scalers = {
            'feature_scaler': StandardScaler(),
            'temporal_scaler': StandardScaler()
        }
        
        self.encoders = {
            'file_type_encoder': LabelEncoder(),
            'language_encoder': LabelEncoder(),
            'error_type_encoder': LabelEncoder(),
            'severity_encoder': LabelEncoder()
        }
    
    def extract_features(self, doc_chars: DocumentCharacteristics) -> np.ndarray:
        """Extract features from document characteristics"""
        features = np.array([
            doc_chars.file_size,
            doc_chars.page_count,
            doc_chars.text_density,
            doc_chars.image_count,
            doc_chars.image_quality_score,
            doc_chars.processing_time,
            doc_chars.confidence_score,
            doc_chars.document_complexity,
            doc_chars.time_of_day,
            doc_chars.day_of_week,
            doc_chars.historical_failure_rate
        ])
        
        # Add interaction features
        size_density_interaction = doc_chars.file_size * doc_chars.text_density
        confidence_time_interaction = doc_chars.confidence_score * doc_chars.processing_time
        complexity_density_interaction = doc_chars.document_complexity * doc_chars.text_density
        
        additional_features = np.array([
            size_density_interaction,
            confidence_time_interaction,
            complexity_density_interaction
        ])
        
        return np.concatenate([features, additional_features])
    
    def encode_categorical_features(self, doc_chars: DocumentCharacteristics) -> Tuple[np.ndarray, np.ndarray]:
        """Encode categorical features"""
        try:
            # Encode file type
            file_type_encoded = self.encoders['file_type_encoder'].transform([doc_chars.file_type])[0]
        except ValueError:
            # Unknown file type, use most common
            file_type_encoded = 0
        
        try:
            # Encode language
            language_encoded = self.encoders['language_encoder'].transform([doc_chars.language])[0]
        except ValueError:
            # Unknown language, use most common
            language_encoded = 0
        
        categorical_features = np.array([file_type_encoded, language_encoded])
        return categorical_features
    
    def predict_error_probability(self, doc_chars: DocumentCharacteristics) -> PredictionResult:
        """Predict error probability and type"""
        if not self.is_trained:
            logger.warning("Model not trained, using heuristic prediction")
            return self._heuristic_prediction(doc_chars)
        
        try:
            # Extract and encode features
            numerical_features = self.extract_features(doc_chars)
            categorical_features = self.encode_categorical_features(doc_chars)
            
            # Combine all features
            all_features = np.concatenate([numerical_features, categorical_features])
            all_features = all_features.reshape(1, -1)
            
            # Scale features
            scaled_features = self.scalers['feature_scaler'].transform(all_features)
            
            # Get predictions
            error_probs = self.models['error_classifier'].predict_proba(scaled_features)[0]
            severity_probs = self.models['severity_classifier'].predict_proba(scaled_features)[0]
            overall_probability = self.models['probability_estimator'].predict_proba(scaled_features)[0][1]
            
            # Get error type predictions
            error_types = list(ErrorType)
            error_type_predictions = []
            for i, prob in enumerate(error_probs):
                if i < len(error_types):
                    error_type_predictions.append((error_types[i], prob))
            
            # Sort by probability
            error_type_predictions.sort(key=lambda x: x[1], reverse=True)
            
            # Get severity prediction
            severity_levels = list(SeverityLevel)
            severity_prediction = severity_levels[np.argmax(severity_probs)]
            
            # Calculate confidence
            confidence = max(error_probs) - np.std(error_probs)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(doc_chars, error_type_predictions[:3])
            
            # Generate recommendations
            recommendations = self._generate_recommendations(doc_chars, error_type_predictions[:3])
            
            result = PredictionResult(
                error_probability=overall_probability,
                predicted_error_types=error_type_predictions,
                severity_prediction=severity_prediction,
                confidence=max(0, min(1, confidence)),
                risk_factors=risk_factors,
                recommendations=recommendations
            )
            
            # Store prediction history
            self.prediction_history.append({
                'timestamp': datetime.now(),
                'doc_chars': doc_chars,
                'result': result
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return self._fallback_prediction(doc_chars)
    
    def _heuristic_prediction(self, doc_chars: DocumentCharacteristics) -> PredictionResult:
        """Heuristic-based prediction when model is not trained"""
        risk_score = 0
        risk_factors = []
        recommendations = []
        
        # Size-based risk
        if doc_chars.file_size > 50 * 1024 * 1024:  # 50MB
            risk_score += 0.3
            risk_factors.append("Large file size")
            recommendations.append("Consider splitting large files")
        
        # Confidence-based risk
        if doc_chars.confidence_score < 0.7:
            risk_score += 0.4
            risk_factors.append("Low confidence score")
            recommendations.append("Review input quality")
        
        # Processing time risk
        if doc_chars.processing_time > 300:  # 5 minutes
            risk_score += 0.2
            risk_factors.append("Extended processing time")
            recommendations.append("Optimize processing pipeline")
        
        # Historical risk
        risk_score += doc_chars.historical_failure_rate * 0.5
        if doc_chars.historical_failure_rate > 0.1:
            risk_factors.append("High historical failure rate")
        
        # Determine severity
        if risk_score > 0.8:
            severity = SeverityLevel.CRITICAL
        elif risk_score > 0.6:
            severity = SeverityLevel.HIGH
        elif risk_score > 0.4:
            severity = SeverityLevel.MEDIUM
        else:
            severity = SeverityLevel.LOW
        
        # Most likely error types
        error_types = []
        if doc_chars.confidence_score < 0.7:
            error_types.append((ErrorType.EXTRACTION_FAILURE, 0.8))
        if doc_chars.file_size > 100 * 1024 * 1024:
            error_types.append((ErrorType.PROCESSING_TIMEOUT, 0.6))
        if doc_chars.processing_time > 300:
            error_types.append((ErrorType.SYSTEM_OVERLOAD, 0.5))
        
        if not error_types:
            error_types.append((ErrorType.UNKNOWN_ERROR, 0.3))
        
        return PredictionResult(
            error_probability=min(1.0, risk_score),
            predicted_error_types=error_types,
            severity_prediction=severity,
            confidence=0.6,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
    
    def _identify_risk_factors(self, doc_chars: DocumentCharacteristics, 
                             top_errors: List[Tuple[ErrorType, float]]) -> List[str]:
        """Identify specific risk factors"""
        risk_factors = []
        
        for error_type, prob in top_errors:
            if prob > 0.5:
                if error_type == ErrorType.PROCESSING_TIMEOUT:
                    if doc_chars.file_size > 50 * 1024 * 1024:
                        risk_factors.append("Large file size may cause timeout")
                    if doc_chars.processing_time > 200:
                        risk_factors.append("High processing time correlation")
                
                elif error_type == ErrorType.INVALID_FORMAT:
                    if doc_chars.file_type not in ['pdf', 'docx', 'txt']:
                        risk_factors.append("Unsupported file format")
                
                elif error_type == ErrorType.CORRUPTED_DATA:
                    if doc_chars.confidence_score < 0.6:
                        risk_factors.append("Low confidence indicates potential corruption")
                
                elif error_type == ErrorType.EXTRACTION_FAILURE:
                    if doc_chars.text_density < 0.1:
                        risk_factors.append("Low text density may hinder extraction")
                    if doc_chars.image_count > 10:
                        risk_factors.append("High image count may cause extraction issues")
                
                elif error_type == ErrorType.SYSTEM_OVERLOAD:
                    if doc_chars.time_of_day in [9, 10, 11, 14, 15, 16]:  # Peak hours
                        risk_factors.append("Processing during peak hours")
        
        return list(set(risk_factors))
    
    def _generate_recommendations(self, doc_chars: DocumentCharacteristics,
                                top_errors: List[Tuple[ErrorType, float]]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        for error_type, prob in top_errors:
            if prob > 0.5:
                if error_type == ErrorType.PROCESSING_TIMEOUT:
                    recommendations.append("Enable chunked processing")
                    recommendations.append("Increase timeout thresholds")
                
                elif error_type == ErrorType.INVALID_FORMAT:
                    recommendations.append("Add format validation before processing")
                    recommendations.append("Implement format conversion")
                
                elif error_type == ErrorType.CORRUPTED_DATA:
                    recommendations.append("Implement data integrity checks")
                    recommendations.append("Add input validation")
                
                elif error_type == ErrorType.EXTRACTION_FAILURE:
                    recommendations.append("Pre-process images for better quality")
                    recommendations.append("Use multiple extraction algorithms")
                
                elif error_type == ErrorType.SYSTEM_OVERLOAD:
                    recommendations.append("Schedule processing during off-peak hours")
                    recommendations.append("Implement load balancing")
        
        # General recommendations based on characteristics
        if doc_chars.file_size > 100 * 1024 * 1024:
            recommendations.append("Consider file compression")
        
        if doc_chars.confidence_score < 0.8:
            recommendations.append("Improve input quality controls")
        
        return list(set(recommendations))
    
    def _fallback_prediction(self, doc_chars: DocumentCharacteristics) -> PredictionResult:
        """Fallback prediction method"""
        logger.warning("Using fallback prediction method")
        return self._heuristic_prediction(doc_chars)
    
    def train_model(self, training_data: List[Tuple[DocumentCharacteristics, ErrorType, SeverityLevel]]) -> Dict[str, float]:
        """Train prediction models with historical data"""
        logger.info("Starting model training")
        
        if len(training_data) < 100:
            raise ValueError("Insufficient training data (minimum 100 samples required)")
        
        # Prepare training data
        X_numerical = []
        X_categorical = []
        y_error = []
        y_severity = []
        y_probability = []
        
        for doc_chars, error_type, severity in training_data:
            numerical_features = self.extract_features(doc_chars)
            categorical_features = self.encode_categorical_features(doc_chars)
            
            X_numerical.append(numerical_features)
            X_categorical.append(categorical_features)
            y_error.append(error_type.value)
            y_severity.append(severity.value)
            
            # Create probability label (1 if error, 0 if success)
            y_probability.append(1.0)  # This is training on error cases
        
        # Convert to arrays
        X_numerical = np.array(X_numerical)
        X_categorical = np.array(X_categorical)
        X_combined = np.hstack([X_numerical, X_categorical])
        
        # Encode target variables
        y_error_encoded = self.encoders['error_type_encoder'].fit_transform(y_error)
        y_severity_encoded = self.encoders['severity_encoder'].fit_transform(y_severity)
        
        # Scale features
        X_scaled = self.scalers['feature_scaler'].fit_transform(X_combined)
        
        # Train models
        self.models['error_classifier'].fit(X_scaled, y_error_encoded)
        self.models['severity_classifier'].fit(X_scaled, y_severity_encoded)
        self.models['probability_estimator'].fit(X_scaled, y_probability)
        
        # Calculate feature importance
        self.feature_importance = dict(
            zip(range(len(X_combined[0])), 
                self.models['error_classifier'].feature_importances_)
        )
        
        # Cross-validation scores
        cv_scores = {
            'error_classifier': cross_val_score(
                self.models['error_classifier'], X_scaled, y_error_encoded, cv=5
            ).mean(),
            'severity_classifier': cross_val_score(
                self.models['severity_classifier'], X_scaled, y_severity_encoded, cv=5
            ).mean(),
            'probability_estimator': cross_val_score(
                self.models['probability_estimator'], X_scaled, y_probability, cv=5
            ).mean()
        }
        
        self.is_trained = True
        logger.info(f"Training completed. CV scores: {cv_scores}")
        
        return cv_scores
    
    def save_model(self, filepath: str):
        """Save trained models to disk"""
        model_data = {
            'models': self.models,
            'scalers': self.scalers,
            'encoders': self.encoders,
            'feature_importance': self.feature_importance,
            'is_trained': self.is_trained,
            'model_threshold': self.model_threshold
        }
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained models from disk"""
        model_data = joblib.load(filepath)
        self.models = model_data['models']
        self.scalers = model_data['scalers']
        self.encoders = model_data['encoders']
        self.feature_importance = model_data['feature_importance']
        self.is_trained = model_data['is_trained']
        self.model_threshold = model_data.get('model_threshold', 0.7)
        logger.info(f"Model loaded from {filepath}")
    
    def get_prediction_statistics(self) -> Dict[str, Any]:
        """Get statistics about recent predictions"""
        if not self.prediction_history:
            return {"message": "No prediction history available"}
        
        recent_predictions = self.prediction_history[-100:]  # Last 100 predictions
        
        avg_error_prob = np.mean([p['result'].error_probability for p in recent_predictions])
        avg_confidence = np.mean([p['result'].confidence for p in recent_predictions])
        
        # Count error types
        error_type_counts = {}
        severity_counts = {}
        for pred in recent_predictions:
            for error_type, prob in pred['result'].predicted_error_types[:1]:  # Top prediction
                error_type_counts[error_type.value] = error_type_counts.get(error_type.value, 0) + 1
            
            severity = pred['result'].severity_prediction.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_predictions": len(recent_predictions),
            "average_error_probability": avg_error_prob,
            "average_confidence": avg_confidence,
            "error_type_distribution": error_type_counts,
            "severity_distribution": severity_counts,
            "high_risk_predictions": sum(1 for p in recent_predictions if p['result'].error_probability > 0.7)
        }
    
    def generate_training_data_synthetic(self, n_samples: int = 1000) -> List[Tuple[DocumentCharacteristics, ErrorType, SeverityLevel]]:
        """Generate synthetic training data for demonstration"""
        logger.info(f"Generating {n_samples} synthetic training samples")
        
        training_data = []
        
        for i in range(n_samples):
            # Generate realistic document characteristics
            file_size = np.random.exponential(10) * 1024 * 1024  # Exponential distribution
            page_count = max(1, int(np.random.poisson(10)))
            text_density = np.random.beta(2, 5)  # Skewed towards lower density
            image_count = np.random.poisson(5)
            image_quality_score = np.random.beta(3, 2)  # Skewed towards higher quality
            processing_time = np.random.exponential(60)  # Exponential distribution
            confidence_score = np.random.beta(3, 2)  # Skewed towards higher confidence
            document_complexity = np.random.beta(2, 2)  # Uniform-ish distribution
            time_of_day = np.random.randint(0, 24)
            day_of_week = np.random.randint(0, 7)
            historical_failure_rate = np.random.beta(1, 4)  # Skewed towards lower rates
            
            # Determine file type based on size and complexity
            if file_size > 50 * 1024 * 1024:
                file_type = np.random.choice(['pdf', 'docx'], p=[0.7, 0.3])
            else:
                file_type = np.random.choice(['pdf', 'docx', 'txt', 'image'], p=[0.4, 0.3, 0.2, 0.1])
            
            # Determine language
            language = np.random.choice(['en', 'es', 'fr', 'de', 'zh'], p=[0.6, 0.15, 0.1, 0.1, 0.05])
            
            doc_chars = DocumentCharacteristics(
                file_size=file_size,
                file_type=file_type,
                page_count=page_count,
                text_density=text_density,
                image_count=image_count,
                image_quality_score=image_quality_score,
                language=language,
                processing_time=processing_time,
                confidence_score=confidence_score,
                document_complexity=document_complexity,
                time_of_day=time_of_day,
                day_of_week=day_of_week,
                historical_failure_rate=historical_failure_rate
            )
            
            # Generate error based on realistic conditions
            error_type, severity = self._generate_realistic_error(doc_chars)
            
            training_data.append((doc_chars, error_type, severity))
        
        return training_data
    
    def _generate_realistic_error(self, doc_chars: DocumentCharacteristics) -> Tuple[ErrorType, SeverityLevel]:
        """Generate realistic error based on document characteristics"""
        error_weights = {error_type: 1.0 for error_type in ErrorType}
        
        # Adjust weights based on characteristics
        if doc_chars.file_size > 50 * 1024 * 1024:
            error_weights[ErrorType.PROCESSING_TIMEOUT] *= 3.0
            error_weights[ErrorType.SYSTEM_OVERLOAD] *= 2.0
        
        if doc_chars.confidence_score < 0.6:
            error_weights[ErrorType.CORRUPTED_DATA] *= 3.0
            error_weights[ErrorType.EXTRACTION_FAILURE] *= 2.0
        
        if doc_chars.processing_time > 300:
            error_weights[ErrorType.PROCESSING_TIMEOUT] *= 2.0
            error_weights[ErrorType.SYSTEM_OVERLOAD] *= 2.0
        
        if doc_chars.text_density < 0.1:
            error_weights[ErrorType.EXTRACTION_FAILURE] *= 2.0
        
        if doc_chars.image_count > 10:
            error_weights[ErrorType.EXTRACTION_FAILURE] *= 1.5
        
        if doc_chars.time_of_day in [9, 10, 11, 14, 15, 16]:
            error_weights[ErrorType.SYSTEM_OVERLOAD] *= 2.0
        
        # Select error type
        error_types = list(error_weights.keys())
        weights = list(error_weights.values())
        error_type = np.random.choice(error_types, p=np.array(weights)/sum(weights))
        
        # Determine severity
        if error_type in [ErrorType.SYSTEM_OVERLOAD, ErrorType.PROCESSING_TIMEOUT]:
            severity = SeverityLevel.HIGH
        elif error_type in [ErrorType.CORRUPTED_DATA, ErrorType.EXTRACTION_FAILURE]:
            severity = SeverityLevel.MEDIUM
        else:
            severity = SeverityLevel.LOW
        
        return error_type, severity