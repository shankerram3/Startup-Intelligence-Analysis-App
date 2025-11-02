# Why MENTIONED_IN Relationships Are So Common

## The Problem

You're seeing many `MENTIONED_IN` relationships in your graph because:

### 1. **LLM Extraction Creates Them**
   - The entity extraction prompt includes `MENTIONED_IN` as a valid relationship type
   - The LLM may extract entity-to-article relationships as `MENTIONED_IN` relationships
   - Each entity mentioned in an article can create one `MENTIONED_IN` relationship

### 2. **Redundant Design**
   - The graph builder has TWO ways to link entities to articles:
     - **Properties** (preferred): `source_articles`, `article_count` 
     - **Relationships**: `MENTIONED_IN` relationships
   - This creates redundancy and clutter

## The Solution

### ✅ Fixed in Code
I've updated the code to:
1. **Removed MENTIONED_IN from extraction prompt** - The LLM won't be told to create these
2. **Skip MENTIONED_IN in graph builder** - Even if extracted, they won't be created

### ✅ Clean Up Existing Graph
Run the graph cleanup utility:
```bash
python utils/graph_cleanup.py
```

Or if it's part of the pipeline, run:
```bash
python pipeline.py --no-cleanup  # First without cleanup
python pipeline.py --skip-extraction --skip-scraping --skip-graph  # Then cleanup
```

The cleanup will:
1. Convert existing `MENTIONED_IN` relationships → entity properties
2. Delete all `MENTIONED_IN` relationships
3. Keep the same information in a cleaner format

## Why Use Properties Instead of Relationships?

### Properties (Current Design):
- ✅ Cleaner graph - fewer relationships
- ✅ Faster queries - direct property access
- ✅ Better performance - no relationship traversal needed
- ✅ Still queryable - can find entities by article_id

### Relationships (Old Design):
- ❌ Creates many relationships (1 per entity-article pair)
- ❌ Graph clutter - thousands of relationships
- ❌ Slower queries - must traverse relationships
- ❌ Redundant - same info as properties

## Check Your Graph

Run these queries to see the current state:

```cypher
// Count MENTIONED_IN relationships
MATCH ()-[r:MENTIONED_IN]->()
RETURN count(r) as total;

// See sample relationships
MATCH (e)-[r:MENTIONED_IN]->(a:Article)
RETURN e.name, a.title LIMIT 10;

// Check if cleanup worked
MATCH (e)
WHERE e.source_articles IS NOT NULL
RETURN count(e) as entities_with_properties;
```

## After Cleanup

After running the cleanup:
- ✅ All `MENTIONED_IN` relationships will be deleted
- ✅ Entity properties (`source_articles`, `article_count`) will contain the same information
- ✅ Graph will be much cleaner and faster
- ✅ You can still query which entities appeared in which articles

## Future Processing

Going forward:
- ✅ New extractions won't create `MENTIONED_IN` relationships
- ✅ Entities will use properties for article linkage
- ✅ Only semantic relationships (FUNDED_BY, FOUNDED_BY, etc.) will be relationships

