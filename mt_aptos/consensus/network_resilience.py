#!/usr/bin/env python3
"""
Network Resilience Module

This module provides robust network communication with:
- Exponential backoff retry logic
- Circuit breaker pattern for failing endpoints
- Connection pooling and lifecycle management
- Health check and recovery mechanisms
- Error rate monitoring and alerting

Key Features:
- Automatic retry with exponential backoff
- Circuit breaker to prevent cascade failures
- Connection pool management
- Endpoint health monitoring
- Graceful degradation strategies
"""

import asyncio
import logging
import time
import random
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque

import httpx

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 60.0  # seconds
DEFAULT_BACKOFF_MULTIPLIER = 2.0
DEFAULT_JITTER_RANGE = 0.1  # ±10% jitter
DEFAULT_CIRCUIT_FAILURE_THRESHOLD = 5
DEFAULT_CIRCUIT_RECOVERY_TIMEOUT = 30.0  # seconds
DEFAULT_HEALTH_CHECK_INTERVAL = 60.0  # seconds


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_retries: int = DEFAULT_MAX_RETRIES
    base_delay: float = DEFAULT_BASE_DELAY
    max_delay: float = DEFAULT_MAX_DELAY
    backoff_multiplier: float = DEFAULT_BACKOFF_MULTIPLIER
    jitter_range: float = DEFAULT_JITTER_RANGE


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = DEFAULT_CIRCUIT_FAILURE_THRESHOLD
    recovery_timeout: float = DEFAULT_CIRCUIT_RECOVERY_TIMEOUT
    success_threshold: int = 2  # Successes needed to close circuit


@dataclass
class EndpointHealth:
    """Health metrics for an endpoint"""
    endpoint: str
    success_count: int = 0
    failure_count: int = 0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    response_times: deque = field(default_factory=lambda: deque(maxlen=10))
    circuit_state: CircuitState = CircuitState.CLOSED
    circuit_opened_at: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0


class NetworkResilientClient:
    """
    Resilient HTTP client with retry logic, circuit breakers, and health monitoring.
    """
    
    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None,
        connection_limits: Optional[httpx.Limits] = None,
        timeout: float = 30.0
    ):
        """
        Initialize resilient network client.
        
        Args:
            retry_config: Retry configuration
            circuit_config: Circuit breaker configuration  
            connection_limits: HTTP connection limits
            timeout: Default request timeout
        """
        self.retry_config = retry_config or RetryConfig()
        self.circuit_config = circuit_config or CircuitBreakerConfig()
        self.timeout = timeout
        
        # Connection management
        self.connection_limits = connection_limits or httpx.Limits(
            max_connections=50,
            max_keepalive_connections=20
        )
        
        # Health monitoring
        self.endpoint_health: Dict[str, EndpointHealth] = {}
        self.health_check_task: Optional[asyncio.Task] = None
        
        # HTTP client
        self.client: Optional[httpx.AsyncClient] = None
        self._client_lock = asyncio.Lock()
        
        # Metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.circuit_opened_count = 0
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
    
    async def start(self):
        """Start the resilient client"""
        async with self._client_lock:
            if not self.client:
                self.client = httpx.AsyncClient(
                    timeout=self.timeout,
                    limits=self.connection_limits
                )
        
        # Start health check background task
        if not self.health_check_task:
            self.health_check_task = asyncio.create_task(self._health_check_loop())
        
        logger.info("🌐 Network resilient client started")
    
    async def stop(self):
        """Stop the resilient client"""
        # Stop health check task
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
            self.health_check_task = None
        
        # Close HTTP client
        async with self._client_lock:
            if self.client:
                await self.client.aclose()
                self.client = None
        
        logger.info("🌐 Network resilient client stopped")
    
    def _get_endpoint_health(self, endpoint: str) -> EndpointHealth:
        """Get or create health tracking for endpoint"""
        if endpoint not in self.endpoint_health:
            self.endpoint_health[endpoint] = EndpointHealth(endpoint=endpoint)
        return self.endpoint_health[endpoint]
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter"""
        delay = min(
            self.retry_config.base_delay * (self.retry_config.backoff_multiplier ** attempt),
            self.retry_config.max_delay
        )
        
        # Add jitter to prevent thundering herd
        jitter = delay * self.retry_config.jitter_range * (random.random() * 2 - 1)
        return max(0, delay + jitter)
    
    def _should_circuit_be_open(self, health: EndpointHealth) -> bool:
        """Check if circuit should be opened"""
        return (
            health.consecutive_failures >= self.circuit_config.failure_threshold and
            health.circuit_state == CircuitState.CLOSED
        )
    
    def _should_circuit_be_half_open(self, health: EndpointHealth) -> bool:
        """Check if circuit should transition to half-open"""
        return (
            health.circuit_state == CircuitState.OPEN and
            health.circuit_opened_at and
            time.time() - health.circuit_opened_at >= self.circuit_config.recovery_timeout
        )
    
    def _should_circuit_be_closed(self, health: EndpointHealth) -> bool:
        """Check if circuit should be closed"""
        return (
            health.circuit_state == CircuitState.HALF_OPEN and
            health.consecutive_successes >= self.circuit_config.success_threshold
        )
    
    def _update_circuit_state(self, health: EndpointHealth):
        """Update circuit breaker state based on health"""
        if self._should_circuit_be_open(health):
            health.circuit_state = CircuitState.OPEN
            health.circuit_opened_at = time.time()
            self.circuit_opened_count += 1
            logger.warning(f"🔴 Circuit opened for {health.endpoint} after {health.consecutive_failures} failures")
            
        elif self._should_circuit_be_half_open(health):
            health.circuit_state = CircuitState.HALF_OPEN
            health.consecutive_successes = 0
            logger.info(f"🟡 Circuit half-open for {health.endpoint}, testing recovery")
            
        elif self._should_circuit_be_closed(health):
            health.circuit_state = CircuitState.CLOSED
            health.circuit_opened_at = None
            logger.info(f"🟢 Circuit closed for {health.endpoint}, service recovered")
    
    def _record_success(self, endpoint: str, response_time: float):
        """Record successful request"""
        health = self._get_endpoint_health(endpoint)
        health.success_count += 1
        health.last_success = time.time()
        health.response_times.append(response_time)
        health.consecutive_failures = 0
        health.consecutive_successes += 1
        
        self.successful_requests += 1
        self._update_circuit_state(health)
    
    def _record_failure(self, endpoint: str, error: Exception):
        """Record failed request"""
        health = self._get_endpoint_health(endpoint)
        health.failure_count += 1
        health.last_failure = time.time()
        health.consecutive_failures += 1
        health.consecutive_successes = 0
        
        self.failed_requests += 1
        self._update_circuit_state(health)
        
        logger.warning(f"❌ Request failed to {endpoint}: {error}")
    
    async def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make a resilient HTTP request with retry logic and circuit breaker.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional httpx request arguments
            
        Returns:
            httpx.Response object
            
        Raises:
            httpx.HTTPError: If all retries fail
            CircuitBreakerError: If circuit is open
        """
        endpoint = self._extract_endpoint(url)
        health = self._get_endpoint_health(endpoint)
        
        # Check circuit breaker
        if health.circuit_state == CircuitState.OPEN:
            raise CircuitBreakerError(f"Circuit breaker open for {endpoint}")
        
        self.total_requests += 1
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # Record start time
                start_time = time.time()
                
                # Make request
                if not self.client:
                    raise RuntimeError("Client not initialized. Call start() first.")
                
                response = await self.client.request(method, url, **kwargs)
                
                # Calculate response time
                response_time = time.time() - start_time
                
                # Check for HTTP errors
                response.raise_for_status()
                
                # Record success
                self._record_success(endpoint, response_time)
                
                return response
                
            except Exception as e:
                last_exception = e
                self._record_failure(endpoint, e)
                
                # If this is the last attempt, don't wait
                if attempt == self.retry_config.max_retries:
                    break
                
                # Calculate delay and wait
                delay = self._calculate_delay(attempt)
                logger.debug(f"⏳ Retrying {method} {url} in {delay:.1f}s (attempt {attempt + 1}/{self.retry_config.max_retries})")
                await asyncio.sleep(delay)
        
        # All retries failed
        raise last_exception or RuntimeError(f"Request failed after {self.retry_config.max_retries} retries")
    
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Make a POST request"""
        return await self.request("POST", url, **kwargs)
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Make a GET request"""
        return await self.request("GET", url, **kwargs)
    
    def _extract_endpoint(self, url: str) -> str:
        """Extract base endpoint from URL"""
        try:
            parsed = httpx.URL(url)
            return f"{parsed.scheme}://{parsed.host}:{parsed.port or (443 if parsed.scheme == 'https' else 80)}"
        except Exception:
            return url
    
    async def _health_check_loop(self):
        """Background task for health checking"""
        while True:
            try:
                await asyncio.sleep(DEFAULT_HEALTH_CHECK_INTERVAL)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Health check loop error: {e}")
    
    async def _perform_health_checks(self):
        """Perform health checks on all endpoints"""
        if not self.endpoint_health:
            return
        
        tasks = []
        for endpoint in list(self.endpoint_health.keys()):
            task = asyncio.create_task(self._health_check_endpoint(endpoint))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _health_check_endpoint(self, endpoint: str):
        """Health check a specific endpoint"""
        try:
            health_url = f"{endpoint}/health"
            response = await self.get(health_url, timeout=5.0)
            
            logger.debug(f"✅ Health check passed for {endpoint}")
            
        except Exception as e:
            logger.debug(f"❌ Health check failed for {endpoint}: {e}")
    
    def get_endpoint_stats(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get statistics for an endpoint"""
        health = self.endpoint_health.get(endpoint)
        if not health:
            return None
        
        total_requests = health.success_count + health.failure_count
        success_rate = health.success_count / total_requests if total_requests > 0 else 0
        avg_response_time = sum(health.response_times) / len(health.response_times) if health.response_times else 0
        
        return {
            "endpoint": endpoint,
            "total_requests": total_requests,
            "success_count": health.success_count,
            "failure_count": health.failure_count,
            "success_rate": success_rate,
            "average_response_time": avg_response_time,
            "circuit_state": health.circuit_state.value,
            "consecutive_failures": health.consecutive_failures,
            "last_success": health.last_success,
            "last_failure": health.last_failure
        }
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall client statistics"""
        success_rate = self.successful_requests / self.total_requests if self.total_requests > 0 else 0
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "circuit_opened_count": self.circuit_opened_count,
            "active_endpoints": len(self.endpoint_health),
            "healthy_endpoints": sum(1 for h in self.endpoint_health.values() if h.circuit_state == CircuitState.CLOSED)
        }


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass


# === Convenience Functions ===

async def create_resilient_client(**kwargs) -> NetworkResilientClient:
    """Create and start a resilient network client"""
    client = NetworkResilientClient(**kwargs)
    await client.start()
    return client


def create_retry_config(
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY
) -> RetryConfig:
    """Create a retry configuration"""
    return RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay
    )


def create_circuit_config(
    failure_threshold: int = DEFAULT_CIRCUIT_FAILURE_THRESHOLD,
    recovery_timeout: float = DEFAULT_CIRCUIT_RECOVERY_TIMEOUT
) -> CircuitBreakerConfig:
    """Create a circuit breaker configuration"""
    return CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout
    ) 