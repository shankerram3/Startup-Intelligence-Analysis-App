"""
Entity Resolution and Deduplication
Merges duplicate entities in the Neo4j graph
"""

import re
from typing import Dict, List, Tuple, Set, Optional
from neo4j import GraphDatabase
from .entity_normalization import (
    normalize_entity_name,
    are_similar_entities,
    get_canonical_name,
)


class EntityResolver:
    """Resolve and merge duplicate entities in the graph"""

    def __init__(self, driver: GraphDatabase):
        self.driver = driver

    def find_duplicate_entities(
        self, entity_type: str = None, threshold: float = 0.85
    ) -> List[Tuple[str, str, float]]:
        """
        Find duplicate entities in the graph

        Args:
            entity_type: Filter by entity type (Company, Person, etc.) or None for all
            threshold: Similarity threshold (0-1)

        Returns:
            List of (entity_id_1, entity_id_2, similarity) tuples
        """
        duplicates = []

        with self.driver.session() as session:
            # Get all entities (optionally filtered by type)
            if entity_type:
                query = f"""
                    MATCH (e:{entity_type})
                    RETURN e.id as id, e.name as name
                """
            else:
                query = """
                    MATCH (e)
                    WHERE NOT e:Article
                    RETURN e.id as id, e.name as name, labels(e)[0] as type
                """

            result = session.run(query)
            entities = list(result)

            # Compare all pairs
            for i, entity1 in enumerate(entities):
                for entity2 in entities[i + 1 :]:
                    name1 = entity1["name"]
                    name2 = entity2["name"]

                    # Skip if already merged or same ID
                    if entity1["id"] == entity2["id"]:
                        continue

                    # Check similarity
                    if are_similar_entities(name1, name2, threshold):
                        similarity = self._calculate_similarity(name1, name2)
                        duplicates.append((entity1["id"], entity2["id"], similarity))

        return duplicates

    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity ratio between two names"""
        from difflib import SequenceMatcher

        norm1 = normalize_entity_name(name1)
        norm2 = normalize_entity_name(name2)
        return SequenceMatcher(None, norm1, norm2).ratio()

    def merge_entities(
        self, entity_id_1: str, entity_id_2: str, keep_canonical: bool = True
    ) -> bool:
        """
        Merge two duplicate entities

        Args:
            entity_id_1: First entity ID
            entity_id_2: Second entity ID (will be merged into entity_id_1)
            keep_canonical: If True, keep the entity with the longer/more common name

        Returns:
            True if merge successful, False otherwise
        """
        with self.driver.session() as session:
            # Get both entities
            query1 = """
                MATCH (e {id: $id})
                RETURN e.id as id, e.name as name, labels(e)[0] as type, e.description as description
            """

            result1 = session.run(query1, id=entity_id_1)
            entity1 = result1.single()

            result2 = session.run(query1, id=entity_id_2)
            entity2 = result2.single()

            if not entity1 or not entity2:
                return False

            # Determine which to keep (canonical name)
            if keep_canonical:
                canonical_name = get_canonical_name([entity1["name"], entity2["name"]])
                if canonical_name == entity2["name"]:
                    # Swap so entity_id_1 becomes the canonical
                    entity_id_1, entity_id_2 = entity_id_2, entity_id_1
                    entity1, entity2 = entity2, entity1

            try:
                # Step 1: Merge properties
                session.run(
                    """
                    MATCH (e1 {id: $id1})
                    MATCH (e2 {id: $id2})
                    WHERE e1.id <> e2.id
                    SET e1.description = coalesce(e1.description, '') + ' | ' + coalesce(e2.description, '')
                    SET e1.source_articles = CASE
                        WHEN e1.source_articles IS NULL AND e2.source_articles IS NULL THEN []
                        WHEN e1.source_articles IS NULL THEN e2.source_articles
                        WHEN e2.source_articles IS NULL THEN e1.source_articles
                        ELSE [x IN e1.source_articles WHERE NOT x IN e2.source_articles] + e2.source_articles
                    END
                    SET e1.article_count = size(coalesce(e1.source_articles, []))
                """,
                    id1=entity_id_1,
                    id2=entity_id_2,
                )

                # Step 2: Redirect outgoing relationships (simplified)
                # Get all outgoing relationships from e2
                outgoing = session.run(
                    """
                    MATCH (e2 {id: $id2})-[r]->(target)
                    RETURN type(r) as rel_type, target.id as target_id, properties(r) as props
                """,
                    id2=entity_id_2,
                )

                for record in outgoing:
                    rel_type = record["rel_type"]
                    target_id = record["target_id"]
                    props = record["props"]

                    # Check if relationship already exists
                    exists = session.run(
                        """
                        MATCH (e1 {id: $id1})-[r]->(t {id: $target_id})
                        WHERE type(r) = $rel_type
                        RETURN count(r) > 0 as exists
                    """,
                        id1=entity_id_1,
                        target_id=target_id,
                        rel_type=rel_type,
                    )

                    exists_record = exists.single()
                    if exists_record and not exists_record["exists"]:
                        # Create new relationship
                        session.run(
                            f"""
                            MATCH (e1 {{id: $id1}})
                            MATCH (t {{id: $target_id}})
                            MERGE (e1)-[r:{rel_type}]->(t)
                            SET r = $props, r.created_at = timestamp()
                        """,
                            id1=entity_id_1,
                            target_id=target_id,
                            props=props,
                        )

                # Delete old outgoing relationships
                session.run(
                    """
                    MATCH (e2 {id: $id2})-[r]->()
                    DELETE r
                """,
                    id2=entity_id_2,
                )

                # Step 3: Redirect incoming relationships
                incoming = session.run(
                    """
                    MATCH (source)-[r]->(e2 {id: $id2})
                    RETURN type(r) as rel_type, source.id as source_id, properties(r) as props
                """,
                    id2=entity_id_2,
                )

                for record in incoming:
                    rel_type = record["rel_type"]
                    source_id = record["source_id"]
                    props = record["props"]

                    # Check if relationship already exists
                    exists = session.run(
                        """
                        MATCH (s {id: $source_id})-[r]->(e1 {id: $id1})
                        WHERE type(r) = $rel_type
                        RETURN count(r) > 0 as exists
                    """,
                        source_id=source_id,
                        id1=entity_id_1,
                        rel_type=rel_type,
                    )

                    exists_record = exists.single()
                    if exists_record and not exists_record["exists"]:
                        # Create new relationship
                        session.run(
                            f"""
                            MATCH (s {{id: $source_id}})
                            MATCH (e1 {{id: $id1}})
                            MERGE (s)-[r:{rel_type}]->(e1)
                            SET r = $props, r.created_at = timestamp()
                        """,
                            source_id=source_id,
                            id1=entity_id_1,
                            props=props,
                        )

                # Delete old incoming relationships
                session.run(
                    """
                    MATCH ()-[r]->(e2 {id: $id2})
                    DELETE r
                """,
                    id2=entity_id_2,
                )

                # Step 4: Delete entity2
                session.run(
                    """
                    MATCH (e2 {id: $id2})
                    DELETE e2
                """,
                    id2=entity_id_2,
                )

                return True

            except Exception as e:
                print(f"⚠️  Error merging entities {entity_id_1} and {entity_id_2}: {e}")
                return False

    def merge_all_duplicates(
        self, entity_type: str = None, threshold: float = 0.85, dry_run: bool = False
    ) -> Dict:
        """
        Find and merge all duplicate entities

        Args:
            entity_type: Filter by entity type or None for all
            threshold: Similarity threshold
            dry_run: If True, only report what would be merged

        Returns:
            Dictionary with merge statistics
        """
        print(f"\n{'='*80}")
        print(f"FINDING DUPLICATE ENTITIES")
        print(f"{'='*80}\n")

        duplicates = self.find_duplicate_entities(entity_type, threshold)

        print(f"Found {len(duplicates)} potential duplicate pairs\n")

        if dry_run:
            print("DRY RUN - No merges performed\n")
            for id1, id2, sim in duplicates[:10]:  # Show first 10
                print(f"  Would merge: {id1} <-> {id2} (similarity: {sim:.2f})")
            return {"found": len(duplicates), "merged": 0}

        # Merge duplicates
        merged_count = 0
        failed_count = 0

        for entity_id_1, entity_id_2, similarity in duplicates:
            if self.merge_entities(entity_id_1, entity_id_2):
                merged_count += 1
                print(
                    f"  ✓ Merged: {entity_id_1} <-> {entity_id_2} (similarity: {similarity:.2f})"
                )
            else:
                failed_count += 1

        print(f"\n{'='*80}")
        print(f"MERGE COMPLETE: {merged_count} merged, {failed_count} failed")
        print(f"{'='*80}\n")

        return {
            "found": len(duplicates),
            "merged": merged_count,
            "failed": failed_count,
        }
