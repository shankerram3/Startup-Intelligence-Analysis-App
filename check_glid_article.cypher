// ============================================================================
// Check if Glīd article is in the graph
// ============================================================================

// ----------------------------------------------------------------------------
// 1. Search by article ID from extraction file
// ----------------------------------------------------------------------------
MATCH (a:Article {id: "a19d80c3f574"})
RETURN a.id as article_id,
       a.title as title,
       a.url as url,
       a.published_date as published_date,
       datetime({epochMillis: a.created_at}) as inserted_at;

// ----------------------------------------------------------------------------
// 2. Search by URL pattern
// ----------------------------------------------------------------------------
MATCH (a:Article)
WHERE a.url CONTAINS "glid-won-startup-battlefield"
   OR a.url CONTAINS "glid"
RETURN a.id as article_id,
       a.title as title,
       a.url as url,
       a.published_date as published_date;

// ----------------------------------------------------------------------------
// 3. Search all articles and check titles
// ----------------------------------------------------------------------------
MATCH (a:Article)
WHERE toLower(a.title) CONTAINS toLower("glid")
   OR toLower(a.title) CONTAINS toLower("battlefield")
RETURN a.id as article_id,
       a.title as title,
       substring(a.url, 0, 80) as url_short,
       a.published_date as published_date
ORDER BY a.published_date DESC
LIMIT 10;

// ----------------------------------------------------------------------------
// 4. Check if article exists by checking all article IDs
// ----------------------------------------------------------------------------
// This will show if the article ID exists at all
MATCH (a:Article)
WHERE a.id = "a19d80c3f574"
RETURN count(a) as article_exists;

// ----------------------------------------------------------------------------
// 5. Get all article IDs to verify
// ----------------------------------------------------------------------------
MATCH (a:Article)
RETURN a.id as article_id, 
       a.title as title
ORDER BY a.published_date DESC
LIMIT 20;

// ----------------------------------------------------------------------------
// 6. Check entities from the article (if article exists)
// ----------------------------------------------------------------------------
MATCH (a:Article {id: "a19d80c3f574"})
MATCH (e)
WHERE e.source_articles IS NOT NULL 
  AND a.id IN e.source_articles
RETURN a.id as article_id,
       a.title as article_title,
       count(e) as entity_count,
       collect(DISTINCT labels(e)[0]) as entity_types,
       collect(DISTINCT e.name)[0..10] as sample_entities;

