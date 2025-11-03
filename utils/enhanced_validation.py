"""
Enhanced data validation with funding amounts, dates, and cross-referencing
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime


def validate_funding_amount(amount: str) -> Tuple[bool, Optional[str]]:
    """
    Validate and normalize funding amount
    
    Args:
        amount: Funding amount string (e.g., "$50M", "$50 million", "$50,000,000")
    
    Returns:
        (is_valid, normalized_amount_or_error) tuple
    """
    if not amount:
        return False, "Funding amount is empty"
    
    # Remove whitespace
    amount = amount.strip()
    
    # Extract number and unit
    # Patterns: $50M, $50 million, $50,000,000, $50M USD, 50M, etc.
    patterns = [
        r'\$?\s*([\d,]+\.?\d*)\s*(M|million|B|billion|K|thousand|k)?',
        r'([\d,]+\.?\d*)\s*(M|million|B|billion|K|thousand|k)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, amount, re.IGNORECASE)
        if match:
            number_str = match.group(1).replace(',', '')
            unit = match.group(2).upper() if match.group(2) else ''
            
            try:
                number = float(number_str)
                
                # Convert to millions
                if unit in ['B', 'BILLION']:
                    value_millions = number * 1000
                elif unit in ['K', 'THOUSAND']:
                    value_millions = number / 1000
                elif unit in ['M', 'MILLION'] or unit == '':
                    value_millions = number
                else:
                    value_millions = number
                
                # Validate range ($1M - $10B)
                if value_millions < 1:
                    return False, f"Funding amount too small: ${value_millions:.2f}M (minimum $1M)"
                if value_millions > 10000:
                    return False, f"Funding amount too large: ${value_millions:.2f}M (maximum $10B)"
                
                # Return normalized format
                normalized = f"${value_millions:.2f}M"
                return True, normalized
                
            except ValueError:
                return False, f"Invalid number format in funding amount: {amount}"
    
    return False, f"Could not parse funding amount: {amount}"


def validate_date_format(date_str: str, format_type: str = "iso") -> Tuple[bool, Optional[str]]:
    """
    Validate date format
    
    Args:
        date_str: Date string to validate
        format_type: Expected format ("iso", "any")
    
    Returns:
        (is_valid, error_message_or_normalized_date) tuple
    """
    if not date_str:
        return False, "Date is empty"
    
    date_str = date_str.strip()
    
    # Try ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
    iso_patterns = [
        r'^\d{4}-\d{2}-\d{2}$',
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[-+]\d{2}:\d{2}$',
    ]
    
    for pattern in iso_patterns:
        if re.match(pattern, date_str):
            try:
                # Parse and validate
                if 'T' in date_str:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                
                # Check reasonable date range (1990-2100)
                if dt.year < 1990:
                    return False, f"Date too old: {date_str} (minimum 1990)"
                if dt.year > 2100:
                    return False, f"Date too far in future: {date_str} (maximum 2100)"
                
                return True, date_str
                
            except ValueError:
                return False, f"Invalid date format: {date_str}"
    
    if format_type == "iso":
        return False, f"Date not in ISO format: {date_str}"
    
    # Try other common formats
    common_formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%B %d, %Y',
    ]
    
    for fmt in common_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if 1990 <= dt.year <= 2100:
                # Normalize to ISO
                normalized = dt.strftime('%Y-%m-%d')
                return True, normalized
        except ValueError:
            continue
    
    return False, f"Could not parse date: {date_str}"


def validate_entity_name_format(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate entity name format
    
    Args:
        name: Entity name to validate
    
    Returns:
        (is_valid, error_message) tuple
    """
    if not name:
        return False, "Entity name is empty"
    
    name = name.strip()
    
    # Check length
    if len(name) < 2:
        return False, f"Entity name too short: '{name}' (minimum 2 characters)"
    if len(name) > 200:
        return False, f"Entity name too long: '{name}' (maximum 200 characters)"
    
    # Check for proper capitalization (at least first letter should be capital)
    if not name[0].isupper():
        # Allow acronyms (all caps)
        if not name.isupper():
            return False, f"Entity name should start with capital letter: '{name}'"
    
    # Check for valid characters (letters, numbers, spaces, hyphens, apostrophes)
    if not re.match(r'^[A-Za-z0-9\s\-\'\.]+$', name):
        return False, f"Entity name contains invalid characters: '{name}'"
    
    return True, None


def validate_funding_round(round_info: Dict) -> Tuple[bool, List[str]]:
    """
    Validate funding round information
    
    Args:
        round_info: Dictionary with funding round details
    
    Returns:
        (is_valid, list_of_errors) tuple
    """
    errors = []
    
    # Validate amount if present
    if "amount" in round_info:
        is_valid, error = validate_funding_amount(round_info["amount"])
        if not is_valid:
            errors.append(f"Invalid funding amount: {error}")
    
    # Validate date if present
    if "date" in round_info:
        is_valid, error = validate_date_format(round_info["date"])
        if not is_valid:
            errors.append(f"Invalid funding date: {error}")
    
    # Validate round type if present
    if "type" in round_info:
        valid_types = ["Seed", "Series A", "Series B", "Series C", "Series D", 
                      "Series E", "Pre-Seed", "Angel", "Bridge", "IPO"]
        round_type = round_info["type"]
        if round_type not in valid_types:
            errors.append(f"Invalid funding round type: {round_type}")
    
    return len(errors) == 0, errors


def cross_reference_entity(entity: Dict, known_entities: List[Dict]) -> Tuple[bool, Optional[str]]:
    """
    Cross-reference entity against known entities list
    
    Args:
        entity: Entity to check
        known_entities: List of known valid entities
    
    Returns:
        (is_known, matching_entity_name) tuple
    """
    entity_name = entity.get("name", "").upper()
    
    for known in known_entities:
        known_name = known.get("name", "").upper()
        if known_name == entity_name:
            return True, known.get("name")
        
        # Check aliases if present
        aliases = known.get("aliases", [])
        for alias in aliases:
            if alias.upper() == entity_name:
                return True, known.get("name")
    
    return False, None


def validate_extraction_enhanced(extraction: Dict, known_entities: Optional[List[Dict]] = None) -> Tuple[bool, List[str]]:
    """
    Enhanced extraction validation with funding amounts, dates, etc.
    
    Args:
        extraction: Extraction dictionary
        known_entities: Optional list of known valid entities for cross-referencing
    
    Returns:
        (is_valid, list_of_errors) tuple
    """
    errors = []
    
    entities = extraction.get("entities", [])
    relationships = extraction.get("relationships", [])
    
    # Validate entity names
    for i, entity in enumerate(entities):
        name = entity.get("name", "")
        is_valid, error = validate_entity_name_format(name)
        if not is_valid:
            errors.append(f"Entity {i} name format error: {error}")
        
        # Cross-reference if known entities provided
        if known_entities:
            is_known, canonical_name = cross_reference_entity(entity, known_entities)
            if not is_known and canonical_name:
                # Suggest canonical name
                errors.append(f"Entity {i} ('{name}') not in known entities, did you mean '{canonical_name}'?")
    
    # Validate funding amounts in relationships
    for i, rel in enumerate(relationships):
        if "amount" in rel:
            is_valid, error = validate_funding_amount(rel["amount"])
            if not is_valid:
                errors.append(f"Relationship {i} funding amount error: {error}")
        
        if "date" in rel:
            is_valid, error = validate_date_format(rel["date"])
            if not is_valid:
                errors.append(f"Relationship {i} date error: {error}")
    
    return len(errors) == 0, errors

