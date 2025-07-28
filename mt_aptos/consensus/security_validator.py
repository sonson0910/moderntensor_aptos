#!/usr/bin/env python3
"""
Security Validation Module

This module provides comprehensive security validation with:
- Input validation and sanitization
- Anti-spam and rate limiting measures
- Validator authentication and authorization
- Consensus integrity verification
- Attack detection and prevention
- Security audit logging

Key Features:
- Multi-layer input validation
- Cryptographic signature verification
- Rate limiting with adaptive thresholds
- Anomaly detection for attacks
- Security event logging and alerting
- Validator reputation-based access control
"""

import asyncio
import logging
import time
import hashlib
import hmac
from typing import Tuple, Optional, Any, Callable, Union, Dict, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import json
import re
import ipaddress
from pathlib import Path
from typing import Set

logger = logging.getLogger(__name__)

# Constants
DEFAULT_RATE_LIMIT_PER_MINUTE = 60
DEFAULT_RATE_LIMIT_BURST = 10
DEFAULT_REPUTATION_THRESHOLD = 0.5
DEFAULT_INPUT_SIZE_LIMIT = 1024 * 1024  # 1MB
DEFAULT_SECURITY_LOG_RETENTION = 7 * 24 * 3600  # 7 days
MAX_VALIDATION_ERRORS = 100


class SecurityThreat(Enum):
    """Types of security threats"""
    SPAM = "spam"
    DOS = "dos"
    INJECTION = "injection"
    FORGERY = "forgery"
    REPLAY = "replay"
    IMPERSONATION = "impersonation"
    DATA_CORRUPTION = "data_corruption"


class ValidationResult(Enum):
    """Input validation results"""
    VALID = "valid"
    INVALID = "invalid"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"


@dataclass
class SecurityEvent:
    """Security event record"""
    timestamp: float
    threat_type: SecurityThreat
    source_id: str
    description: str
    severity: str = "medium"
    blocked: bool = False
    data: Optional[Dict[str, Any]] = None


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = DEFAULT_RATE_LIMIT_PER_MINUTE
    burst_limit: int = DEFAULT_RATE_LIMIT_BURST
    window_size: int = 60  # seconds
    adaptive: bool = True


@dataclass
class ValidatorCredentials:
    """Validator authentication credentials"""
    validator_uid: str
    public_key: str
    reputation_score: float = 1.0
    last_authenticated: Optional[float] = None
    authentication_failures: int = 0
    is_trusted: bool = False


class InputValidator:
    """Validates and sanitizes input data"""
    
    def __init__(self, max_size: int = DEFAULT_INPUT_SIZE_LIMIT):
        self.max_size = max_size
        self.validation_errors: deque = deque(maxlen=MAX_VALIDATION_ERRORS)
        
        # Dangerous patterns to detect
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script injection
            r'javascript:',  # JavaScript URLs
            r'on\w+\s*=',  # Event handlers
            r'eval\s*\(',  # eval() calls
            r'exec\s*\(',  # exec() calls
            r'\$\([^)]*\)',  # jQuery selectors
            r'document\.',  # DOM access
            r'window\.',  # Window access
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.dangerous_patterns]
    
    def validate_input(self, data: Any, context: str = "unknown") -> Tuple[ValidationResult, Optional[str]]:
        """
        Validate input data for security threats.
        
        Args:
            data: Input data to validate
            context: Context of the validation
            
        Returns:
            Tuple of (validation_result, error_message)
        """
        try:
            # Size validation
            serialized_data = json.dumps(data, default=str)
            if len(serialized_data) > self.max_size:
                error_msg = f"Input size {len(serialized_data)} exceeds limit {self.max_size}"
                self._record_validation_error(context, "size_limit", error_msg)
                return ValidationResult.INVALID, error_msg
            
            # Type validation
            if not self._validate_data_types(data):
                error_msg = "Invalid data types detected"
                self._record_validation_error(context, "type_validation", error_msg)
                return ValidationResult.INVALID, error_msg
            
            # Content validation
            if self._contains_malicious_content(serialized_data):
                error_msg = "Malicious content detected"
                self._record_validation_error(context, "malicious_content", error_msg)
                return ValidationResult.MALICIOUS, error_msg
            
            # Structure validation
            if not self._validate_structure(data, context):
                error_msg = "Invalid data structure"
                self._record_validation_error(context, "structure_validation", error_msg)
                return ValidationResult.INVALID, error_msg
            
            return ValidationResult.VALID, None
            
        except Exception as e:
            error_msg = f"Validation error: {e}"
            self._record_validation_error(context, "validation_exception", error_msg)
            return ValidationResult.INVALID, error_msg
    
    def _validate_data_types(self, data: Any) -> bool:
        """Validate data types are safe"""
        if isinstance(data, dict):
            return all(
                isinstance(key, str) and self._validate_data_types(value)
                for key, value in data.items()
            )
        elif isinstance(data, list):
            return all(self._validate_data_types(item) for item in data)
        elif isinstance(data, (str, int, float, bool, type(None))):
            return True
        else:
            return False
    
    def _contains_malicious_content(self, content: str) -> bool:
        """Check for malicious content patterns"""
        for pattern in self.compiled_patterns:
            if pattern.search(content):
                return True
        return False
    
    def _validate_structure(self, data: Any, context: str) -> bool:
        """Validate data structure based on context"""
        if context == "task_data":
            return self._validate_task_data_structure(data)
        elif context == "consensus_proposal":
            return self._validate_consensus_proposal_structure(data)
        elif context == "miner_result":
            return self._validate_miner_result_structure(data)
        else:
            return True  # Unknown context, allow
    
    def _validate_task_data_structure(self, data: Any) -> bool:
        """Validate task data structure"""
        if not isinstance(data, dict):
            return False
        
        required_fields = ["task_id", "timestamp"]
        return all(field in data for field in required_fields)
    
    def _validate_consensus_proposal_structure(self, data: Any) -> bool:
        """Validate consensus proposal structure"""
        if not isinstance(data, dict):
            return False
        
        required_fields = ["slot", "phase", "proposer_uid", "proposal_data"]
        return all(field in data for field in required_fields)
    
    def _validate_miner_result_structure(self, data: Any) -> bool:
        """Validate miner result structure"""
        if not isinstance(data, dict):
            return False
        
        required_fields = ["miner_uid", "result"]
        return all(field in data for field in required_fields)
    
    def _record_validation_error(self, context: str, error_type: str, message: str):
        """Record validation error"""
        self.validation_errors.append({
            "timestamp": time.time(),
            "context": context,
            "error_type": error_type,
            "message": message
        })
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        recent_errors = list(self.validation_errors)[-20:]  # Last 20 errors
        
        error_types = defaultdict(int)
        for error in recent_errors:
            error_types[error["error_type"]] += 1
        
        return {
            "total_validation_errors": len(self.validation_errors),
            "recent_errors": recent_errors,
            "error_types": dict(error_types),
            "max_input_size": self.max_size
        }


class RateLimiter:
    """Advanced rate limiter with adaptive thresholds"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.request_windows: Dict[str, deque] = defaultdict(lambda: deque())
        self.burst_counters: Dict[str, int] = defaultdict(int)
        self.adaptive_limits: Dict[str, int] = defaultdict(lambda: config.requests_per_minute)
        
        # Tracking for adaptive adjustment
        self.client_behaviors: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "legitimate_requests": 0,
            "rejected_requests": 0,
            "avg_request_interval": 0.0,
            "last_request_time": 0.0
        })
    
    async def check_rate_limit(self, client_id: str, request_weight: float = 1.0) -> Tuple[bool, Optional[str]]:
        """
        Check if request is within rate limits.
        
        Args:
            client_id: Identifier for the client
            request_weight: Weight of the request (default 1.0)
            
        Returns:
            Tuple of (allowed, reason_if_denied)
        """
        current_time = time.time()
        window_start = current_time - self.config.window_size
        
        # Clean old requests from window
        client_window = self.request_windows[client_id]
        while client_window and client_window[0] < window_start:
            client_window.popleft()
        
        # Check window limit
        current_requests = len(client_window)
        adaptive_limit = self.adaptive_limits[client_id]
        
        if current_requests >= adaptive_limit:
            self._record_rejection(client_id, "window_limit")
            return False, f"Rate limit exceeded: {current_requests}/{adaptive_limit} requests in window"
        
        # Check burst limit
        if self.burst_counters[client_id] >= self.config.burst_limit:
            # Reset burst counter if enough time has passed
            last_request_time = client_window[-1] if client_window else 0
            if current_time - last_request_time > 10:  # 10 second burst reset
                self.burst_counters[client_id] = 0
            else:
                self._record_rejection(client_id, "burst_limit")
                return False, f"Burst limit exceeded: {self.burst_counters[client_id]}/{self.config.burst_limit}"
        
        # Allow request
        client_window.append(current_time)
        self.burst_counters[client_id] += int(request_weight)
        self._record_legitimate_request(client_id, current_time)
        
        # Adaptive adjustment
        if self.config.adaptive:
            await self._adjust_adaptive_limits(client_id)
        
        return True, None
    
    def _record_rejection(self, client_id: str, reason: str):
        """Record rejected request"""
        behavior = self.client_behaviors[client_id]
        behavior["rejected_requests"] += 1
        
        logger.debug(f"🚫 Rate limit rejection for {client_id}: {reason}")
    
    def _record_legitimate_request(self, client_id: str, current_time: float):
        """Record legitimate request"""
        behavior = self.client_behaviors[client_id]
        behavior["legitimate_requests"] += 1
        
        # Update average request interval
        if behavior["last_request_time"] > 0:
            interval = current_time - behavior["last_request_time"]
            behavior["avg_request_interval"] = (
                behavior["avg_request_interval"] * 0.9 + interval * 0.1
            )
        
        behavior["last_request_time"] = current_time
    
    async def _adjust_adaptive_limits(self, client_id: str):
        """Adjust rate limits based on client behavior"""
        behavior = self.client_behaviors[client_id]
        
        total_requests = behavior["legitimate_requests"] + behavior["rejected_requests"]
        if total_requests < 10:  # Need more data
            return
        
        rejection_rate = behavior["rejected_requests"] / total_requests
        
        # Increase limit for well-behaved clients
        if rejection_rate < 0.1 and behavior["avg_request_interval"] > 2.0:
            self.adaptive_limits[client_id] = min(
                self.config.requests_per_minute * 2,
                int(self.adaptive_limits[client_id] * 1.1)
            )
        
        # Decrease limit for problematic clients
        elif rejection_rate > 0.3:
            self.adaptive_limits[client_id] = max(
                self.config.requests_per_minute // 4,
                int(self.adaptive_limits[client_id] * 0.8)
            )
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        total_requests = 0
        total_rejections = 0
        
        for behavior in self.client_behaviors.values():
            total_requests += behavior["legitimate_requests"] + behavior["rejected_requests"]
            total_rejections += behavior["rejected_requests"]
        
        return {
            "total_requests": total_requests,
            "total_rejections": total_rejections,
            "rejection_rate": total_rejections / total_requests if total_requests > 0 else 0.0,
            "active_clients": len(self.client_behaviors),
            "config": {
                "requests_per_minute": self.config.requests_per_minute,
                "burst_limit": self.config.burst_limit,
                "adaptive": self.config.adaptive
            }
        }


class ValidatorAuthenticator:
    """Handles validator authentication and authorization"""
    
    def __init__(self):
        self.credentials: Dict[str, ValidatorCredentials] = {}
        self.authentication_log: deque = deque(maxlen=1000)
        self.trusted_validators: Set[str] = set()
        
        # Security settings
        self.max_auth_failures = 5
        self.auth_failure_window = 300  # 5 minutes
    
    def register_validator(self, validator_uid: str, public_key: str, is_trusted: bool = False):
        """Register a validator with credentials"""
        self.credentials[validator_uid] = ValidatorCredentials(
            validator_uid=validator_uid,
            public_key=public_key,
            is_trusted=is_trusted
        )
        
        if is_trusted:
            self.trusted_validators.add(validator_uid)
        
        logger.info(f"🔐 Registered validator: {validator_uid} (trusted: {is_trusted})")
    
    def authenticate_validator(self, validator_uid: str, signature: str, message: str) -> Tuple[bool, Optional[str]]:
        """
        Authenticate a validator using cryptographic signature.
        
        Args:
            validator_uid: Validator identifier
            signature: Cryptographic signature
            message: Original message that was signed
            
        Returns:
            Tuple of (authenticated, error_message)
        """
        if validator_uid not in self.credentials:
            self._record_auth_event(validator_uid, False, "Unknown validator")
            return False, "Unknown validator"
        
        credentials = self.credentials[validator_uid]
        
        # Check if validator is locked due to too many failures
        if self._is_validator_locked(validator_uid):
            self._record_auth_event(validator_uid, False, "Validator locked due to auth failures")
            return False, "Authentication locked due to repeated failures"
        
        try:
            # Verify signature (simplified - in real implementation, use proper crypto)
            if self._verify_signature(credentials.public_key, signature, message):
                credentials.last_authenticated = time.time()
                credentials.authentication_failures = 0
                self._record_auth_event(validator_uid, True, "Authentication successful")
                return True, None
            else:
                credentials.authentication_failures += 1
                self._record_auth_event(validator_uid, False, "Invalid signature")
                return False, "Invalid signature"
                
        except Exception as e:
            credentials.authentication_failures += 1
            self._record_auth_event(validator_uid, False, f"Authentication error: {e}")
            return False, f"Authentication error: {e}"
    
    def _verify_signature(self, public_key: str, signature: str, message: str) -> bool:
        """Verify cryptographic signature (simplified implementation)"""
        # In a real implementation, this would use proper cryptographic verification
        # For now, we'll use a simple HMAC-based verification
        expected_signature = hmac.new(
            public_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def _is_validator_locked(self, validator_uid: str) -> bool:
        """Check if validator is locked due to authentication failures"""
        if validator_uid not in self.credentials:
            return True
        
        credentials = self.credentials[validator_uid]
        return credentials.authentication_failures >= self.max_auth_failures
    
    def _record_auth_event(self, validator_uid: str, success: bool, details: str):
        """Record authentication event"""
        self.authentication_log.append({
            "timestamp": time.time(),
            "validator_uid": validator_uid,
            "success": success,
            "details": details
        })
        
        if not success:
            logger.warning(f"🔐 Authentication failed for {validator_uid}: {details}")
    
    def is_authorized(self, validator_uid: str, action: str) -> bool:
        """Check if validator is authorized for an action"""
        if validator_uid not in self.credentials:
            return False
        
        credentials = self.credentials[validator_uid]
        
        # Check if recently authenticated
        if not credentials.last_authenticated:
            return False
        
        auth_age = time.time() - credentials.last_authenticated
        if auth_age > 3600:  # 1 hour expiry
            return False
        
        # Check reputation threshold
        if credentials.reputation_score < DEFAULT_REPUTATION_THRESHOLD:
            return False
        
        # Check if locked
        if self._is_validator_locked(validator_uid):
            return False
        
        return True
    
    def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        recent_events = list(self.authentication_log)[-50:]  # Last 50 events
        
        successful_auths = sum(1 for event in recent_events if event["success"])
        failed_auths = len(recent_events) - successful_auths
        
        return {
            "registered_validators": len(self.credentials),
            "trusted_validators": len(self.trusted_validators),
            "recent_successful_auths": successful_auths,
            "recent_failed_auths": failed_auths,
            "locked_validators": sum(
                1 for cred in self.credentials.values()
                if cred.authentication_failures >= self.max_auth_failures
            ),
            "authentication_events": recent_events
        }


class SecurityValidator:
    """Main security validation coordinator"""
    
    def __init__(
        self,
        rate_limit_config: Optional[RateLimitConfig] = None,
        input_size_limit: int = DEFAULT_INPUT_SIZE_LIMIT
    ):
        """
        Initialize security validator.
        
        Args:
            rate_limit_config: Rate limiting configuration
            input_size_limit: Maximum input size in bytes
        """
        self.input_validator = InputValidator(input_size_limit)
        self.rate_limiter = RateLimiter(rate_limit_config or RateLimitConfig())
        self.authenticator = ValidatorAuthenticator()
        
        # Security monitoring
        self.security_events: deque = deque(maxlen=1000)
        self.blocked_clients: Dict[str, float] = {}  # client_id -> block_expiry_time
        
        # Statistics
        self.total_requests_processed = 0
        self.total_requests_blocked = 0
        self.start_time = time.time()
    
    async def validate_request(
        self,
        client_id: str,
        data: Any,
        context: str = "unknown",
        require_auth: bool = False,
        signature: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive request validation.
        
        Args:
            client_id: Client identifier
            data: Request data
            context: Request context
            require_auth: Whether authentication is required
            signature: Cryptographic signature if authentication required
            
        Returns:
            Tuple of (allowed, reason_if_denied)
        """
        self.total_requests_processed += 1
        
        # Check if client is blocked
        if self._is_client_blocked(client_id):
            reason = "Client temporarily blocked"
            await self._record_security_event(SecurityThreat.DOS, client_id, reason, blocked=True)
            self.total_requests_blocked += 1
            return False, reason
        
        # Rate limiting check
        rate_allowed, rate_reason = await self.rate_limiter.check_rate_limit(client_id)
        if not rate_allowed:
            await self._record_security_event(SecurityThreat.SPAM, client_id, rate_reason, blocked=True)
            self.total_requests_blocked += 1
            return False, rate_reason
        
        # Input validation
        validation_result, validation_error = self.input_validator.validate_input(data, context)
        if validation_result in [ValidationResult.INVALID, ValidationResult.MALICIOUS]:
            threat_type = SecurityThreat.INJECTION if validation_result == ValidationResult.MALICIOUS else SecurityThreat.DATA_CORRUPTION
            await self._record_security_event(threat_type, client_id, validation_error, blocked=True)
            self.total_requests_blocked += 1
            return False, validation_error
        
        # Authentication check
        if require_auth:
            if not signature:
                reason = "Authentication required but no signature provided"
                await self._record_security_event(SecurityThreat.IMPERSONATION, client_id, reason, blocked=True)
                self.total_requests_blocked += 1
                return False, reason
            
            auth_success, auth_error = self.authenticator.authenticate_validator(
                client_id, signature, json.dumps(data, default=str)
            )
            
            if not auth_success:
                await self._record_security_event(SecurityThreat.FORGERY, client_id, auth_error, blocked=True)
                self.total_requests_blocked += 1
                return False, auth_error
        
        # All checks passed
        return True, None
    
    def _is_client_blocked(self, client_id: str) -> bool:
        """Check if client is temporarily blocked"""
        if client_id not in self.blocked_clients:
            return False
        
        expiry_time = self.blocked_clients[client_id]
        if time.time() > expiry_time:
            del self.blocked_clients[client_id]
            return False
        
        return True
    
    def block_client(self, client_id: str, duration_seconds: int = 300):
        """Block a client temporarily"""
        self.blocked_clients[client_id] = time.time() + duration_seconds
        logger.warning(f"🚫 Blocked client {client_id} for {duration_seconds} seconds")
    
    async def _record_security_event(
        self,
        threat_type: SecurityThreat,
        source_id: str,
        description: str,
        blocked: bool = False
    ):
        """Record a security event"""
        event = SecurityEvent(
            timestamp=time.time(),
            threat_type=threat_type,
            source_id=source_id,
            description=description,
            blocked=blocked
        )
        
        self.security_events.append(event)
        
        # Log security event
        log_func = logger.warning if blocked else logger.info
        log_func(f"🔒 Security event: {threat_type.value} from {source_id} - {description}")
        
        # Auto-block for severe threats
        if threat_type in [SecurityThreat.DOS, SecurityThreat.INJECTION] and blocked:
            self.block_client(source_id, 600)  # 10 minute block
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get comprehensive security statistics"""
        recent_events = list(self.security_events)[-100:]  # Last 100 events
        
        threat_counts = defaultdict(int)
        for event in recent_events:
            threat_counts[event.threat_type.value] += 1
        
        return {
            "uptime_hours": (time.time() - self.start_time) / 3600,
            "total_requests_processed": self.total_requests_processed,
            "total_requests_blocked": self.total_requests_blocked,
            "block_rate": self.total_requests_blocked / self.total_requests_processed if self.total_requests_processed > 0 else 0.0,
            "currently_blocked_clients": len(self.blocked_clients),
            "recent_threat_counts": dict(threat_counts),
            "input_validation": self.input_validator.get_validation_stats(),
            "rate_limiting": self.rate_limiter.get_rate_limit_stats(),
            "authentication": self.authenticator.get_auth_stats(),
            "recent_security_events": [
                {
                    "timestamp": event.timestamp,
                    "threat_type": event.threat_type.value,
                    "source_id": event.source_id,
                    "description": event.description,
                    "blocked": event.blocked
                }
                for event in recent_events[-20:]  # Last 20 events
            ]
        }


# === Convenience Functions ===

def create_security_validator(**kwargs) -> SecurityValidator:
    """Create a security validator with optional configuration"""
    return SecurityValidator(**kwargs)


def setup_validator_security(validator_node_core):
    """Setup security validation for a validator node"""
    security_validator = SecurityValidator()
    
    # Register this validator for authentication
    security_validator.authenticator.register_validator(
        validator_uid=validator_node_core.info.uid,
        public_key=getattr(validator_node_core.account, 'public_key', 'default_key'),
        is_trusted=True
    )
    
    return security_validator 