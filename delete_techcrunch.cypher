// ============================================================================
// Delete TechCrunch and TechCrunch Disrupt Nodes - Neo4j Cypher Queries
// ============================================================================
// Run these queries in Neo4j Browser (http://localhost:7474)
// ============================================================================

// ----------------------------------------------------------------------------
// STEP 1: Find all TechCrunch/TechCrunch Disrupt nodes
// ----------------------------------------------------------------------------

// Find nodes by name pattern (case-insensitive)
MATCH (n)
WHERE n.name =~ '(?i).*TECHCRUNCH.*DISRUPT.*'
   OR n.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
   OR n.name =~ '(?i)^TECHCRUNCH.*'
   OR n.name =~ '(?i).*TECHCRUNCH$'
RETURN labels(n)[0] as type, n.name as name, n.id as id, id(n) as internal_id
ORDER BY n.name;

// Find nodes with TechCrunch in description
MATCH (n)
WHERE n.description CONTAINS 'TechCrunch' 
   OR n.description CONTAINS 'TECHCRUNCH'
   OR n.description CONTAINS 'techcrunch'
RETURN labels(n)[0] as type, n.name as name, n.id as id, n.description as description
ORDER BY n.name;

// Count total nodes to be deleted
MATCH (n)
WHERE n.name =~ '(?i).*TECHCRUNCH.*DISRUPT.*'
   OR n.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
   OR n.name =~ '(?i)^TECHCRUNCH.*'
   OR n.name =~ '(?i).*TECHCRUNCH$'
   OR n.description CONTAINS 'TechCrunch'
   OR n.description CONTAINS 'TECHCRUNCH'
RETURN count(n) as total_nodes;

// Count relationships to be deleted
MATCH (n)-[r]-()
WHERE n.name =~ '(?i).*TECHCRUNCH.*DISRUPT.*'
   OR n.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
   OR n.name =~ '(?i)^TECHCRUNCH.*'
   OR n.name =~ '(?i).*TECHCRUNCH$'
   OR n.description CONTAINS 'TechCrunch'
   OR n.description CONTAINS 'TECHCRUNCH'
RETURN count(r) as total_relationships;

// ----------------------------------------------------------------------------
// STEP 2: Preview relationships (optional)
// ----------------------------------------------------------------------------

// See all relationships connected to TechCrunch nodes
MATCH path = (n)-[r]-(related)
WHERE n.name =~ '(?i).*TECHCRUNCH.*DISRUPT.*'
   OR n.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
   OR n.name =~ '(?i)^TECHCRUNCH.*'
   OR n.name =~ '(?i).*TECHCRUNCH$'
RETURN type(r) as rel_type, n.name as from_node, related.name as to_node
LIMIT 50;

// ----------------------------------------------------------------------------
// STEP 3: DELETE ALL TECHCRUNCH/TECHCRUNCH DISRUPT NODES
// ----------------------------------------------------------------------------

// Delete all nodes matching TechCrunch patterns and all their relationships
MATCH (n)
WHERE n.name =~ '(?i).*TECHCRUNCH.*DISRUPT.*'
   OR n.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
   OR n.name =~ '(?i)^TECHCRUNCH.*'
   OR n.name =~ '(?i).*TECHCRUNCH$'
   OR n.description CONTAINS 'TechCrunch'
   OR n.description CONTAINS 'TECHCRUNCH'
DETACH DELETE n;

// ----------------------------------------------------------------------------
// STEP 4: VERIFY DELETION
// ----------------------------------------------------------------------------

// Check if any TechCrunch nodes remain
MATCH (n)
WHERE n.name =~ '(?i).*TECHCRUNCH.*DISRUPT.*'
   OR n.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
   OR n.name =~ '(?i)^TECHCRUNCH.*'
   OR n.name =~ '(?i).*TECHCRUNCH$'
   OR n.description CONTAINS 'TechCrunch'
   OR n.description CONTAINS 'TECHCRUNCH'
RETURN count(n) as remaining_nodes;

// Should return: remaining_nodes: 0

// ----------------------------------------------------------------------------
// ALTERNATIVE: Delete by exact name
// ----------------------------------------------------------------------------

// If you know specific names, use exact match:
// MATCH (n {name: "TECHCRUNCH DISRUPT 2025"})
// DETACH DELETE n;

// MATCH (n {name: "TECHCRUNCH"})
// DETACH DELETE n;

// ----------------------------------------------------------------------------
// ALTERNATIVE: Delete only Event nodes (if TechCrunch Disrupt is an Event)
// ----------------------------------------------------------------------------

// Delete only Event nodes with TechCrunch in name
// MATCH (e:Event)
// WHERE e.name =~ '(?i).*TECHCRUNCH.*DISRUPT.*'
//    OR e.name =~ '(?i).*TECHCRUNCH.*'
// DETACH DELETE e;

// ----------------------------------------------------------------------------
// NOTES:
// ----------------------------------------------------------------------------
// 1. DETACH DELETE automatically removes all relationships before deleting nodes
// 2. The regex pattern (?i) makes matching case-insensitive
// 3. Patterns match:
//    - "TECHCRUNCH DISRUPT 2025"
//    - "TechCrunch Disrupt"
//    - "TECHCRUNCH"
//    - Any variation with TechCrunch in name or description
// 4. Always run the FIND queries first to verify what will be deleted
// 5. Back up your database before running delete queries!
// ============================================================================

