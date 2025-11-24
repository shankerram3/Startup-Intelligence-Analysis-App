"""
Query Template Library - Pre-built Cypher Queries for GraphRAG
Provides common query patterns for knowledge graph exploration
"""

from typing import Any, Dict, List, Optional

from neo4j import Driver


class QueryTemplates:
    """Library of pre-built Cypher query templates"""

    def __init__(self, driver: Driver):
        self.driver = driver

    def _enrich_with_article_urls(
        self, entity_id: str, source_articles: Optional[List[str]] = None
    ) -> List[str]:
        """
        Helper method to get article URLs for an entity

        Args:
            entity_id: Entity ID
            source_articles: Optional list of article IDs (if already known)

        Returns:
            List of article URLs
        """
        if not source_articles:
            # Get source_articles from entity
            with self.driver.session() as session:
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
                return record["urls"] if record and record["urls"] else []
        else:
            # Use provided source_articles
            with self.driver.session() as session:
                result = session.run(
                    """
                    UNWIND $article_ids as article_id
                    MATCH (a:Article {id: article_id})
                    RETURN collect(DISTINCT a.url) as urls
                """,
                    article_ids=source_articles,
                )
                record = result.single()
                return record["urls"] if record and record["urls"] else []

    # =========================================================================
    # ENTITY QUERIES
    # =========================================================================

    def get_entity_by_name(
        self, entity_name: str, entity_type: Optional[str] = None
    ) -> Dict:
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
            result = session.run(
                """
                MATCH (e {id: $id})
                RETURN e.id as id, e.name as name, labels(e)[0] as type,
                       e.description as description, e.mention_count as mention_count,
                       e.source_articles as source_articles,
                       e.community_id as community_id
            """,
                id=entity_id,
            )

            record = result.single()
            return dict(record) if record else {}

    def search_entities_by_type(self, entity_type: str, limit: int = 10) -> List[Dict]:
        """Search entities by type"""
        with self.driver.session() as session:
            result = session.run(
                f"""
                MATCH (e:{entity_type})
                RETURN e.id as id, e.name as name, e.description as description,
                       e.mention_count as mention_count, e.source_articles as source_articles
                ORDER BY e.mention_count DESC
                LIMIT $limit
            """,
                limit=limit,
            )

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
            result = session.run(
                """
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
                
                // Collect article URLs from source_articles
                OPTIONAL MATCH (c)
                WHERE c.source_articles IS NOT NULL
                UNWIND c.source_articles as article_id
                MATCH (a:Article {id: article_id})
                WITH c, investors, founders, technologies, locations, competitors, collect(DISTINCT a.url) as article_urls

                RETURN c.id as id, c.name as name, c.description as description,
                       c.mention_count as mention_count,
                       investors, founders, technologies, locations, competitors,
                       COALESCE(article_urls, []) as article_urls
                LIMIT 1
            """,
                name=company_name,
            )

            record = result.single()
            return dict(record) if record else {}

    def get_companies_by_funding(self, min_investors: int = 1) -> List[Dict]:
        """Get companies by funding relationships"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (c:Company)-[:FUNDED_BY]->(i:Investor)
                WITH c, collect(DISTINCT i.name) as investors, count(DISTINCT i) as investor_count
                WHERE investor_count >= $min_investors AND c.source_articles IS NOT NULL
                
                // Collect article URLs from source_articles
                UNWIND c.source_articles as article_id
                MATCH (a:Article {id: article_id})
                WITH c, investors, investor_count, collect(DISTINCT a.url) as article_urls
                WHERE size(article_urls) > 0
                
                RETURN c.id as id, c.name as name, c.description as description,
                       investor_count, investors, article_urls
                ORDER BY investor_count DESC
                LIMIT 20
            """,
                min_investors=min_investors,
            )

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
            result = session.run(
                """
                MATCH (c:Company)
                WHERE toLower(c.description) CONTAINS toLower($keyword)

                OPTIONAL MATCH (c)-[:FUNDED_BY]->(i:Investor)
                WITH c, count(DISTINCT i) as investor_count, collect(DISTINCT i.name) as investors
                
                // Collect article URLs from source_articles if available
                OPTIONAL MATCH (c)
                WHERE c.source_articles IS NOT NULL
                UNWIND c.source_articles as article_id
                MATCH (a:Article {id: article_id})
                WITH c, investor_count, investors, collect(DISTINCT a.url) as article_urls

                RETURN c.id as id, c.name as name, c.description as description,
                       c.mention_count as mention_count, investor_count, 
                       investors, COALESCE(article_urls, []) as article_urls
                ORDER BY c.mention_count DESC
                LIMIT 20
            """,
                keyword=sector_keyword,
            )

            return [dict(record) for record in result]

    def get_recently_funded_companies(
        self, days: int = 90, sector_keyword: Optional[str] = None
    ) -> List[Dict]:
        """
        Get companies with recent funding announcements

        Args:
            days: Number of days to look back (default: 90)
            sector_keyword: Optional sector filter

        Returns:
            List of recently funded companies
        """
        with self.driver.session() as session:
            if sector_keyword:
                result = session.run(
                    """
                    MATCH (c:Company)-[:FUNDED_BY]->(i:Investor)
                    WHERE toLower(c.description) CONTAINS toLower($keyword)
                      AND c.source_articles IS NOT NULL

                    // Use source_articles property to find related articles
                    WITH c, collect(DISTINCT i.name) as investors, count(DISTINCT i) as investor_count
                    UNWIND c.source_articles as article_id
                    MATCH (a:Article {id: article_id})
                    WHERE a.published_date IS NOT NULL
                      AND datetime(a.published_date) > datetime() - duration({days: $days})

                    WITH c, investors, investor_count, max(a.published_date) as latest_announcement
                    WHERE investor_count > 0

                    // Collect article URLs from source_articles
                    UNWIND c.source_articles as article_id
                    MATCH (art:Article {id: article_id})
                    WHERE art.published_date IS NOT NULL
                      AND datetime(art.published_date) > datetime() - duration({days: $days})
                    WITH c, investors, investor_count, latest_announcement, collect(DISTINCT art.url) as article_urls
                    WHERE size(article_urls) > 0

                    RETURN c.id as id, c.name as name, c.description as description,
                           c.mention_count as mention_count,
                           investor_count, investors, latest_announcement, article_urls
                    ORDER BY latest_announcement DESC, investor_count DESC
                    LIMIT 20
                """,
                    keyword=sector_keyword,
                    days=days,
                )
            else:
                result = session.run(
                    """
                    MATCH (c:Company)-[:FUNDED_BY]->(i:Investor)
                    WHERE c.source_articles IS NOT NULL
                    
                    // Use source_articles property to find related articles
                    WITH c, collect(DISTINCT i.name) as investors, count(DISTINCT i) as investor_count
                    UNWIND c.source_articles as article_id
                    MATCH (a:Article {id: article_id})
                    WHERE a.published_date IS NOT NULL
                      AND datetime(a.published_date) > datetime() - duration({days: $days})

                    WITH c, investors, investor_count, max(a.published_date) as latest_announcement
                    WHERE investor_count > 0

                    // Collect article URLs from source_articles
                    UNWIND c.source_articles as article_id
                    MATCH (art:Article {id: article_id})
                    WHERE art.published_date IS NOT NULL
                      AND datetime(art.published_date) > datetime() - duration({days: $days})
                    WITH c, investors, investor_count, latest_announcement, collect(DISTINCT art.url) as article_urls
                    WHERE size(article_urls) > 0

                    RETURN c.id as id, c.name as name, c.description as description,
                           c.mention_count as mention_count,
                           investor_count, investors, latest_announcement, article_urls
                    ORDER BY latest_announcement DESC, investor_count DESC
                    LIMIT 20
                """,
                    days=days,
                )

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
            result = session.run(
                """
                MATCH (i:Investor)
                WHERE toLower(i.name) CONTAINS toLower($name)

                OPTIONAL MATCH (c:Company)-[:FUNDED_BY]->(i)
                WITH i, collect(DISTINCT {
                    name: c.name,
                    description: c.description,
                    mention_count: c.mention_count
                }) as portfolio
                
                // Get article URLs from source_articles if available
                OPTIONAL MATCH (i)
                WHERE i.source_articles IS NOT NULL
                UNWIND i.source_articles as article_id
                MATCH (a:Article {id: article_id})
                WITH i, portfolio, collect(DISTINCT a.url) as article_urls

                RETURN i.id as id, i.name as name, i.description as description,
                       size(portfolio) as portfolio_size, portfolio,
                       COALESCE(article_urls, []) as article_urls
                LIMIT 1
            """,
                name=investor_name,
            )

            record = result.single()
            return dict(record) if record else {}

    def get_top_investors(self, limit: int = 10) -> List[Dict]:
        """Get most active investors by portfolio size"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (i:Investor)<-[:FUNDED_BY]-(c:Company)
                WITH i, count(DISTINCT c) as portfolio_size,
                     collect(DISTINCT c.name) as companies
                RETURN i.id as id, i.name as name, i.description as description,
                       portfolio_size, companies
                ORDER BY portfolio_size DESC
                LIMIT $limit
            """,
                limit=limit,
            )

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
            result = session.run(
                """
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
            """,
                name=person_name,
            )

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
            result = session.run(
                f"""
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
            """,
                id=entity_id,
            )

            record = result.single()
            return dict(record) if record else {}

    def find_connection_path(
        self, entity1_name: str, entity2_name: str, max_hops: int = 4
    ) -> List[Dict]:
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
            result = session.run(
                """
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
            """
                % max_hops,
                name1=entity1_name,
                name2=entity2_name,
            )

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
            result = session.run(
                """
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
                
                // Collect article URLs from source_articles
                OPTIONAL MATCH (c)
                WHERE c.source_articles IS NOT NULL
                UNWIND c.source_articles as article_id
                MATCH (a:Article {id: article_id})
                WITH c, direct_competitors, similar_companies, companies_with_shared_investors,
                     collect(DISTINCT a.url) as article_urls

                RETURN c.id as id, c.name as company, c.description as description,
                       direct_competitors, similar_companies,
                       companies_with_shared_investors,
                       COALESCE(article_urls, []) as article_urls
                LIMIT 1
            """,
                name=company_name,
            )

            record = result.single()
            return dict(record) if record else {}

    # =========================================================================
    # COMMUNITY QUERIES
    # =========================================================================

    def get_communities(self, min_size: int = 3, limit: int = 50) -> List[Dict]:
        """Get all detected communities"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e)
                WHERE e.community_id IS NOT NULL AND NOT e:Article
                WITH e.community_id as community_id,
                     collect({name: e.name, type: labels(e)[0]}) as members,
                     count(e) as size
                WHERE size >= $min_size
                RETURN community_id, size, members
                ORDER BY size DESC
                LIMIT $limit
            """,
                min_size=min_size,
                limit=limit,
            )

            return [dict(record) for record in result]

    def get_community_by_id(self, community_id: int) -> Dict:
        """Get detailed information about a specific community"""
        with self.driver.session() as session:
            result = session.run(
                """
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
            """,
                community_id=community_id,
            )

            record = result.single()
            return dict(record) if record else {}

    def get_community_statistics(self) -> Dict:
        """Get comprehensive community statistics"""
        try:
            with self.driver.session() as session:
                # Total communities
                result = session.run(
                    """
                    MATCH (e)
                    WHERE e.community_id IS NOT NULL AND NOT e:Article
                    WITH DISTINCT e.community_id as cid
                    RETURN count(cid) as total_communities
                """
                )
                record = result.single()
                total = record.get("total_communities", 0) if record else 0

                # Community size distribution
                result = session.run(
                    """
                    MATCH (e)
                    WHERE e.community_id IS NOT NULL AND NOT e:Article
                    WITH e.community_id as cid, count(e) as size
                    RETURN 
                        min(size) as min_size,
                        max(size) as max_size,
                        avg(size) as avg_size,
                        percentileCont(size, 0.5) as median_size
                """
                )
                record = result.single()
                size_stats = record if record else {}

                # Entities in communities
                result = session.run(
                    """
                    MATCH (e)
                    WHERE e.community_id IS NOT NULL AND NOT e:Article
                    RETURN count(e) as entities_in_communities
                """
                )
                record = result.single()
                entities_in_communities = (
                    record.get("entities_in_communities", 0) if record else 0
                )

                # Total entities
                result = session.run(
                    """
                    MATCH (e)
                    WHERE NOT e:Article
                    RETURN count(e) as total_entities
                """
                )
                record = result.single()
                total_entities = record.get("total_entities", 0) if record else 0

                return {
                    "total_communities": total,
                    "total_entities": total_entities,
                    "entities_in_communities": entities_in_communities,
                    "coverage_percentage": round(
                        (
                            (entities_in_communities / total_entities * 100)
                            if total_entities > 0
                            else 0
                        ),
                        2,
                    ),
                    "size_distribution": {
                        "min": (
                            int(size_stats.get("min_size", 0))
                            if size_stats.get("min_size") is not None
                            else 0
                        ),
                        "max": (
                            int(size_stats.get("max_size", 0))
                            if size_stats.get("max_size") is not None
                            else 0
                        ),
                        "avg": (
                            round(float(size_stats.get("avg_size", 0)), 2)
                            if size_stats.get("avg_size") is not None
                            else 0
                        ),
                        "median": (
                            round(float(size_stats.get("median_size", 0)), 2)
                            if size_stats.get("median_size") is not None
                            else 0
                        ),
                    },
                }
        except Exception as e:
            # Log the error and return default values
            import traceback

            print(f"Error in get_community_statistics: {e}")
            print(traceback.format_exc())
            return {
                "total_communities": 0,
                "total_entities": 0,
                "entities_in_communities": 0,
                "coverage_percentage": 0,
                "size_distribution": {"min": 0, "max": 0, "avg": 0, "median": 0},
            }

    def get_community_graph_data(
        self,
        community_id: Optional[int] = None,
        max_nodes: int = 200,
        max_communities: int = 10,
    ) -> Dict:
        """Get community graph data formatted for visualization"""
        try:
            with self.driver.session() as session:
                if community_id is not None:
                    # Get specific community - two-step approach
                    # First get nodes
                    node_query = """
                    MATCH (e)
                    WHERE e.community_id = $community_id AND NOT e:Article
                    WITH e
                    LIMIT $max_nodes
                    RETURN collect({
                        id: e.id,
                        label: coalesce(e.name, 'Unknown'),
                        type: labels(e)[0],
                        community_id: e.community_id,
                        title: coalesce(e.name, 'Unknown') + ' (' + labels(e)[0] + ')'
                    }) as nodes
                    """
                    node_result = session.run(
                        node_query, community_id=community_id, max_nodes=max_nodes
                    )
                    node_record = node_result.single()
                    nodes = node_record.get("nodes", []) if node_record else []

                    if not nodes:
                        return {
                            "nodes": [],
                            "edges": [],
                            "communities": [],
                            "node_count": 0,
                            "edge_count": 0,
                        }

                    # Get node IDs
                    node_ids = [n["id"] for n in nodes]

                    # Then get edges
                    edge_query = """
                    MATCH (e1)-[r]->(e2)
                    WHERE e1.community_id = $community_id 
                      AND e2.community_id = $community_id
                      AND NOT e1:Article AND NOT e2:Article
                      AND e1.id IN $node_ids
                      AND e2.id IN $node_ids
                    RETURN collect(DISTINCT {
                        from: e1.id,
                        to: e2.id,
                        type: type(r),
                        label: type(r)
                    }) as edges
                    """
                    edge_result = session.run(
                        edge_query, community_id=community_id, node_ids=node_ids
                    )
                    edge_record = edge_result.single()
                    edges = edge_record.get("edges", []) if edge_record else []

                    community_ids = [community_id] if community_id else []
                    return {
                        "nodes": nodes,
                        "edges": edges,
                        "communities": community_ids,
                        "node_count": len(nodes),
                        "edge_count": len(edges),
                    }
                else:
                    # Get top communities by size - two-step approach
                    # First get top community IDs
                    comm_query = """
                    MATCH (e)
                    WHERE e.community_id IS NOT NULL AND NOT e:Article
                    WITH e.community_id as cid, count(e) as size
                    ORDER BY size DESC
                    LIMIT $max_communities
                    RETURN collect(cid) as top_communities
                    """
                    comm_result = session.run(
                        comm_query, max_communities=max_communities
                    )
                    comm_record = comm_result.single()
                    top_communities = (
                        comm_record.get("top_communities", []) if comm_record else []
                    )

                    if not top_communities:
                        return {
                            "nodes": [],
                            "edges": [],
                            "communities": [],
                            "node_count": 0,
                            "edge_count": 0,
                        }

                    # Get nodes from top communities
                    node_query = """
                    MATCH (e)
                    WHERE e.community_id IN $top_communities AND NOT e:Article
                    WITH e
                    LIMIT $max_nodes
                    RETURN collect({
                        id: e.id,
                        label: coalesce(e.name, 'Unknown'),
                        type: labels(e)[0],
                        community_id: e.community_id,
                        title: coalesce(e.name, 'Unknown') + ' (' + labels(e)[0] + ')'
                    }) as nodes
                    """
                    node_result = session.run(
                        node_query, top_communities=top_communities, max_nodes=max_nodes
                    )
                    node_record = node_result.single()
                    nodes = node_record.get("nodes", []) if node_record else []

                    if not nodes:
                        return {
                            "nodes": [],
                            "edges": [],
                            "communities": top_communities,
                            "node_count": 0,
                            "edge_count": 0,
                        }

                    # Get node IDs
                    node_ids = [n["id"] for n in nodes]

                    # Get edges
                    edge_query = """
                    MATCH (e1)-[r]->(e2)
                    WHERE e1.community_id IN $top_communities
                      AND e2.community_id IN $top_communities
                      AND NOT e1:Article AND NOT e2:Article
                      AND e1.id IN $node_ids
                      AND e2.id IN $node_ids
                    RETURN collect(DISTINCT {
                        from: e1.id,
                        to: e2.id,
                        type: type(r),
                        label: type(r)
                    }) as edges
                    """
                    edge_result = session.run(
                        edge_query, top_communities=top_communities, node_ids=node_ids
                    )
                    edge_record = edge_result.single()
                    edges = edge_record.get("edges", []) if edge_record else []

                    return {
                        "nodes": nodes,
                        "edges": edges,
                        "communities": top_communities,
                        "node_count": len(nodes),
                        "edge_count": len(edges),
                    }
        except Exception as e:
            # Log the error and return empty result
            import traceback

            print(f"Error in get_community_graph_data: {e}")
            print(traceback.format_exc())
            return {
                "nodes": [],
                "edges": [],
                "communities": [],
                "node_count": 0,
                "edge_count": 0,
            }

    # =========================================================================
    # THEME EXTRACTION QUERIES
    # =========================================================================

    def get_recurring_themes(
        self,
        min_frequency: int = 3,
        limit: int = 20,
        time_window_days: Optional[int] = None,
    ) -> List[Dict]:
        """
        Extract recurring themes from the graph based on:
        - Common entity co-occurrences
        - Relationship patterns
        - Community clusters
        - Technology/industry trends
        """
        with self.driver.session() as session:
            themes = []

            # Theme 1: Common relationship patterns - USES_TECHNOLOGY (works with any node types)
            tech_query = """
                MATCH (source)-[:USES_TECHNOLOGY]->(target)
                WHERE NOT source:Article AND NOT target:Article
                WITH target.name as tech_name, 
                     labels(target)[0] as target_type,
                     count(DISTINCT source) as company_count, 
                     collect(DISTINCT source.name)[0..5] as sample_companies
                WHERE company_count >= $min_frequency
                RETURN {
                    theme: tech_name + ' Adoption',
                    type: 'technology_trend',
                    frequency: company_count,
                    description: tech_name + ' is used by ' + toString(company_count) + ' entities',
                    entities: sample_companies,
                    strength: company_count
                } as theme
                ORDER BY company_count DESC
                LIMIT $limit
            """

            # Theme 2: Common funding patterns
            funding_query = """
                MATCH (c)-[:FUNDED_BY]->(i)
                WHERE NOT c:Article AND NOT i:Article
                WITH i.name as investor_name, count(DISTINCT c) as portfolio_size,
                     collect(DISTINCT c.name)[0..5] as sample_companies
                WHERE portfolio_size >= $min_frequency
                RETURN {
                    theme: investor_name + ' Portfolio',
                    type: 'funding_pattern',
                    frequency: portfolio_size,
                    description: investor_name + ' has invested in ' + toString(portfolio_size) + ' companies',
                    entities: sample_companies,
                    strength: portfolio_size
                } as theme
                ORDER BY portfolio_size DESC
                LIMIT $limit
            """

            # Theme 3: Most mentioned entities (general popularity)
            popular_entities_query = """
                MATCH (e)
                WHERE NOT e:Article 
                  AND e.mention_count IS NOT NULL
                  AND e.mention_count >= $min_frequency
                WITH e, labels(e)[0] as entity_type
                RETURN {
                    theme: e.name + ' (Popular ' + entity_type + ')',
                    type: 'industry_cluster',
                    frequency: e.mention_count,
                    description: e.name + ' is mentioned ' + toString(e.mention_count) + ' times',
                    entities: [e.name],
                    strength: e.mention_count
                } as theme
                ORDER BY e.mention_count DESC
                LIMIT $limit
            """

            # Theme 4: Common relationship types (any relationship pattern)
            relationship_pattern_query = """
                MATCH (e1)-[r]->(e2)
                WHERE NOT e1:Article AND NOT e2:Article
                WITH type(r) as rel_type, count(r) as rel_count,
                     collect(DISTINCT e1.name + ' → ' + e2.name)[0..5] as sample_pairs
                WHERE rel_count >= $min_frequency
                RETURN {
                    theme: rel_type + ' Relationships',
                    type: 'partnership_pattern',
                    frequency: rel_count,
                    description: rel_type + ' relationship appears ' + toString(rel_count) + ' times',
                    entities: sample_pairs,
                    strength: rel_count
                } as theme
                ORDER BY rel_count DESC
                LIMIT $limit
            """

            # Theme 5: Community-based themes
            community_theme_query = """
                MATCH (e)
                WHERE NOT e:Article 
                  AND e.community_id IS NOT NULL
                WITH e.community_id as comm_id, 
                     count(e) as community_size,
                     collect(DISTINCT e.name)[0..5] as sample_entities
                WHERE community_size >= $min_frequency
                RETURN {
                    theme: 'Community ' + toString(comm_id) + ' Cluster',
                    type: 'industry_cluster',
                    frequency: community_size,
                    description: 'Community ' + toString(comm_id) + ' contains ' + toString(community_size) + ' entities',
                    entities: sample_entities,
                    strength: community_size
                } as theme
                ORDER BY community_size DESC
                LIMIT $limit
            """

            # Theme 6: Common co-occurrence patterns (entities mentioned together in articles)
            # Using source_articles property instead of MENTIONED_IN relationships
            cooccurrence_query = """
                MATCH (e1), (e2)
                WHERE NOT e1:Article AND NOT e2:Article 
                  AND e1.id < e2.id
                  AND e1.source_articles IS NOT NULL
                  AND e2.source_articles IS NOT NULL
                WITH e1, e2, 
                     [article_id IN e1.source_articles WHERE article_id IN e2.source_articles] as common_articles
                WHERE size(common_articles) >= $min_frequency
                RETURN {
                    theme: e1.name + ' & ' + e2.name + ' Co-occurrence',
                    type: 'partnership_pattern',
                    frequency: size(common_articles),
                    description: e1.name + ' & ' + e2.name + ' appear together in ' + toString(size(common_articles)) + ' articles',
                    entities: [e1.name, e2.name],
                    strength: size(common_articles)
                } as theme
                ORDER BY size(common_articles) DESC
                LIMIT $limit
            """

            # Execute all queries and combine results
            queries = [
                tech_query,
                funding_query,
                popular_entities_query,
                relationship_pattern_query,
                community_theme_query,
                cooccurrence_query,
            ]

            for query in queries:
                try:
                    result = session.run(
                        query, min_frequency=min_frequency, limit=limit
                    )
                    for record in result:
                        theme = record.get("theme")
                        if theme:
                            themes.append(theme)
                except Exception as e:
                    # Skip queries that fail (e.g., if certain node types or relationships don't exist)
                    import traceback

                    print(f"Query failed: {e}")
                    print(traceback.format_exc())
                    continue

            # Sort by strength and return top themes
            themes.sort(key=lambda x: x.get("strength", 0), reverse=True)
            return themes[:limit]

    def get_theme_details(self, theme_name: str, theme_type: str) -> Dict:
        """
        Get detailed information about a specific theme
        """
        with self.driver.session() as session:
            if theme_type == "technology_trend":
                # Extract technology name from theme (handle various formats)
                tech_name = theme_name.replace(" Adoption", "").strip()

                # Try case-insensitive matching
                query = """
                    MATCH (source)-[:USES_TECHNOLOGY]->(target)
                    WHERE toLower(target.name) = toLower($tech_name) 
                      AND NOT source:Article AND NOT target:Article
                    WITH target.name as tech_name, source
                    OPTIONAL MATCH (source)-[:FUNDED_BY]->(i)
                    WHERE NOT i:Article
                    WITH tech_name, source, collect(DISTINCT i.name) as investors
                    WITH tech_name, collect({
                        name: source.name,
                        description: source.description,
                        investors: investors
                    }) as companies
                    RETURN {
                        technology: tech_name,
                        companies: companies,
                        total_companies: size(companies)
                    } as details
                """
                result = session.run(query, tech_name=tech_name)
                record = result.single()
                if record and record.get("details"):
                    return record.get("details", {})

                # If no exact match, try partial match
                query_fuzzy = """
                    MATCH (source)-[:USES_TECHNOLOGY]->(target)
                    WHERE toLower(target.name) CONTAINS toLower($tech_name)
                      AND NOT source:Article AND NOT target:Article
                    WITH target.name as tech_name, source
                    LIMIT 1
                    OPTIONAL MATCH (source)-[:FUNDED_BY]->(i)
                    WHERE NOT i:Article
                    WITH tech_name, source, collect(DISTINCT i.name) as investors
                    WITH tech_name, collect({
                        name: source.name,
                        description: source.description,
                        investors: investors
                    }) as companies
                    RETURN {
                        technology: tech_name,
                        companies: companies,
                        total_companies: size(companies)
                    } as details
                """
                result = session.run(query_fuzzy, tech_name=tech_name)
                record = result.single()
                return record.get("details", {}) if record else {}

            elif theme_type == "funding_pattern":
                # Extract investor name from theme (e.g., "Investor Portfolio")
                investor_name = theme_name.replace(" Portfolio", "").strip()
                query = """
                    MATCH (c)-[:FUNDED_BY]->(i)
                    WHERE toLower(i.name) = toLower($investor_name)
                      AND NOT c:Article AND NOT i:Article
                    WITH i.name as investor_name, c
                    RETURN {
                        investor: investor_name,
                        companies: collect({
                            name: c.name,
                            description: c.description
                        }),
                        total_companies: count(DISTINCT c)
                    } as details
                """
                result = session.run(query, investor_name=investor_name)
                record = result.single()
                return record.get("details", {}) if record else {}

            elif theme_type == "partnership_pattern":
                # For partnership patterns, return relationship information
                query = """
                    MATCH (e1)-[r:PARTNERS_WITH]->(e2)
                    WHERE NOT e1:Article AND NOT e2:Article
                    WITH e1, e2, r
                    LIMIT 50
                    RETURN {
                        partnerships: collect({
                            from: e1.name,
                            to: e2.name,
                            type: type(r)
                        }),
                        total_partnerships: count(r)
                    } as details
                """
                result = session.run(query)
                record = result.single()
                return record.get("details", {}) if record else {}

            elif theme_type == "industry_cluster":
                # Handle community-based themes (format: "Community X Cluster")
                if theme_name.startswith("Community ") and theme_name.endswith(" Cluster"):
                    # Extract community ID from theme name (e.g., "Community 2 Cluster" -> 2)
                    try:
                        comm_id_str = theme_name.replace("Community ", "").replace(" Cluster", "").strip()
                        comm_id = int(comm_id_str)
                        query = """
                            MATCH (e)
                            WHERE NOT e:Article 
                              AND e.community_id = $comm_id
                            WITH e
                            OPTIONAL MATCH (e)-[r]->(related)
                            WHERE NOT related:Article
                            WITH e, collect(DISTINCT {
                                name: related.name,
                                type: labels(related)[0],
                                relationship: type(r)
                            })[0..20] as relationships
                            WITH collect({
                                name: e.name,
                                type: labels(e)[0],
                                description: e.description,
                                mention_count: e.mention_count
                            }) as entities, relationships
                            UNWIND relationships as rel
                            WITH entities, collect(DISTINCT rel) as all_relationships
                            RETURN {
                                community_id: $comm_id,
                                entities: entities,
                                total_entities: size(entities),
                                relationships: all_relationships,
                                description: 'Community ' + toString($comm_id) + ' contains ' + toString(size(entities)) + ' entities'
                            } as details
                        """
                        result = session.run(query, comm_id=comm_id)
                        record = result.single()
                        if record and record.get("details"):
                            return record.get("details", {})
                    except (ValueError, TypeError):
                        # If community ID extraction fails, fall through to other handlers
                        pass
                
                # For industry clusters, try to extract the keyword
                # Theme format might be "Industry: keyword" or "Entity Name (Popular Type)"
                if theme_name.startswith("Industry: "):
                    keyword = theme_name.replace("Industry: ", "").strip()
                    query = """
                        MATCH (c)
                        WHERE NOT c:Article 
                          AND c.description IS NOT NULL
                          AND toLower(c.description) CONTAINS toLower($keyword)
                        RETURN {
                            keyword: $keyword,
                            companies: collect({
                                name: c.name,
                                description: c.description
                            })[0..20],
                            total_companies: count(DISTINCT c)
                        } as details
                    """
                    result = session.run(query, keyword=keyword)
                    record = result.single()
                    return record.get("details", {}) if record else {}
                else:
                    # Try to find entity by name (for "Popular Entity" themes)
                    entity_name = theme_name.split(" (Popular")[0].strip()
                    query = """
                        MATCH (e)
                        WHERE toLower(e.name) = toLower($entity_name)
                          AND NOT e:Article
                        OPTIONAL MATCH (e)-[r]->(related)
                        WHERE NOT related:Article
                        WITH e, collect({
                            name: related.name,
                            relationship: type(r)
                        })[0..10] as relationships
                        RETURN {
                            entity: e.name,
                            description: e.description,
                            mention_count: e.mention_count,
                            relationships: relationships
                        } as details
                    """
                    result = session.run(query, entity_name=entity_name)
                    record = result.single()
                    return record.get("details", {}) if record else {}

            # Default: return basic theme info
            return {
                "theme_name": theme_name,
                "theme_type": theme_type,
                "message": "Details not yet implemented for this theme type",
            }

    # =========================================================================
    # TEMPORAL QUERIES
    # =========================================================================

    def get_recent_entities(self, days: int = 30, limit: int = 10) -> List[Dict]:
        """Get recently mentioned entities"""
        with self.driver.session() as session:
            cutoff_timestamp = (
                days * 24 * 60 * 60 * 1000
            )  # Convert days to milliseconds

            result = session.run(
                """
                MATCH (e)
                WHERE e.last_mentioned IS NOT NULL
                  AND e.last_mentioned > timestamp() - $cutoff
                  AND NOT e:Article
                RETURN e.id as id, e.name as name, labels(e)[0] as type,
                       e.description as description,
                       e.last_mentioned as last_mentioned
                ORDER BY e.last_mentioned DESC
                LIMIT $limit
            """,
                cutoff=cutoff_timestamp,
                limit=limit,
            )

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
                result = session.run(
                    """
                    MATCH (c:Company)-[:FUNDED_BY]->(i:Investor)
                    WHERE toLower(c.name) CONTAINS toLower($name)

                    OPTIONAL MATCH (c)-[:ANNOUNCED_AT]->(a:Article)

                    RETURN c.name as company, i.name as investor,
                           a.published_date as date, a.title as article_title
                    ORDER BY a.published_date DESC
                """,
                    name=company_name,
                )
            else:
                result = session.run(
                    """
                    MATCH (c:Company)-[:FUNDED_BY]->(i:Investor)
                    OPTIONAL MATCH (c)-[:ANNOUNCED_AT]->(a:Article)

                    RETURN c.name as company, i.name as investor,
                           a.published_date as date, a.title as article_title
                    ORDER BY a.published_date DESC
                    LIMIT 50
                """
                )

            return [dict(record) for record in result]

    # =========================================================================
    # ANALYTICS QUERIES
    # =========================================================================

    def get_graph_statistics(self) -> Dict:
        """Get overall graph statistics"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (n)
                WITH labels(n)[0] as label, count(n) as count
                RETURN collect({label: label, count: count}) as node_counts
            """
            )

            node_stats = result.single()

            result = session.run(
                """
                MATCH ()-[r]->()
                WITH type(r) as rel_type, count(r) as count
                RETURN collect({type: rel_type, count: count}) as rel_counts
            """
            )

            rel_stats = result.single()

            result = session.run(
                """
                MATCH (n)
                WHERE n.community_id IS NOT NULL
                RETURN count(DISTINCT n.community_id) as community_count
            """
            )

            community_stats = result.single()

            return {
                "node_counts": node_stats["node_counts"] if node_stats else [],
                "relationship_counts": rel_stats["rel_counts"] if rel_stats else [],
                "community_count": (
                    community_stats["community_count"] if community_stats else 0
                ),
            }

    def get_most_connected_entities(self, limit: int = 10) -> List[Dict]:
        """Get entities with most relationships"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e)
                WHERE NOT e:Article
                OPTIONAL MATCH (e)-[r]-()
                WITH e, count(r) as degree
                WHERE degree > 0
                RETURN e.id as id, e.name as name, labels(e)[0] as type,
                       e.description as description, degree
                ORDER BY degree DESC
                LIMIT $limit
            """,
                limit=limit,
            )

            return [dict(record) for record in result]

    def get_entity_importance_scores(self, limit: int = 20) -> List[Dict]:
        """
        Calculate entity importance using multiple metrics

        Importance = mention_count * 0.3 + relationship_count * 0.5 + article_count * 0.2
        """
        with self.driver.session() as session:
            result = session.run(
                """
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
            """,
                limit=limit,
            )

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
            result = session.run(
                """
                MATCH (t:Technology)
                WHERE toLower(t.name) CONTAINS toLower($keyword)

                OPTIONAL MATCH (c:Company)-[:USES_TECHNOLOGY]->(t)
                WITH t, collect(DISTINCT c.name) as companies, count(c) as adoption_count

                RETURN t.name as technology, t.description as description,
                       adoption_count, companies
                ORDER BY adoption_count DESC
                LIMIT 1
            """,
                keyword=technology_keyword,
            )

            record = result.single()
            return dict(record) if record else {}

    def get_trending_technologies(self, limit: int = 10) -> List[Dict]:
        """Get most mentioned/used technologies"""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (t:Technology)
                OPTIONAL MATCH (c:Company)-[:USES_TECHNOLOGY]->(t)
                WITH t, count(c) as company_count
                RETURN t.id as id, t.name as name, t.description as description,
                       t.mention_count as mentions, company_count
                ORDER BY company_count DESC, t.mention_count DESC
                LIMIT $limit
            """,
                limit=limit,
            )

            return [dict(record) for record in result]

    # =========================================================================
    # FULL-TEXT SEARCH
    # =========================================================================

    def search_entities_full_text(
        self, search_term: str, limit: int = 10
    ) -> List[Dict]:
        """
        Search entities by name or description

        Args:
            search_term: Search term
            limit: Maximum results

        Returns:
            Matching entities
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e)
                WHERE (toLower(e.name) CONTAINS toLower($term)
                   OR toLower(e.description) CONTAINS toLower($term))
                   AND NOT e:Article
                RETURN e.id as id, e.name as name, labels(e)[0] as type,
                       e.description as description, e.mention_count as mention_count
                ORDER BY e.mention_count DESC
                LIMIT $limit
            """,
                term=search_term,
                limit=limit,
            )

            return [dict(record) for record in result]
