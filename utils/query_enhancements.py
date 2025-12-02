"""
Enhanced Query Capabilities for GraphRAG
Improves fidelity and flexibility of query and chat system
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict


class QueryExpander:
    """Expand queries with synonyms and related terms"""
    
    # Domain-specific synonyms and expansions
    SYNONYMS = {
        "startup": ["startups", "company", "companies", "firm", "firms", "business", "businesses"],
        "funding": ["funded", "investment", "invested", "raised", "capital", "financing"],
        "investor": ["investors", "vc", "venture capital", "venture capitalist", "backer", "backers"],
        "ai": ["artificial intelligence", "machine learning", "ml", "deep learning"],
        "recent": ["latest", "new", "newest", "last", "current"],
        "article": ["articles", "news", "story", "stories", "post", "posts", "piece"],
    }
    
    @classmethod
    def expand_query(cls, query: str) -> List[str]:
        """
        Generate query variations with synonyms
        
        Args:
            query: Original query
            
        Returns:
            List of expanded query variations
        """
        variations = [query]  # Always include original
        
        query_lower = query.lower()
        
        # Generate variations by replacing synonyms
        for term, synonyms in cls.SYNONYMS.items():
            if term in query_lower:
                for synonym in synonyms:
                    if synonym != term:
                        variation = query_lower.replace(term, synonym)
                        if variation not in variations:
                            variations.append(variation)
        
        return variations


class ReciprocalRankFusion:
    """Reciprocal Rank Fusion for combining search results"""
    
    @staticmethod
    def fuse_results(
        result_lists: List[List[Dict]], 
        k: int = 60,
        entity_id_key: str = "id"
    ) -> List[Dict]:
        """
        Combine multiple ranked result lists using RRF
        
        Args:
            result_lists: List of ranked result lists
            k: RRF constant (typically 60)
            entity_id_key: Key to use for entity ID
            
        Returns:
            Fused and re-ranked results
        """
        scores = defaultdict(float)
        entity_data = {}
        
        # Calculate RRF scores
        for rank, result_list in enumerate(result_lists):
            for position, result in enumerate(result_lists[rank]):
                entity_id = result.get(entity_id_key)
                if entity_id:
                    # RRF formula: 1 / (k + rank)
                    rrf_score = 1.0 / (k + position + 1)
                    scores[entity_id] += rrf_score
                    # Store entity data from first occurrence
                    if entity_id not in entity_data:
                        entity_data[entity_id] = result
        
        # Sort by RRF score
        ranked = sorted(
            scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Return entities with scores
        return [
            {**entity_data[entity_id], "rrf_score": score}
            for entity_id, score in ranked
        ]


class EnhancedPromptBuilder:
    """Build enhanced prompts for better LLM responses"""
    
    @staticmethod
    def build_structured_prompt(
        query: str,
        context: Any,
        context_type: str = "knowledge_graph",
        include_examples: bool = True,
        require_citations: bool = True
    ) -> str:
        """
        Build a structured prompt with better instructions
        
        Args:
            query: User question
            context: Retrieved context
            context_type: Type of context (knowledge_graph, articles, etc.)
            include_examples: Whether to include example responses
            require_citations: Whether to require entity citations
            
        Returns:
            Structured prompt string
        """
        # Format context
        context_str = _format_context(context)
        
        has_context = context_str and len(context_str.strip()) > 50
        
        prompt_parts = [
            "You are an expert knowledge graph assistant specializing in startup and tech industry intelligence.",
            "You analyze data from TechCrunch articles stored in a Neo4j knowledge graph.",
            "",
            "## User Question:",
            query,
            ""
        ]
        
        if has_context:
            # Extract actual company names from context for examples
            example_names = []
            all_names = []
            if isinstance(context, list):
                all_names = [item.get("name") for item in context if isinstance(item, dict) and item.get("name")]
                example_names = all_names[:5]  # Get first 5 for examples
            elif isinstance(context, dict) and "items" in context:
                items = context.get("items", [])
                all_names = [item.get("name") for item in items if isinstance(item, dict) and item.get("name")]
                example_names = all_names[:5]
            
            # Add explicit list of company names at the start
            names_header = ""
            if all_names:
                names_list = ", ".join(f'"{name}"' for name in all_names[:10] if name)  # Show up to 10 names
                if len(all_names) > 10:
                    names_list += f" (and {len(all_names) - 10} more)"
                names_header = f"\n## COMPANIES IN CONTEXT (YOU MUST USE THESE EXACT NAMES):\n{names_list}\n\n"
            
            example_text = ""
            if example_names and len(example_names) >= 2:
                names_list = ", ".join(f'"{name}"' for name in example_names if name)
                example_text = f"\n\n## REAL EXAMPLES FROM YOUR CONTEXT:\nThe context above contains companies like {names_list}. You MUST use these exact names in your answer.\n\nExample correct answer format:\n\"According to the knowledge graph, {example_names[0]} raised funding recently. {example_names[1]} also secured investment from {example_names[2] if len(example_names) > 2 else 'investors'}...\"\n\nDO NOT write: \"Startup A raised funding. Startup B also received investment...\""
            
            prompt_parts.extend([
                names_header,
                "## Available Context:",
                context_str,
                "",
                "## CRITICAL INSTRUCTIONS - READ CAREFULLY:",
                "1. **MANDATORY: Use Exact Names from Context**: You MUST use the exact company names, investor names, and entity names as they appear in the context above. Look at the 'name' field in each item. NEVER use placeholder names like 'Startup A', 'Company X', or 'Entity Y'. NEVER make up generic names.",
                "2. **Answer Accuracy**: Base your answer ONLY on the provided context. Do not make up information or use generic placeholders.",
                "3. **Specificity**: Be specific and mention exact entity names, dates, and numbers when available. Always cite the actual names from the context.",
                "4. **Citations**: " + ("Cite specific entities from the context using their exact names (e.g., 'According to the graph, [ACTUAL COMPANY NAME FROM CONTEXT] raised funding...')." if require_citations else "Reference the context naturally using exact entity names."),
                "5. **Connections**: Highlight relationships and connections between entities when relevant, using their exact names.",
                "6. **Completeness**: If the context doesn't fully answer the question, clearly state what information is missing, but still use the exact names that ARE available.",
                "7. **Structure**: Organize your answer logically with clear paragraphs.",
                "8. **Length**: Aim for 2-4 paragraphs, but adjust based on question complexity.",
                "",
                "## Example of CORRECT format:",
                "✅ 'According to the knowledge graph, [USE ACTUAL COMPANY NAME FROM CONTEXT] raised funding recently. [USE ANOTHER ACTUAL COMPANY NAME FROM CONTEXT] also secured investment...'",
                "",
                "## Example of INCORRECT format (DO NOT DO THIS):",
                "❌ 'Startup A raised funding. Another entity, Startup B, also received investment...'",
                example_text,
                ""
            ])
        else:
            prompt_parts.extend([
                "## Note:",
                "The knowledge graph search returned limited or no relevant context for this question.",
                "",
                "## Instructions:",
                "1. If you can provide general knowledge about the topic, do so while noting it's not from the graph.",
                "2. Clearly explain what specific data would be needed from the knowledge graph to answer this question.",
                "3. Suggest what types of entities or relationships would help answer this (e.g., 'To answer this, the graph would need information about companies in the AI sector and their funding rounds').",
                "4. Be helpful and informative, even if you can't provide a complete answer.",
                ""
            ])
        
        if include_examples and has_context:
            prompt_parts.extend([
                "## Example Response Format:",
                "Based on the knowledge graph data, [specific answer with entity names]. ",
                "For example, [entity X] is connected to [entity Y] through [relationship]. ",
                "The graph shows that [specific insight from context].",
                ""
            ])
        
        prompt_parts.append("## Your Answer:")
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def build_chain_of_thought_prompt(
        query: str,
        context: Any,
        reasoning_steps: Optional[List[str]] = None
    ) -> str:
        """
        Build a prompt that encourages chain-of-thought reasoning
        
        Args:
            query: User question
            context: Retrieved context
            reasoning_steps: Optional list of reasoning steps to guide the LLM
            
        Returns:
            Chain-of-thought prompt
        """
        context_str = _format_context(context)
        
        prompt = f"""You are analyzing a question about startup and tech industry data.

Question: {query}

Available Context:
{context_str}

Think through this step by step:

1. What is the question asking for?
2. What relevant information is available in the context?
3. What relationships or connections can be made?
4. What is the answer based on the available data?
5. What information is missing (if any)?

Provide your reasoning, then give a clear answer.

Reasoning:
"""
        
        if reasoning_steps:
            prompt += "\n".join(f"- {step}" for step in reasoning_steps) + "\n\n"
        
        prompt += "Answer:"
        
        return prompt


class QueryRefiner:
    """Refine and clarify ambiguous queries"""
    
    AMBIGUITY_PATTERNS = [
        (r"\b(which|what)\s+(company|companies|startup|startups)\b", "multiple_entities"),
        (r"\b(recent|latest|new)\s+(.*?)\b", "temporal_ambiguity"),
        (r"\b(.*?)\s+(or|vs|versus)\s+(.*?)\b", "comparison_ambiguity"),
    ]
    
    @classmethod
    def detect_ambiguity(cls, query: str) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        """
        Detect if a query is ambiguous and needs clarification
        
        Args:
            query: User query
            
        Returns:
            Tuple of (is_ambiguous, ambiguity_type, clarifying_questions)
        """
        query_lower = query.lower()
        clarifying_questions = []
        
        # Check for multiple entity mentions without specificity
        # But skip if query has specific context (funding, sector, technology, etc.)
        if re.search(r"\b(which|what)\s+(company|companies|startup|startups)\b", query_lower):
            # Check if query has specific context that makes it clear
            has_specific_context = any(
                word in query_lower 
                for word in ["in", "with", "that", "funded", "raised", "funding", "ai", "tech", 
                            "sector", "industry", "recent", "latest", "new", "investor", "round"]
            )
            if not has_specific_context:
                clarifying_questions.append(
                    "Are you looking for companies in a specific sector, with certain characteristics, or with recent funding?"
                )
                return True, "multiple_entities", clarifying_questions
        
        # Check for vague temporal references
        # But don't trigger if query is clearly about articles, news, or specific entities
        if re.search(r"\b(recent|latest|new)\b", query_lower):
            # Skip ambiguity check if query is clearly about articles/news
            if any(word in query_lower for word in ["article", "articles", "news", "story", "stories", "post", "posts"]):
                # Clear article query - not ambiguous
                return False, None, None
            
            # Skip if query specifies what they want (e.g., "recent funding", "latest companies")
            if any(word in query_lower for word in ["funding", "companies", "startups", "investors", "rounds"]):
                # Has context - not ambiguous
                return False, None, None
            
            # Only ask for clarification if truly vague (no context about what is recent)
            if not any(word in query_lower for word in ["days", "weeks", "months", "year", "article", "articles", "news"]):
                clarifying_questions.append(
                    "What time period do you mean by 'recent'? (e.g., last 30 days, last 3 months)"
                )
                return True, "temporal_ambiguity", clarifying_questions
        
        # Check for comparison without clear entities
        if re.search(r"\b(or|vs|versus)\b", query_lower):
            entities = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", query)
            if len(entities) < 2:
                clarifying_questions.append(
                    "Which specific entities would you like to compare?"
                )
                return True, "comparison_ambiguity", clarifying_questions
        
        return False, None, None
    
    @classmethod
    def generate_clarification_response(
        cls, 
        query: str, 
        clarifying_questions: List[str]
    ) -> str:
        """Generate a response asking for clarification"""
        return f"""I'd like to provide you with the most accurate answer. Could you clarify:

{chr(10).join(f"- {q}" for q in clarifying_questions)}

Once you provide more details, I can give you a precise answer based on the knowledge graph data."""


class ContextEnricher:
    """Enrich context with additional relevant information"""
    
    @staticmethod
    def enrich_with_temporal_context(
        context: Any,
        query: str,
        query_templates
    ) -> Any:
        """
        Add temporal context (recent trends, changes over time)
        
        Args:
            context: Current context (can be dict, list, or other type)
            query: User query
            query_templates: QueryTemplates instance
            
        Returns:
            Enriched context (same type as input)
        """
        # Handle list context (e.g., list of companies)
        if isinstance(context, list):
            # For lists, add temporal metadata as a wrapper
            # Check if query has temporal aspects
            if any(word in query.lower() for word in ["recent", "latest", "trend", "change"]):
                try:
                    recent_entities = query_templates.get_recent_entities(days=90, limit=5)
                    if recent_entities:
                        # Return list with metadata attached
                        return {
                            "items": context,
                            "recent_entities": recent_entities,
                            "temporal_enrichment": True
                        }
                except:
                    pass
            # Return list as-is if no enrichment needed
            return context
        
        # Handle dict context
        elif isinstance(context, dict):
            enriched = dict(context)
            
            # Check if query has temporal aspects
            if any(word in query.lower() for word in ["recent", "latest", "trend", "change"]):
                # Add recent entities if available
                try:
                    recent_entities = query_templates.get_recent_entities(days=90, limit=5)
                    if recent_entities:
                        enriched["recent_entities"] = recent_entities
                except:
                    pass
            
            return enriched
        
        # For other types, return as-is
        return context
    
    @staticmethod
    def enrich_with_related_entities(
        context: Any,
        query_templates,
        max_related: int = 5
    ) -> Any:
        """
        Add related entities to context
        
        Args:
            context: Current context (can be dict, list, or other type)
            query_templates: QueryTemplates instance
            max_related: Maximum related entities to add
            
        Returns:
            Enriched context (same type as input)
        """
        # Handle list context
        if isinstance(context, list):
            # For lists, extract entity IDs from items
            entity_ids = []
            for item in context:
                if isinstance(item, dict) and "id" in item:
                    entity_ids.append(item["id"])
            
            # Get relationships for entities
            related = []
            for entity_id in entity_ids[:3]:  # Limit to avoid too much data
                try:
                    relationships = query_templates.get_entity_relationships(entity_id, max_hops=1)
                    if relationships:
                        related.extend(relationships[:max_related])
                except:
                    pass
            
            # Return list as-is if no related entities found
            if not related:
                return context
            
            # Return list with related entities metadata
            return {
                "items": context,
                "related_entities": related[:max_related],
                "related_enrichment": True
            }
        
        # Handle dict context
        elif isinstance(context, dict):
            enriched = dict(context)
            
            # Extract entity IDs from context
            entity_ids = []
            if "id" in context:
                entity_ids.append(context["id"])
            if "entities" in context:
                entity_ids.extend([e.get("id") for e in context.get("entities", []) if e.get("id")])
            
            # Get relationships for each entity
            related = []
            for entity_id in entity_ids[:3]:  # Limit to avoid too much data
                try:
                    relationships = query_templates.get_entity_relationships(entity_id, max_hops=1)
                    if relationships:
                        related.extend(relationships[:max_related])
                except:
                    pass
            
            if related:
                enriched["related_entities"] = related[:max_related]
            
            return enriched
        
        # For other types, return as-is
        return context


def _format_context(context: Any) -> str:
    """Format context for prompt (helper function)"""
    # Handle enriched context (dict with "items" key)
    if isinstance(context, dict) and "items" in context:
        items = context.get("items", [])
        if isinstance(items, list) and items:
            formatted_items = "\n".join(
                f"- {_format_single_item(item)}" 
                for item in items[:20]  # Limit to 20 items
            )
            # Add metadata if present
            metadata_parts = []
            if "recent_entities" in context:
                metadata_parts.append("Recent entities: " + str(len(context["recent_entities"])))
            if "related_entities" in context:
                metadata_parts.append("Related entities: " + str(len(context["related_entities"])))
            if metadata_parts:
                return formatted_items + "\n\nAdditional context: " + ", ".join(metadata_parts)
            return formatted_items
        else:
            return _format_single_item(context)
    
    if isinstance(context, list):
        if not context:
            return "No context available."
        return "\n".join(
            f"- {_format_single_item(item)}" 
            for item in context[:20]  # Limit to 20 items
        )
    elif isinstance(context, dict):
        return _format_single_item(context)
    else:
        return str(context) if context else "No context available."


def _format_single_item(item: Any) -> str:
    """Format a single context item, emphasizing entity names"""
    if isinstance(item, dict):
        parts = []
        # Prioritize name field - put it first and make it prominent
        if "name" in item:
            parts.append(f"**Name: {item['name']}**")
        elif "title" in item:
            parts.append(f"**Title: {item['title']}**")
        
        for key, value in item.items():
            if key not in ["id", "embedding", "rrf_score", "name", "title"]:  # Skip technical fields and name (already shown)
                if isinstance(value, list):
                    if len(value) > 0 and isinstance(value[0], str):
                        # For lists of strings (like investors), show them
                        parts.append(f"{key}: {', '.join(str(v) for v in value[:5])}")
                    else:
                        parts.append(f"{key}: {len(value)} items")
                elif isinstance(value, dict):
                    parts.append(f"{key}: {len(value)} fields")
                else:
                    parts.append(f"{key}: {value}")
        return " | ".join(parts)
    return str(item)

