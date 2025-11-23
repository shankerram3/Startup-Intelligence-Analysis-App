"""
Entity Type Classification Refinement
Improve entity type classification with confidence scores and multi-signal analysis
"""

from typing import Dict, List, Tuple, Optional
import re
from collections import Counter


class EntityClassifier:
    """Refine entity type classification with confidence scores"""

    def __init__(self):
        # Keywords for each entity type
        self.type_keywords = {
            "company": [
                "company",
                "corporation",
                "corp",
                "inc",
                "llc",
                "ltd",
                "startup",
                "firm",
                "enterprise",
                "business",
                "organization",
                "co",
                "technologies",
                "systems",
                "solutions",
                "labs",
                "ventures",
            ],
            "person": [
                "founder",
                "ceo",
                "cto",
                "president",
                "director",
                "executive",
                "manager",
                "lead",
                "head",
                "chief",
                "officer",
                "vp",
                "investor",
                "partner",
                "co-founder",
            ],
            "investor": [
                "capital",
                "ventures",
                "partners",
                "fund",
                "investments",
                "investors",
                "group",
                "holdings",
                "management",
                "vc",
                "venture capital",
                "private equity",
                "angel",
            ],
            "technology": [
                "ai",
                "artificial intelligence",
                "machine learning",
                "blockchain",
                "cloud",
                "software",
                "platform",
                "system",
                "algorithm",
                "api",
                "framework",
                "protocol",
                "language",
                "tool",
            ],
            "product": [
                "app",
                "application",
                "service",
                "tool",
                "platform",
                "software",
                "system",
                "product",
                "solution",
                "device",
                "service",
            ],
            "location": [
                "city",
                "state",
                "country",
                "region",
                "area",
                "district",
                "valley",
                "bay",
                "coast",
                "island",
                "mountains",
            ],
            "event": [
                "conference",
                "summit",
                "event",
                "meeting",
                "show",
                "festival",
                "awards",
                "competition",
                "hackathon",
                "workshop",
                "seminar",
            ],
        }

    def refine_classification(
        self, entity: Dict, context: str = ""
    ) -> Tuple[str, float]:
        """
        Refine entity type classification with confidence score

        Args:
            entity: Entity dictionary with name, type, description
            context: Optional context string (article text)

        Returns:
            (refined_type, confidence_score) tuple
        """
        name = entity.get("name", "").lower()
        current_type = entity.get("type", "").lower()
        description = entity.get("description", "").lower()
        full_context = f"{name} {description} {context}".lower()

        # Calculate scores for each type
        type_scores = {}

        for entity_type, keywords in self.type_keywords.items():
            score = 0.0

            # Check name
            name_matches = sum(1 for kw in keywords if kw in name)
            score += name_matches * 2.0  # Name matches are strong signal

            # Check description
            desc_matches = sum(1 for kw in keywords if kw in description)
            score += desc_matches * 1.0

            # Check context
            if context:
                context_matches = sum(1 for kw in keywords if kw in context.lower())
                score += context_matches * 0.5

            type_scores[entity_type] = score

        # Special heuristics
        type_scores = self._apply_heuristics(name, description, type_scores)

        # Find best type
        best_type = max(type_scores.items(), key=lambda x: x[1])

        # Normalize confidence (0-1)
        total_score = sum(type_scores.values())
        if total_score > 0:
            confidence = best_type[1] / max(total_score, 1.0)
        else:
            confidence = 0.5  # Default confidence

        # If current type is close, boost its confidence
        if current_type in type_scores:
            current_score = type_scores[current_type]
            best_score = best_type[1]

            if current_score >= best_score * 0.8:  # Within 20% of best
                refined_type = current_type
                confidence = max(confidence, 0.7)  # Boost confidence
            else:
                refined_type = best_type[0]
        else:
            refined_type = best_type[0]

        return refined_type.upper(), min(1.0, confidence)

    def _apply_heuristics(self, name: str, description: str, scores: Dict) -> Dict:
        """Apply special heuristics for entity classification"""

        # Company vs Person: Check for titles
        person_titles = ["mr", "mrs", "ms", "dr", "professor", "prof"]
        if any(title in name for title in person_titles):
            scores["person"] += 5.0
            scores["company"] -= 2.0

        # Investor subtypes
        if "venture capital" in description or "vc" in description:
            scores["investor"] += 3.0

        if "angel" in description:
            scores["investor"] += 3.0

        if "corporate" in description:
            scores["investor"] += 2.0
            scores["company"] += 1.0

        # Technology vs Product
        if any(tech in description for tech in ["algorithm", "framework", "protocol"]):
            scores["technology"] += 2.0

        if any(prod in description for prod in ["app", "service", "platform"]):
            scores["product"] += 2.0

        # Location detection
        location_indicators = [
            "located",
            "based",
            "headquarters",
            "headquarters",
            "city",
            "country",
        ]
        if any(indicator in description for indicator in location_indicators):
            scores["location"] += 1.0

        # Event detection
        event_indicators = ["conference", "summit", "event", "meeting", "show"]
        if any(indicator in description for indicator in event_indicators):
            scores["event"] += 3.0

        return scores

    def classify_investor_subtype(self, investor: Dict) -> str:
        """
        Classify investor subtype (VC, Angel, Corporate, etc.)

        Args:
            investor: Investor entity dictionary

        Returns:
            Subtype string
        """
        description = investor.get("description", "").lower()
        name = investor.get("name", "").lower()

        # Check for keywords
        if "venture capital" in description or "vc" in name or "ventures" in name:
            return "VC"

        if "angel" in description or "angel" in name:
            return "Angel"

        if "corporate" in description or "corp" in name:
            return "Corporate"

        if "private equity" in description or "pe" in name:
            return "Private Equity"

        if "fund" in name:
            return "Fund"

        return "Unknown"

    def disambiguate_entity(
        self, entity: Dict, co_occurring_entities: List[Dict]
    ) -> Tuple[str, float]:
        """
        Disambiguate entity type using co-occurring entities

        Example: "Ford" could be Company (Ford Motor) or Person (Ford surname)

        Args:
            entity: Entity to disambiguate
            co_occurring_entities: List of other entities in same context

        Returns:
            (disambiguated_type, confidence) tuple
        """
        name = entity.get("name", "").lower()

        # Special cases
        if name in ["ford", "gates", "jobs", "bezos", "musk"]:
            # Check context: if surrounded by company indicators, it's a company
            # If surrounded by person indicators, it's a person
            company_indicators = sum(
                1
                for e in co_occurring_entities
                if e.get("type", "").lower() == "company"
            )
            person_indicators = sum(
                1
                for e in co_occurring_entities
                if e.get("type", "").lower() == "person"
            )

            if company_indicators > person_indicators:
                return "COMPANY", 0.7
            elif person_indicators > company_indicators:
                return "PERSON", 0.7
            else:
                # Default based on common knowledge
                if name in ["gates", "jobs", "bezos", "musk"]:
                    return "PERSON", 0.9
                else:
                    return "COMPANY", 0.9

        # Use default classification
        return self.refine_classification(entity)

    def get_classification_confidence(self, entity: Dict) -> Dict[str, float]:
        """
        Get confidence scores for all possible types

        Args:
            entity: Entity dictionary

        Returns:
            Dictionary mapping type -> confidence score
        """
        name = entity.get("name", "").lower()
        description = entity.get("description", "").lower()

        confidences = {}
        total_score = 0.0

        for entity_type, keywords in self.type_keywords.items():
            score = 0.0

            # Count keyword matches
            name_matches = sum(1 for kw in keywords if kw in name)
            desc_matches = sum(1 for kw in keywords if kw in description)

            score = (name_matches * 2.0) + (desc_matches * 1.0)
            confidences[entity_type] = score
            total_score += score

        # Normalize to 0-1
        if total_score > 0:
            for entity_type in confidences:
                confidences[entity_type] /= total_score

        return confidences
