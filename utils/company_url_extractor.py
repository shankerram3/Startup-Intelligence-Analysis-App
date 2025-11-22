"""
Company URL Extractor
Extracts company website URLs from article content and entity mentions
"""

import logging
import re
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class CompanyURLExtractor:
    """Extract company website URLs from articles and associate with entities"""

    def __init__(self):
        # Common URL patterns in article content
        self.url_pattern = re.compile(
            r"https?://(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?)"
            r"(?:/[^\s\)\]\"\'\<]*)?",
            re.IGNORECASE,
        )

        # Domains to exclude (TechCrunch, social media, etc.)
        self.excluded_domains = {
            "techcrunch.com",
            "crunchbase.com",
            "twitter.com",
            "x.com",
            "facebook.com",
            "linkedin.com",
            "instagram.com",
            "youtube.com",
            "tiktok.com",
            "reddit.com",
            "medium.com",
            "substack.com",
            "apple.com",
            "google.com",
            "microsoft.com",
            "amazon.com",
            "github.com",
            "gitlab.com",
            "bitbucket.org",
            "wsj.com",
            "nytimes.com",
            "bloomberg.com",
            "forbes.com",
            "reuters.com",
            "apnews.com",
            "bbc.com",
            "cnn.com",
            "yahoo.com",
            "bing.com",
            "duckduckgo.com",
            "wikipedia.org",
            "wikimedia.org",
        }

    def extract_urls_from_article(self, article_data: Dict) -> List[str]:
        """
        Extract all potential company URLs from article content

        Args:
            article_data: Article JSON with content field

        Returns:
            List of unique, filtered URLs
        """
        urls = set()

        # Extract from article body text
        content = article_data.get("content", {})
        body_text = content.get("body_text", "")

        if body_text:
            found_urls = self.url_pattern.findall(body_text)
            urls.update(found_urls)

        # Extract from paragraphs
        paragraphs = content.get("paragraphs", [])
        for para in paragraphs:
            if isinstance(para, str):
                found_urls = self.url_pattern.findall(para)
                urls.update(found_urls)

        # Filter and normalize
        filtered_urls = self._filter_and_normalize_urls(urls)

        return list(filtered_urls)

    def _filter_and_normalize_urls(self, urls: Set[str]) -> Set[str]:
        """Filter out excluded domains and normalize URLs"""
        normalized = set()

        for url in urls:
            # Ensure it has a scheme
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()

                # Remove www. prefix for comparison
                clean_domain = domain.replace("www.", "")

                # Skip excluded domains
                if any(excluded in clean_domain for excluded in self.excluded_domains):
                    continue

                # Skip URLs with paths that look like articles/blog posts
                path = parsed.path.lower()
                if any(
                    keyword in path
                    for keyword in [
                        "/blog/",
                        "/news/",
                        "/press/",
                        "/article/",
                        "/post/",
                        "/category/",
                    ]
                ):
                    # Only include base domain
                    normalized.add(f"{parsed.scheme}://{domain}")
                else:
                    # Include full URL
                    normalized.add(url)

            except Exception as e:
                logger.warning(f"Failed to parse URL {url}: {e}")
                continue

        return normalized

    def match_urls_to_companies(
        self, article_data: Dict, extraction_data: Dict, urls: List[str]
    ) -> Dict[str, Optional[str]]:
        """
        Match extracted URLs to company entities mentioned in the article

        Args:
            article_data: Article JSON
            extraction_data: Extraction JSON with entities
            urls: List of URLs extracted from article

        Returns:
            Dictionary mapping company names to their URLs
        """
        company_urls = {}

        # Get all company entities
        entities = extraction_data.get("entities", [])
        companies = [e for e in entities if e.get("type", "").lower() == "company"]

        if not companies:
            return company_urls

        # Get article text for context matching
        content = article_data.get("content", {})
        body_text = content.get("body_text", "").lower()
        paragraphs = content.get("paragraphs", [])

        # Try to match each URL to a company
        for url in urls:
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.replace("www.", "").lower()
                domain_parts = domain.split(".")[
                    0
                ]  # e.g., 'anthropic' from 'anthropic.com'

                # Find best matching company
                best_match = None
                best_score = 0

                for company in companies:
                    company_name = company.get("name", "").lower()
                    normalized_name = company.get("normalized_name", "").lower()

                    # Check if domain contains company name or vice versa
                    score = 0

                    # Exact domain match
                    if domain_parts in company_name or company_name in domain_parts:
                        score = 10
                    # Normalized name match
                    elif (
                        domain_parts in normalized_name
                        or normalized_name in domain_parts
                    ):
                        score = 8
                    # Check if URL appears near company mention in text
                    elif self._check_proximity_in_text(
                        company_name, url, body_text, paragraphs
                    ):
                        score = 6

                    if score > best_score:
                        best_score = score
                        best_match = company.get("name")

                # Assign URL to company if good match
                if best_match and best_score >= 6:
                    # If company already has a URL, keep the one with higher score
                    if best_match not in company_urls:
                        company_urls[best_match] = url

            except Exception as e:
                logger.warning(f"Failed to match URL {url}: {e}")
                continue

        # Log unmatched companies for debugging
        unmatched = [
            c.get("name") for c in companies if c.get("name") not in company_urls
        ]
        if unmatched:
            logger.debug(f"Companies without URLs: {unmatched}")

        return company_urls

    def _check_proximity_in_text(
        self,
        company_name: str,
        url: str,
        body_text: str,
        paragraphs: List[str],
        proximity_window: int = 200,
    ) -> bool:
        """
        Check if URL appears near company name in text

        Args:
            company_name: Name of the company
            url: URL to check
            body_text: Full article text
            paragraphs: List of paragraphs
            proximity_window: Character window to check around company mention

        Returns:
            True if URL is near company mention
        """
        # Check in full text
        company_pos = body_text.find(company_name)
        url_pos = body_text.find(url)

        if company_pos != -1 and url_pos != -1:
            if abs(company_pos - url_pos) < proximity_window:
                return True

        # Check if they appear in the same paragraph
        for para in paragraphs:
            if isinstance(para, str):
                para_lower = para.lower()
                if company_name in para_lower and url in para_lower:
                    return True

        return False

    def extract_and_match(
        self, article_data: Dict, extraction_data: Dict
    ) -> Dict[str, str]:
        """
        Complete workflow: extract URLs and match to companies

        Args:
            article_data: Article JSON
            extraction_data: Extraction JSON

        Returns:
            Dictionary mapping company names to URLs
        """
        urls = self.extract_urls_from_article(article_data)

        if not urls:
            logger.debug(f"No URLs found in article {article_data.get('article_id')}")
            return {}

        company_urls = self.match_urls_to_companies(article_data, extraction_data, urls)

        logger.info(
            f"Article {article_data.get('article_id')}: "
            f"Found {len(urls)} URLs, matched {len(company_urls)} to companies"
        )

        return company_urls


def extract_company_urls_from_extractions(
    extractions: List[Dict], articles_dir: str
) -> Dict[str, Dict[str, str]]:
    """
    Process all extractions and extract company URLs

    Args:
        extractions: List of extraction dictionaries
        articles_dir: Directory containing article JSON files

    Returns:
        Dictionary mapping article_id -> {company_name: url}
    """
    import json
    import os
    from pathlib import Path

    extractor = CompanyURLExtractor()
    all_company_urls = {}

    for extraction in extractions:
        article_metadata = extraction.get("article_metadata", {})
        article_id = article_metadata.get("article_id")

        if not article_id:
            continue

        # Load full article data
        article_file = None
        for root, dirs, files in os.walk(articles_dir):
            for file in files:
                if file == f"tc_{article_id}.json":
                    article_file = os.path.join(root, file)
                    break
            if article_file:
                break

        if not article_file:
            logger.warning(f"Article file not found for {article_id}")
            continue

        try:
            with open(article_file, "r", encoding="utf-8") as f:
                article_data = json.load(f)

            # Extract and match URLs
            company_urls = extractor.extract_and_match(article_data, extraction)

            if company_urls:
                all_company_urls[article_id] = company_urls

        except Exception as e:
            logger.error(f"Failed to process article {article_id}: {e}")
            continue

    logger.info(
        f"Extracted URLs for {len(all_company_urls)} articles, "
        f"{sum(len(urls) for urls in all_company_urls.values())} total company URLs"
    )

    return all_company_urls
