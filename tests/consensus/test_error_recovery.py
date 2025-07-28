#!/usr/bin/env python3
"""
Tests for Error Recovery Module

Tests error detection, recovery mechanisms, graceful degradation, and health monitoring.
"""

import asyncio
import pytest
import time
import traceback
from unittest.mock import Mock, patch, AsyncMock, call
from collections import deque

from mt_aptos.consensus.error_recovery import (
    AutoRecovery, ErrorPattern, GracefulDegradation, 
    ComponentState, RecoveryStrategy, ErrorSeverity, 
    ErrorRecord, ComponentHealth, RecoveryAction,
    auto_recover, create_auto_recovery, setup_component_recovery
)


class TestErrorPattern:
    """Test ErrorPattern functionality"""
    
    @pytest.fixture
    def error_pattern(self):
        """Create error pattern detector for testing"""
        return ErrorPattern(window_seconds=60)  # 1 minute window
    
    def test_error_pattern_initialization(self, error_pattern):
        """Test error pattern initialization"""
        assert error_pattern.window_seconds == 60
        assert len(error_pattern.error_sequences) == 0
        assert len(error_pattern.pattern_cache) == 0
    
    def test_add_error(self, error_pattern):
        """Test adding errors to pattern tracking"""
        error = ErrorRecord(
            timestamp=time.time(),
            component="test_component",
            error_type="TestError",
            message="Test error message",
            severity=ErrorSeverity.MEDIUM
        )
        
        error_pattern.add_error(error)
        
        assert len(error_pattern.error_sequences) == 1
        assert error_pattern.error_sequences[0] == error
    
    def test_detect_high_frequency_pattern(self, error_pattern):
        """Test detecting high frequency error patterns"""
        current_time = time.time()
        
        # Add multiple similar errors
        for i in range(5):
            error = ErrorRecord(
                timestamp=current_time - i * 5,  # 5 seconds apart
                component="test_component",
                error_type="NetworkError",
                message=f"Network error {i}",
                severity=ErrorSeverity.MEDIUM
            )
            error_pattern.add_error(error)
        
        patterns = error_pattern.detect_patterns()
        
        # Should detect high frequency pattern
        assert len(patterns) > 0
        high_freq_patterns = [p for p in patterns if p["type"] == "high_frequency"]
        assert len(high_freq_patterns) > 0
        
        pattern = high_freq_patterns[0]
        assert pattern["component"] == "test_component"
        assert pattern["error_type"] == "NetworkError"
        assert pattern["count"] >= 3
    
    def test_detect_cascade_failure_pattern(self, error_pattern):
        """Test detecting cascade failure patterns"""
        current_time = time.time()
        
        # Add multiple different error types from same component
        error_types = ["NetworkError", "TimeoutError", "ValidationError"]
        for i, error_type in enumerate(error_types):
            error = ErrorRecord(
                timestamp=current_time - i * 2,
                component="critical_component",
                error_type=error_type,
                message=f"{error_type} occurred",
                severity=ErrorSeverity.HIGH
            )
            error_pattern.add_error(error)
        
        patterns = error_pattern.detect_patterns()
        
        # Should detect cascade failure
        cascade_patterns = [p for p in patterns if p["type"] == "cascade_failure"]
        assert len(cascade_patterns) > 0
        
        pattern = cascade_patterns[0]
        assert pattern["component"] == "critical_component"
        assert len(pattern["error_types"]) >= 2
        assert pattern["severity"] == "critical"


class TestGracefulDegradation:
    """Test GracefulDegradation functionality"""
    
    @pytest.fixture
    def degradation(self):
        """Create graceful degradation manager for testing"""
        return GracefulDegradation()
    
    def test_degradation_initialization(self, degradation):
        """Test degradation initialization"""
        assert len(degradation.degradation_modes) == 0
        assert len(degradation.active_degradations) == 0
        assert len(degradation.degradation_callbacks) == 0
    
    def test_register_degradation_mode(self, degradation):
        """Test registering degradation modes"""
        activated = False
        
        def activate_func():
            nonlocal activated
            activated = True
        
        def deactivate_func():
            nonlocal activated
            activated = False
        
        degradation.register_degradation_mode(
            component="test_component",
            mode_name="limited_mode",
            activate_func=activate_func,
            deactivate_func=deactivate_func,
            description="Test degradation mode"
        )
        
        assert "test_component" in degradation.degradation_modes
        assert "limited_mode" in degradation.degradation_modes["test_component"]
        
        mode_info = degradation.degradation_modes["test_component"]["limited_mode"]
        assert mode_info["description"] == "Test degradation mode"
        assert mode_info["activations"] == 0
    
    @pytest.mark.asyncio
    async def test_activate_degradation(self, degradation):
        """Test activating degradation mode"""
        activated = False
        
        def activate_func():
            nonlocal activated
            activated = True
        
        degradation.register_degradation_mode(
            component="test_component",
            mode_name="safe_mode",
            activate_func=activate_func
        )
        
        # Activate degradation
        result = await degradation.activate_degradation("test_component", "safe_mode")
        
        assert result is True
        assert activated is True
        assert "test_component" in degradation.active_degradations
        
        mode_info = degradation.degradation_modes["test_component"]["safe_mode"]
        assert mode_info["activations"] == 1
    
    @pytest.mark.asyncio
    async def test_deactivate_degradation(self, degradation):
        """Test deactivating degradation mode"""
        activated = True
        
        def activate_func():
            nonlocal activated
            activated = True
        
        def deactivate_func():
            nonlocal activated
            activated = False
        
        degradation.register_degradation_mode(
            component="test_component",
            mode_name="safe_mode",
            activate_func=activate_func,
            deactivate_func=deactivate_func
        )
        
        # Activate then deactivate
        await degradation.activate_degradation("test_component", "safe_mode")
        assert activated is True
        
        result = await degradation.deactivate_degradation("test_component")
        
        assert result is True
        assert activated is False
        assert "test_component" not in degradation.active_degradations
    
    def test_is_degraded(self, degradation):
        """Test checking degradation status"""
        # Initially not degraded
        assert not degradation.is_degraded("test_component")
        
        # Mark as degraded
        degradation.active_degradations["test_component"] = time.time()
        
        # Should be degraded now
        assert degradation.is_degraded("test_component")
    
    def test_get_degradation_stats(self, degradation):
        """Test degradation statistics"""
        def dummy_func():
            pass
        
        degradation.register_degradation_mode(
            component="comp1",
            mode_name="mode1",
            activate_func=dummy_func,
            description="Test mode 1"
        )
        
        degradation.active_degradations["comp1"] = time.time()
        
        stats = degradation.get_degradation_stats()
        
        assert "currently_degraded" in stats
        assert "degradation_count" in stats
        assert "modes" in stats
        
        assert "comp1" in stats["currently_degraded"]
        assert stats["degradation_count"] == 1
        assert "comp1" in stats["modes"]
        assert "mode1" in stats["modes"]["comp1"]


class TestAutoRecovery:
    """Test AutoRecovery functionality"""
    
    @pytest.fixture
    def auto_recovery(self):
        """Create auto recovery system for testing"""
        recovery = AutoRecovery(test_mode=True)
        return recovery
    
    def test_auto_recovery_initialization(self, auto_recovery):
        """Test auto recovery initialization"""
        assert len(auto_recovery.recovery_actions) == 0
        assert len(auto_recovery.component_health) == 0
        assert len(auto_recovery.recovery_in_progress) == 0
        assert not auto_recovery.health_check_active
    
    def test_register_component(self, auto_recovery):
        """Test registering components"""
        def restart_func():
            pass
        
        auto_recovery.register_component(
            component_name="test_component",
            restart_func=restart_func
        )
        
        assert "test_component" in auto_recovery.component_health
        health = auto_recovery.component_health["test_component"]
        assert health.component_name == "test_component"
        assert health.state == ComponentState.HEALTHY
        
        # Should have registered restart action
        assert "test_component" in auto_recovery.recovery_actions
        actions = auto_recovery.recovery_actions["test_component"]
        assert len(actions) == 1
        assert actions[0].strategy == RecoveryStrategy.RESTART
    
    def test_register_recovery_action(self, auto_recovery):
        """Test registering recovery actions"""
        def custom_recovery():
            pass
        
        action = RecoveryAction(
            strategy=RecoveryStrategy.DEGRADE,
            component="test_component",
            action_func=custom_recovery,
            description="Custom recovery action"
        )
        
        auto_recovery.register_recovery_action(action)
        
        assert "test_component" in auto_recovery.recovery_actions
        actions = auto_recovery.recovery_actions["test_component"]
        assert len(actions) == 1
        assert actions[0] == action
    
    @pytest.mark.asyncio
    async def test_record_error_low_severity(self, auto_recovery):
        """Test recording low severity error"""
        auto_recovery.register_component("test_component")
        
        error = Exception("Test error")
        await auto_recovery.record_error("test_component", error, ErrorSeverity.LOW)
        
        health = auto_recovery.component_health["test_component"]
        assert health.error_count == 1
        assert health.consecutive_failures == 1
        assert health.state == ComponentState.DEGRADED
        assert health.last_error is not None
        assert health.last_error.error_type == "Exception"
    
    @pytest.mark.asyncio
    async def test_record_multiple_errors_triggers_recovery(self, auto_recovery):
        """Test that multiple errors trigger recovery"""
        recovery_called = False
        
        def restart_func():
            nonlocal recovery_called
            recovery_called = True
        
        auto_recovery.register_component("test_component", restart_func=restart_func, test_mode=True)
        
        # Record multiple errors to trigger recovery
        for i in range(3):
            error = Exception(f"Test error {i}")
            await auto_recovery.record_error("test_component", error, ErrorSeverity.MEDIUM)
        
        # Give recovery time to execute
        await asyncio.sleep(0.1)
        
        health = auto_recovery.component_health["test_component"]
        # After successful recovery, consecutive_failures should be reset to 0
        assert health.consecutive_failures == 0
        assert health.state == ComponentState.HEALTHY
        assert recovery_called is True
    
    @pytest.mark.asyncio
    async def test_critical_error_triggers_immediate_recovery(self, auto_recovery):
        """Test that critical error triggers immediate recovery"""
        recovery_called = False
        
        def restart_func():
            nonlocal recovery_called
            recovery_called = True
        
        auto_recovery.register_component("test_component", restart_func=restart_func, test_mode=True)
        
        # Record critical error
        error = Exception("Critical system failure")
        await auto_recovery.record_error("test_component", error, ErrorSeverity.CRITICAL)
        
        # Give recovery time to execute
        await asyncio.sleep(0.1)
        
        assert recovery_called is True
    
    @pytest.mark.asyncio
    async def test_successful_recovery_resets_failures(self, auto_recovery):
        """Test successful recovery resets failure count"""
        recovery_called = False
        
        def restart_func():
            nonlocal recovery_called
            recovery_called = True
        
        auto_recovery.register_component("test_component", restart_func=restart_func, test_mode=True)
        
        # Record errors to trigger recovery
        for i in range(3):
            error = Exception(f"Test error {i}")
            await auto_recovery.record_error("test_component", error, ErrorSeverity.MEDIUM)
        
        # Give recovery time to execute
        await asyncio.sleep(0.2)
        
        health = auto_recovery.component_health["test_component"]
        assert recovery_called is True
        assert health.consecutive_failures == 0  # Should be reset after successful recovery
        assert health.state == ComponentState.HEALTHY
    
    @pytest.mark.asyncio
    async def test_start_stop_health_monitoring(self, auto_recovery):
        """Test starting and stopping health monitoring"""
        await auto_recovery.start_health_monitoring()
        
        assert auto_recovery.health_check_active
        assert auto_recovery.health_check_task is not None
        
        await auto_recovery.stop_health_monitoring()
        
        assert not auto_recovery.health_check_active
        assert auto_recovery.health_check_task is None
    
    def test_get_recovery_stats(self, auto_recovery):
        """Test recovery statistics"""
        auto_recovery.register_component("comp1")
        auto_recovery.register_component("comp2")
        
        # Mark one component as unhealthy
        auto_recovery.component_health["comp1"].state = ComponentState.UNHEALTHY
        auto_recovery.component_health["comp1"].consecutive_failures = 2
        
        stats = auto_recovery.get_recovery_stats()
        
        assert "total_components" in stats
        assert "healthy_components" in stats
        assert "unhealthy_components" in stats
        assert "recovery_in_progress" in stats
        assert "component_status" in stats
        
        assert stats["total_components"] == 2
        assert stats["healthy_components"] == 1
        assert stats["unhealthy_components"] == 1
        
        assert "comp1" in stats["component_status"]
        assert "comp2" in stats["component_status"]


class TestAutoRecoverDecorator:
    """Test auto_recover decorator"""
    
    @pytest.fixture
    def recovery_system(self):
        """Create recovery system for decorator testing"""
        return AutoRecovery()
    
    @pytest.mark.asyncio
    async def test_async_function_success(self, recovery_system):
        """Test decorator with successful async function"""
        
        @auto_recover("test_component", recovery_system, ErrorSeverity.MEDIUM)
        async def test_async_func():
            return "success"
        
        result = await test_async_func()
        assert result == "success"
        
        # No errors should be recorded
        assert "test_component" not in recovery_system.component_health
    
    @pytest.mark.asyncio
    async def test_async_function_error(self, recovery_system):
        """Test decorator with failing async function"""
        
        @auto_recover("test_component", recovery_system, ErrorSeverity.HIGH)
        async def test_async_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await test_async_func()
        
        # Error should be recorded (but component might not be registered yet)
        # In real usage, component would be registered first
    
    def test_sync_function_success(self, recovery_system):
        """Test decorator with successful sync function"""
        
        @auto_recover("test_component", recovery_system, ErrorSeverity.MEDIUM)
        def test_sync_func():
            return "success"
        
        result = test_sync_func()
        assert result == "success"
    
    def test_sync_function_error(self, recovery_system):
        """Test decorator with failing sync function"""
        
        @auto_recover("test_component", recovery_system, ErrorSeverity.HIGH)
        def test_sync_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_sync_func()


class TestIntegrationFunctions:
    """Test integration and utility functions"""
    
    @pytest.mark.asyncio
    async def test_create_auto_recovery(self):
        """Test create_auto_recovery convenience function"""
        recovery = await create_auto_recovery()
        
        try:
            assert isinstance(recovery, AutoRecovery)
            assert recovery.health_check_active
        finally:
            await recovery.stop_health_monitoring()
    
    def test_setup_component_recovery(self):
        """Test setup_component_recovery function"""
        recovery_system = AutoRecovery()
        
        def restart_func():
            pass
        
        def health_check_func():
            return True
        
        result = setup_component_recovery(
            component_name="test_component",
            recovery_system=recovery_system,
            restart_func=restart_func,
            health_check_func=health_check_func
        )
        
        assert result == recovery_system
        assert "test_component" in recovery_system.component_health
        assert "test_component" in recovery_system.recovery_actions


class TestComplexScenarios:
    """Test complex error recovery scenarios"""
    
    @pytest.mark.asyncio
    async def test_cascading_failures(self):
        """Test handling cascading failures across multiple components"""
        recovery = AutoRecovery(test_mode=True)
        
        recovery_calls = {"comp1": 0, "comp2": 0, "comp3": 0}
        
        def make_restart_func(comp_name):
            def restart_func():
                recovery_calls[comp_name] += 1
            return restart_func
        
        # Register multiple components
        for comp in ["comp1", "comp2", "comp3"]:
            recovery.register_component(comp, restart_func=make_restart_func(comp), test_mode=True)
        
        # Simulate cascading failures
        components = ["comp1", "comp2", "comp3"]
        for i, comp in enumerate(components):
            for j in range(3):  # 3 errors per component
                error = Exception(f"Cascading error {j} in {comp}")
                await recovery.record_error(comp, error, ErrorSeverity.HIGH)
                await asyncio.sleep(0.01)  # Small delay between errors
        
        # Give recovery time to execute
        await asyncio.sleep(0.3)
        
        # All components should have attempted recovery
        for comp in components:
            assert recovery_calls[comp] > 0
    
    @pytest.mark.asyncio
    async def test_recovery_failure_and_degradation(self):
        """Test graceful degradation when recovery fails"""
        recovery = AutoRecovery()
        
        def failing_restart():
            raise Exception("Recovery failed")
        
        recovery.register_component("failing_component", restart_func=failing_restart)
        
        # Record multiple errors to trigger recovery
        for i in range(3):
            error = Exception(f"Test error {i}")
            await recovery.record_error("failing_component", error, ErrorSeverity.HIGH)
        
        # Give recovery time to fail
        await asyncio.sleep(0.2)
        
        health = recovery.component_health["failing_component"]
        # Component should still be in failed state since recovery failed
        assert health.state in [ComponentState.FAILED, ComponentState.DEGRADED]
    
    @pytest.mark.asyncio
    async def test_error_pattern_triggers_preemptive_recovery(self):
        """Test that error patterns trigger preemptive recovery"""
        recovery = AutoRecovery(test_mode=True)
        
        recovery_called = False
        
        def restart_func():
            nonlocal recovery_called
            recovery_called = True
        
        recovery.register_component("pattern_component", restart_func=restart_func, test_mode=True)
        
        # Generate error pattern (same error type repeatedly)
        current_time = time.time()
        for i in range(4):  # 4 similar errors in short time
            error = Exception("Network timeout")
            await recovery.record_error("pattern_component", error, ErrorSeverity.MEDIUM)
            await asyncio.sleep(0.01)
        
        # Give recovery time to execute
        await asyncio.sleep(0.2)
        
        # Should have triggered recovery due to pattern detection
        assert recovery_called is True


@pytest.mark.asyncio
async def test_integration_with_real_component():
    """Test integration with a real component simulation"""
    recovery = AutoRecovery(test_mode=True)
    
    class SimulatedService:
        def __init__(self):
            self.running = True
            self.error_count = 0
        
        def restart(self):
            self.running = True
            self.error_count = 0
        
        def simulate_error(self):
            self.error_count += 1
            if self.error_count >= 3:
                self.running = False
        
        def health_check(self):
            return self.running
    
    service = SimulatedService()
    
    # Register service with recovery system
    recovery.register_component(
        component_name="simulated_service",
        restart_func=service.restart,
        health_check_func=service.health_check, test_mode=True
    )
    
    # Start health monitoring
    await recovery.start_health_monitoring()
    
    try:
        # Simulate errors
        for i in range(3):
            service.simulate_error()
            error = Exception(f"Service error {i}")
            await recovery.record_error("simulated_service", error, ErrorSeverity.MEDIUM)
        
        # Give recovery time to execute
        await asyncio.sleep(0.3)
        
        # Service should be restarted and healthy again
        assert service.running is True
        assert service.error_count == 0
        
        health = recovery.component_health["simulated_service"]
        assert health.state == ComponentState.HEALTHY
        
    finally:
        await recovery.stop_health_monitoring()


if __name__ == "__main__":
    # Run tests with: python -m pytest test_error_recovery.py -v
    pytest.main([__file__, "-v"]) 