"""
Analytics tracking for API calls, OpenAI usage, and system metrics
Stores detailed logs of all API interactions for analytics dashboard
"""

import json
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from threading import Lock

# In-memory storage for analytics (can be replaced with Redis/DB later)
_analytics_store: List[Dict[str, Any]] = []
_analytics_lock = Lock()
_max_store_size = 10000  # Keep last 10k records


def track_api_call(
    endpoint: str,
    method: str = "GET",
    status_code: int = 200,
    duration: float = 0.0,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    request_size: int = 0,
    response_size: int = 0,
    **kwargs
):
    """Track an API endpoint call"""
    with _analytics_lock:
        record = {
            "type": "api_call",
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": duration * 1000,
            "user_agent": user_agent,
            "ip_address": ip_address,
            "request_size_bytes": request_size,
            "response_size_bytes": response_size,
            **kwargs
        }
        _analytics_store.append(record)
        _trim_store()


def track_openai_call(
    model: str,
    operation: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    duration: float = 0.0,
    success: bool = True,
    error: Optional[str] = None,
    cost_usd: Optional[float] = None,
    **kwargs
):
    """Track an OpenAI API call"""
    with _analytics_lock:
        record = {
            "type": "openai_call",
            "timestamp": datetime.utcnow().isoformat(),
            "model": model,
            "operation": operation,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "duration_ms": duration * 1000,
            "success": success,
            "error": error,
            "cost_usd": cost_usd or _estimate_cost(model, prompt_tokens, completion_tokens),
            **kwargs
        }
        _analytics_store.append(record)
        _trim_store()


def track_neo4j_query(
    query_type: str,
    duration: float = 0.0,
    success: bool = True,
    result_count: int = 0,
    **kwargs
):
    """Track a Neo4j query"""
    with _analytics_lock:
        record = {
            "type": "neo4j_query",
            "timestamp": datetime.utcnow().isoformat(),
            "query_type": query_type,
            "duration_ms": duration * 1000,
            "success": success,
            "result_count": result_count,
            **kwargs
        }
        _analytics_store.append(record)
        _trim_store()


def track_query_execution(
    query_text: str,
    query_type: str = "natural_language",
    duration: float = 0.0,
    success: bool = True,
    cache_hit: bool = False,
    **kwargs
):
    """Track a GraphRAG query execution"""
    with _analytics_lock:
        record = {
            "type": "query_execution",
            "timestamp": datetime.utcnow().isoformat(),
            "query_text": query_text[:200],  # Truncate long queries
            "query_type": query_type,
            "duration_ms": duration * 1000,
            "success": success,
            "cache_hit": cache_hit,
            **kwargs
        }
        _analytics_store.append(record)
        _trim_store()


def track_pipeline_event(
    phase: str,
    event_type: str = "phase_complete",
    duration: float = 0.0,
    success: bool = True,
    articles_scraped: int = 0,
    articles_extracted: int = 0,
    entities_extracted: int = 0,
    relationships_created: int = 0,
    companies_enriched: int = 0,
    nodes_created: int = 0,
    **kwargs
):
    """Track a pipeline event (scraping, extraction, etc.)"""
    with _analytics_lock:
        record = {
            "type": "pipeline_event",
            "timestamp": datetime.utcnow().isoformat(),
            "phase": phase,  # scraping, extraction, enrichment, graph_building, etc.
            "event_type": event_type,  # phase_complete, phase_start, phase_error
            "duration_ms": duration * 1000,
            "success": success,
            "articles_scraped": articles_scraped,
            "articles_extracted": articles_extracted,
            "entities_extracted": entities_extracted,
            "relationships_created": relationships_created,
            "companies_enriched": companies_enriched,
            "nodes_created": nodes_created,
            **kwargs
        }
        _analytics_store.append(record)
        _trim_store()


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate cost in USD based on model and token usage"""
    # Pricing as of 2024 (per 1M tokens)
    pricing = {
        "gpt-4o": {"prompt": 2.50, "completion": 10.00},
        "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
        "gpt-4": {"prompt": 30.00, "completion": 60.00},
        "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
    }
    
    model_key = model.lower()
    if model_key not in pricing:
        # Default to gpt-4o-mini pricing
        model_key = "gpt-4o-mini"
    
    prompt_cost = (prompt_tokens / 1_000_000) * pricing[model_key]["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * pricing[model_key]["completion"]
    
    return prompt_cost + completion_cost


def _trim_store():
    """Keep only the most recent records"""
    global _analytics_store
    if len(_analytics_store) > _max_store_size:
        _analytics_store = _analytics_store[-_max_store_size:]


def get_analytics_summary(
    hours: int = 24,
    group_by: str = "hour"
) -> Dict[str, Any]:
    """Get analytics summary for the specified time period"""
    with _analytics_lock:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_records = [
            r for r in _analytics_store
            if datetime.fromisoformat(r["timestamp"]) >= cutoff
        ]
        
        # Group by time period
        time_groups = defaultdict(lambda: {
            "api_calls": 0,
            "openai_calls": 0,
            "neo4j_queries": 0,
            "query_executions": 0,
            "pipeline_events": 0,
            "articles_scraped": 0,
            "articles_extracted": 0,
            "entities_extracted": 0,
            "relationships_created": 0,
            "openai_tokens": 0,
            "openai_cost": 0.0,
            "api_errors": 0,
            "openai_errors": 0,
            "avg_api_duration": 0.0,
            "avg_openai_duration": 0.0,
        })
        
        api_durations = []
        openai_durations = []
        
        for record in recent_records:
            ts = datetime.fromisoformat(record["timestamp"])
            if group_by == "hour":
                key = ts.strftime("%Y-%m-%d %H:00")
            elif group_by == "day":
                key = ts.strftime("%Y-%m-%d")
            else:
                key = ts.strftime("%Y-%m-%d %H:%M")
            
            group = time_groups[key]
            
            if record["type"] == "api_call":
                group["api_calls"] += 1
                if record.get("status_code", 200) >= 400:
                    group["api_errors"] += 1
                if record.get("duration_ms"):
                    api_durations.append(record["duration_ms"])
                    
            elif record["type"] == "openai_call":
                group["openai_calls"] += 1
                group["openai_tokens"] += record.get("total_tokens", 0)
                group["openai_cost"] += record.get("cost_usd", 0.0)
                if not record.get("success", True):
                    group["openai_errors"] += 1
                if record.get("duration_ms"):
                    openai_durations.append(record["duration_ms"])
                    
            elif record["type"] == "neo4j_query":
                group["neo4j_queries"] += 1
                
            elif record["type"] == "query_execution":
                group["query_executions"] += 1
                
            elif record["type"] == "pipeline_event":
                group["pipeline_events"] += 1
                group["articles_scraped"] += record.get("articles_scraped", 0)
                group["articles_extracted"] += record.get("articles_extracted", 0)
                group["entities_extracted"] += record.get("entities_extracted", 0)
                group["relationships_created"] += record.get("relationships_created", 0)
        
        # Calculate averages
        if api_durations:
            avg_api_duration = sum(api_durations) / len(api_durations)
            for group in time_groups.values():
                group["avg_api_duration"] = avg_api_duration
                
        if openai_durations:
            avg_openai_duration = sum(openai_durations) / len(openai_durations)
            for group in time_groups.values():
                group["avg_openai_duration"] = avg_openai_duration
        
        # Get endpoint breakdown
        endpoint_counts = defaultdict(int)
        endpoint_errors = defaultdict(int)
        for record in recent_records:
            if record["type"] == "api_call":
                endpoint = record.get("endpoint", "unknown")
                endpoint_counts[endpoint] += 1
                if record.get("status_code", 200) >= 400:
                    endpoint_errors[endpoint] += 1
        
        # Get OpenAI model breakdown
        model_counts = defaultdict(int)
        model_tokens = defaultdict(int)
        model_costs = defaultdict(float)
        for record in recent_records:
            if record["type"] == "openai_call":
                model = record.get("model", "unknown")
                model_counts[model] += 1
                model_tokens[model] += record.get("total_tokens", 0)
                model_costs[model] += record.get("cost_usd", 0.0)
        
        # Get operation breakdown
        operation_counts = defaultdict(int)
        operation_costs = defaultdict(float)
        for record in recent_records:
            if record["type"] == "openai_call":
                operation = record.get("operation", "unknown")
                operation_counts[operation] += 1
                operation_costs[operation] += record.get("cost_usd", 0.0)
        
        return {
            "time_period_hours": hours,
            "total_records": len(recent_records),
            "time_series": dict(sorted(time_groups.items())),
            "endpoints": {
                "counts": dict(endpoint_counts),
                "errors": dict(endpoint_errors)
            },
            "openai_models": {
                "counts": dict(model_counts),
                "tokens": dict(model_tokens),
                "costs": dict(model_costs)
            },
            "openai_operations": {
                "counts": dict(operation_counts),
                "costs": dict(operation_costs)
            },
            "summary": {
                "total_api_calls": sum(g["api_calls"] for g in time_groups.values()),
                "total_openai_calls": sum(g["openai_calls"] for g in time_groups.values()),
                "total_neo4j_queries": sum(g["neo4j_queries"] for g in time_groups.values()),
                "total_query_executions": sum(g["query_executions"] for g in time_groups.values()),
                "total_pipeline_events": sum(g["pipeline_events"] for g in time_groups.values()),
                "total_articles_scraped": sum(g["articles_scraped"] for g in time_groups.values()),
                "total_articles_extracted": sum(g["articles_extracted"] for g in time_groups.values()),
                "total_entities_extracted": sum(g["entities_extracted"] for g in time_groups.values()),
                "total_relationships_created": sum(g["relationships_created"] for g in time_groups.values()),
                "total_openai_tokens": sum(g["openai_tokens"] for g in time_groups.values()),
                "total_openai_cost": sum(g["openai_cost"] for g in time_groups.values()),
                "total_api_errors": sum(g["api_errors"] for g in time_groups.values()),
                "total_openai_errors": sum(g["openai_errors"] for g in time_groups.values()),
            }
        }


def get_recent_calls(limit: int = 100, call_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get recent API/OpenAI calls"""
    with _analytics_lock:
        records = _analytics_store[-limit:] if limit > 0 else _analytics_store
        if call_type:
            records = [r for r in records if r.get("type") == call_type]
        return list(reversed(records))  # Most recent first

