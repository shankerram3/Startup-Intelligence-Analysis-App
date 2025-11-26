"""
GraphRAG Query Module
Combines semantic search with graph traversal and LLM generation
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from neo4j import Driver, GraphDatabase

from query_templates import QueryTemplates
from utils.embedding_generator import EmbeddingGenerator


class GraphRAGQuery:
    """
    Main GraphRAG Query interface
    Combines semantic search, graph traversal, and LLM generation
    """

    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        openai_api_key: Optional[str] = None,
        embedding_model: str = "openai",
    ):
        """
        Initialize GraphRAG Query system

        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            openai_api_key: OpenAI API key (for embeddings and generation)
            embedding_model: Embedding model to use (openai or sentence_transformers)
        """
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.embedding_generator = EmbeddingGenerator(self.driver, embedding_model)
        self.query_templates = QueryTemplates(self.driver)

        # Initialize LLM for answer generation
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.llm = None
        if self.openai_api_key:
            self._initialize_llm()

    def _initialize_llm(self):
        """Initialize LLM for answer generation"""
        try:
            from langchain_openai import ChatOpenAI

            self.llm = ChatOpenAI(
                temperature=0.7, model="gpt-4o", api_key=self.openai_api_key
            )
        except ImportError:
            print(
                "⚠️  LangChain not installed. Install with: pip install langchain-openai"
            )
        except Exception as e:
            print(f"⚠️  Error initializing LLM: {e}")

    def close(self):
        """Close Neo4j connection"""
        self.driver.close()

    # =========================================================================
    # SEMANTIC SEARCH
    # =========================================================================

    def semantic_search(
        self, query: str, top_k: int = 10, entity_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Perform semantic search using embeddings

        Args:
            query: Search query
            top_k: Number of results to return
            entity_type: Optional entity type filter

        Returns:
            List of similar entities with similarity scores
        """
        similar_entities = self.embedding_generator.find_similar_entities(
            query, limit=top_k
        )

        # Filter by entity type if specified
        if entity_type:
            similar_entities = [
                e
                for e in similar_entities
                if e.get("type", "").lower() == entity_type.lower()
            ]

        return similar_entities

    def hybrid_search(
        self, query: str, top_k: int = 10, semantic_weight: float = 0.7
    ) -> List[Dict]:
        """
        Hybrid search combining semantic similarity and keyword matching

        Args:
            query: Search query
            top_k: Number of results
            semantic_weight: Weight for semantic search (0-1)

        Returns:
            Combined search results
        """
        # Semantic search
        semantic_results = self.semantic_search(query, top_k=top_k * 2)

        # Keyword search
        keyword_results = self.query_templates.search_entities_full_text(
            query, limit=top_k * 2
        )

        # Combine and re-rank
        combined = {}

        for result in semantic_results:
            entity_id = result["id"]
            combined[entity_id] = {
                **result,
                "score": result["similarity"] * semantic_weight,
            }

        for result in keyword_results:
            entity_id = result["id"]
            if entity_id in combined:
                # Boost entities found in both searches
                combined[entity_id]["score"] += 1 - semantic_weight
            else:
                combined[entity_id] = {**result, "score": (1 - semantic_weight)}

        # Sort by score
        ranked_results = sorted(
            combined.values(), key=lambda x: x["score"], reverse=True
        )

        return ranked_results[:top_k]

    # =========================================================================
    # CONTEXT RETRIEVAL
    # =========================================================================

    def get_entity_context(
        self, entity_id: str, max_hops: int = 2, max_entities: int = 20
    ) -> Dict:
        """
        Get rich context around an entity (subgraph)

        Args:
            entity_id: Entity ID
            max_hops: Maximum relationship hops
            max_entities: Maximum entities to include

        Returns:
            Entity context with relationships
        """
        return self.query_templates.get_entity_relationships(
            entity_id, max_hops=max_hops
        )

    def get_multi_entity_context(
        self, entity_ids: List[str], max_hops: int = 2
    ) -> Dict:
        """
        Get context for multiple entities and their connections

        Args:
            entity_ids: List of entity IDs
            max_hops: Maximum relationship hops

        Returns:
            Combined context for all entities
        """
        contexts = []
        for entity_id in entity_ids:
            context = self.get_entity_context(entity_id, max_hops=max_hops)
            if context:
                contexts.append(context)

        return {"entities": contexts, "entity_count": len(contexts)}

    # =========================================================================
    # QUERY ROUTING
    # =========================================================================

    def classify_query_intent(self, query: str) -> Dict:
        """
        Classify query intent to route to appropriate handlers

        Args:
            query: User query

        Returns:
            Intent classification with confidence and extracted parameters
        """
        query_lower = query.lower()

        # Detect if this is a list query (asking for multiple entities)
        # "Which" and "What are" are strong list indicators
        # "What" alone could be singular, so check for plural indicators
        has_plural = any(
            word in query_lower
            for word in ["companies", "startups", "investors", "firms", "businesses"]
        )
        is_list_query = (
            query_lower.startswith("which ")
            or query_lower.startswith("what are ")
            or query_lower.startswith("list ")
            or query_lower.startswith("show ")
            or (query_lower.startswith("what ") and has_plural)
            or any(
                f" {word} " in f" {query_lower} "
                for word in ["which", "list", "show", "all"]
            )
        )

        # Detect temporal context
        is_recent = any(
            word in query_lower
            for word in ["recent", "recently", "latest", "new", "last"]
        )

        # Detect sector/category filters (use word boundaries to avoid partial matches)
        sector = None
        import re

        for sector_keyword in [
            "artificial intelligence",
            "machine learning",
            "fintech",
            "blockchain",
            "crypto",
            "saas",
            "healthcare",
            "biotech",
            "ai",
            "ml",
        ]:
            # Use word boundaries for short keywords to avoid false matches
            if len(sector_keyword) <= 2:
                pattern = r"\b" + re.escape(sector_keyword) + r"\b"
            else:
                pattern = re.escape(sector_keyword)
            if re.search(pattern, query_lower):
                sector = sector_keyword
                break

        # Check for funding-related queries first (higher priority)
        has_funding_keywords = any(
            word in query_lower
            for word in ["funding", "raised", "invested", "series", "investment"]
        )

        if has_funding_keywords:
            # Check if it's asking about investor info
            if any(
                word in query_lower
                for word in ["who funded", "which investors", "who invested"]
            ):
                return {"intent": "funding_info", "confidence": 0.9}
            # Check if it's a list query asking for multiple companies
            elif is_list_query:
                return {
                    "intent": "list_funded_companies",
                    "confidence": 0.9,
                    "filters": {"sector": sector, "recent": is_recent},
                }
            # Single company funding query
            else:
                return {"intent": "funding_info", "confidence": 0.9}

        # Company-related queries
        has_company_keywords = any(
            word in query_lower
            for word in [
                "company",
                "companies",
                "startup",
                "startups",
                "firm",
                "business",
            ]
        )

        # Check if it's a "tell me about X" or "about X" query (likely company info)
        is_about_query = any(
            phrase in query_lower
            for phrase in ["tell me about", "about ", "what is", "who is"]
        )

        if has_company_keywords or (
            is_about_query
            and not any(
                word in query_lower
                for word in ["investor", "vc", "person", "technology"]
            )
        ):
            if any(
                word in query_lower
                for word in ["competitor", "compete", "vs", "compared to"]
            ):
                return {"intent": "competitive_analysis", "confidence": 0.9}
            elif any(
                word in query_lower for word in ["founder", "founded", "ceo", "team"]
            ):
                return {"intent": "company_leadership", "confidence": 0.8}
            else:
                # Check if asking for list of companies in a sector
                if is_list_query and sector:
                    return {
                        "intent": "list_companies_in_sector",
                        "confidence": 0.85,
                        "filters": {"sector": sector},
                    }
                return {"intent": "company_info", "confidence": 0.7}

        # Investor queries
        elif any(
            word in query_lower
            for word in ["investor", "vc", "venture capital", "fund"]
        ):
            if any(
                word in query_lower for word in ["portfolio", "invested in", "backed"]
            ):
                return {"intent": "investor_portfolio", "confidence": 0.9}
            else:
                return {"intent": "investor_info", "confidence": 0.7}

        # Person queries
        elif any(
            word in query_lower
            for word in ["who is", "person", "founder", "ceo", "executive"]
        ):
            return {"intent": "person_info", "confidence": 0.8}

        # Technology queries
        elif any(
            word in query_lower
            for word in ["technology", "tech", "ai", "ml", "blockchain"]
        ):
            return {"intent": "technology_info", "confidence": 0.8}

        # Trend queries
        elif any(
            word in query_lower for word in ["trend", "popular", "growing", "emerging"]
        ):
            return {"intent": "trend_analysis", "confidence": 0.8}

        # Relationship queries
        elif any(
            word in query_lower
            for word in ["connection", "related", "link", "relationship"]
        ):
            return {"intent": "relationship_query", "confidence": 0.8}

        # General search
        else:
            return {"intent": "general_search", "confidence": 0.5}

    def _enrich_with_article_urls(self, context: Any) -> Any:
        """
        Enrich context results with article URLs from source_articles

        Args:
            context: Context data (dict, list, or nested structure)

        Returns:
            Context enriched with article URLs
        """
        if isinstance(context, list):
            # Enrich each item in the list
            enriched = []
            for item in context:
                if isinstance(item, dict):
                    # Recursively enrich nested structures
                    enriched_item = self._enrich_with_article_urls(item)
                    enriched.append(enriched_item)
                else:
                    enriched.append(item)
            return enriched
        elif isinstance(context, dict):
            # Enrich single entity or nested dict
            enriched = dict(context)

            # If this dict has an entity ID, get article URLs
            if enriched.get("id"):
                entity_id = enriched["id"]
                source_articles = enriched.get("source_articles")
                article_urls = self._get_article_urls_for_entity(
                    entity_id, source_articles
                )
                if article_urls:
                    enriched["article_urls"] = article_urls

            # Recursively enrich nested dicts (like portfolio, investors, etc.)
            for key, value in enriched.items():
                if isinstance(value, (dict, list)):
                    enriched[key] = self._enrich_with_article_urls(value)

            return enriched
        else:
            return context

    def _get_article_urls_for_entity(
        self, entity_id: str, source_articles: Optional[List[str]] = None
    ) -> List[str]:
        """Get article URLs for an entity"""
        with self.driver.session() as session:
            if source_articles:
                # Use provided article IDs
                result = session.run(
                    """
                    UNWIND $article_ids as article_id
                    MATCH (a:Article {id: article_id})
                    RETURN collect(DISTINCT a.url) as urls
                """,
                    article_ids=source_articles,
                )
            else:
                # Get from entity's source_articles property
                result = session.run(
                    """
                    MATCH (e {id: $entity_id})
                    WHERE e.source_articles IS NOT NULL
                    UNWIND e.source_articles as article_id
                    MATCH (a:Article {id: article_id})
                    RETURN collect(DISTINCT a.url) as urls
                """,
                    entity_id=entity_id,
                )

            record = result.single()
            return record["urls"] if record and record.get("urls") else []

    def route_query(self, query: str, intent: Dict) -> Any:
        """
        Route query to appropriate handler based on intent

        Args:
            query: User query
            intent: Intent classification with optional filters

        Returns:
            Query results
        """
        intent_type = intent["intent"]
        filters = intent.get("filters", {})

        if intent_type == "company_info":
            # Extract company name from query
            results = self.semantic_search(query, top_k=1, entity_type="Company")
            if results:
                company = results[0]
                return self.query_templates.get_company_profile(company["name"])

        elif intent_type == "competitive_analysis":
            results = self.semantic_search(query, top_k=1, entity_type="Company")
            if results:
                company = results[0]
                return self.query_templates.get_competitive_landscape(company["name"])

        elif intent_type == "funding_info":
            results = self.semantic_search(query, top_k=1, entity_type="Company")
            if results:
                company = results[0]
                return self.query_templates.get_funding_timeline(company["name"])

        elif intent_type == "list_funded_companies":
            # Get list of companies with funding, optionally filtered by sector and recency
            sector = filters.get("sector")
            is_recent = filters.get("recent", False)

            if is_recent:
                # Get recently funded companies (last 90 days)
                return self.query_templates.get_recently_funded_companies(
                    days=90, sector_keyword=sector
                )
            elif sector:
                # Get companies in sector with funding info
                companies = self.query_templates.get_companies_in_sector(sector)
                # Enrich with funding information
                funded_companies = [
                    c for c in companies if c.get("investor_count", 0) > 0
                ]
                return funded_companies[:20]
            else:
                # Get all companies with funding
                return self.query_templates.get_companies_by_funding(min_investors=1)

        elif intent_type == "list_companies_in_sector":
            # Get companies in a specific sector
            sector = filters.get("sector")
            if sector:
                return self.query_templates.get_companies_in_sector(sector)
            else:
                # Fallback to general search
                return self.hybrid_search(query, top_k=10)

        elif intent_type == "investor_portfolio":
            results = self.semantic_search(query, top_k=1, entity_type="Investor")
            if results:
                investor = results[0]
                return self.query_templates.get_investor_portfolio(investor["name"])

        elif intent_type == "person_info":
            results = self.semantic_search(query, top_k=1, entity_type="Person")
            if results:
                person = results[0]
                return self.query_templates.get_person_profile(person["name"])

        elif intent_type == "technology_info":
            results = self.semantic_search(query, top_k=5, entity_type="Technology")
            return results

        elif intent_type == "trend_analysis":
            return self.query_templates.get_trending_technologies(limit=10)

        else:
            # General semantic search
            return self.hybrid_search(query, top_k=10)

    # =========================================================================
    # LLM GENERATION
    # =========================================================================

    def generate_answer(
        self, query: str, context: Any, temperature: float = 0.7
    ) -> str:
        """
        Generate natural language answer using LLM and context

        Args:
            query: User question
            context: Retrieved context from graph
            temperature: LLM temperature

        Returns:
            Generated answer
        """
        if not self.llm:
            return "LLM not initialized. Please provide OpenAI API key."

        # Format context for LLM
        context_str = self._format_context_for_llm(context)

        # Check if context is empty or minimal
        has_minimal_context = (
            not context_str
            or context_str.strip() in ["{}", "[]", "null", ""]
            or len(context_str.strip()) < 50
        )

        # Create prompt
        if has_minimal_context:
            prompt = f"""You are a knowledge graph assistant analyzing startup and tech industry data from TechCrunch articles.

User Question: {query}

Note: The knowledge graph search didn't return much relevant context for this question.

Please provide a helpful response:
1. If you can answer based on general knowledge about the topic, provide that answer
2. If the question is about specific data that should be in the knowledge graph, explain that the graph doesn't contain enough relevant information to answer this specific question
3. Suggest what kind of data would be needed to answer this question (e.g., "To answer this, the knowledge graph would need information about companies located in India and their characteristics")

Be helpful and informative, even if you can't provide a complete answer based on the graph data.

Answer:"""
        else:
            prompt = f"""You are a knowledge graph assistant analyzing startup and tech industry data from TechCrunch articles.

Context from Knowledge Graph:
{context_str}

User Question: {query}

Instructions:
1. Answer the question based on the provided context from the knowledge graph
2. Be specific and cite entity names when possible
3. If the context doesn't directly answer the question, you can make reasonable inferences based on the available data
4. If there's no relevant data in the context, clearly state that the knowledge graph doesn't contain enough information to answer this question
5. Provide insights by connecting related information
6. Keep the answer concise but informative (2-4 paragraphs max)

Answer:"""

        try:
            import time
            from utils.analytics import track_openai_call
            
            start_time = time.time()
            response = self.llm.invoke(prompt)
            duration = time.time() - start_time
            
            # Extract token usage if available
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            
            if hasattr(response, 'response_metadata'):
                usage = response.response_metadata.get('token_usage', {})
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', 0)
            
            # Track the OpenAI call
            track_openai_call(
                model=self.llm.model_name if hasattr(self.llm, 'model_name') else 'gpt-4o',
                operation='generate_answer',
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                duration=duration,
                success=True,
                query_preview=query[:100]  # Store query preview for context
            )
            
            return response.content
        except Exception as e:
            import time
            from utils.analytics import track_openai_call
            
            duration = time.time() - start_time if 'start_time' in locals() else 0.0
            
            # Track failed call
            track_openai_call(
                model=self.llm.model_name if hasattr(self.llm, 'model_name') else 'gpt-4o',
                operation='generate_answer',
                duration=duration,
                success=False,
                error=str(e),
                query_preview=query[:100]
            )
            
            return f"Error generating answer: {e}"

    def _format_context_for_llm(self, context: Any) -> str:
        """Format context dictionary/list for LLM consumption"""
        if isinstance(context, dict):
            return json.dumps(context, indent=2, default=str)
        elif isinstance(context, list):
            return json.dumps(context, indent=2, default=str)
        else:
            return str(context)

    # =========================================================================
    # MAIN QUERY INTERFACE
    # =========================================================================

    def _extract_traversal_data(self, context: Any) -> Dict:
        """
        Extract graph traversal data from context for visualization
        
        Args:
            context: Query context (can be dict, list, or nested structure)
            
        Returns:
            Dictionary with nodes and edges visited during traversal
        """
        nodes = {}
        edges = []
        node_order = []
        edge_order = []
        visited_edges = set()
        
        def extract_from_item(item: Any, parent_id: Optional[str] = None, relationship_type: Optional[str] = None):
            """Recursively extract nodes and edges from context"""
            if isinstance(item, dict):
                # Extract node information
                if "id" in item:
                    node_id = item["id"]
                    if node_id not in nodes:
                        nodes[node_id] = {
                            "id": node_id,
                            "label": item.get("name", item.get("id", "")),
                            "type": item.get("type", "Unknown"),
                            "description": item.get("description", ""),
                        }
                        node_order.append(node_id)
                    
                    # Create edge if there's a parent
                    if parent_id and parent_id != node_id:
                        edge_id = f"{parent_id}-{node_id}"
                        if edge_id not in visited_edges:
                            visited_edges.add(edge_id)
                            edges.append({
                                "id": edge_id,
                                "from": parent_id,
                                "to": node_id,
                                "type": relationship_type or "RELATED_TO",
                                "label": relationship_type or "related"
                            })
                            edge_order.append(edge_id)
                    
                    # Recursively process nested structures
                    for key, value in item.items():
                        if key not in ["id", "name", "type", "description", "mention_count", "source_articles", "article_urls", "similarity", "score"]:
                            if isinstance(value, (dict, list)):
                                # Determine relationship type from key name
                                rel_type = key.upper().replace("_", "_")
                                extract_from_item(value, node_id, rel_type)
                
                # Handle relationship structures (investors, founders, etc.)
                elif "investors" in item or "founders" in item or "technologies" in item:
                    for key in ["investors", "founders", "technologies", "competitors", "locations", "portfolio"]:
                        if key in item and isinstance(item[key], list):
                            for related_item in item[key]:
                                if isinstance(related_item, dict):
                                    extract_from_item(related_item, parent_id, key.upper())
                                elif isinstance(related_item, str) and parent_id:
                                    # Create a node for the string entity
                                    related_id = related_item.lower().replace(" ", "_").replace("-", "_")
                                    if related_id not in nodes:
                                        nodes[related_id] = {
                                            "id": related_id,
                                            "label": related_item,
                                            "type": key[:-1].title() if key.endswith("s") else key.title(),
                                        }
                                        node_order.append(related_id)
                                    
                                    edge_id = f"{parent_id}-{related_id}"
                                    if edge_id not in visited_edges:
                                        visited_edges.add(edge_id)
                                        edges.append({
                                            "id": edge_id,
                                            "from": parent_id,
                                            "to": related_id,
                                            "type": key.upper(),
                                            "label": key
                                        })
                                        edge_order.append(edge_id)
            
            elif isinstance(item, list):
                # For lists, connect items sequentially if no parent
                prev_id = parent_id
                for idx, sub_item in enumerate(item):
                    if isinstance(sub_item, dict) and "id" in sub_item:
                        current_id = sub_item["id"]
                        extract_from_item(sub_item, prev_id)
                        # Connect sequential items in list
                        if prev_id and prev_id != current_id and idx > 0:
                            edge_id = f"{prev_id}-{current_id}"
                            if edge_id not in visited_edges:
                                visited_edges.add(edge_id)
                                edges.append({
                                    "id": edge_id,
                                    "from": prev_id,
                                    "to": current_id,
                                    "type": "SEQUENTIAL",
                                    "label": "next"
                                })
                                edge_order.append(edge_id)
                        prev_id = current_id
                    else:
                        extract_from_item(sub_item, prev_id)
        
        # Extract traversal data from context
        extract_from_item(context)
        
        # If we have nodes but no edges (e.g., from semantic search), create a simple chain
        if len(nodes) > 0 and len(edges) == 0 and len(node_order) > 1:
            for i in range(len(node_order) - 1):
                edge_id = f"{node_order[i]}-{node_order[i+1]}"
                if edge_id not in visited_edges:
                    visited_edges.add(edge_id)
                    edges.append({
                        "id": edge_id,
                        "from": node_order[i],
                        "to": node_order[i+1],
                        "type": "RELATED_TO",
                        "label": "related"
                    })
                    edge_order.append(edge_id)
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges,
            "node_order": node_order,
            "edge_order": edge_order
        }

    def query(
        self, question: str, return_context: bool = False, use_llm: bool = True, return_traversal: bool = False
    ) -> Dict:
        """
        Main query interface - handles end-to-end RAG pipeline

        Args:
            question: User question
            return_context: Whether to return raw context
            use_llm: Whether to generate LLM answer
            return_traversal: Whether to return graph traversal data for visualization

        Returns:
            Query results with answer and/or context
        """
        # Step 1: Classify intent
        intent = self.classify_query_intent(question)

        # Step 2: Route to appropriate handler and get context
        context = self.route_query(question, intent)

        # Step 2.5: Enrich context with article URLs
        if context:
            context = self._enrich_with_article_urls(context)

        # Step 3: Generate answer if LLM enabled
        # Always try to generate an answer, even if context is minimal/empty
        # The LLM can handle cases where context is insufficient
        answer = None
        if use_llm:
            # Use empty dict if context is None/empty to ensure LLM still generates a response
            answer = self.generate_answer(question, context if context else {})

        # Prepare response
        response = {"question": question, "intent": intent, "answer": answer}

        if return_context:
            response["context"] = context
        
        # Extract traversal data for visualization
        if return_traversal and context:
            traversal_data = self._extract_traversal_data(context)
            response["traversal"] = traversal_data

        return response

    # =========================================================================
    # ADVANCED QUERY METHODS
    # =========================================================================

    def multi_hop_reasoning(self, question: str, max_hops: int = 3) -> Dict:
        """
        Perform multi-hop reasoning across the graph

        Args:
            question: Complex question requiring multiple reasoning steps
            max_hops: Maximum relationship hops

        Returns:
            Answer with reasoning chain
        """
        # Find relevant starting entities
        entities = self.semantic_search(question, top_k=3)

        if not entities:
            return {"error": "No relevant entities found"}

        # Get extended context for top entity
        main_entity = entities[0]
        context = self.get_entity_context(main_entity["id"], max_hops=max_hops)

        # Generate answer with reasoning
        answer = self.generate_answer(question, context)

        return {
            "question": question,
            "starting_entity": main_entity,
            "reasoning_hops": max_hops,
            "answer": answer,
            "context": context,
        }

    def compare_entities(self, entity1_name: str, entity2_name: str) -> Dict:
        """
        Compare two entities

        Args:
            entity1_name: First entity name
            entity2_name: Second entity name

        Returns:
            Comparison analysis
        """
        # Get both entities
        entity1_results = self.semantic_search(entity1_name, top_k=1)
        entity2_results = self.semantic_search(entity2_name, top_k=1)

        if not entity1_results or not entity2_results:
            return {"error": "One or both entities not found"}

        entity1 = entity1_results[0]
        entity2 = entity2_results[0]

        # Get contexts
        context1 = self.get_entity_context(entity1["id"], max_hops=2)
        context2 = self.get_entity_context(entity2["id"], max_hops=2)

        # Find connections
        connections = self.query_templates.find_connection_path(
            entity1_name, entity2_name, max_hops=4
        )

        # Generate comparison
        comparison_context = {
            "entity1": context1,
            "entity2": context2,
            "connections": connections,
        }

        question = f"Compare {entity1_name} and {entity2_name}"
        answer = self.generate_answer(question, comparison_context)

        return {
            "entity1": entity1,
            "entity2": entity2,
            "connections": connections,
            "comparison": answer,
        }

    def get_insights(self, topic: str, limit: int = 5) -> Dict:
        """
        Get insights about a topic using graph analytics

        Args:
            topic: Topic to analyze
            limit: Number of insights

        Returns:
            Key insights
        """
        # Find relevant entities
        entities = self.semantic_search(topic, top_k=limit)

        # Get importance scores
        important_entities = self.query_templates.get_entity_importance_scores(
            limit=limit
        )

        # Generate insights
        insights_context = {
            "relevant_entities": entities,
            "important_entities": important_entities,
            "topic": topic,
        }

        question = f"What are the key insights about {topic}?"
        insights = self.generate_answer(question, insights_context)

        return {
            "topic": topic,
            "insights": insights,
            "key_entities": entities[:3],
            "supporting_data": insights_context,
        }

    # =========================================================================
    # BATCH QUERIES
    # =========================================================================

    def batch_query(self, questions: List[str]) -> List[Dict]:
        """
        Process multiple queries in batch

        Args:
            questions: List of questions

        Returns:
            List of query results
        """
        results = []
        for question in questions:
            result = self.query(question)
            results.append(result)

        return results


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def create_rag_query(
    neo4j_uri: Optional[str] = None,
    neo4j_user: Optional[str] = None,
    neo4j_password: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    embedding_model: str = "openai",
) -> GraphRAGQuery:
    """
    Create GraphRAG query instance with defaults from environment

    Args:
        neo4j_uri: Neo4j URI (defaults to env NEO4J_URI, required for AuraDB)
        neo4j_user: Neo4j user (defaults to env NEO4J_USER)
        neo4j_password: Neo4j password (defaults to env NEO4J_PASSWORD, required)
        openai_api_key: OpenAI key (defaults to env OPENAI_API_KEY, required)
        embedding_model: Embedding model to use

    Returns:
        GraphRAGQuery instance

    Raises:
        ValueError: If required environment variables are not set
    """
    # Get values from arguments or environment, no fallbacks for required vars
    neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI")
    neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
    openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    
    # Validate required configuration (no fallbacks for AuraDB setup)
    if not neo4j_uri:
        raise ValueError(
            "NEO4J_URI environment variable is required. "
            "For AuraDB, set NEO4J_URI in your .env file (e.g., neo4j+s://xxxxx.databases.neo4j.io). "
            "See README.md for setup instructions."
        )
    if not neo4j_password:
        raise ValueError(
            "NEO4J_PASSWORD environment variable is required. "
            "Set NEO4J_PASSWORD in your .env file with your AuraDB password. "
            "See README.md for setup instructions."
        )
    if not openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Set OPENAI_API_KEY in your .env file. "
            "See README.md for setup instructions."
        )

    return GraphRAGQuery(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password,
        openai_api_key=openai_api_key,
        embedding_model=embedding_model,
    )


# =============================================================================
# MAIN - Example Usage
# =============================================================================


def main():
    """Example usage of GraphRAG Query"""
    from dotenv import load_dotenv

    load_dotenv()

    # Create query instance
    rag = create_rag_query()

    try:
        # Example 1: Simple query
        print("=" * 80)
        print("Example 1: Simple Query")
        print("=" * 80)
        result = rag.query("Tell me about AI startups that raised funding")
        print(f"Question: {result['question']}")
        print(f"Intent: {result['intent']}")
        print(f"Answer: {result['answer']}\n")

        # Example 2: Company comparison
        print("=" * 80)
        print("Example 2: Company Comparison")
        print("=" * 80)
        comparison = rag.compare_entities("Anthropic", "OpenAI")
        print(f"Comparison: {comparison.get('comparison')}\n")

        # Example 3: Investor portfolio
        print("=" * 80)
        print("Example 3: Investor Portfolio")
        print("=" * 80)
        result = rag.query("What companies has Sequoia Capital invested in?")
        print(f"Answer: {result['answer']}\n")

        # Example 4: Multi-hop reasoning
        print("=" * 80)
        print("Example 4: Multi-hop Reasoning")
        print("=" * 80)
        result = rag.multi_hop_reasoning(
            "What technologies are used by companies funded by top investors?"
        )
        print(f"Answer: {result['answer']}\n")

    finally:
        rag.close()


if __name__ == "__main__":
    main()
