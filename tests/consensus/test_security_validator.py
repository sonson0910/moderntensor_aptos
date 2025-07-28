#!/usr/bin/env python3
"""
Tests for Security Validator Module

Tests input validation, rate limiting, authentication, and security monitoring.
"""

import asyncio
import pytest
import time
import json
import hashlib
import hmac
from unittest.mock import Mock, patch, AsyncMock
from collections import deque

from mt_aptos.consensus.security_validator import (
    SecurityValidator, InputValidator, RateLimiter, ValidatorAuthenticator,
    SecurityThreat, ValidationResult, SecurityEvent, RateLimitConfig,
    ValidatorCredentials, create_security_validator, setup_validator_security
)


class TestInputValidator:
    """Test InputValidator functionality"""
    
    @pytest.fixture
    def validator(self):
        """Create input validator for testing"""
        return InputValidator(max_size=1024)  # 1KB limit for testing
    
    def test_validator_initialization(self, validator):
        """Test validator initialization"""
        assert validator.max_size == 1024
        assert len(validator.validation_errors) == 0
        assert len(validator.dangerous_patterns) > 0
        assert len(validator.compiled_patterns) == len(validator.dangerous_patterns)
    
    def test_valid_input(self, validator):
        """Test validation of valid input"""
        valid_data = {
            "task_id": "task_123",
            "timestamp": time.time(),
            "data": {"key": "value", "number": 42}
        }
        
        result, error = validator.validate_input(valid_data, "task_data")
        
        assert result == ValidationResult.VALID
        assert error is None
    
    def test_size_limit_validation(self, validator):
        """Test size limit validation"""
        # Create large data that exceeds limit
        large_data = {"large_field": "x" * 2000}  # 2KB of data
        
        result, error = validator.validate_input(large_data, "test")
        
        assert result == ValidationResult.INVALID
        assert "size" in error.lower()
        assert len(validator.validation_errors) == 1
    
    def test_malicious_content_detection(self, validator):
        """Test detection of malicious content"""
        malicious_data = {
            "script": "<script>alert('xss')</script>",
            "js_url": "javascript:alert('malicious')",
            "eval": "eval(malicious_code)"
        }
        
        result, error = validator.validate_input(malicious_data, "user_input")
        
        assert result == ValidationResult.MALICIOUS
        assert "malicious content" in error.lower()
        assert len(validator.validation_errors) == 1
    
    def test_invalid_data_types(self, validator):
        """Test validation of invalid data types"""
        # Data with invalid types (functions, classes, etc.)
        invalid_data = {
            "function": lambda x: x,  # Functions not allowed
            "valid_field": "valid_value"
        }
        
        result, error = validator.validate_input(invalid_data, "test")
        
        assert result == ValidationResult.INVALID
        assert "data types" in error.lower()
    
    def test_task_data_structure_validation(self, validator):
        """Test task data structure validation"""
        # Valid task data
        valid_task = {
            "task_id": "task_123",
            "timestamp": time.time(),
            "extra_field": "allowed"
        }
        
        result, error = validator.validate_input(valid_task, "task_data")
        assert result == ValidationResult.VALID
        
        # Invalid task data (missing required fields)
        invalid_task = {
            "extra_field": "not_enough"
        }
        
        result, error = validator.validate_input(invalid_task, "task_data")
        assert result == ValidationResult.INVALID
        assert "structure" in error.lower()
    
    def test_consensus_proposal_structure_validation(self, validator):
        """Test consensus proposal structure validation"""
        # Valid consensus proposal
        valid_proposal = {
            "slot": 123,
            "phase": "task_assignment",
            "proposer_uid": "validator_1",
            "proposal_data": {"key": "value"}
        }
        
        result, error = validator.validate_input(valid_proposal, "consensus_proposal")
        assert result == ValidationResult.VALID
        
        # Invalid proposal (missing fields)
        invalid_proposal = {
            "slot": 123
        }
        
        result, error = validator.validate_input(invalid_proposal, "consensus_proposal")
        assert result == ValidationResult.INVALID
    
    def test_miner_result_structure_validation(self, validator):
        """Test miner result structure validation"""
        # Valid miner result
        valid_result = {
            "miner_uid": "miner_1",
            "result": {"output": "generated_content"},
            "extra_data": "allowed"
        }
        
        result, error = validator.validate_input(valid_result, "miner_result")
        assert result == ValidationResult.VALID
        
        # Invalid result (missing fields)
        invalid_result = {
            "result": {"output": "content"}
        }
        
        result, error = validator.validate_input(invalid_result, "miner_result")
        assert result == ValidationResult.INVALID
    
    def test_get_validation_stats(self, validator):
        """Test validation statistics"""
        # Generate some validation errors
        validator.validate_input({"large": "x" * 2000}, "test")  # Size error
        validator.validate_input({"script": "<script>alert(1)</script>"}, "test")  # Malicious
        
        stats = validator.get_validation_stats()
        
        assert "total_validation_errors" in stats
        assert "recent_errors" in stats
        assert "error_types" in stats
        assert "max_input_size" in stats
        
        assert stats["total_validation_errors"] == 2
        assert len(stats["recent_errors"]) == 2
        assert stats["max_input_size"] == 1024


class TestRateLimiter:
    """Test RateLimiter functionality"""
    
    @pytest.fixture
    def rate_config(self):
        """Create rate limit config for testing"""
        return RateLimitConfig(
            requests_per_minute=20,
            burst_limit=25,
            window_size=60,
            adaptive=True
        )
    
    @pytest.fixture
    def burst_test_config(self):
        """Config optimized for burst limit testing"""
        return RateLimitConfig(
            requests_per_minute=50,  # High window limit
            burst_limit=5,  # Low burst limit for testing
            window_size=60,
            adaptive=True
        )
    
    @pytest.fixture 
    def window_test_config(self):
        """Config optimized for window limit testing"""
        return RateLimitConfig(
            requests_per_minute=10,  # Low window limit for testing
            burst_limit=50,  # High burst limit
            window_size=60,
            adaptive=True
        )

    @pytest.fixture
    def rate_limiter(self, rate_config):
        """Create rate limiter for testing"""
        return RateLimiter(rate_config)
    
    @pytest.fixture
    def burst_rate_limiter(self, burst_test_config):
        """Create rate limiter for burst testing"""
        return RateLimiter(burst_test_config)
    
    @pytest.fixture
    def window_rate_limiter(self, window_test_config):
        """Create rate limiter for window testing"""
        return RateLimiter(window_test_config)
    
    def test_rate_limiter_initialization(self, rate_limiter, rate_config):
        """Test rate limiter initialization"""
        assert rate_limiter.config == rate_config
        assert len(rate_limiter.request_windows) == 0
        assert len(rate_limiter.burst_counters) == 0
        assert len(rate_limiter.adaptive_limits) == 0
    
    @pytest.mark.asyncio
    async def test_normal_rate_limiting(self, rate_limiter):
        """Test normal rate limiting behavior"""
        client_id = "test_client"
        
        # First few requests should be allowed
        for i in range(3):
            allowed, reason = await rate_limiter.check_rate_limit(client_id)
            assert allowed is True
            assert reason is None
    
    @pytest.mark.asyncio
    async def test_burst_limit_enforcement(self, burst_rate_limiter):
        """Test burst limit enforcement"""
        client_id = "burst_client"
        
        # Fill burst limit (5 with burst_test_config)
        for i in range(5):
            allowed, reason = await burst_rate_limiter.check_rate_limit(client_id)
            assert allowed is True
        
        # Next request should be blocked
        allowed, reason = await burst_rate_limiter.check_rate_limit(client_id)
        assert allowed is False
        assert "burst limit" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_window_limit_enforcement(self, window_rate_limiter):
        """Test window limit enforcement"""
        client_id = "window_client"
        
        # Simulate requests over time to fill window (10 requests allowed)
        for i in range(10):
            allowed, reason = await window_rate_limiter.check_rate_limit(client_id, request_weight=1.0)
            assert allowed is True
        
        # 11th request should be blocked (exceeds window limit)
        allowed, reason = await window_rate_limiter.check_rate_limit(client_id)
        assert allowed is False
        assert "rate limit exceeded" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_adaptive_limits(self, rate_limiter):
        """Test adaptive rate limiting"""
        well_behaved_client = "good_client"
        
        # Simulate well-behaved client with reasonable intervals
        for i in range(5):
            allowed, reason = await rate_limiter.check_rate_limit(well_behaved_client)
            assert allowed is True
            await asyncio.sleep(0.01)  # Small delay between requests
        
        # Check that client behavior is being tracked
        assert well_behaved_client in rate_limiter.client_behaviors
        behavior = rate_limiter.client_behaviors[well_behaved_client]
        assert behavior["legitimate_requests"] == 5
        assert behavior["rejected_requests"] == 0
    
    @pytest.mark.asyncio
    async def test_burst_reset_after_delay(self, burst_rate_limiter):
        """Test burst counter reset after delay"""
        client_id = "reset_client"
        
        # Fill burst limit (5 with burst_test_config)
        for i in range(5):
            allowed, reason = await burst_rate_limiter.check_rate_limit(client_id)
            assert allowed is True
        
        # Should be blocked
        allowed, reason = await burst_rate_limiter.check_rate_limit(client_id)
        assert allowed is False
        
        # Wait for burst reset (mocked by directly modifying last request time)
        burst_rate_limiter.request_windows[client_id].append(time.time() - 11)  # 11 seconds ago
        
        # Should be allowed again
        allowed, reason = await burst_rate_limiter.check_rate_limit(client_id)
        assert allowed is True
    
    def test_get_rate_limit_stats(self, rate_limiter):
        """Test rate limiting statistics"""
        stats = rate_limiter.get_rate_limit_stats()
        
        assert "total_requests" in stats
        assert "total_rejections" in stats
        assert "rejection_rate" in stats
        assert "active_clients" in stats
        assert "config" in stats
        
        assert stats["total_requests"] == 0
        assert stats["total_rejections"] == 0
        assert stats["rejection_rate"] == 0.0
        assert stats["active_clients"] == 0


class TestValidatorAuthenticator:
    """Test ValidatorAuthenticator functionality"""
    
    @pytest.fixture
    def authenticator(self):
        """Create validator authenticator for testing"""
        return ValidatorAuthenticator()
    
    def test_authenticator_initialization(self, authenticator):
        """Test authenticator initialization"""
        assert len(authenticator.credentials) == 0
        assert len(authenticator.authentication_log) == 0
        assert len(authenticator.trusted_validators) == 0
        assert authenticator.max_auth_failures == 5
    
    def test_register_validator(self, authenticator):
        """Test validator registration"""
        validator_uid = "test_validator"
        public_key = "test_public_key"
        
        authenticator.register_validator(validator_uid, public_key, is_trusted=True)
        
        assert validator_uid in authenticator.credentials
        assert validator_uid in authenticator.trusted_validators
        
        credentials = authenticator.credentials[validator_uid]
        assert credentials.validator_uid == validator_uid
        assert credentials.public_key == public_key
        assert credentials.is_trusted is True
        assert credentials.reputation_score == 1.0
    
    def test_successful_authentication(self, authenticator):
        """Test successful validator authentication"""
        validator_uid = "test_validator"
        public_key = "test_key"
        message = "test_message"
        
        # Register validator
        authenticator.register_validator(validator_uid, public_key)
        
        # Create expected signature (simplified HMAC)
        expected_signature = hmac.new(
            public_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Authenticate
        success, error = authenticator.authenticate_validator(
            validator_uid, expected_signature, message
        )
        
        assert success is True
        assert error is None
        
        # Check credentials updated
        credentials = authenticator.credentials[validator_uid]
        assert credentials.last_authenticated is not None
        assert credentials.authentication_failures == 0
    
    def test_failed_authentication(self, authenticator):
        """Test failed validator authentication"""
        validator_uid = "test_validator"
        public_key = "test_key"
        message = "test_message"
        invalid_signature = "invalid_signature"
        
        # Register validator
        authenticator.register_validator(validator_uid, public_key)
        
        # Authenticate with invalid signature
        success, error = authenticator.authenticate_validator(
            validator_uid, invalid_signature, message
        )
        
        assert success is False
        assert "invalid signature" in error.lower()
        
        # Check failure recorded
        credentials = authenticator.credentials[validator_uid]
        assert credentials.authentication_failures == 1
    
    def test_unknown_validator_authentication(self, authenticator):
        """Test authentication of unknown validator"""
        success, error = authenticator.authenticate_validator(
            "unknown_validator", "signature", "message"
        )
        
        assert success is False
        assert "unknown validator" in error.lower()
    
    def test_validator_lockout_after_failures(self, authenticator):
        """Test validator lockout after repeated failures"""
        validator_uid = "failing_validator"
        public_key = "test_key"
        
        # Register validator
        authenticator.register_validator(validator_uid, public_key)
        
        # Generate multiple authentication failures
        for i in range(5):
            success, error = authenticator.authenticate_validator(
                validator_uid, "invalid_signature", "message"
            )
            assert success is False
        
        # Should be locked now
        success, error = authenticator.authenticate_validator(
            validator_uid, "any_signature", "message"
        )
        
        assert success is False
        assert "locked" in error.lower()
    
    def test_authorization_check(self, authenticator):
        """Test validator authorization"""
        validator_uid = "auth_validator"
        public_key = "test_key"
        message = "test_message"
        
        # Register validator
        authenticator.register_validator(validator_uid, public_key)
        
        # Should not be authorized without authentication
        assert not authenticator.is_authorized(validator_uid, "some_action")
        
        # Authenticate
        signature = hmac.new(
            public_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        authenticator.authenticate_validator(validator_uid, signature, message)
        
        # Should be authorized now
        assert authenticator.is_authorized(validator_uid, "some_action")
    
    def test_get_auth_stats(self, authenticator):
        """Test authentication statistics"""
        # Register some validators
        authenticator.register_validator("val1", "key1", is_trusted=True)
        authenticator.register_validator("val2", "key2", is_trusted=False)
        
        # Generate some auth events
        authenticator.authenticate_validator("val1", "invalid", "message")  # Failure
        
        stats = authenticator.get_auth_stats()
        
        assert "registered_validators" in stats
        assert "trusted_validators" in stats
        assert "recent_successful_auths" in stats
        assert "recent_failed_auths" in stats
        assert "locked_validators" in stats
        assert "authentication_events" in stats
        
        assert stats["registered_validators"] == 2
        assert stats["trusted_validators"] == 1
        assert stats["recent_failed_auths"] >= 1


class TestSecurityValidator:
    """Test SecurityValidator integration"""
    
    @pytest.fixture
    def security_validator(self):
        """Create security validator for testing"""
        rate_config = RateLimitConfig(
            requests_per_minute=10,
            burst_limit=3
        )
        return SecurityValidator(
            rate_limit_config=rate_config,
            input_size_limit=1024
        )
    
    def test_security_validator_initialization(self, security_validator):
        """Test security validator initialization"""
        assert security_validator.input_validator is not None
        assert security_validator.rate_limiter is not None
        assert security_validator.authenticator is not None
        assert security_validator.total_requests_processed == 0
        assert security_validator.total_requests_blocked == 0
    
    @pytest.mark.asyncio
    async def test_validate_request_success(self, security_validator):
        """Test successful request validation"""
        client_id = "good_client"
        valid_data = {
            "task_id": "task_123",
            "timestamp": time.time(),
            "data": {"key": "value"}
        }
        
        allowed, reason = await security_validator.validate_request(
            client_id=client_id,
            data=valid_data,
            context="task_data",
            require_auth=False
        )
        
        assert allowed is True
        assert reason is None
        assert security_validator.total_requests_processed == 1
        assert security_validator.total_requests_blocked == 0
    
    @pytest.mark.asyncio
    async def test_validate_request_input_validation_failure(self, security_validator):
        """Test request validation with input validation failure"""
        client_id = "malicious_client"
        malicious_data = {
            "script": "<script>alert('xss')</script>"
        }
        
        allowed, reason = await security_validator.validate_request(
            client_id=client_id,
            data=malicious_data,
            context="user_input"
        )
        
        assert allowed is False
        assert "malicious content" in reason.lower()
        assert security_validator.total_requests_blocked == 1
    
    @pytest.mark.asyncio
    async def test_validate_request_rate_limit_failure(self, security_validator):
        """Test request validation with rate limiting failure"""
        client_id = "spam_client"
        valid_data = {"task_id": "task_123", "timestamp": time.time()}
        
        # Fill rate limit
        for i in range(3):
            await security_validator.validate_request(client_id, valid_data)
        
        # Should be blocked now
        allowed, reason = await security_validator.validate_request(client_id, valid_data)
        
        assert allowed is False
        assert "burst limit" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_validate_request_authentication_required(self, security_validator):
        """Test request validation with authentication requirement"""
        client_id = "auth_client"
        public_key = "test_key"
        message_data = {"task_id": "task_123", "timestamp": time.time()}
        
        # Register validator
        security_validator.authenticator.register_validator(client_id, public_key)
        
        # Test without signature (should fail)
        allowed, reason = await security_validator.validate_request(
            client_id=client_id,
            data=message_data,
            require_auth=True
        )
        
        assert allowed is False
        assert "authentication required" in reason.lower()
        
        # Test with valid signature
        message = json.dumps(message_data, default=str)
        signature = hmac.new(
            public_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        allowed, reason = await security_validator.validate_request(
            client_id=client_id,
            data=message_data,
            require_auth=True,
            signature=signature
        )
        
        assert allowed is True
        assert reason is None
    
    @pytest.mark.asyncio
    async def test_validate_request_authentication_failure(self, security_validator):
        """Test request validation with authentication failure"""
        client_id = "fake_client"
        public_key = "test_key"
        message_data = {"task_id": "task_123", "timestamp": time.time()}
        invalid_signature = "invalid_signature"
        
        # Register validator
        security_validator.authenticator.register_validator(client_id, public_key)
        
        # Test with invalid signature
        allowed, reason = await security_validator.validate_request(
            client_id=client_id,
            data=message_data,
            require_auth=True,
            signature=invalid_signature
        )
        
        assert allowed is False
        assert "invalid signature" in reason.lower()
    
    def test_block_client(self, security_validator):
        """Test client blocking functionality"""
        client_id = "blocked_client"
        
        # Block client
        security_validator.block_client(client_id, duration_seconds=60)
        
        # Should be blocked
        assert security_validator._is_client_blocked(client_id)
        assert client_id in security_validator.blocked_clients
    
    def test_client_block_expiry(self, security_validator):
        """Test client block expiry"""
        client_id = "temp_blocked_client"
        
        # Block client for very short duration
        security_validator.block_client(client_id, duration_seconds=0.1)
        
        # Should be blocked initially
        assert security_validator._is_client_blocked(client_id)
        
        # Wait for expiry
        time.sleep(0.2)
        
        # Should not be blocked anymore
        assert not security_validator._is_client_blocked(client_id)
    
    def test_get_security_stats(self, security_validator):
        """Test security statistics"""
        stats = security_validator.get_security_stats()
        
        assert "uptime_hours" in stats
        assert "total_requests_processed" in stats
        assert "total_requests_blocked" in stats
        assert "block_rate" in stats
        assert "currently_blocked_clients" in stats
        assert "input_validation" in stats
        assert "rate_limiting" in stats
        assert "authentication" in stats
        assert "recent_security_events" in stats
        
        assert stats["total_requests_processed"] >= 0
        assert stats["total_requests_blocked"] >= 0


class TestIntegrationFunctions:
    """Test integration and utility functions"""
    
    def test_create_security_validator(self):
        """Test create_security_validator convenience function"""
        rate_config = RateLimitConfig(requests_per_minute=20)
        
        validator = create_security_validator(
            rate_limit_config=rate_config,
            input_size_limit=2048
        )
        
        assert isinstance(validator, SecurityValidator)
        assert validator.rate_limiter.config.requests_per_minute == 20
        assert validator.input_validator.max_size == 2048
    
    def test_setup_validator_security(self):
        """Test setup_validator_security function"""
        # Mock validator node core
        mock_core = Mock()
        mock_core.info.uid = "test_validator"
        mock_core.account.public_key = "test_public_key"
        
        security_validator = setup_validator_security(mock_core)
        
        assert isinstance(security_validator, SecurityValidator)
        
        # Should have registered the validator
        assert "test_validator" in security_validator.authenticator.credentials
        credentials = security_validator.authenticator.credentials["test_validator"]
        assert credentials.is_trusted is True


@pytest.mark.asyncio
async def test_complex_security_scenario():
    """Test complex security validation scenario"""
    security_validator = SecurityValidator(
        rate_limit_config=RateLimitConfig(
            requests_per_minute=5,
            burst_limit=2
        ),
        input_size_limit=512
    )
    
    # Register some validators
    security_validator.authenticator.register_validator("trusted_val", "trusted_key", is_trusted=True)
    security_validator.authenticator.register_validator("normal_val", "normal_key", is_trusted=False)
    
    # Scenario 1: Normal operation
    valid_data = {"task_id": "task_1", "timestamp": time.time()}
    
    allowed, reason = await security_validator.validate_request(
        client_id="trusted_val",
        data=valid_data,
        context="task_data"
    )
    assert allowed is True
    
    # Scenario 2: Rate limiting kicks in
    for i in range(3):  # Exceed burst limit
        await security_validator.validate_request("spam_client", valid_data)
    
    # Should be blocked
    allowed, reason = await security_validator.validate_request("spam_client", valid_data)
    assert allowed is False
    assert "burst limit" in reason.lower()
    
    # Scenario 3: Malicious input detected
    malicious_data = {
        "task_id": "evil_task",
        "script": "<script>document.location='http://evil.com'</script>"
    }
    
    allowed, reason = await security_validator.validate_request(
        client_id="attacker",
        data=malicious_data
    )
    assert allowed is False
    assert "malicious content" in reason.lower()
    
    # Scenario 4: Authentication flow
    message_data = {"sensitive": "data", "timestamp": time.time()}
    message = json.dumps(message_data, default=str)
    signature = hmac.new(
        "trusted_key".encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    allowed, reason = await security_validator.validate_request(
        client_id="trusted_val",
        data=message_data,
        require_auth=True,
        signature=signature
    )
    assert allowed is True
    
    # Check security stats
    stats = security_validator.get_security_stats()
    
    assert stats["total_requests_processed"] >= 4
    assert stats["total_requests_blocked"] >= 2
    assert stats["block_rate"] > 0
    assert len(stats["recent_security_events"]) > 0


if __name__ == "__main__":
    # Run tests with: python -m pytest test_security_validator.py -v
    pytest.main([__file__, "-v"]) 