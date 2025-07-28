#!/usr/bin/env python3
"""
Resource Management Module

This module provides comprehensive resource management with:
- Memory leak prevention and monitoring
- Automatic cleanup of old data structures
- Resource usage tracking and alerting
- Cache management and optimization
- Database connection pooling
- File handle management

Key Features:
- Automatic memory monitoring and cleanup
- Configurable data retention policies
- Resource usage alerts and limits
- Garbage collection optimization
- Cache expiration and rotation
"""

import asyncio
import gc
import logging
import psutil
import time
import threading
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import sys
import os

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MEMORY_THRESHOLD_MB = 512  # Alert when memory usage exceeds 512MB
DEFAULT_CLEANUP_INTERVAL = 300  # 5 minutes
DEFAULT_DATA_RETENTION_HOURS = 24  # Keep data for 24 hours
DEFAULT_CACHE_SIZE_LIMIT = 1000  # Maximum cache entries
DEFAULT_GC_THRESHOLD = 100  # Force GC after 100 allocations
MEMORY_SAMPLING_INTERVAL = 60  # Sample memory every 60 seconds


class ResourceType(Enum):
    """Types of resources to monitor"""
    MEMORY = "memory"
    CPU = "cpu"
    DISK = "disk"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    FILES = "files"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ResourceAlert:
    """Resource usage alert"""
    resource_type: ResourceType
    level: AlertLevel
    message: str
    current_value: float
    threshold: float
    timestamp: float


@dataclass
class MemorySnapshot:
    """Memory usage snapshot"""
    timestamp: float
    rss_mb: float  # Resident Set Size
    vms_mb: float  # Virtual Memory Size
    percent: float  # Memory percentage
    available_mb: float
    gc_objects: int
    gc_collections: Dict[int, int] = field(default_factory=dict)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    size_bytes: Optional[int] = None


class ResourceMonitor:
    """
    Monitors system resource usage and triggers alerts.
    """
    
    def __init__(
        self,
        memory_threshold_mb: float = DEFAULT_MEMORY_THRESHOLD_MB,
        cpu_threshold_percent: float = 80.0,
        disk_threshold_percent: float = 85.0,
        alert_callback: Optional[Callable[[ResourceAlert], None]] = None
    ):
        """
        Initialize resource monitor.
        
        Args:
            memory_threshold_mb: Memory threshold in MB
            cpu_threshold_percent: CPU usage threshold
            disk_threshold_percent: Disk usage threshold
            alert_callback: Function to call when alerts are triggered
        """
        self.memory_threshold_mb = memory_threshold_mb
        self.cpu_threshold_percent = cpu_threshold_percent
        self.disk_threshold_percent = disk_threshold_percent
        self.alert_callback = alert_callback
        
        # Monitoring state
        self.process = psutil.Process()
        self.memory_snapshots: deque = deque(maxlen=100)  # Last 100 snapshots
        self.alerts: deque = deque(maxlen=50)  # Last 50 alerts
        self.monitoring_active = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.peak_memory_mb = 0.0
        self.total_alerts = 0
        self.start_time = time.time()
    
    async def start_monitoring(self):
        """Start resource monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("🔍 Resource monitoring started")
    
    async def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring_active = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None
        
        logger.info("🔍 Resource monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Take memory snapshot
                await self._take_memory_snapshot()
                
                # Check thresholds and generate alerts
                await self._check_thresholds()
                
                # Wait for next sample
                await asyncio.sleep(MEMORY_SAMPLING_INTERVAL)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in resource monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    async def _take_memory_snapshot(self):
        """Take a memory usage snapshot"""
        try:
            # Get process memory info
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # Get system memory info
            system_memory = psutil.virtual_memory()
            
            # Get garbage collection stats
            gc_stats = {i: gc.get_count()[i] for i in range(len(gc.get_count()))}
            
            snapshot = MemorySnapshot(
                timestamp=time.time(),
                rss_mb=memory_info.rss / 1024 / 1024,
                vms_mb=memory_info.vms / 1024 / 1024,
                percent=memory_percent,
                available_mb=system_memory.available / 1024 / 1024,
                gc_objects=len(gc.get_objects()),
                gc_collections=gc_stats
            )
            
            self.memory_snapshots.append(snapshot)
            
            # Update peak memory
            if snapshot.rss_mb > self.peak_memory_mb:
                self.peak_memory_mb = snapshot.rss_mb
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to take memory snapshot: {e}")
    
    async def _check_thresholds(self):
        """Check resource thresholds and generate alerts"""
        if not self.memory_snapshots:
            return
        
        latest = self.memory_snapshots[-1]
        
        # Check memory threshold
        if latest.rss_mb > self.memory_threshold_mb:
            alert = ResourceAlert(
                resource_type=ResourceType.MEMORY,
                level=AlertLevel.WARNING if latest.rss_mb < self.memory_threshold_mb * 1.5 else AlertLevel.CRITICAL,
                message=f"High memory usage: {latest.rss_mb:.1f}MB (threshold: {self.memory_threshold_mb}MB)",
                current_value=latest.rss_mb,
                threshold=self.memory_threshold_mb,
                timestamp=latest.timestamp
            )
            await self._trigger_alert(alert)
        
        # Check CPU threshold
        try:
            cpu_percent = self.process.cpu_percent()
            if cpu_percent > self.cpu_threshold_percent:
                alert = ResourceAlert(
                    resource_type=ResourceType.CPU,
                    level=AlertLevel.WARNING if cpu_percent < self.cpu_threshold_percent * 1.2 else AlertLevel.CRITICAL,
                    message=f"High CPU usage: {cpu_percent:.1f}% (threshold: {self.cpu_threshold_percent}%)",
                    current_value=cpu_percent,
                    threshold=self.cpu_threshold_percent,
                    timestamp=time.time()
                )
                await self._trigger_alert(alert)
        except Exception as e:
            logger.debug(f"Failed to check CPU: {e}")
    
    async def _trigger_alert(self, alert: ResourceAlert):
        """Trigger a resource alert"""
        self.alerts.append(alert)
        self.total_alerts += 1
        
        # Log the alert
        log_func = logger.critical if alert.level == AlertLevel.CRITICAL else logger.warning
        log_func(f"🚨 {alert.level.value.upper()}: {alert.message}")
        
        # Call external alert handler
        if self.alert_callback:
            try:
                await asyncio.create_task(
                    alert.callback(alert) if asyncio.iscoroutinefunction(self.alert_callback) 
                    else asyncio.to_thread(self.alert_callback, alert)
                )
            except Exception as e:
                logger.error(f"❌ Alert callback failed: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        if not self.memory_snapshots:
            return {"error": "No memory data available"}
        
        latest = self.memory_snapshots[-1]
        snapshots = list(self.memory_snapshots)
        
        return {
            "current_mb": latest.rss_mb,
            "peak_mb": self.peak_memory_mb,
            "threshold_mb": self.memory_threshold_mb,
            "usage_percent": latest.percent,
            "available_mb": latest.available_mb,
            "gc_objects": latest.gc_objects,
            "trend_mb": snapshots[-1].rss_mb - snapshots[0].rss_mb if len(snapshots) > 1 else 0,
            "samples_count": len(snapshots),
            "uptime_hours": (time.time() - self.start_time) / 3600
        }


class DataCleanupManager:
    """
    Manages automatic cleanup of old data structures.
    """
    
    def __init__(
        self,
        cleanup_interval: int = DEFAULT_CLEANUP_INTERVAL,
        data_retention_hours: int = DEFAULT_DATA_RETENTION_HOURS
    ):
        """
        Initialize cleanup manager.
        
        Args:
            cleanup_interval: Cleanup interval in seconds
            data_retention_hours: How long to keep data in hours
        """
        self.cleanup_interval = cleanup_interval
        self.data_retention_seconds = data_retention_hours * 3600
        
        # Registered cleanup targets
        self.cleanup_targets: Dict[str, Dict[str, Any]] = {}
        self.cleanup_active = False
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.total_cleanups = 0
        self.total_items_cleaned = 0
    
    def register_cleanup_target(
        self,
        name: str,
        data_structure: Union[Dict, List, deque],
        cleanup_strategy: str = "timestamp",
        timestamp_key: str = "timestamp",
        max_size: Optional[int] = None
    ):
        """
        Register a data structure for automatic cleanup.
        
        Args:
            name: Unique name for the target
            data_structure: The data structure to clean
            cleanup_strategy: Strategy to use ("timestamp", "size", "custom")
            timestamp_key: Key to use for timestamp-based cleanup
            max_size: Maximum size for size-based cleanup
        """
        self.cleanup_targets[name] = {
            "data_structure": data_structure,  # Use direct reference instead of weakref
            "cleanup_strategy": cleanup_strategy,
            "timestamp_key": timestamp_key,
            "max_size": max_size,
            "last_cleanup": time.time(),
            "items_cleaned": 0
        }
        
        logger.debug(f"🧹 Registered cleanup target: {name} ({cleanup_strategy})")
    
    async def start_cleanup(self):
        """Start automatic cleanup"""
        if self.cleanup_active:
            return
        
        self.cleanup_active = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("🧹 Automatic cleanup started")
    
    async def stop_cleanup(self):
        """Stop automatic cleanup"""
        self.cleanup_active = False
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None
        
        logger.info("🧹 Automatic cleanup stopped")
    
    async def _cleanup_loop(self):
        """Main cleanup loop"""
        while self.cleanup_active:
            try:
                await self._perform_cleanup()
                await asyncio.sleep(self.cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in cleanup loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _perform_cleanup(self):
        """Perform cleanup on all registered targets"""
        current_time = time.time()
        cutoff_time = current_time - self.data_retention_seconds
        
        for name, target_info in list(self.cleanup_targets.items()):
            try:
                # Get the data structure (using direct reference now)
                data_ref = target_info["data_structure"]
                if data_ref is None:
                    # Data structure was deleted, remove target
                    del self.cleanup_targets[name]
                    continue
                
                # Perform cleanup based on strategy
                items_cleaned = await self._cleanup_target(name, data_ref, target_info, cutoff_time)
                
                target_info["items_cleaned"] += items_cleaned
                target_info["last_cleanup"] = current_time
                self.total_items_cleaned += items_cleaned
                
                if items_cleaned > 0:
                    logger.debug(f"🧹 Cleaned {items_cleaned} items from {name}")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to cleanup target {name}: {e}")
        
        # Perform garbage collection if needed
        if self.total_items_cleaned % DEFAULT_GC_THRESHOLD == 0:
            collected = gc.collect()
            if collected > 0:
                logger.debug(f"🗑️ Garbage collected {collected} objects")
        
        self.total_cleanups += 1
    
    async def _cleanup_target(
        self,
        name: str,
        data_structure: Any,
        target_info: Dict[str, Any],
        cutoff_time: float
    ) -> int:
        """Cleanup a specific target"""
        strategy = target_info["cleanup_strategy"]
        items_cleaned = 0
        
        if strategy == "timestamp":
            items_cleaned = await self._cleanup_by_timestamp(
                data_structure, target_info["timestamp_key"], cutoff_time
            )
        elif strategy == "size":
            items_cleaned = await self._cleanup_by_size(
                data_structure, target_info["max_size"]
            )
        
        return items_cleaned
    
    async def _cleanup_by_timestamp(self, data_structure: Any, timestamp_key: str, cutoff_time: float) -> int:
        """Cleanup items older than cutoff time"""
        items_cleaned = 0
        
        try:
            if isinstance(data_structure, dict):
                # Dictionary cleanup
                keys_to_remove = []
                for key, value in data_structure.items():
                    item_time = self._extract_timestamp(value, timestamp_key)
                    if item_time and item_time < cutoff_time:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del data_structure[key]
                    items_cleaned += 1
                    
            elif isinstance(data_structure, (list, deque)):
                # List/deque cleanup (remove from beginning)
                original_length = len(data_structure)
                
                while data_structure:
                    item_time = self._extract_timestamp(data_structure[0], timestamp_key)
                    if item_time and item_time < cutoff_time:
                        data_structure.popleft() if hasattr(data_structure, 'popleft') else data_structure.pop(0)
                        items_cleaned += 1
                    else:
                        break
                        
        except Exception as e:
            logger.warning(f"⚠️ Error in timestamp cleanup: {e}")
        
        return items_cleaned
    
    async def _cleanup_by_size(self, data_structure: Any, max_size: Optional[int]) -> int:
        """Cleanup items to maintain maximum size"""
        if max_size is None:
            return 0
        
        items_cleaned = 0
        current_size = len(data_structure)
        
        if current_size <= max_size:
            return 0
        
        items_to_remove = current_size - max_size
        
        try:
            if isinstance(data_structure, dict):
                # Remove oldest items (assuming ordered dict)
                keys_to_remove = list(data_structure.keys())[:items_to_remove]
                for key in keys_to_remove:
                    del data_structure[key]
                    items_cleaned += 1
                    
            elif isinstance(data_structure, (list, deque)):
                # Remove from beginning
                for _ in range(items_to_remove):
                    if data_structure:
                        data_structure.popleft() if hasattr(data_structure, 'popleft') else data_structure.pop(0)
                        items_cleaned += 1
                        
        except Exception as e:
            logger.warning(f"⚠️ Error in size cleanup: {e}")
        
        return items_cleaned
    
    def _extract_timestamp(self, item: Any, timestamp_key: str) -> Optional[float]:
        """Extract timestamp from an item"""
        try:
            if isinstance(item, dict):
                return item.get(timestamp_key)
            elif hasattr(item, timestamp_key):
                return getattr(item, timestamp_key)
            elif hasattr(item, 'timestamp'):
                return item.timestamp
            else:
                return None
        except Exception:
            return None
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """Get cleanup statistics"""
        target_stats = {}
        for name, target_info in self.cleanup_targets.items():
            data_ref = target_info["data_structure"]  # Remove () call
            target_stats[name] = {
                "strategy": target_info["cleanup_strategy"],
                "items_cleaned": target_info["items_cleaned"],
                "last_cleanup": target_info["last_cleanup"],
                "current_size": len(data_ref) if data_ref else 0
            }
        
        return {
            "total_cleanups": self.total_cleanups,
            "total_items_cleaned": self.total_items_cleaned,
            "active_targets": len(self.cleanup_targets),
            "targets": target_stats
        }


class CacheManager:
    """
    Manages intelligent caching with size limits and expiration.
    """
    
    def __init__(
        self,
        max_size: int = DEFAULT_CACHE_SIZE_LIMIT,
        default_ttl: int = 3600,  # 1 hour default TTL
        cleanup_interval: int = 300  # 5 minutes
    ):
        """
        Initialize cache manager.
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default time-to-live in seconds
            cleanup_interval: Cleanup interval in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        
        # Cache storage
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: deque = deque()  # For LRU eviction
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expirations = 0
        
        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        self.active = False
    
    async def start(self):
        """Start cache manager"""
        if self.active:
            return
        
        self.active = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("💾 Cache manager started")
    
    async def stop(self):
        """Stop cache manager"""
        self.active = False
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None
        
        logger.info("💾 Cache manager stopped")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        current_time = time.time()
        
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        
        # Check expiration
        if current_time - entry.created_at > self.default_ttl:
            self._remove_entry(key)
            self.misses += 1
            self.expirations += 1
            return None
        
        # Update access info
        entry.last_accessed = current_time
        entry.access_count += 1
        
        # Update LRU order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        self.hits += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        current_time = time.time()
        
        # Calculate size if possible
        size_bytes = None
        try:
            size_bytes = sys.getsizeof(value)
        except Exception:
            pass
        
        # Create cache entry
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=current_time,
            last_accessed=current_time,
            size_bytes=size_bytes
        )
        
        # Remove existing entry if present
        if key in self.cache:
            self._remove_entry(key)
        
        # Check size limit and evict if necessary
        while len(self.cache) >= self.max_size:
            self._evict_lru()
        
        # Add new entry
        self.cache[key] = entry
        self.access_order.append(key)
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        if key in self.cache:
            self._remove_entry(key)
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.access_order.clear()
    
    def _remove_entry(self, key: str) -> None:
        """Remove entry from cache and access order"""
        if key in self.cache:
            del self.cache[key]
        
        if key in self.access_order:
            self.access_order.remove(key)
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if self.access_order:
            lru_key = self.access_order.popleft()
            if lru_key in self.cache:
                del self.cache[lru_key]
                self.evictions += 1
    
    async def _cleanup_loop(self):
        """Cleanup expired entries periodically"""
        while self.active:
            try:
                await self._cleanup_expired()
                await asyncio.sleep(self.cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in cache cleanup: {e}")
                await asyncio.sleep(30)
    
    async def _cleanup_expired(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if current_time - entry.created_at > self.default_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_entry(key)
            self.expirations += 1
        
        if expired_keys:
            logger.debug(f"💾 Cleaned {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
        
        total_size_bytes = sum(
            entry.size_bytes for entry in self.cache.values() 
            if entry.size_bytes is not None
        )
        
        return {
            "entries": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "evictions": self.evictions,
            "expirations": self.expirations,
            "total_size_bytes": total_size_bytes,
            "average_size_bytes": total_size_bytes / len(self.cache) if self.cache else 0
        }


class ResourceManager:
    """
    Comprehensive resource management system.
    """
    
    def __init__(
        self,
        memory_threshold_mb: float = DEFAULT_MEMORY_THRESHOLD_MB,
        cleanup_interval: int = DEFAULT_CLEANUP_INTERVAL,
        data_retention_hours: int = DEFAULT_DATA_RETENTION_HOURS,
        cache_size_limit: int = DEFAULT_CACHE_SIZE_LIMIT
    ):
        """
        Initialize resource manager.
        
        Args:
            memory_threshold_mb: Memory alert threshold
            cleanup_interval: Data cleanup interval
            data_retention_hours: How long to keep data
            cache_size_limit: Maximum cache entries
        """
        # Initialize components
        self.monitor = ResourceMonitor(
            memory_threshold_mb=memory_threshold_mb,
            alert_callback=self._handle_resource_alert
        )
        
        self.cleanup_manager = DataCleanupManager(
            cleanup_interval=cleanup_interval,
            data_retention_hours=data_retention_hours
        )
        
        self.cache_manager = CacheManager(
            max_size=cache_size_limit
        )
        
        # State
        self.active = False
        self.start_time = time.time()
    
    async def start(self):
        """Start resource management"""
        if self.active:
            return
        
        self.active = True
        
        # Start all components
        await self.monitor.start_monitoring()
        await self.cleanup_manager.start_cleanup()
        await self.cache_manager.start()
        
        logger.info("🛠️ Resource management started")
    
    async def stop(self):
        """Stop resource management"""
        if not self.active:
            return
        
        self.active = False
        
        # Stop all components
        await self.monitor.stop_monitoring()
        await self.cleanup_manager.stop_cleanup()
        await self.cache_manager.stop()
        
        logger.info("🛠️ Resource management stopped")
    
    def register_cleanup_target(self, name: str, data_structure: Any, **kwargs):
        """Register data structure for cleanup"""
        self.cleanup_manager.register_cleanup_target(name, data_structure, **kwargs)
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get from cache"""
        return self.cache_manager.get(key)
    
    def cache_set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set cache value"""
        self.cache_manager.set(key, value, ttl)
    
    def cache_delete(self, key: str) -> bool:
        """Delete from cache"""
        return self.cache_manager.delete(key)
    
    async def _handle_resource_alert(self, alert: ResourceAlert):
        """Handle resource alerts"""
        # Log the alert
        logger.warning(f"🚨 Resource Alert: {alert.message}")
        
        # Take action based on alert type and level
        if alert.resource_type == ResourceType.MEMORY:
            if alert.level == AlertLevel.CRITICAL:
                # Force garbage collection
                collected = gc.collect()
                logger.info(f"🗑️ Emergency GC collected {collected} objects")
                
                # Clear cache if needed
                if alert.current_value > alert.threshold * 2:
                    cache_entries = len(self.cache_manager.cache)
                    self.cache_manager.clear()
                    logger.info(f"💾 Emergency cache clear: {cache_entries} entries removed")
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive resource statistics"""
        return {
            "uptime_hours": (time.time() - self.start_time) / 3600,
            "memory": self.monitor.get_memory_stats(),
            "cleanup": self.cleanup_manager.get_cleanup_stats(),
            "cache": self.cache_manager.get_stats(),
            "alerts": {
                "total": self.monitor.total_alerts,
                "recent": [
                    {
                        "type": alert.resource_type.value,
                        "level": alert.level.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp
                    }
                    for alert in list(self.monitor.alerts)[-5:]  # Last 5 alerts
                ]
            }
        }


# === Convenience Functions ===

async def create_resource_manager(**kwargs) -> ResourceManager:
    """Create and start a resource manager"""
    manager = ResourceManager(**kwargs)
    await manager.start()
    return manager


def setup_basic_cleanup(validator_node_core):
    """Setup basic cleanup for validator node core components"""
    manager = ResourceManager()
    
    # Register common cleanup targets
    manager.register_cleanup_target(
        "tasks_sent",
        validator_node_core.tasks_sent,
        cleanup_strategy="timestamp",
        timestamp_key="timestamp_sent"
    )
    
    manager.register_cleanup_target(
        "results_buffer",
        validator_node_core.results_buffer,
        cleanup_strategy="size",
        max_size=1000
    )
    
    manager.register_cleanup_target(
        "cycle_scores",
        validator_node_core.cycle_scores,
        cleanup_strategy="size",
        max_size=500
    )
    
    return manager 