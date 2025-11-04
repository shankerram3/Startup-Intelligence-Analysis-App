// ============================================================================
// Neo4j Knowledge Graph - Exploration Queries
// ============================================================================
// Run these queries in Neo4j Browser (http://localhost:7474)
// ============================================================================

// ----------------------------------------------------------------------------
// 1. SEE ENTIRE GRAPH (Limited to prevent browser overload)
// ----------------------------------------------------------------------------

// View entire graph with all nodes and relationships (limit to 500 nodes)
MATCH (n)-[r]-(m)
RETURN n, r, m
LIMIT 500;

// ----------------------------------------------------------------------------
// 2. SEE ENTIRE GRAPH BY TYPE (Better for large graphs)
// ----------------------------------------------------------------------------

// View all nodes and relationships, organized by type
MATCH path = (n)-[r]->(m)
RETURN n, r, m, 
       labels(n) as node_labels,
       type(r) as relationship_type,
       labels(m) as target_labels
LIMIT 500;

// ----------------------------------------------------------------------------
// 3. STATISTICS FIRST (Recommended before viewing entire graph)
// ----------------------------------------------------------------------------

// Get total counts
MATCH (n)
RETURN count(n) as total_nodes;

MATCH ()-[r]->()
RETURN count(r) as total_relationships;

// Get breakdown by node type
MATCH (n)
RETURN labels(n)[0] as node_type, count(n) as count
ORDER BY count DESC;

// Get breakdown by relationship type
MATCH ()-[r]->()
RETURN type(r) as relationship_type, count(r) as count
ORDER BY count DESC;

// ----------------------------------------------------------------------------
// 4. VIEW GRAPH BY ENTITY TYPE
// ----------------------------------------------------------------------------

// View all Companies and their relationships
MATCH path = (c:Company)-[r]-(related)
RETURN c, r, related
LIMIT 100;

// View all People and their relationships
MATCH path = (p:Person)-[r]-(related)
RETURN p, r, related
LIMIT 100;

// View all Articles (with their connections)
MATCH path = (a:Article)<-[r]-(entity)
RETURN a, r, entity
LIMIT 100;

// ----------------------------------------------------------------------------
// 5. VIEW CONNECTED COMPONENTS (Most connected entities)
// ----------------------------------------------------------------------------

// Find most connected nodes (degree centrality)
MATCH (n)-[r]-()
RETURN n, 
       labels(n)[0] as type,
       count(r) as connections
ORDER BY connections DESC
LIMIT 50;

// View a highly connected node and its neighbors
MATCH (n)-[r]-(related)
WHERE n.name IS NOT NULL
WITH n, count(r) as connections, collect(DISTINCT related)[0..10] as neighbors
ORDER BY connections DESC
LIMIT 1
RETURN n, neighbors;

// ----------------------------------------------------------------------------
// 6. VIEW SPECIFIC RELATIONSHIP PATTERNS
// ----------------------------------------------------------------------------

// Funding relationships
MATCH path = (company)-[:FUNDED_BY]->(investor)
RETURN company, investor
LIMIT 50;

// Founding relationships
MATCH path = (company)-[:FOUNDED_BY]->(person)
RETURN company, person
LIMIT 50;

// Competition relationships
MATCH path = (entity1)-[:COMPETES_WITH]->(entity2)
RETURN entity1, entity2
LIMIT 50;

// Technology usage
MATCH path = (entity)-[:USES_TECHNOLOGY]->(tech)
RETURN entity, tech
LIMIT 50;

// ----------------------------------------------------------------------------
// 7. INTERACTIVE EXPLORATION (Start from a specific entity)
// ----------------------------------------------------------------------------

// Find an entity by name
MATCH (n)
WHERE n.name CONTAINS 'OpenAI' OR n.name CONTAINS 'ANTHROPIC'
RETURN n, labels(n) as type
LIMIT 20;

// Explore 2-hop neighborhood from a specific entity
MATCH path = (start)-[*1..2]-(connected)
WHERE start.name = 'ANTHROPIC' OR start.name CONTAINS 'ANTHROPIC'
RETURN path
LIMIT 100;

// Explore entire neighborhood from a specific entity (3 hops)
MATCH path = (start)-[*1..3]-(connected)
WHERE start.name CONTAINS 'OPENAI'
RETURN path
LIMIT 200;

// ----------------------------------------------------------------------------
// 8. SUMMARY VIEW (High-level overview)
// ----------------------------------------------------------------------------

// View all entity types with sample nodes
MATCH (n)
WITH labels(n)[0] as type, collect(n)[0..5] as sample_nodes, count(n) as total
RETURN type, total, sample_nodes;

// View relationship types with examples
MATCH ()-[r]->()
WITH type(r) as rel_type, collect(r)[0..3] as sample_rels, count(r) as total
RETURN rel_type, total, sample_rels;

// ----------------------------------------------------------------------------
// 9. GRAPH PATTERN VISUALIZATIONS
// ----------------------------------------------------------------------------

// Company funding chain
MATCH path = (company:Company)-[:FUNDED_BY]->(investor)-[:FUNDED_BY*0..2]->(parent_investor)
RETURN path
LIMIT 50;

// Company ecosystem (company, founders, products, investors)
MATCH path = (company:Company)-[:FOUNDED_BY]->(founder:Person),
      (company)-[:FUNDED_BY]->(investor:Investor),
      (company)-[:USES_TECHNOLOGY]->(product:Product)
RETURN path
LIMIT 50;

// ----------------------------------------------------------------------------
// 10. FORCE-DIRECTED LAYOUT (Better visualization)
// ----------------------------------------------------------------------------

// View graph with force-directed layout (Neo4j Browser will handle this)
// Use this query and let Neo4j Browser auto-layout
MATCH (n)-[r]-(m)
WHERE n:Company OR n:Person OR n:Investor
RETURN n, r, m
LIMIT 200;

// ----------------------------------------------------------------------------
// 11. GRAPH EXPORT (For external visualization tools)
// ----------------------------------------------------------------------------

// Export nodes
MATCH (n)
RETURN labels(n)[0] as type, 
       id(n) as id, 
       n.name as name, 
       n.id as entity_id,
       n.description as description,
       n.article_count as article_count;

// Export relationships
MATCH (a)-[r]->(b)
RETURN id(a) as source_id,
       labels(a)[0] as source_type,
       a.name as source_name,
       type(r) as relationship_type,
       r.description as rel_description,
       id(b) as target_id,
       labels(b)[0] as target_type,
       b.name as target_name;

// ----------------------------------------------------------------------------
// 12. CUSTOM EXPLORATION QUERIES
// ----------------------------------------------------------------------------

// Find all entities connected to articles
MATCH (article:Article)<-[:MENTIONED_IN]-(entity)
RETURN article.title, collect(entity.name)[0..10] as entities
LIMIT 20;

// Find entities mentioned in most articles
MATCH (entity)
WHERE entity.article_count IS NOT NULL
RETURN entity.name, entity.article_count, labels(entity)[0] as type
ORDER BY entity.article_count DESC
LIMIT 20;

// Find articles that mention the most entities
MATCH (article:Article)
WHERE article.id IS NOT NULL
OPTIONAL MATCH (entity)-[:MENTIONED_IN]->(article)
WITH article, count(entity) as entity_count
ORDER BY entity_count DESC
RETURN article.title, article.id, entity_count
LIMIT 20;

// ----------------------------------------------------------------------------
// NOTES:
// ----------------------------------------------------------------------------
// 1. Start with statistics queries (#3) to understand graph size
// 2. Use LIMIT to prevent browser overload on large graphs
// 3. For very large graphs, use type-specific queries (#4)
// 4. Neo4j Browser will auto-layout nodes for visualization
// 5. Use #11 queries to export data for external tools (Gephi, Cytoscape)
// ============================================================================

