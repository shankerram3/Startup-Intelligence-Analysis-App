"""
Entity name normalization and deduplication utilities
"""

import re
from typing import Optional
from difflib import SequenceMatcher


def normalize_entity_name(name: str) -> str:
    """
    Normalize entity name for better matching
    
    Args:
        name: Original entity name
    
    Returns:
        Normalized entity name
    """
    if not name:
        return ""
    
    # Convert to uppercase for consistent comparison
    normalized = name.upper().strip()
    
    # Remove common suffixes/prefixes that cause duplicates
    suffixes_to_remove = [
        r'\s+INC\.?$', r'\s+LLC\.?$', r'\s+LTD\.?$', r'\s+CORP\.?$',
        r'\s+COMPANY$', r'\s+CO\.?$', r'\s+PVT\.?$', r'\s+LLP\.?$',
        r'\s+LP\.?$', r'\s+PLC\.?$', r'\s+AG\.?$', r'\s+GMBH\.?$'
    ]
    
    for suffix in suffixes_to_remove:
        normalized = re.sub(suffix, '', normalized, flags=re.IGNORECASE)
    
    # Remove special characters except spaces and hyphens
    normalized = re.sub(r'[^\w\s-]', '', normalized)
    
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized.strip()


def are_similar_entities(name1: str, name2: str, threshold: float = 0.85) -> bool:
    """
    Check if two entity names are similar (likely duplicates)
    
    Args:
        name1: First entity name
        name2: Second entity name
        threshold: Similarity threshold (0-1)
    
    Returns:
        True if names are similar enough to be considered duplicates
    """
    norm1 = normalize_entity_name(name1)
    norm2 = normalize_entity_name(name2)
    
    # Exact match after normalization
    if norm1 == norm2:
        return True
    
    # Calculate similarity ratio
    ratio = SequenceMatcher(None, norm1, norm2).ratio()
    
    return ratio >= threshold


def get_canonical_name(names: list[str]) -> str:
    """
    Get canonical name from a list of similar names (chooses the most common/longest)
    
    Args:
        names: List of similar entity names
    
    Returns:
        Canonical name
    """
    if not names:
        return ""
    
    # Sort by length (longest first) and then by frequency
    # Prefer longer names as they're usually more complete
    names_with_counts = {}
    for name in names:
        normalized = normalize_entity_name(name)
        if normalized not in names_with_counts:
            names_with_counts[normalized] = {"original": name, "count": 0}
        names_with_counts[normalized]["count"] += 1
    
    # Sort by count (descending), then by length (descending)
    sorted_names = sorted(
        names_with_counts.items(),
        key=lambda x: (x[1]["count"], len(x[1]["original"])),
        reverse=True
    )
    
    return sorted_names[0][1]["original"] if sorted_names else names[0]

