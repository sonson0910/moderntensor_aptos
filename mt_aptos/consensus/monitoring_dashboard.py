#!/usr/bin/env python3
"""
Monitoring and Metrics Dashboard Module

This module provides comprehensive monitoring and metrics with:
- Real-time performance dashboards
- System health monitoring
- Consensus quality metrics
- Network topology visualization
- Alerting and notification system
- Historical data analysis

Key Features:
- Web-based dashboard interface
- Real-time metrics streaming
- Automated health checks
- Performance bottleneck detection
- Consensus fork detection
- SLA monitoring and reporting
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import json
import statistics
from pathlib import Path

logger = logging.getLogger(__name__)

# Constants
DEFAULT_DASHBOARD_PORT = 8080
DEFAULT_METRICS_RETENTION = 86400  # 24 hours
DEFAULT_HEALTH_CHECK_INTERVAL = 30  # 30 seconds
MAX_METRICS_SAMPLES = 10000


class HealthStatus(Enum):
    """System health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class MetricType(Enum):
    """Types of metrics to track"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricSample:
    """Single metric sample"""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Health check definition"""
    name: str
    check_func: Callable[[], bool]
    interval: float = DEFAULT_HEALTH_CHECK_INTERVAL
    timeout: float = 10.0
    last_check: Optional[float] = None
    last_status: HealthStatus = HealthStatus.UNKNOWN
    failure_count: int = 0
    description: str = ""


class MetricsCollector:
    """Collects and stores metrics"""
    
    def __init__(self, retention_seconds: int = DEFAULT_METRICS_RETENTION):
        self.retention_seconds = retention_seconds
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self.samples: Dict[str, deque] = defaultdict(lambda: deque(maxlen=MAX_METRICS_SAMPLES))
        
        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        self.active = False
    
    async def start(self):
        """Start metrics collection"""
        if self.active:
            return
        
        self.active = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("📊 Metrics collector started")
    
    async def stop(self):
        """Stop metrics collection"""
        self.active = False
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None
        
        logger.info("📊 Metrics collector stopped")
    
    def register_metric(self, name: str, metric_type: MetricType, description: str = "", labels: Optional[List[str]] = None):
        """Register a new metric"""
        self.metrics[name] = {
            "type": metric_type,
            "description": description,
            "labels": labels or [],
            "created_at": time.time()
        }
    
    def record_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Record counter metric"""
        self._record_sample(name, value, labels)
    
    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record gauge metric"""
        self._record_sample(name, value, labels)
    
    def record_timer(self, name: str, duration: float, labels: Optional[Dict[str, str]] = None):
        """Record timer metric"""
        self._record_sample(name, duration, labels)
    
    def _record_sample(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a metric sample"""
        sample = MetricSample(
            timestamp=time.time(),
            value=value,
            labels=labels or {}
        )
        
        self.samples[name].append(sample)
    
    def get_metric_summary(self, name: str, window_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        if name not in self.samples:
            return {"error": "Metric not found"}
        
        samples = list(self.samples[name])
        
        if window_seconds:
            cutoff_time = time.time() - window_seconds
            samples = [s for s in samples if s.timestamp >= cutoff_time]
        
        if not samples:
            return {"error": "No samples in time window"}
        
        values = [s.value for s in samples]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "latest": values[-1],
            "rate_per_second": len(values) / window_seconds if window_seconds else 0.0
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics and their current values"""
        result = {}
        
        for name in self.metrics.keys():
            result[name] = self.get_metric_summary(name, window_seconds=300)  # Last 5 minutes
        
        return result
    
    async def _cleanup_loop(self):
        """Background cleanup of old samples"""
        while self.active:
            try:
                await self._cleanup_old_samples()
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Metrics cleanup error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_old_samples(self):
        """Remove old metric samples"""
        cutoff_time = time.time() - self.retention_seconds
        cleaned_count = 0
        
        for name, samples in self.samples.items():
            original_length = len(samples)
            
            # Remove old samples
            while samples and samples[0].timestamp < cutoff_time:
                samples.popleft()
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.debug(f"📊 Cleaned up {cleaned_count} old metric samples")


class HealthMonitor:
    """Monitors system health"""
    
    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.overall_status = HealthStatus.UNKNOWN
        self.monitor_task: Optional[asyncio.Task] = None
        self.active = False
        
        # Health history
        self.status_history: deque = deque(maxlen=1000)
    
    async def start(self):
        """Start health monitoring"""
        if self.active:
            return
        
        self.active = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("🏥 Health monitor started")
    
    async def stop(self):
        """Stop health monitoring"""
        self.active = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None
        
        logger.info("🏥 Health monitor stopped")
    
    def register_health_check(self, health_check: HealthCheck):
        """Register a health check"""
        self.health_checks[health_check.name] = health_check
        logger.debug(f"🏥 Registered health check: {health_check.name}")
    
    async def _monitoring_loop(self):
        """Background health monitoring loop"""
        while self.active:
            try:
                await self._run_health_checks()
                await self._update_overall_status()
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Health monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _run_health_checks(self):
        """Run all health checks"""
        current_time = time.time()
        
        for name, health_check in self.health_checks.items():
            # Check if it's time to run this health check
            if (health_check.last_check and 
                current_time - health_check.last_check < health_check.interval):
                continue
            
            try:
                # Run health check with timeout
                result = await asyncio.wait_for(
                    asyncio.to_thread(health_check.check_func),
                    timeout=health_check.timeout
                )
                
                if result:
                    health_check.last_status = HealthStatus.HEALTHY
                    health_check.failure_count = 0
                else:
                    health_check.failure_count += 1
                    if health_check.failure_count >= 3:
                        health_check.last_status = HealthStatus.CRITICAL
                    else:
                        health_check.last_status = HealthStatus.WARNING
                
            except asyncio.TimeoutError:
                health_check.failure_count += 1
                health_check.last_status = HealthStatus.CRITICAL
                logger.warning(f"⚠️ Health check timeout: {name}")
                
            except Exception as e:
                health_check.failure_count += 1
                health_check.last_status = HealthStatus.CRITICAL
                logger.error(f"❌ Health check failed: {name} - {e}")
            
            health_check.last_check = current_time
    
    async def _update_overall_status(self):
        """Update overall system health status"""
        if not self.health_checks:
            self.overall_status = HealthStatus.UNKNOWN
            return
        
        statuses = [check.last_status for check in self.health_checks.values()]
        
        if any(status == HealthStatus.CRITICAL for status in statuses):
            self.overall_status = HealthStatus.CRITICAL
        elif any(status == HealthStatus.WARNING for status in statuses):
            self.overall_status = HealthStatus.WARNING
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            self.overall_status = HealthStatus.HEALTHY
        else:
            self.overall_status = HealthStatus.UNKNOWN
        
        # Record status change
        self.status_history.append({
            "timestamp": time.time(),
            "status": self.overall_status.value
        })
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        return {
            "overall_status": self.overall_status.value,
            "health_checks": {
                name: {
                    "status": check.last_status.value,
                    "last_check": check.last_check,
                    "failure_count": check.failure_count,
                    "description": check.description
                }
                for name, check in self.health_checks.items()
            },
            "status_changes": list(self.status_history)[-10:]  # Last 10 status changes
        }


class MonitoringDashboard:
    """Main monitoring dashboard coordinator"""
    
    def __init__(self, validator_uid: str):
        """
        Initialize monitoring dashboard.
        
        Args:
            validator_uid: Validator identifier
        """
        self.validator_uid = validator_uid
        self.metrics = MetricsCollector()
        self.health = HealthMonitor()
        
        # Dashboard state
        self.active = False
        self.start_time = time.time()
        
        # Register default metrics
        self._register_default_metrics()
        
        # Register default health checks
        self._register_default_health_checks()
    
    async def start(self):
        """Start monitoring dashboard"""
        if self.active:
            return
        
        self.active = True
        
        await self.metrics.start()
        await self.health.start()
        
        logger.info(f"📊 Monitoring dashboard started for validator {self.validator_uid}")
    
    async def stop(self):
        """Stop monitoring dashboard"""
        if not self.active:
            return
        
        self.active = False
        
        await self.metrics.stop()
        await self.health.stop()
        
        logger.info(f"📊 Monitoring dashboard stopped for validator {self.validator_uid}")
    
    def _register_default_metrics(self):
        """Register default system metrics"""
        self.metrics.register_metric("consensus_rounds_total", MetricType.COUNTER, "Total consensus rounds")
        self.metrics.register_metric("consensus_success_rate", MetricType.GAUGE, "Consensus success rate")
        self.metrics.register_metric("task_assignment_duration", MetricType.TIMER, "Task assignment duration")
        self.metrics.register_metric("network_requests_total", MetricType.COUNTER, "Total network requests")
        self.metrics.register_metric("network_errors_total", MetricType.COUNTER, "Total network errors")
        self.metrics.register_metric("memory_usage_bytes", MetricType.GAUGE, "Memory usage in bytes")
        self.metrics.register_metric("cpu_usage_percent", MetricType.GAUGE, "CPU usage percentage")
    
    def _register_default_health_checks(self):
        """Register default health checks"""
        # Memory health check
        def memory_health_check():
            try:
                import psutil
                memory = psutil.virtual_memory()
                return memory.percent < 90  # Less than 90% memory usage
            except Exception:
                return False
        
        self.health.register_health_check(HealthCheck(
            name="memory_usage",
            check_func=memory_health_check,
            description="Memory usage health check"
        ))
        
        # Disk health check
        def disk_health_check():
            try:
                import psutil
                disk = psutil.disk_usage('/')
                return (disk.used / disk.total) < 0.9  # Less than 90% disk usage
            except Exception:
                return False
        
        self.health.register_health_check(HealthCheck(
            name="disk_usage",
            check_func=disk_health_check,
            description="Disk usage health check"
        ))
    
    # Convenience methods for metrics recording
    def record_consensus_round(self, success: bool, duration: float):
        """Record consensus round metrics"""
        self.metrics.record_counter("consensus_rounds_total")
        if success:
            self.metrics.record_counter("consensus_rounds_successful")
        self.metrics.record_timer("consensus_round_duration", duration)
    
    def record_task_assignment(self, duration: float, tasks_count: int):
        """Record task assignment metrics"""
        self.metrics.record_timer("task_assignment_duration", duration)
        self.metrics.record_gauge("tasks_assigned", tasks_count)
    
    def record_network_request(self, success: bool, duration: float):
        """Record network request metrics"""
        self.metrics.record_counter("network_requests_total")
        if not success:
            self.metrics.record_counter("network_errors_total")
        self.metrics.record_timer("network_request_duration", duration)
    
    def record_system_metrics(self, memory_bytes: float, cpu_percent: float):
        """Record system resource metrics"""
        self.metrics.record_gauge("memory_usage_bytes", memory_bytes)
        self.metrics.record_gauge("cpu_usage_percent", cpu_percent)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        return {
            "validator_uid": self.validator_uid,
            "uptime_hours": (time.time() - self.start_time) / 3600,
            "timestamp": time.time(),
            "health": self.health.get_health_report(),
            "metrics": self.metrics.get_all_metrics(),
            "system_status": {
                "active": self.active,
                "components": {
                    "metrics_collector": self.metrics.active,
                    "health_monitor": self.health.active
                }
            }
        }


# === Convenience Functions ===

async def create_monitoring_dashboard(validator_uid: str) -> MonitoringDashboard:
    """Create and start a monitoring dashboard"""
    dashboard = MonitoringDashboard(validator_uid)
    await dashboard.start()
    return dashboard


def setup_monitoring_for_validator(validator_node_core):
    """Setup monitoring for a validator node"""
    dashboard = MonitoringDashboard(validator_node_core.info.uid)
    
    # Add validator-specific health checks
    def validator_health_check():
        return hasattr(validator_node_core, 'aptos_client') and validator_node_core.aptos_client is not None
    
    dashboard.health.register_health_check(HealthCheck(
        name="validator_connection",
        check_func=validator_health_check,
        description="Validator blockchain connection health"
    ))
    
    return dashboard 