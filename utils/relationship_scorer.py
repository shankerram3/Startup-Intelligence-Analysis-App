"""
Relationship Strength Scoring
Calculate relationship strength based on frequency, recency, source credibility, and context
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from neo4j import GraphDatabase


class RelationshipScorer:
    """Calculate and update relationship strengths"""

    def __init__(self, driver: GraphDatabase):
        self.driver = driver
        # Cache for frequency scores to avoid redundant database queries
        self._frequency_cache: Dict[str, float] = {}

    def calculate_strength(self, relationship: Dict, article_metadata: Dict) -> float:
        """
        Calculate relationship strength from 0-10

        Factors:
        - Base strength from extraction (0-10)
        - Frequency: How many times mentioned (weight: 0.3)
        - Recency: When last mentioned (weight: 0.2)
        - Source credibility: Direct quote vs inference (weight: 0.3)
        - Context importance: Main topic vs passing mention (weight: 0.2)

        Args:
            relationship: Relationship dictionary
            article_metadata: Article metadata with published_date

        Returns:
            Strength score (0-10)
        """
        base_strength = relationship.get("strength", 5)

        # Frequency component (0-10)
        frequency_score = self._calculate_frequency_score(relationship)

        # Recency component (0-10)
        recency_score = self._calculate_recency_score(relationship, article_metadata)

        # Source credibility (0-10)
        credibility_score = self._calculate_credibility_score(relationship)

        # Context importance (0-10)
        context_score = self._calculate_context_score(relationship)

        # Weighted average
        weighted_strength = (
            base_strength * 0.1  # Base gets 10% weight
            + frequency_score * 0.3
            + recency_score * 0.2
            + credibility_score * 0.3
            + context_score * 0.2
        )

        return min(10.0, max(0.0, weighted_strength))

    def _calculate_frequency_score(self, relationship: Dict) -> float:
        """
        Calculate frequency score based on how often relationship is mentioned
        Uses caching to avoid redundant database queries

        Returns:
            Score 0-10 (10 = very frequent, 0 = rare)
        """
        source = relationship.get("source", "")
        target = relationship.get("target", "")
        rel_type = relationship.get("type", "")

        # Create cache key
        cache_key = f"{source}::{target}::{rel_type}"

        # Check cache first
        if cache_key in self._frequency_cache:
            return self._frequency_cache[cache_key]

        # Calculate frequency from database
        with self.driver.session() as session:
            # Count occurrences in graph
            query = """
                MATCH (s)-[r]->(t)
                WHERE s.name = $source AND t.name = $target AND type(r) = $type
                RETURN count(r) as count
            """

            result = session.run(query, source=source, target=target, type=rel_type)
            record = result.single()
            count = record["count"] if record else 0

            # Normalize: 1 mention = 5, 5+ mentions = 10
            if count == 0:
                score = 0.0
            elif count == 1:
                score = 5.0
            elif count <= 5:
                score = 5.0 + (count - 1) * 1.25  # 5 -> 10 over 4 steps
            else:
                score = 10.0

            # Cache the result
            self._frequency_cache[cache_key] = score
            return score

    def _calculate_recency_score(
        self, relationship: Dict, article_metadata: Dict
    ) -> float:
        """
        Calculate recency score based on when relationship was last mentioned

        Returns:
            Score 0-10 (10 = very recent, 0 = old)
        """
        published_date = article_metadata.get("published_date")
        if not published_date:
            return 5.0  # Default if no date

        try:
            # Parse date
            if "T" in published_date:
                article_date = datetime.fromisoformat(
                    published_date.replace("Z", "+00:00")
                )
            else:
                article_date = datetime.strptime(published_date, "%Y-%m-%d")

            now = datetime.now(article_date.tzinfo if article_date.tzinfo else None)

            # Calculate days since article
            days_ago = (now - article_date).days

            # Score: 0 days = 10, 30 days = 7, 90 days = 5, 365 days = 0
            if days_ago <= 7:
                return 10.0
            elif days_ago <= 30:
                return 10.0 - (days_ago - 7) * 0.13  # 7-30 days
            elif days_ago <= 90:
                return 7.0 - (days_ago - 30) * 0.033  # 30-90 days
            elif days_ago <= 365:
                return 5.0 - (days_ago - 90) * 0.018  # 90-365 days
            else:
                return 0.0

        except (ValueError, TypeError):
            return 5.0  # Default on parse error

    def _calculate_credibility_score(self, relationship: Dict) -> float:
        """
        Calculate source credibility score

        Factors:
        - Direct quote in description = 10
        - Explicit statement = 8
        - Inference = 5
        - Weak inference = 2

        Returns:
            Score 0-10
        """
        description = relationship.get("description", "").lower()

        # Check for direct quotes
        if '"' in description or "'" in description:
            return 10.0

        # Check for explicit statements
        explicit_keywords = ["announced", "confirmed", "stated", "said", "reported"]
        if any(keyword in description for keyword in explicit_keywords):
            return 8.0

        # Check for inference keywords
        inference_keywords = ["likely", "probably", "appears", "seems", "suggests"]
        if any(keyword in description for keyword in inference_keywords):
            return 2.0

        # Default: moderate inference
        return 5.0

    def _calculate_context_score(self, relationship: Dict) -> float:
        """
        Calculate context importance score

        Factors:
        - Description length (longer = more important)
        - Keywords indicating importance
        - Relationship type importance

        Returns:
            Score 0-10
        """
        description = relationship.get("description", "")
        rel_type = relationship.get("type", "")

        # Base score on description length
        desc_length = len(description)
        if desc_length < 50:
            base_score = 3.0
        elif desc_length < 100:
            base_score = 5.0
        elif desc_length < 200:
            base_score = 7.0
        else:
            base_score = 9.0

        # Boost for important relationship types
        important_types = ["ACQUIRED", "FUNDED_BY", "FOUNDED_BY"]
        if rel_type in important_types:
            base_score += 1.0

        # Boost for important keywords
        important_keywords = [
            "major",
            "significant",
            "important",
            "key",
            "primary",
            "main",
        ]
        desc_lower = description.lower()
        keyword_count = sum(1 for kw in important_keywords if kw in desc_lower)
        base_score += min(2.0, keyword_count * 0.5)

        return min(10.0, base_score)

    def update_relationship_strengths(self, rel_type: Optional[str] = None) -> Dict:
        """
        Update all relationship strengths in graph

        Args:
            rel_type: Optional relationship type to filter

        Returns:
            Statistics dictionary
        """
        # Clear cache at the start of each update run to ensure fresh data
        self._frequency_cache.clear()

        with self.driver.session() as session:
            # First, get total count for progress tracking
            if rel_type:
                count_query = """
                    MATCH (s)-[r]->(t)
                    WHERE type(r) = $type
                    RETURN count(r) as total
                """
                count_result = session.run(count_query, type=rel_type)
            else:
                count_query = """
                    MATCH (s)-[r]->(t)
                    RETURN count(r) as total
                """
                count_result = session.run(count_query)

            total_count = count_result.single()["total"] if count_result else 0

            if total_count == 0:
                print(f"   ℹ️  No relationships found to update")
                return {"updated": 0, "total": 0}

            print(f"   📊 Found {total_count} relationships to process")

            if rel_type:
                query = f"""
                    MATCH (s)-[r]->(t)
                    WHERE type(r) = $type
                    RETURN s, r, t, s.name as source, t.name as target, type(r) as type,
                           r.strength as current_strength, r.description as description
                """
                result = session.run(query, type=rel_type)
            else:
                query = """
                    MATCH (s)-[r]->(t)
                    RETURN s, r, t, s.name as source, t.name as target, type(r) as type,
                           r.strength as current_strength, r.description as description
                """
                result = session.run(query)

            updated_count = 0
            processed_count = 0
            log_interval = max(
                1, total_count // 20
            )  # Log every 5% or at least every relationship

            for record in result:
                relationship = {
                    "source": record["source"],
                    "target": record["target"],
                    "type": record["type"],
                    "strength": record["current_strength"] or 5,
                    "description": record["description"] or "",
                }

                # Get article metadata (use most recent article)
                article_query = """
                    MATCH (a:Article)
                    WHERE a.id IN $source_articles
                    RETURN a.published_date as published_date
                    ORDER BY a.published_date DESC
                    LIMIT 1
                """

                # Calculate new strength (simplified - would need article metadata)
                # For now, use frequency-based update
                old_strength = relationship["strength"]
                new_strength = self._calculate_frequency_score(relationship)

                # Update relationship
                update_query = """
                    MATCH (s)-[r]->(t)
                    WHERE s.name = $source AND t.name = $target AND type(r) = $type
                    SET r.strength = $strength, r.updated_at = timestamp()
                """

                session.run(
                    update_query,
                    source=relationship["source"],
                    target=relationship["target"],
                    type=relationship["type"],
                    strength=new_strength,
                )

                updated_count += 1
                processed_count += 1

                # Log progress
                if (
                    processed_count % log_interval == 0
                    or processed_count == total_count
                ):
                    percentage = (processed_count / total_count) * 100
                    print(
                        f"   ⏳ Processing relationship [{processed_count}/{total_count}] ({percentage:.1f}%) - {relationship['type']}: {relationship['source']} → {relationship['target']}"
                    )

            print(f"   ✓ Completed: Updated {updated_count} relationship strengths")

            return {"updated": updated_count, "total": total_count}
