"""
Company Intelligence Aggregator
Merges company intelligence from multiple sources (articles, scraped websites)
and prepares enriched data for the knowledge graph
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CompanyIntelligenceAggregator:
    """
    Aggregates and merges company intelligence from multiple sources
    """

    def __init__(self):
        self.confidence_weights = {
            "website_scrape": 0.8,
            "article_mention": 0.6,
            "inferred": 0.3,
        }

    def aggregate_company_intelligence(
        self,
        company_name: str,
        article_mentions: List[Dict],
        scraped_intelligence: Optional[Dict] = None,
    ) -> Dict:
        """
        Aggregate intelligence for a single company from multiple sources

        Args:
            company_name: Name of the company
            article_mentions: List of article extraction data mentioning the company
            scraped_intelligence: Scraped website intelligence (if available)

        Returns:
            Enriched company data dictionary
        """
        enriched = {
            "company_name": company_name,
            "enrichment_timestamp": datetime.utcnow().isoformat(),
            "sources": [],
            "confidence_score": 0.0,
            "data": {
                "website_url": None,
                "founded_year": None,
                "employee_count": None,
                "headquarters": None,
                "description": None,
                "founders": [],
                "executives": [],
                "products": [],
                "technologies": [],
                "funding_total": None,
                "funding_stage": None,
                "pricing_model": None,
                "social_links": {},
            },
            "field_confidence": {},
        }

        # Aggregate from article mentions
        article_data = self._aggregate_from_articles(article_mentions)
        if article_data:
            enriched["sources"].append(
                {
                    "type": "articles",
                    "count": len(article_mentions),
                    "article_ids": [m.get("article_id") for m in article_mentions],
                }
            )

        # Aggregate from scraped website
        website_data = None
        if scraped_intelligence:
            website_data = self._aggregate_from_website(scraped_intelligence)
            enriched["sources"].append(
                {
                    "type": "website_scrape",
                    "url": scraped_intelligence.get("website_url"),
                    "scraped_at": scraped_intelligence.get("scraped_at"),
                }
            )

        # Merge data with conflict resolution
        enriched["data"] = self._merge_data_sources(article_data, website_data)

        # Calculate field-level confidence scores
        enriched["field_confidence"] = self._calculate_field_confidence(
            enriched["data"], article_data, website_data
        )

        # Calculate overall confidence score
        enriched["confidence_score"] = self._calculate_overall_confidence(
            enriched["field_confidence"]
        )

        return enriched

    def _aggregate_from_articles(self, article_mentions: List[Dict]) -> Dict:
        """Extract intelligence from article mentions"""
        data = {
            "description": [],
            "relationships": [],
            "mentions_count": len(article_mentions),
        }

        for mention in article_mentions:
            # Collect descriptions
            if "description" in mention:
                data["description"].append(mention["description"])

            # Collect relationships
            if "relationships" in mention:
                data["relationships"].extend(mention["relationships"])

        # Merge descriptions
        if data["description"]:
            data["description"] = " ".join(data["description"])
        else:
            data["description"] = None

        return data

    def _aggregate_from_website(self, scraped_data: Dict) -> Dict:
        """Extract intelligence from scraped website data"""
        if not scraped_data:
            return {}

        extracted = scraped_data.get("extracted_data", {})

        data = {
            "website_url": scraped_data.get("website_url"),
            "founded_year": extracted.get("founded_year"),
            "employee_count": extracted.get("employee_count"),
            "headquarters": extracted.get("headquarters"),
            "description": extracted.get("description"),
            "founders": extracted.get("founders", []),
            "executives": extracted.get("executives", []),
            "products": extracted.get("products", []),
            "technologies": extracted.get("technologies", []),
            "pricing_model": extracted.get("pricing_model"),
            "funding_announcements": extracted.get("funding_announcements", []),
        }

        return data

    def _merge_data_sources(
        self, article_data: Optional[Dict], website_data: Optional[Dict]
    ) -> Dict:
        """
        Merge data from articles and website with conflict resolution

        Priority: website_data > article_data (website is more authoritative)
        """
        merged = {
            "website_url": None,
            "founded_year": None,
            "employee_count": None,
            "headquarters": None,
            "description": None,
            "founders": [],
            "executives": [],
            "products": [],
            "technologies": [],
            "funding_total": None,
            "funding_stage": None,
            "pricing_model": None,
            "social_links": {},
        }

        # Simple fields: prefer website data
        if website_data:
            merged["website_url"] = website_data.get("website_url")
            merged["founded_year"] = website_data.get("founded_year")
            merged["employee_count"] = website_data.get("employee_count")
            merged["headquarters"] = website_data.get("headquarters")
            merged["pricing_model"] = website_data.get("pricing_model")

            # For description, prefer website but combine if both exist
            if website_data.get("description"):
                merged["description"] = website_data["description"]
            elif article_data and article_data.get("description"):
                merged["description"] = article_data["description"]

            # Lists: merge and deduplicate
            merged["founders"] = list(set(website_data.get("founders", [])))
            merged["executives"] = website_data.get("executives", [])
            merged["products"] = list(set(website_data.get("products", [])))
            merged["technologies"] = list(set(website_data.get("technologies", [])))

            # Extract funding info from announcements
            funding_announcements = website_data.get("funding_announcements", [])
            if funding_announcements:
                # Get most recent/largest funding
                for announcement in funding_announcements:
                    if announcement.get("type") == "funding":
                        merged["funding_total"] = announcement.get("amount")
                        merged["funding_stage"] = announcement.get("round")
                        break

        elif article_data:
            # Fallback to article data if no website data
            merged["description"] = article_data.get("description")

        return merged

    def _calculate_field_confidence(
        self,
        merged_data: Dict,
        article_data: Optional[Dict],
        website_data: Optional[Dict],
    ) -> Dict:
        """
        Calculate confidence scores for each field

        Returns:
            Dictionary mapping field names to confidence scores (0-1)
        """
        confidence = {}

        for field, value in merged_data.items():
            if value is None or (isinstance(value, (list, dict)) and not value):
                confidence[field] = 0.0
                continue

            # Determine source of data
            if website_data and website_data.get(field) == value:
                confidence[field] = self.confidence_weights["website_scrape"]
            elif article_data and article_data.get(field) == value:
                confidence[field] = self.confidence_weights["article_mention"]
            else:
                confidence[field] = self.confidence_weights["inferred"]

        return confidence

    def _calculate_overall_confidence(self, field_confidence: Dict) -> float:
        """
        Calculate overall confidence score based on field-level confidence

        Args:
            field_confidence: Dictionary of field confidence scores

        Returns:
            Overall confidence score (0-1)
        """
        if not field_confidence:
            return 0.0

        # Weight important fields more heavily
        field_weights = {
            "website_url": 2.0,
            "founded_year": 1.5,
            "description": 1.5,
            "headquarters": 1.0,
            "employee_count": 1.0,
            "founders": 1.5,
            "technologies": 1.0,
            "products": 1.0,
            "funding_total": 1.5,
            "pricing_model": 0.5,
        }

        weighted_sum = 0.0
        weight_total = 0.0

        for field, confidence in field_confidence.items():
            weight = field_weights.get(field, 1.0)
            weighted_sum += confidence * weight
            weight_total += weight

        return weighted_sum / weight_total if weight_total > 0 else 0.0

    def aggregate_all_companies(
        self, extractions: List[Dict], intelligence_dir: str
    ) -> Dict[str, Dict]:
        """
        Aggregate intelligence for all companies across all articles

        Args:
            extractions: List of extraction dictionaries
            intelligence_dir: Directory containing scraped intelligence JSON files

        Returns:
            Dictionary mapping company names to enriched data
        """
        intelligence_path = Path(intelligence_dir)

        # Build map of company mentions from articles
        company_mentions = {}

        for extraction in extractions:
            article_id = extraction.get("article_metadata", {}).get("article_id")
            entities = extraction.get("entities", [])

            for entity in entities:
                if entity.get("type", "").lower() != "company":
                    continue

                company_name = entity.get("name")
                if not company_name:
                    continue

                if company_name not in company_mentions:
                    company_mentions[company_name] = []

                company_mentions[company_name].append(
                    {
                        "article_id": article_id,
                        "description": entity.get("description"),
                        "normalized_name": entity.get("normalized_name"),
                    }
                )

        # Load scraped intelligence
        scraped_intelligence = {}
        if intelligence_path.exists():
            for intelligence_file in intelligence_path.glob("*.json"):
                try:
                    with open(intelligence_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        company_name = data.get("company_name")
                        if company_name:
                            scraped_intelligence[company_name] = data
                except Exception as e:
                    logger.warning(
                        f"Failed to load intelligence file {intelligence_file}: {e}"
                    )

        # Aggregate intelligence for each company
        enriched_companies = {}

        for company_name, mentions in company_mentions.items():
            scraped_data = scraped_intelligence.get(company_name)

            enriched = self.aggregate_company_intelligence(
                company_name, mentions, scraped_data
            )

            enriched_companies[company_name] = enriched

        logger.info(
            f"Aggregated intelligence for {len(enriched_companies)} companies. "
            f"{len(scraped_intelligence)} had scraped website data."
        )

        return enriched_companies

    def save_aggregated_intelligence(
        self, enriched_companies: Dict[str, Dict], output_file: str
    ):
        """
        Save aggregated intelligence to JSON file

        Args:
            enriched_companies: Dictionary of enriched company data
            output_file: Path to output file
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(enriched_companies, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved aggregated intelligence to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save aggregated intelligence: {e}")


def create_enrichment_summary(enriched_companies: Dict[str, Dict]) -> Dict:
    """
    Create a summary of the enrichment results

    Args:
        enriched_companies: Dictionary of enriched company data

    Returns:
        Summary statistics
    """
    summary = {
        "total_companies": len(enriched_companies),
        "companies_with_website": 0,
        "companies_with_founded_year": 0,
        "companies_with_headquarters": 0,
        "companies_with_founders": 0,
        "companies_with_funding": 0,
        "average_confidence": 0.0,
        "high_confidence_companies": 0,  # > 0.7
        "medium_confidence_companies": 0,  # 0.4 - 0.7
        "low_confidence_companies": 0,  # < 0.4
    }

    confidence_scores = []

    for company_name, data in enriched_companies.items():
        company_data = data.get("data", {})
        confidence = data.get("confidence_score", 0.0)
        confidence_scores.append(confidence)

        if company_data.get("website_url"):
            summary["companies_with_website"] += 1
        if company_data.get("founded_year"):
            summary["companies_with_founded_year"] += 1
        if company_data.get("headquarters"):
            summary["companies_with_headquarters"] += 1
        if company_data.get("founders"):
            summary["companies_with_founders"] += 1
        if company_data.get("funding_total"):
            summary["companies_with_funding"] += 1

        # Confidence categories
        if confidence > 0.7:
            summary["high_confidence_companies"] += 1
        elif confidence > 0.4:
            summary["medium_confidence_companies"] += 1
        else:
            summary["low_confidence_companies"] += 1

    if confidence_scores:
        summary["average_confidence"] = sum(confidence_scores) / len(confidence_scores)

    return summary
