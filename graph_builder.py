"""
Neo4j Knowledge Graph Builder for TechCrunch Articles
Builds a knowledge graph from extracted entities and relationships
"""

import json
from pathlib import Path
from typing import List, Dict
from neo4j import GraphDatabase
from collections import defaultdict
import hashlib


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
                "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                    print(f"✓ Created constraint")
                except Exception as e:
                    print(f"  Constraint may already exist: {e}")
            
            # Indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.name)",
                "CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.name)",
                "CREATE INDEX IF NOT EXISTS FOR (a:Article) ON (a.published_date)"
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                    print(f"✓ Created index")
                except Exception as e:
                    print(f"  Index may already exist: {e}")
    
    @staticmethod
    def generate_entity_id(name: str, entity_type: str) -> str:
        """Generate consistent ID for entity"""
        normalized = name.lower().strip()
        return hashlib.md5(f"{entity_type}:{normalized}".encode()).hexdigest()[:12]
    
    def create_article_node(self, metadata: Dict) -> str:
        """Create Article node"""
        with self.driver.session() as session:
            result = session.run("""
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
                published_date=metadata["published_date"]
            )
            record = result.single()
            return record["id"] if record else None
    
    def create_entity_node(self, entity: Dict, article_id: str):
        """Create entity node based on type"""
        entity_type = entity["type"].upper()
        name = entity["name"]
        description = entity["description"]
        
        # Generate consistent ID
        entity_id = self.generate_entity_id(name, entity_type)
        
        # Track entity mentions for deduplication
        self.entity_registry[entity_id].append({
            "name": name,
            "type": entity_type,
            "description": description,
            "article_id": article_id
        })
        
        with self.driver.session() as session:
            # Map entity type to node label
            node_label = self._get_node_label(entity_type)
            
            # Create or update entity node
            query = f"""
                MERGE (e:{node_label} {{id: $id}})
                ON CREATE SET 
                    e.name = $name,
                    e.description = $description,
                    e.created_at = timestamp(),
                    e.mention_count = 1
                ON MATCH SET
                    e.description = e.description + ' | ' + $description,
                    e.mention_count = e.mention_count + 1,
                    e.updated_at = timestamp()
                RETURN e.id as id
            """
            
            result = session.run(query,
                id=entity_id,
                name=name,
                description=description
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
            "EVENT": "Event"
        }
        return type_mapping.get(entity_type, "Entity")
    
    def link_article_to_entity(self, entity_id: str, article_id: str, entity_label: str):
        """
        Link article to entity using properties (not relationships)
        This keeps the graph clean and focused on semantic relationships
        """
        with self.driver.session() as session:
            session.run(f"""
                MATCH (e:{entity_label} {{id: $entity_id}})
                SET e.source_articles = CASE 
                    WHEN e.source_articles IS NULL THEN [$article_id]
                    WHEN NOT $article_id IN e.source_articles THEN e.source_articles + $article_id
                    ELSE e.source_articles
                END,
                e.article_count = size(e.source_articles),
                e.last_mentioned = timestamp()
            """, entity_id=entity_id, article_id=article_id)
    
    def create_relationship(self, relationship: Dict, article_id: str):
        """Create relationship between entities"""
        source_name = relationship["source"]
        target_name = relationship["target"]
        rel_type = relationship["type"]
        description = relationship["description"]
        strength = relationship.get("strength", 5)
        
        # Generate entity IDs (we need to find the actual entities)
        with self.driver.session() as session:
            # Find source entity
            source_result = session.run("""
                MATCH (e)
                WHERE e.name =~ $name_pattern
                RETURN e.id as id, labels(e)[0] as label
                LIMIT 1
            """, name_pattern=f"(?i).*{source_name}.*")
            
            source_record = source_result.single()
            if not source_record:
                print(f"  ⚠ Source entity not found: {source_name}")
                return
            
            # Find target entity
            target_result = session.run("""
                MATCH (e)
                WHERE e.name =~ $name_pattern
                RETURN e.id as id, labels(e)[0] as label
                LIMIT 1
            """, name_pattern=f"(?i).*{target_name}.*")
            
            target_record = target_result.single()
            if not target_record:
                print(f"  ⚠ Target entity not found: {target_name}")
                return
            
            # Create relationship
            source_id = source_record["id"]
            target_id = target_record["id"]
            source_label = source_record["label"]
            target_label = target_record["label"]
            
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
            
            session.run(query,
                source_id=source_id,
                target_id=target_id,
                description=description,
                strength=strength,
                article_id=article_id
            )
    
    def ingest_extraction(self, extraction: Dict):
        """Ingest a complete extraction (entities + relationships)"""
        article_id = extraction["article_metadata"]["article_id"]
        
        print(f"\nIngesting article: {article_id}")
        
        # Create article node
        self.create_article_node(extraction["article_metadata"])
        print(f"  ✓ Created article node")
        
        # Create entity nodes
        entity_count = 0
        for entity in extraction["entities"]:
            self.create_entity_node(entity, article_id)
            entity_count += 1
        print(f"  ✓ Created {entity_count} entity nodes")
        
        # Create relationships
        rel_count = 0
        for relationship in extraction["relationships"]:
            self.create_relationship(relationship, article_id)
            rel_count += 1
        print(f"  ✓ Created {rel_count} relationships")
    
    def get_statistics(self) -> Dict:
        """Get graph statistics"""
        with self.driver.session() as session:
            # Count nodes by type
            node_counts = {}
            labels = ["Company", "Person", "Investor", "Technology", 
                     "Product", "FundingRound", "Location", "Event", "Article"]
            
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
                "total_relationships": total_relationships
            }
    
    def print_statistics(self):
        """Print graph statistics"""
        stats = self.get_statistics()
        
        print("\n" + "="*80)
        print("KNOWLEDGE GRAPH STATISTICS")
        print("="*80)
        print(f"Total Nodes: {stats['total_nodes']}")
        print(f"Total Relationships: {stats['total_relationships']}")
        print("\nNode Breakdown:")
        for label, count in stats['nodes'].items():
            if count > 0:
                print(f"  {label}: {count}")
        print("="*80 + "\n")


def build_graph_from_extractions(
    extractions_file: str,
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str
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
    with open(extractions_file, 'r', encoding='utf-8') as f:
        extractions = json.load(f)
    
    print(f"Loaded {len(extractions)} extractions")
    
    # Initialize graph builder
    builder = TechCrunchGraphBuilder(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        # Initialize schema
        print("\nInitializing Neo4j schema...")
        builder.initialize_schema()
        
        # Ingest each extraction
        print(f"\nIngesting {len(extractions)} articles into Neo4j...")
        for i, extraction in enumerate(extractions, 1):
            print(f"\n[{i}/{len(extractions)}]", end=" ")
            builder.ingest_extraction(extraction)
        
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
        neo4j_password=NEO4J_PASSWORD
    )


if __name__ == "__main__":
    main()