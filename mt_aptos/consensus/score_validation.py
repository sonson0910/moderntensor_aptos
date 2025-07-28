#!/usr/bin/env python3
"""
Score Validation and Aggregation Module

This module provides robust score validation and aggregation with:
- Outlier detection and filtering
- Weighted averaging based on validator reliability
- Sanity checks and score normalization
- Historical performance tracking
- Statistical analysis and anomaly detection

Key Features:
- Multi-level validation (range, format, consistency)
- Statistical outlier detection (IQR, Z-score methods)
- Weighted aggregation based on validator trust scores
- Historical context for score validation
- Anomaly detection and alerting
"""

import logging
import statistics
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import math

logger = logging.getLogger(__name__)

# Constants
MIN_SCORE = 0.0
MAX_SCORE = 1.0
DEFAULT_OUTLIER_THRESHOLD_IQR = 1.5  # IQR multiplier for outlier detection
DEFAULT_OUTLIER_THRESHOLD_ZSCORE = 2.0  # Z-score threshold for outliers
DEFAULT_MIN_VALIDATORS_FOR_CONSENSUS = 2
DEFAULT_VALIDATOR_TRUST_DECAY = 0.95  # Trust score decay factor
DEFAULT_SCORE_HISTORY_SIZE = 100
DEFAULT_ANOMALY_DETECTION_WINDOW = 10


class OutlierDetectionMethod(Enum):
    """Methods for outlier detection"""
    IQR = "iqr"  # Interquartile Range
    ZSCORE = "zscore"  # Z-score method
    MODIFIED_ZSCORE = "modified_zscore"  # Modified Z-score (more robust)
    BOTH = "both"  # Use both IQR and Z-score


class ValidationResult(Enum):
    """Score validation results"""
    VALID = "valid"
    INVALID_RANGE = "invalid_range"
    INVALID_FORMAT = "invalid_format"
    OUTLIER = "outlier"
    INSUFFICIENT_DATA = "insufficient_data"
    ANOMALY = "anomaly"


@dataclass
class ScoreEntry:
    """Individual score entry with metadata"""
    task_id: str
    miner_uid: str
    validator_uid: str
    score: float
    timestamp: float
    task_difficulty: Optional[float] = None
    response_time: Optional[float] = None
    quality_metrics: Optional[Dict[str, float]] = None


@dataclass
class ValidatorReliability:
    """Validator reliability metrics"""
    validator_uid: str
    trust_score: float = 1.0
    total_scores_submitted: int = 0
    valid_scores_submitted: int = 0
    outlier_scores_submitted: int = 0
    average_deviation: float = 0.0
    last_activity: Optional[float] = None
    score_history: deque = field(default_factory=lambda: deque(maxlen=DEFAULT_SCORE_HISTORY_SIZE))


@dataclass
class MinerPerformance:
    """Miner performance tracking"""
    miner_uid: str
    scores: deque = field(default_factory=lambda: deque(maxlen=DEFAULT_SCORE_HISTORY_SIZE))
    average_score: float = 0.0
    score_variance: float = 0.0
    total_tasks: int = 0
    recent_performance_trend: float = 0.0  # Positive = improving, negative = declining
    last_updated: Optional[float] = None


class ScoreValidator:
    """
    Comprehensive score validation and aggregation system.
    """
    
    def __init__(
        self,
        outlier_method: OutlierDetectionMethod = OutlierDetectionMethod.BOTH,
        outlier_threshold_iqr: float = DEFAULT_OUTLIER_THRESHOLD_IQR,
        outlier_threshold_zscore: float = DEFAULT_OUTLIER_THRESHOLD_ZSCORE,
        min_validators_for_consensus: int = DEFAULT_MIN_VALIDATORS_FOR_CONSENSUS,
        enable_anomaly_detection: bool = True
    ):
        """
        Initialize score validator.
        
        Args:
            outlier_method: Method for outlier detection
            outlier_threshold_iqr: IQR multiplier threshold
            outlier_threshold_zscore: Z-score threshold
            min_validators_for_consensus: Minimum validators needed for consensus
            enable_anomaly_detection: Whether to enable anomaly detection
        """
        self.outlier_method = outlier_method
        self.outlier_threshold_iqr = outlier_threshold_iqr
        self.outlier_threshold_zscore = outlier_threshold_zscore
        self.min_validators_for_consensus = min_validators_for_consensus
        self.enable_anomaly_detection = enable_anomaly_detection
        
        # Tracking dictionaries
        self.validator_reliability: Dict[str, ValidatorReliability] = {}
        self.miner_performance: Dict[str, MinerPerformance] = {}
        self.score_history: deque = deque(maxlen=1000)  # Global score history
        
        # Statistics
        self.total_scores_processed = 0
        self.valid_scores = 0
        self.invalid_scores = 0
        self.outlier_scores = 0
        self.anomaly_scores = 0
    
    def validate_score_format(self, score: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate score format and basic constraints.
        
        Args:
            score: Score value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if score is numeric
        if not isinstance(score, (int, float)):
            return False, f"Score must be numeric, got {type(score)}"
        
        # Check for NaN or infinity
        if math.isnan(score) or math.isinf(score):
            return False, f"Score cannot be NaN or infinity, got {score}"
        
        # Check range
        if not (MIN_SCORE <= score <= MAX_SCORE):
            return False, f"Score must be between {MIN_SCORE} and {MAX_SCORE}, got {score}"
        
        return True, None
    
    def detect_outliers_iqr(self, scores: List[float]) -> List[bool]:
        """
        Detect outliers using Interquartile Range (IQR) method.
        
        Args:
            scores: List of scores to analyze
            
        Returns:
            List of boolean flags indicating outliers
        """
        if len(scores) < 4:  # Need at least 4 points for meaningful IQR
            return [False] * len(scores)
        
        try:
            q1 = statistics.quantiles(scores, n=4)[0]  # 25th percentile
            q3 = statistics.quantiles(scores, n=4)[2]  # 75th percentile
            iqr = q3 - q1
            
            lower_bound = q1 - (self.outlier_threshold_iqr * iqr)
            upper_bound = q3 + (self.outlier_threshold_iqr * iqr)
            
            return [score < lower_bound or score > upper_bound for score in scores]
            
        except Exception as e:
            logger.warning(f"❌ IQR outlier detection failed: {e}")
            return [False] * len(scores)
    
    def detect_outliers_zscore(self, scores: List[float]) -> List[bool]:
        """
        Detect outliers using Z-score method.
        
        Args:
            scores: List of scores to analyze
            
        Returns:
            List of boolean flags indicating outliers
        """
        if len(scores) < 3:  # Need at least 3 points for meaningful Z-score
            return [False] * len(scores)
        
        try:
            mean_score = statistics.mean(scores)
            std_score = statistics.stdev(scores)
            
            if std_score == 0:  # All scores are identical
                return [False] * len(scores)
            
            z_scores = [abs(score - mean_score) / std_score for score in scores]
            return [z_score > self.outlier_threshold_zscore for z_score in z_scores]
            
        except Exception as e:
            logger.warning(f"❌ Z-score outlier detection failed: {e}")
            return [False] * len(scores)
    
    def detect_outliers_modified_zscore(self, scores: List[float]) -> List[bool]:
        """
        Detect outliers using Modified Z-score method (more robust).
        
        Args:
            scores: List of scores to analyze
            
        Returns:
            List of boolean flags indicating outliers
        """
        if len(scores) < 3:
            return [False] * len(scores)
        
        try:
            median_score = statistics.median(scores)
            mad = statistics.median([abs(score - median_score) for score in scores])
            
            if mad == 0:  # All scores are identical
                return [False] * len(scores)
            
            modified_z_scores = [0.6745 * (score - median_score) / mad for score in scores]
            return [abs(z_score) > self.outlier_threshold_zscore for z_score in modified_z_scores]
            
        except Exception as e:
            logger.warning(f"❌ Modified Z-score outlier detection failed: {e}")
            return [False] * len(scores)
    
    def detect_outliers(self, scores: List[float]) -> List[bool]:
        """
        Detect outliers using the configured method.
        
        Args:
            scores: List of scores to analyze
            
        Returns:
            List of boolean flags indicating outliers
        """
        if len(scores) < 2:
            return [False] * len(scores)
        
        if self.outlier_method == OutlierDetectionMethod.IQR:
            return self.detect_outliers_iqr(scores)
        elif self.outlier_method == OutlierDetectionMethod.ZSCORE:
            return self.detect_outliers_zscore(scores)
        elif self.outlier_method == OutlierDetectionMethod.MODIFIED_ZSCORE:
            return self.detect_outliers_modified_zscore(scores)
        elif self.outlier_method == OutlierDetectionMethod.BOTH:
            # Use both IQR and Z-score, mark as outlier if either method flags it
            iqr_outliers = self.detect_outliers_iqr(scores)
            zscore_outliers = self.detect_outliers_zscore(scores)
            return [iqr or zscore for iqr, zscore in zip(iqr_outliers, zscore_outliers)]
        
        return [False] * len(scores)
    
    def get_validator_reliability(self, validator_uid: str) -> ValidatorReliability:
        """Get or create validator reliability tracking"""
        if validator_uid not in self.validator_reliability:
            self.validator_reliability[validator_uid] = ValidatorReliability(validator_uid=validator_uid)
        return self.validator_reliability[validator_uid]
    
    def get_miner_performance(self, miner_uid: str) -> MinerPerformance:
        """Get or create miner performance tracking"""
        if miner_uid not in self.miner_performance:
            self.miner_performance[miner_uid] = MinerPerformance(miner_uid=miner_uid)
        return self.miner_performance[miner_uid]
    
    def update_validator_reliability(self, validator_uid: str, was_outlier: bool, deviation: float):
        """Update validator reliability metrics"""
        reliability = self.get_validator_reliability(validator_uid)
        
        reliability.total_scores_submitted += 1
        reliability.last_activity = time.time()
        
        if not was_outlier:
            reliability.valid_scores_submitted += 1
        else:
            reliability.outlier_scores_submitted += 1
        
        # Update average deviation (exponential moving average)
        alpha = 0.1  # Smoothing factor
        reliability.average_deviation = (alpha * deviation + (1 - alpha) * reliability.average_deviation)
        
        # Update trust score based on accuracy
        accuracy = reliability.valid_scores_submitted / reliability.total_scores_submitted if reliability.total_scores_submitted > 0 else 1.0
        outlier_rate = reliability.outlier_scores_submitted / reliability.total_scores_submitted if reliability.total_scores_submitted > 0 else 0.0
        
        # Trust score is based on accuracy and low outlier rate
        base_trust = accuracy * (1.0 - outlier_rate)
        reliability.trust_score = max(0.1, min(1.0, base_trust))  # Keep trust between 0.1 and 1.0
        
        logger.debug(f"🎯 Updated validator {validator_uid} trust: {reliability.trust_score:.3f} "
                    f"(accuracy: {accuracy:.3f}, outlier_rate: {outlier_rate:.3f})")
    
    def update_miner_performance(self, miner_uid: str, score: float):
        """Update miner performance tracking"""
        performance = self.get_miner_performance(miner_uid)
        
        performance.scores.append(score)
        performance.total_tasks += 1
        performance.last_updated = time.time()
        
        # Calculate statistics
        if len(performance.scores) > 0:
            performance.average_score = statistics.mean(performance.scores)
        
        if len(performance.scores) > 1:
            performance.score_variance = statistics.variance(performance.scores)
            
            # Calculate trend (simple linear regression slope)
            if len(performance.scores) >= 5:
                recent_scores = list(performance.scores)[-10:]  # Last 10 scores
                x_values = list(range(len(recent_scores)))
                n = len(recent_scores)
                
                if n > 1:
                    x_mean = statistics.mean(x_values)
                    y_mean = statistics.mean(recent_scores)
                    
                    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, recent_scores))
                    denominator = sum((x - x_mean) ** 2 for x in x_values)
                    
                    performance.recent_performance_trend = numerator / denominator if denominator != 0 else 0.0
    
    def validate_score_entry(self, score_entry: ScoreEntry) -> Tuple[ValidationResult, Optional[str]]:
        """
        Validate a single score entry.
        
        Args:
            score_entry: Score entry to validate
            
        Returns:
            Tuple of (validation_result, error_message)
        """
        # Basic format validation
        is_valid_format, format_error = self.validate_score_format(score_entry.score)
        if not is_valid_format:
            return ValidationResult.INVALID_FORMAT, format_error
        
        # Range validation (already done in format validation, but explicit check)
        if not (MIN_SCORE <= score_entry.score <= MAX_SCORE):
            return ValidationResult.INVALID_RANGE, f"Score {score_entry.score} outside valid range [{MIN_SCORE}, {MAX_SCORE}]"
        
        # Anomaly detection (if enabled and we have historical data)
        if self.enable_anomaly_detection:
            miner_performance = self.get_miner_performance(score_entry.miner_uid)
            if len(miner_performance.scores) >= DEFAULT_ANOMALY_DETECTION_WINDOW:
                # Check if score is significantly different from miner's historical performance
                historical_mean = statistics.mean(miner_performance.scores)
                historical_std = statistics.stdev(miner_performance.scores) if len(miner_performance.scores) > 1 else 0.1
                
                deviation = abs(score_entry.score - historical_mean)
                if historical_std > 0 and deviation > (3 * historical_std):  # 3-sigma rule
                    return ValidationResult.ANOMALY, f"Score {score_entry.score} is anomalous for miner {score_entry.miner_uid} (historical mean: {historical_mean:.3f})"
        
        return ValidationResult.VALID, None
    
    def aggregate_scores_for_miner(
        self,
        task_id: str,
        miner_uid: str,
        score_entries: List[ScoreEntry]
    ) -> Tuple[Optional[float], Dict[str, Any]]:
        """
        Aggregate multiple scores for a miner on a specific task.
        
        Args:
            task_id: Task identifier
            miner_uid: Miner identifier
            score_entries: List of score entries from different validators
            
        Returns:
            Tuple of (aggregated_score, metadata)
        """
        if not score_entries:
            return None, {"error": "No score entries provided"}
        
        # Filter score entries for this specific miner and task
        relevant_entries = [
            entry for entry in score_entries 
            if entry.miner_uid == miner_uid and entry.task_id == task_id
        ]
        
        if not relevant_entries:
            return None, {"error": f"No scores found for miner {miner_uid} and task {task_id}"}
        
        # Validate all scores
        valid_entries = []
        validation_results = {}
        
        for entry in relevant_entries:
            validation_result, error_msg = self.validate_score_entry(entry)
            validation_results[entry.validator_uid] = {
                "result": validation_result.value,
                "error": error_msg,
                "score": entry.score
            }
            
            if validation_result == ValidationResult.VALID:
                valid_entries.append(entry)
        
        if not valid_entries:
            return None, {
                "error": "No valid scores after validation",
                "validation_results": validation_results
            }
        
        # Check minimum validators requirement
        if len(valid_entries) < self.min_validators_for_consensus:
            return None, {
                "error": f"Insufficient validators: {len(valid_entries)} < {self.min_validators_for_consensus}",
                "validation_results": validation_results
            }
        
        # Extract scores and check for outliers
        scores = [entry.score for entry in valid_entries]
        outlier_flags = self.detect_outliers(scores)
        
        # Filter out outliers
        non_outlier_entries = [
            entry for entry, is_outlier in zip(valid_entries, outlier_flags)
            if not is_outlier
        ]
        
        # Update validator reliability
        for entry, is_outlier in zip(valid_entries, outlier_flags):
            if scores:
                median_score = statistics.median(scores)
                deviation = abs(entry.score - median_score)
                self.update_validator_reliability(entry.validator_uid, is_outlier, deviation)
        
        # If all scores are outliers, use the median of all valid scores
        if not non_outlier_entries:
            logger.warning(f"⚠️ All scores marked as outliers for miner {miner_uid}, task {task_id}. Using median.")
            final_score = statistics.median(scores)
            non_outlier_entries = valid_entries
        else:
            # Calculate weighted average based on validator trust scores
            weighted_scores = []
            weights = []
            
            for entry in non_outlier_entries:
                reliability = self.get_validator_reliability(entry.validator_uid)
                trust_score = reliability.trust_score
                
                weighted_scores.append(entry.score * trust_score)
                weights.append(trust_score)
            
            # Calculate weighted average
            if sum(weights) > 0:
                final_score = sum(weighted_scores) / sum(weights)
            else:
                final_score = statistics.mean([entry.score for entry in non_outlier_entries])
        
        # Update statistics
        self.total_scores_processed += len(relevant_entries)
        self.valid_scores += len(valid_entries)
        self.invalid_scores += len(relevant_entries) - len(valid_entries)
        self.outlier_scores += sum(outlier_flags)
        
        # Update miner performance
        self.update_miner_performance(miner_uid, final_score)
        
        # Store in history
        self.score_history.append({
            "task_id": task_id,
            "miner_uid": miner_uid,
            "final_score": final_score,
            "num_validators": len(relevant_entries),
            "num_valid": len(valid_entries),
            "num_outliers": sum(outlier_flags),
            "timestamp": time.time()
        })
        
        # Prepare metadata
        metadata = {
            "num_validators": len(relevant_entries),
            "num_valid_scores": len(valid_entries),
            "num_outliers": sum(outlier_flags),
            "score_range": [min(scores), max(scores)] if scores else None,
            "score_std": statistics.stdev(scores) if len(scores) > 1 else 0.0,
            "aggregation_method": "weighted_average",
            "validation_results": validation_results,
            "outlier_flags": dict(zip([entry.validator_uid for entry in valid_entries], outlier_flags))
        }
        
        logger.debug(f"🎯 Aggregated score for {miner_uid}: {final_score:.4f} "
                    f"(from {len(valid_entries)} validators, {sum(outlier_flags)} outliers)")
        
        return final_score, metadata
    
    def get_validator_trust_scores(self) -> Dict[str, float]:
        """Get current trust scores for all validators"""
        return {
            validator_uid: reliability.trust_score 
            for validator_uid, reliability in self.validator_reliability.items()
        }
    
    def get_miner_performance_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get performance summary for all miners"""
        summary = {}
        
        for miner_uid, performance in self.miner_performance.items():
            summary[miner_uid] = {
                "average_score": performance.average_score,
                "score_variance": performance.score_variance,
                "total_tasks": performance.total_tasks,
                "recent_trend": performance.recent_performance_trend,
                "score_count": len(performance.scores)
            }
        
        return summary
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get overall validation statistics"""
        total_processed = self.total_scores_processed
        
        return {
            "total_scores_processed": total_processed,
            "valid_scores": self.valid_scores,
            "invalid_scores": self.invalid_scores,
            "outlier_scores": self.outlier_scores,
            "anomaly_scores": self.anomaly_scores,
            "valid_score_rate": self.valid_scores / total_processed if total_processed > 0 else 0.0,
            "outlier_rate": self.outlier_scores / total_processed if total_processed > 0 else 0.0,
            "total_validators_tracked": len(self.validator_reliability),
            "total_miners_tracked": len(self.miner_performance)
        }


# === Convenience Functions ===

def create_score_entry(
    task_id: str,
    miner_uid: str,
    validator_uid: str,
    score: float,
    timestamp: Optional[float] = None,
    **kwargs
) -> ScoreEntry:
    """Create a score entry with optional metadata"""
    return ScoreEntry(
        task_id=task_id,
        miner_uid=miner_uid,
        validator_uid=validator_uid,
        score=score,
        timestamp=timestamp or time.time(),
        **kwargs
    )


def create_score_validator(
    outlier_detection: str = "both",
    strict_validation: bool = True
) -> ScoreValidator:
    """Create a score validator with common configurations"""
    outlier_method = OutlierDetectionMethod(outlier_detection.lower())
    
    if strict_validation:
        return ScoreValidator(
            outlier_method=outlier_method,
            outlier_threshold_iqr=1.2,  # Stricter IQR threshold
            outlier_threshold_zscore=1.8,  # Stricter Z-score threshold
            min_validators_for_consensus=3,  # Require more validators
            enable_anomaly_detection=True
        )
    else:
        return ScoreValidator(
            outlier_method=outlier_method,
            enable_anomaly_detection=False
        ) 