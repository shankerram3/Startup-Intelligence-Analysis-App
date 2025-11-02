// ============================================================================
// Direct Cypher Query to Remove All MENTIONED_IN Relationships
// ============================================================================
// Run this in Neo4j Browser to remove remaining MENTIONED_IN relationships
// ============================================================================

// Step 1: Count remaining MENTIONED_IN relationships
MATCH ()-[r:MENTIONED_IN]->()
RETURN count(r) as remaining_relationships;

// Step 2: See what they look like
MATCH (e)-[r:MENTIONED_IN]->(a:Article)
RETURN labels(e)[0] as entity_type, 
       e.name as entity_name, 
       a.title as article_title,
       a.id as article_id
LIMIT 20;

// Step 3: Convert to properties (for entities that don't have them yet)
MATCH (e)-[r:MENTIONED_IN]->(a:Article)
WITH e, collect(DISTINCT a.id) as article_ids
WHERE e.source_articles IS NULL OR NOT all(id IN article_ids WHERE id IN e.source_articles)
SET e.source_articles = CASE 
    WHEN e.source_articles IS NULL THEN article_ids
    ELSE [x IN e.source_articles WHERE x IN article_ids] + [x IN article_ids WHERE NOT x IN e.source_articles]
END,
e.article_count = size(e.source_articles),
e.last_mentioned = timestamp();

// Step 4: Delete ALL MENTIONED_IN relationships
MATCH ()-[r:MENTIONED_IN]->()
DELETE r
RETURN count(r) as deleted_relationships;

// Step 5: Verify they're gone
MATCH ()-[r:MENTIONED_IN]->()
RETURN count(r) as remaining_after_cleanup;
// Should return 0

// ============================================================================
// Alternative: One-step deletion (if properties are already set)
// ============================================================================

// If properties are already set, just delete relationships:
MATCH ()-[r:MENTIONED_IN]->()
DELETE r;

// Verify
MATCH ()-[r:MENTIONED_IN]->()
RETURN count(r) as remaining;
// Should return 0

