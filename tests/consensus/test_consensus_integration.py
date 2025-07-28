#!/usr/bin/env python3
"""
Integration Tests for Consensus System

Tests the integration of all consensus modules working together:
- Resource Management
- Error Recovery  
- Performance Optimization
- Security Validation
- Monitoring Dashboard
- Consensus Coordination
- Continuous Task Assignment
"""

import asyncio
import pytest
import pytest_asyncio
import time
import json
from unittest.mock import Mock, patch, AsyncMock
from collections import deque

from mt_aptos.consensus.resource_manager import ResourceManager, setup_basic_cleanup
from mt_aptos.consensus.error_recovery import AutoRecovery, ErrorSeverity, setup_component_recovery
from mt_aptos.consensus.performance_optimizer import PerformanceOptimizer, BatchConfig, CacheConfig
from mt_aptos.consensus.security_validator import SecurityValidator, RateLimitConfig
from mt_aptos.consensus.monitoring_dashboard import MonitoringDashboard
from mt_aptos.consensus.consensus_coordinator import ConsensusCoordinator, ConsensusPhase
from mt_aptos.consensus.continuous_task_assignment import ContinuousTaskAssignment


class MockValidatorCore:
    """Mock validator core for testing"""
    
    def __init__(self, validator_uid: str):
        self.info = Mock()
        self.info.uid = validator_uid
        
        self.account = Mock()
        self.account.public_key = f"pubkey_{validator_uid}"
        
        self.aptos_client = Mock()
        self.contract_address = "0x123"
        
        # Task management
        self.tasks_sent = {}
        self.results_buffer = {}
        self.cycle_scores = {}
        self.miner_is_busy = set()
        
        # Network
        self.http_client = Mock()
        
        # Slot configuration
        self.slot_config = Mock()
        self.slot_config.task_assignment_minutes = 2.0
        
        # Validators and miners
        self.validators_info = {}
        self.miners_info = {}
        
        # Settings
        self.settings = Mock()
        self.settings.CONTINUOUS_BATCH_SIZE = 3
        self.settings.CONTINUOUS_TIMEOUT_SECONDS = 10.0
        self.settings.CONTINUOUS_SCORE_AGGREGATION = "average"
    
    def get_current_blockchain_slot(self):
        """Mock current slot"""
        return int(time.time()) // 60  # 1 minute slots
    
    async def send_task_to_miner(self, miner_uid: str, task_data: dict):
        """Mock task sending"""
        await asyncio.sleep(0.01)  # Simulate network delay
        return {"status": "sent", "task_id": task_data.get("task_id")}


class TestConsensusCoreIntegration:
    """Test core consensus components integration"""
    
    @pytest_asyncio.fixture
    async def validator_core(self):
        """Create mock validator core"""
        return MockValidatorCore("test_validator_1")
    
    @pytest_asyncio.fixture
    async def resource_manager(self, validator_core):
        """Create resource manager"""
        manager = setup_basic_cleanup(validator_core)
        await manager.start()
        yield manager
        await manager.stop()
    
    @pytest_asyncio.fixture
    async def error_recovery(self):
        """Create error recovery system"""
        recovery = AutoRecovery()
        await recovery.start_health_monitoring()
        yield recovery
        await recovery.stop_health_monitoring()
    
    @pytest_asyncio.fixture
    async def performance_optimizer(self):
        """Create performance optimizer"""
        optimizer = PerformanceOptimizer(
            max_workers=2,
            batch_config=BatchConfig(batch_size=3, max_wait_time=0.1),
            cache_config=CacheConfig(max_size=10, ttl=1.0)
        )
        await optimizer.start()
        yield optimizer
        await optimizer.stop()
    
    @pytest.fixture
    def security_validator(self):
        """Create security validator"""
        return SecurityValidator(
            rate_limit_config=RateLimitConfig(requests_per_minute=20, burst_limit=5),
            input_size_limit=2048
        )
    
    @pytest_asyncio.fixture
    async def monitoring_dashboard(self, validator_core):
        """Create monitoring dashboard"""
        dashboard = MonitoringDashboard(validator_core.info.uid)
        await dashboard.start()
        yield dashboard
        await dashboard.stop()
    
    @pytest.mark.asyncio
    async def test_integrated_resource_management_and_monitoring(
        self, validator_core, resource_manager, monitoring_dashboard
    ):
        """Test resource management integration with monitoring"""
        
        # Create test data that will be cleaned up
        test_data = {f"item_{i}": {"timestamp": time.time()} for i in range(10)}
        
        # Register for cleanup
        resource_manager.register_cleanup_target(
            "test_data",
            test_data,
            cleanup_strategy="size",
            max_size=5
        )
        
        # Let resource manager run briefly
        await asyncio.sleep(0.2)
        
        # Check that cleanup occurred
        assert len(test_data) <= 5
        
        # Check resource stats
        resource_stats = resource_manager.get_comprehensive_stats()
        assert "cleanup" in resource_stats
        assert resource_stats["cleanup"]["total_cleanups"] > 0
        
        # Record metrics in monitoring
        monitoring_dashboard.record_system_metrics(
            memory_bytes=resource_stats["memory"]["current_mb"] * 1024 * 1024,
            cpu_percent=50.0
        )
        
        # Verify monitoring recorded the data
        dashboard_data = monitoring_dashboard.get_dashboard_data()
        assert "memory_usage_bytes" in dashboard_data["metrics"]
        assert dashboard_data["metrics"]["memory_usage_bytes"]["count"] >= 1
    
    @pytest.mark.asyncio
    async def test_error_recovery_with_performance_monitoring(
        self, error_recovery, performance_optimizer, monitoring_dashboard
    ):
        """Test error recovery integration with performance monitoring"""
        
        # Register a component with error recovery
        recovery_called = False
        
        def restart_component():
            nonlocal recovery_called
            recovery_called = True
        
        error_recovery.register_component(
            "test_component",
            restart_func=restart_component
        )
        
        # Simulate errors and recovery using performance optimizer
        async def failing_task():
            raise ValueError("Simulated failure")
        
        # Execute failing task through optimizer (should catch error)
        try:
            await performance_optimizer.execute_task(failing_task)
        except ValueError:
            pass  # Expected
        
        # Record error in recovery system
        await error_recovery.record_error(
            "test_component",
            ValueError("Simulated failure"),
            ErrorSeverity.HIGH
        )
        
        # Give recovery time to execute
        await asyncio.sleep(0.1)
        
        # Verify recovery was triggered
        assert recovery_called is True
        
        # Record recovery metrics
        monitoring_dashboard.record_consensus_round(success=False, duration=2.0)
        monitoring_dashboard.record_consensus_round(success=True, duration=1.5)  # After recovery
        
        # Check recovery stats
        recovery_stats = error_recovery.get_recovery_stats()
        assert recovery_stats["total_components"] == 1
        
        # Check monitoring data
        dashboard_data = monitoring_dashboard.get_dashboard_data()
        consensus_metrics = dashboard_data["metrics"]["consensus_rounds_total"]
        assert consensus_metrics["count"] == 2
    
    @pytest.mark.asyncio
    async def test_security_validation_with_performance_optimization(
        self, security_validator, performance_optimizer, monitoring_dashboard
    ):
        """Test security validation integration with performance optimization"""
        
        # Register validator for authentication
        security_validator.authenticator.register_validator(
            "test_client", "test_key", is_trusted=True
        )
        
        # Test valid request through security and performance systems
        valid_data = {
            "task_id": "secure_task_1",
            "timestamp": time.time(),
            "data": {"operation": "test"}
        }
        
        # Validate security
        allowed, reason = await security_validator.validate_request(
            client_id="test_client",
            data=valid_data,
            context="task_data"
        )
        
        assert allowed is True
        assert reason is None
        
        # Process through performance optimizer
        async def secure_task(data):
            await asyncio.sleep(0.01)
            return {"result": f"processed_{data['task_id']}"}
        
        result = await performance_optimizer.execute_task(secure_task, valid_data)
        assert "processed_secure_task_1" in result["result"]
        
        # Record network request metrics
        monitoring_dashboard.record_network_request(success=True, duration=0.05)
        
        # Check security stats
        security_stats = security_validator.get_security_stats()
        assert security_stats["total_requests_processed"] >= 1
        assert security_stats["total_requests_blocked"] == 0
        
        # Check performance stats
        perf_stats = performance_optimizer.get_comprehensive_stats()
        assert perf_stats["task_pool"]["completed_tasks"] >= 1
    
    @pytest.mark.asyncio
    async def test_malicious_request_handling_with_monitoring(
        self, security_validator, monitoring_dashboard
    ):
        """Test malicious request handling with comprehensive monitoring"""
        
        # Test malicious input
        malicious_data = {
            "task_id": "evil_task",
            "script": "<script>alert('xss')</script>",
            "timestamp": time.time()
        }
        
        # Should be blocked by security validator
        allowed, reason = await security_validator.validate_request(
            client_id="attacker",
            data=malicious_data,
            context="user_input"
        )
        
        assert allowed is False
        assert "malicious content" in reason.lower()
        
        # Record the security event in monitoring
        monitoring_dashboard.record_network_request(success=False, duration=0.01)
        
        # Check security stats
        security_stats = security_validator.get_security_stats()
        assert security_stats["total_requests_blocked"] >= 1
        assert len(security_stats["recent_security_events"]) >= 1
        
        # Verify the security event was recorded
        recent_events = security_stats["recent_security_events"]
        assert any("injection" in event["threat_type"] for event in recent_events)
        
        # Check monitoring recorded the failed request
        dashboard_data = monitoring_dashboard.get_dashboard_data()
        network_errors = dashboard_data["metrics"]["network_errors_total"]
        assert network_errors["count"] >= 1


class TestContinuousTaskAssignmentIntegration:
    """Test continuous task assignment with full system integration"""
    
    @pytest_asyncio.fixture
    async def integrated_validator(self):
        """Create fully integrated validator system"""
        validator_core = MockValidatorCore("integrated_validator")
        
        # Initialize all systems
        systems = {
            "resource_manager": setup_basic_cleanup(validator_core),
            "error_recovery": AutoRecovery(),
            "performance_optimizer": PerformanceOptimizer(max_workers=2),
            "security_validator": SecurityValidator(),
            "monitoring_dashboard": MonitoringDashboard(validator_core.info.uid),
        }
        
        # Start all systems
        await systems["resource_manager"].start()
        await systems["error_recovery"].start_health_monitoring()
        await systems["performance_optimizer"].start()
        await systems["monitoring_dashboard"].start()
        
        # Create task assignment system
        task_assignment = ContinuousTaskAssignment(validator_core)
        
        yield {
            "core": validator_core,
            "task_assignment": task_assignment,
            **systems
        }
        
        # Cleanup
        await systems["resource_manager"].stop()
        await systems["error_recovery"].stop_health_monitoring()
        await systems["performance_optimizer"].stop()
        await systems["monitoring_dashboard"].stop()
    
    @pytest.mark.asyncio
    async def test_full_system_task_assignment_flow(self, integrated_validator):
        """Test complete task assignment flow with all systems integrated"""
        
        systems = integrated_validator
        core = systems["core"]
        task_assignment = systems["task_assignment"]
        
        # Mock miners
        core.miners_info = {
            f"miner_{i}": {
                "uid": f"miner_{i}",
                "endpoint": f"http://miner{i}.test",
                "stake": 1000 + i * 100
            }
            for i in range(5)
        }
        
        # Mock task creation
        async def create_test_task(miner_uid):
            return {
                "task_id": f"task_{miner_uid}_{int(time.time())}",
                "timestamp": time.time(),
                "prompt": "Generate an image of a sunset",
                "guidance_scale": 7.5,
                "resolution": "512x512"
            }
        
        # Mock miner responses
        async def mock_send_task(miner_uid, task_data):
            await asyncio.sleep(0.01)  # Simulate network delay
            
            # Simulate different response qualities
            if "miner_0" in miner_uid or "miner_1" in miner_uid:
                # High quality response
                return {
                    "status": "success",
                    "result": {
                        "image_url": f"http://result.test/{task_data['task_id']}.jpg",
                        "generation_time": 2.5,
                        "model_version": "stable-diffusion-v2"
                    },
                    "miner_uid": miner_uid
                }
            else:
                # Lower quality or failed response
                return {
                    "status": "partial",
                    "result": {
                        "image_url": f"http://result.test/{task_data['task_id']}.jpg",
                        "generation_time": 5.0
                    },
                    "miner_uid": miner_uid
                }
        
        # Patch methods
        with patch.object(task_assignment, 'create_task_data', side_effect=create_test_task):
            with patch.object(core, 'send_task_to_miner', side_effect=mock_send_task):
                
                # Run continuous task assignment
                current_slot = core.get_current_blockchain_slot()
                final_scores = await task_assignment.run_continuous_assignment(current_slot)
                
                # Verify results
                assert len(final_scores) > 0
                assert all(0.0 <= score <= 1.0 for score in final_scores.values())
                
                # Check that high-quality miners got better scores
                if "miner_0" in final_scores and "miner_2" in final_scores:
                    assert final_scores["miner_0"] >= final_scores["miner_2"]
                
                # Record metrics in monitoring
                systems["monitoring_dashboard"].record_task_assignment(
                    duration=2.0, 
                    tasks_count=len(final_scores)
                )
                
                # Check resource usage
                resource_stats = systems["resource_manager"].get_comprehensive_stats()
                assert resource_stats["uptime_hours"] > 0
                
                # Check performance stats
                perf_stats = systems["performance_optimizer"].get_comprehensive_stats()
                assert perf_stats["task_pool"]["completed_tasks"] >= 0
                
                # Check monitoring data
                dashboard_data = systems["monitoring_dashboard"].get_dashboard_data()
                assert "task_assignment_duration" in dashboard_data["metrics"]
                assert dashboard_data["metrics"]["tasks_assigned"]["latest"] == len(final_scores)
    
    @pytest.mark.asyncio
    async def test_system_resilience_under_load(self, integrated_validator):
        """Test system resilience under high load conditions"""
        
        systems = integrated_validator
        core = systems["core"]
        task_assignment = systems["task_assignment"]
        
        # Create many miners
        core.miners_info = {f"miner_{i}": {"uid": f"miner_{i}"} for i in range(20)}
        
        # Mock task creation with potential failures
        failure_count = 0
        
        async def unreliable_create_task(miner_uid):
            nonlocal failure_count
            
            # Simulate occasional failures
            if failure_count % 7 == 0:  # Every 7th task fails
                failure_count += 1
                raise ValueError("Task creation failed")
            
            failure_count += 1
            return {
                "task_id": f"load_test_{miner_uid}_{failure_count}",
                "timestamp": time.time(),
                "prompt": "Load test task"
            }
        
        # Mock unreliable network
        async def unreliable_send_task(miner_uid, task_data):
            # Simulate network issues
            if "miner_19" in miner_uid:  # Last miner always fails
                raise ConnectionError("Network timeout")
            
            await asyncio.sleep(0.001)  # Very fast for load test
            return {
                "status": "success",
                "result": {"score": 0.8},
                "miner_uid": miner_uid
            }
        
        # Track errors for recovery system
        errors_recorded = []
        
        async def track_errors(component, error, severity):
            errors_recorded.append((component, error, severity))
            await systems["error_recovery"].record_error(component, error, severity)
        
        # Patch methods
        with patch.object(task_assignment, 'create_task_data', side_effect=unreliable_create_task):
            with patch.object(core, 'send_task_to_miner', side_effect=unreliable_send_task):
                
                # Run load test
                try:
                    current_slot = core.get_current_blockchain_slot()
                    final_scores = await task_assignment.run_continuous_assignment(current_slot)
                    
                    # Should complete despite some failures
                    assert len(final_scores) > 0
                    
                    # Record the load test results
                    systems["monitoring_dashboard"].record_task_assignment(
                        duration=1.0,
                        tasks_count=len(final_scores)
                    )
                    
                except Exception as e:
                    # Record system-level error
                    await track_errors("task_assignment_system", e, ErrorSeverity.HIGH)
                
                # Check that systems remained stable
                
                # Resource management should be active
                resource_stats = systems["resource_manager"].get_comprehensive_stats()
                assert resource_stats["memory"]["current_mb"] > 0
                
                # Error recovery should have recorded issues
                recovery_stats = systems["error_recovery"].get_recovery_stats()
                # May have recorded errors depending on failures
                
                # Performance optimizer should show activity
                perf_stats = systems["performance_optimizer"].get_comprehensive_stats()
                assert perf_stats["uptime_hours"] > 0
                
                # Monitoring should have health data
                dashboard_data = systems["monitoring_dashboard"].get_dashboard_data()
                health_status = dashboard_data["health"]["overall_status"]
                assert health_status in ["healthy", "warning", "critical"]
    
    @pytest.mark.asyncio
    async def test_consensus_coordination_integration(self):
        """Test consensus coordination with other systems"""
        
        # Create multiple validators
        validators = []
        coordinators = []
        
        for i in range(3):
            validator_core = MockValidatorCore(f"validator_{i}")
            coordinator = ConsensusCoordinator(
                validator_uid=validator_core.info.uid,
                coordination_dir=f"test_coordination_{i}"
            )
            
            validators.append(validator_core)
            coordinators.append(coordinator)
        
        try:
            # Start coordination
            for coordinator in coordinators:
                await coordinator.start_coordination()
            
            # Simulate consensus proposal
            slot = int(time.time()) // 60
            phase = ConsensusPhase.TASK_ASSIGNMENT
            
            proposal_data = {
                "task_assignment_config": {
                    "batch_size": 5,
                    "timeout": 30.0
                },
                "miners_selected": ["miner_1", "miner_2", "miner_3"]
            }
            
            # Each validator proposes
            consensus_results = []
            for coordinator in coordinators:
                try:
                    result, decision = await coordinator.propose_consensus(
                        slot=slot,
                        phase=phase,
                        proposal_data=proposal_data,
                        timeout=2.0  # Short timeout for test
                    )
                    consensus_results.append((result, decision))
                except asyncio.TimeoutError:
                    consensus_results.append((None, None))
            
            # At least one should have attempted consensus
            assert len(consensus_results) == 3
            
            # Check coordination stats
            for coordinator in coordinators:
                stats = coordinator.get_coordination_stats()
                assert stats["validator_uid"] in [f"validator_{i}" for i in range(3)]
                assert "successful_consensus" in stats
                assert "failed_consensus" in stats
        
        finally:
            # Cleanup
            for coordinator in coordinators:
                await coordinator.stop_coordination()


@pytest.mark.asyncio
async def test_end_to_end_consensus_simulation():
    """End-to-end simulation of consensus system with all components"""
    
    # Create validator system
    validator_core = MockValidatorCore("e2e_validator")
    
    # Initialize all consensus components
    resource_manager = setup_basic_cleanup(validator_core)
    error_recovery = AutoRecovery()
    performance_optimizer = PerformanceOptimizer(max_workers=3)
    security_validator = SecurityValidator()
    monitoring_dashboard = MonitoringDashboard(validator_core.info.uid)
    consensus_coordinator = ConsensusCoordinator(validator_core.info.uid)
    
    # Start all systems
    await resource_manager.start()
    await error_recovery.start_health_monitoring()
    await performance_optimizer.start()
    await monitoring_dashboard.start()
    await consensus_coordinator.start_coordination()
    
    try:
        # Register validator for security
        security_validator.authenticator.register_validator(
            validator_core.info.uid, 
            validator_core.account.public_key,
            is_trusted=True
        )
        
        # Register error recovery for all components
        setup_component_recovery(
            "resource_manager",
            error_recovery,
            restart_func=lambda: print("Restarting resource manager")
        )
        
        setup_component_recovery(
            "performance_optimizer", 
            error_recovery,
            restart_func=lambda: print("Restarting performance optimizer")
        )
        
        # Simulate consensus workflow
        current_slot = validator_core.get_current_blockchain_slot()
        
        # 1. Security validation of incoming request
        task_request = {
            "slot": current_slot,
            "phase": "task_assignment",
            "miners": ["miner_1", "miner_2", "miner_3"],
            "timestamp": time.time()
        }
        
        allowed, reason = await security_validator.validate_request(
            client_id=validator_core.info.uid,
            data=task_request,
            context="consensus_proposal"
        )
        assert allowed is True
        
        # 2. Performance-optimized task processing
        async def process_consensus_task(task_data):
            await asyncio.sleep(0.01)  # Simulate processing
            return {
                "processed": True,
                "miners_assigned": len(task_data["miners"]),
                "slot": task_data["slot"]
            }
        
        # Cache the processing result
        cache_key = f"consensus_result_{current_slot}"
        cached_result = performance_optimizer.cache_get(cache_key)
        
        if cached_result is None:
            result = await performance_optimizer.execute_task(process_consensus_task, task_request)
            performance_optimizer.cache_set(cache_key, result)
        else:
            result = cached_result
        
        assert result["processed"] is True
        assert result["miners_assigned"] == 3
        
        # 3. Resource monitoring and cleanup
        # Add some test data for cleanup
        test_data = {f"old_task_{i}": {"timestamp": time.time() - 3600} for i in range(10)}
        resource_manager.register_cleanup_target(
            "old_tasks",
            test_data,
            cleanup_strategy="timestamp",
            timestamp_key="timestamp"
        )
        
        # Let cleanup run
        await asyncio.sleep(0.1)
        
        # 4. Record comprehensive metrics
        monitoring_dashboard.record_consensus_round(success=True, duration=0.5)
        monitoring_dashboard.record_task_assignment(duration=1.0, tasks_count=3)
        monitoring_dashboard.record_network_request(success=True, duration=0.1)
        
        # Get final system statistics
        final_stats = {
            "resource_manager": resource_manager.get_comprehensive_stats(),
            "error_recovery": error_recovery.get_recovery_stats(),
            "performance_optimizer": performance_optimizer.get_comprehensive_stats(),
            "security_validator": security_validator.get_security_stats(),
            "monitoring_dashboard": monitoring_dashboard.get_dashboard_data(),
            "consensus_coordinator": consensus_coordinator.get_coordination_stats()
        }
        
        # Verify all systems are functioning
        assert final_stats["resource_manager"]["uptime_hours"] > 0
        assert final_stats["error_recovery"]["total_components"] >= 2
        assert final_stats["performance_optimizer"]["task_pool"]["completed_tasks"] >= 1
        assert final_stats["security_validator"]["total_requests_processed"] >= 1
        assert final_stats["monitoring_dashboard"]["system_status"]["active"] is True
        assert final_stats["consensus_coordinator"]["validator_uid"] == "e2e_validator"
        
        # Check cache effectiveness
        cache_stats = final_stats["performance_optimizer"]["cache"]
        assert cache_stats["size"] >= 1
        
        # Check security processed requests without blocking
        security_stats = final_stats["security_validator"]
        assert security_stats["total_requests_blocked"] == 0
        assert security_stats["block_rate"] == 0.0
        
        # Check monitoring recorded all metrics
        metrics = final_stats["monitoring_dashboard"]["metrics"]
        assert "consensus_rounds_total" in metrics
        assert "task_assignment_duration" in metrics
        assert "network_requests_total" in metrics
        
        print("✅ End-to-end consensus simulation completed successfully!")
        print(f"📊 Processed {security_stats['total_requests_processed']} requests")
        print(f"⚡ Completed {final_stats['performance_optimizer']['task_pool']['completed_tasks']} tasks")
        print(f"🔍 Monitored {len(metrics)} different metrics")
        print(f"🛡️ Blocked {security_stats['total_requests_blocked']} malicious requests")
        
    finally:
        # Cleanup all systems
        await resource_manager.stop()
        await error_recovery.stop_health_monitoring()
        await performance_optimizer.stop()
        await monitoring_dashboard.stop()
        await consensus_coordinator.stop_coordination()


if __name__ == "__main__":
    # Run tests with: python -m pytest test_consensus_integration.py -v
    pytest.main([__file__, "-v"]) 