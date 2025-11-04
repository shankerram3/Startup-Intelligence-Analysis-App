// ============================================================================
// Check MENTIONED_IN Relationships in Graph
// ============================================================================

// Count total MENTIONED_IN relationships
MATCH ()-[r:MENTIONED_IN]->()
RETURN count(r) as total_mentioned_in_relationships;

// Count MENTIONED_IN by entity type
MATCH (e)-[r:MENTIONED_IN]->(a:Article)
RETURN labels(e)[0] as entity_type, count(r) as count
ORDER BY count DESC;

// See sample MENTIONED_IN relationships
MATCH (e)-[r:MENTIONED_IN]->(a:Article)
RETURN e.name as entity, labels(e)[0] as entity_type, a.title as article, a.id as article_id
LIMIT 20;

// Check if entities have source_articles property (after cleanup)
MATCH (e)
WHERE e.source_articles IS NOT NULL
RETURN labels(e)[0] as entity_type, count(e) as entities_with_property
ORDER BY entities_with_property DESC;

// Compare: relationships vs properties
MATCH (e)-[r:MENTIONED_IN]->(:Article)
WITH labels(e)[0] as type, count(r) as relationship_count
MATCH (e2)
WHERE labels(e2)[0] = type AND e2.source_articles IS NOT NULL
RETURN type, relationship_count, count(e2) as property_count
ORDER BY relationship_count DESC;

