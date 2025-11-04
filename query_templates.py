"""
Query Template Library - Pre-built Cypher Queries for GraphRAG
Provides common query patterns for knowledge graph exploration
"""

from typing import Dict, List, Optional, Any
from neo4j import Driver


class QueryTemplates:
    """Library of pre-built Cypher query templates"""

    def __init__(self, driver: Driver):
        self.driver = driver

    # =========================================================================
    # ENTITY QUERIES
    # =========================================================================

    def get_entity_by_name(self, entity_name: str, entity_type: Optional[str] = None) -> Dict:
        """
        Get entity details by name

        Args:
            entity_name: Name of the entity
            entity_type: Optional entity type filter

        Returns:
            Entity information
        """
        with self.driver.session() as session:
            if entity_type:
                query = f"""
                    MATCH (e:{entity_type})
                    WHERE toLower(e.name) CONTAINS toLower($name)
                    RETURN e.id as id, e.name as name, labels(e)[0] as type,
                           e.description as description, e.mention_count as mention_count,
                           e.source_articles as source_articles
                    LIMIT 1
                """
            else:
                query = """
                    MATCH (e)
                    WHERE toLower(e.name) CONTAINS toLower($name) AND NOT e:Article
                    RETURN e.id as id, e.name as name, labels(e)[0] as type,
                           e.description as description, e.mention_count as mention_count,
                           e.source_articles as source_articles
                    LIMIT 1
                """

            result = session.run(query, name=entity_name)
            record = result.single()

            if record:
                return dict(record)
            return {}

    def get_entity_by_id(self, entity_id: str) -> Dict:
        """Get entity by ID"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e {id: $id})
                RETURN e.id as id, e.name as name, labels(e)[0] as type,
                       e.description as description, e.mention_count as mention_count,
                       e.source_articles as source_articles,
                       e.community_id as community_id
            """, id=entity_id)

            record = result.single()
            return dict(record) if record else {}

    def search_entities_by_type(self, entity_type: str, limit: int = 10) -> List[Dict]:
        """Search entities by type"""
        with self.driver.session() as session:
            result = session.run(f"""
                MATCH (e:{entity_type})
                RETURN e.id as id, e.name as name, e.description as description,
                       e.mention_count as mention_count
                ORDER BY e.mention_count DESC
                LIMIT $limit
            """, limit=limit)

            return [dict(record) for record in result]

    # =========================================================================
    # COMPANY QUERIES
    # =========================================================================

    def get_company_profile(self, company_name: str) -> Dict:
        """
        Get comprehensive company profile with relationships

        Args:
            company_name: Name of the company

        Returns:
            Company profile with funding, founders, investors, etc.
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Company)
                WHERE toLower(c.name) CONTAINS toLower($name)

                OPTIONAL MATCH (c)-[r:FUNDED_BY]->(i:Investor)
                WITH c, collect(DISTINCT {name: i.name, type: type(r)}) as investors

                OPTIONAL MATCH (c)-[r2:FOUNDED_BY]-(p:Person)
                WITH c, investors, collect(DISTINCT p.name) as founders

                OPTIONAL MATCH (c)-[r3:USES_TECHNOLOGY|PARTNERS_WITH]-(t)
                WHERE NOT t:Article
                WITH c, investors, founders, collect(DISTINCT {name: t.name, relationship: type(r3)}) as technologies

                OPTIONAL MATCH (c)-[r4:LOCATED_IN]->(l:Location)
                WITH c, investors, founders, technologies, collect(DISTINCT l.name) as locations

                OPTIONAL MATCH (c)-[r5:COMPETES_WITH]-(comp:Company)
                WITH c, investors, founders, technologies, locations, collect(DISTINCT comp.name) as competitors

                RETURN c.id as id, c.name as name, c.description as description,
                       c.mention_count as mention_count,
                       investors, founders, technologies, locations, competitors
                LIMIT 1
            """, name=company_name)

            record = result.single()
            return dict(record) if record else {}

    def get_companies_by_funding(self, min_investors: int = 1) -> List[Dict]:
        """Get companies by funding relationships"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Company)-[:FUNDED_BY]->(i:Investor)
                WITH c, collect(DISTINCT i.name) as investors, count(DISTINCT i) as investor_count
                WHERE investor_count >= $min_investors
                RETURN c.id as id, c.name as name, c.description as description,
                       investor_count, investors
                ORDER BY investor_count DESC
                LIMIT 20
            """, min_investors=min_investors)

            return [dict(record) for record in result]

    def get_companies_in_sector(self, sector_keyword: str) -> List[Dict]:
        """
        Find companies in a specific sector (AI, fintech, etc.)

        Args:
            sector_keyword: Keyword to search in descriptions

        Returns:
            List of companies in the sector
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Company)
                WHERE toLower(c.description) CONTAINS toLower($keyword)

                OPTIONAL MATCH (c)-[:FUNDED_BY]->(i:Investor)
                WITH c, count(DISTINCT i) as investor_count

                RETURN c.id as id, c.name as name, c.description as description,
                       c.mention_count as mention_count, investor_count
                ORDER BY c.mention_count DESC
                LIMIT 20
            """, keyword=sector_keyword)

            return [dict(record) for record in result]

    # =========================================================================
    # INVESTOR QUERIES
    # =========================================================================

    def get_investor_portfolio(self, investor_name: str) -> Dict:
        """
        Get investor's portfolio of investments

        Args:
            investor_name: Name of the investor

        Returns:
            Investor portfolio information
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (i:Investor)
                WHERE toLower(i.name) CONTAINS toLower($name)

                OPTIONAL MATCH (c:Company)-[:FUNDED_BY]->(i)
                WITH i, collect(DISTINCT {
                    name: c.name,
                    description: c.description,
                    mention_count: c.mention_count
                }) as portfolio

                RETURN i.id as id, i.name as name, i.description as description,
                       size(portfolio) as portfolio_size, portfolio
                LIMIT 1
            """, name=investor_name)

            record = result.single()
            return dict(record) if record else {}

    def get_top_investors(self, limit: int = 10) -> List[Dict]:
        """Get most active investors by portfolio size"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (i:Investor)<-[:FUNDED_BY]-(c:Company)
                WITH i, count(DISTINCT c) as portfolio_size,
                     collect(DISTINCT c.name) as companies
                RETURN i.id as id, i.name as name, i.description as description,
                       portfolio_size, companies
                ORDER BY portfolio_size DESC
                LIMIT $limit
            """, limit=limit)

            return [dict(record) for record in result]

    # =========================================================================
    # PERSON QUERIES
    # =========================================================================

    def get_person_profile(self, person_name: str) -> Dict:
        """
        Get person's profile with company affiliations

        Args:
            person_name: Name of the person

        Returns:
            Person profile information
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person)
                WHERE toLower(p.name) CONTAINS toLower($name)

                OPTIONAL MATCH (p)-[r:WORKS_AT|FOUNDED_BY]-(c:Company)
                WITH p, collect(DISTINCT {
                    company: c.name,
                    relationship: type(r)
                }) as affiliations

                RETURN p.id as id, p.name as name, p.description as description,
                       p.mention_count as mention_count, affiliations
                LIMIT 1
            """, name=person_name)

            record = result.single()
            return dict(record) if record else {}

    # =========================================================================
    # RELATIONSHIP QUERIES
    # =========================================================================

    def get_entity_relationships(self, entity_id: str, max_hops: int = 2) -> Dict:
        """
        Get entity's relationships up to N hops

        Args:
            entity_id: ID of the entity
            max_hops: Maximum relationship hops (1-3)

        Returns:
            Entity with its relationship network
        """
        with self.driver.session() as session:
            result = session.run(f"""
                MATCH (e {{id: $id}})
                MATCH path = (e)-[*1..{max_hops}]-(related)
                WHERE NOT related:Article

                WITH e, related, relationships(path) as rels
                WITH e,
                     collect(DISTINCT {{
                         id: related.id,
                         name: related.name,
                         type: labels(related)[0],
                         relationship_types: [r IN rels | type(r)]
                     }}) as related_entities

                RETURN e.id as id, e.name as name, labels(e)[0] as type,
                       e.description as description, related_entities
            """, id=entity_id)

            record = result.single()
            return dict(record) if record else {}

    def find_connection_path(self, entity1_name: str, entity2_name: str,
                            max_hops: int = 4) -> List[Dict]:
        """
        Find shortest path between two entities

        Args:
            entity1_name: First entity name
            entity2_name: Second entity name
            max_hops: Maximum path length

        Returns:
            List of paths between entities
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e1), (e2)
                WHERE toLower(e1.name) CONTAINS toLower($name1)
                  AND toLower(e2.name) CONTAINS toLower($name2)
                  AND NOT e1:Article AND NOT e2:Article

                MATCH path = shortestPath((e1)-[*1..%d]-(e2))

                RETURN [n IN nodes(path) | {name: n.name, type: labels(n)[0]}] as nodes,
                       [r IN relationships(path) | {type: type(r), strength: r.strength}] as relationships,
                       length(path) as path_length
                ORDER BY path_length
                LIMIT 5
            """ % max_hops, name1=entity1_name, name2=entity2_name)

            return [dict(record) for record in result]

    def get_competitive_landscape(self, company_name: str) -> Dict:
        """
        Get competitive landscape for a company

        Args:
            company_name: Name of the company

        Returns:
            Company with competitors and shared relationships
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Company)
                WHERE toLower(c.name) CONTAINS toLower($name)

                // Direct competitors
                OPTIONAL MATCH (c)-[:COMPETES_WITH]-(comp:Company)
                WITH c, collect(DISTINCT comp.name) as direct_competitors

                // Companies in same sector (similar technologies)
                OPTIONAL MATCH (c)-[:USES_TECHNOLOGY]->(t:Technology)<-[:USES_TECHNOLOGY]-(similar:Company)
                WHERE c <> similar
                WITH c, direct_competitors,
                     collect(DISTINCT similar.name)[..5] as similar_companies

                // Shared investors
                OPTIONAL MATCH (c)-[:FUNDED_BY]->(i:Investor)<-[:FUNDED_BY]-(funded:Company)
                WHERE c <> funded
                WITH c, direct_competitors, similar_companies,
                     collect(DISTINCT funded.name)[..5] as companies_with_shared_investors

                RETURN c.name as company, c.description as description,
                       direct_competitors, similar_companies,
                       companies_with_shared_investors
                LIMIT 1
            """, name=company_name)

            record = result.single()
            return dict(record) if record else {}

    # =========================================================================
    # COMMUNITY QUERIES
    # =========================================================================

    def get_communities(self, min_size: int = 3) -> List[Dict]:
        """Get all detected communities"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e)
                WHERE e.community_id IS NOT NULL AND NOT e:Article
                WITH e.community_id as community_id,
                     collect({name: e.name, type: labels(e)[0]}) as members,
                     count(e) as size
                WHERE size >= $min_size
                RETURN community_id, size, members
                ORDER BY size DESC
            """, min_size=min_size)

            return [dict(record) for record in result]

    def get_community_by_id(self, community_id: int) -> Dict:
        """Get detailed information about a specific community"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e)
                WHERE e.community_id = $community_id AND NOT e:Article

                WITH collect(DISTINCT {
                    id: e.id,
                    name: e.name,
                    type: labels(e)[0],
                    description: e.description
                }) as members

                // Get internal relationships
                MATCH (e1)-[r]->(e2)
                WHERE e1.community_id = $community_id
                  AND e2.community_id = $community_id
                  AND NOT e1:Article AND NOT e2:Article

                WITH members,
                     collect({
                         from: e1.name,
                         to: e2.name,
                         type: type(r),
                         strength: r.strength
                     }) as relationships

                RETURN $community_id as community_id,
                       size(members) as size,
                       members,
                       relationships
            """, community_id=community_id)

            record = result.single()
            return dict(record) if record else {}

    # =========================================================================
    # TEMPORAL QUERIES
    # =========================================================================

    def get_recent_entities(self, days: int = 30, limit: int = 10) -> List[Dict]:
        """Get recently mentioned entities"""
        with self.driver.session() as session:
            cutoff_timestamp = (days * 24 * 60 * 60 * 1000)  # Convert days to milliseconds

            result = session.run("""
                MATCH (e)
                WHERE e.last_mentioned IS NOT NULL
                  AND e.last_mentioned > timestamp() - $cutoff
                  AND NOT e:Article
                RETURN e.id as id, e.name as name, labels(e)[0] as type,
                       e.description as description,
                       e.last_mentioned as last_mentioned
                ORDER BY e.last_mentioned DESC
                LIMIT $limit
            """, cutoff=cutoff_timestamp, limit=limit)

            return [dict(record) for record in result]

    def get_funding_timeline(self, company_name: Optional[str] = None) -> List[Dict]:
        """
        Get funding events timeline

        Args:
            company_name: Optional company name filter

        Returns:
            Funding events ordered by time
        """
        with self.driver.session() as session:
            if company_name:
                result = session.run("""
                    MATCH (c:Company)-[:FUNDED_BY]->(i:Investor)
                    WHERE toLower(c.name) CONTAINS toLower($name)

                    OPTIONAL MATCH (c)-[:ANNOUNCED_AT]->(a:Article)

                    RETURN c.name as company, i.name as investor,
                           a.published_date as date, a.title as article_title
                    ORDER BY a.published_date DESC
                """, name=company_name)
            else:
                result = session.run("""
                    MATCH (c:Company)-[:FUNDED_BY]->(i:Investor)
                    OPTIONAL MATCH (c)-[:ANNOUNCED_AT]->(a:Article)

                    RETURN c.name as company, i.name as investor,
                           a.published_date as date, a.title as article_title
                    ORDER BY a.published_date DESC
                    LIMIT 50
                """)

            return [dict(record) for record in result]

    # =========================================================================
    # ANALYTICS QUERIES
    # =========================================================================

    def get_graph_statistics(self) -> Dict:
        """Get overall graph statistics"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                WITH labels(n)[0] as label, count(n) as count
                RETURN collect({label: label, count: count}) as node_counts
            """)

            node_stats = result.single()

            result = session.run("""
                MATCH ()-[r]->()
                WITH type(r) as rel_type, count(r) as count
                RETURN collect({type: rel_type, count: count}) as rel_counts
            """)

            rel_stats = result.single()

            result = session.run("""
                MATCH (n)
                WHERE n.community_id IS NOT NULL
                RETURN count(DISTINCT n.community_id) as community_count
            """)

            community_stats = result.single()

            return {
                "node_counts": node_stats["node_counts"] if node_stats else [],
                "relationship_counts": rel_stats["rel_counts"] if rel_stats else [],
                "community_count": community_stats["community_count"] if community_stats else 0
            }

    def get_most_connected_entities(self, limit: int = 10) -> List[Dict]:
        """Get entities with most relationships"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e)
                WHERE NOT e:Article
                OPTIONAL MATCH (e)-[r]-()
                WITH e, count(r) as degree
                WHERE degree > 0
                RETURN e.id as id, e.name as name, labels(e)[0] as type,
                       e.description as description, degree
                ORDER BY degree DESC
                LIMIT $limit
            """, limit=limit)

            return [dict(record) for record in result]

    def get_entity_importance_scores(self, limit: int = 20) -> List[Dict]:
        """
        Calculate entity importance using multiple metrics

        Importance = mention_count * 0.3 + relationship_count * 0.5 + article_count * 0.2
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e)
                WHERE NOT e:Article

                OPTIONAL MATCH (e)-[r]-()
                WITH e, count(DISTINCT r) as rel_count

                WITH e, rel_count,
                     coalesce(e.mention_count, 0) as mentions,
                     coalesce(e.article_count, 0) as articles,
                     (coalesce(e.mention_count, 0) * 0.3 +
                      rel_count * 0.5 +
                      coalesce(e.article_count, 0) * 0.2) as importance_score

                RETURN e.id as id, e.name as name, labels(e)[0] as type,
                       mentions, rel_count as relationships, articles,
                       round(importance_score, 2) as importance_score
                ORDER BY importance_score DESC
                LIMIT $limit
            """, limit=limit)

            return [dict(record) for record in result]

    # =========================================================================
    # TECHNOLOGY & TREND QUERIES
    # =========================================================================

    def get_technology_adoption(self, technology_keyword: str) -> Dict:
        """
        Get companies using a specific technology

        Args:
            technology_keyword: Technology name or keyword

        Returns:
            Technology adoption information
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Technology)
                WHERE toLower(t.name) CONTAINS toLower($keyword)

                OPTIONAL MATCH (c:Company)-[:USES_TECHNOLOGY]->(t)
                WITH t, collect(DISTINCT c.name) as companies, count(c) as adoption_count

                RETURN t.name as technology, t.description as description,
                       adoption_count, companies
                ORDER BY adoption_count DESC
                LIMIT 1
            """, keyword=technology_keyword)

            record = result.single()
            return dict(record) if record else {}

    def get_trending_technologies(self, limit: int = 10) -> List[Dict]:
        """Get most mentioned/used technologies"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Technology)
                OPTIONAL MATCH (c:Company)-[:USES_TECHNOLOGY]->(t)
                WITH t, count(c) as company_count
                RETURN t.id as id, t.name as name, t.description as description,
                       t.mention_count as mentions, company_count
                ORDER BY company_count DESC, t.mention_count DESC
                LIMIT $limit
            """, limit=limit)

            return [dict(record) for record in result]

    # =========================================================================
    # FULL-TEXT SEARCH
    # =========================================================================

    def search_entities_full_text(self, search_term: str, limit: int = 10) -> List[Dict]:
        """
        Search entities by name or description

        Args:
            search_term: Search term
            limit: Maximum results

        Returns:
            Matching entities
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e)
                WHERE (toLower(e.name) CONTAINS toLower($term)
                   OR toLower(e.description) CONTAINS toLower($term))
                   AND NOT e:Article
                RETURN e.id as id, e.name as name, labels(e)[0] as type,
                       e.description as description, e.mention_count as mention_count
                ORDER BY e.mention_count DESC
                LIMIT $limit
            """, term=search_term, limit=limit)

            return [dict(record) for record in result]
