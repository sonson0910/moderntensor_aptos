#!/usr/bin/env python3
"""
Pytest configuration for ModernTensor consensus tests.

Provides shared fixtures, configuration, and test utilities.
"""

import asyncio
import logging
import os
import sys
import pytest
import time
from pathlib import Path
from unittest.mock import Mock

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Disable noisy loggers during tests
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_time():
    """Mock time.time() for consistent testing."""
    return time.time()


@pytest.fixture
def mock_validator_core():
    """Create a mock validator core for testing."""
    mock_core = Mock()
    mock_core.info.uid = "test_validator"
    mock_core.account.public_key = "test_public_key"
    mock_core.aptos_client = Mock()
    mock_core.contract_address = "0x123"
    
    # Task management
    mock_core.tasks_sent = {}
    mock_core.results_buffer = {}
    mock_core.cycle_scores = {}
    mock_core.miner_is_busy = set()
    
    # Network
    mock_core.http_client = Mock()
    
    # Configuration
    mock_core.settings = Mock()
    mock_core.settings.CONTINUOUS_BATCH_SIZE = 3
    mock_core.settings.CONTINUOUS_TIMEOUT_SECONDS = 10.0
    mock_core.settings.CONTINUOUS_SCORE_AGGREGATION = "average"
    
    # Slot configuration
    mock_core.slot_config = Mock()
    mock_core.slot_config.task_assignment_minutes = 2.0
    
    # Mock methods
    mock_core.get_current_blockchain_slot = Mock(return_value=123)
    
    return mock_core


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "task_id": "test_task_123",
        "timestamp": time.time(),
        "prompt": "Generate a test image",
        "guidance_scale": 7.5,
        "resolution": "512x512"
    }


@pytest.fixture
def sample_miner_result():
    """Sample miner result data for testing."""
    return {
        "miner_uid": "test_miner_1",
        "result": {
            "image_url": "http://test.com/result.jpg",
            "generation_time": 2.5,
            "model_version": "test-model-v1"
        },
        "status": "success"
    }


@pytest.fixture
def sample_miners_info():
    """Sample miners information for testing."""
    return {
        f"miner_{i}": {
            "uid": f"miner_{i}",
            "endpoint": f"http://miner{i}.test",
            "stake": 1000 + i * 100,
            "reputation": 0.8 + (i * 0.05)
        }
        for i in range(5)
    }


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create temporary directory for test files."""
    test_dir = tmp_path / "consensus_test"
    test_dir.mkdir()
    return test_dir


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security-related"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance-related"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add automatic markers."""
    for item in items:
        # Add markers based on test file names
        if "integration" in item.fspath.basename:
            item.add_marker(pytest.mark.integration)
        elif "security" in item.fspath.basename:
            item.add_marker(pytest.mark.security)
        elif "performance" in item.fspath.basename:
            item.add_marker(pytest.mark.performance)
        else:
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests
        if "test_end_to_end" in item.name or "test_comprehensive" in item.name:
            item.add_marker(pytest.mark.slow)


# Custom test utilities
class TestTimer:
    """Context manager for timing test execution."""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        print(f"⏱️  {self.test_name} completed in {duration:.2f}s")
    
    @property
    def duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


@pytest.fixture
def test_timer():
    """Fixture for timing test execution."""
    def _timer(test_name: str):
        return TestTimer(test_name)
    return _timer


# Async test helpers
@pytest.fixture
async def async_cleanup():
    """Fixture for async cleanup operations."""
    cleanup_tasks = []
    
    def add_cleanup(coro):
        cleanup_tasks.append(coro)
    
    yield add_cleanup
    
    # Run cleanup tasks
    for cleanup_task in cleanup_tasks:
        try:
            await cleanup_task
        except Exception as e:
            logging.warning(f"Cleanup task failed: {e}")


# Mock external dependencies
@pytest.fixture
def mock_psutil():
    """Mock psutil for system monitoring tests."""
    import unittest.mock
    
    with unittest.mock.patch('psutil.Process') as mock_process:
        # Configure mock process
        mock_process.return_value.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
        mock_process.return_value.memory_info.return_value.vms = 200 * 1024 * 1024  # 200MB
        mock_process.return_value.memory_percent.return_value = 5.0
        mock_process.return_value.cpu_percent.return_value = 10.0
        
        with unittest.mock.patch('psutil.virtual_memory') as mock_virtual_memory:
            mock_virtual_memory.return_value.available = 8 * 1024 * 1024 * 1024  # 8GB
            mock_virtual_memory.return_value.percent = 20.0
            
            with unittest.mock.patch('psutil.disk_usage') as mock_disk_usage:
                mock_disk_usage.return_value.total = 100 * 1024 * 1024 * 1024  # 100GB
                mock_disk_usage.return_value.used = 50 * 1024 * 1024 * 1024   # 50GB
                mock_disk_usage.return_value.free = 50 * 1024 * 1024 * 1024   # 50GB
                
                yield {
                    'process': mock_process,
                    'virtual_memory': mock_virtual_memory,
                    'disk_usage': mock_disk_usage
                }


# Test data generators
def generate_test_metrics(count: int = 10):
    """Generate test metrics data."""
    return [
        {
            "timestamp": time.time() - (count - i) * 60,  # 1 minute intervals
            "value": 50 + (i * 5) + (i % 3),  # Varying values
            "labels": {"component": f"comp_{i % 3}"}
        }
        for i in range(count)
    ]


def generate_test_errors(count: int = 5):
    """Generate test error data."""
    error_types = ["NetworkError", "TimeoutError", "ValidationError", "SystemError"]
    components = ["validator", "miner", "network", "storage"]
    
    return [
        {
            "timestamp": time.time() - (count - i) * 30,  # 30 second intervals
            "component": components[i % len(components)],
            "error_type": error_types[i % len(error_types)],
            "message": f"Test error {i}",
            "severity": "medium" if i % 2 == 0 else "high"
        }
        for i in range(count)
    ]


@pytest.fixture
def test_metrics():
    """Fixture providing test metrics data."""
    return generate_test_metrics()


@pytest.fixture
def test_errors():
    """Fixture providing test error data."""
    return generate_test_errors()


# Environment configuration
@pytest.fixture(autouse=True)
def configure_test_environment():
    """Configure test environment variables."""
    # Set test-specific environment variables
    os.environ['CONSENSUS_TEST_MODE'] = 'true'
    os.environ['LOG_LEVEL'] = 'INFO'
    
    # Disable external network calls during tests
    os.environ['DISABLE_EXTERNAL_CALLS'] = 'true'
    
    yield
    
    # Cleanup environment
    test_env_vars = [
        'CONSENSUS_TEST_MODE',
        'LOG_LEVEL', 
        'DISABLE_EXTERNAL_CALLS'
    ]
    
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]


# Performance benchmarking
@pytest.fixture
def benchmark_timer():
    """Fixture for benchmarking test performance."""
    times = {}
    
    def time_operation(name: str):
        def decorator(func):
            start_time = time.time()
            try:
                result = func()
                return result
            finally:
                end_time = time.time()
                times[name] = end_time - start_time
        return decorator
    
    def get_times():
        return times.copy()
    
    time_operation.get_times = get_times
    return time_operation


# Test assertion helpers
def assert_metrics_valid(metrics: dict):
    """Assert that metrics dictionary has valid structure."""
    assert isinstance(metrics, dict)
    assert len(metrics) > 0
    
    for metric_name, metric_data in metrics.items():
        assert isinstance(metric_name, str)
        assert isinstance(metric_data, dict)
        assert "count" in metric_data
        assert isinstance(metric_data["count"], int)
        assert metric_data["count"] >= 0


def assert_health_status_valid(health_status: dict):
    """Assert that health status has valid structure."""
    assert isinstance(health_status, dict)
    assert "overall_status" in health_status
    assert health_status["overall_status"] in ["healthy", "warning", "critical", "unknown"]
    assert "health_checks" in health_status
    assert isinstance(health_status["health_checks"], dict)


def assert_performance_stats_valid(perf_stats: dict):
    """Assert that performance stats have valid structure."""
    assert isinstance(perf_stats, dict)
    assert "uptime_hours" in perf_stats
    assert isinstance(perf_stats["uptime_hours"], (int, float))
    assert perf_stats["uptime_hours"] >= 0


# Add assertion helpers to pytest namespace
@pytest.fixture
def assert_helpers():
    """Provide assertion helper functions."""
    return {
        'assert_metrics_valid': assert_metrics_valid,
        'assert_health_status_valid': assert_health_status_valid,
        'assert_performance_stats_valid': assert_performance_stats_valid
    }
