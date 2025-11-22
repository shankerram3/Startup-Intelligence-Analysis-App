"""
Embedding Generation for Knowledge Graph
Generate vector embeddings for entities and enable semantic search
"""

from typing import Dict, List, Optional, Tuple
from neo4j import GraphDatabase
import numpy as np
import os as _os

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
        
        # Initialize embedding function based on model
        self._initialize_embedding_function()
    
    def _initialize_embedding_function(self):
        """Initialize embedding function based on model"""
        # Force sentence-transformers for embeddings
        try:
            from sentence_transformers import SentenceTransformer
            import os as _os
            model_name = self.sentence_model_name or _os.getenv(
                'SENTENCE_TRANSFORMERS_MODEL', 'all-MiniLM-L6-v2'
            )
            model = SentenceTransformer(model_name)
            
            def st_embed(text: str) -> List[float]:
                return model.encode(text).tolist()
            
            self.embedding_function = st_embed
        except ImportError:
            print("⚠️  sentence-transformers not installed. Install with: pip install sentence-transformers")
            self.embedding_function = None
        except Exception as e:
            print(f"⚠️  Error initializing sentence-transformers: {e}")
            self.embedding_function = None
    
    def generate_entity_embedding(self, entity: Dict) -> Optional[List[float]]:
        """
        Generate embedding for an entity

        Args:
            entity: Entity dictionary with name, type, description, and enriched fields

        Returns:
            Embedding vector or None
        """
        if not self.embedding_function:
            return None

        # Combine name and description for embedding
        name = entity.get("name", "")
        entity_type = entity.get("type", "")

        # Prefer enriched description over basic description
        description = entity.get("enriched_description") or entity.get("description", "")

        # Start with basic text
        text_parts = [f"{entity_type}: {name}"]

        if description:
            text_parts.append(description)

        # For Company entities, include enriched fields for richer embeddings
        if entity_type == "Company":
            # Add headquarters/location
            if entity.get("headquarters"):
                text_parts.append(f"Located in {entity['headquarters']}")

            # Add founding information
            if entity.get("founded_year"):
                text_parts.append(f"Founded in {entity['founded_year']}")

            # Add founders
            if entity.get("founders"):
                founders = entity["founders"]
                if isinstance(founders, list) and founders:
                    founders_str = ", ".join(str(f) for f in founders[:3])  # Limit to first 3
                    text_parts.append(f"Founded by {founders_str}")

            # Add products
            if entity.get("products"):
                products = entity["products"]
                if isinstance(products, list) and products:
                    products_str = ", ".join(str(p) for p in products[:5])  # Limit to first 5
                    text_parts.append(f"Products: {products_str}")

            # Add technologies
            if entity.get("technologies"):
                technologies = entity["technologies"]
                if isinstance(technologies, list) and technologies:
                    tech_str = ", ".join(str(t) for t in technologies[:10])  # Limit to first 10
                    text_parts.append(f"Technologies: {tech_str}")

            # Add funding information
            if entity.get("funding_total"):
                funding = entity["funding_total"]
                stage = entity.get("funding_stage", "")
                if stage:
                    text_parts.append(f"Raised {funding} in {stage}")
                else:
                    text_parts.append(f"Raised {funding}")

        # Combine all parts
        text = ". ".join(text_parts)

        try:
            embedding = self.embedding_function(text)
            return embedding
        except Exception as e:
            print(f"⚠️  Error generating embedding: {e}")
            return None
    
    def generate_embeddings_for_all_entities(self, entity_type: Optional[str] = None) -> Dict:
        """
        Generate embeddings for all entities in graph

        Args:
            entity_type: Optional entity type filter

        Returns:
            Statistics dictionary
        """
        if not self.embedding_function:
            return {"error": "Embedding function not initialized"}

        with self.driver.session() as session:
            # Properties are now initialized on Company nodes, so direct access is safe
            if entity_type:
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
                query = """
                    MATCH (e)
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
                    "funding_stage": record.get("funding_stage")
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
                        session.run("""
                            MATCH (e {id: $id})
                            SET e.embedding = $embedding,
                                e.embedding_model = $model,
                                e.embedding_updated = timestamp()
                        """, id=record["id"], embedding=embedding,
                           model=self.embedding_model)
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
                "model": self.embedding_model
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
        if not self.embedding_function:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_function(query_text)
        
        if not query_embedding:
            return []
        
        # Find similar entities (cosine similarity)
        with self.driver.session() as session:
            # Get all entities with embeddings
            result = session.run("""
                MATCH (e)
                WHERE NOT e:Article AND e.embedding IS NOT NULL
                RETURN e.id as id, e.name as name, labels(e)[0] as type,
                       e.description as description, e.embedding as embedding
            """)
            
            similarities = []
            query_vec = np.array(query_embedding)
            
            for record in result:
                entity_embedding = record["embedding"]
                if not entity_embedding:
                    continue
                
                entity_vec = np.array(entity_embedding)
                
                # Skip if embedding dimensions don't match
                if query_vec.ndim != 1 or entity_vec.ndim != 1 or query_vec.shape[0] != entity_vec.shape[0]:
                    # Dimension mismatch (e.g., OpenAI 1536 vs ST 384); skip this entity
                    continue
                
                # Calculate cosine similarity
                similarity = np.dot(query_vec, entity_vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(entity_vec)
                )
                
                similarities.append({
                    "id": record["id"],
                    "name": record["name"],
                    "type": record["type"],
                    "description": record.get("description", ""),
                    "similarity": float(similarity)
                })
            
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
        if not self.embedding_function:
            return {"error": "Embedding function not initialized"}

        with self.driver.session() as session:
            # Only fetch companies with enrichment status
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
                    "funding_stage": record.get("funding_stage")
                }

                embedding = self.generate_entity_embedding(entity)

                if embedding:
                    try:
                        session.run("""
                            MATCH (c:Company {id: $id})
                            SET c.embedding = $embedding,
                                c.embedding_model = $model,
                                c.embedding_updated = timestamp()
                        """, id=record["id"], embedding=embedding,
                           model=self.embedding_model)
                        regenerated_count += 1
                    except Exception as e:
                        print(f"⚠️  Error updating embedding for {record['name']}: {e}")
                        failed_count += 1
                else:
                    failed_count += 1

            return {
                "regenerated": regenerated_count,
                "failed": failed_count,
                "model": self.embedding_model
            }

