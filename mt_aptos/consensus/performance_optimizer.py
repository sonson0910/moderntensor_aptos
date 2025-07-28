#!/usr/bin/env python3
"""
Performance Optimization Module

This module provides comprehensive performance optimization with:
- Concurrent processing and task parallelization
- Intelligent batching and load balancing
- Multi-level caching strategies
- Performance monitoring and profiling
- Adaptive optimization based on real-time metrics
- Memory and CPU optimization techniques

Key Features:
- Async task pool management
- Dynamic batch sizing optimization
- Intelligent caching with LRU and TTL
- Performance bottleneck detection
- Auto-tuning of system parameters
- Real-time performance metrics
"""

import asyncio
import logging
import time
import threading
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import concurrent.futures
import psutil
import statistics
import weakref
import functools
import hashlib

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_WORKERS = 10
DEFAULT_BATCH_SIZE = 50
DEFAULT_CACHE_SIZE = 1000
DEFAULT_PERFORMANCE_WINDOW = 300  # 5 minutes
DEFAULT_OPTIMIZATION_INTERVAL = 60  # 1 minute
MAX_CONCURRENT_TASKS = 100


class OptimizationStrategy(Enum):
    """Performance optimization strategies"""
    CONCURRENT = "concurrent"
    BATCHING = "batching"
    CACHING = "caching"
    PREFETCHING = "prefetching"
    COMPRESSION = "compression"
    LAZY_LOADING = "lazy_loading"


class PerformanceMetric(Enum):
    """Performance metrics to track"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    CACHE_HIT_RATE = "cache_hit_rate"
    ERROR_RATE = "error_rate"


@dataclass
class PerformanceSample:
    """Single performance measurement"""
    timestamp: float
    metric: PerformanceMetric
    value: float
    context: Optional[Dict[str, Any]] = None


@dataclass
class BatchConfig:
    """Batch processing configuration"""
    batch_size: int = DEFAULT_BATCH_SIZE
    max_wait_time: float = 1.0  # seconds
    min_batch_size: int = 1
    max_batch_size: int = 1000
    adaptive: bool = True


@dataclass
class CacheConfig:
    """Cache configuration"""
    max_size: int = DEFAULT_CACHE_SIZE
    ttl: float = 3600.0  # 1 hour
    strategy: str = "lru"  # lru, lfu, fifo
    compression: bool = False


class AsyncTaskPool:
    """Manages concurrent task execution with optimizations"""
    
    def __init__(self, max_workers: int = DEFAULT_MAX_WORKERS):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
        
        # Task tracking
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.total_execution_time = 0.0
        
        # Performance monitoring
        self.task_durations: deque = deque(maxlen=1000)
        self.peak_concurrent_tasks = 0
    
    async def submit_task(
        self,
        task_func: Callable,
        *args,
        task_id: Optional[str] = None,
        priority: int = 0,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Any:
        """Submit a task for concurrent execution"""
        task_id = task_id or f"task_{int(time.time() * 1000)}"
        
        async with self.semaphore:
            start_time = time.time()
            
            try:
                # Track active tasks
                current_tasks = len(self.active_tasks)
                self.peak_concurrent_tasks = max(self.peak_concurrent_tasks, current_tasks)
                
                if asyncio.iscoroutinefunction(task_func):
                    # Async function
                    if timeout:
                        result = await asyncio.wait_for(task_func(*args, **kwargs), timeout=timeout)
                    else:
                        result = await task_func(*args, **kwargs)
                else:
                    # Sync function - run in thread pool
                    loop = asyncio.get_event_loop()
                    if timeout:
                        result = await asyncio.wait_for(
                            loop.run_in_executor(self.executor, functools.partial(task_func, *args, **kwargs)),
                            timeout=timeout
                        )
                    else:
                        result = await loop.run_in_executor(
                            self.executor, functools.partial(task_func, *args, **kwargs)
                        )
                
                # Record success
                execution_time = time.time() - start_time
                self.task_durations.append(execution_time)
                self.total_execution_time += execution_time
                self.completed_tasks += 1
                
                return result
                
            except Exception as e:
                self.failed_tasks += 1
                logger.error(f"❌ Task {task_id} failed: {e}")
                raise
            
            finally:
                # Clean up task tracking
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
    
    async def submit_batch(
        self,
        tasks: List[Tuple[Callable, Tuple, Dict]],
        max_concurrent: Optional[int] = None
    ) -> List[Any]:
        """Submit a batch of tasks for concurrent execution"""
        max_concurrent = max_concurrent or min(len(tasks), self.max_workers)
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_single_task(task_info):
            func, args, kwargs = task_info
            async with semaphore:
                return await self.submit_task(func, *args, **kwargs)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(
            *[execute_single_task(task) for task in tasks],
            return_exceptions=True
        )
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task pool statistics"""
        total_tasks = self.completed_tasks + self.failed_tasks
        success_rate = self.completed_tasks / total_tasks if total_tasks > 0 else 0.0
        avg_duration = statistics.mean(self.task_durations) if self.task_durations else 0.0
        
        return {
            "max_workers": self.max_workers,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": success_rate,
            "average_duration": avg_duration,
            "peak_concurrent_tasks": self.peak_concurrent_tasks,
            "total_execution_time": self.total_execution_time
        }


class IntelligentBatcher:
    """Intelligent batching system with adaptive sizing"""
    
    def __init__(self, config: BatchConfig):
        self.config = config
        self.pending_items: List[Any] = []
        self.batch_queue: asyncio.Queue = asyncio.Queue()
        self.processing_times: deque = deque(maxlen=100)
        
        # Adaptive optimization
        self.optimal_batch_size = config.batch_size
        self.last_optimization = time.time()
        
        # Statistics
        self.batches_processed = 0
        self.items_processed = 0
        self.total_processing_time = 0.0
        
        # Background processing
        self.processor_task: Optional[asyncio.Task] = None
        self.running = False
    
    async def start(self, processor_func: Callable[[List[Any]], Any]):
        """Start batch processing"""
        if self.running:
            return
        
        self.running = True
        self.processor_func = processor_func
        self.processor_task = asyncio.create_task(self._batch_processor())
        logger.info(f"📦 Intelligent batcher started")
    
    async def stop(self):
        """Stop batch processing"""
        self.running = False
        
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
            self.processor_task = None
        
        logger.info(f"📦 Intelligent batcher stopped")
    
    async def add_item(self, item: Any) -> Any:
        """Add item to batch queue"""
        future = asyncio.Future()
        await self.batch_queue.put((item, future))
        return await future
    
    async def _batch_processor(self):
        """Background batch processing loop"""
        while self.running:
            try:
                batch_items = []
                batch_futures = []
                
                # Collect items for batch
                await self._collect_batch_items(batch_items, batch_futures)
                
                if not batch_items:
                    await asyncio.sleep(0.1)
                    continue
                
                # Process batch
                start_time = time.time()
                try:
                    results = await self._process_batch(batch_items)
                    
                    # Set results for futures
                    for future, result in zip(batch_futures, results):
                        if not future.cancelled():
                            future.set_result(result)
                    
                except Exception as e:
                    # Set exception for all futures
                    for future in batch_futures:
                        if not future.cancelled():
                            future.set_exception(e)
                
                # Record performance
                processing_time = time.time() - start_time
                self.processing_times.append(processing_time)
                self.total_processing_time += processing_time
                self.batches_processed += 1
                self.items_processed += len(batch_items)
                
                # Optimize batch size if needed
                if self.config.adaptive:
                    await self._optimize_batch_size()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in batch processor: {e}")
                await asyncio.sleep(1)
    
    async def _collect_batch_items(self, batch_items: List[Any], batch_futures: List[asyncio.Future]):
        """Collect items for a batch"""
        batch_start_time = time.time()
        
        # Get first item (blocking)
        try:
            item, future = await asyncio.wait_for(
                self.batch_queue.get(),
                timeout=self.config.max_wait_time
            )
            batch_items.append(item)
            batch_futures.append(future)
        except asyncio.TimeoutError:
            return
        
        # Collect additional items (non-blocking)
        while (len(batch_items) < self.optimal_batch_size and
               time.time() - batch_start_time < self.config.max_wait_time):
            try:
                item, future = self.batch_queue.get_nowait()
                batch_items.append(item)
                batch_futures.append(future)
            except asyncio.QueueEmpty:
                break
    
    async def _process_batch(self, batch_items: List[Any]) -> List[Any]:
        """Process a batch of items"""
        if asyncio.iscoroutinefunction(self.processor_func):
            return await self.processor_func(batch_items)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.processor_func, batch_items)
    
    async def _optimize_batch_size(self):
        """Optimize batch size based on performance"""
        if (time.time() - self.last_optimization < DEFAULT_OPTIMIZATION_INTERVAL or
            len(self.processing_times) < 10):
            return
        
        # Calculate throughput for recent batches
        recent_times = list(self.processing_times)[-10:]
        avg_time = statistics.mean(recent_times)
        current_throughput = self.optimal_batch_size / avg_time
        
        # Test different batch sizes
        test_sizes = [
            max(self.config.min_batch_size, int(self.optimal_batch_size * 0.8)),
            self.optimal_batch_size,
            min(self.config.max_batch_size, int(self.optimal_batch_size * 1.2))
        ]
        
        # Simple heuristic: if processing time is increasing, reduce batch size
        if len(recent_times) >= 2:
            if recent_times[-1] > recent_times[-2] * 1.2:
                self.optimal_batch_size = max(
                    self.config.min_batch_size,
                    int(self.optimal_batch_size * 0.9)
                )
            elif recent_times[-1] < recent_times[-2] * 0.8:
                self.optimal_batch_size = min(
                    self.config.max_batch_size,
                    int(self.optimal_batch_size * 1.1)
                )
        
        self.last_optimization = time.time()
        logger.debug(f"📦 Optimized batch size to {self.optimal_batch_size}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batching statistics"""
        avg_processing_time = statistics.mean(self.processing_times) if self.processing_times else 0.0
        throughput = self.items_processed / self.total_processing_time if self.total_processing_time > 0 else 0.0
        
        return {
            "optimal_batch_size": self.optimal_batch_size,
            "configured_batch_size": self.config.batch_size,
            "batches_processed": self.batches_processed,
            "items_processed": self.items_processed,
            "average_processing_time": avg_processing_time,
            "throughput_items_per_second": throughput,
            "queue_size": self.batch_queue.qsize()
        }


class PerformanceCache:
    """High-performance caching system with multiple strategies"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.access_counts: Dict[str, int] = defaultdict(int)
        self.insertion_order: deque = deque()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        self.running = False
    
    async def start(self):
        """Start cache cleanup task"""
        if self.running:
            return
        
        self.running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"💾 Performance cache started")
    
    async def stop(self):
        """Stop cache cleanup task"""
        self.running = False
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None
        
        logger.info(f"💾 Performance cache stopped")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        current_time = time.time()
        
        # Check TTL
        if current_time - entry["timestamp"] > self.config.ttl:
            self._remove_key(key)
            self.misses += 1
            return None
        
        # Update access info
        self.access_times[key] = current_time
        self.access_counts[key] += 1
        self.hits += 1
        
        # Move to end for LRU
        if self.config.strategy == "lru":
            self.insertion_order.remove(key)
            self.insertion_order.append(key)
        
        return entry["value"]
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        current_time = time.time()
        
        # Remove existing entry if present
        if key in self.cache:
            self._remove_key(key)
        
        # Check size limit and evict if necessary
        while len(self.cache) >= self.config.max_size:
            self._evict_entry()
        
        # Add new entry
        self.cache[key] = {
            "value": value,
            "timestamp": current_time
        }
        self.access_times[key] = current_time
        self.access_counts[key] = 1
        self.insertion_order.append(key)
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        if key in self.cache:
            self._remove_key(key)
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.access_times.clear()
        self.access_counts.clear()
        self.insertion_order.clear()
    
    def _remove_key(self, key: str) -> None:
        """Remove key from all data structures"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_times:
            del self.access_times[key]
        if key in self.access_counts:
            del self.access_counts[key]
        if key in self.insertion_order:
            self.insertion_order.remove(key)
    
    def _evict_entry(self) -> None:
        """Evict entry based on strategy"""
        if not self.cache:
            return
        
        if self.config.strategy == "lru":
            # Least Recently Used
            key = self.insertion_order.popleft()
        elif self.config.strategy == "lfu":
            # Least Frequently Used
            key = min(self.access_counts.keys(), key=lambda k: self.access_counts[k])
        elif self.config.strategy == "fifo":
            # First In, First Out
            key = self.insertion_order.popleft()
        else:
            # Default to LRU
            key = self.insertion_order.popleft()
        
        self._remove_key(key)
        self.evictions += 1
    
    async def _cleanup_loop(self):
        """Background cleanup of expired entries"""
        while self.running:
            try:
                await self._cleanup_expired()
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Cache cleanup error: {e}")
                await asyncio.sleep(30)
    
    async def _cleanup_expired(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if current_time - entry["timestamp"] > self.config.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_key(key)
        
        if expired_keys:
            logger.debug(f"💾 Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "size": len(self.cache),
            "max_size": self.config.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "evictions": self.evictions,
            "strategy": self.config.strategy,
            "ttl": self.config.ttl
        }


class PerformanceMonitor:
    """Monitors and tracks performance metrics"""
    
    def __init__(self, window_seconds: float = DEFAULT_PERFORMANCE_WINDOW):
        self.window_seconds = window_seconds
        self.samples: Dict[PerformanceMetric, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.thresholds: Dict[PerformanceMetric, float] = {
            PerformanceMetric.LATENCY: 1.0,  # 1 second
            PerformanceMetric.CPU_USAGE: 80.0,  # 80%
            PerformanceMetric.MEMORY_USAGE: 85.0,  # 85%
            PerformanceMetric.ERROR_RATE: 5.0,  # 5%
        }
        
        # System monitoring
        self.process = psutil.Process()
        self.monitor_task: Optional[asyncio.Task] = None
        self.running = False
    
    async def start_monitoring(self):
        """Start performance monitoring"""
        if self.running:
            return
        
        self.running = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"📊 Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        self.running = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None
        
        logger.info(f"📊 Performance monitoring stopped")
    
    def record_metric(self, metric: PerformanceMetric, value: float, context: Optional[Dict[str, Any]] = None):
        """Record a performance metric"""
        sample = PerformanceSample(
            timestamp=time.time(),
            metric=metric,
            value=value,
            context=context
        )
        
        self.samples[metric].append(sample)
        
        # Check threshold
        if metric in self.thresholds and value > self.thresholds[metric]:
            logger.warning(f"⚠️ Performance threshold exceeded: {metric.value} = {value} > {self.thresholds[metric]}")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                # Monitor system metrics
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                memory_percent = self.process.memory_percent()
                
                self.record_metric(PerformanceMetric.CPU_USAGE, cpu_percent)
                self.record_metric(PerformanceMetric.MEMORY_USAGE, memory_percent)
                
                await asyncio.sleep(10)  # Sample every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Performance monitoring error: {e}")
                await asyncio.sleep(30)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics"""
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        
        summary = {}
        
        for metric, samples in self.samples.items():
            recent_samples = [
                sample for sample in samples
                if sample.timestamp >= cutoff_time
            ]
            
            if not recent_samples:
                continue
            
            values = [sample.value for sample in recent_samples]
            
            summary[metric.value] = {
                "count": len(values),
                "average": statistics.mean(values),
                "min": min(values),
                "max": max(values),
                "median": statistics.median(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
                "threshold": self.thresholds.get(metric),
                "threshold_violations": sum(1 for v in values if self.thresholds.get(metric) and v > self.thresholds[metric])
            }
        
        return summary


class PerformanceOptimizer:
    """Main performance optimization coordinator"""
    
    def __init__(
        self,
        max_workers: int = DEFAULT_MAX_WORKERS,
        batch_config: Optional[BatchConfig] = None,
        cache_config: Optional[CacheConfig] = None
    ):
        """
        Initialize performance optimizer.
        
        Args:
            max_workers: Maximum concurrent workers
            batch_config: Batch processing configuration
            cache_config: Cache configuration
        """
        self.task_pool = AsyncTaskPool(max_workers)
        self.batcher = IntelligentBatcher(batch_config or BatchConfig())
        self.cache = PerformanceCache(cache_config or CacheConfig())
        self.monitor = PerformanceMonitor()
        
        # Optimization state
        self.active = False
        self.start_time = time.time()
    
    async def start(self):
        """Start all optimization components"""
        if self.active:
            return
        
        self.active = True
        
        await self.cache.start()
        await self.monitor.start_monitoring()
        
        logger.info(f"⚡ Performance optimizer started")
    
    async def stop(self):
        """Stop all optimization components"""
        if not self.active:
            return
        
        self.active = False
        
        await self.batcher.stop()
        await self.cache.stop()
        await self.monitor.stop_monitoring()
        
        logger.info(f"⚡ Performance optimizer stopped")
    
    async def execute_task(self, task_func: Callable, *args, **kwargs) -> Any:
        """Execute task with optimization"""
        return await self.task_pool.submit_task(task_func, *args, **kwargs)
    
    async def execute_batch(self, tasks: List[Tuple[Callable, Tuple, Dict]]) -> List[Any]:
        """Execute batch of tasks with optimization"""
        return await self.task_pool.submit_batch(tasks)
    
    async def start_batch_processing(self, processor_func: Callable):
        """Start intelligent batch processing"""
        await self.batcher.start(processor_func)
    
    async def add_to_batch(self, item: Any) -> Any:
        """Add item to batch queue"""
        return await self.batcher.add_item(item)
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get from cache"""
        return self.cache.get(key)
    
    def cache_set(self, key: str, value: Any):
        """Set cache value"""
        self.cache.set(key, value)
    
    def record_performance_metric(self, metric: PerformanceMetric, value: float, context: Optional[Dict[str, Any]] = None):
        """Record performance metric"""
        self.monitor.record_metric(metric, value, context)
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        return {
            "uptime_hours": (time.time() - self.start_time) / 3600,
            "task_pool": self.task_pool.get_stats(),
            "batching": self.batcher.get_stats(),
            "cache": self.cache.get_stats(),
            "performance_metrics": self.monitor.get_metrics_summary()
        }


# === Convenience Functions ===

async def create_performance_optimizer(**kwargs) -> PerformanceOptimizer:
    """Create and start a performance optimizer"""
    optimizer = PerformanceOptimizer(**kwargs)
    await optimizer.start()
    return optimizer


def performance_optimize(cache_key: Optional[str] = None, use_batching: bool = False):
    """Decorator for automatic performance optimization"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Check cache first
            if cache_key and hasattr(self, 'performance_optimizer'):
                cached_result = self.performance_optimizer.cache_get(cache_key)
                if cached_result is not None:
                    return cached_result
            
            # Execute with performance monitoring
            start_time = time.time()
            try:
                if hasattr(self, 'performance_optimizer'):
                    result = await self.performance_optimizer.execute_task(func, self, *args, **kwargs)
                else:
                    result = await func(self, *args, **kwargs)
                
                # Cache result
                if cache_key and hasattr(self, 'performance_optimizer'):
                    self.performance_optimizer.cache_set(cache_key, result)
                
                # Record performance
                if hasattr(self, 'performance_optimizer'):
                    latency = time.time() - start_time
                    self.performance_optimizer.record_performance_metric(
                        PerformanceMetric.LATENCY, latency, {"function": func.__name__}
                    )
                
                return result
                
            except Exception as e:
                # Record error
                if hasattr(self, 'performance_optimizer'):
                    self.performance_optimizer.record_performance_metric(
                        PerformanceMetric.ERROR_RATE, 1.0, {"function": func.__name__, "error": str(e)}
                    )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            # For sync functions, just add basic monitoring
            start_time = time.time()
            try:
                result = func(self, *args, **kwargs)
                
                # Record performance
                if hasattr(self, 'performance_optimizer'):
                    latency = time.time() - start_time
                    self.performance_optimizer.record_performance_metric(
                        PerformanceMetric.LATENCY, latency, {"function": func.__name__}
                    )
                
                return result
                
            except Exception as e:
                # Record error
                if hasattr(self, 'performance_optimizer'):
                    self.performance_optimizer.record_performance_metric(
                        PerformanceMetric.ERROR_RATE, 1.0, {"function": func.__name__, "error": str(e)}
                    )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator 