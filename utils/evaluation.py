"""
Evaluation metrics for the GraphRAG system
Measures query quality, performance, accuracy, and system health
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

try:
    from langchain.evaluation import EmbeddingDistance
    from langchain_openai import ChatOpenAI
    HAS_LANGCHAIN_EVAL = True
except ImportError:
    HAS_LANGCHAIN_EVAL = False


@dataclass
class QueryEvaluationResult:
    """Result of evaluating a single query"""
    query: str
    expected_answer: Optional[str] = None
    actual_answer: Optional[str] = None
    context_retrieved: Optional[Any] = None
    
    # Performance metrics
    latency_ms: float = 0.0
    tokens_used: int = 0
    cost_usd: float = 0.0
    
    # Quality metrics
    relevance_score: float = 0.0  # 0-1, how relevant is the answer
    accuracy_score: float = 0.0  # 0-1, how accurate is the answer
    completeness_score: float = 0.0  # 0-1, how complete is the answer
    coherence_score: float = 0.0  # 0-1, how coherent is the answer
    
    # RAG metrics
    context_relevance: float = 0.0  # How relevant is retrieved context
    answer_faithfulness: float = 0.0  # How faithful is answer to context
    answer_relevancy: float = 0.0  # How relevant is answer to query
    
    # System metrics
    cache_hit: bool = False
    error: Optional[str] = None
    success: bool = True
    
    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    model_used: Optional[str] = None
    endpoint: str = "/query"
    
    # Detailed logs and calculation breakdowns
    logs: List[str] = field(default_factory=list)
    calculation_details: Dict[str, Any] = field(default_factory=dict)
    intent_classified: Optional[str] = None
    context_size: int = 0
    context_entities: List[str] = field(default_factory=list)


@dataclass
class EvaluationSummary:
    """Summary of evaluation results"""
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    
    # Performance metrics
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    
    # Quality metrics
    avg_relevance: float = 0.0
    avg_accuracy: float = 0.0
    avg_completeness: float = 0.0
    avg_coherence: float = 0.0
    
    # RAG metrics
    avg_context_relevance: float = 0.0
    avg_answer_faithfulness: float = 0.0
    avg_answer_relevancy: float = 0.0
    
    # Cache metrics
    cache_hit_rate: float = 0.0
    
    # Error rate
    error_rate: float = 0.0
    
    # Results
    results: List[QueryEvaluationResult] = field(default_factory=list)


class QueryEvaluator:
    """Evaluate query performance and quality"""
    
    def __init__(self, rag_instance=None, openai_api_key: Optional[str] = None):
        self.rag_instance = rag_instance
        self.openai_api_key = openai_api_key
        self.evaluator_llm = None
        
        if openai_api_key and HAS_LANGCHAIN_EVAL:
            try:
                self.evaluator_llm = ChatOpenAI(
                    temperature=0,
                    model="gpt-4o-mini",
                    api_key=openai_api_key
                )
            except Exception:
                pass
    
    def evaluate_query(
        self,
        query: str,
        expected_answer: Optional[str] = None,
        use_llm: bool = True
    ) -> QueryEvaluationResult:
        """
        Evaluate a single query
        
        Args:
            query: The query to evaluate
            expected_answer: Optional expected answer for accuracy comparison
            use_llm: Whether to use LLM for answer generation
            
        Returns:
            QueryEvaluationResult with all metrics
        """
        result = QueryEvaluationResult(query=query, expected_answer=expected_answer)
        start_time = time.time()
        
        try:
            result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Starting evaluation for query: '{query}'")
            
            # Execute query
            query_start = time.time()
            result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Executing query through RAG system...")
            
            response = self.rag_instance.query(
                question=query,
                return_context=True,
                use_llm=use_llm
            )
            
            query_latency = (time.time() - query_start) * 1000
            result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Query completed in {query_latency:.2f}ms")
            
            result.actual_answer = response.get("answer", "")
            result.context_retrieved = response.get("context")
            
            # Handle intent - could be string or object
            intent_data = response.get("intent", "unknown")
            if isinstance(intent_data, dict):
                result.intent_classified = intent_data.get("intent", "unknown")
            else:
                result.intent_classified = str(intent_data) if intent_data else "unknown"
            
            result.latency_ms = (time.time() - start_time) * 1000
            result.success = True
            
            result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Intent classified as: {result.intent_classified}")
            
            # Extract metadata if available (response is a dict, not an object)
            if isinstance(response, dict):
                result.tokens_used = response.get("tokens_used", 0)
                result.cost_usd = response.get("cost_usd", 0.0)
                result.model_used = response.get("model", None)
                result.cache_hit = response.get("cache_hit", False)
                
                if result.tokens_used > 0:
                    result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Tokens used: {result.tokens_used}, Cost: ${result.cost_usd:.4f}")
                if result.cache_hit:
                    result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] ⚡ Cache hit - response served from cache")
            
            # Analyze context
            if result.context_retrieved:
                context_str = str(result.context_retrieved)
                result.context_size = len(context_str)
                
                # Try to extract entity names from context
                if isinstance(result.context_retrieved, dict):
                    # Look for common entity keys
                    entities = []
                    for key in ['entities', 'nodes', 'results', 'data']:
                        if key in result.context_retrieved:
                            data = result.context_retrieved[key]
                            if isinstance(data, list):
                                for item in data[:10]:  # Limit to first 10
                                    if isinstance(item, dict):
                                        name = item.get('name') or item.get('label') or item.get('title')
                                        if name:
                                            entities.append(str(name))
                    result.context_entities = entities[:10]  # Limit to 10
                
                result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Context retrieved: {result.context_size} characters, {len(result.context_entities)} entities identified")
            
            # Calculate quality metrics
            if result.actual_answer:
                result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Calculating quality metrics...")
                
                # Relevance calculation
                relevance_details = self._calculate_relevance_with_details(query, result.actual_answer)
                result.relevance_score = relevance_details['score']
                result.calculation_details['relevance'] = relevance_details
                result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Relevance score: {result.relevance_score:.3f} ({relevance_details.get('explanation', '')})")
                
                # Coherence calculation
                coherence_details = self._calculate_coherence_with_details(result.actual_answer)
                result.coherence_score = coherence_details['score']
                result.calculation_details['coherence'] = coherence_details
                result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Coherence score: {result.coherence_score:.3f} ({coherence_details.get('explanation', '')})")
                
                if expected_answer:
                    # Accuracy calculation
                    accuracy_details = self._calculate_accuracy_with_details(
                        expected_answer, 
                        result.actual_answer
                    )
                    result.accuracy_score = accuracy_details['score']
                    result.calculation_details['accuracy'] = accuracy_details
                    result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Accuracy score: {result.accuracy_score:.3f} ({accuracy_details.get('explanation', '')})")
                    
                    # Completeness calculation
                    completeness_details = self._calculate_completeness_with_details(
                        expected_answer,
                        result.actual_answer
                    )
                    result.completeness_score = completeness_details['score']
                    result.calculation_details['completeness'] = completeness_details
                    result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Completeness score: {result.completeness_score:.3f} ({completeness_details.get('explanation', '')})")
                
                # RAG-specific metrics
                if result.context_retrieved:
                    result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Calculating RAG metrics...")
                    
                    # Context relevance
                    ctx_rel_details = self._calculate_context_relevance_with_details(
                        query,
                        result.context_retrieved
                    )
                    result.context_relevance = ctx_rel_details['score']
                    result.calculation_details['context_relevance'] = ctx_rel_details
                    result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Context relevance: {result.context_relevance:.3f} ({ctx_rel_details.get('explanation', '')})")
                    
                    # Answer faithfulness
                    faithfulness_details = self._calculate_faithfulness_with_details(
                        result.actual_answer,
                        result.context_retrieved
                    )
                    result.answer_faithfulness = faithfulness_details['score']
                    result.calculation_details['answer_faithfulness'] = faithfulness_details
                    result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Answer faithfulness: {result.answer_faithfulness:.3f} ({faithfulness_details.get('explanation', '')})")
                    
                    # Answer relevancy
                    answer_rel_details = self._calculate_answer_relevancy_with_details(
                        query,
                        result.actual_answer
                    )
                    result.answer_relevancy = answer_rel_details['score']
                    result.calculation_details['answer_relevancy'] = answer_rel_details
                    result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Answer relevancy: {result.answer_relevancy:.3f} ({answer_rel_details.get('explanation', '')})")
            
            result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] ✅ Evaluation completed successfully")
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            result.latency_ms = (time.time() - start_time) * 1000
            result.logs.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] ❌ Error: {str(e)}")
        
        return result
    
    def evaluate_batch(
        self,
        queries: List[Dict[str, Any]],
        use_llm: bool = True
    ) -> EvaluationSummary:
        """
        Evaluate a batch of queries
        
        Args:
            queries: List of dicts with 'query' and optionally 'expected_answer'
            use_llm: Whether to use LLM for answer generation
            
        Returns:
            EvaluationSummary with aggregated metrics
        """
        results = []
        
        for query_data in queries:
            query = query_data.get("query", "")
            expected = query_data.get("expected_answer")
            
            result = self.evaluate_query(query, expected, use_llm)
            results.append(result)
        
        return self._summarize_results(results)
    
    def _calculate_relevance(self, query: str, answer: str) -> float:
        """Calculate how relevant the answer is to the query (0-1)"""
        if not answer or not query:
            return 0.0
        
        # Simple keyword overlap
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        
        if not query_words:
            return 0.0
        
        overlap = len(query_words.intersection(answer_words))
        return min(overlap / len(query_words), 1.0)
    
    def _calculate_relevance_with_details(self, query: str, answer: str) -> Dict[str, Any]:
        """Calculate relevance with detailed breakdown"""
        if not answer or not query:
            return {"score": 0.0, "explanation": "Empty query or answer"}
        
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        
        if not query_words:
            return {"score": 0.0, "explanation": "Query has no words"}
        
        overlap_words = query_words.intersection(answer_words)
        overlap_count = len(overlap_words)
        total_query_words = len(query_words)
        score = min(overlap_count / total_query_words, 1.0)
        
        return {
            "score": score,
            "explanation": f"{overlap_count}/{total_query_words} query words found in answer",
            "query_words": list(query_words),
            "overlap_words": list(overlap_words),
            "method": "Keyword overlap (Jaccard similarity)"
        }
    
    def _calculate_accuracy(self, expected: str, actual: str) -> float:
        """Calculate accuracy by comparing expected vs actual (0-1)"""
        if not expected or not actual:
            return 0.0
        
        # Simple word overlap
        expected_words = set(expected.lower().split())
        actual_words = set(actual.lower().split())
        
        if not expected_words:
            return 0.0
        
        overlap = len(expected_words.intersection(actual_words))
        return min(overlap / len(expected_words), 1.0)
    
    def _calculate_accuracy_with_details(self, expected: str, actual: str) -> Dict[str, Any]:
        """Calculate accuracy with detailed breakdown"""
        if not expected or not actual:
            return {"score": 0.0, "explanation": "Missing expected or actual answer"}
        
        expected_words = set(expected.lower().split())
        actual_words = set(actual.lower().split())
        
        if not expected_words:
            return {"score": 0.0, "explanation": "Expected answer has no words"}
        
        overlap_words = expected_words.intersection(actual_words)
        overlap_count = len(overlap_words)
        total_expected = len(expected_words)
        score = min(overlap_count / total_expected, 1.0)
        
        return {
            "score": score,
            "explanation": f"{overlap_count}/{total_expected} expected words found in actual answer",
            "expected_words": list(expected_words),
            "overlap_words": list(overlap_words),
            "method": "Word overlap between expected and actual"
        }
    
    def _calculate_completeness(self, expected: str, actual: str) -> float:
        """Calculate how complete the answer is (0-1)"""
        if not expected or not actual:
            return 0.0
        
        # Check if key information from expected is present
        expected_key_terms = set(expected.lower().split())
        actual_terms = set(actual.lower().split())
        
        if not expected_key_terms:
            return 0.0
        
        coverage = len(expected_key_terms.intersection(actual_terms)) / len(expected_key_terms)
        return min(coverage, 1.0)
    
    def _calculate_completeness_with_details(self, expected: str, actual: str) -> Dict[str, Any]:
        """Calculate completeness with detailed breakdown"""
        if not expected or not actual:
            return {"score": 0.0, "explanation": "Missing expected or actual answer"}
        
        expected_terms = set(expected.lower().split())
        actual_terms = set(actual.lower().split())
        
        if not expected_terms:
            return {"score": 0.0, "explanation": "Expected answer has no terms"}
        
        covered_terms = expected_terms.intersection(actual_terms)
        coverage_count = len(covered_terms)
        total_expected = len(expected_terms)
        score = min(coverage_count / total_expected, 1.0)
        
        return {
            "score": score,
            "explanation": f"{coverage_count}/{total_expected} expected terms covered",
            "expected_terms": list(expected_terms),
            "covered_terms": list(covered_terms),
            "method": "Term coverage analysis"
        }
    
    def _calculate_coherence(self, answer: str) -> float:
        """Calculate answer coherence (0-1)"""
        if not answer:
            return 0.0
        
        # Simple heuristic: check for sentence structure
        sentences = answer.split('.')
        if len(sentences) < 2:
            return 0.5  # Single sentence, moderate coherence
        
        # Check average sentence length (coherent answers have reasonable length)
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        # Ideal sentence length is 10-20 words
        if 10 <= avg_length <= 20:
            return 1.0
        elif 5 <= avg_length < 10 or 20 < avg_length <= 30:
            return 0.7
        else:
            return 0.4
    
    def _calculate_coherence_with_details(self, answer: str) -> Dict[str, Any]:
        """Calculate coherence with detailed breakdown"""
        if not answer:
            return {"score": 0.0, "explanation": "Empty answer"}
        
        sentences = [s.strip() for s in answer.split('.') if s.strip()]
        sentence_count = len(sentences)
        
        if sentence_count < 2:
            return {
                "score": 0.5,
                "explanation": "Single sentence - moderate coherence",
                "sentence_count": sentence_count,
                "method": "Sentence structure analysis"
            }
        
        sentence_lengths = [len(s.split()) for s in sentences]
        avg_length = sum(sentence_lengths) / len(sentence_lengths)
        
        # Score based on sentence length
        if 10 <= avg_length <= 20:
            score = 1.0
            explanation = f"Optimal sentence length ({avg_length:.1f} words avg)"
        elif 5 <= avg_length < 10 or 20 < avg_length <= 30:
            score = 0.7
            explanation = f"Acceptable sentence length ({avg_length:.1f} words avg)"
        else:
            score = 0.4
            explanation = f"Suboptimal sentence length ({avg_length:.1f} words avg)"
        
        return {
            "score": score,
            "explanation": explanation,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_length, 1),
            "sentence_lengths": sentence_lengths,
            "method": "Sentence structure and length analysis"
        }
    
    def _calculate_context_relevance(self, query: str, context: Any) -> float:
        """Calculate how relevant the retrieved context is (0-1)"""
        if not context:
            return 0.0
        
        # Convert context to string
        context_str = str(context).lower()
        query_words = set(query.lower().split())
        
        if not query_words:
            return 0.0
        
        # Count query word occurrences in context
        matches = sum(1 for word in query_words if word in context_str)
        return min(matches / len(query_words), 1.0)
    
    def _calculate_context_relevance_with_details(self, query: str, context: Any) -> Dict[str, Any]:
        """Calculate context relevance with detailed breakdown"""
        if not context:
            return {"score": 0.0, "explanation": "No context retrieved"}
        
        context_str = str(context).lower()
        query_words = set(query.lower().split())
        
        if not query_words:
            return {"score": 0.0, "explanation": "Query has no words"}
        
        matched_words = [word for word in query_words if word in context_str]
        match_count = len(matched_words)
        total_query_words = len(query_words)
        score = min(match_count / total_query_words, 1.0)
        
        return {
            "score": score,
            "explanation": f"{match_count}/{total_query_words} query words found in context",
            "query_words": list(query_words),
            "matched_words": matched_words,
            "context_size": len(context_str),
            "method": "Query word matching in context"
        }
    
    def _calculate_faithfulness(self, answer: str, context: Any) -> float:
        """Calculate how faithful the answer is to the context (0-1)"""
        if not answer or not context:
            return 0.0
        
        context_str = str(context).lower()
        answer_words = set(answer.lower().split())
        
        # Check how many answer words appear in context
        context_words = set(context_str.split())
        overlap = len(answer_words.intersection(context_words))
        
        if not answer_words:
            return 0.0
        
        return min(overlap / len(answer_words), 1.0)
    
    def _calculate_faithfulness_with_details(self, answer: str, context: Any) -> Dict[str, Any]:
        """Calculate faithfulness with detailed breakdown"""
        if not answer or not context:
            return {"score": 0.0, "explanation": "Missing answer or context"}
        
        context_str = str(context).lower()
        answer_words = set(answer.lower().split())
        context_words = set(context_str.split())
        
        if not answer_words:
            return {"score": 0.0, "explanation": "Answer has no words"}
        
        grounded_words = answer_words.intersection(context_words)
        grounded_count = len(grounded_words)
        total_answer_words = len(answer_words)
        score = min(grounded_count / total_answer_words, 1.0)
        
        return {
            "score": score,
            "explanation": f"{grounded_count}/{total_answer_words} answer words found in context",
            "answer_word_count": total_answer_words,
            "grounded_words": list(grounded_words)[:20],  # Limit to first 20
            "method": "Answer word grounding in context"
        }
    
    def _calculate_answer_relevancy(self, query: str, answer: str) -> float:
        """Calculate how relevant the answer is to the query (0-1)"""
        # Same as relevance, but can be enhanced with LLM
        return self._calculate_relevance(query, answer)
    
    def _calculate_answer_relevancy_with_details(self, query: str, answer: str) -> Dict[str, Any]:
        """Calculate answer relevancy with detailed breakdown"""
        return self._calculate_relevance_with_details(query, answer)
    
    def _summarize_results(self, results: List[QueryEvaluationResult]) -> EvaluationSummary:
        """Aggregate evaluation results into summary"""
        summary = EvaluationSummary()
        summary.results = results
        summary.total_queries = len(results)
        
        successful = [r for r in results if r.success]
        summary.successful_queries = len(successful)
        summary.failed_queries = summary.total_queries - summary.successful_queries
        
        if not successful:
            return summary
        
        # Performance metrics
        latencies = [r.latency_ms for r in successful]
        latencies.sort()
        summary.avg_latency_ms = sum(latencies) / len(latencies)
        summary.p50_latency_ms = latencies[len(latencies) // 2]
        summary.p95_latency_ms = latencies[int(len(latencies) * 0.95)]
        summary.p99_latency_ms = latencies[int(len(latencies) * 0.99)]
        
        summary.total_tokens = sum(r.tokens_used for r in successful)
        summary.total_cost_usd = sum(r.cost_usd for r in successful)
        
        # Quality metrics
        summary.avg_relevance = sum(r.relevance_score for r in successful) / len(successful)
        summary.avg_accuracy = sum(r.accuracy_score for r in successful if r.accuracy_score > 0) / max(1, sum(1 for r in successful if r.accuracy_score > 0))
        summary.avg_completeness = sum(r.completeness_score for r in successful if r.completeness_score > 0) / max(1, sum(1 for r in successful if r.completeness_score > 0))
        summary.avg_coherence = sum(r.coherence_score for r in successful) / len(successful)
        
        # RAG metrics
        summary.avg_context_relevance = sum(r.context_relevance for r in successful if r.context_relevance > 0) / max(1, sum(1 for r in successful if r.context_relevance > 0))
        summary.avg_answer_faithfulness = sum(r.answer_faithfulness for r in successful if r.answer_faithfulness > 0) / max(1, sum(1 for r in successful if r.answer_faithfulness > 0))
        summary.avg_answer_relevancy = sum(r.answer_relevancy for r in successful) / len(successful)
        
        # Cache metrics
        cache_hits = sum(1 for r in successful if r.cache_hit)
        summary.cache_hit_rate = cache_hits / len(successful) if successful else 0.0
        
        # Error rate
        summary.error_rate = summary.failed_queries / summary.total_queries if summary.total_queries > 0 else 0.0
        
        return summary


def create_sample_evaluation_dataset() -> List[Dict[str, Any]]:
    """Create a sample dataset for evaluation"""
    return [
        {
            "query": "Which AI startups raised funding recently?",
            "expected_answer": "Information about AI startups that received funding"
        },
        {
            "query": "What companies are using OpenAI technology?",
            "expected_answer": "Companies adopting OpenAI's technology"
        },
        {
            "query": "Who are the top investors in the tech industry?",
            "expected_answer": "List of prominent tech investors"
        },
        {
            "query": "Tell me about Anthropic",
            "expected_answer": "Information about Anthropic company"
        },
        {
            "query": "What is the relationship between Sam Altman and OpenAI?",
            "expected_answer": "Sam Altman's role at OpenAI"
        }
    ]

