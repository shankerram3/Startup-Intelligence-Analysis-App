"""
FastAPI REST API for GraphRAG Query System
Provides HTTP endpoints for querying the knowledge graph

Version 2.0.0 - Enhanced with:
- Structured logging
- Authentication & authorization
- Rate limiting
- Caching
- Prometheus metrics
- Security improvements
"""

import asyncio
import io
import os
import subprocess
import sys
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response, FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from query_templates import QueryTemplates
from rag_query import GraphRAGQuery, create_rag_query
from utils.cache import EntityCache, QueryCache, async_cached, get_cache

# Import new utility modules
from utils.logging_config import get_logger, setup_logging
from utils.analytics import (
    get_analytics_summary,
    get_recent_calls,
    track_api_call,
    track_openai_call,
    track_query_execution as track_query_exec,
)
from utils.monitoring import (
    PrometheusMiddleware,
    get_metrics,
    get_metrics_content_type,
    record_cache_operation,
    record_query_execution,
)
from utils.security import (
    SecurityConfig,
    optional_auth,
    require_api_key,
    sanitize_error_message,
    verify_token,
)
from utils.evaluation import (
    QueryEvaluator,
    create_sample_evaluation_dataset,
    EvaluationSummary,
    QueryEvaluationResult,
)

# Load environment variables
load_dotenv()

# Initialize structured logging
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    json_logs=os.getenv("JSON_LOGS", "true").lower() == "true",
    log_file=(
        Path("logs/api.log") if os.getenv("ENABLE_FILE_LOGGING") == "true" else None
    ),
)

# Get logger for this module
logger = get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize cache
cache = get_cache()

# Global RAG instance
rag_instance = None


# =============================================================================
# PYDANTIC MODELS (Request/Response schemas)
# =============================================================================


class QueryRequest(BaseModel):
    """Request model for main query endpoint"""

    question: str = Field(..., description="Natural language question", min_length=3)
    return_context: bool = Field(False, description="Include raw context in response")
    use_llm: bool = Field(True, description="Generate LLM answer")
    return_traversal: bool = Field(False, description="Include graph traversal data for visualization")

    model_config = ConfigDict(
        json_schema_extra={
        "example": {
            "question": "Which AI startups raised funding recently?",
            "return_context": False,
                "use_llm": True,
                "return_traversal": False,
        }
        }
    )


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search"""

    query: str = Field(..., description="Search query", min_length=2)
    top_k: int = Field(10, description="Number of results", ge=1, le=50)
    entity_type: Optional[str] = Field(None, description="Filter by entity type")

    model_config = ConfigDict(
        json_schema_extra={
        "example": {
            "query": "artificial intelligence",
            "top_k": 10,
                "entity_type": "Company",
        }
        }
    )


class CompareEntitiesRequest(BaseModel):
    """Request model for entity comparison"""

    entity1: str = Field(..., description="First entity name")
    entity2: str = Field(..., description="Second entity name")

    model_config = ConfigDict(
        json_schema_extra={"example": {"entity1": "Anthropic", "entity2": "OpenAI"}}
    )


class BatchQueryRequest(BaseModel):
    """Request model for batch queries"""

    questions: List[str] = Field(
        ..., description="List of questions", min_length=1, max_length=10
    )

    model_config = ConfigDict(
        json_schema_extra={
        "example": {
            "questions": [
                "What is Anthropic?",
                "Who are the top investors?",
                    "What are trending technologies?",
            ]
        }
        }
    )


class QueryResponse(BaseModel):
    """Response model for query results"""

    question: str
    intent: Dict[str, Any]
    answer: Optional[str]
    context: Optional[Any] = None
    traversal: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response model"""

    error: str
    detail: Optional[str] = None


# =============================================================================
# ADMIN / PIPELINE CONTROL MODELS
# =============================================================================


class PipelineStartRequest(BaseModel):
    """Options for starting the pipeline"""

    scrape_category: Optional[str] = Field(
        None, description="TechCrunch category to scrape (e.g., 'startups', 'ai')"
    )
    scrape_max_pages: Optional[int] = Field(
        None, description="Max pages to scrape", ge=1
    )
    max_articles: Optional[int] = Field(
        None, description="Limit number of articles", ge=1
    )
    skip_scraping: bool = Field(False, description="Skip scraping phase")
    skip_extraction: bool = Field(False, description="Skip entity extraction phase")
    skip_graph: bool = Field(False, description="Skip graph construction phase")
    no_resume: bool = Field(False, description="Do not resume from checkpoints")
    enable_debug_logs: bool = Field(False, description="Enable DEBUG level logging for detailed troubleshooting")


# =============================================================================
# LIFESPAN CONTEXT MANAGER
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan (startup/shutdown)"""
    global rag_instance

    # Startup
    logger.info("api_starting", version="2.0.0")

    try:
        rag_instance = create_rag_query()
        logger.info("rag_instance_initialized", status="success")

        # Log cache status
        cache_stats = cache.get_stats()
        logger.info("cache_initialized", **cache_stats)

    except Exception as e:
        logger.error("rag_initialization_failed", error=str(e), exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("api_shutting_down")
    if rag_instance:
        rag_instance.close()
        logger.info("rag_instance_closed", status="success")


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="GraphRAG API",
    description="REST API for TechCrunch Knowledge Graph Query System with Security & Monitoring",
    version="2.0.0",
    lifespan=lifespan,
)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Add request size limiting middleware
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    """Limit request body size to prevent DoS"""
    content_length = request.headers.get("content-length")
    if content_length:
        content_length = int(content_length)
        if content_length > SecurityConfig.MAX_REQUEST_SIZE:
            logger.warning(
                "request_too_large",
                size=content_length,
                max_size=SecurityConfig.MAX_REQUEST_SIZE,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=413,
                content={
                    "detail": f"Request body too large. Maximum size: {SecurityConfig.MAX_REQUEST_SIZE} bytes"
                },
            )

    response = await call_next(request)
    return response


# Add Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware)

# Add Gzip compression for responses > 1KB (reduces response size by 70-90%)
app.add_middleware(GZipMiddleware, minimum_size=1000)



# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # HSTS - Force HTTPS (1 year, include subdomains)
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains; preload"
    )
    
    # Content Security Policy - Restrict resource loading
    # Note: connect-src allows https: connections, enabling Vercel frontend to connect
    # Frontend is served separately from Vercel, this backend only serves API endpoints
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Allow inline for frontend
        "style-src 'self' 'unsafe-inline'; "  # Allow inline styles
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https:; "  # Allows Vercel frontend and other HTTPS APIs
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    response.headers["Content-Security-Policy"] = csp_policy
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # XSS Protection (legacy, but still useful)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Permissions Policy (formerly Feature-Policy)
    response.headers["Permissions-Policy"] = (
        "geolocation=(), " "microphone=(), " "camera=(), " "payment=(), " "usb=()"
    )
    
    return response


# Custom CORS middleware that handles both explicit origins and Vercel preview deployments
# This replaces CORSMiddleware to support wildcard matching for Vercel previews
class CustomCORSMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware that handles explicit origins and Vercel preview deployments
    """
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        # Handle OPTIONS preflight requests
        if request.method == "OPTIONS":
            # If no origin header, allow the request (same-origin requests don't send origin)
            if not origin:
                return Response(
                    status_code=200,
                    headers={
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Request-ID, Accept",
                        "Access-Control-Max-Age": "600",
                    },
                )
            
            # Check if origin is explicitly allowed
            if origin in SecurityConfig.ALLOWED_ORIGINS:
                return Response(
                    status_code=200,
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Request-ID, Accept",
                        "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Max-Age": "600",
                    },
                )
            
            # Allow Vercel preview deployments only if they start with configured project name prefix
            # This ensures only previews from the same project are allowed, not all *.vercel.app domains
            if origin.endswith(".vercel.app") and SecurityConfig._VERCEL_PREVIEW_PATTERN_ENABLED:
                # Extract project name from preview domain using same logic as configuration
                try:
                    domain = origin.replace("https://", "").replace("http://", "").split("/")[0]
                    if domain.endswith(".vercel.app"):
                        preview_base_name = domain.replace(".vercel.app", "")
                        # Extract project name from preview domain
                        request_project_name = preview_base_name
                        if "-projects" in request_project_name:
                            request_project_name = request_project_name.rsplit("-projects", 1)[0]
                            parts = request_project_name.split("-")
                            # Remove username
                            if len(parts) > 1:
                                last = parts[-1]
                                if len(last) >= 5 and len(last) <= 20 and last.replace("-", "").replace("_", "").isalnum():
                                    parts.pop()
                                request_project_name = "-".join(parts)
                            # Remove hash
                            parts = request_project_name.split("-")
                            if len(parts) > 1:
                                last = parts[-1]
                                if len(last) >= 6 and len(last) <= 12 and last.isalnum():
                                    parts.pop()
                                request_project_name = "-".join(parts)
                        # Remove -git- pattern
                        if "-git-" in request_project_name:
                            request_project_name = request_project_name.split("-git-")[0]
                        elif request_project_name.endswith("-git"):
                            request_project_name = request_project_name[:-4]
                        
                        # Check if extracted project name matches any configured project prefix
                        for project_prefix in SecurityConfig._VERCEL_PROJECT_PREFIXES:
                            if request_project_name == project_prefix or preview_base_name.startswith(project_prefix + "-"):
                                return Response(
                                    status_code=200,
                                    headers={
                                        "Access-Control-Allow-Origin": origin,
                                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                                        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Request-ID, Accept",
                                        "Access-Control-Allow-Credentials": "true",
                                        "Access-Control-Max-Age": "600",
                                    },
                                )
                except Exception:
                    pass  # If parsing fails, deny access
            
            # If origin not allowed, return 403
            return Response(status_code=403, content="CORS not allowed")
        
        # For non-OPTIONS requests, check origin first before processing request
        # This ensures consistent 403 status for disallowed origins (same as OPTIONS)
        if origin:
            # Check if origin is explicitly allowed
            origin_allowed = origin in SecurityConfig.ALLOWED_ORIGINS
            
            # If not explicitly allowed, check Vercel preview pattern
            if not origin_allowed and origin.endswith(".vercel.app") and SecurityConfig._VERCEL_PREVIEW_PATTERN_ENABLED:
                try:
                    domain = origin.replace("https://", "").replace("http://", "").split("/")[0]
                    if domain.endswith(".vercel.app"):
                        preview_base_name = domain.replace(".vercel.app", "")
                        # Extract project name from preview domain using same logic as configuration
                        request_project_name = preview_base_name
                        if "-projects" in request_project_name:
                            request_project_name = request_project_name.rsplit("-projects", 1)[0]
                            parts = request_project_name.split("-")
                            # Remove username
                            if len(parts) > 1:
                                last = parts[-1]
                                if len(last) >= 5 and len(last) <= 20 and last.replace("-", "").replace("_", "").isalnum():
                                    parts.pop()
                                request_project_name = "-".join(parts)
                            # Remove hash
                            parts = request_project_name.split("-")
                            if len(parts) > 1:
                                last = parts[-1]
                                if len(last) >= 6 and len(last) <= 12 and last.isalnum():
                                    parts.pop()
                                request_project_name = "-".join(parts)
                        # Remove -git- pattern
                        if "-git-" in request_project_name:
                            request_project_name = request_project_name.split("-git-")[0]
                        elif request_project_name.endswith("-git"):
                            request_project_name = request_project_name[:-4]
                        
                        # Check if extracted project name matches any configured project prefix
                        for project_prefix in SecurityConfig._VERCEL_PROJECT_PREFIXES:
                            if request_project_name == project_prefix or preview_base_name.startswith(project_prefix + "-"):
                                origin_allowed = True
                                break
                except Exception:
                    pass  # If parsing fails, deny access
            
            # If origin not allowed, return 403 before processing request (consistent with OPTIONS)
            if not origin_allowed:
                return Response(status_code=403, content="CORS not allowed")
        
        # Process request and add CORS headers for allowed origins
        response = await call_next(request)
        
        # Add CORS headers if origin is present and was validated above
        if origin:
            # Origin was already validated above, so it's safe to add headers
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response

# Add custom CORS middleware (replaces CORSMiddleware to support Vercel previews)
app.add_middleware(CustomCORSMiddleware)


# =============================================================================
# HEALTH CHECK
# =============================================================================


@app.get("/health", tags=["Health"])
async def health():
    """Detailed health check with component status"""
    if not rag_instance:
        logger.error("health_check_failed", reason="rag_not_initialized")
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        # Test database connection
        stats = rag_instance.query_templates.get_graph_statistics()

        health_status = {
            "status": "healthy",
            "version": "2.0.0",
            "components": {
                "database": "connected",
                "cache": "enabled" if cache.enabled else "disabled",
                "authentication": (
                    "enabled" if SecurityConfig.ENABLE_AUTH else "disabled"
                ),
                "rate_limiting": (
                    "enabled" if SecurityConfig.ENABLE_RATE_LIMITING else "disabled"
                ),
            },
            "graph_stats": stats,
        }

        logger.info("health_check_success", **health_status)
        return health_status

    except Exception as e:
        logger.error("health_check_failed", error=str(e), exc_info=True)
        error_msg = sanitize_error_message(e, include_details=False)
        raise HTTPException(status_code=503, detail=error_msg)


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    Prometheus metrics endpoint

    Returns metrics in Prometheus text format for scraping
    """
    return Response(content=get_metrics(), media_type=get_metrics_content_type())


def _parse_pipeline_logs_for_stats() -> Dict[str, Any]:
    """Parse pipeline logs to extract statistics"""
    import json
    import re
    from datetime import datetime
    
    stats = {
        "total_runs": 0,
        "total_articles_scraped": 0,
        "total_articles_extracted": 0,
        "total_entities_extracted": 0,
        "total_relationships_created": 0,
        "total_companies_enriched": 0,
        "runs_by_phase": {},
        "last_run": None,
    }
    
    if not os.path.exists(pipeline_log_path):
        return stats
    
    try:
        with open(pipeline_log_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        # Parse JSON log lines
        lines = content.splitlines()
        pipeline_starts = 0
        last_scraping_stats = {}
        last_extraction_stats = {}
        last_enrichment_stats = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            try:
                # Try to parse as JSON log
                if line.startswith("{") or '"event"' in line:
                    log_entry = json.loads(line)
                    event = log_entry.get("event", "")
                    
                    if event == "pipeline_starting":
                        pipeline_starts += 1
                        stats["total_runs"] = pipeline_starts
                        stats["last_run"] = {
                            "timestamp": log_entry.get("timestamp"),
                            "phase": "starting"
                        }
                    
                    elif event == "scraping_articles_discovered":
                        count = log_entry.get("count", 0)
                        last_scraping_stats["articles_discovered"] = count
                    
                    elif event == "scraping_complete":
                        articles_extracted = log_entry.get("articles_extracted", 0)
                        stats["total_articles_scraped"] += articles_extracted
                        last_scraping_stats["articles_extracted"] = articles_extracted
                    
                    elif event == "extraction_complete" or event == "pipeline_phase_starting":
                        phase = log_entry.get("phase", "")
                        if phase == "1" and "name" in log_entry:
                            last_extraction_stats["phase"] = "extraction"
                            # Capture articles_extracted count if present
                            if "articles_extracted" in log_entry:
                                last_extraction_stats["articles_extracted"] = log_entry.get("articles_extracted", 0)
                    
                    elif event == "enrichment_complete":
                        # Use explicit None checking to avoid issues when value is 0
                        companies_scraped = log_entry.get("companies_scraped")
                        if companies_scraped is not None:
                            companies = companies_scraped
                        else:
                            companies = log_entry.get("total_companies", 0)
                        last_enrichment_stats["companies"] = companies
                        stats["total_companies_enriched"] += companies
                        
            except (json.JSONDecodeError, KeyError):
                # Not JSON, try regex patterns for plain text logs
                if "articles discovered" in line.lower() or "articles_discovered" in line.lower():
                    match = re.search(r'count[":\s]+(\d+)', line, re.IGNORECASE)
                    if match:
                        last_scraping_stats["articles_discovered"] = int(match.group(1))
                
                if "articles extracted" in line.lower() or "articles_extracted" in line.lower():
                    match = re.search(r'articles_extracted[":\s]+(\d+)', line, re.IGNORECASE)
                    if match:
                        count = int(match.group(1))
                        # Check if this is in extraction phase context BEFORE incrementing stats
                        # Only count as extracted if it's from the extraction phase, not scraping
                        if "extraction" in line.lower() or "phase" in line.lower() or last_extraction_stats.get("phase") == "extraction":
                            # This is from extraction phase - count as extracted
                            stats["total_articles_extracted"] += count
                            last_extraction_stats["articles_extracted"] = count
                        else:
                            # This is from scraping phase - count as scraped, not extracted
                            # Note: articles_scraped may already be counted elsewhere, so we only update last_scraping_stats
                            last_scraping_stats["articles_extracted"] = count
                            # Don't increment total_articles_extracted for scraping phase articles
                
                # Also check for "New articles processed" pattern from entity_extractor
                if "new articles processed" in line.lower():
                    match = re.search(r'new articles processed.*?:\s*(\d+)', line, re.IGNORECASE)
                    if match:
                        count = int(match.group(1))
                        # This is from extraction phase - increment total and update tracking
                        stats["total_articles_extracted"] += count
                        last_extraction_stats["articles_extracted"] = count
                
                if "entities extracted" in line.lower():
                    match = re.search(r'(\d+)\s+entities', line, re.IGNORECASE)
                    if match:
                        stats["total_entities_extracted"] += int(match.group(1))
        
        # Update last run with collected stats
        if stats["last_run"]:
            stats["last_run"].update({
                "articles_scraped": last_scraping_stats.get("articles_extracted", 0),
                "articles_extracted": last_extraction_stats.get("articles_extracted", 0),
                "companies_enriched": last_enrichment_stats.get("companies", 0),
            })
        
    except Exception as e:
        logger.warning("pipeline_stats_parse_failed", error=str(e))
    
    return stats


@app.get("/analytics/dashboard", tags=["Analytics"])
async def get_analytics_dashboard(
    hours: int = Query(24, ge=1, le=168, description="Time period in hours (max 7 days)"),
    group_by: str = Query("hour", description="Group by: hour, day, or minute")
):
    """
    Get analytics dashboard data including API calls, OpenAI usage, and system metrics
    
    Returns:
    - Time series data for the specified period
    - Endpoint breakdown
    - OpenAI model and operation breakdown
    - Pipeline statistics (scraping, extraction, etc.)
    - Summary statistics
    """
    try:
        summary = get_analytics_summary(hours=hours, group_by=group_by)
        
        # Add pipeline statistics
        pipeline_stats = _parse_pipeline_logs_for_stats()
        summary["pipeline_stats"] = pipeline_stats
        
        return summary
    except Exception as e:
        logger.error("analytics_dashboard_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analytics: {sanitize_error_message(str(e))}"
        )


@app.get("/analytics/recent-calls", tags=["Analytics"])
async def get_recent_calls_endpoint(
    limit: int = Query(100, ge=1, le=1000, description="Number of recent calls to return"),
    call_type: Optional[str] = Query(None, description="Filter by type: api_call, openai_call, neo4j_query, query_execution")
):
    """Get recent API/OpenAI calls for detailed inspection"""
    try:
        calls = get_recent_calls(limit=limit, call_type=call_type)
        return {"calls": calls, "count": len(calls)}
    except Exception as e:
        logger.error("recent_calls_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recent calls: {sanitize_error_message(str(e))}"
        )


# =============================================================================
# EVALUATION ENDPOINTS
# =============================================================================


class EvaluationRequest(BaseModel):
    """Request model for evaluation"""
    queries: List[Dict[str, Any]] = Field(
        ...,
        description="List of queries to evaluate. Each query should have 'query' and optionally 'expected_answer'"
    )
    use_llm: bool = Field(True, description="Whether to use LLM for answer generation")
    use_sample_dataset: bool = Field(
        False, 
        description="If true, use built-in sample dataset instead of provided queries"
    )


@app.post("/evaluation/run", tags=["Evaluation"])
async def run_evaluation(
    request: EvaluationRequest,
    user: Optional[Dict] = Depends(optional_auth),
):
    """
    Run evaluation metrics on a set of queries
    
    Evaluates:
    - Query performance (latency, throughput)
    - Response quality (relevance, accuracy, completeness, coherence)
    - RAG metrics (context relevance, answer faithfulness, answer relevancy)
    - System metrics (cache hit rate, error rate)
    """
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")
    
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        evaluator = QueryEvaluator(rag_instance=rag_instance, openai_api_key=openai_api_key)
        
        # Use sample dataset if requested
        if request.use_sample_dataset:
            queries = create_sample_evaluation_dataset()
        else:
            queries = request.queries
        
        # Run evaluation
        summary = evaluator.evaluate_batch(queries, use_llm=request.use_llm)
        
        # Convert to dict for JSON serialization
        result = {
            "summary": {
                "total_queries": summary.total_queries,
                "successful_queries": summary.successful_queries,
                "failed_queries": summary.failed_queries,
                "avg_latency_ms": round(summary.avg_latency_ms, 2),
                "p50_latency_ms": round(summary.p50_latency_ms, 2),
                "p95_latency_ms": round(summary.p95_latency_ms, 2),
                "p99_latency_ms": round(summary.p99_latency_ms, 2),
                "total_tokens": summary.total_tokens,
                "total_cost_usd": round(summary.total_cost_usd, 4),
                "avg_relevance": round(summary.avg_relevance, 3),
                "avg_accuracy": round(summary.avg_accuracy, 3),
                "avg_completeness": round(summary.avg_completeness, 3),
                "avg_coherence": round(summary.avg_coherence, 3),
                "avg_context_relevance": round(summary.avg_context_relevance, 3),
                "avg_answer_faithfulness": round(summary.avg_answer_faithfulness, 3),
                "avg_answer_relevancy": round(summary.avg_answer_relevancy, 3),
                "cache_hit_rate": round(summary.cache_hit_rate, 3),
                "error_rate": round(summary.error_rate, 3),
            },
            "results": [
                {
                    "query": r.query,
                    "expected_answer": r.expected_answer,
                    "actual_answer": r.actual_answer,
                    "latency_ms": round(r.latency_ms, 2),
                    "tokens_used": r.tokens_used,
                    "cost_usd": round(r.cost_usd, 4),
                    "relevance_score": round(r.relevance_score, 3),
                    "accuracy_score": round(r.accuracy_score, 3),
                    "completeness_score": round(r.completeness_score, 3),
                    "coherence_score": round(r.coherence_score, 3),
                    "context_relevance": round(r.context_relevance, 3),
                    "answer_faithfulness": round(r.answer_faithfulness, 3),
                    "answer_relevancy": round(r.answer_relevancy, 3),
                    "cache_hit": r.cache_hit,
                    "success": r.success,
                    "error": r.error,
                    "timestamp": r.timestamp,
                    "logs": r.logs,
                    "calculation_details": r.calculation_details,
                    "intent_classified": r.intent_classified,
                    "context_size": r.context_size,
                    "context_entities": r.context_entities,
                }
                for r in summary.results
            ]
        }
        
        logger.info(
            "evaluation_completed",
            total_queries=summary.total_queries,
            success_rate=1 - summary.error_rate,
            avg_latency_ms=summary.avg_latency_ms
        )
        
        return result
        
    except Exception as e:
        logger.error("evaluation_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run evaluation: {sanitize_error_message(str(e))}"
        )


@app.get("/evaluation/sample-dataset", tags=["Evaluation"])
async def get_sample_dataset():
    """Get the sample evaluation dataset"""
    return {"queries": create_sample_evaluation_dataset()}


@app.get("/admin/status", tags=["Admin"])
async def get_system_status():
    """
    Get detailed system status including all components

    Returns:
        Comprehensive system status
    """
    status = {
        "api_version": "2.0.0",
        "rag_initialized": rag_instance is not None,
        "cache": cache.get_stats(),
        "security": {
            "authentication_enabled": SecurityConfig.ENABLE_AUTH,
            "rate_limiting_enabled": SecurityConfig.ENABLE_RATE_LIMITING,
            "max_request_size": SecurityConfig.MAX_REQUEST_SIZE,
            "allowed_origins": SecurityConfig.ALLOWED_ORIGINS,
        },
    }

    if rag_instance:
        try:
            status["graph_stats"] = rag_instance.query_templates.get_graph_statistics()
        except Exception as e:
            status["graph_stats"] = {"error": str(e)}

    logger.info("system_status_requested", **status)
    return status


# =============================================================================
# NEO4J ADMIN / AURADB OVERVIEW
# =============================================================================


def _run_neo4j_metadata_queries(driver) -> Dict[str, Any]:
    """Helper function to run blocking Neo4j metadata queries (runs in thread pool)"""
    db_info: Dict[str, Any] = {"components": []}
    labels: List[str] = []
    rel_types: List[str] = []
    
    # Run best-effort metadata queries (Aura may restrict some procedures)
    with driver.session() as session:
        try:
            comp = session.run(
                "CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition"
            )
            db_info["components"] = [dict(r) for r in comp]
        except Exception:
            db_info["components"] = []
        try:
            labs = session.run(
                "CALL db.labels() YIELD label RETURN label ORDER BY label"
            )
            labels = [r["label"] for r in labs]
        except Exception:
            labels = []
        try:
            rels = session.run(
                "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType"
            )
            rel_types = [r["relationshipType"] for r in rels]
        except Exception:
            rel_types = []
    
    return {"db_info": db_info, "labels": labels, "rel_types": rel_types}


@async_cached(ttl=1800, key_prefix="neo4j_overview")  # Cache for 30 minutes
async def _get_neo4j_overview_data() -> Dict[str, Any]:
    """Internal function to fetch Neo4j overview data (cached)"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")
    
    # Run all blocking Neo4j operations in thread pool to avoid blocking event loop
    # These operations are I/O bound and safe to run in threads
    stats = await asyncio.to_thread(rag_instance.query_templates.get_graph_statistics)
    
    # Run metadata queries in thread pool
    metadata_result = await asyncio.to_thread(_run_neo4j_metadata_queries, rag_instance.driver)
    db_info = metadata_result["db_info"]
    labels = metadata_result["labels"]
    rel_types = metadata_result["rel_types"]
    
    # Top entities (also blocking, run in thread pool)
    top_connected = []
    top_important = []
    try:
        top_connected = await asyncio.to_thread(
            rag_instance.query_templates.get_most_connected_entities,
            limit=10
        )
    except Exception:
        top_connected = []
    try:
        top_important = await asyncio.to_thread(
            rag_instance.query_templates.get_entity_importance_scores,
            limit=10
        )
    except Exception:
        top_important = []

    return {
        "status": "ok",
        "db_info": db_info,
        "labels": labels,
        "relationship_types": rel_types,
        "graph_stats": stats,
        "top_connected_entities": top_connected,
        "top_important_entities": top_important,
    }


@app.get("/admin/neo4j/overview", tags=["Admin", "Neo4j"])
async def neo4j_overview() -> Dict[str, Any]:
    """
    Return an overview of the connected Neo4j (AuraDB) instance:
    - dbms components (version/edition) when available
    - labels, relationship types
    - node/relationship counts, community count
    - top entities by connectivity and importance
    
    Results are cached for 30 minutes to improve performance.
    """
    try:
        return await _get_neo4j_overview_data()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch Neo4j overview: {e}"
        )


# =============================================================================
# ADMIN / PIPELINE CONTROL ENDPOINTS
# =============================================================================

# Simple in-process state for a single pipeline run
pipeline_proc: Optional[subprocess.Popen] = None
pipeline_log_path: str = os.getenv("PIPELINE_LOG_PATH", "pipeline.log")


def _build_pipeline_args(options: PipelineStartRequest) -> List[str]:
    # Use unbuffered python so stdout flushes to the log file immediately
    args: List[str] = ["python", "-u", "pipeline.py"]
    if options.scrape_category:
        args += ["--scrape-category", options.scrape_category]
    if options.scrape_max_pages:
        args += ["--scrape-max-pages", str(options.scrape_max_pages)]
    if options.max_articles:
        args += ["--max-articles", str(options.max_articles)]
    if options.skip_scraping:
        args.append("--skip-scraping")
    if options.skip_extraction:
        args.append("--skip-extraction")
    if options.skip_graph:
        args.append("--skip-graph")
    if options.no_resume:
        args.append("--no-resume")
    return args


@app.post("/admin/pipeline/start", tags=["Admin"])
async def start_pipeline(options: PipelineStartRequest):
    """Start the ETL pipeline as a background process"""
    global pipeline_proc
    if pipeline_proc and pipeline_proc.poll() is None:
        raise HTTPException(status_code=409, detail="Pipeline is already running")

    args = _build_pipeline_args(options)
    
    # Clear log file before starting new pipeline run
    # Use binary mode to match how subprocess writes to the file
    if os.path.exists(pipeline_log_path):
        with open(pipeline_log_path, "wb") as f:
            f.write(b"")
    
    # Prepare environment variables for subprocess
    # Inherit current environment and override LOG_LEVEL if debug is enabled
    env = os.environ.copy()
    if options.enable_debug_logs:
        env["LOG_LEVEL"] = "DEBUG"
        logger.info("pipeline_starting_with_debug", pid=None, args=args)
    else:
        # Ensure LOG_LEVEL is set (default to INFO if not set)
        if "LOG_LEVEL" not in env:
            env["LOG_LEVEL"] = "INFO"
    
    # Open log file in append mode for the new run
    # Move open() inside try block to ensure file errors are caught and converted to HTTP 500
    log_fh = None
    try:
        log_fh = open(pipeline_log_path, "ab")
        # start_new_session is Unix/Linux only - conditionally apply based on platform
        # On Windows, this parameter would raise ValueError
        popen_kwargs = {
            "args": args,
            "stdout": log_fh,
            "stderr": subprocess.STDOUT,
            "cwd": os.getcwd(),
            "env": env,
        }
        # Only use start_new_session on Unix/Linux systems (not Windows)
        if sys.platform != "win32":
            popen_kwargs["start_new_session"] = True  # Start in new session to survive parent termination
        pipeline_proc = subprocess.Popen(**popen_kwargs)
        # Close the file handle in parent process after Popen inherits it
        # The subprocess will keep the file open until it exits
        log_fh.close()
        log_fh = None  # Mark as closed to avoid closing again in exception handler
        logger.info(
            "pipeline_started",
            pid=pipeline_proc.pid,
            args=args,
            debug_logs=options.enable_debug_logs
        )
        return {
            "status": "started",
            "pid": pipeline_proc.pid,
            "args": args,
            "log": pipeline_log_path,
            "debug_logs": options.enable_debug_logs,
        }
    except Exception as e:
        # Close file handle if it was opened but Popen failed
        if log_fh is not None:
            try:
                log_fh.close()
            except Exception:
                pass  # Ignore errors when closing failed file handle
        logger.error("pipeline_start_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {e}")


@app.get("/admin/pipeline/status", tags=["Admin"])
async def pipeline_status():
    """Get current pipeline process status"""
    global pipeline_proc
    try:
        if not pipeline_proc:
            return {"running": False}
        
        # Use asyncio timeout to prevent hanging
        try:
            # Run poll() in executor to avoid blocking, with timeout
            # Use get_running_loop() instead of get_event_loop() for Python 3.10+ compatibility
            loop = asyncio.get_running_loop()
            code = await asyncio.wait_for(
                loop.run_in_executor(None, pipeline_proc.poll),
                timeout=1.0  # 1 second max for poll()
            )
            # Get PID safely
            try:
                pid = pipeline_proc.pid
            except (AttributeError, ProcessLookupError):
                pid = None
            
            return {"running": code is None, "pid": pid, "returncode": code}
        except asyncio.TimeoutError:
            # Poll() took too long - process might be in bad state
            logger.warning("pipeline_status_poll_timeout", pid=getattr(pipeline_proc, 'pid', None))
            # Return safe default - assume not running if we can't check
            return {"running": False, "error": "Status check timeout"}
        except (ProcessLookupError, ValueError) as e:
            # Process no longer exists - might have been killed by container/system
            logger.warning("pipeline_process_not_found", error=str(e), pid=getattr(pipeline_proc, 'pid', None))
            pipeline_proc = None
            return {"running": False, "error": "Process no longer exists (may have been killed)"}
        except OSError as e:
            # Process lookup failed - process was killed or container restarted
            logger.warning("pipeline_process_os_error", error=str(e), pid=getattr(pipeline_proc, 'pid', None))
            pipeline_proc = None
            return {"running": False, "error": f"Process error: {str(e)}"}
            
    except Exception as e:
        logger.error("pipeline_status_error", error=str(e), exc_info=True)
        # Return safe default on error to prevent timeouts
        return {"running": False, "error": str(e)}


@app.post("/admin/pipeline/stop", tags=["Admin"])
async def stop_pipeline():
    """Terminate the pipeline process if running"""
    global pipeline_proc
    if not pipeline_proc or pipeline_proc.poll() is not None:
        raise HTTPException(status_code=409, detail="Pipeline is not running")
    try:
        pipeline_proc.terminate()
        try:
            pipeline_proc.wait(timeout=10)
        except Exception:
            pipeline_proc.kill()
        return {"status": "stopped"}
    finally:
        pipeline_proc = None


@app.get("/admin/pipeline/logs", tags=["Admin"])
async def pipeline_logs(tail: int = Query(200, ge=1, le=5000)):
    """Return the last N lines of the pipeline log"""
    if not os.path.exists(pipeline_log_path):
        return {"log": "(no logs)"}
    try:
        with open(pipeline_log_path, "rb") as f:
            content = f.read()
        lines = content.splitlines()[-tail:]
        text = b"\n".join(lines).decode(errors="replace")
        return {"log": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {e}")


@app.post("/admin/pipeline/logs/clear", tags=["Admin"])
async def clear_pipeline_logs():
    """Clear the pipeline log file"""
    global pipeline_proc
    # Don't allow clearing logs if pipeline is currently running
    if pipeline_proc and pipeline_proc.poll() is None:
        raise HTTPException(
            status_code=409, detail="Cannot clear logs while pipeline is running"
        )
    
    try:
        # Clear the log file by truncating it
        if os.path.exists(pipeline_log_path):
            with open(pipeline_log_path, "w") as f:
                f.write("")
        return {"status": "cleared", "message": "Pipeline logs cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear logs: {e}")


# =============================================================================
# MAIN QUERY ENDPOINTS
# =============================================================================


@app.post("/query", response_model=QueryResponse, tags=["Query"])
@limiter.limit("30/minute" if SecurityConfig.ENABLE_RATE_LIMITING else "1000/minute")
async def query(
    request: Request,
    query_request: QueryRequest,
    user: Optional[Dict] = Depends(optional_auth),
):
    """
    Main query endpoint - natural language questions

    This endpoint handles natural language questions and returns AI-generated answers
    based on the knowledge graph context.

    Features:
    - Rate limiting (30 queries/minute)
    - Result caching (1 hour TTL)
    - Structured logging
    - Optional authentication
    """
    start_time = time.time()

    if not rag_instance:
        logger.error("query_failed", reason="rag_not_initialized")
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    # Log query request
    logger.info(
        "query_received",
        question=query_request.question[:100],  # Truncate for logging
        use_llm=query_request.use_llm,
        user_id=user.get("sub") if user else "anonymous",
    )

    try:
        # Check cache first
        cached_result = QueryCache.get(query_request.question)
        if cached_result and query_request.use_llm:
            logger.info("query_cache_hit", question=query_request.question[:50])
            record_cache_operation("query", hit=True)
            record_query_execution("cached", success=True)
            return cached_result

        record_cache_operation("query", hit=False)

        # Execute query
        result = rag_instance.query(
            question=query_request.question,
            return_context=query_request.return_context,
            use_llm=query_request.use_llm,
            return_traversal=query_request.return_traversal,
        )

        # Cache result if LLM was used
        if query_request.use_llm and result:
            QueryCache.set(query_request.question, result, ttl=3600)  # 1 hour

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "query_success",
            question=query_request.question[:50],
            duration_ms=duration_ms,
            cached=False,
        )
        record_query_execution("natural_language", success=True)
        
        # Track query execution
        track_query_exec(
            query_text=query_request.question,
            query_type="natural_language",
            duration=(time.time() - start_time),
            success=True,
            cache_hit=False
        )

        return result

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            "query_failed",
            question=query_request.question[:50],
            error=str(e),
            duration_ms=duration_ms,
            exc_info=True,
        )
        record_query_execution("natural_language", success=False)
        
        # Track failed query
        track_query_exec(
            query_text=query_request.question,
            query_type="natural_language",
            duration=(time.time() - start_time),
            success=False,
            cache_hit=False
        )

        error_msg = sanitize_error_message(e, include_details=False)
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/query/batch", tags=["Query"])
async def batch_query(request: BatchQueryRequest):
    """Process multiple queries in batch"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        results = rag_instance.batch_query(request.questions)
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch query failed: {str(e)}")


@app.post("/query/multi-hop", tags=["Query"])
async def multi_hop_reasoning(
    question: str = Body(..., embed=True), max_hops: int = Body(3, embed=True)
):
    """Perform multi-hop reasoning across the graph"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        result = rag_instance.multi_hop_reasoning(question, max_hops=max_hops)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-hop query failed: {str(e)}")


# =============================================================================
# ARTICLE ENDPOINTS (for Flutter app)
# =============================================================================


@app.get("/api/articles", tags=["Articles"], dependencies=[Depends(require_api_key)])
async def get_articles(
    page: int = Query(0, ge=0, description="Page number (0-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Number of articles per page"),
):
    """
    Get paginated list of articles, sorted by published date (newest first)
    """
    try:
        import json
        from pathlib import Path
        from datetime import datetime

        articles_dir = Path("data/articles/articles")
        if not articles_dir.exists():
            return {"articles": [], "total": 0, "page": page, "limit": limit}

        # Find all article JSON files
        article_files = []
        for json_file in articles_dir.rglob("tc_*.json"):
            # Skip metadata files
            if "metadata" in json_file.parts:
                continue
            article_files.append(json_file)

        # Load and parse articles
        articles = []
        for article_file in article_files:
            try:
                with open(article_file, "r", encoding="utf-8") as f:
                    article_data = json.load(f)
                    # Ensure it has required fields
                    if "article_id" in article_data and "url" in article_data:
                        articles.append(article_data)
            except Exception as e:
                logger.debug(f"Failed to load article {article_file}: {e}")
                continue

        # Sort by published_date (newest first)
        def get_date(article):
            date_str = article.get("published_date", "")
            if not date_str:
                return datetime.min
            try:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except:
                return datetime.min

        articles.sort(key=get_date, reverse=True)

        # Paginate
        total = len(articles)
        start = page * limit
        end = start + limit
        paginated_articles = articles[start:end]

        return {
            "articles": paginated_articles,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": end < total,
        }
    except Exception as e:
        logger.error("get_articles_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get articles: {sanitize_error_message(str(e))}",
        )


@app.get("/api/articles/{article_id}/exists", tags=["Articles"])
async def check_article_exists(article_id: str):
    """
    Check if an article exists in the graph database
    """
    try:
        if not rag_instance:
            raise HTTPException(
                status_code=503, detail="RAG instance not initialized"
            )

        # Check if article exists in Neo4j
        from neo4j import GraphDatabase
        import os

        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(
                os.getenv("NEO4J_USER", "neo4j"),
                os.getenv("NEO4J_PASSWORD", ""),
            ),
        )

        try:
            with driver.session() as session:
                result = session.run(
                    """
                    MATCH (a:Article {id: $article_id})
                    OPTIONAL MATCH (e)
                    WHERE e.article_count IS NOT NULL 
                      AND $article_id IN e.source_articles
                    RETURN count(e) as entity_count
                """,
                    article_id=article_id,
                )
                record = result.single()
                entity_count = record["entity_count"] if record else 0
                exists = entity_count > 0
        finally:
            driver.close()

        return {"exists": exists, "article_id": article_id}
    except Exception as e:
        logger.error("check_article_exists_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check article existence: {sanitize_error_message(str(e))}",
        )


class AddArticleRequest(BaseModel):
    """Request model for adding article"""

    url: str = Field(..., description="Article URL to scrape and add")


@app.post("/api/articles/add", tags=["Articles"])
async def add_article_to_graph(
    request: AddArticleRequest,
    user: Optional[Dict] = Depends(optional_auth),
):
    """
    Add an article to the graph by URL.
    If the article is not cached, it will be scraped and processed.
    """
    try:
        import hashlib
        import json
        from pathlib import Path
        from datetime import datetime

        # Generate article ID from URL
        article_id = hashlib.md5(request.url.encode()).hexdigest()[:12]

        # Check if article already exists in cache
        articles_dir = Path("data/articles/articles")
        article_file = None

        # Search for existing article file
        if articles_dir.exists():
            for json_file in articles_dir.rglob(f"tc_{article_id}.json"):
                if "metadata" not in json_file.parts:
                    article_file = json_file
                    break

        # If article doesn't exist, we need to scrape it
        # For now, return a message that scraping needs to be done via pipeline
        if article_file is None:
            return {
                "status": "pending",
                "message": "Article not found in cache. Please use the pipeline to scrape and process it.",
                "article_id": article_id,
                "url": request.url,
            }

        # Article exists in cache, check if it's in graph
        with open(article_file, "r", encoding="utf-8") as f:
            article_data = json.load(f)

        # Check if already in graph
        from neo4j import GraphDatabase
        import os

        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(
                os.getenv("NEO4J_USER", "neo4j"),
                os.getenv("NEO4J_PASSWORD", ""),
            ),
        )

        try:
            with driver.session() as session:
                result = session.run(
                    """
                    MATCH (a:Article {id: $article_id})
                    OPTIONAL MATCH (e)
                    WHERE e.article_count IS NOT NULL 
                      AND $article_id IN e.source_articles
                    RETURN count(e) as entity_count
                """,
                    article_id=article_id,
                )
                record = result.single()
                entity_count = record["entity_count"] if record else 0
                in_graph = entity_count > 0
        finally:
            driver.close()

        if in_graph:
            return {
                "status": "exists",
                "message": "Article already exists in graph",
                "article_id": article_id,
            }

        # Article is cached but not in graph - trigger processing
        # This would require running the entity extraction and graph building pipeline
        # For now, return a message
        return {
            "status": "cached_not_processed",
            "message": "Article found in cache but not processed. Please run the pipeline to process it.",
            "article_id": article_id,
        }

    except Exception as e:
        logger.error("add_article_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add article: {sanitize_error_message(str(e))}",
        )


# =============================================================================
# SEARCH ENDPOINTS
# =============================================================================


@app.post("/search/semantic", tags=["Search"])
async def semantic_search(request: SemanticSearchRequest):
    """
    Semantic search using embeddings

    Find entities similar to the query based on vector similarity.
    """
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        results = rag_instance.semantic_search(
            query=request.query, top_k=request.top_k, entity_type=request.entity_type
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")


@app.post("/search/hybrid", tags=["Search"])
async def hybrid_search(
    query: str = Body(..., embed=True),
    top_k: int = Body(10, embed=True),
    semantic_weight: float = Body(0.7, embed=True),
):
    """
    Hybrid search combining semantic and keyword matching

    Combines vector similarity with traditional keyword search.
    """
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        results = rag_instance.hybrid_search(
            query=query, top_k=top_k, semantic_weight=semantic_weight
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")


@app.get("/search/fulltext", tags=["Search"])
async def fulltext_search(
    query: str = Query(..., description="Search term"),
    limit: int = Query(10, description="Max results", ge=1, le=50),
):
    """Full-text search in entity names and descriptions"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        results = rag_instance.query_templates.search_entities_full_text(
            query, limit=limit
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Full-text search failed: {str(e)}"
        )


# =============================================================================
# ENTITY ENDPOINTS
# =============================================================================


@app.get("/entity/{entity_id}", tags=["Entities"])
async def get_entity(
    entity_id: str,
    include_relationships: bool = Query(False, description="Include related entities"),
):
    """Get entity details by ID"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        entity = rag_instance.query_templates.get_entity_by_id(entity_id)

        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        if include_relationships:
            relationships = rag_instance.get_entity_context(entity_id, max_hops=1)
            entity["relationships"] = relationships

        return entity
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity: {str(e)}")


@app.get("/entity/name/{entity_name}", tags=["Entities"])
async def get_entity_by_name(
    entity_name: str,
    entity_type: Optional[str] = Query(None, description="Entity type filter"),
):
    """Get entity by name"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        entity = rag_instance.query_templates.get_entity_by_name(
            entity_name, entity_type
        )

        if not entity:
            raise HTTPException(
                status_code=404, detail=f"Entity '{entity_name}' not found"
            )

        return entity
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity: {str(e)}")


@app.get("/entities/type/{entity_type}", tags=["Entities"])
async def get_entities_by_type(entity_type: str, limit: int = Query(10, ge=1, le=100)):
    """Get entities by type"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        entities = rag_instance.query_templates.search_entities_by_type(
            entity_type, limit=limit
        )
        return {"results": entities, "count": len(entities), "type": entity_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entities: {str(e)}")


@app.post("/entity/compare", tags=["Entities"])
async def compare_entities(request: CompareEntitiesRequest):
    """Compare two entities"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        result = rag_instance.compare_entities(request.entity1, request.entity2)

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


# =============================================================================
# COMPANY ENDPOINTS
# =============================================================================


@app.get("/company/{company_name}", tags=["Companies"])
async def get_company_profile(company_name: str):
    """Get comprehensive company profile"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        profile = rag_instance.query_templates.get_company_profile(company_name)

        if not profile:
            raise HTTPException(
                status_code=404, detail=f"Company '{company_name}' not found"
            )

        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get company: {str(e)}")


@app.get("/companies/funded", tags=["Companies"])
async def get_funded_companies(min_investors: int = Query(1, ge=1)):
    """Get companies with funding information"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        companies = rag_instance.query_templates.get_companies_by_funding(min_investors)
        return {"results": companies, "count": len(companies)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get companies: {str(e)}"
        )


@app.get("/companies/sector/{sector}", tags=["Companies"])
async def get_companies_by_sector(sector: str):
    """Get companies in a specific sector"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        companies = rag_instance.query_templates.get_companies_in_sector(sector)
        return {"results": companies, "count": len(companies), "sector": sector}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get companies: {str(e)}"
        )


@app.get("/company/{company_name}/competitive-landscape", tags=["Companies"])
async def get_competitive_landscape(company_name: str):
    """Get competitive landscape for a company"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        landscape = rag_instance.query_templates.get_competitive_landscape(company_name)

        if not landscape:
            raise HTTPException(
                status_code=404, detail=f"Company '{company_name}' not found"
            )

        return landscape
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get competitive landscape: {str(e)}"
        )


# =============================================================================
# INVESTOR ENDPOINTS
# =============================================================================


@app.get("/investor/{investor_name}/portfolio", tags=["Investors"])
async def get_investor_portfolio(investor_name: str):
    """Get investor's portfolio"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        portfolio = rag_instance.query_templates.get_investor_portfolio(investor_name)

        if not portfolio:
            raise HTTPException(
                status_code=404, detail=f"Investor '{investor_name}' not found"
            )

        return portfolio
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get portfolio: {str(e)}"
        )


@app.get("/investors/top", tags=["Investors"])
async def get_top_investors(limit: int = Query(10, ge=1, le=50)):
    """Get most active investors"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        investors = rag_instance.query_templates.get_top_investors(limit)
        return {"results": investors, "count": len(investors)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get investors: {str(e)}"
        )


# =============================================================================
# PERSON ENDPOINTS
# =============================================================================


@app.get("/person/{person_name}", tags=["People"])
async def get_person_profile(person_name: str):
    """Get person's profile"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        profile = rag_instance.query_templates.get_person_profile(person_name)

        if not profile:
            raise HTTPException(
                status_code=404, detail=f"Person '{person_name}' not found"
            )

        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get person: {str(e)}")


# =============================================================================
# RELATIONSHIP ENDPOINTS
# =============================================================================


@app.get("/relationships/{entity_id}", tags=["Relationships"])
async def get_entity_relationships(
    entity_id: str, max_hops: int = Query(2, ge=1, le=3)
):
    """Get entity's relationship network"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        relationships = rag_instance.get_entity_context(entity_id, max_hops=max_hops)

        if not relationships:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        return relationships
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get relationships: {str(e)}"
        )


@app.get("/connection-path", tags=["Relationships"])
async def find_connection_path(
    entity1: str = Query(..., description="First entity name"),
    entity2: str = Query(..., description="Second entity name"),
    max_hops: int = Query(4, ge=1, le=6),
):
    """Find shortest path between two entities"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        paths = rag_instance.query_templates.find_connection_path(
            entity1, entity2, max_hops
        )

        if not paths:
            return {
                "message": f"No connection found between {entity1} and {entity2}",
                "paths": [],
            }

        return {
            "entity1": entity1,
            "entity2": entity2,
            "paths": paths,
            "count": len(paths),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to find connection: {str(e)}"
        )


# =============================================================================
# COMMUNITY ENDPOINTS
# =============================================================================


@app.get("/communities", tags=["Communities"])
async def get_communities(min_size: int = Query(3, ge=1)):
    """Get all detected communities"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        communities = rag_instance.query_templates.get_communities(min_size)
        return {"results": communities, "count": len(communities)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get communities: {str(e)}"
        )


@app.get("/community/{community_id}", tags=["Communities"])
async def get_community(community_id: int):
    """Get detailed community information"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        community = rag_instance.query_templates.get_community_by_id(community_id)

        if not community:
            raise HTTPException(
                status_code=404, detail=f"Community {community_id} not found"
            )

        return community
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get community: {str(e)}"
        )


# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================


@app.get("/analytics/statistics", tags=["Analytics"])
async def get_statistics():
    """Get graph statistics"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        stats = rag_instance.query_templates.get_graph_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}"
        )


@app.get("/analytics/most-connected", tags=["Analytics"])
async def get_most_connected(limit: int = Query(10, ge=1, le=50)):
    """Get most connected entities"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        entities = rag_instance.query_templates.get_most_connected_entities(limit)
        return {"results": entities, "count": len(entities)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entities: {str(e)}")


@app.get("/analytics/importance", tags=["Analytics"])
async def get_entity_importance(limit: int = Query(20, ge=1, le=50)):
    """Get entity importance scores"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        entities = rag_instance.query_templates.get_entity_importance_scores(limit)
        return {"results": entities, "count": len(entities)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get importance scores: {str(e)}"
        )


@app.get("/analytics/insights/{topic}", tags=["Analytics"])
async def get_insights(topic: str, limit: int = Query(5, ge=1, le=10)):
    """Get AI-generated insights about a topic"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        insights = rag_instance.get_insights(topic, limit=limit)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")


@app.get("/analytics/recurring-themes", tags=["Analytics"])
async def get_recurring_themes(
    min_frequency: int = Query(
        3, ge=1, le=50, description="Minimum frequency for a theme to be included"
    ),
    limit: int = Query(
        20, ge=1, le=100, description="Maximum number of themes to return"
    ),
    time_window_days: Optional[int] = Query(
        None,
        ge=1,
        le=365,
        description="Only consider entities mentioned within this time window",
    ),
):
    """Extract recurring themes from the knowledge graph"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        themes = rag_instance.query_templates.get_recurring_themes(
            min_frequency=min_frequency, limit=limit, time_window_days=time_window_days
        )
        return {"themes": themes, "count": len(themes)}
    except Exception as e:
        logger.error("recurring_themes_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract themes: {sanitize_error_message(str(e))}",
        )


@app.get("/analytics/theme/{theme_name}", tags=["Analytics"])
async def get_theme_details(
    theme_name: str,
    theme_type: str = Query(
        ...,
        description="Type of theme: technology_trend, funding_pattern, partnership_pattern, industry_cluster",
    ),
):
    """Get detailed information about a specific theme"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        details = rag_instance.query_templates.get_theme_details(theme_name, theme_type)
        if not details:
            raise HTTPException(
                status_code=404, detail=f"Theme '{theme_name}' not found"
            )
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error("theme_details_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get theme details: {sanitize_error_message(str(e))}",
        )


@app.post("/analytics/theme/summary", tags=["Analytics"])
async def generate_theme_summary(
    theme_data: Dict[str, Any] = Body(..., description="Theme details to summarize")
):
    """Generate an LLM-powered summary of theme details"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        import os

        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI

        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise HTTPException(status_code=503, detail="OpenAI API key not configured")

        llm = ChatOpenAI(temperature=0.3, model="gpt-4o-mini", api_key=openai_api_key)

        # Build context from theme data
        context_parts = []

        if theme_data.get("theme_name"):
            context_parts.append(f"Theme: {theme_data['theme_name']}")

        if theme_data.get("theme_type"):
            context_parts.append(f"Type: {theme_data['theme_type']}")

        if theme_data.get("description"):
            context_parts.append(f"Description: {theme_data['description']}")

        if theme_data.get("frequency"):
            context_parts.append(f"Frequency: {theme_data['frequency']} occurrences")

        if theme_data.get("strength"):
            context_parts.append(f"Strength Score: {theme_data['strength']}")

        if theme_data.get("technology"):
            context_parts.append(f"\nTechnology: {theme_data['technology']}")

        if theme_data.get("investor"):
            context_parts.append(f"\nInvestor: {theme_data['investor']}")

        if theme_data.get("entity"):
            context_parts.append(f"\nEntity: {theme_data['entity']}")
            if theme_data.get("mention_count"):
                context_parts.append(f"Mentioned {theme_data['mention_count']} times")

        if theme_data.get("community_id") is not None:
            context_parts.append(f"\nCommunity ID: {theme_data['community_id']}")
            if theme_data.get("total_entities"):
                context_parts.append(f"Total Entities: {theme_data['total_entities']}")

        if theme_data.get("companies"):
            companies = theme_data["companies"]
            context_parts.append(
                f"\nCompanies ({theme_data.get('total_companies', len(companies))}):"
            )
            for i, company in enumerate(companies[:10], 1):  # Limit to first 10
                company_info = f"  {i}. {company.get('name', 'Unknown')}"
                if company.get("description"):
                    company_info += f" - {company.get('description', '')[:100]}"
                if company.get("investors"):
                    company_info += (
                        f" | Investors: {', '.join(company.get('investors', [])[:3])}"
                    )
                context_parts.append(company_info)

        if theme_data.get("partnerships"):
            partnerships = theme_data["partnerships"]
            context_parts.append(
                f"\nPartnerships ({theme_data.get('total_partnerships', len(partnerships))}):"
            )
            for i, p in enumerate(partnerships[:10], 1):
                context_parts.append(
                    f"  {i}. {p.get('from', 'Unknown')} ↔ {p.get('to', 'Unknown')}"
                )

        if theme_data.get("entities"):
            entities = theme_data["entities"]
            context_parts.append(f"\nEntities ({theme_data.get('total_entities', len(entities))}):")
            for i, entity in enumerate(entities[:10], 1):
                if isinstance(entity, dict):
                    entity_name = entity.get("name", entity.get("entity", "Unknown"))
                    entity_type = entity.get("type", "")
                    entity_desc = entity.get("description", "")
                    entity_info = f"  {i}. {entity_name}"
                    if entity_type:
                        entity_info += f" ({entity_type})"
                    if entity_desc:
                        entity_info += f" - {entity_desc[:100]}"
                    context_parts.append(entity_info)
                else:
                    context_parts.append(f"  {i}. {entity}")

        if theme_data.get("relationships"):
            relationships = theme_data["relationships"]
            context_parts.append(f"\nRelationships ({len(relationships)}):")
            for i, rel in enumerate(relationships[:10], 1):
                if isinstance(rel, dict):
                    rel_info = f"  {i}. {rel.get('name', 'Unknown')}"
                    if rel.get("relationship"):
                        rel_info += f" - {rel.get('relationship')}"
                    if rel.get("type"):
                        rel_info += f" ({rel.get('type')})"
                    context_parts.append(rel_info)
                else:
                    context_parts.append(
                        f"  {i}. {rel.get('name', 'Unknown')} ({rel.get('relationship', 'related')})"
                    )

        context = "\n".join(context_parts)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert analyst specializing in knowledge graph analysis. 
Your task is to create a concise, focused summary of theme details.

CRITICAL GUIDELINES:
- Be BRIEF and DIRECT - maximum 100-120 words (2-3 short paragraphs)
- Focus ONLY on the most significant insights - avoid listing every detail
- Skip generic statements like "reveals patterns" or "highlights importance"
- Don't list individual entity names unless they're truly exceptional
- Focus on WHAT the theme means, not HOW it was identified
- Remove redundant phrases and filler words
- Get straight to the point - what does this theme tell us?
- Use active voice and clear, direct language""",
                ),
                (
                    "user",
                    """Analyze the following theme details and provide a concise, focused summary:

{context}

Write a brief summary (100-120 words max) that:
1. Explains what this theme represents in one clear sentence
2. Highlights the 2-3 most important insights or patterns
3. Mentions only the most significant statistics or entities if they add real value

Be direct and avoid verbose explanations.""",
                ),
            ]
        )

        chain = prompt | llm | StrOutputParser()

        # Track OpenAI call
        import time
        start_time = time.time()
        summary = chain.invoke({"context": context})
        duration = time.time() - start_time
        
        # Extract token usage if available
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        
        # Try to get token usage from response metadata
        if hasattr(llm, 'get_num_tokens'):
            try:
                prompt_tokens = llm.get_num_tokens(context)
            except:
                pass
        
        track_openai_call(
            model="gpt-4o-mini",
            operation="theme_summary",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            duration=duration,
            success=True,
            theme_name=theme_data.get("theme_name", "unknown")
        )

        return {
            "summary": summary,
            "theme_name": theme_data.get("theme_name"),
            "theme_type": theme_data.get("theme_type"),
        }
    except Exception as e:
        logger.error("theme_summary_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {sanitize_error_message(str(e))}",
        )


# =============================================================================
# AURA GRAPH ANALYTICS ENDPOINTS
# =============================================================================


@app.post("/aura/community-detection", tags=["Aura Analytics"])
async def run_community_detection(
    algorithm: str = Body(
        "leiden", description="Algorithm: leiden, louvain, or label_propagation"
    ),
    min_community_size: int = Body(3, ge=1, le=100),
    graph_name: str = Body("entity-graph", description="Name for the projected graph"),
):
    """Run community detection using Aura Graph Analytics"""
    try:
        from utils.aura_graph_analytics import AuraGraphAnalytics

        analytics = AuraGraphAnalytics()
        result = analytics.detect_communities(
            algorithm=algorithm,
            min_community_size=min_community_size,
            graph_name=graph_name,
        )
        return result
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Aura Graph Analytics not available: {str(e)}. Install graphdatascience package.",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("community_detection_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run community detection: {sanitize_error_message(str(e))}",
        )


@app.get("/aura/communities", tags=["Aura Analytics"])
async def get_communities(
    min_size: int = Query(3, ge=1, le=100), limit: int = Query(50, ge=1, le=200)
):
    """Get communities from the graph"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        # Query communities from Neo4j
        communities = rag_instance.query_templates.get_communities(
            min_size=min_size, limit=limit
        )
        return {"communities": communities, "count": len(communities)}
    except Exception as e:
        logger.error("get_communities_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get communities: {sanitize_error_message(str(e))}",
        )


@app.get("/aura/community-stats", tags=["Aura Analytics"])
async def get_community_statistics():
    """Get community statistics"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        stats = rag_instance.query_templates.get_community_statistics()
        return stats
    except Exception as e:
        logger.error("community_stats_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get community statistics: {sanitize_error_message(str(e))}",
        )


@app.get("/aura/community-graph", tags=["Aura Analytics"])
async def get_community_graph(
    community_id: Optional[int] = Query(
        None, description="Specific community ID, or None for all communities"
    ),
    max_nodes: int = Query(
        200, ge=10, le=1000, description="Maximum number of nodes to return"
    ),
    max_communities: int = Query(
        10, ge=1, le=50, description="Maximum number of communities to visualize"
    ),
):
    """Get community graph data for visualization"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        graph_data = rag_instance.query_templates.get_community_graph_data(
            community_id=community_id,
            max_nodes=max_nodes,
            max_communities=max_communities,
        )
        return graph_data
    except Exception as e:
        logger.error("community_graph_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get community graph: {sanitize_error_message(str(e))}",
        )


# =============================================================================
# TECHNOLOGY & TREND ENDPOINTS
# =============================================================================


@app.get("/technology/{technology_name}", tags=["Technology"])
async def get_technology_adoption(technology_name: str):
    """Get technology adoption information"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        adoption = rag_instance.query_templates.get_technology_adoption(technology_name)

        if not adoption:
            raise HTTPException(
                status_code=404, detail=f"Technology '{technology_name}' not found"
            )

        return adoption
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get technology info: {str(e)}"
        )


@app.get("/technologies/trending", tags=["Technology"])
async def get_trending_technologies(limit: int = Query(10, ge=1, le=50)):
    """Get trending technologies"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        technologies = rag_instance.query_templates.get_trending_technologies(limit)
        return {"results": technologies, "count": len(technologies)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get technologies: {str(e)}"
        )


# =============================================================================
# TEMPORAL ENDPOINTS
# =============================================================================


@app.get("/recent-entities", tags=["Temporal"])
async def get_recent_entities(
    days: int = Query(30, ge=1, le=365), limit: int = Query(10, ge=1, le=50)
):
    """Get recently mentioned entities"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        entities = rag_instance.query_templates.get_recent_entities(days, limit)
        return {"results": entities, "count": len(entities), "days": days}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get recent entities: {str(e)}"
        )


@app.get("/funding-timeline", tags=["Temporal"])
async def get_funding_timeline(company_name: Optional[str] = Query(None)):
    """Get funding events timeline"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        timeline = rag_instance.query_templates.get_funding_timeline(company_name)
        return {"results": timeline, "count": len(timeline)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")


# =============================================================================
# DOCUMENTATION ENDPOINTS
# =============================================================================


@app.get("/docs/readme", tags=["Documentation"])
async def get_readme():
    """Get README.md content"""
    try:
        base_path = Path(__file__).parent
        # Try different case variations
        readme_path = None
        for filename in ["README.md", "README.MD", "readme.md"]:
            candidate = base_path / filename
            if candidate.exists():
                readme_path = candidate
                break
        
        if not readme_path:
            raise HTTPException(status_code=404, detail="README.md not found")
        
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return Response(content=content, media_type="text/markdown; charset=utf-8")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read README: {str(e)}")


# =============================================================================
# BACKEND-ONLY API
# Frontend is hosted separately on Vercel - this backend serves API endpoints only
# =============================================================================
# 
# This is a backend-only deployment. The frontend React app is deployed separately
# to Vercel and communicates with this API via CORS-enabled HTTP requests.
# 
# Setup:
# 1. Deploy this backend API (Docker/Render/DigitalOcean/etc.)
# 2. Deploy frontend to Vercel (see VERCEL_DEPLOYMENT.md)
# 3. Configure ALLOWED_ORIGINS env var with your Vercel domain(s)
# 4. Set VITE_API_BASE_URL in Vercel to point to this backend API
#

# Mount lib folder for static libraries if needed (vis-network, etc.)
# This is for any static assets the API might need, not frontend files
lib_path = Path(__file__).parent / "lib"
if lib_path.exists():
    app.mount("/lib", StaticFiles(directory=str(lib_path)), name="lib")
    logger.info("lib_static_files_mounted", path=str(lib_path))
else:
    logger.info("lib_folder_not_found", path=str(lib_path))

# Root endpoint - API info
@app.get("/")
async def root():
    """API root endpoint - Backend-only API for Vercel-hosted frontend"""
    return {
        "name": "GraphRAG API",
        "version": "2.0.0",
        "description": "Backend API for TechCrunch Knowledge Graph Query System",
        "deployment": "backend-only (frontend on Vercel)",
        "docs": "/docs",
        "health": "/health"
    }


# =============================================================================
# MAIN - Run server
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Create data directories at runtime (not in Docker image to save memory)
    for data_dir in ["data/articles", "data/metadata", "data/processing", "data/raw_data", "logs"]:
        os.makedirs(data_dir, exist_ok=True)
    
    # Render uses PORT, fallback to API_PORT, then default to 8000
    port = int(os.getenv("PORT") or os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")

    logger.info("api_starting", host=host, port=port)
    logger.info(
        "api_documentation",
        docs_url=f"http://{host}:{port}/docs",
        redoc_url=f"http://{host}:{port}/redoc",
    )
    logger.info("api_metrics", metrics_url=f"http://{host}:{port}/metrics")

    # Determine if we're in production (disable reload)
    # Check multiple indicators of production environment
    env_var = os.getenv("ENVIRONMENT", "").lower()
    disable_reload = os.getenv("DISABLE_RELOAD", "false").lower() == "true"
    
    # Check if we're in a container (common in production deployments)
    # Multiple detection methods for different container environments
    is_container = (
        os.path.exists("/.dockerenv") or  # Docker
        os.getenv("CONTAINER", "").lower() == "true" or  # Explicit flag
        os.path.exists("/.containerenv") or  # Podman
        os.getenv("KUBERNETES_SERVICE_HOST") is not None or  # Kubernetes
        os.getenv("ECS_CONTAINER_METADATA_URI") is not None  # AWS ECS
    )
    
    # Check cgroup for container indicators (safe check)
    if not is_container and os.path.exists("/proc/1/cgroup"):
        try:
            with open("/proc/1/cgroup", "r") as f:
                cgroup_content = f.read()
                is_container = any(
                    indicator in cgroup_content
                    for indicator in ["docker", "kubepods", "containerd", "crio"]
                )
        except Exception:
            pass  # Ignore errors reading cgroup
    
    # DigitalOcean App Platform and most cloud platforms don't set ENVIRONMENT, so be more aggressive
    # If we're not explicitly in development, assume production
    is_explicit_dev = env_var in ("development", "dev", "local") or os.getenv("ENABLE_RELOAD", "false").lower() == "true"
    
    is_production = (
        env_var in ("production", "prod") or 
        disable_reload or 
        (is_container and not is_explicit_dev)  # In container and not explicitly dev = production
    )
    
    # Log the decision for debugging
    logger.info(
        "reload_configuration",
        is_production=is_production,
        env_var=env_var,
        is_container=is_container,
        is_explicit_dev=is_explicit_dev,
        disable_reload=disable_reload,
        reload_enabled=not is_production
    )
    
    # Exclude log files and data directories from file watcher to prevent reloads when pipeline writes logs
    # This prevents Uvicorn from reloading when:
    # - Pipeline writes to pipeline.log
    # - Scraped articles are saved (tc_*.json files in data/articles/)
    # - Checkpoint files are updated (extraction_checkpoint_*.json, discovery_checkpoint_*.json)
    # - Progress files are updated (extraction_progress.json)
    # - Data files are written (all_extractions.json, enriched_companies.json, etc.)
    # - Article JSON files are created/updated anywhere in data directories
    reload_excludes = [
        "*.log",
        "pipeline.log",
        "logs/*",
        "logs/**/*",
        # Exclude all data directories recursively
        "data/*",
        "data/**/*",
        "data/articles/**/*",
        "data/articles/*/*/*.json",  # Article files like data/articles/2025-10/31/tc_*.json
        "data/metadata/**/*",
        "data/processing/**/*",
        "data/processing/vector_index/**/*",  # Vector index directory
        "data/raw_data/**/*",
        # Exclude all JSON files in data directories (articles, checkpoints, etc.)
        "data/**/*.json",
        "data/**/*.jsonl",
        # Vector index files specifically
        "**/vector_index/**/*",
        "**/vector_index/*.npy",
        "**/vector_index/*.json",
        "**/vector_index/*.jsonl",
        # Specific patterns for pipeline-generated files
        "*checkpoint*.json",
        "*progress*.json",
        "*_extractions.json",
        "*_companies.json",
        "all_extractions.json",
        "enriched_companies.json",
        "tc_*.json",  # TechCrunch article files
        "discovered_articles_*.json",
        "failed_articles_*.json",
        "scraping_stats_*.json",
        # Python cache files
        "__pycache__/*",
        "__pycache__/**/*",
        "*.pyc",
        # Git files
        ".git/*",
        ".git/**/*",
        # Binary/data files
        "*.npy",  # NumPy array files (embeddings)
        "*.jsonl",  # JSON Lines files (vector index chunks)
        "*.pkl",  # Pickle files (if any caching uses pickle files)
        "*.pickle",  # Pickle files (alternative extension)
        "*.tmp",  # Temporary files
        "*.temp",  # Temporary files
        "*.cache",  # Cache files
    ]
    
    # Configure uvicorn access logging to exclude health checks (reduces log noise)
    # Docker healthcheck polls every 60s, so we filter these expected requests
    import logging.config
    
    # Custom access log format that excludes health checks
    class HealthCheckFilter(logging.Filter):
        def filter(self, record):
            # Suppress uvicorn access logs for /health endpoint
            message = record.getMessage()
            return "/health" not in message or "ERROR" in message or "WARNING" in message
    
    # Apply filter to uvicorn.access logger
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.addFilter(HealthCheckFilter())
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=not is_production,  # Auto-reload only in development
        reload_excludes=reload_excludes if not is_production else None,  # Exclude log files from watcher
        log_level="info",
    )
