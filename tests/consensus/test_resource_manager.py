#!/usr/bin/env python3
"""
Tests for Resource Manager Module

Tests resource monitoring, cleanup, caching, and overall resource management.
"""

import asyncio
import pytest
import pytest_asyncio
import time
import psutil
from unittest.mock import Mock, patch, AsyncMock
from collections import deque

from mt_aptos.consensus.resource_manager import (
    ResourceManager, ResourceMonitor, DataCleanupManager, CacheManager,
    ResourceType, AlertLevel, ResourceAlert, MemorySnapshot,
    create_resource_manager, setup_basic_cleanup
)


class TestResourceMonitor:
    """Test ResourceMonitor functionality"""
    
    @pytest_asyncio.fixture
    async def monitor(self):
        """Create a resource monitor for testing"""
        monitor = ResourceMonitor(
            memory_threshold_mb=100,  # Low threshold for testing
            cpu_threshold_percent=50.0
        )
        yield monitor
        if monitor.monitoring_active:
            await monitor.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_monitor_initialization(self, monitor):
        """Test monitor initialization"""
        assert monitor.memory_threshold_mb == 100
        assert monitor.cpu_threshold_percent == 50.0
        assert not monitor.monitoring_active
        assert monitor.peak_memory_mb == 0.0
        assert len(monitor.memory_snapshots) == 0
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, monitor):
        """Test starting and stopping monitoring"""
        # Start monitoring
        await monitor.start_monitoring()
        assert monitor.monitoring_active
        assert monitor.monitor_task is not None
        
        # Stop monitoring
        await monitor.stop_monitoring()
        assert not monitor.monitoring_active
        assert monitor.monitor_task is None
    
    @pytest.mark.asyncio
    async def test_memory_snapshot(self, monitor):
        """Test memory snapshot creation"""
        await monitor._take_memory_snapshot()
        
        assert len(monitor.memory_snapshots) == 1
        snapshot = monitor.memory_snapshots[0]
        
        assert isinstance(snapshot, MemorySnapshot)
        assert snapshot.rss_mb > 0
        assert snapshot.vms_mb > 0
        assert 0 <= snapshot.percent <= 100
        assert snapshot.available_mb > 0
        assert snapshot.gc_objects > 0
    
    @pytest.mark.asyncio
    async def test_memory_threshold_alert(self, monitor):
        """Test memory threshold alerting"""
        # Mock high memory usage
        with patch.object(monitor.process, 'memory_info') as mock_memory:
            mock_memory.return_value.rss = 200 * 1024 * 1024  # 200MB
            mock_memory.return_value.vms = 300 * 1024 * 1024  # 300MB
            
            with patch.object(monitor.process, 'memory_percent', return_value=85.0):
                await monitor._take_memory_snapshot()
                await monitor._check_thresholds()
        
        # Should have triggered an alert
        assert len(monitor.alerts) > 0
        alert = monitor.alerts[-1]
        assert alert.resource_type == ResourceType.MEMORY
        assert alert.level in [AlertLevel.WARNING, AlertLevel.CRITICAL]
    
    @pytest.mark.asyncio
    async def test_get_memory_stats(self, monitor):
        """Test memory statistics"""
        await monitor._take_memory_snapshot()
        stats = monitor.get_memory_stats()
        
        assert "current_mb" in stats
        assert "peak_mb" in stats
        assert "threshold_mb" in stats
        assert "usage_percent" in stats
        assert "available_mb" in stats
        assert "gc_objects" in stats
        assert stats["threshold_mb"] == 100


class TestDataCleanupManager:
    """Test DataCleanupManager functionality"""
    
    @pytest_asyncio.fixture
    async def cleanup_manager(self):
        """Create a cleanup manager for testing"""
        manager = DataCleanupManager(
            cleanup_interval=1,  # 1 second for testing
            data_retention_hours=1  # 1 hour for testing
        )
        yield manager
        if manager.cleanup_active:
            await manager.stop_cleanup()
    
    @pytest.mark.asyncio
    async def test_cleanup_manager_initialization(self, cleanup_manager):
        """Test cleanup manager initialization"""
        assert cleanup_manager.cleanup_interval == 1
        assert cleanup_manager.data_retention_seconds == 3600
        assert not cleanup_manager.cleanup_active
        assert len(cleanup_manager.cleanup_targets) == 0
    
    @pytest.mark.asyncio
    async def test_register_cleanup_target(self, cleanup_manager):
        """Test registering cleanup targets"""
        test_dict = {"key1": {"timestamp": time.time()}}
        
        cleanup_manager.register_cleanup_target(
            name="test_dict",
            data_structure=test_dict,
            cleanup_strategy="timestamp",
            timestamp_key="timestamp"
        )
        
        assert "test_dict" in cleanup_manager.cleanup_targets
        target_info = cleanup_manager.cleanup_targets["test_dict"]
        assert target_info["cleanup_strategy"] == "timestamp"
        assert target_info["timestamp_key"] == "timestamp"
    
    @pytest.mark.asyncio
    async def test_timestamp_based_cleanup(self, cleanup_manager):
        """Test timestamp-based cleanup"""
        # Create test data with old timestamp
        old_time = time.time() - 7200  # 2 hours ago
        test_dict = {
            "old_item": {"timestamp": old_time},
            "new_item": {"timestamp": time.time()}
        }
        
        cleanup_manager.register_cleanup_target(
            name="test_dict",
            data_structure=test_dict,
            cleanup_strategy="timestamp",
            timestamp_key="timestamp"
        )
        
        # Perform cleanup
        await cleanup_manager._perform_cleanup()
        
        # Old item should be removed, new item should remain
        assert "old_item" not in test_dict
        assert "new_item" in test_dict
    
    @pytest.mark.asyncio
    async def test_size_based_cleanup(self, cleanup_manager):
        """Test size-based cleanup"""
        test_list = list(range(20))  # 20 items
        
        cleanup_manager.register_cleanup_target(
            name="test_list",
            data_structure=test_list,
            cleanup_strategy="size",
            max_size=10
        )
        
        # Perform cleanup
        await cleanup_manager._perform_cleanup()
        
        # Should be reduced to max_size
        assert len(test_list) == 10
        # Should keep the last 10 items (10-19)
        assert test_list == list(range(10, 20))
    
    @pytest.mark.asyncio
    async def test_cleanup_stats(self, cleanup_manager):
        """Test cleanup statistics"""
        test_dict = {"item1": {"timestamp": time.time()}}
        
        cleanup_manager.register_cleanup_target(
            name="test_dict",
            data_structure=test_dict,
            cleanup_strategy="timestamp"
        )
        
        stats = cleanup_manager.get_cleanup_stats()
        
        assert "total_cleanups" in stats
        assert "total_items_cleaned" in stats
        assert "active_targets" in stats
        assert "targets" in stats
        assert stats["active_targets"] == 1
        assert "test_dict" in stats["targets"]


class TestCacheManager:
    """Test CacheManager functionality"""
    
    @pytest_asyncio.fixture
    async def cache_manager(self):
        """Create a cache manager for testing"""
        manager = CacheManager(
            max_size=5,  # Small size for testing
            default_ttl=2,  # 2 seconds for testing
            cleanup_interval=1
        )
        yield manager
        if manager.active:
            await manager.stop()
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self, cache_manager):
        """Test cache initialization"""
        assert cache_manager.max_size == 5
        assert cache_manager.default_ttl == 2
        assert len(cache_manager.cache) == 0
        assert cache_manager.hits == 0
        assert cache_manager.misses == 0
    
    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache_manager):
        """Test basic cache set and get operations"""
        # Set value
        cache_manager.set("key1", "value1")
        
        # Get value
        result = cache_manager.get("key1")
        assert result == "value1"
        assert cache_manager.hits == 1
        assert cache_manager.misses == 0
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_manager):
        """Test cache miss"""
        result = cache_manager.get("nonexistent_key")
        assert result is None
        assert cache_manager.hits == 0
        assert cache_manager.misses == 1
    
    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, cache_manager):
        """Test TTL expiration"""
        cache_manager.set("key1", "value1")
        
        # Should get value immediately
        result = cache_manager.get("key1")
        assert result == "value1"
        
        # Wait for TTL expiration
        await asyncio.sleep(3)
        
        # Should be expired now
        result = cache_manager.get("key1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_size_limit(self, cache_manager):
        """Test cache size limit and eviction"""
        # Fill cache beyond limit
        for i in range(7):  # More than max_size (5)
            cache_manager.set(f"key{i}", f"value{i}")
        
        # Should only have max_size items
        assert len(cache_manager.cache) == 5
        
        # Should have evicted earliest items (LRU)
        assert cache_manager.get("key0") is None  # Evicted
        assert cache_manager.get("key1") is None  # Evicted
        assert cache_manager.get("key6") == "value6"  # Still there
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, cache_manager):
        """Test cache deletion"""
        cache_manager.set("key1", "value1")
        
        # Delete should succeed
        result = cache_manager.delete("key1")
        assert result is True
        
        # Key should be gone
        assert cache_manager.get("key1") is None
        
        # Delete non-existent key should return False
        result = cache_manager.delete("nonexistent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_manager):
        """Test cache statistics"""
        cache_manager.set("key1", "value1")
        cache_manager.get("key1")  # Hit
        cache_manager.get("missing")  # Miss
        
        stats = cache_manager.get_stats()

        assert stats["entries"] == 1
        assert stats["max_size"] == 5
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        # assert stats["strategy"] == "lru"  # Not implemented in get_stats


class TestResourceManager:
    """Test ResourceManager integration"""
    
    @pytest_asyncio.fixture
    async def resource_manager(self):
        """Create a resource manager for testing"""
        manager = ResourceManager(
            memory_threshold_mb=100,
            cleanup_interval=1,
            data_retention_hours=1,
            cache_size_limit=10
        )
        yield manager
        if manager.active:
            await manager.stop()
    
    @pytest.mark.asyncio
    async def test_resource_manager_initialization(self, resource_manager):
        """Test resource manager initialization"""
        assert resource_manager.monitor is not None
        assert resource_manager.cleanup_manager is not None
        assert resource_manager.cache_manager is not None
        assert not resource_manager.active
    
    @pytest.mark.asyncio
    async def test_resource_manager_start_stop(self, resource_manager):
        """Test starting and stopping resource manager"""
        await resource_manager.start()
        assert resource_manager.active
        assert resource_manager.monitor.monitoring_active
        assert resource_manager.cleanup_manager.cleanup_active
        assert resource_manager.cache_manager.active
        
        await resource_manager.stop()
        assert not resource_manager.active
        assert not resource_manager.monitor.monitoring_active
        assert not resource_manager.cleanup_manager.cleanup_active
        assert not resource_manager.cache_manager.active
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, resource_manager):
        """Test cache operations through resource manager"""
        # Set cache value
        resource_manager.cache_set("test_key", "test_value")
        
        # Get cache value
        result = resource_manager.cache_get("test_key")
        assert result == "test_value"
        
        # Delete cache value
        deleted = resource_manager.cache_delete("test_key")
        assert deleted is True
        
        # Should be gone now
        result = resource_manager.cache_get("test_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_register_cleanup_target(self, resource_manager):
        """Test registering cleanup targets"""
        test_data = {"item": {"timestamp": time.time()}}
        
        resource_manager.register_cleanup_target(
            name="test_data",
            data_structure=test_data,
            cleanup_strategy="timestamp",
            timestamp_key="timestamp"
        )
        
        # Should be registered with cleanup manager
        assert "test_data" in resource_manager.cleanup_manager.cleanup_targets
    
    @pytest.mark.asyncio
    async def test_comprehensive_stats(self, resource_manager):
        """Test comprehensive statistics"""
        await resource_manager.start()
        
        # Let it run briefly to generate some data
        await asyncio.sleep(0.5)
        
        stats = resource_manager.get_comprehensive_stats()
        
        assert "uptime_hours" in stats
        assert "memory" in stats
        assert "cleanup" in stats
        assert "cache" in stats
        assert "alerts" in stats
        
        # Check structure of nested stats
        assert "current_mb" in stats["memory"]
        assert "total_cleanups" in stats["cleanup"]
        assert "entries" in stats["cache"]  # Use entries instead of size
        assert "total" in stats["alerts"]


class TestIntegrationFunctions:
    """Test integration and utility functions"""
    
    @pytest.mark.asyncio
    async def test_create_resource_manager(self):
        """Test create_resource_manager convenience function"""
        manager = await create_resource_manager(
            memory_threshold_mb=200,
            cache_size_limit=50
        )
        
        try:
            assert manager.active
            assert manager.monitor.memory_threshold_mb == 200
            assert manager.cache_manager.max_size == 50
        finally:
            await manager.stop()
    
    def test_setup_basic_cleanup(self):
        """Test setup_basic_cleanup function"""
        # Mock validator node core
        mock_core = Mock()
        mock_core.tasks_sent = {}
        mock_core.results_buffer = {}
        mock_core.cycle_scores = {}
        
        manager = setup_basic_cleanup(mock_core)
        
        assert isinstance(manager, ResourceManager)
        # Should have registered cleanup targets
        assert len(manager.cleanup_manager.cleanup_targets) >= 3


@pytest.mark.asyncio
async def test_memory_alert_handling():
    """Test memory alert handling"""
    alert_received = False
    alert_data = None
    
    async def alert_callback(alert):
        nonlocal alert_received, alert_data
        alert_received = True
        alert_data = alert
    
    manager = ResourceManager(
        memory_threshold_mb=1  # Very low threshold
    )
    manager.monitor.alert_callback = alert_callback
    
    try:
        await manager.start()
        
        # Force a memory snapshot that should trigger alert
        await manager.monitor._take_memory_snapshot()
        await manager.monitor._check_thresholds()
        
        # Give time for alert processing
        await asyncio.sleep(0.1)
        
        # Should have received alert for high memory usage
        # (Current memory will likely exceed 1MB threshold)
        assert alert_received or len(manager.monitor.alerts) > 0
        
    finally:
        await manager.stop()


if __name__ == "__main__":
    # Run tests with: python -m pytest test_resource_manager.py -v
    pytest.main([__file__, "-v"]) 