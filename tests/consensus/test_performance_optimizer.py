#!/usr/bin/env python3
"""
Tests for Performance Optimizer Module

Tests task pool management, intelligent batching, caching, and performance monitoring.
"""

import asyncio
import pytest
import pytest_asyncio
import time
import statistics
from unittest.mock import Mock, patch, AsyncMock
from collections import deque

from mt_aptos.consensus.performance_optimizer import (
    PerformanceOptimizer, AsyncTaskPool, IntelligentBatcher, PerformanceCache,
    PerformanceMonitor, BatchConfig, CacheConfig, PerformanceMetric,
    OptimizationStrategy, performance_optimize, create_performance_optimizer
)


class TestAsyncTaskPool:
    """Test AsyncTaskPool functionality"""
    
    @pytest_asyncio.fixture
    def task_pool(self):
        """Create a task pool for testing"""
        return AsyncTaskPool(max_workers=3)
    
    def test_task_pool_initialization(self, task_pool):
        """Test task pool initialization"""
        assert task_pool.max_workers == 3
        assert task_pool.completed_tasks == 0
        assert task_pool.failed_tasks == 0
        assert len(task_pool.active_tasks) == 0
        assert len(task_pool.task_durations) == 0
    
    @pytest.mark.asyncio
    async def test_submit_async_task(self, task_pool):
        """Test submitting async tasks"""
        async def async_task(value):
            await asyncio.sleep(0.01)
            return value * 2
        
        result = await task_pool.submit_task(async_task, 5)
        
        assert result == 10
        assert task_pool.completed_tasks == 1
        assert task_pool.failed_tasks == 0
        assert len(task_pool.task_durations) == 1
    
    @pytest.mark.asyncio
    async def test_submit_sync_task(self, task_pool):
        """Test submitting sync tasks"""
        def sync_task(value):
            return value * 3
        
        result = await task_pool.submit_task(sync_task, 4)
        
        assert result == 12
        assert task_pool.completed_tasks == 1
        assert task_pool.failed_tasks == 0
    
    @pytest.mark.asyncio
    async def test_submit_task_with_timeout(self, task_pool):
        """Test task submission with timeout"""
        async def slow_task():
            await asyncio.sleep(1)
            return "completed"
        
        with pytest.raises(asyncio.TimeoutError):
            await task_pool.submit_task(slow_task, timeout=0.1)
        
        assert task_pool.failed_tasks == 1
    
    @pytest.mark.asyncio
    async def test_submit_task_with_error(self, task_pool):
        """Test task submission that raises error"""
        async def failing_task():
            raise ValueError("Task failed")
        
        with pytest.raises(ValueError):
            await task_pool.submit_task(failing_task)
        
        assert task_pool.failed_tasks == 1
        assert task_pool.completed_tasks == 0
    
    @pytest.mark.asyncio
    async def test_submit_batch(self, task_pool):
        """Test batch task submission"""
        def multiply_task(value):
            return value * 2
        
        # Create batch of tasks
        tasks = [
            (multiply_task, (i,), {}) for i in range(5)
        ]
        
        results = await task_pool.submit_batch(tasks)
        
        assert len(results) == 5
        assert results == [0, 2, 4, 6, 8]  # Each value multiplied by 2
        assert task_pool.completed_tasks == 5
    
    @pytest.mark.asyncio
    async def test_concurrent_tasks(self, task_pool):
        """Test concurrent task execution"""
        async def concurrent_task(task_id, delay):
            await asyncio.sleep(delay)
            return f"task_{task_id}"
        
        # Submit multiple tasks concurrently
        tasks = [
            task_pool.submit_task(concurrent_task, i, 0.01) 
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(result.startswith("task_") for result in results)
        assert task_pool.completed_tasks == 5
    
    def test_get_stats(self, task_pool):
        """Test task pool statistics"""
        stats = task_pool.get_stats()
        
        assert "max_workers" in stats
        assert "active_tasks" in stats
        assert "completed_tasks" in stats
        assert "failed_tasks" in stats
        assert "success_rate" in stats
        assert "average_duration" in stats
        
        assert stats["max_workers"] == 3
        assert stats["completed_tasks"] == 0
        assert stats["failed_tasks"] == 0


class TestIntelligentBatcher:
    """Test IntelligentBatcher functionality"""
    
    @pytest_asyncio.fixture
    def batch_config(self):
        """Create batch config for testing"""
        return BatchConfig(
            batch_size=3,
            max_wait_time=0.1,  # 100ms for testing
            min_batch_size=1,
            max_batch_size=10,
            adaptive=True
        )
    
    @pytest_asyncio.fixture
    async def batcher(self, batch_config):
        """Create intelligent batcher for testing"""
        batcher = IntelligentBatcher(batch_config)
        yield batcher
        if batcher.running:
            await batcher.stop()
    
    def test_batcher_initialization(self, batcher, batch_config):
        """Test batcher initialization"""
        assert batcher.config == batch_config
        assert batcher.optimal_batch_size == batch_config.batch_size
        assert batcher.batches_processed == 0
        assert batcher.items_processed == 0
        assert not batcher.running
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, batcher):
        """Test basic batch processing"""
        processed_batches = []
        
        def process_batch(items):
            processed_batches.append(items)
            return [item * 2 for item in items]
        
        await batcher.start(process_batch)
        
        # Add items to be batched
        tasks = [batcher.add_item(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        await batcher.stop()
        
        # Check results
        assert len(results) == 5
        assert all(isinstance(r, int) for r in results)
        
        # Check that batching occurred
        assert len(processed_batches) > 0
        assert batcher.batches_processed > 0
        assert batcher.items_processed == 5
    
    @pytest.mark.asyncio
    async def test_batch_size_optimization(self, batcher):
        """Test adaptive batch size optimization"""
        process_times = []
        
        def slow_process_batch(items):
            # Simulate processing time proportional to batch size
            processing_time = len(items) * 0.01
            time.sleep(processing_time)
            process_times.append(processing_time)
            return [item for item in items]
        
        await batcher.start(slow_process_batch)
        
        # Process multiple batches to trigger optimization
        for round_num in range(3):
            tasks = [batcher.add_item(i + round_num * 10) for i in range(8)]
            await asyncio.gather(*tasks)
            await asyncio.sleep(0.2)  # Allow optimization to occur
        
        await batcher.stop()
        
        # Should have processed multiple batches
        assert batcher.batches_processed >= 3
        assert len(batcher.processing_times) > 0
    
    @pytest.mark.asyncio
    async def test_batch_timeout(self, batcher):
        """Test batch timeout mechanism"""
        processed_batches = []
        
        def process_batch(items):
            processed_batches.append(items)
            return items
        
        await batcher.start(process_batch)
        
        # Add single item and wait for timeout
        result = await batcher.add_item("timeout_test")
        
        await batcher.stop()
        
        assert result == "timeout_test"
        assert len(processed_batches) == 1
        assert processed_batches[0] == ["timeout_test"]
    
    def test_get_stats(self, batcher):
        """Test batcher statistics"""
        stats = batcher.get_stats()
        
        assert "optimal_batch_size" in stats
        assert "configured_batch_size" in stats
        assert "batches_processed" in stats
        assert "items_processed" in stats
        assert "throughput_items_per_second" in stats
        assert "queue_size" in stats
        
        assert stats["optimal_batch_size"] == batcher.config.batch_size
        assert stats["batches_processed"] == 0
        assert stats["items_processed"] == 0


class TestPerformanceCache:
    """Test PerformanceCache functionality"""
    
    @pytest_asyncio.fixture
    def cache_config(self):
        """Create cache config for testing"""
        return CacheConfig(
            max_size=5,
            ttl=0.5,  # 500ms for testing
            strategy="lru",
            compression=False
        )
    
    @pytest_asyncio.fixture
    async def cache(self, cache_config):
        """Create performance cache for testing"""
        cache = PerformanceCache(cache_config)
        yield cache
        if cache.running:
            await cache.stop()
    
    def test_cache_initialization(self, cache, cache_config):
        """Test cache initialization"""
        assert cache.config == cache_config
        assert len(cache.cache) == 0
        assert cache.hits == 0
        assert cache.misses == 0
        assert not cache.running
    
    def test_basic_cache_operations(self, cache):
        """Test basic cache set/get operations"""
        # Set value
        cache.set("key1", "value1")
        
        # Get value (hit)
        result = cache.get("key1")
        assert result == "value1"
        assert cache.hits == 1
        assert cache.misses == 0
        
        # Get non-existent value (miss)
        result = cache.get("key2")
        assert result is None
        assert cache.hits == 1
        assert cache.misses == 1
    
    def test_cache_size_limit(self, cache):
        """Test cache size limiting and LRU eviction"""
        # Fill cache beyond limit
        for i in range(8):  # More than max_size (5)
            cache.set(f"key{i}", f"value{i}")
        
        # Should only have max_size items
        assert len(cache.cache) == 5
        
        # Oldest items should be evicted
        assert cache.get("key0") is None
        assert cache.get("key1") is None
        assert cache.get("key7") == "value7"  # Latest should remain
    
    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, cache):
        """Test TTL-based cache expiration"""
        cache.set("expiring_key", "expiring_value")
        
        # Should get value immediately
        result = cache.get("expiring_key")
        assert result == "expiring_value"
        
        # Wait for TTL expiration
        await asyncio.sleep(0.6)
        
        # Should be expired now
        result = cache.get("expiring_key")
        assert result is None
    
    def test_cache_delete(self, cache):
        """Test cache deletion"""
        cache.set("delete_key", "delete_value")
        
        # Should exist
        assert cache.get("delete_key") == "delete_value"
        
        # Delete should succeed
        result = cache.delete("delete_key")
        assert result is True
        
        # Should be gone
        assert cache.get("delete_key") is None
        
        # Delete non-existent should return False
        result = cache.delete("non_existent")
        assert result is False
    
    def test_cache_clear(self, cache):
        """Test cache clearing"""
        # Add some items
        for i in range(3):
            cache.set(f"key{i}", f"value{i}")
        
        assert len(cache.cache) == 3
        
        # Clear cache
        cache.clear()
        
        assert len(cache.cache) == 0
        assert len(cache.access_times) == 0
    
    @pytest.mark.asyncio
    async def test_cache_cleanup_loop(self, cache):
        """Test automatic cache cleanup"""
        await cache.start()
        
        # Add item that will expire
        cache.set("cleanup_test", "cleanup_value")
        
        # Wait for cleanup to run
        await asyncio.sleep(0.7)
        
        # Item should be cleaned up
        assert cache.get("cleanup_test") is None
        
        await cache.stop()
    
    def test_get_stats(self, cache):
        """Test cache statistics"""
        cache.set("stats_key", "stats_value")
        cache.get("stats_key")  # Hit
        cache.get("missing_key")  # Miss
        
        stats = cache.get_stats()
        
        assert "size" in stats
        assert "max_size" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert "evictions" in stats
        assert "strategy" in stats
        
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestPerformanceMonitor:
    """Test PerformanceMonitor functionality"""
    
    @pytest_asyncio.fixture
    async def monitor(self):
        """Create performance monitor for testing"""
        monitor = PerformanceMonitor(window_seconds=60)
        yield monitor
        if monitor.running:
            await monitor.stop_monitoring()
    
    def test_monitor_initialization(self, monitor):
        """Test monitor initialization"""
        assert monitor.window_seconds == 60
        assert len(monitor.samples) == 0
        assert PerformanceMetric.LATENCY in monitor.thresholds
        assert not monitor.running
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, monitor):
        """Test starting and stopping monitoring"""
        await monitor.start_monitoring()
        
        assert monitor.running
        assert monitor.monitor_task is not None
        
        await monitor.stop_monitoring()
        
        assert not monitor.running
        assert monitor.monitor_task is None
    
    def test_record_metric(self, monitor):
        """Test recording performance metrics"""
        monitor.record_metric(PerformanceMetric.LATENCY, 0.5)
        monitor.record_metric(PerformanceMetric.CPU_USAGE, 75.0)
        
        assert len(monitor.samples[PerformanceMetric.LATENCY]) == 1
        assert len(monitor.samples[PerformanceMetric.CPU_USAGE]) == 1
        
        latency_sample = monitor.samples[PerformanceMetric.LATENCY][0]
        assert latency_sample.value == 0.5
        assert latency_sample.metric == PerformanceMetric.LATENCY
    
    def test_threshold_violation(self, monitor):
        """Test performance threshold violations"""
        # Should not trigger threshold (below limit)
        monitor.record_metric(PerformanceMetric.CPU_USAGE, 50.0)
        
        # Should trigger threshold (above limit)
        with patch('mt_aptos.consensus.performance_optimizer.logger') as mock_logger:
            monitor.record_metric(PerformanceMetric.CPU_USAGE, 90.0)
            mock_logger.warning.assert_called_once()
    
    def test_get_metrics_summary(self, monitor):
        """Test metrics summary generation"""
        # Record some metrics
        values = [10, 20, 30, 40, 50]
        for value in values:
            monitor.record_metric(PerformanceMetric.LATENCY, value)
        
        summary = monitor.get_metrics_summary()
        
        assert "latency" in summary
        latency_summary = summary["latency"]
        
        assert latency_summary["count"] == 5
        assert latency_summary["average"] == 30.0
        assert latency_summary["min"] == 10
        assert latency_summary["max"] == 50
        assert latency_summary["median"] == 30.0


class TestPerformanceOptimizer:
    """Test PerformanceOptimizer integration"""
    
    @pytest_asyncio.fixture
    async def optimizer(self):
        """Create performance optimizer for testing"""
        optimizer = PerformanceOptimizer(
            max_workers=2,
            batch_config=BatchConfig(batch_size=2, max_wait_time=0.1),
            cache_config=CacheConfig(max_size=10, ttl=1.0)
        )
        yield optimizer
        if optimizer.active:
            await optimizer.stop()
    
    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization"""
        assert optimizer.task_pool is not None
        assert optimizer.batcher is not None
        assert optimizer.cache is not None
        assert optimizer.monitor is not None
        assert not optimizer.active
    
    @pytest.mark.asyncio
    async def test_start_stop_optimizer(self, optimizer):
        """Test starting and stopping optimizer"""
        await optimizer.start()
        
        assert optimizer.active
        assert optimizer.cache.running
        assert optimizer.monitor.running
        
        await optimizer.stop()
        
        assert not optimizer.active
        assert not optimizer.cache.running
        assert not optimizer.monitor.running
    
    @pytest.mark.asyncio
    async def test_execute_task(self, optimizer):
        """Test task execution through optimizer"""
        async def test_task(value):
            return value * 2
        
        result = await optimizer.execute_task(test_task, 5)
        
        assert result == 10
        assert optimizer.task_pool.completed_tasks == 1
    
    @pytest.mark.asyncio
    async def test_execute_batch(self, optimizer):
        """Test batch execution through optimizer"""
        def multiply_task(value):
            return value * 3
        
        tasks = [
            (multiply_task, (i,), {}) for i in range(4)
        ]
        
        results = await optimizer.execute_batch(tasks)
        
        assert len(results) == 4
        assert results == [0, 3, 6, 9]
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, optimizer):
        """Test intelligent batch processing"""
        processed_items = []
        
        def batch_processor(items):
            processed_items.extend(items)
            return [item * 2 for item in items]
        
        await optimizer.start_batch_processing(batch_processor)
        
        # Add items to batch
        tasks = [optimizer.add_to_batch(i) for i in range(3)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        assert all(isinstance(r, int) for r in results)
        assert len(processed_items) == 3
    
    def test_cache_operations(self, optimizer):
        """Test cache operations through optimizer"""
        # Set cache value
        optimizer.cache_set("test_key", "test_value")
        
        # Get cache value
        result = optimizer.cache_get("test_key")
        assert result == "test_value"
        
        # Cache should have recorded hit
        assert optimizer.cache.hits == 1
    
    def test_performance_metrics(self, optimizer):
        """Test performance metrics recording"""
        optimizer.record_performance_metric(
            PerformanceMetric.LATENCY, 
            0.5, 
            {"operation": "test"}
        )
        
        # Should be recorded in monitor
        assert len(optimizer.monitor.samples[PerformanceMetric.LATENCY]) == 1
    
    def test_comprehensive_stats(self, optimizer):
        """Test comprehensive statistics"""
        stats = optimizer.get_comprehensive_stats()
        
        assert "uptime_hours" in stats
        assert "task_pool" in stats
        assert "batching" in stats
        assert "cache" in stats
        assert "performance_metrics" in stats
        
        # Check nested structure
        assert "completed_tasks" in stats["task_pool"]
        assert "batches_processed" in stats["batching"]
        assert "hits" in stats["cache"]


class TestPerformanceOptimizeDecorator:
    """Test performance_optimize decorator"""
    
    @pytest_asyncio.fixture
    async def optimizer(self):
        """Create optimizer for decorator testing"""
        optimizer = await create_performance_optimizer(max_workers=2)
        yield optimizer
        await optimizer.stop()
    
    @pytest.mark.asyncio
    async def test_decorator_with_caching(self, optimizer):
        """Test decorator with caching enabled"""
        call_count = 0
        
        class TestService:
            def __init__(self):
                self.performance_optimizer = optimizer
            
            @performance_optimize(cache_key="test_method")
            async def cached_method(self, value):
                nonlocal call_count
                call_count += 1
                return value * 2
        
        service = TestService()
        
        # First call should execute method
        result1 = await service.cached_method(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = await service.cached_method(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment
        
        # Cache should have recorded hit
        assert optimizer.cache.hits >= 1
    
    @pytest.mark.asyncio
    async def test_decorator_performance_monitoring(self, optimizer):
        """Test decorator performance monitoring"""
        class TestService:
            def __init__(self):
                self.performance_optimizer = optimizer
            
            @performance_optimize()
            async def monitored_method(self, delay):
                await asyncio.sleep(delay)
                return "completed"
        
        service = TestService()
        
        # Execute method
        result = await service.monitored_method(0.01)
        assert result == "completed"
        
        # Should have recorded latency metric
        latency_samples = optimizer.monitor.samples[PerformanceMetric.LATENCY]
        assert len(latency_samples) > 0
    
    @pytest.mark.asyncio
    async def test_decorator_error_handling(self, optimizer):
        """Test decorator error handling and metrics"""
        class TestService:
            def __init__(self):
                self.performance_optimizer = optimizer
            
            @performance_optimize()
            async def failing_method(self):
                raise ValueError("Test error")
        
        service = TestService()
        
        # Method should still raise error
        with pytest.raises(ValueError):
            await service.failing_method()
        
        # Should have recorded error metric
        error_samples = optimizer.monitor.samples[PerformanceMetric.ERROR_RATE]
        assert len(error_samples) > 0


class TestIntegrationFunctions:
    """Test integration and utility functions"""
    
    @pytest.mark.asyncio
    async def test_create_performance_optimizer(self):
        """Test create_performance_optimizer convenience function"""
        optimizer = await create_performance_optimizer(
            max_workers=4,
            batch_config=BatchConfig(batch_size=5),
            cache_config=CacheConfig(max_size=20)
        )
        
        try:
            assert optimizer.active
            assert optimizer.task_pool.max_workers == 4
            assert optimizer.batcher.config.batch_size == 5
            assert optimizer.cache.config.max_size == 20
        finally:
            await optimizer.stop()


@pytest.mark.asyncio
async def test_complex_optimization_scenario():
    """Test complex optimization scenario with multiple components"""
    optimizer = await create_performance_optimizer(
        max_workers=3,
        batch_config=BatchConfig(batch_size=3, adaptive=True),
        cache_config=CacheConfig(max_size=10, ttl=2.0)
    )
    
    try:
        # Set up batch processing
        batch_results = []
        
        def complex_batch_processor(items):
            # Simulate complex processing
            processed = []
            for item in items:
                result = {
                    "original": item,
                    "processed": item * 2,
                    "timestamp": time.time()
                }
                processed.append(result)
            batch_results.extend(processed)
            return processed
        
        await optimizer.start_batch_processing(complex_batch_processor)
        
        # Execute various operations
        
        # 1. Direct task execution
        async def compute_task(x, y):
            await asyncio.sleep(0.01)
            return x + y
        
        task_result = await optimizer.execute_task(compute_task, 3, 4)
        assert task_result == 7
        
        # 2. Batch processing
        batch_tasks = [optimizer.add_to_batch(i) for i in range(6)]
        batch_task_results = await asyncio.gather(*batch_tasks)
        
        assert len(batch_task_results) == 6
        assert len(batch_results) == 6
        
        # 3. Cache operations
        optimizer.cache_set("complex_key", {"data": "complex_value"})
        cached_result = optimizer.cache_get("complex_key")
        assert cached_result["data"] == "complex_value"
        
        # 4. Performance metrics
        optimizer.record_performance_metric(PerformanceMetric.THROUGHPUT, 150.5)
        
        # Check comprehensive stats
        stats = optimizer.get_comprehensive_stats()
        
        assert stats["task_pool"]["completed_tasks"] >= 1
        assert stats["batching"]["items_processed"] == 6
        assert stats["cache"]["hits"] >= 1
        assert len(stats["performance_metrics"]) > 0
        
    finally:
        await optimizer.stop()


if __name__ == "__main__":
    # Run tests with: python -m pytest test_performance_optimizer.py -v
    pytest.main([__file__, "-v"]) 