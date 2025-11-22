"""
Company Intelligence Scraper using Playwright
Extracts detailed company information from company websites
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

try:
    from playwright.async_api import Browser, Page, async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning(
        "Playwright not available. Install with: pip install playwright && playwright install"
    )

logger = logging.getLogger(__name__)


class CompanyIntelligenceScraper:
    """
    Scrapes detailed company intelligence from company websites using Playwright
    """

    def __init__(
        self,
        output_dir: str = "data/company_intelligence",
        rate_limit_delay: float = 0.5,
        timeout: int = 30000,
        headless: bool = True,
    ):
        """
        Initialize the company intelligence scraper

        Args:
            output_dir: Directory to save scraped intelligence
            rate_limit_delay: Delay between requests in seconds
            timeout: Page load timeout in milliseconds
            headless: Run browser in headless mode
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is required. Install with: pip install playwright && playwright install"
            )

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.headless = headless

        # Common page paths to scrape
        self.page_paths = [
            "",  # Homepage
            "/about",
            "/about-us",
            "/company",
            "/team",
            "/our-team",
            "/people",
            "/careers",
            "/jobs",
            "/press",
            "/news",
            "/newsroom",
            "/blog",
            "/products",
            "/solutions",
            "/pricing",
        ]

        # Stats
        self.stats = {"companies_scraped": 0, "pages_scraped": 0, "failed_scrapes": 0}

    async def scrape_company(
        self, company_name: str, company_url: str, article_id: str
    ) -> Optional[Dict]:
        """
        Scrape intelligence for a single company

        Args:
            company_name: Name of the company
            company_url: Company website URL
            article_id: Source article ID

        Returns:
            Dictionary containing scraped intelligence
        """
        logger.info(f"Scraping intelligence for {company_name} from {company_url}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)

            try:
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                )

                intelligence = {
                    "company_name": company_name,
                    "website_url": company_url,
                    "source_article_id": article_id,
                    "scraped_at": datetime.utcnow().isoformat(),
                    "pages_scraped": {},
                    "extracted_data": {},
                }

                # Try to scrape different pages
                for path in self.page_paths:
                    url = urljoin(company_url, path)

                    try:
                        page = await context.new_page()
                        page_data = await self._scrape_page(page, url, company_name)

                        if page_data:
                            page_key = path if path else "homepage"
                            intelligence["pages_scraped"][page_key] = {
                                "url": url,
                                "success": True,
                                "data": page_data,
                            }
                            self.stats["pages_scraped"] += 1
                        else:
                            intelligence["pages_scraped"][
                                path if path else "homepage"
                            ] = {"url": url, "success": False}

                        await page.close()
                        await asyncio.sleep(self.rate_limit_delay)

                    except Exception as e:
                        logger.debug(f"Failed to scrape {url}: {e}")
                        intelligence["pages_scraped"][path if path else "homepage"] = {
                            "url": url,
                            "success": False,
                            "error": str(e),
                        }
                        continue

                # Aggregate extracted data
                intelligence["extracted_data"] = self._aggregate_intelligence(
                    intelligence["pages_scraped"]
                )

                await context.close()
                self.stats["companies_scraped"] += 1

                # Save to file
                self._save_intelligence(company_name, article_id, intelligence)

                return intelligence

            except Exception as e:
                logger.error(f"Failed to scrape {company_name}: {e}")
                self.stats["failed_scrapes"] += 1
                return None
            finally:
                await browser.close()

    async def _scrape_page(
        self, page: Page, url: str, company_name: str
    ) -> Optional[Dict]:
        """
        Scrape a single page and extract relevant information

        Args:
            page: Playwright page object
            url: URL to scrape
            company_name: Company name for context

        Returns:
            Dictionary of extracted data
        """
        try:
            # Navigate to page
            response = await page.goto(
                url, timeout=self.timeout, wait_until="networkidle"
            )

            if not response or response.status != 200:
                return None

            # Wait for content to load
            await page.wait_for_timeout(1000)

            # Extract page data
            data = {
                "title": await page.title(),
                "url": url,
                "text_content": None,
                "structured_data": {},
            }

            # Get main text content
            data["text_content"] = await page.evaluate(
                """() => {
                // Remove scripts, styles, and other non-content elements
                const unwanted = document.querySelectorAll('script, style, nav, header, footer, iframe, noscript');
                unwanted.forEach(el => el.remove());

                // Get main content
                const main = document.querySelector('main') || document.body;
                return main ? main.innerText : '';
            }"""
            )

            # Extract structured data based on page type
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()

            if "about" in path or "company" in path or path == "/":
                data["structured_data"]["about"] = await self._extract_about_info(
                    page, data["text_content"]
                )

            if "team" in path or "people" in path or "about" in path:
                data["structured_data"]["team"] = await self._extract_team_info(
                    page, data["text_content"]
                )

            if "press" in path or "news" in path or "blog" in path:
                data["structured_data"]["news"] = await self._extract_news_info(
                    page, data["text_content"]
                )

            if "product" in path or "solution" in path or path == "/":
                data["structured_data"]["products"] = await self._extract_product_info(
                    page, data["text_content"]
                )

            if "pricing" in path:
                data["structured_data"]["pricing"] = await self._extract_pricing_info(
                    page, data["text_content"]
                )

            return data

        except Exception as e:
            logger.debug(f"Error scraping page {url}: {e}")
            return None

    async def _extract_about_info(self, page: Page, text: str) -> Dict:
        """Extract company about information"""
        info = {}

        # Extract founding year
        year_pattern = r"(?:founded|established|started|since)\s+(?:in\s+)?(\d{4})"
        year_match = re.search(year_pattern, text, re.IGNORECASE)
        if year_match:
            info["founded_year"] = int(year_match.group(1))

        # Extract employee count
        employee_patterns = [
            r"(\d+)\+?\s+employees",
            r"team\s+of\s+(\d+)",
            r"(\d+)\s+people",
            r"employees?:\s*(\d+)",
        ]
        for pattern in employee_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info["employee_count"] = int(match.group(1))
                break

        # Extract headquarters/location
        location_pattern = r"(?:headquartered|based|located)\s+(?:in\s+)?([A-Z][a-zA-Z\s]+,\s*[A-Z]{2}(?:,\s*[A-Z][a-zA-Z\s]+)?)"
        location_match = re.search(location_pattern, text)
        if location_match:
            info["headquarters"] = location_match.group(1).strip()

        # Extract mission/description (first paragraph-like text)
        paragraphs = text.split("\n\n")
        for para in paragraphs:
            if len(para) > 100 and len(para) < 500:
                info["description"] = para.strip()
                break

        return info

    async def _extract_team_info(self, page: Page, text: str) -> Dict:
        """Extract team/founder information"""
        info = {"founders": [], "executives": []}

        # Look for founder mentions
        founder_pattern = r"(?:founded by|founders?:?|co-founders?:?)\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+and\s+[A-Z][a-z]+\s+[A-Z][a-z]+)*)"
        founder_match = re.search(founder_pattern, text, re.IGNORECASE)
        if founder_match:
            founders_text = founder_match.group(1)
            # Split by 'and' or ','
            founders = re.split(r"\s+and\s+|,\s*", founders_text)
            info["founders"] = [f.strip() for f in founders if len(f.strip()) > 3]

        # Try to extract from structured elements
        try:
            # Look for common team member patterns
            team_members = await page.evaluate(
                """() => {
                const members = [];
                const selectors = [
                    '.team-member',
                    '.person',
                    '.founder',
                    '.executive',
                    '[class*="team"]',
                    '[class*="member"]'
                ];

                selectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        const name = el.querySelector('h1, h2, h3, h4, .name, [class*="name"]')?.innerText;
                        const title = el.querySelector('.title, .role, [class*="title"], [class*="role"]')?.innerText;
                        if (name && title) {
                            members.push({name: name.trim(), title: title.trim()});
                        }
                    });
                });

                return members;
            }"""
            )

            # Categorize team members
            for member in team_members[:10]:  # Limit to top 10
                title_lower = member.get("title", "").lower()
                if any(
                    keyword in title_lower
                    for keyword in ["founder", "co-founder", "founding"]
                ):
                    info["founders"].append(member["name"])
                elif any(
                    keyword in title_lower
                    for keyword in [
                        "ceo",
                        "cto",
                        "cfo",
                        "coo",
                        "chief",
                        "president",
                        "vp",
                    ]
                ):
                    info["executives"].append(
                        {"name": member["name"], "title": member["title"]}
                    )

        except Exception as e:
            logger.debug(f"Could not extract structured team data: {e}")

        return info

    async def _extract_news_info(self, page: Page, text: str) -> Dict:
        """Extract recent news/press information"""
        info = {"recent_announcements": []}

        # Extract funding announcements
        funding_pattern = r"(?:raised|secured|closed)\s+\$?([\d.]+)\s*(million|billion|M|B)\s+(?:in\s+)?(Series\s+[A-Z]|seed|pre-seed)?"
        funding_matches = re.finditer(funding_pattern, text, re.IGNORECASE)
        for match in funding_matches:
            amount = match.group(1)
            unit = match.group(2).lower()
            round_type = match.group(3) if match.group(3) else "funding"

            info["recent_announcements"].append(
                {
                    "type": "funding",
                    "amount": f"${amount}{unit[0].upper()}",
                    "round": round_type,
                }
            )

        return info

    async def _extract_product_info(self, page: Page, text: str) -> Dict:
        """Extract product information"""
        info = {"products": [], "technologies": []}

        # Extract technology mentions
        tech_keywords = [
            "AI",
            "machine learning",
            "ML",
            "artificial intelligence",
            "blockchain",
            "crypto",
            "web3",
            "cloud",
            "SaaS",
            "mobile",
            "iOS",
            "Android",
            "API",
            "platform",
            "Python",
            "JavaScript",
            "React",
            "Node.js",
            "AWS",
            "Azure",
            "GCP",
        ]

        for tech in tech_keywords:
            if re.search(rf"\b{re.escape(tech)}\b", text, re.IGNORECASE):
                info["technologies"].append(tech)

        # Limit to unique technologies
        info["technologies"] = list(set(info["technologies"]))[:10]

        return info

    async def _extract_pricing_info(self, page: Page, text: str) -> Dict:
        """Extract pricing information"""
        info = {"has_pricing": False, "pricing_model": None}

        # Detect pricing model
        if re.search(r"\bfree\b", text, re.IGNORECASE):
            info["has_pricing"] = True
            info["pricing_model"] = (
                "freemium"
                if re.search(r"\bpaid\b|\bpremium\b|\bpro\b", text, re.IGNORECASE)
                else "free"
            )
        elif re.search(r"\bsubscription\b|\bmonthly\b|\bannual\b", text, re.IGNORECASE):
            info["has_pricing"] = True
            info["pricing_model"] = "subscription"
        elif re.search(r"\benterprise\b|\bcontact\s+sales\b", text, re.IGNORECASE):
            info["has_pricing"] = True
            info["pricing_model"] = "enterprise"

        return info

    def _aggregate_intelligence(self, pages_scraped: Dict) -> Dict:
        """
        Aggregate intelligence from all scraped pages

        Args:
            pages_scraped: Dictionary of scraped page data

        Returns:
            Aggregated intelligence dictionary
        """
        aggregated = {
            "founded_year": None,
            "employee_count": None,
            "headquarters": None,
            "description": None,
            "founders": [],
            "executives": [],
            "products": [],
            "technologies": [],
            "funding_announcements": [],
            "pricing_model": None,
        }

        # Aggregate from all pages
        for page_key, page_info in pages_scraped.items():
            if not page_info.get("success"):
                continue

            data = page_info.get("data", {})
            structured = data.get("structured_data", {})

            # About info
            if "about" in structured:
                about = structured["about"]
                if not aggregated["founded_year"] and "founded_year" in about:
                    aggregated["founded_year"] = about["founded_year"]
                if not aggregated["employee_count"] and "employee_count" in about:
                    aggregated["employee_count"] = about["employee_count"]
                if not aggregated["headquarters"] and "headquarters" in about:
                    aggregated["headquarters"] = about["headquarters"]
                if not aggregated["description"] and "description" in about:
                    aggregated["description"] = about["description"]

            # Team info
            if "team" in structured:
                team = structured["team"]
                aggregated["founders"].extend(team.get("founders", []))
                aggregated["executives"].extend(team.get("executives", []))

            # Product info
            if "products" in structured:
                products = structured["products"]
                aggregated["technologies"].extend(products.get("technologies", []))

            # News info
            if "news" in structured:
                news = structured["news"]
                aggregated["funding_announcements"].extend(
                    news.get("recent_announcements", [])
                )

            # Pricing info
            if "pricing" in structured:
                pricing = structured["pricing"]
                if not aggregated["pricing_model"] and pricing.get("pricing_model"):
                    aggregated["pricing_model"] = pricing["pricing_model"]

        # Deduplicate lists
        aggregated["founders"] = list(set(aggregated["founders"]))
        aggregated["executives"] = list(
            {exec["name"]: exec for exec in aggregated["executives"]}.values()
        )
        aggregated["technologies"] = list(set(aggregated["technologies"]))

        return aggregated

    def _save_intelligence(
        self, company_name: str, article_id: str, intelligence: Dict
    ):
        """Save scraped intelligence to JSON file"""
        # Create safe filename
        safe_name = re.sub(r"[^\w\s-]", "", company_name).strip().replace(" ", "_")
        filename = f"{safe_name}_{article_id}.json"
        filepath = self.output_dir / filename

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(intelligence, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved intelligence to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save intelligence for {company_name}: {e}")

    async def scrape_companies_batch(
        self,
        company_urls: Dict[str, str],
        article_id: str,
        max_companies: Optional[int] = None,
    ) -> List[Dict]:
        """
        Scrape intelligence for a batch of companies

        Args:
            company_urls: Dictionary mapping company names to URLs
            article_id: Source article ID
            max_companies: Maximum number of companies to scrape

        Returns:
            List of intelligence dictionaries
        """
        results = []

        companies_to_scrape = list(company_urls.items())
        if max_companies:
            companies_to_scrape = companies_to_scrape[:max_companies]

        logger.info(
            f"Scraping intelligence for {len(companies_to_scrape)} companies from article {article_id}"
        )

        for company_name, url in companies_to_scrape:
            try:
                intelligence = await self.scrape_company(company_name, url, article_id)
                if intelligence:
                    results.append(intelligence)
            except Exception as e:
                logger.error(f"Failed to scrape {company_name}: {e}")
                continue

        return results

    def get_stats(self) -> Dict:
        """Get scraping statistics"""
        return self.stats.copy()
