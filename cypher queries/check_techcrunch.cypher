// ============================================================================
// Check for remaining TechCrunch related nodes
// ============================================================================

// Find all nodes with "TechCrunch" in name (case-insensitive)
MATCH (n)
WHERE n.name CONTAINS 'TechCrunch' 
   OR n.name CONTAINS 'TECHCRUNCH'
   OR n.name CONTAINS 'techcrunch'
   OR n.name =~ '(?i).*TECHCRUNCH.*DISRUPT.*'
   OR n.name =~ '(?i).*TECHCRUNCH DISRUPT.*'
RETURN labels(n)[0] as type, n.name as name, n.id as id
ORDER BY n.name;

// Count nodes with TechCrunch in name
MATCH (n)
WHERE n.name CONTAINS 'TechCrunch' 
   OR n.name CONTAINS 'TECHCRUNCH'
   OR n.name =~ '(?i).*TECHCRUNCH.*DISRUPT.*'
RETURN count(n) as total_nodes;

// Find nodes related to TechCrunch Disrupt events
MATCH (n)
WHERE n.name CONTAINS 'Disrupt'
   OR n.name CONTAINS 'DISRUPT'
   OR n.name CONTAINS 'Battlefield'
   OR n.name CONTAINS 'BATTLEFIELD'
RETURN labels(n)[0] as type, n.name as name, n.id as id
ORDER BY n.name;

// Count Disrupt/Battlefield related nodes
MATCH (n)
WHERE n.name CONTAINS 'Disrupt'
   OR n.name CONTAINS 'DISRUPT'
   OR n.name CONTAINS 'Battlefield'
   OR n.name CONTAINS 'BATTLEFIELD'
RETURN count(n) as total_nodes;

