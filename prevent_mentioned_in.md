# Preventing MENTIONED_IN Relationships in Graph

## Multiple Layers of Protection

The system now has **multiple safeguards** to prevent MENTIONED_IN relationships from being created:

### 1. ✅ Extraction Prompt (Layer 1)
- **Location**: `entity_extractor.py` line 56-57
- **Action**: MENTIONED_IN is **not** included in valid relationship types
- **Note**: Explicit instruction not to create MENTIONED_IN relationships

### 2. ✅ Parsing Filter (Layer 2)
- **Location**: `entity_extractor.py` `_parse_extraction_result()` method
- **Action**: Filters out any MENTIONED_IN relationships during parsing
- **Warning**: Logs a warning if MENTIONED_IN is detected

### 3. ✅ Validation Check (Layer 3)
- **Location**: `utils/data_validation.py` `validate_extraction()` function
- **Action**: Validation error if MENTIONED_IN is found
- **Result**: Extraction marked as invalid if MENTIONED_IN relationships exist

### 4. ✅ Ingestion Filter (Layer 4)
- **Location**: `graph_builder.py` `ingest_extraction()` method
- **Action**: Filters out MENTIONED_IN relationships before processing
- **Warning**: Logs skipped count

### 5. ✅ Creation Guard (Layer 5)
- **Location**: `graph_builder.py` `create_relationship()` method
- **Action**: Skips creation if MENTIONED_IN is detected
- **Validation**: Also validates relationship type is in allowed list
- **Warning**: Logs warning if MENTIONED_IN is attempted

## Summary

**5 layers of protection** ensure MENTIONED_IN relationships never get into the graph:

1. LLM is told not to create them (prompt)
2. Parsed results filter them out
3. Validation rejects them
4. Ingestion filters them
5. Creation method blocks them

Even if the LLM creates them, they'll be filtered out at multiple stages.

## Testing

To verify the protection works:

```python
# Test extraction validation
from utils.data_validation import validate_extraction

test_extraction = {
    "relationships": [
        {"source": "Entity", "target": "Article", "type": "MENTIONED_IN", "description": "test"}
    ]
}

is_valid, errors = validate_extraction(test_extraction)
# Should be False with error about MENTIONED_IN
```

## Monitoring

If you see warnings about MENTIONED_IN:
- Check extraction logs for filtered relationships
- Review validation errors
- Check graph builder warnings

All warnings are logged to help identify if MENTIONED_IN is being extracted.

