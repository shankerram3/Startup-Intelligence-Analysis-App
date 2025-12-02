// ============================================================================
// Search for Article: "Glīd won Startup Battlefield 2025..."
// ============================================================================

// ----------------------------------------------------------------------------
// 1. EXACT TITLE MATCH
// ----------------------------------------------------------------------------
MATCH (a:Article)
WHERE a.title CONTAINS "Glīd won Startup Battlefield 2025"
RETURN a.id as article_id,
       a.title as title,
       a.url as url,
       a.published_date as published_date,
       a.author as author,
       datetime({epochMillis: a.created_at}) as inserted_at;

// ----------------------------------------------------------------------------
// 2. PARTIAL TITLE SEARCH (More Flexible)
// ----------------------------------------------------------------------------
MATCH (a:Article)
WHERE toLower(a.title) CONTAINS toLower("Glīd")
   OR toLower(a.title) CONTAINS toLower("Startup Battlefield")
   OR toLower(a.title) CONTAINS toLower("logistics")
RETURN a.id as article_id,
       a.title as title,
       a.url as url,
       a.published_date as published_date,
       a.author as author,
       datetime({epochMillis: a.created_at}) as inserted_at
ORDER BY 
  CASE 
    WHEN toLower(a.title) CONTAINS toLower("Glīd") AND toLower(a.title) CONTAINS toLower("Startup Battlefield") THEN 1
    WHEN toLower(a.title) CONTAINS toLower("Glīd") THEN 2
    WHEN toLower(a.title) CONTAINS toLower("Startup Battlefield") THEN 3
    ELSE 4
  END;

// ----------------------------------------------------------------------------
// 3. FULL TEXT SEARCH (If fulltext index exists)
// ----------------------------------------------------------------------------
// Note: This requires a fulltext index to be created first
// CREATE FULLTEXT INDEX articleTitle IF NOT EXISTS FOR (a:Article) ON EACH [a.title]
MATCH (a:Article)
WHERE a.title =~ "(?i).*Glīd.*Startup Battlefield.*"
RETURN a.id as article_id,
       a.title as title,
       a.url as url,
       a.published_date as published_date;

// ----------------------------------------------------------------------------
// 4. SEARCH BY KEYWORDS
// ----------------------------------------------------------------------------
MATCH (a:Article)
WHERE toLower(a.title) CONTAINS toLower("Glīd")
   OR toLower(a.title) CONTAINS toLower("Startup Battlefield 2025")
   OR toLower(a.title) CONTAINS toLower("logistics simpler safer smarter")
RETURN a.id as article_id,
       a.title as title,
       a.url as url,
       a.published_date as published_date,
       a.author as author;

// ----------------------------------------------------------------------------
// 5. COMPLETE ARTICLE WITH ENTITIES
// ----------------------------------------------------------------------------
// Get the article and all entities extracted from it
MATCH (a:Article)
WHERE toLower(a.title) CONTAINS toLower("Glīd")
   AND toLower(a.title) CONTAINS toLower("Startup Battlefield")
OPTIONAL MATCH (e)
WHERE e.source_articles IS NOT NULL 
  AND a.id IN e.source_articles
RETURN a.id as article_id,
       a.title as article_title,
       a.url as article_url,
       a.published_date as published_date,
       a.author as author,
       a.categories as categories,
       datetime({epochMillis: a.created_at}) as inserted_at,
       count(DISTINCT e) as entity_count,
       collect(DISTINCT {
         type: labels(e)[0],
         name: e.name,
         id: e.id,
         description: e.description
       }) as entities
LIMIT 1;

// ----------------------------------------------------------------------------
// 6. SEARCH FOR "Glid" (without special character)
// ----------------------------------------------------------------------------
// Sometimes the special character might be stored differently
MATCH (a:Article)
WHERE toLower(a.title) CONTAINS toLower("Glid")
   OR toLower(a.title) CONTAINS toLower("Glīd")
RETURN a.id as article_id,
       a.title as title,
       a.url as url,
       a.published_date as published_date;

// ----------------------------------------------------------------------------
// 7. SEARCH BY URL PATTERN
// ----------------------------------------------------------------------------
// If you know it's a Startup Battlefield article, search by URL pattern
MATCH (a:Article)
WHERE a.url CONTAINS "startup-battlefield"
   OR a.url CONTAINS "battlefield"
RETURN a.id as article_id,
       a.title as title,
       a.url as url,
       a.published_date as published_date
ORDER BY a.published_date DESC
LIMIT 10;

// ----------------------------------------------------------------------------
// 8. SEARCH FOR ENTITY "Glīd" OR "Glid"
// ----------------------------------------------------------------------------
// Also search for the company entity that might be mentioned
MATCH (e:Company)
WHERE toLower(e.name) CONTAINS toLower("glid")
RETURN e.id as entity_id,
       e.name as company_name,
       e.description as description,
       e.source_articles as source_articles,
       size(e.source_articles) as article_count;

// ----------------------------------------------------------------------------
// 9. FIND ARTICLE BY ENTITY
// ----------------------------------------------------------------------------
// Find articles that mention Glīd company
MATCH (e:Company)
WHERE toLower(e.name) CONTAINS toLower("glid")
MATCH (a:Article)
WHERE a.id IN e.source_articles
RETURN a.id as article_id,
       a.title as title,
       a.url as url,
       a.published_date as published_date,
       e.name as company_name;

// ----------------------------------------------------------------------------
// 10. COMPREHENSIVE SEARCH
// ----------------------------------------------------------------------------
// Search everything related to Glīd and Startup Battlefield
MATCH (a:Article)
WHERE toLower(a.title) CONTAINS toLower("glid")
   OR toLower(a.title) CONTAINS toLower("startup battlefield")
OPTIONAL MATCH (e)
WHERE e.source_articles IS NOT NULL 
  AND a.id IN e.source_articles
OPTIONAL MATCH (e)-[r]-(related)
WHERE NOT related:Article
RETURN a.id as article_id,
       a.title as article_title,
       a.url as article_url,
       a.published_date as published_date,
       datetime({epochMillis: a.created_at}) as inserted_at,
       count(DISTINCT e) as total_entities,
       count(DISTINCT CASE WHEN e:Company THEN 1 END) as companies,
       count(DISTINCT CASE WHEN e:Person THEN 1 END) as people,
       count(DISTINCT CASE WHEN e:Event THEN 1 END) as events,
       collect(DISTINCT {
         type: labels(e)[0],
         name: e.name,
         id: e.id
       }) as entities
LIMIT 5;

