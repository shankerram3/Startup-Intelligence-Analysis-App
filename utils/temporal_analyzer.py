"""
Temporal Analysis for Knowledge Graph
Track relationship timeline, trends, and historical data
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from neo4j import GraphDatabase


class TemporalAnalyzer:
    """Analyze temporal aspects of the knowledge graph"""

    def __init__(self, driver: GraphDatabase):
        self.driver = driver

    def add_temporal_properties(
        self, relationship_id: str, created_date: str, ended_date: Optional[str] = None
    ) -> bool:
        """
        Add temporal properties to a relationship

        Args:
            relationship_id: Relationship internal ID or unique identifier
            created_date: When relationship was formed (ISO date string)
            ended_date: Optional end date (for dissolved relationships)

        Returns:
            True if successful
        """
        with self.driver.session() as session:
            # Use elementId() instead of deprecated id()
            query = """
                MATCH ()-[r]->()
                WHERE elementId(r) = $rel_id
                SET r.created_date = $created_date,
                    r.is_active = CASE WHEN $ended_date IS NULL THEN true ELSE false END,
                    r.ended_date = $ended_date
                RETURN r
            """

            try:
                session.run(
                    query,
                    rel_id=relationship_id,
                    created_date=created_date,
                    ended_date=ended_date,
                )
                return True
            except Exception as e:
                print(f"⚠️  Error adding temporal properties: {e}")
                return False

    def track_funding_trends(
        self, company_name: str, start_date: str, end_date: str
    ) -> List[Dict]:
        """
        Track funding trends for a company over time

        Args:
            company_name: Company name
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            List of funding rounds with dates
        """
        with self.driver.session() as session:
            query = """
                MATCH (c:Company {name: $company})-[:FUNDED_BY]->(i:Investor)
                MATCH (c)<-[:MENTIONED_IN]-(a:Article)
                WHERE a.published_date >= $start_date AND a.published_date <= $end_date
                RETURN a.published_date as date, i.name as investor, 
                       a.title as article_title, a.url as article_url
                ORDER BY a.published_date DESC
            """

            result = session.run(
                query, company=company_name, start_date=start_date, end_date=end_date
            )

            trends = []
            for record in result:
                trends.append(
                    {
                        "date": record["date"],
                        "investor": record["investor"],
                        "article_title": record["article_title"],
                        "article_url": record["article_url"],
                    }
                )

            return trends

    def find_relationship_timeline(
        self, entity1_name: str, entity2_name: str
    ) -> List[Dict]:
        """
        Find timeline of relationship between two entities

        Args:
            entity1_name: First entity name
            entity2_name: Second entity name

        Returns:
            List of relationship events over time
        """
        with self.driver.session() as session:
            query = """
                MATCH (e1 {name: $name1})-[r]-(e2 {name: $name2})
                MATCH (e1)<-[:MENTIONED_IN]-(a:Article)
                WHERE e2 IN a.entities OR e2 IN a.entities
                RETURN a.published_date as date, type(r) as rel_type, 
                       r.description as description, a.title as article_title,
                       r.is_active as is_active, r.created_date as created_date,
                       r.ended_date as ended_date
                ORDER BY a.published_date ASC
            """

            result = session.run(query, name1=entity1_name, name2=entity2_name)

            timeline = []
            for record in result:
                timeline.append(
                    {
                        "date": record["date"],
                        "type": record["rel_type"],
                        "description": record["description"],
                        "article_title": record["article_title"],
                        "is_active": record.get("is_active", True),
                        "created_date": record.get("created_date"),
                        "ended_date": record.get("ended_date"),
                    }
                )

            return timeline

    def get_funding_trends_by_sector(self, sector: str, months: int = 6) -> Dict:
        """
        Get funding trends for a sector over time

        Args:
            sector: Sector name (e.g., "AI", "fintech")
            months: Number of months to analyze

        Returns:
            Dictionary with trend data
        """
        with self.driver.session() as session:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)

            # Find companies in sector (based on description or relationships)
            query = """
                MATCH (c:Company)-[:FUNDED_BY]->(i:Investor)
                WHERE c.description CONTAINS $sector 
                   OR c.name CONTAINS $sector
                MATCH (c)<-[:MENTIONED_IN]-(a:Article)
                WHERE a.published_date >= $start_date
                RETURN a.published_date as date, c.name as company, 
                       i.name as investor, COUNT(*) as count
                ORDER BY a.published_date ASC
            """

            result = session.run(
                query, sector=sector, start_date=start_date.isoformat()
            )

            trends = []
            monthly_counts = {}

            for record in result:
                date_str = record["date"]
                if date_str:
                    try:
                        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        month_key = date.strftime("%Y-%m")

                        if month_key not in monthly_counts:
                            monthly_counts[month_key] = 0
                        monthly_counts[month_key] += 1

                        trends.append(
                            {
                                "date": date_str,
                                "company": record["company"],
                                "investor": record["investor"],
                            }
                        )
                    except:
                        continue

            return {
                "sector": sector,
                "period_months": months,
                "total_funding_events": len(trends),
                "monthly_counts": monthly_counts,
                "events": trends,
            }

    def find_leadership_changes(self, company_name: str) -> List[Dict]:
        """
        Find leadership changes (WORKS_AT relationships ending)

        Args:
            company_name: Company name

        Returns:
            List of leadership changes
        """
        with self.driver.session() as session:
            query = """
                MATCH (p:Person)-[r:WORKS_AT]->(c:Company {name: $company})
                WHERE r.is_active = false OR r.ended_date IS NOT NULL
                RETURN p.name as person, r.created_date as start_date, 
                       r.ended_date as end_date, r.description as description
                ORDER BY r.ended_date DESC
            """

            result = session.run(query, company=company_name)

            changes = []
            for record in result:
                changes.append(
                    {
                        "person": record["person"],
                        "start_date": record.get("start_date"),
                        "end_date": record.get("end_date"),
                        "description": record.get("description"),
                    }
                )

            return changes

    def get_entity_activity_timeline(
        self, entity_name: str, entity_type: str = "Company"
    ) -> List[Dict]:
        """
        Get timeline of all activity for an entity

        Args:
            entity_name: Entity name
            entity_type: Entity type label

        Returns:
            List of events over time
        """
        with self.driver.session() as session:
            query = f"""
                MATCH (e:{entity_type} {{name: $name}})
                MATCH (e)<-[:MENTIONED_IN]-(a:Article)
                OPTIONAL MATCH (e)-[r]->(related)
                RETURN a.published_date as date, a.title as article_title,
                       collect(DISTINCT {{type: type(r), target: related.name}}) as relationships
                ORDER BY a.published_date DESC
            """

            result = session.run(query, name=entity_name)

            timeline = []
            for record in result:
                timeline.append(
                    {
                        "date": record["date"],
                        "article_title": record["article_title"],
                        "relationships": record["relationships"],
                    }
                )

            return timeline
