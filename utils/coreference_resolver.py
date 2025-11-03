"""
Coreference Resolution
Resolve pronouns and references in text to improve entity extraction
"""

import re
from typing import Dict, List, Optional, Tuple


class CoreferenceResolver:
    """Resolve pronouns and references in text"""
    
    def __init__(self):
        self.entity_cache = {}  # Cache resolved entities
    
    def resolve_references(self, text: str, entities: List[Dict]) -> str:
        """
        Resolve pronouns and references in text
        
        Args:
            text: Original text
            entities: List of extracted entities
        
        Returns:
            Text with resolved references
        """
        if not text or not entities:
            return text
        
        resolved_text = text
        
        # Create entity map (name -> entity)
        entity_map = {}
        for entity in entities:
            name = entity.get("name", "")
            entity_type = entity.get("type", "").lower()
            entity_map[name.lower()] = entity
            entity_map[entity_type] = entity  # Also map by type
        
        # Common patterns
        patterns = [
            # "The company" -> entity name
            (r'\bthe company\b', lambda m: self._find_last_entity(entities, "company")),
            
            # "The startup" -> entity name
            (r'\bthe startup\b', lambda m: self._find_last_entity(entities, "company")),
            
            # "The firm" -> entity name
            (r'\bthe firm\b', lambda m: self._find_last_entity(entities, "company")),
            
            # "He/She" -> person name
            (r'\b(he|she)\b', lambda m: self._find_last_entity(entities, "person")),
            
            # "They" -> entity name (company or team)
            (r'\bthey\b', lambda m: self._find_last_entity(entities, "company")),
            
            # "It" -> entity name
            (r'\bit\b', lambda m: self._find_last_entity(entities)),
        ]
        
        for pattern, replacement_func in patterns:
            matches = list(re.finditer(pattern, resolved_text, re.IGNORECASE))
            # Process from end to beginning to preserve indices
            for match in reversed(matches):
                replacement = replacement_func(match)
                if replacement:
                    start, end = match.span()
                    resolved_text = resolved_text[:start] + replacement + resolved_text[end:]
        
        return resolved_text
    
    def _find_last_entity(self, entities: List[Dict], entity_type: Optional[str] = None) -> Optional[str]:
        """
        Find the most recently mentioned entity of given type
        
        Args:
            entities: List of entities
            entity_type: Optional entity type filter
        
        Returns:
            Entity name or None
        """
        if not entities:
            return None
        
        # Filter by type if specified
        if entity_type:
            filtered = [e for e in entities if e.get("type", "").lower() == entity_type.lower()]
            if filtered:
                # Return last one (most recent)
                return filtered[-1].get("name")
        
        # Return last entity overall
        return entities[-1].get("name") if entities else None
    
    def resolve_pronouns_in_sentence(self, sentence: str, previous_sentences: List[str], 
                                     entities: List[Dict]) -> str:
        """
        Resolve pronouns in a sentence using context from previous sentences
        
        Args:
            sentence: Current sentence
            previous_sentences: List of previous sentences for context
            entities: List of entities mentioned so far
        
        Returns:
            Sentence with resolved pronouns
        """
        resolved = sentence
        
        # Check for pronouns
        pronouns = {
            "he": self._find_last_entity(entities, "person"),
            "she": self._find_last_entity(entities, "person"),
            "they": self._find_last_entity(entities, "company") or self._find_last_entity(entities),
            "it": self._find_last_entity(entities),
            "the company": self._find_last_entity(entities, "company"),
            "the startup": self._find_last_entity(entities, "company"),
            "the firm": self._find_last_entity(entities, "company"),
        }
        
        for pronoun, replacement in pronouns.items():
            if replacement:
                # Replace pronoun with entity name (case-aware)
                pattern = r'\b' + re.escape(pronoun) + r'\b'
                resolved = re.sub(pattern, replacement, resolved, flags=re.IGNORECASE)
        
        return resolved
    
    def enhance_text_for_extraction(self, text: str, entities: List[Dict]) -> str:
        """
        Enhance text for better entity extraction by resolving references
        
        Args:
            text: Original text
            entities: Entities already extracted or known
        
        Returns:
            Enhanced text with resolved references
        """
        if not text:
            return text
        
        # Split into sentences
        sentences = re.split(r'[.!?]+\s+', text)
        
        resolved_sentences = []
        accumulated_entities = []
        
        for i, sentence in enumerate(sentences):
            # Resolve references using previous context
            resolved = self.resolve_pronouns_in_sentence(
                sentence, sentences[:i], accumulated_entities
            )
            
            resolved_sentences.append(resolved)
            
            # Update accumulated entities (would need to re-extract, simplified here)
            # In practice, you'd extract entities from resolved sentence
            
        return '. '.join(resolved_sentences) + '.'
    
    def find_coreference_chains(self, text: str, entities: List[Dict]) -> List[List[str]]:
        """
        Find coreference chains (groups of mentions referring to same entity)
        
        Args:
            text: Original text
            entities: List of entities
        
        Returns:
            List of coreference chains (each chain is list of mentions)
        """
        chains = []
        entity_names = [e.get("name", "").lower() for e in entities]
        
        # Find all mentions of each entity
        for entity in entities:
            name = entity.get("name", "")
            chain = [name]
            
            # Find variations and references
            variations = self._find_variations(name, text)
            chain.extend(variations)
            
            if len(chain) > 1:
                chains.append(chain)
        
        return chains
    
    def _find_variations(self, entity_name: str, text: str) -> List[str]:
        """Find variations and references to entity name in text"""
        variations = []
        name_lower = entity_name.lower()
        
        # Check for abbreviated versions
        words = name_lower.split()
        if len(words) > 1:
            # First word
            if len(words[0]) > 3:
                variations.append(words[0])
            # Acronym
            acronym = ''.join([w[0] for w in words])
            if acronym in text.lower():
                variations.append(acronym)
        
        # Check for "the company", "the startup" patterns near entity
        # This is simplified - full implementation would use NLP library
        pattern = rf'\b{re.escape(name_lower)}\b.*?(?:the company|the startup|the firm)'
        if re.search(pattern, text.lower()):
            variations.append("the company")
        
        return variations

