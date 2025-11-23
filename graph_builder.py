"""
Neo4j Knowledge Graph Builder for TechCrunch Articles
Builds a knowledge graph from extracted entities and relationships
"""

import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from neo4j import GraphDatabase

from utils.logging_config import get_logger, setup_logging

# Setup logging
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    json_logs=os.getenv("JSON_LOGS", "false").lower() == "true",
    log_file=(
        Path("logs/graph_builder.log")
        if os.getenv("ENABLE_FILE_LOGGING") == "true"
        else None
    ),
)

logger = get_logger(__name__)


class TechCrunchGraphBuilder:
    """Build and populate Neo4j knowledge graph"""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.entity_registry = defaultdict(list)  # Track all entity mentions

    def close(self):
        self.driver.close()

    def initialize_schema(self):
        """Create indexes and constraints"""
        with self.driver.session() as session:
            # Constraints (ensure uniqueness)
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Investor) REQUIRE i.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Technology) REQUIRE t.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (pr:Product) REQUIRE pr.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE",
            ]

            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.debug("constraint_created", constraint=constraint[:50])
                except Exception as e:
                    logger.debug("constraint_already_exists", error=str(e))

            # Initialize enrichment properties for existing nodes (all entity types)
            self._initialize_enrichment_properties(session)

            # Indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.name)",
                "CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.enrichment_status)",
                "CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.name)",
                "CREATE INDEX IF NOT EXISTS FOR (a:Article) ON (a.published_date)",
            ]

            for index in indexes:
                try:
                    session.run(index)
                    logger.debug("index_created", index=index[:50])
                except Exception as e:
                    logger.debug("index_already_exists", error=str(e))

    def _initialize_enrichment_properties(self, session):
        """Initialize enrichment properties for ALL entity nodes (not just Company)"""
        # Initialize properties on all non-Article nodes to avoid Neo4j warnings
        # This allows dynamic enrichment on any entity type
        query = """
            MATCH (e)
            WHERE NOT e:Article
            SET e.headquarters = COALESCE(e.headquarters, null),
                e.founded_year = COALESCE(e.founded_year, null),
                e.founders = COALESCE(e.founders, null),
                e.products = COALESCE(e.products, null),
                e.technologies = COALESCE(e.technologies, null),
                e.funding_total = COALESCE(e.funding_total, null),
                e.funding_stage = COALESCE(e.funding_stage, null),
                e.enriched_description = COALESCE(e.enriched_description, null),
                e.enrichment_status = COALESCE(e.enrichment_status, 'pending'),
                e.website_url = COALESCE(e.website_url, null),
                e.employee_count = COALESCE(e.employee_count, null),
                e.pricing_model = COALESCE(e.pricing_model, null)
            RETURN count(e) as updated
        """

        try:
            result = session.run(query)
            record = result.single()
            updated = record["updated"] if record else 0
            if updated > 0:
                logger.info("enrichment_properties_initialized", updated=updated)
        except Exception as e:
            logger.debug("enrichment_properties_init_skipped", error=str(e))

    @staticmethod
    def generate_entity_id(name: str, entity_type: str) -> str:
        """Generate consistent ID for entity"""
        normalized = name.lower().strip()
        return hashlib.md5(f"{entity_type}:{normalized}".encode()).hexdigest()[:12]

    def create_article_node(self, metadata: Dict) -> str:
        """Create Article node"""
        with self.driver.session() as session:
            result = session.run(
                """
                MERGE (a:Article {id: $id})
                SET a.url = $url,
                    a.title = $title,
                    a.published_date = $published_date,
                    a.created_at = timestamp()
                RETURN a.id as id
            """,
                id=metadata["article_id"],
                url=metadata["url"],
                title=metadata["title"],
                published_date=metadata["published_date"],
            )
            record = result.single()
            return record["id"] if record else None

    def create_entity_node(self, entity: Dict, article_id: str):
        """Create entity node based on type"""
        entity_type = entity["type"].upper()
        name = entity["name"]
        description = entity["description"]

        # Filter out TechCrunch/Disrupt related entities
        from utils.filter_techcrunch import filter_techcrunch_entity

        should_filter, reason = filter_techcrunch_entity(entity)
        if should_filter:
            logger.debug("skipping_techcrunch_entity", name=name)
            return None

        # Generate consistent ID
        entity_id = self.generate_entity_id(name, entity_type)

        # Track entity mentions for deduplication
        self.entity_registry[entity_id].append(
            {
                "name": name,
                "type": entity_type,
                "description": description,
                "article_id": article_id,
            }
        )

        with self.driver.session() as session:
            # Map entity type to node label
            node_label = self._get_node_label(entity_type)

            # Initialize enrichment properties for ALL entity types
            # This allows dynamic enrichment and avoids Neo4j warnings
            query = f"""
                    MERGE (e:{node_label} {{id: $id}})
                    ON CREATE SET 
                        e.name = $name,
                        e.description = $description,
                        e.created_at = timestamp(),
                        e.mention_count = 1,
                        e.headquarters = null,
                        e.founded_year = null,
                        e.founders = null,
                        e.products = null,
                        e.technologies = null,
                        e.funding_total = null,
                        e.funding_stage = null,
                        e.enriched_description = null,
                    e.enrichment_status = COALESCE(e.enrichment_status, 'pending'),
                        e.website_url = null,
                        e.employee_count = null,
                        e.pricing_model = null
                    ON MATCH SET
                        e.description = e.description + ' | ' + $description,
                        e.mention_count = e.mention_count + 1,
                    e.updated_at = timestamp(),
                    e.headquarters = COALESCE(e.headquarters, null),
                    e.founded_year = COALESCE(e.founded_year, null),
                    e.founders = COALESCE(e.founders, null),
                    e.products = COALESCE(e.products, null),
                    e.technologies = COALESCE(e.technologies, null),
                    e.funding_total = COALESCE(e.funding_total, null),
                    e.funding_stage = COALESCE(e.funding_stage, null),
                    e.enriched_description = COALESCE(e.enriched_description, null),
                    e.enrichment_status = COALESCE(e.enrichment_status, 'pending'),
                    e.website_url = COALESCE(e.website_url, null),
                    e.employee_count = COALESCE(e.employee_count, null),
                    e.pricing_model = COALESCE(e.pricing_model, null)
                    RETURN e.id as id
                """

            result = session.run(
                query, id=entity_id, name=name, description=description
            )

            record = result.single()
            created_id = record["id"] if record else None
            if not created_id:
                return None

            # Link entity to article (using properties, not relationships)
            self.link_article_to_entity(created_id, article_id, node_label)

            return created_id

    def _get_node_label(self, entity_type: str) -> str:
        """Map entity type to Neo4j node label"""
        type_mapping = {
            "COMPANY": "Company",
            "PERSON": "Person",
            "INVESTOR": "Investor",
            "TECHNOLOGY": "Technology",
            "PRODUCT": "Product",
            "FUNDING_ROUND": "FundingRound",
            "LOCATION": "Location",
            "EVENT": "Event",
        }
        return type_mapping.get(entity_type, "Entity")

    def link_article_to_entity(
        self, entity_id: str, article_id: str, entity_label: str
    ):
        """
        Link article to entity using properties (not relationships)
        This keeps the graph clean and focused on semantic relationships
        """
        with self.driver.session() as session:
            session.run(
                f"""
                MATCH (e:{entity_label} {{id: $entity_id}})
                SET e.source_articles = CASE 
                    WHEN e.source_articles IS NULL THEN [$article_id]
                    WHEN NOT $article_id IN e.source_articles THEN e.source_articles + $article_id
                    ELSE e.source_articles
                END,
                e.article_count = size(e.source_articles),
                e.last_mentioned = timestamp()
            """,
                entity_id=entity_id,
                article_id=article_id,
            )

    def create_relationship(self, relationship: Dict, article_id: str):
        """Create relationship between entities"""
        source_name = relationship["source"]
        target_name = relationship["target"]
        rel_type = relationship["type"]
        description = relationship["description"]
        strength = relationship.get("strength", 5)

        # STRICT: Skip MENTIONED_IN relationships - these are handled via properties
        # This should never happen if extraction is correct, but double-check here
        if rel_type == "MENTIONED_IN":
            logger.warning(
                "skipped_mentioned_in_relationship",
                source=source_name,
                target=target_name,
            )
            return

        # STRICT: Skip relationships involving TechCrunch/Disrupt entities
        from utils.filter_techcrunch import is_techcrunch_related

        if is_techcrunch_related(source_name) or is_techcrunch_related(target_name):
            logger.warning(
                "skipped_techcrunch_relationship",
                source=source_name,
                target=target_name,
            )
            return

        # Validate relationship type
        valid_types = [
            "FUNDED_BY",
            "FOUNDED_BY",
            "WORKS_AT",
            "ACQUIRED",
            "PARTNERS_WITH",
            "COMPETES_WITH",
            "USES_TECHNOLOGY",
            "LOCATED_IN",
            "ANNOUNCED_AT",
            "REGULATES",
            "OPPOSES",
            "SUPPORTS",
            "COLLABORATES_WITH",
            "INVESTS_IN",
            "ADVISES",
            "LEADS",
        ]
        if rel_type not in valid_types:
            logger.warning(
                "invalid_relationship_type",
                rel_type=rel_type,
                source=source_name,
                target=target_name,
            )
            return

        # Generate entity IDs (we need to find the actual entities)
        with self.driver.session() as session:
            # Find source entity
            source_result = session.run(
                """
                MATCH (e)
                WHERE e.name =~ $name_pattern
                RETURN e.id as id, labels(e)[0] as label
                LIMIT 1
            """,
                name_pattern=f"(?i).*{source_name}.*",
            )

            source_record = source_result.single()
            if not source_record:
                logger.warning("source_entity_not_found", source_name=source_name)
                return

            # Find target entity
            target_result = session.run(
                """
                MATCH (e)
                WHERE e.name =~ $name_pattern
                RETURN e.id as id, labels(e)[0] as label
                LIMIT 1
            """,
                name_pattern=f"(?i).*{target_name}.*",
            )

            target_record = target_result.single()
            if not target_record:
                logger.warning("target_entity_not_found", target_name=target_name)
                return

            # Create relationship
            source_id = source_record["id"]
            target_id = target_record["id"]
            source_label = source_record["label"]
            target_label = target_record["label"]

            # Double-check: MENTIONED_IN should never reach here, but check again
            if rel_type == "MENTIONED_IN":
                logger.error(
                    "unexpected_mentioned_in_relationship",
                    source=source_name,
                    target=target_name,
                )
                return

            # Create typed relationship
            query = f"""
                MATCH (s:{source_label} {{id: $source_id}})
                MATCH (t:{target_label} {{id: $target_id}})
                MERGE (s)-[r:{rel_type}]->(t)
                ON CREATE SET 
                    r.description = $description,
                    r.strength = $strength,
                    r.source_article = $article_id,
                    r.created_at = timestamp()
                ON MATCH SET
                    r.description = r.description + ' | ' + $description,
                    r.strength = (r.strength + $strength) / 2,
                    r.updated_at = timestamp()
            """

            session.run(
                query,
                source_id=source_id,
                target_id=target_id,
                description=description,
                strength=strength,
                article_id=article_id,
            )

    def is_article_ingested(self, article_id: str) -> bool:
        """Check if an article has already been fully ingested into the graph"""
        with self.driver.session() as session:
            # Check if article exists and has entities linked to it
            # Entities link to articles via article_count and source_articles properties
            result = session.run(
                """
                MATCH (a:Article {id: $article_id})
                MATCH (e)
                WHERE e.article_count IS NOT NULL 
                  AND $article_id IN e.source_articles
                RETURN count(e) as entity_count
            """,
                article_id=article_id,
            )
            record = result.single()
            entity_count = record["entity_count"] if record else 0

            # If article has entities linked, consider it ingested
            return entity_count > 0

    def ingest_extraction(self, extraction: Dict, skip_if_exists: bool = True):
        """
        Ingest a complete extraction (entities + relationships)

        Args:
            extraction: Extraction dictionary with article_metadata, entities, relationships
            skip_if_exists: If True, skip articles that have already been ingested
        """
        article_id = extraction["article_metadata"]["article_id"]

        # Check if article already ingested
        if skip_if_exists and self.is_article_ingested(article_id):
            logger.debug("skipping_already_ingested_article", article_id=article_id)
            return

        logger.info("ingesting_article", article_id=article_id)

        # Create article node
        self.create_article_node(extraction["article_metadata"])
        logger.debug("article_node_created", article_id=article_id)

        # Create entity nodes (filter out TechCrunch/Disrupt)
        entity_count = 0
        skipped_count = 0
        from utils.filter_techcrunch import filter_techcrunch_entities

        filtered_entities, filtered_names = filter_techcrunch_entities(
            extraction["entities"]
        )
        skipped_count = len(filtered_names)

        for entity in filtered_entities:
            result = self.create_entity_node(entity, article_id)
            if result:  # Only count if node was actually created
                entity_count += 1

        if skipped_count > 0:
            logger.debug("skipped_techcrunch_entities", count=skipped_count)
        logger.info("entities_created", count=entity_count, article_id=article_id)

        # Create relationships (filter out MENTIONED_IN and TechCrunch/Disrupt related)
        rel_count = 0
        skipped_mentioned = 0
        skipped_techcrunch = 0

        from utils.filter_techcrunch import filter_techcrunch_relationship

        for relationship in extraction["relationships"]:
            rel_type = relationship.get("type", "")
            # Skip MENTIONED_IN relationships - these should never be created
            if rel_type == "MENTIONED_IN":
                skipped_mentioned += 1
                continue

            # Skip relationships involving TechCrunch/Disrupt entities
            should_filter, reason = filter_techcrunch_relationship(relationship)
            if should_filter:
                skipped_techcrunch += 1
                continue

            self.create_relationship(relationship, article_id)
            rel_count += 1

        if skipped_mentioned > 0:
            logger.debug("skipped_mentioned_in_relationships", count=skipped_mentioned)
        if skipped_techcrunch > 0:
            logger.debug("skipped_techcrunch_relationships", count=skipped_techcrunch)
        logger.info("relationships_created", count=rel_count, article_id=article_id)

    def get_statistics(self) -> Dict:
        """Get graph statistics"""
        with self.driver.session() as session:
            # Count nodes by type
            node_counts = {}
            labels = [
                "Company",
                "Person",
                "Investor",
                "Technology",
                "Product",
                "FundingRound",
                "Location",
                "Event",
                "Article",
            ]

            for label in labels:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                record = result.single()
                node_counts[label] = record["count"] if record else 0

            # Count relationships
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            record = rel_result.single()
            total_relationships = record["count"] if record else 0

            return {
                "nodes": node_counts,
                "total_nodes": sum(node_counts.values()),
                "total_relationships": total_relationships,
            }

    def print_statistics(self):
        """Print graph statistics"""
        stats = self.get_statistics()
        logger.info("graph_statistics", **stats)

    def enrich_company_node(self, company_name: str, enriched_data: Dict):
        """
        Dynamically enrich a Company node with all available intelligence data

        Args:
            company_name: Name of the company
            enriched_data: Enriched intelligence data from aggregator
        """
        with self.driver.session() as session:
            # Find the company node
            find_result = session.run(
                """
                MATCH (c:Company)
                WHERE c.name =~ $name_pattern
                RETURN c.id as id
                LIMIT 1
            """,
                name_pattern=f"(?i).*{company_name}.*",
            )

            company_record = find_result.single()
            if not company_record:
                logger.warning("company_not_found_in_graph", company_name=company_name)
                return False

            company_id = company_record["id"]

            # Extract enrichment data
            data = enriched_data.get("data", {})
            confidence = enriched_data.get("confidence_score", 0.0)
            timestamp = enriched_data.get("enrichment_timestamp")

            # Build SET clause dynamically from all available properties
            set_clauses = []
            params = {"company_id": company_id}

            # Always set enrichment metadata
            set_clauses.append("c.enrichment_status = 'enriched'")
            set_clauses.append("c.enrichment_timestamp = $enrichment_timestamp")
            set_clauses.append("c.enrichment_confidence = $enrichment_confidence")
            set_clauses.append("c.updated_at = timestamp()")
            params["enrichment_timestamp"] = timestamp
            params["enrichment_confidence"] = confidence

            # Process all properties in the enriched data dynamically
            for key, value in data.items():
                if value is None:
                    continue

                # Skip metadata fields that aren't node properties
                if key in ["relationships", "mentions_count"]:
                    continue

                # Handle special cases
                if key == "description":
                    # Only use enriched description if it's substantial
                    if isinstance(value, str) and len(value) > 50:
                        set_clauses.append(
                            "c.enriched_description = $enriched_description"
                        )
                        params["enriched_description"] = value
                    continue

                if key == "executives":
                    # Convert executives list to list of strings (name - title)
                    if isinstance(value, list) and value:
                        exec_list = []
                        for e in value:
                            if isinstance(e, dict):
                                exec_list.append(
                                    f"{e.get('name', '')} - {e.get('title', '')}"
                                )
                            elif isinstance(e, str):
                                exec_list.append(e)
                        if exec_list:
                            set_clauses.append(f"c.{key} = ${key}")
                            params[key] = exec_list
                    continue

                # Handle list fields (founders, products, technologies, etc.)
                if isinstance(value, list):
                    if value:  # Only set if list is not empty
                        set_clauses.append(f"c.{key} = ${key}")
                        params[key] = value
                # Handle dict fields (like social_links)
                elif isinstance(value, dict):
                    if value:  # Only set if dict is not empty
                        set_clauses.append(f"c.{key} = ${key}")
                        params[key] = value
                # Handle primitive values (strings, numbers, booleans)
                else:
                    set_clauses.append(f"c.{key} = ${key}")
                    params[key] = value

            # Build the final query
            if not set_clauses:
                logger.warning("no_enrichment_data", company_name=company_name)
                return False

            query = f"""
                MATCH (c:Company {{id: $company_id}})
                SET {', '.join(set_clauses)}
                RETURN c.id as id
            """

            try:
                session.run(query, **params)
                # Log which properties were set
                property_count = len(
                    [
                        k
                        for k in params.keys()
                        if k != "company_id"
                        and k not in ["enrichment_timestamp", "enrichment_confidence"]
                    ]
                )
                logger.info(
                    "company_enriched",
                    company_name=company_name,
                    property_count=property_count,
                )
                return True
            except Exception as e:
                logger.error(
                    "company_enrichment_error",
                    company_name=company_name,
                    error=str(e),
                    exc_info=True,
                )
                return False

    def enrich_all_companies(self, enriched_companies: Dict[str, Dict]):
        """
        Enrich all companies in the graph with intelligence data

        Args:
            enriched_companies: Dictionary mapping company names to enriched data
        """
        logger.info(
            "enriching_companies_starting", company_count=len(enriched_companies)
        )

        enriched_count = 0
        failed_count = 0

        for company_name, enriched_data in enriched_companies.items():
            try:
                success = self.enrich_company_node(company_name, enriched_data)
                if success:
                    enriched_count += 1
                    confidence = enriched_data.get("confidence_score", 0.0)
                    logger.info(
                        "company_enriched",
                        company_name=company_name,
                        confidence=confidence,
                    )
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                logger.warning(
                    "company_enrichment_failed", company_name=company_name, error=str(e)
                )

        logger.info(
            "enrichment_complete",
            enriched_count=enriched_count,
            failed_count=failed_count,
        )

        return {
            "enriched": enriched_count,
            "failed": failed_count,
            "total": len(enriched_companies),
        }


def build_graph_from_extractions(
    extractions_file: str, neo4j_uri: str, neo4j_user: str, neo4j_password: str
):
    """
    Build complete knowledge graph from extraction file

    Args:
        extractions_file: Path to all_extractions.json
        neo4j_uri: Neo4j connection URI (e.g., "bolt://localhost:7687")
        neo4j_user: Neo4j username
        neo4j_password: Neo4j password
    """

    # Load extractions
    with open(extractions_file, "r", encoding="utf-8") as f:
        extractions = json.load(f)

    logger.info("extractions_loaded", count=len(extractions))

    # Initialize graph builder
    builder = TechCrunchGraphBuilder(neo4j_uri, neo4j_user, neo4j_password)

    try:
        # Initialize schema
        logger.info("initializing_neo4j_schema")
        builder.initialize_schema()

        # Ingest each extraction
        logger.info("ingesting_articles", count=len(extractions))
        ingested_count = 0
        skipped_count = 0

        for i, extraction in enumerate(extractions, 1):
            logger.debug(
                "ingesting_article_progress", current=i + 1, total=len(extractions)
            )
            article_id = extraction.get("article_metadata", {}).get(
                "article_id", "unknown"
            )

            # Check if already ingested
            if builder.is_article_ingested(article_id):
                logger.debug("skipping_already_ingested", article_id=article_id)
                skipped_count += 1
                continue

            builder.ingest_extraction(extraction, skip_if_exists=False)
            ingested_count += 1

        if skipped_count > 0:
            logger.info("skipped_already_ingested_articles", count=skipped_count)
        logger.info("ingestion_complete", ingested_count=ingested_count)

        # Print statistics
        builder.print_statistics()

    finally:
        builder.close()


def main():
    """Example usage"""
    import os

    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()

    # Configuration
    EXTRACTIONS_FILE = "data/processing/all_extractions.json"
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

    build_graph_from_extractions(
        extractions_file=EXTRACTIONS_FILE,
        neo4j_uri=NEO4J_URI,
        neo4j_user=NEO4J_USER,
        neo4j_password=NEO4J_PASSWORD,
    )


if __name__ == "__main__":
    main()
