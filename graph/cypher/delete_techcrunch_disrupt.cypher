// ============================================================================
// Delete TechCrunch Disrupt Nodes and Relationships - Neo4j Cypher Queries
// ============================================================================
// Run these queries in Neo4j Browser (http://localhost:7474)
// Or use the Neo4j Python driver
//
// IMPORTANT: Backup your database before running delete queries!
// ============================================================================

// ----------------------------------------------------------------------------
// STEP 1: Find all nodes related to "TechCrunch Disrupt"
// ----------------------------------------------------------------------------

// Find nodes with "TechCrunch Disrupt" in the name (case-insensitive)
MATCH (n)
WHERE n.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
RETURN labels(n) as type, n.name as name, n.id as id, id(n) as internal_id
ORDER BY n.name;

// Find all relationships connected to TechCrunch Disrupt nodes
MATCH (n)-[r]-(related)
WHERE n.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
RETURN type(r) as relationship_type, 
       n.name as from_node, 
       labels(n) as from_type,
       related.name as to_node,
       labels(related) as to_type;

// Count nodes and relationships to be deleted
MATCH (n)
WHERE n.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
WITH n, count{(n)-[r]-()} as rel_count
RETURN count(n) as nodes_to_delete, sum(rel_count) as relationships_to_delete;

// ----------------------------------------------------------------------------
// STEP 2: Preview what will be deleted (relationships)
// ----------------------------------------------------------------------------

// Show all relationships connected to TechCrunch Disrupt nodes
MATCH (n)-[r]-(related)
WHERE n.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
RETURN n, r, related
LIMIT 50;

// ----------------------------------------------------------------------------
// STEP 3: DELETE RELATIONSHIPS (Run this first!)
// ----------------------------------------------------------------------------

// Delete all relationships connected to TechCrunch Disrupt nodes
// This must be done before deleting the nodes
MATCH (n)-[r]-(related)
WHERE n.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
DELETE r;

// Alternative: Delete only specific relationship types
// MATCH (n)-[r:ANNOUNCED_AT|LOCATED_IN|MENTIONED_IN]-(related)
// WHERE n.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
// DELETE r;

// ----------------------------------------------------------------------------
// STEP 4: DELETE NODES (Run after deleting relationships)
// ----------------------------------------------------------------------------

// Delete all nodes with "TechCrunch Disrupt" in the name
MATCH (n)
WHERE n.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
DELETE n;

// ----------------------------------------------------------------------------
// ONE-STEP DELETION (More efficient - deletes nodes and relationships together)
// ----------------------------------------------------------------------------

// Delete nodes and all their relationships in one query
MATCH (n)
WHERE n.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
DETACH DELETE n;

// ----------------------------------------------------------------------------
// VERIFICATION: Check if deletion was successful
// ----------------------------------------------------------------------------

// Verify no TechCrunch Disrupt nodes remain
MATCH (n)
WHERE n.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
RETURN count(n) as remaining_nodes;

// Should return: remaining_nodes: 0

// ============================================================================
// ALTERNATIVE: Delete by exact name match
// ============================================================================

// If you know the exact name(s), use exact match instead of regex:
// MATCH (n {name: "TECHCRUNCH DISRUPT 2025"})
// DETACH DELETE n;

// ============================================================================
// ALTERNATIVE: Delete by Event label and name pattern
// ============================================================================

// Delete only Event nodes with TechCrunch Disrupt in name
// MATCH (e:Event)
// WHERE e.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
// DETACH DELETE e;

// ============================================================================
// NOTES:
// ============================================================================
// 1. DETACH DELETE automatically removes all relationships before deleting nodes
// 2. The regex pattern (?i).*TECHCRUNCH DISRUPT.* is case-insensitive
// 3. Adjust the pattern if you need exact match: "(?i)^TECHCRUNCH DISRUPT 2025$"
// 4. For multiple variants, use: "TECHCRUNCH DISRUPT.*" or specific years
// 5. Always run the FIND queries first to verify what will be deleted
// ============================================================================

