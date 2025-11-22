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

from fastapi import FastAPI, HTTPException, Query, Body, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import subprocess
import threading
import io
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from rag_query import GraphRAGQuery, create_rag_query
from query_templates import QueryTemplates

# Import new utility modules
from utils.logging_config import setup_logging, get_logger
from utils.security import SecurityConfig, verify_token, optional_auth, sanitize_error_message
from utils.cache import get_cache, QueryCache, EntityCache
from utils.monitoring import (
    PrometheusMiddleware,
    get_metrics,
    get_metrics_content_type,
    record_query_execution,
    record_cache_operation
)

# Load environment variables
load_dotenv()

# Initialize structured logging
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    json_logs=os.getenv("JSON_LOGS", "true").lower() == "true",
    log_file=Path("logs/api.log") if os.getenv("ENABLE_FILE_LOGGING") == "true" else None
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

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "question": "Which AI startups raised funding recently?",
            "return_context": False,
            "use_llm": True
        }
    })


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search"""
    query: str = Field(..., description="Search query", min_length=2)
    top_k: int = Field(10, description="Number of results", ge=1, le=50)
    entity_type: Optional[str] = Field(None, description="Filter by entity type")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "query": "artificial intelligence",
            "top_k": 10,
            "entity_type": "Company"
        }
    })


class CompareEntitiesRequest(BaseModel):
    """Request model for entity comparison"""
    entity1: str = Field(..., description="First entity name")
    entity2: str = Field(..., description="Second entity name")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "entity1": "Anthropic",
            "entity2": "OpenAI"
        }
    })


class BatchQueryRequest(BaseModel):
    """Request model for batch queries"""
    questions: List[str] = Field(..., description="List of questions", min_length=1, max_length=10)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "questions": [
                "What is Anthropic?",
                "Who are the top investors?",
                "What are trending technologies?"
            ]
        }
    })


class QueryResponse(BaseModel):
    """Response model for query results"""
    question: str
    intent: Dict[str, Any]
    answer: Optional[str]
    context: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None


# =============================================================================
# ADMIN / PIPELINE CONTROL MODELS
# =============================================================================

class PipelineStartRequest(BaseModel):
    """Options for starting the pipeline"""
    scrape_category: Optional[str] = Field(None, description="TechCrunch category to scrape (e.g., 'startups', 'ai')")
    scrape_max_pages: Optional[int] = Field(None, description="Max pages to scrape", ge=1)
    max_articles: Optional[int] = Field(None, description="Limit number of articles", ge=1)
    skip_scraping: bool = Field(False, description="Skip scraping phase")
    skip_extraction: bool = Field(False, description="Skip entity extraction phase")
    skip_graph: bool = Field(False, description="Skip graph construction phase")
    no_resume: bool = Field(False, description="Do not resume from checkpoints")



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
        logger.error(
            "rag_initialization_failed",
            error=str(e),
            exc_info=True
        )
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
    lifespan=lifespan
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
                path=request.url.path
            )
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request body too large. Maximum size: {SecurityConfig.MAX_REQUEST_SIZE} bytes"}
            )

    response = await call_next(request)
    return response

# Add Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware)

# Add CORS middleware with security restrictions
app.add_middleware(
    CORSMiddleware,
    allow_origins=SecurityConfig.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)

# Frontend static files path (will be mounted after all API routes)
frontend_dist = Path(__file__).parent / "frontend" / "dist"


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    logger.info("root_endpoint_accessed")
    return {
        "status": "healthy",
        "service": "GraphRAG API",
        "version": "2.0.0",
        "features": [
            "structured_logging",
            "authentication",
            "rate_limiting",
            "caching",
            "metrics"
        ]
    }


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
                "authentication": "enabled" if SecurityConfig.ENABLE_AUTH else "disabled",
                "rate_limiting": "enabled" if SecurityConfig.ENABLE_RATE_LIMITING else "disabled"
            },
            "graph_stats": stats
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
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    )


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
            "allowed_origins": SecurityConfig.ALLOWED_ORIGINS
        }
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
                comp = session.run("CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition")
                db_info["components"] = [dict(r) for r in comp]
            except Exception:
                db_info["components"] = []
            try:
                labs = session.run("CALL db.labels() YIELD label RETURN label ORDER BY label")
                labels = [r["label"] for r in labs]
            except Exception:
                labels = []
            try:
                rels = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType")
                rel_types = [r["relationshipType"] for r in rels]
            except Exception:
                rel_types = []

        # Top entities
        try:
            top_connected = rag_instance.query_templates.get_most_connected_entities(limit=10)
        except Exception:
            top_connected = []
        try:
            top_important = rag_instance.query_templates.get_entity_importance_scores(limit=10)
        except Exception:
            top_important = []

        return {
            "status": "ok",
            "db_info": db_info,
            "labels": labels,
            "relationship_types": rel_types,
            "graph_stats": stats,
            "top_connected_entities": top_connected,
            "top_important_entities": top_important
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Neo4j overview: {e}")

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
        
        # Open log file in append mode for the new run
        log_fh = open(pipeline_log_path, "ab")
        pipeline_proc = subprocess.Popen(
            args,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            cwd=os.getcwd()
        )
        return {"status": "started", "pid": pipeline_proc.pid, "args": args, "log": pipeline_log_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {e}")


@app.get("/admin/pipeline/status", tags=["Admin"])
async def pipeline_status():
    """Get current pipeline process status"""
    if not pipeline_proc:
        return {"running": False}
    code = pipeline_proc.poll()
    return {"running": code is None, "pid": pipeline_proc.pid, "returncode": code}


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
        raise HTTPException(status_code=409, detail="Cannot clear logs while pipeline is running")
    
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
async def query(request: Request, query_request: QueryRequest, user: Optional[Dict] = Depends(optional_auth)):
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
        user_id=user.get("sub") if user else "anonymous"
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
            use_llm=query_request.use_llm
        )

        # Cache result if LLM was used
        if query_request.use_llm and result:
            QueryCache.set(query_request.question, result, ttl=3600)  # 1 hour

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "query_success",
            question=query_request.question[:50],
            duration_ms=duration_ms,
            cached=False
        )
        record_query_execution("natural_language", success=True)

        return result

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            "query_failed",
            question=query_request.question[:50],
            error=str(e),
            duration_ms=duration_ms,
            exc_info=True
        )
        record_query_execution("natural_language", success=False)

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
    question: str = Body(..., embed=True),
    max_hops: int = Body(3, embed=True)
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
            query=request.query,
            top_k=request.top_k,
            entity_type=request.entity_type
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")


@app.post("/search/hybrid", tags=["Search"])
async def hybrid_search(
    query: str = Body(..., embed=True),
    top_k: int = Body(10, embed=True),
    semantic_weight: float = Body(0.7, embed=True)
):
    """
    Hybrid search combining semantic and keyword matching

    Combines vector similarity with traditional keyword search.
    """
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        results = rag_instance.hybrid_search(
            query=query,
            top_k=top_k,
            semantic_weight=semantic_weight
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")


@app.get("/search/fulltext", tags=["Search"])
async def fulltext_search(
    query: str = Query(..., description="Search term"),
    limit: int = Query(10, description="Max results", ge=1, le=50)
):
    """Full-text search in entity names and descriptions"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        results = rag_instance.query_templates.search_entities_full_text(query, limit=limit)
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Full-text search failed: {str(e)}")


# =============================================================================
# ENTITY ENDPOINTS
# =============================================================================

@app.get("/entity/{entity_id}", tags=["Entities"])
async def get_entity(
    entity_id: str,
    include_relationships: bool = Query(False, description="Include related entities")
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
    entity_type: Optional[str] = Query(None, description="Entity type filter")
):
    """Get entity by name"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        entity = rag_instance.query_templates.get_entity_by_name(entity_name, entity_type)

        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' not found")

        return entity
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity: {str(e)}")


@app.get("/entities/type/{entity_type}", tags=["Entities"])
async def get_entities_by_type(
    entity_type: str,
    limit: int = Query(10, ge=1, le=100)
):
    """Get entities by type"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        entities = rag_instance.query_templates.search_entities_by_type(entity_type, limit=limit)
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
            raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found")

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
        raise HTTPException(status_code=500, detail=f"Failed to get companies: {str(e)}")


@app.get("/companies/sector/{sector}", tags=["Companies"])
async def get_companies_by_sector(sector: str):
    """Get companies in a specific sector"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        companies = rag_instance.query_templates.get_companies_in_sector(sector)
        return {"results": companies, "count": len(companies), "sector": sector}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get companies: {str(e)}")


@app.get("/company/{company_name}/competitive-landscape", tags=["Companies"])
async def get_competitive_landscape(company_name: str):
    """Get competitive landscape for a company"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        landscape = rag_instance.query_templates.get_competitive_landscape(company_name)

        if not landscape:
            raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found")

        return landscape
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get competitive landscape: {str(e)}")


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
            raise HTTPException(status_code=404, detail=f"Investor '{investor_name}' not found")

        return portfolio
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio: {str(e)}")


@app.get("/investors/top", tags=["Investors"])
async def get_top_investors(limit: int = Query(10, ge=1, le=50)):
    """Get most active investors"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        investors = rag_instance.query_templates.get_top_investors(limit)
        return {"results": investors, "count": len(investors)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get investors: {str(e)}")


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
            raise HTTPException(status_code=404, detail=f"Person '{person_name}' not found")

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
    entity_id: str,
    max_hops: int = Query(2, ge=1, le=3)
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
        raise HTTPException(status_code=500, detail=f"Failed to get relationships: {str(e)}")


@app.get("/connection-path", tags=["Relationships"])
async def find_connection_path(
    entity1: str = Query(..., description="First entity name"),
    entity2: str = Query(..., description="Second entity name"),
    max_hops: int = Query(4, ge=1, le=6)
):
    """Find shortest path between two entities"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        paths = rag_instance.query_templates.find_connection_path(entity1, entity2, max_hops)

        if not paths:
            return {"message": f"No connection found between {entity1} and {entity2}", "paths": []}

        return {"entity1": entity1, "entity2": entity2, "paths": paths, "count": len(paths)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find connection: {str(e)}")


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
        raise HTTPException(status_code=500, detail=f"Failed to get communities: {str(e)}")


@app.get("/community/{community_id}", tags=["Communities"])
async def get_community(community_id: int):
    """Get detailed community information"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        community = rag_instance.query_templates.get_community_by_id(community_id)

        if not community:
            raise HTTPException(status_code=404, detail=f"Community {community_id} not found")

        return community
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get community: {str(e)}")


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
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


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
        raise HTTPException(status_code=500, detail=f"Failed to get importance scores: {str(e)}")


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
            raise HTTPException(status_code=404, detail=f"Technology '{technology_name}' not found")

        return adoption
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get technology info: {str(e)}")


@app.get("/technologies/trending", tags=["Technology"])
async def get_trending_technologies(limit: int = Query(10, ge=1, le=50)):
    """Get trending technologies"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        technologies = rag_instance.query_templates.get_trending_technologies(limit)
        return {"results": technologies, "count": len(technologies)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get technologies: {str(e)}")


# =============================================================================
# TEMPORAL ENDPOINTS
# =============================================================================

@app.get("/recent-entities", tags=["Temporal"])
async def get_recent_entities(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50)
):
    """Get recently mentioned entities"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        entities = rag_instance.query_templates.get_recent_entities(days, limit)
        return {"results": entities, "count": len(entities), "days": days}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent entities: {str(e)}")


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
# STATIC FILES & FRONTEND SERVING (must be after all API routes)
# =============================================================================

# Mount static files and SPA route (must be last, after all API routes)
if frontend_dist.exists():
    # Serve static assets
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    
    # Serve frontend index.html for all non-API routes (catch-all, must be last)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend SPA - catch all non-API routes"""
        # Don't serve frontend for API routes
        # Note: /docs/readme is handled by the endpoint above, so it won't reach here
        if full_path.startswith(("api/", "docs/", "redoc", "openapi.json", "health", "query", "search", "company", "investors", "admin")):
            raise HTTPException(status_code=404, detail="Not found")
        
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        raise HTTPException(status_code=404, detail="Frontend not found")


# =============================================================================
# MAIN - Run server
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")

    print(f"🚀 Starting GraphRAG API on {host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"📊 ReDoc Documentation: http://{host}:{port}/redoc")
    if frontend_dist.exists():
        print(f"🌐 Frontend: http://{host}:{port}/")

    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=True,  # Auto-reload on code changes (disable in production)
        log_level="info"
    )
