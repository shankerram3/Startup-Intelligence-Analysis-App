// ============================================================================
// Query to Understand Article Insertion Time
// ============================================================================
// This query explains the timestamps and when the article was inserted
// ============================================================================

// ----------------------------------------------------------------------------
// UNDERSTANDING THE TIMESTAMPS:
// ----------------------------------------------------------------------------
// 1. published_date: "2025-11-18T13:42:48-08:00"
//    - This is when the article was ORIGINALLY PUBLISHED on TechCrunch
//    - Format: ISO 8601 with timezone (-08:00 = Pacific Time)
//    - This is the article's publication date, NOT when it was inserted
//
// 2. created_at / timestamp: "2025-11-28T03:03:33.225000000Z"
//    - This is when the article was INSERTED INTO YOUR GRAPH DATABASE
//    - Format: UTC timestamp (Z = UTC/Zulu time)
//    - This is when your pipeline processed and added it to Neo4j
//
// DIFFERENCE: The article was published on Nov 18, but your pipeline
//             processed and inserted it on Nov 28 (10 days later)

// ----------------------------------------------------------------------------
// QUERY: Get Article Details with All Timestamps
// ----------------------------------------------------------------------------
MATCH (a:Article {id: "24fe8f9e0a08"})
RETURN a.id as article_id,
       a.title as title,
       a.url as url,
       a.published_date as published_date,
       datetime({epochMillis: a.created_at}) as inserted_at_utc,
       a.created_at as created_at_timestamp,
       a.author as author,
       a.categories as categories,
       size(a.categories) as category_count;

// ----------------------------------------------------------------------------
// QUERY: Article with Time Difference Calculation
// ----------------------------------------------------------------------------
// Shows the time difference between publication and insertion
MATCH (a:Article {id: "24fe8f9e0a08"})
WITH a,
     datetime({epochMillis: a.created_at}) as inserted_datetime,
     datetime(a.published_date) as published_datetime
RETURN a.id as article_id,
       a.title as title,
       a.published_date as published_date,
       inserted_datetime as inserted_at,
       duration.between(published_datetime, inserted_datetime) as time_since_publication,
       a.url as url;

// ----------------------------------------------------------------------------
// QUERY: Article with All Entities Extracted
// ----------------------------------------------------------------------------
// See what entities were extracted from this article
MATCH (a:Article {id: "24fe8f9e0a08"})
MATCH (e)
WHERE e.source_articles IS NOT NULL 
  AND a.id IN e.source_articles
RETURN a.id as article_id,
       a.title as article_title,
       a.published_date as published_date,
       datetime({epochMillis: a.created_at}) as inserted_at,
       labels(e)[0] as entity_type,
       e.name as entity_name,
       e.id as entity_id,
       e.description as description,
       e.mention_count as mention_count
ORDER BY entity_type, e.name;

// ----------------------------------------------------------------------------
// QUERY: Complete Article Summary
// ----------------------------------------------------------------------------
// Full details about when and how this article was processed
MATCH (a:Article {id: "24fe8f9e0a08"})
OPTIONAL MATCH (e)
WHERE e.source_articles IS NOT NULL 
  AND a.id IN e.source_articles
OPTIONAL MATCH (e)-[r]-(related)
WHERE NOT related:Article
WITH a, 
     collect(DISTINCT e) as entities,
     collect(DISTINCT r) as relationships
RETURN a.id as article_id,
       a.title as article_title,
       a.url as article_url,
       a.published_date as original_publication_date,
       datetime({epochMillis: a.created_at}) as inserted_into_graph_at,
       a.author as author,
       a.categories as categories,
       count(DISTINCT entities) as total_entities_extracted,
       count(DISTINCT CASE WHEN e:Company THEN 1 END) as companies,
       count(DISTINCT CASE WHEN e:Person THEN 1 END) as people,
       count(DISTINCT CASE WHEN e:Investor THEN 1 END) as investors,
       count(DISTINCT CASE WHEN e:Technology THEN 1 END) as technologies,
       count(DISTINCT relationships) as relationships_found;

// ----------------------------------------------------------------------------
// QUERY: When Was This Article Processed? (Simple Version)
// ----------------------------------------------------------------------------
MATCH (a:Article {id: "24fe8f9e0a08"})
RETURN 
  "Article ID" as field,
  a.id as value
UNION ALL
MATCH (a:Article {id: "24fe8f9e0a08"})
RETURN 
  "Title" as field,
  a.title as value
UNION ALL
MATCH (a:Article {id: "24fe8f9e0a08"})
RETURN 
  "Published Date (Original)" as field,
  a.published_date as value
UNION ALL
MATCH (a:Article {id: "24fe8f9e0a08"})
RETURN 
  "Inserted Into Graph At" as field,
  datetime({epochMillis: a.created_at}) as value
UNION ALL
MATCH (a:Article {id: "24fe8f9e0a08"})
RETURN 
  "Days Since Publication" as field,
  toString(
    duration.between(
      datetime(a.published_date), 
      datetime({epochMillis: a.created_at})
    ).days
  ) + " days" as value;

