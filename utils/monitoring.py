"""
Monitoring and metrics collection using Prometheus
Provides metrics for API requests, database operations, and business logic
"""

import time
from functools import wraps
from typing import Callable, Optional

from fastapi import Request, Response
from prometheus_client import (CONTENT_TYPE_LATEST, CollectorRegistry, Counter,
                               Gauge, Histogram, Info, generate_latest)
from starlette.middleware.base import BaseHTTPMiddleware

# Create registry for metrics
registry = CollectorRegistry()

# =============================================================================
# API Metrics
# =============================================================================

# Request counters
api_requests_total = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status_code"],
    registry=registry,
)

api_request_duration_seconds = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry,
)

api_request_size_bytes = Histogram(
    "api_request_size_bytes",
    "API request body size in bytes",
    ["method", "endpoint"],
    registry=registry,
)

api_response_size_bytes = Histogram(
    "api_response_size_bytes",
    "API response body size in bytes",
    ["method", "endpoint"],
    registry=registry,
)

# =============================================================================
# Database Metrics
# =============================================================================

neo4j_queries_total = Counter(
    "neo4j_queries_total",
    "Total Neo4j queries executed",
    ["query_type", "status"],
    registry=registry,
)

neo4j_query_duration_seconds = Histogram(
    "neo4j_query_duration_seconds",
    "Neo4j query duration in seconds",
    ["query_type"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry,
)

neo4j_connection_pool_size = Gauge(
    "neo4j_connection_pool_size",
    "Number of active Neo4j connections",
    registry=registry,
)

# =============================================================================
# LLM Metrics
# =============================================================================

llm_requests_total = Counter(
    "llm_requests_total",
    "Total LLM API requests",
    ["model", "operation", "status"],
    registry=registry,
)

llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration in seconds",
    ["model", "operation"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0],
    registry=registry,
)

llm_tokens_used = Counter(
    "llm_tokens_used_total",
    "Total tokens used in LLM requests",
    ["model", "token_type"],
    registry=registry,
)

# =============================================================================
# Business Logic Metrics
# =============================================================================

articles_scraped_total = Counter(
    "articles_scraped_total",
    "Total articles scraped",
    ["source", "status"],
    registry=registry,
)

entities_extracted_total = Counter(
    "entities_extracted_total",
    "Total entities extracted",
    ["entity_type"],
    registry=registry,
)

relationships_created_total = Counter(
    "relationships_created_total",
    "Total relationships created",
    ["relationship_type"],
    registry=registry,
)

pipeline_phase_duration_seconds = Histogram(
    "pipeline_phase_duration_seconds",
    "Pipeline phase duration in seconds",
    ["phase"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0],
    registry=registry,
)

queries_executed_total = Counter(
    "queries_executed_total",
    "Total GraphRAG queries executed",
    ["query_type", "status"],
    registry=registry,
)

# =============================================================================
# Cache Metrics
# =============================================================================

cache_hits_total = Counter(
    "cache_hits_total", "Total cache hits", ["cache_type"], registry=registry
)

cache_misses_total = Counter(
    "cache_misses_total", "Total cache misses", ["cache_type"], registry=registry
)

# =============================================================================
# System Metrics
# =============================================================================

app_info = Info("app", "Application information", registry=registry)

# Set app info
app_info.info(
    {"name": "startup-intelligence", "version": "1.0.0", "environment": "production"}
)


# =============================================================================
# Middleware for automatic API metrics
# =============================================================================


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically collect API metrics
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request and collect metrics

        Args:
            request: FastAPI request
            call_next: Next middleware/handler in chain

        Returns:
            Response with metrics recorded
        """
        # Skip metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)

        # Record request start time
        start_time = time.time()

        # Get request size
        request_size = int(request.headers.get("content-length", 0))

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Extract endpoint pattern (remove IDs for better aggregation)
        endpoint = self._normalize_endpoint(request.url.path)

        # Record metrics
        api_requests_total.labels(
            method=request.method, endpoint=endpoint, status_code=response.status_code
        ).inc()

        api_request_duration_seconds.labels(
            method=request.method, endpoint=endpoint
        ).observe(duration)

        if request_size > 0:
            api_request_size_bytes.labels(
                method=request.method, endpoint=endpoint
            ).observe(request_size)

        # Response size (if available)
        response_size = int(response.headers.get("content-length", 0))
        if response_size > 0:
            api_response_size_bytes.labels(
                method=request.method, endpoint=endpoint
            ).observe(response_size)

        return response

    @staticmethod
    def _normalize_endpoint(path: str) -> str:
        """
        Normalize endpoint path for better metric aggregation

        Args:
            path: Original request path

        Returns:
            Normalized path with IDs replaced by placeholders

        Example:
            /companies/123 -> /companies/{id}
            /entities/company-name/relationships -> /entities/{name}/relationships
        """
        parts = path.split("/")
        normalized = []

        for i, part in enumerate(parts):
            # Replace numeric IDs
            if part.isdigit():
                normalized.append("{id}")
            # Replace UUIDs and long alphanumeric strings
            elif len(part) > 20 and "-" in part:
                normalized.append("{uuid}")
            # Replace entity names (heuristic: after /entities/ or /companies/)
            elif i > 0 and parts[i - 1] in [
                "entities",
                "companies",
                "people",
                "investors",
            ]:
                normalized.append("{name}")
            else:
                normalized.append(part)

        return "/".join(normalized)


# =============================================================================
# Decorator for function metrics
# =============================================================================


def track_time(metric: Histogram, labels: Optional[dict] = None):
    """
    Decorator to track function execution time

    Args:
        metric: Prometheus Histogram metric
        labels: Optional labels for the metric

    Example:
        @track_time(neo4j_query_duration_seconds, {"query_type": "search"})
        def execute_search_query():
            # Query logic
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        return wrapper

    return decorator


def track_count(metric: Counter, labels: Optional[dict] = None):
    """
    Decorator to count function calls

    Args:
        metric: Prometheus Counter metric
        labels: Optional labels for the metric

    Example:
        @track_count(articles_scraped_total, {"source": "techcrunch", "status": "success"})
        def scrape_article():
            # Scraping logic
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if labels:
                    metric.labels(**labels).inc()
                else:
                    metric.inc()
                return result
            except Exception as e:
                # Increment with error status if available
                if labels and "status" in labels:
                    error_labels = labels.copy()
                    error_labels["status"] = "error"
                    metric.labels(**error_labels).inc()
                raise

        return wrapper

    return decorator


# =============================================================================
# Helper functions for manual metric recording
# =============================================================================


def record_api_request(method: str, endpoint: str, status_code: int, duration: float):
    """Record API request metrics manually"""
    api_requests_total.labels(
        method=method, endpoint=endpoint, status_code=status_code
    ).inc()

    api_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
        duration
    )


def record_neo4j_query(query_type: str, duration: float, success: bool = True):
    """Record Neo4j query metrics"""
    status = "success" if success else "error"

    neo4j_queries_total.labels(query_type=query_type, status=status).inc()

    neo4j_query_duration_seconds.labels(query_type=query_type).observe(duration)


def record_llm_request(
    model: str,
    operation: str,
    duration: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    success: bool = True,
):
    """Record LLM request metrics"""
    status = "success" if success else "error"

    llm_requests_total.labels(model=model, operation=operation, status=status).inc()

    llm_request_duration_seconds.labels(model=model, operation=operation).observe(
        duration
    )

    if prompt_tokens > 0:
        llm_tokens_used.labels(model=model, token_type="prompt").inc(prompt_tokens)

    if completion_tokens > 0:
        llm_tokens_used.labels(model=model, token_type="completion").inc(
            completion_tokens
        )


def record_entity_extraction(entity_type: str, count: int = 1):
    """Record entity extraction"""
    entities_extracted_total.labels(entity_type=entity_type).inc(count)


def record_relationship_creation(relationship_type: str, count: int = 1):
    """Record relationship creation"""
    relationships_created_total.labels(relationship_type=relationship_type).inc(count)


def record_pipeline_phase(phase: str, duration: float):
    """Record pipeline phase execution"""
    pipeline_phase_duration_seconds.labels(phase=phase).observe(duration)


def record_query_execution(query_type: str, success: bool = True):
    """Record GraphRAG query execution"""
    status = "success" if success else "error"
    queries_executed_total.labels(query_type=query_type, status=status).inc()


def record_cache_operation(cache_type: str, hit: bool):
    """Record cache hit/miss"""
    if hit:
        cache_hits_total.labels(cache_type=cache_type).inc()
    else:
        cache_misses_total.labels(cache_type=cache_type).inc()


def get_metrics() -> bytes:
    """
    Get all metrics in Prometheus format

    Returns:
        Metrics in Prometheus text format

    Usage:
        @app.get("/metrics")
        async def metrics():
            return Response(content=get_metrics(), media_type=CONTENT_TYPE_LATEST)
    """
    return generate_latest(registry)


def get_metrics_content_type() -> str:
    """Get Prometheus metrics content type"""
    return CONTENT_TYPE_LATEST
