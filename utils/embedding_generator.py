"""
Embedding Generation for Knowledge Graph
Generate vector embeddings for entities and enable semantic search
"""

import os as _os
from typing import Dict, List, Optional, Tuple

import numpy as np
from neo4j import GraphDatabase

# Avoid Hugging Face tokenizers parallelism warning after fork
_os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


class EmbeddingGenerator:
    """Generate embeddings for entities"""

    def __init__(
        self,
        driver: GraphDatabase,
        embedding_model: str = "openai",
        sentence_model_name: Optional[str] = None,
    ):
        self.driver = driver
        self.embedding_model = embedding_model
        self.sentence_model_name = sentence_model_name
        self.embedding_function = None
        self._model = None  # Lazy-loaded model instance
        self._model_loaded = False

        # Don't load model at initialization - lazy load on first use
        # This prevents OOM on Render's 512 MiB free tier

    def _get_model(self):
        """Lazy-load the SentenceTransformer model only when needed"""
        if self._model_loaded and self._model is not None:
            return self._model
        
        # Load model on first use
        try:
            import os as _os

            from sentence_transformers import SentenceTransformer

            # Use smaller model by default to fit in Render's 512 MiB limit
            # Options: 
            # - "intfloat/multilingual-e5-small" (~40-60 MB, recommended)
            # - "BAAI/bge-small-en-v1.5" (~55 MB)
            # - "all-MiniLM-L6-v2" (~120-180 MB, too large for Render free tier)
            default_model = _os.getenv(
                "SENTENCE_TRANSFORMERS_MODEL", 
                "intfloat/multilingual-e5-small"  # Smaller default for Render compatibility
            )
            
            model_name = self.sentence_model_name or default_model
            
            # Log model loading (helps debug OOM issues)
            print(f"Loading SentenceTransformer model: {model_name}...")
            self._model = SentenceTransformer(model_name)
            self._model_loaded = True
            print(f"✓ Model loaded: {model_name}")
            
            return self._model
        except ImportError:
            print(
                "⚠️  sentence-transformers not installed. Install with: pip install sentence-transformers"
            )
            self._model = None
            self._model_loaded = True  # Mark as attempted to avoid retrying
            return None
        except Exception as e:
            print(f"⚠️  Error loading sentence-transformers model: {e}")
            self._model = None
            self._model_loaded = True  # Mark as attempted to avoid retrying
            return None

    def _get_embedding_function(self):
        """Get or create embedding function (lazy-loaded)"""
        if self.embedding_function is not None:
            return self.embedding_function
        
        # Only load if using sentence-transformers
        if self.embedding_model != "sentence_transformers":
            return None
        
        model = self._get_model()
        if model is None:
            return None
        
        def st_embed(text: str) -> List[float]:
            return model.encode(text).tolist()
        
        self.embedding_function = st_embed
        return self.embedding_function

    def generate_entity_embedding(self, entity: Dict) -> Optional[List[float]]:
        """
        Generate embedding for an entity

        Args:
            entity: Entity dictionary with name, type, description, and enriched fields

        Returns:
            Embedding vector or None
        """
        # Lazy-load embedding function on first use
        embedding_func = self._get_embedding_function()
        if not embedding_func:
            return None

        # Combine name and description for embedding
        name = entity.get("name", "")
        entity_type = entity.get("type", "")

        # Prefer enriched description over basic description
        description = entity.get("enriched_description") or entity.get(
            "description", ""
        )

        # Start with basic text
        text_parts = [f"{entity_type}: {name}"]

        if description:
            text_parts.append(description)

        # For Company entities, include enriched fields for richer embeddings
        if entity_type == "Company":
            # Known enrichment fields (in priority order)
            known_fields = {
                "headquarters": lambda v: f"Located in {v}",
                "founded_year": lambda v: f"Founded in {v}",
                "founders": lambda v: f"Founded by {', '.join(str(f) for f in (v[:3] if isinstance(v, list) else [v]))}",
                "products": lambda v: f"Products: {', '.join(str(p) for p in (v[:5] if isinstance(v, list) else [v]))}",
                "technologies": lambda v: f"Technologies: {', '.join(str(t) for t in (v[:10] if isinstance(v, list) else [v]))}",
                "funding_total": lambda v: f"Raised {v}",
                "funding_stage": None,  # Handled with funding_total
                "employee_count": lambda v: f"{v} employees",
                "pricing_model": lambda v: f"Pricing: {v}",
                "website_url": None,  # Skip URL in embedding text
                "description": None,  # Already handled above
                "enriched_description": None,  # Already handled above
                "enrichment_status": None,  # Metadata, skip
                "enrichment_timestamp": None,  # Metadata, skip
                "enrichment_confidence": None,  # Metadata, skip
            }

            # Process known fields first
            if entity.get("headquarters"):
                text_parts.append(f"Located in {entity['headquarters']}")

            if entity.get("founded_year"):
                text_parts.append(f"Founded in {entity['founded_year']}")

            if entity.get("founders"):
                founders = entity["founders"]
                if isinstance(founders, list) and founders:
                    founders_str = ", ".join(str(f) for f in founders[:3])
                    text_parts.append(f"Founded by {founders_str}")

            if entity.get("products"):
                products = entity["products"]
                if isinstance(products, list) and products:
                    products_str = ", ".join(str(p) for p in products[:5])
                    text_parts.append(f"Products: {products_str}")

            if entity.get("technologies"):
                technologies = entity["technologies"]
                if isinstance(technologies, list) and technologies:
                    tech_str = ", ".join(str(t) for t in technologies[:10])
                    text_parts.append(f"Technologies: {tech_str}")

            # Funding information (combine total and stage)
            if entity.get("funding_total"):
                funding = entity["funding_total"]
                stage = entity.get("funding_stage", "")
                if stage:
                    text_parts.append(f"Raised {funding} in {stage}")
                else:
                    text_parts.append(f"Raised {funding}")

            if entity.get("employee_count"):
                text_parts.append(f"{entity['employee_count']} employees")

            if entity.get("pricing_model"):
                text_parts.append(f"Pricing: {entity['pricing_model']}")

            # Dynamically include any other enrichment properties not in known_fields
            # This allows new properties to be automatically included in embeddings
            skip_keys = set(known_fields.keys()) | {
                "id",
                "name",
                "type",
                "description",
                "enriched_description",
            }
            for key, value in entity.items():
                if key in skip_keys or value is None:
                    continue

                # Handle lists
                if isinstance(value, list) and value:
                    value_str = ", ".join(str(v) for v in value[:5])
                    text_parts.append(f"{key.replace('_', ' ').title()}: {value_str}")
                # Handle dicts (like social_links)
                elif isinstance(value, dict) and value:
                    # Include key info from dict
                    keys_str = ", ".join(str(k) for k in list(value.keys())[:3])
                    text_parts.append(f"{key.replace('_', ' ').title()}: {keys_str}")
                # Handle primitives
                elif not isinstance(value, (dict, list)):
                    text_parts.append(f"{key.replace('_', ' ').title()}: {value}")

        # Combine all parts
        text = ". ".join(text_parts)

        try:
            embedding = embedding_func(text)
            return embedding
        except Exception as e:
            print(f"⚠️  Error generating embedding: {e}")
            return None

    def generate_embeddings_for_all_entities(
        self, entity_type: Optional[str] = None
    ) -> Dict:
        """
        Generate embeddings for all entities in graph

        Args:
            entity_type: Optional entity type filter

        Returns:
            Statistics dictionary
        """
        # Lazy-load embedding function on first use
        embedding_func = self._get_embedding_function()
        if not embedding_func:
            return {"error": "Embedding function not initialized"}

        with self.driver.session() as session:
            # Only Company nodes have enrichment properties, so we conditionally access them
            if entity_type:
                if entity_type == "Company":
                    # Company nodes: include all enrichment properties
                    query = f"""
                        MATCH (e:{entity_type})
                        WHERE NOT e:Article
                        RETURN e.id as id, e.name as name, labels(e)[0] as type,
                               COALESCE(e.description, '') as description,
                               e.enriched_description as enriched_description,
                               e.headquarters as headquarters,
                               e.founded_year as founded_year,
                               e.founders as founders,
                               e.products as products,
                               e.technologies as technologies,
                               e.funding_total as funding_total,
                               e.funding_stage as funding_stage
                    """
                else:
                    # Non-Company nodes: exclude enrichment properties
                    query = f"""
                        MATCH (e:{entity_type})
                        WHERE NOT e:Article
                        RETURN e.id as id, e.name as name, labels(e)[0] as type,
                               COALESCE(e.description, '') as description,
                               null as enriched_description,
                               null as headquarters,
                               null as founded_year,
                               null as founders,
                               null as products,
                               null as technologies,
                               null as funding_total,
                               null as funding_stage
                    """
            else:
                # All entities: conditionally access enrichment properties only for Company nodes
                query = """
                    MATCH (e)
                    WHERE NOT e:Article
                    RETURN e.id as id, e.name as name, labels(e)[0] as type,
                           COALESCE(e.description, '') as description,
                           CASE WHEN 'Company' IN labels(e) THEN e.enriched_description ELSE null END as enriched_description,
                           CASE WHEN 'Company' IN labels(e) THEN e.headquarters ELSE null END as headquarters,
                           CASE WHEN 'Company' IN labels(e) THEN e.founded_year ELSE null END as founded_year,
                           CASE WHEN 'Company' IN labels(e) THEN e.founders ELSE null END as founders,
                           CASE WHEN 'Company' IN labels(e) THEN e.products ELSE null END as products,
                           CASE WHEN 'Company' IN labels(e) THEN e.technologies ELSE null END as technologies,
                           CASE WHEN 'Company' IN labels(e) THEN e.funding_total ELSE null END as funding_total,
                           CASE WHEN 'Company' IN labels(e) THEN e.funding_stage ELSE null END as funding_stage
                """

            result = session.run(query)

            generated_count = 0
            failed_count = 0
            enriched_count = 0

            for record in result:
                entity = {
                    "name": record["name"],
                    "type": record["type"],
                    "description": record.get("description", ""),
                    "enriched_description": record.get("enriched_description"),
                    "headquarters": record.get("headquarters"),
                    "founded_year": record.get("founded_year"),
                    "founders": record.get("founders"),
                    "products": record.get("products"),
                    "technologies": record.get("technologies"),
                    "funding_total": record.get("funding_total"),
                    "funding_stage": record.get("funding_stage"),
                }

                # Track if this entity has enriched data
                if entity.get("enriched_description"):
                    enriched_count += 1

                embedding = self.generate_entity_embedding(entity)

                if embedding:
                    # Store embedding in Neo4j
                    # Note: Neo4j supports vector storage, but for simplicity
                    # we'll store as list property
                    try:
                        session.run(
                            """
                            MATCH (e {id: $id})
                            SET e.embedding = $embedding,
                                e.embedding_model = $model,
                                e.embedding_updated = timestamp()
                        """,
                            id=record["id"],
                            embedding=embedding,
                            model=self.embedding_model,
                        )
                        generated_count += 1
                    except Exception as e:
                        print(f"⚠️  Error storing embedding for {record['name']}: {e}")
                        failed_count += 1
                else:
                    failed_count += 1

            return {
                "generated": generated_count,
                "failed": failed_count,
                "enriched": enriched_count,
                "model": self.embedding_model,
            }

    def find_similar_entities(self, query_text: str, limit: int = 10) -> List[Dict]:
        """
        Find entities similar to query text using embeddings

        Args:
            query_text: Query text
            limit: Maximum number of results

        Returns:
            List of similar entities with similarity scores
        """
        # Lazy-load embedding function
        embedding_func = self._get_embedding_function()
        if not embedding_func:
            return []

        # Generate query embedding
        query_embedding = embedding_func(query_text)

        if not query_embedding:
            return []

        # Find similar entities (cosine similarity)
        with self.driver.session() as session:
            # Get all entities with embeddings
            result = session.run(
                """
                MATCH (e)
                WHERE NOT e:Article AND e.embedding IS NOT NULL
                RETURN e.id as id, e.name as name, labels(e)[0] as type,
                       e.description as description, e.embedding as embedding,
                       e.source_articles as source_articles
            """
            )

            similarities = []
            query_vec = np.array(query_embedding)

            for record in result:
                entity_embedding = record["embedding"]
                if not entity_embedding:
                    continue

                entity_vec = np.array(entity_embedding)

                # Skip if embedding dimensions don't match
                if (
                    query_vec.ndim != 1
                    or entity_vec.ndim != 1
                    or query_vec.shape[0] != entity_vec.shape[0]
                ):
                    # Dimension mismatch (e.g., OpenAI 1536 vs ST 384); skip this entity
                    continue

                # Calculate cosine similarity
                similarity = np.dot(query_vec, entity_vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(entity_vec)
                )

                similarities.append(
                    {
                        "id": record["id"],
                        "name": record["name"],
                        "type": record["type"],
                        "description": record.get("description", ""),
                        "similarity": float(similarity),
                        "source_articles": record.get("source_articles"),
                    }
                )

            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:limit]

    def update_embeddings(self, entity_type: Optional[str] = None) -> Dict:
        """Update embeddings for entities (regenerate if model changed)"""
        return self.generate_embeddings_for_all_entities(entity_type)

    def regenerate_enriched_company_embeddings(self) -> Dict:
        """
        Regenerate embeddings specifically for companies with enriched data

        This ensures enriched company intelligence is reflected in semantic search.

        Returns:
            Statistics dictionary
        """
        # Lazy-load embedding function on first use
        embedding_func = self._get_embedding_function()
        if not embedding_func:
            return {"error": "Embedding function not initialized"}

        with self.driver.session() as session:
            # All nodes now have enrichment properties initialized, so we can query directly
            query = """
                MATCH (c:Company)
                WHERE c.enrichment_status = 'enriched'
                RETURN c.id as id, c.name as name, labels(c)[0] as type,
                       COALESCE(c.description, '') as description,
                       c.enriched_description as enriched_description,
                       c.headquarters as headquarters,
                       c.founded_year as founded_year,
                       c.founders as founders,
                       c.products as products,
                       c.technologies as technologies,
                       c.funding_total as funding_total,
                       c.funding_stage as funding_stage,
                       c.enrichment_confidence as confidence
            """

            result = session.run(query)

            regenerated_count = 0
            failed_count = 0

            for record in result:
                entity = {
                    "name": record["name"],
                    "type": record["type"],
                    "description": record.get("description", ""),
                    "enriched_description": record.get("enriched_description"),
                    "headquarters": record.get("headquarters"),
                    "founded_year": record.get("founded_year"),
                    "founders": record.get("founders"),
                    "products": record.get("products"),
                    "technologies": record.get("technologies"),
                    "funding_total": record.get("funding_total"),
                    "funding_stage": record.get("funding_stage"),
                }

                embedding = self.generate_entity_embedding(entity)

                if embedding:
                    try:
                        session.run(
                            """
                            MATCH (c:Company {id: $id})
                            SET c.embedding = $embedding,
                                c.embedding_model = $model,
                                c.embedding_updated = timestamp()
                        """,
                            id=record["id"],
                            embedding=embedding,
                            model=self.embedding_model,
                        )
                        regenerated_count += 1
                    except Exception as e:
                        print(f"⚠️  Error updating embedding for {record['name']}: {e}")
                        failed_count += 1
                else:
                    failed_count += 1

            return {
                "regenerated": regenerated_count,
                "failed": failed_count,
                "model": self.embedding_model,
            }
