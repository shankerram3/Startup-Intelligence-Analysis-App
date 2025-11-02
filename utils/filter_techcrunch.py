"""
Utility functions to filter out TechCrunch/TechCrunch Disrupt related entities
Prevents TechCrunch/Disrupt nodes from being created in the graph
"""

import re
from typing import Tuple


def is_techcrunch_related(name: str) -> bool:
    """
    Check if an entity name is related to TechCrunch or TechCrunch Disrupt
    
    Args:
        name: Entity name to check
    
    Returns:
        True if entity is TechCrunch/Disrupt related, False otherwise
    """
    if not name:
        return False
    
    name_upper = name.upper()
    
    # Patterns to match TechCrunch or TechCrunch Disrupt
    techcrunch_patterns = [
        r'.*TECHCRUNCH.*DISRUPT.*',
        r'.*TECHCRUNCH DISRUPT.*',
        r'^TECHCRUNCH$',
        r'^TECHCRUNCH ',
        r'.*TECHCRUNCH.*',
    ]
    
    # Patterns to match TechCrunch Disrupt events/stages
    disrupt_patterns = [
        r'^STARTUP BATTLEFIELD.*',
        r'.*BATTLEFIELD.*',
        r'^DISRUPT.*',
        r'.*DISRUPT.*',
    ]
    
    # Check against TechCrunch patterns
    for pattern in techcrunch_patterns:
        if re.match(pattern, name_upper):
            return True
    
    # Check against Disrupt/Battlefield patterns (TechCrunch Disrupt related)
    for pattern in disrupt_patterns:
        if re.match(pattern, name_upper):
            return True
    
    return False


def filter_techcrunch_entity(entity: dict) -> Tuple[bool, str]:
    """
    Check if an entity should be filtered out (TechCrunch/Disrupt related)
    
    Args:
        entity: Entity dictionary with 'name' key
    
    Returns:
        (should_filter, reason) tuple
    """
    if not entity or not isinstance(entity, dict):
        return False, ""
    
    name = entity.get("name", "")
    if not name:
        return False, ""
    
    if is_techcrunch_related(name):
        return True, f"Entity '{name}' is TechCrunch/TechCrunch Disrupt related and should not be added to graph"
    
    return False, ""


def filter_techcrunch_entities(entities: list) -> Tuple[list, list]:
    """
    Filter out TechCrunch/Disrupt related entities
    
    Args:
        entities: List of entity dictionaries
    
    Returns:
        (filtered_entities, filtered_names) tuple
    """
    filtered_entities = []
    filtered_names = []
    
    for entity in entities:
        should_filter, reason = filter_techcrunch_entity(entity)
        if should_filter:
            filtered_names.append(entity.get("name", "Unknown"))
        else:
            filtered_entities.append(entity)
    
    return filtered_entities, filtered_names


def filter_techcrunch_relationship(relationship: dict) -> Tuple[bool, str]:
    """
    Check if a relationship involves TechCrunch/Disrupt entities
    
    Args:
        relationship: Relationship dictionary with 'source' and 'target' keys
    
    Returns:
        (should_filter, reason) tuple
    """
    if not relationship or not isinstance(relationship, dict):
        return False, ""
    
    source = relationship.get("source", "")
    target = relationship.get("target", "")
    
    source_filtered = is_techcrunch_related(source)
    target_filtered = is_techcrunch_related(target)
    
    if source_filtered or target_filtered:
        reason = f"Relationship involves TechCrunch/Disrupt entity: {source} -> {target}"
        return True, reason
    
    return False, ""

