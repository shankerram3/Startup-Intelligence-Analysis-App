"""
Data validation utilities for the pipeline
"""

from typing import Dict, List, Optional
from pathlib import Path


def validate_article(article_data: Dict) -> tuple[bool, Optional[str]]:
    """
    Validate article data before extraction

    Args:
        article_data: Dictionary with 'content' and 'metadata' keys

    Returns:
        (is_valid, error_message) tuple
    """
    if not article_data:
        return False, "Article data is empty"

    # Check required structure
    if "content" not in article_data:
        return False, "Missing 'content' key"

    if "metadata" not in article_data:
        return False, "Missing 'metadata' key"

    content = article_data.get("content", {})
    metadata = article_data.get("metadata", {})

    # Validate content
    if not isinstance(content, dict):
        return False, "Content must be a dictionary"

    headline = content.get("headline", "").strip()
    paragraphs = content.get("paragraphs", [])

    if not headline:
        return False, "Missing or empty headline"

    if not paragraphs or not isinstance(paragraphs, list):
        return False, "Missing or invalid paragraphs"

    # Check content length (minimum 100 chars)
    full_text = headline + " " + " ".join(paragraphs[:5])
    if len(full_text.strip()) < 100:
        return False, f"Article too short ({len(full_text)} chars, minimum 100)"

    # Validate metadata
    required_fields = ["url", "title", "published_date", "article_id"]
    for field in required_fields:
        if field not in metadata:
            return False, f"Missing required metadata field: {field}"

        value = metadata.get(field, "").strip()
        if not value:
            return False, f"Empty value for metadata field: {field}"

    return True, None


def validate_extraction(extraction: Dict) -> tuple[bool, List[str]]:
    """
    Validate extracted entities and relationships

    Args:
        extraction: Dictionary with entities and relationships

    Returns:
        (is_valid, list_of_errors) tuple
    """
    errors = []

    if not extraction:
        return False, ["Extraction data is empty"]

    # Validate structure
    if "entities" not in extraction:
        errors.append("Missing 'entities' key")

    if "relationships" not in extraction:
        errors.append("Missing 'relationships' key")

    if "article_metadata" not in extraction:
        errors.append("Missing 'article_metadata' key")

    if errors:
        return False, errors

    entities = extraction.get("entities", [])
    relationships = extraction.get("relationships", [])

    # Validate entities
    if not isinstance(entities, list):
        errors.append("Entities must be a list")
    else:
        required_entity_fields = ["name", "type", "description"]
        for i, entity in enumerate(entities):
            if not isinstance(entity, dict):
                errors.append(f"Entity {i} is not a dictionary")
                continue

            for field in required_entity_fields:
                if field not in entity:
                    errors.append(f"Entity {i} missing required field: {field}")
                elif not entity.get(field, "").strip():
                    errors.append(f"Entity {i} has empty {field}")

            # Validate entity type
            entity_type = entity.get("type", "").upper()
            valid_types = [
                "COMPANY",
                "PERSON",
                "INVESTOR",
                "TECHNOLOGY",
                "PRODUCT",
                "FUNDING_ROUND",
                "LOCATION",
                "EVENT",
            ]
            if entity_type not in valid_types:
                errors.append(f"Entity {i} has invalid type: {entity_type}")

            # Filter out TechCrunch/Disrupt related entities
            entity_name = entity.get("name", "")
            if entity_name:
                from .filter_techcrunch import is_techcrunch_related

                if is_techcrunch_related(entity_name):
                    errors.append(
                        f"Entity {i} ('{entity_name}') is TechCrunch/TechCrunch Disrupt related and should not be added to graph"
                    )

    # Validate relationships
    if not isinstance(relationships, list):
        errors.append("Relationships must be a list")
    else:
        required_rel_fields = ["source", "target", "type", "description"]
        for i, rel in enumerate(relationships):
            if not isinstance(rel, dict):
                errors.append(f"Relationship {i} is not a dictionary")
                continue

            for field in required_rel_fields:
                if field not in rel:
                    errors.append(f"Relationship {i} missing required field: {field}")
                elif not rel.get(field, "").strip():
                    errors.append(f"Relationship {i} has empty {field}")

            # Validate relationship type
            rel_type = rel.get("type", "")
            valid_types = [
                "FUNDED_BY",
                "FOUNDED_BY",
                "WORKS_AT",
                "ACQUIRED",
                "PARTNERS_WITH",
                "COMPETES_WITH",
                "USES_TECHNOLOGY",
                "LOCATED_IN",
                "ANNOUNCED_AT",
            ]
            # MENTIONED_IN is not a valid relationship type - use properties instead
            if rel_type == "MENTIONED_IN":
                errors.append(
                    f"Relationship {i} uses MENTIONED_IN - this should be handled via properties, not relationships"
                )
            elif rel_type not in valid_types:
                errors.append(f"Relationship {i} has invalid type: {rel_type}")

            # Validate strength
            strength = rel.get("strength", 0)
            if not isinstance(strength, int) or strength < 0 or strength > 10:
                errors.append(f"Relationship {i} has invalid strength: {strength}")

            # Filter out relationships involving TechCrunch/Disrupt entities
            source = rel.get("source", "")
            target = rel.get("target", "")
            if source or target:
                from .filter_techcrunch import is_techcrunch_related

                if is_techcrunch_related(source) or is_techcrunch_related(target):
                    errors.append(
                        f"Relationship {i} involves TechCrunch/Disrupt entity: {source} -> {target}"
                    )

    return len(errors) == 0, errors
