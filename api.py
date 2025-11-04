"""
FastAPI REST API for GraphRAG Query System
Provides HTTP endpoints for querying the knowledge graph
"""

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import subprocess
import threading
import io
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from rag_query import GraphRAGQuery, create_rag_query
from query_templates import QueryTemplates

# Load environment variables
load_dotenv()

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
    print("🚀 Starting GraphRAG API...")
    try:
        rag_instance = create_rag_query()
        print("✅ GraphRAG instance initialized")
    except Exception as e:
        print(f"❌ Failed to initialize GraphRAG: {e}")
        raise

    yield

    # Shutdown
    print("🛑 Shutting down GraphRAG API...")
    if rag_instance:
        rag_instance.close()
        print("✅ GraphRAG instance closed")


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="GraphRAG API",
    description="REST API for TechCrunch Knowledge Graph Query System",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "GraphRAG API",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health():
    """Detailed health check"""
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        # Test database connection
        stats = rag_instance.query_templates.get_graph_statistics()
        return {
            "status": "healthy",
            "database": "connected",
            "graph_stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {e}")


# =============================================================================
# ADMIN / PIPELINE CONTROL ENDPOINTS
# =============================================================================

# Simple in-process state for a single pipeline run
pipeline_proc: Optional[subprocess.Popen] = None
pipeline_log_path: str = os.getenv("PIPELINE_LOG_PATH", "pipeline.log")


def _build_pipeline_args(options: PipelineStartRequest) -> List[str]:
    args: List[str] = ["python", "pipeline.py"]
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


# =============================================================================
# MAIN QUERY ENDPOINTS
# =============================================================================

@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query(request: QueryRequest):
    """
    Main query endpoint - natural language questions

    This endpoint handles natural language questions and returns AI-generated answers
    based on the knowledge graph context.
    """
    if not rag_instance:
        raise HTTPException(status_code=503, detail="RAG instance not initialized")

    try:
        result = rag_instance.query(
            question=request.question,
            return_context=request.return_context,
            use_llm=request.use_llm
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


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
# MAIN - Run server
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")

    print(f"🚀 Starting GraphRAG API on {host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"📊 ReDoc Documentation: http://{host}:{port}/redoc")

    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=True,  # Auto-reload on code changes (disable in production)
        log_level="info"
    )
