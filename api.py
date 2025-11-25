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
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from query_templates import QueryTemplates
from rag_query import GraphRAGQuery, create_rag_query
from utils.cache import EntityCache, QueryCache, get_cache

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


# Add middleware to handle OPTIONS requests (CORS preflight)
@app.middleware("http")
async def handle_options_requests(request: Request, call_next):
    """Handle OPTIONS requests for CORS preflight"""
    if request.method == "OPTIONS":
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Request-ID",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "3600",
            },
        )
    return await call_next(request)


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
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Allow inline for frontend
        "style-src 'self' 'unsafe-inline'; "  # Allow inline styles
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https:; "
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


# Add CORS middleware with security restrictions
app.add_middleware(
    CORSMiddleware,
    allow_origins=SecurityConfig.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID", "Accept"],
)



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
    - Summary statistics
    """
    try:
        summary = get_analytics_summary(hours=hours, group_by=group_by)
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


@app.get("/admin/neo4j/overview", tags=["Admin", "Neo4j"])
async def neo4j_overview() -> Dict[str, Any]:
    """
    Return an overview of the connected Neo4j (AuraDB) instance:
    - dbms components (version/edition) when available
    - labels, relationship types
    - node/relationship counts, community count
    - top entities by connectivity and importance
    """
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        stats = rag_instance.query_templates.get_graph_statistics()

        db_info: Dict[str, Any] = {"components": []}
        labels: List[str] = []
        rel_types: List[str] = []
        top_connected: List[Dict[str, Any]] = []
        top_important: List[Dict[str, Any]] = []

        # Run best-effort metadata queries (Aura may restrict some procedures)
        with rag_instance.driver.session() as session:
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

        # Top entities
        try:
            top_connected = rag_instance.query_templates.get_most_connected_entities(
                limit=10
            )
        except Exception:
            top_connected = []
        try:
            top_important = rag_instance.query_templates.get_entity_importance_scores(
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
    try:
        # Clear log file before starting new pipeline run
        if os.path.exists(pipeline_log_path):
            with open(pipeline_log_path, "w") as f:
                f.write("")
        
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
        log_fh = open(pipeline_log_path, "ab")
        try:
            pipeline_proc = subprocess.Popen(
                args, 
                stdout=log_fh, 
                stderr=subprocess.STDOUT, 
                cwd=os.getcwd(), 
                env=env,
                start_new_session=True  # Start in new session to survive parent termination
            )
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
            log_fh.close()
            logger.error("pipeline_start_failed", error=str(e), exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {e}")
    except Exception as e:
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
            loop = asyncio.get_event_loop()
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


@app.options("/query", tags=["Query"])
async def query_options():
    """Handle OPTIONS preflight requests for /query endpoint"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Request-ID",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        },
    )


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
# FRONTEND SERVING
# Serve frontend static files and handle React Router
# =============================================================================

frontend_dist_path = Path(__file__).parent / "frontend" / "dist"
lib_path = Path(__file__).parent / "lib"

# Mount lib folder for static libraries (vis-network, etc.)
if lib_path.exists():
    app.mount("/lib", StaticFiles(directory=str(lib_path)), name="lib")
    logger.info("lib_static_files_mounted", path=str(lib_path))
else:
    logger.warning("lib_folder_not_found", path=str(lib_path))

if frontend_dist_path.exists():
    # Mount static assets (JS, CSS, images, etc.)
    app.mount("/assets", StaticFiles(directory=str(frontend_dist_path / "assets")), name="assets")
    
    # Serve index.html for root and all non-API routes (for React Router)
    # This must be the last route to catch all unmatched paths
    @app.get("/")
    async def serve_frontend_root():
        """Serve frontend application at root"""
        index_path = frontend_dist_path / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        else:
            raise HTTPException(status_code=404, detail="Frontend not found")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend application - catch-all for React Router"""
        # Don't serve frontend for API routes or lib files (already handled by mount)
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "health", "metrics", "admin/", "lib/")):
            raise HTTPException(status_code=404, detail="Not found")
        
        index_path = frontend_dist_path / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        else:
            raise HTTPException(status_code=404, detail="Frontend not found")
else:
    logger.warning("frontend_dist_not_found", path=str(frontend_dist_path))


# =============================================================================
# MAIN - Run server
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")

    logger.info("api_starting", host=host, port=port)
    logger.info(
        "api_documentation",
        docs_url=f"http://{host}:{port}/docs",
        redoc_url=f"http://{host}:{port}/redoc",
    )
    logger.info("api_metrics", metrics_url=f"http://{host}:{port}/metrics")

    # Determine if we're in production (disable reload)
    is_production = os.getenv("ENVIRONMENT", "").lower() in ("production", "prod") or os.getenv("DISABLE_RELOAD", "false").lower() == "true"
    
    # Exclude log files and data directories from file watcher to prevent reloads when pipeline writes logs
    # This prevents Uvicorn from reloading when:
    # - Pipeline writes to pipeline.log
    # - Checkpoint files are updated (extraction_checkpoint_*.json, discovery_checkpoint_*.json)
    # - Progress files are updated (extraction_progress.json)
    # - Data files are written (all_extractions.json, enriched_companies.json, etc.)
    # - Article JSON files are created/updated
    reload_excludes = [
        "*.log",
        "pipeline.log",
        "logs/*",
        "logs/**/*",
        "data/*",
        "data/**/*",
        "data/articles/**/*",
        "data/metadata/**/*",
        "data/processing/**/*",
        "data/raw_data/**/*",
        "*checkpoint*.json",
        "*progress*.json",
        "*_extractions.json",
        "*_companies.json",
        "all_extractions.json",
        "enriched_companies.json",
        "__pycache__/*",
        "__pycache__/**/*",
        "*.pyc",
        ".git/*",
        ".git/**/*",
        "*.npy",  # NumPy array files
        "*.jsonl",  # JSON Lines files
    ]
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=not is_production,  # Auto-reload only in development
        reload_excludes=reload_excludes if not is_production else None,  # Exclude log files from watcher
        log_level="info",
    )
