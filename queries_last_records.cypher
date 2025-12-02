// ============================================================================
// Queries to Find Last Records from Pipeline Run
// ============================================================================
// Run these in Neo4j Browser (http://localhost:7474)
// ============================================================================

// ----------------------------------------------------------------------------
// 1. MOST RECENT ARTICLES (by published_date)
// ----------------------------------------------------------------------------
// Get the 10 most recently published articles
MATCH (a:Article)
WHERE a.published_date IS NOT NULL
RETURN a.id as article_id, 
       a.title as title, 
       a.url as url,
       a.published_date as published_date,
       a.author as author,
       size(a.categories) as category_count
ORDER BY a.published_date DESC
LIMIT 10;

// ----------------------------------------------------------------------------
// 2. MOST RECENT ARTICLES (by creation timestamp)
// ----------------------------------------------------------------------------
// Get articles sorted by when they were added to the graph
MATCH (a:Article)
WHERE a.created_at IS NOT NULL
RETURN a.id as article_id,
       a.title as title,
       a.url as url,
       datetime({epochMillis: a.created_at}) as created_at,
       a.published_date as published_date
ORDER BY a.created_at DESC
LIMIT 10;

// ----------------------------------------------------------------------------
// 3. MOST RECENTLY UPDATED ENTITIES
// ----------------------------------------------------------------------------
// Get entities that were most recently updated
MATCH (e)
WHERE e:Company OR e:Person OR e:Investor OR e:Technology OR e:Product
  AND e.updated_at IS NOT NULL
RETURN labels(e)[0] as entity_type,
       e.name as name,
       e.id as id,
       datetime({epochMillis: e.updated_at}) as updated_at,
       e.mention_count as mention_count,
       size(e.source_articles) as article_count
ORDER BY e.updated_at DESC
LIMIT 20;

// ----------------------------------------------------------------------------
// 4. MOST RECENTLY CREATED ENTITIES
// ----------------------------------------------------------------------------
// Get entities that were most recently created
MATCH (e)
WHERE e:Company OR e:Person OR e:Investor OR e:Technology OR e:Product
  AND e.created_at IS NOT NULL
RETURN labels(e)[0] as entity_type,
       e.name as name,
       e.id as id,
       datetime({epochMillis: e.created_at}) as created_at,
       e.description as description
ORDER BY e.created_at DESC
LIMIT 20;

// ----------------------------------------------------------------------------
// 5. MOST RECENTLY MENTIONED ENTITIES
// ----------------------------------------------------------------------------
// Get entities that were most recently mentioned in articles
MATCH (e)
WHERE e:Company OR e:Person OR e:Investor OR e:Technology OR e:Product
  AND e.last_mentioned IS NOT NULL
RETURN labels(e)[0] as entity_type,
       e.name as name,
       e.id as id,
       datetime({epochMillis: e.last_mentioned}) as last_mentioned,
       size(e.source_articles) as article_count
ORDER BY e.last_mentioned DESC
LIMIT 20;

// ----------------------------------------------------------------------------
// 6. LAST ARTICLE WITH ITS ENTITIES
// ----------------------------------------------------------------------------
// Get the most recent article and all entities extracted from it
MATCH (a:Article)
WHERE a.published_date IS NOT NULL
WITH a
ORDER BY a.published_date DESC
LIMIT 1
MATCH (e)
WHERE e.source_articles IS NOT NULL 
  AND a.id IN e.source_articles
RETURN a.id as article_id,
       a.title as article_title,
       a.published_date as published_date,
       collect({
         type: labels(e)[0],
         name: e.name,
         id: e.id,
         description: e.description
       }) as entities
LIMIT 1;

// ----------------------------------------------------------------------------
// 7. MOST RECENT RELATIONSHIPS
// ----------------------------------------------------------------------------
// Get relationships that were most recently created/updated
MATCH (s)-[r]->(t)
WHERE r.created_at IS NOT NULL OR r.updated_at IS NOT NULL
RETURN labels(s)[0] as source_type,
       s.name as source_name,
       type(r) as relationship_type,
       labels(t)[0] as target_type,
       t.name as target_name,
       CASE 
         WHEN r.updated_at IS NOT NULL THEN datetime({epochMillis: r.updated_at})
         ELSE datetime({epochMillis: r.created_at})
       END as last_updated,
       r.strength as strength
ORDER BY COALESCE(r.updated_at, r.created_at) DESC
LIMIT 20;

// ----------------------------------------------------------------------------
// 8. COMPLETE VIEW: Last Article with Full Details
// ----------------------------------------------------------------------------
// Get the most recent article with all its details and connected entities
MATCH (a:Article)
WHERE a.published_date IS NOT NULL
WITH a
ORDER BY a.published_date DESC
LIMIT 1
OPTIONAL MATCH (e)
WHERE e.source_articles IS NOT NULL 
  AND a.id IN e.source_articles
OPTIONAL MATCH (e)-[r]-(related)
WHERE NOT related:Article
RETURN a.id as article_id,
       a.title as article_title,
       a.url as article_url,
       a.published_date as published_date,
       a.author as author,
       a.categories as categories,
       count(DISTINCT e) as entity_count,
       collect(DISTINCT {
         entity_type: labels(e)[0],
         entity_name: e.name,
         entity_id: e.id,
         relationships: count(r)
       }) as entities
LIMIT 1;

// ----------------------------------------------------------------------------
// 9. SUMMARY: Last Pipeline Run Statistics
// ----------------------------------------------------------------------------
// Get summary of what was added in the last run
MATCH (a:Article)
WHERE a.published_date IS NOT NULL
WITH max(a.published_date) as latest_date
MATCH (a:Article {published_date: latest_date})
WITH a, latest_date
MATCH (e)
WHERE e.source_articles IS NOT NULL 
  AND a.id IN e.source_articles
RETURN latest_date as last_article_date,
       count(DISTINCT a) as articles_in_batch,
       count(DISTINCT e) as entities_extracted,
       collect(DISTINCT labels(e)[0]) as entity_types,
       count(DISTINCT CASE WHEN e:Company THEN 1 END) as companies,
       count(DISTINCT CASE WHEN e:Person THEN 1 END) as people,
       count(DISTINCT CASE WHEN e:Investor THEN 1 END) as investors;

// ----------------------------------------------------------------------------
// 10. QUICK CHECK: Latest Article ID and Title
// ----------------------------------------------------------------------------
// Simple query to see the most recent article
MATCH (a:Article)
WHERE a.published_date IS NOT NULL
RETURN a.id as article_id,
       a.title as title,
       a.published_date as published_date
ORDER BY a.published_date DESC
LIMIT 1;

