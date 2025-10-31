"""
AI-Powered Anomaly Detection Module
Uses statistical methods and basic ML approaches to detect data anomalies.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from collections import defaultdict
import logging
from enum import Enum
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Optional ML imports
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    IsolationForest = None
    DBSCAN = None
    StandardScaler = None
    PCA = None


class AnomalyType(Enum):
    """Types of anomalies."""
    STATISTICAL = "statistical"
    PATTERN = "pattern"
    OUTLIER = "outlier"
    TEMPORAL = "temporal"
    CORRELATION = "correlation"


class AnomalyScore:
    """Represents anomaly score with metadata."""
    
    def __init__(self, score: float, method: str, confidence: float = 1.0):
        self.score = score  # 0-1, higher means more anomalous
        self.method = method
        self.confidence = confidence
        self.timestamp = pd.Timestamp.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'score': self.score,
            'method': self.method,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat()
        }


class StatisticalAnomalyDetector:
    """Detects anomalies using statistical methods."""
    
    def __init__(self, z_threshold: float = 3.0, iqr_multiplier: float = 1.5):
        self.z_threshold = z_threshold
        self.iqr_multiplier = iqr_multiplier
        
    def detect_zscore_outliers(self, values: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Detect outliers using Z-score method."""
        z_scores = np.abs(stats.zscore(values, nan_policy='omit'))
        outliers = z_scores > self.z_threshold
        return outliers, z_scores
        
    def detect_iqr_outliers(self, values: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Detect outliers using Interquartile Range method."""
        q1 = np.percentile(values, 25, method='linear')
        q3 = np.percentile(values, 75, method='linear')
        iqr = q3 - q1
        
        lower_bound = q1 - self.iqr_multiplier * iqr
        upper_bound = q3 + self.iqr_multiplier * iqr
        
        outliers = (values < lower_bound) | (values > upper_bound)
        
        # Calculate anomaly scores (distance from bounds)
        scores = np.zeros_like(values, dtype=float)
        scores[values < lower_bound] = (lower_bound - values[values < lower_bound]) / iqr
        scores[values > upper_bound] = (values[values > upper_bound] - upper_bound) / iqr
        
        return outliers, scores
        
    def detect_mad_outliers(self, values: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Detect outliers using Median Absolute Deviation method."""
        median = np.median(values)
        mad = np.median(np.abs(values - median))
        
        # Modified Z-score using MAD
        modified_z_scores = 0.6745 * (values - median) / mad
        outliers = np.abs(modified_z_scores) > self.z_threshold
        
        return outliers, np.abs(modified_z_scores)


class IsolationForestDetector:
    """Detects anomalies using Isolation Forest algorithm."""
    
    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for Isolation Forest detection")
            
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100
        )
        
    def fit_detect(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Fit model and detect anomalies."""
        # Fit the model
        self.model.fit(data)
        
        # Get anomaly scores (-1 for outliers, 1 for inliers)
        anomaly_labels = self.model.predict(data)
        
        # Convert to anomaly scores (0-1, higher means more anomalous)
        anomaly_scores = self.model.decision_function(data)
        anomaly_scores = 1 - (anomaly_scores - anomaly_scores.min()) / (anomaly_scores.max() - anomaly_scores.min())
        
        # Convert labels to boolean (True for outliers)
        outliers = anomaly_labels == -1
        
        return outliers, anomaly_scores


class ClusteringAnomalyDetector:
    """Detects anomalies using clustering methods."""
    
    def __init__(self, eps: float = 0.5, min_samples: int = 5):
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for clustering-based detection")
            
        self.eps = eps
        self.min_samples = min_samples
        self.model = DBSCAN(eps=eps, min_samples=min_samples)
        
    def fit_detect(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Fit clustering model and detect anomalies."""
        # Fit the model
        cluster_labels = self.model.fit_predict(data)
        
        # Points with label -1 are considered noise/anomalies
        outliers = cluster_labels == -1
        
        # Calculate anomaly scores based on distance to nearest cluster center
        scores = np.zeros(len(data))
        
        if len(set(cluster_labels)) > 1:  # If we have multiple clusters
            # Calculate distances to cluster centers
            unique_labels = set(cluster_labels)
            cluster_centers = {}
            
            for label in unique_labels:
                if label != -1:  # Exclude noise points
                    cluster_points = data[cluster_labels == label]
                    cluster_centers[label] = np.mean(cluster_points, axis=0)
            
            # Calculate minimum distance to any cluster center
            for i, point in enumerate(data):
                distances = []
                for center in cluster_centers.values():
                    distances.append(np.linalg.norm(point - center))
                scores[i] = min(distances) if distances else 1.0
                
        return outliers, scores


class PatternAnomalyDetector:
    """Detects anomalies in patterns and sequences."""
    
    def __init__(self):
        self.pattern_cache = {}
        
    def detect_sequence_anomalies(self, sequence: List[Any]) -> Tuple[List[int], List[float]]:
        """Detect anomalies in sequential data."""
        if len(sequence) < 3:
            return [], []
            
        # Calculate differences between consecutive elements
        try:
            numeric_sequence = [float(x) for x in sequence if x is not None]
            if len(numeric_sequence) != len(sequence):
                return [], []
                
            differences = np.diff(numeric_sequence)
            
            # Detect large jumps in differences
            mean_diff = np.mean(differences)
            std_diff = np.std(differences)
            
            anomaly_scores = []
            anomaly_indices = []
            
            for i, diff in enumerate(differences):
                z_score = abs(diff - mean_diff) / std_diff if std_diff > 0 else 0
                score = min(1.0, z_score / 3.0)  # Normalize to 0-1
                
                if z_score > 2.0:  # Threshold for anomaly
                    anomaly_indices.append(i + 1)  # +1 because diff is between points
                    anomaly_scores.append(score)
                    
            return anomaly_indices, anomaly_scores
            
        except (ValueError, TypeError):
            return [], []
            
    def detect_categorical_anomalies(self, values: List[Any]) -> Tuple[List[int], List[float]]:
        """Detect anomalies in categorical data."""
        if len(values) < 3:
            return [], []
            
        # Count frequency of each value
        value_counts = defaultdict(int)
        for value in values:
            if value is not None:
                value_counts[value] += 1
                
        # Values that appear only once might be anomalies
        anomaly_indices = []
        anomaly_scores = []
        
        for i, value in enumerate(values):
            if value is not None and value_counts[value] == 1:
                anomaly_indices.append(i)
                anomaly_scores.append(1.0)  # Single occurrence is highly anomalous
                
        return anomaly_indices, anomaly_scores


class CorrelationAnomalyDetector:
    """Detects anomalies in correlations between variables."""
    
    def __init__(self, correlation_threshold: float = 0.8):
        self.correlation_threshold = correlation_threshold
        
    def detect_correlation_anomalies(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect correlation-based anomalies."""
        anomalies = []
        
        # Calculate correlation matrix
        corr_matrix = data.corr()
        
        # Find high correlations
        high_corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > self.correlation_threshold:
                    high_corr_pairs.append((
                        corr_matrix.columns[i],
                        corr_matrix.columns[j],
                        corr_value
                    ))
                    
        # Check for rows that break the correlation pattern
        for var1, var2, corr_value in high_corr_pairs:
            # Simple check: if correlation is high, deviations might indicate anomalies
            mask = ~(data[var1].isnull() | data[var2].isnull())
            
            if mask.sum() > 10:  # Enough data points
                subset = data[mask]
                
                # Calculate residuals from expected relationship
                x = subset[var1].values
                y = subset[var2].values
                
                # Linear regression
                slope, intercept = np.polyfit(x, y, 1)
                predicted = slope * x + intercept
                residuals = y - predicted
                
                # Find outliers in residuals
                z_scores = np.abs(stats.zscore(residuals))
                outlier_indices = np.where(z_scores > 2.5)[0]
                
                for idx in outlier_indices:
                    anomalies.append({
                        'type': 'correlation_anomaly',
                        'variables': [var1, var2],
                        'correlation': corr_value,
                        'residual': residuals[idx],
                        'z_score': z_scores[idx],
                        'severity': min(1.0, z_scores[idx] / 3.0)
                    })
                    
        return anomalies


class TemporalAnomalyDetector:
    """Detects temporal anomalies in time series data."""
    
    def __init__(self, window_size: int = 7):
        self.window_size = window_size
        
    def detect_temporal_anomalies(self, timeseries_data: pd.DataFrame, 
                                timestamp_column: str) -> List[Dict[str, Any]]:
        """Detect anomalies in time series data."""
        anomalies = []
        
        if timestamp_column not in timeseries_data.columns:
            return anomalies
            
        # Ensure timestamp column is datetime
        timeseries_data[timestamp_column] = pd.to_datetime(timeseries_data[timestamp_column])
        
        # Sort by timestamp
        timeseries_data = timeseries_data.sort_values(timestamp_column)
        
        # Check for missing time periods
        time_diff = timeseries_data[timestamp_column].diff()
        median_diff = time_diff.median()
        
        # Find unusually large gaps
        large_gaps = time_diff > median_diff * 3
        
        for idx in timeseries_data.index[large_gaps]:
            anomalies.append({
                'type': 'temporal_gap',
                'timestamp': timeseries_data.loc[idx, timestamp_column],
                'gap_duration': time_diff.loc[idx],
                'severity': min(1.0, time_diff.loc[idx] / (median_diff * 5))
            })
            
        # Check for values outside expected temporal patterns
        for column in timeseries_data.columns:
            if column != timestamp_column and pd.api.types.is_numeric_dtype(timeseries_data[column]):
                values = timeseries_data[column].dropna()
                
                if len(values) > self.window_size:
                    # Rolling statistics
                    rolling_mean = timeseries_data[column].rolling(window=self.window_size).mean()
                    rolling_std = timeseries_data[column].rolling(window=self.window_size).std()
                    
                    # Detect points far from rolling mean
                    z_scores = np.abs((timeseries_data[column] - rolling_mean) / rolling_std)
                    outlier_mask = z_scores > 2.5
                    
                    for idx in timeseries_data.index[outlier_mask]:
                        anomalies.append({
                            'type': 'temporal_outlier',
                            'variable': column,
                            'timestamp': timeseries_data.loc[idx, timestamp_column],
                            'value': timeseries_data.loc[idx, column],
                            'z_score': z_scores.loc[idx],
                            'severity': min(1.0, z_scores.loc[idx] / 3.0)
                        })
                        
        return anomalies


class AnomalyDetector:
    """Main anomaly detection orchestrator."""
    
    def __init__(self):
        self.statistical_detector = StatisticalAnomalyDetector()
        self.isolation_forest = IsolationForestDetector() if SKLEARN_AVAILABLE else None
        self.clustering_detector = ClusteringAnomalyDetector() if SKLEARN_AVAILABLE else None
        self.pattern_detector = PatternAnomalyDetector()
        self.correlation_detector = CorrelationAnomalyDetector()
        self.temporal_detector = TemporalAnomalyDetector()
        self.logger = logging.getLogger(__name__)
        
        if not SKLEARN_AVAILABLE:
            self.logger.warning("scikit-learn not available. ML-based anomaly detection disabled.")
        
    def detect_numerical_outliers(self, data: Union[pd.Series, np.ndarray, List]) -> Dict[str, Any]:
        """Detect outliers in numerical data."""
        values = pd.Series(data).dropna().values
        
        if len(values) < 3:
            return {'error': 'Insufficient data for outlier detection'}
            
        results = {}
        
        # Z-score method
        z_outliers, z_scores = self.statistical_detector.detect_zscore_outliers(values)
        results['zscore'] = {
            'outliers': z_outliers.tolist(),
            'scores': z_scores.tolist(),
            'count': int(np.sum(z_outliers))
        }
        
        # IQR method
        iqr_outliers, iqr_scores = self.statistical_detector.detect_iqr_outliers(values)
        results['iqr'] = {
            'outliers': iqr_outliers.tolist(),
            'scores': iqr_scores.tolist(),
            'count': int(np.sum(iqr_outliers))
        }
        
        # Isolation Forest
        try:
            if SKLEARN_AVAILABLE and self.isolation_forest is not None:
                if values.ndim == 1:
                    values_reshaped = values.reshape(-1, 1)
                else:
                    values_reshaped = values
                    
                if_outliers, if_scores = self.isolation_forest.fit_detect(values_reshaped)
                results['isolation_forest'] = {
                    'outliers': if_outliers.tolist(),
                    'scores': if_scores.tolist(),
                    'count': int(np.sum(if_outliers))
                }
            else:
                results['isolation_forest'] = {'error': 'scikit-learn not available'}
        except Exception as e:
            results['isolation_forest'] = {'error': str(e)}
            
        return results
        
    def detect_categorical_anomalies(self, data: Union[pd.Series, List]) -> Dict[str, Any]:
        """Detect anomalies in categorical data."""
        values = pd.Series(data).tolist()
        
        anomaly_indices, anomaly_scores = self.pattern_detector.detect_categorical_anomalies(values)
        
        return {
            'anomaly_indices': anomaly_indices,
            'anomaly_scores': anomaly_scores,
            'count': len(anomaly_indices)
        }
        
    def detect_pattern_anomalies(self, data: Union[pd.Series, List]) -> Dict[str, Any]:
        """Detect pattern anomalies in sequential data."""
        values = pd.Series(data).tolist()
        
        anomaly_indices, anomaly_scores = self.pattern_detector.detect_sequence_anomalies(values)
        
        return {
            'anomaly_indices': anomaly_indices,
            'anomaly_scores': anomaly_scores,
            'count': len(anomaly_indices)
        }
        
    def detect_correlation_anomalies(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect correlation-based anomalies."""
        return self.correlation_detector.detect_correlation_anomalies(data)
        
    def detect_temporal_anomalies(self, data: pd.DataFrame, timestamp_column: str) -> List[Dict[str, Any]]:
        """Detect temporal anomalies."""
        return self.temporal_detector.detect_temporal_anomalies(data, timestamp_column)
        
    def detect_dataset_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect all types of anomalies in dataset."""
        results = {
            'numerical_anomalies': {},
            'categorical_anomalies': {},
            'correlation_anomalies': [],
            'temporal_anomalies': [],
            'overall_anomaly_score': 0.0
        }
        
        # Detect numerical anomalies
        for column in data.columns:
            if pd.api.types.is_numeric_dtype(data[column]):
                results['numerical_anomalies'][column] = self.detect_numerical_outliers(data[column])
                
        # Detect categorical anomalies
        for column in data.columns:
            if not pd.api.types.is_numeric_dtype(data[column]):
                results['categorical_anomalies'][column] = self.detect_categorical_anomalies(data[column])
                
        # Detect correlation anomalies
        numeric_data = data.select_dtypes(include=[np.number])
        if len(numeric_data.columns) > 1:
            results['correlation_anomalies'] = self.detect_correlation_anomalies(numeric_data)
            
        # Calculate overall anomaly score
        total_anomalies = 0
        total_checks = 0
        
        # Numerical anomalies
        for column, result in results['numerical_anomalies'].items():
            if 'error' not in result:
                total_anomalies += result.get('count', 0)
                total_checks += len(data[column].dropna())
                
        # Categorical anomalies
        for column, result in results['categorical_anomalies'].items():
            total_anomalies += result.get('count', 0)
            total_checks += len(data[column].dropna())
            
        # Correlation and temporal anomalies
        total_anomalies += len(results['correlation_anomalies'])
        total_anomalies += len(results['temporal_anomalies'])
        total_checks += len(data) * len(data.columns)
        
        # Calculate overall score (0-1, higher means more anomalous)
        if total_checks > 0:
            results['overall_anomaly_score'] = min(1.0, total_anomalies / (total_checks * 0.1))
            
        return results
        
    def get_anomaly_explanation(self, data: pd.DataFrame, anomalies: Dict[str, Any]) -> List[str]:
        """Generate human-readable explanations for anomalies."""
        explanations = []
        
        # Numerical anomalies
        for column, result in anomalies.get('numerical_anomalies', {}).items():
            if 'error' not in result:
                count = result.get('count', 0)
                if count > 0:
                    explanations.append(
                        f"Column '{column}': Found {count} numerical outliers using multiple methods"
                    )
                    
        # Categorical anomalies
        for column, result in anomalies.get('categorical_anomalies', {}).items():
            count = result.get('count', 0)
            if count > 0:
                explanations.append(
                    f"Column '{column}': Found {count} values that appear only once"
                )
                
        # Correlation anomalies
        for corr_anomaly in anomalies.get('correlation_anomalies', []):
            if corr_anomaly.get('type') == 'correlation_anomaly':
                variables = corr_anomaly.get('variables', [])
                explanations.append(
                    f"Relationship between {variables[0]} and {variables[1]} shows unexpected patterns"
                )
                
        return explanations