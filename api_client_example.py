"""
GraphRAG API Client Example
Demonstrates how to use the API endpoints
"""

import json
from typing import Any, Dict, List

import requests


class GraphRAGClient:
    """Simple client for GraphRAG API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def _post(self, endpoint: str, data: Dict) -> Dict:
        """Make POST request"""
        response = requests.post(f"{self.base_url}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()

    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """Make GET request"""
        response = requests.get(f"{self.base_url}{endpoint}", params=params)
        response.raise_for_status()
        return response.json()

    # Query methods
    def query(
        self, question: str, return_context: bool = False, use_llm: bool = True
    ) -> Dict:
        """Ask a natural language question"""
        return self._post(
            "/query",
            {
                "question": question,
                "return_context": return_context,
                "use_llm": use_llm,
            },
        )

    def batch_query(self, questions: List[str]) -> Dict:
        """Process multiple questions"""
        return self._post("/query/batch", {"questions": questions})

    def multi_hop_reasoning(self, question: str, max_hops: int = 3) -> Dict:
        """Perform multi-hop reasoning"""
        return self._post(
            "/query/multi-hop", {"question": question, "max_hops": max_hops}
        )

    # Search methods
    def semantic_search(
        self, query: str, top_k: int = 10, entity_type: str = None
    ) -> Dict:
        """Semantic search for entities"""
        return self._post(
            "/search/semantic",
            {"query": query, "top_k": top_k, "entity_type": entity_type},
        )

    def hybrid_search(
        self, query: str, top_k: int = 10, semantic_weight: float = 0.7
    ) -> Dict:
        """Hybrid search combining semantic and keyword"""
        return self._post(
            "/search/hybrid",
            {"query": query, "top_k": top_k, "semantic_weight": semantic_weight},
        )

    def fulltext_search(self, query: str, limit: int = 10) -> Dict:
        """Full-text search"""
        return self._get("/search/fulltext", {"query": query, "limit": limit})

    # Entity methods
    def get_entity(self, entity_id: str, include_relationships: bool = False) -> Dict:
        """Get entity by ID"""
        return self._get(
            f"/entity/{entity_id}", {"include_relationships": include_relationships}
        )

    def get_entity_by_name(self, name: str, entity_type: str = None) -> Dict:
        """Get entity by name"""
        return self._get(f"/entity/name/{name}", {"entity_type": entity_type})

    def compare_entities(self, entity1: str, entity2: str) -> Dict:
        """Compare two entities"""
        return self._post("/entity/compare", {"entity1": entity1, "entity2": entity2})

    # Company methods
    def get_company_profile(self, company_name: str) -> Dict:
        """Get company profile"""
        return self._get(f"/company/{company_name}")

    def get_funded_companies(self, min_investors: int = 1) -> Dict:
        """Get companies with funding"""
        return self._get("/companies/funded", {"min_investors": min_investors})

    def get_companies_by_sector(self, sector: str) -> Dict:
        """Get companies in sector"""
        return self._get(f"/companies/sector/{sector}")

    def get_competitive_landscape(self, company_name: str) -> Dict:
        """Get competitive landscape"""
        return self._get(f"/company/{company_name}/competitive-landscape")

    # Investor methods
    def get_investor_portfolio(self, investor_name: str) -> Dict:
        """Get investor portfolio"""
        return self._get(f"/investor/{investor_name}/portfolio")

    def get_top_investors(self, limit: int = 10) -> Dict:
        """Get top investors"""
        return self._get("/investors/top", {"limit": limit})

    # Analytics methods
    def get_statistics(self) -> Dict:
        """Get graph statistics"""
        return self._get("/analytics/statistics")

    def get_most_connected(self, limit: int = 10) -> Dict:
        """Get most connected entities"""
        return self._get("/analytics/most-connected", {"limit": limit})

    def get_importance_scores(self, limit: int = 20) -> Dict:
        """Get entity importance scores"""
        return self._get("/analytics/importance", {"limit": limit})

    def get_insights(self, topic: str, limit: int = 5) -> Dict:
        """Get AI insights about a topic"""
        return self._get(f"/analytics/insights/{topic}", {"limit": limit})

    # Technology methods
    def get_trending_technologies(self, limit: int = 10) -> Dict:
        """Get trending technologies"""
        return self._get("/technologies/trending", {"limit": limit})

    def get_technology_adoption(self, technology: str) -> Dict:
        """Get technology adoption info"""
        return self._get(f"/technology/{technology}")


# =============================================================================
# EXAMPLE USAGE
# =============================================================================


def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def main():
    """Example usage of the API client"""
    client = GraphRAGClient()

    try:
        # Test 1: Health check
        print_section("1. Health Check")
        health = client._get("/health")
        print(f"Status: {health['status']}")
        print(
            f"Graph nodes: {sum(c['count'] for c in health['graph_stats']['node_counts'])}"
        )

        # Test 2: Natural language query
        print_section("2. Natural Language Query")
        result = client.query("What AI startups have raised funding recently?")
        print(f"Question: {result['question']}")
        print(f"Intent: {result['intent']}")
        print(f"Answer: {result['answer'][:200]}...")

        # Test 3: Semantic search
        print_section("3. Semantic Search for AI Companies")
        results = client.semantic_search(
            "artificial intelligence", top_k=5, entity_type="Company"
        )
        print(f"Found {results['count']} companies:")
        for entity in results["results"][:3]:
            print(f"  - {entity['name']} (similarity: {entity['similarity']:.3f})")

        # Test 4: Company profile
        print_section("4. Company Profile")
        if results["results"]:
            company_name = results["results"][0]["name"]
            profile = client.get_company_profile(company_name)
            print(f"Company: {profile.get('name')}")
            print(f"Description: {profile.get('description', 'N/A')[:150]}...")
            print(f"Founders: {', '.join(profile.get('founders', []))}")
            print(f"Investors: {len(profile.get('investors', []))} investors")

        # Test 5: Top investors
        print_section("5. Top Investors")
        investors = client.get_top_investors(limit=5)
        print(f"Top {investors['count']} investors:")
        for inv in investors["results"]:
            print(f"  - {inv['name']}: {inv['portfolio_size']} investments")

        # Test 6: Trending technologies
        print_section("6. Trending Technologies")
        tech = client.get_trending_technologies(limit=5)
        print(f"Top {tech['count']} technologies:")
        for t in tech["results"]:
            print(f"  - {t['name']}: {t.get('company_count', 0)} companies")

        # Test 7: Entity comparison
        print_section("7. Entity Comparison")
        comparison = client.compare_entities("OpenAI", "Anthropic")
        if "comparison" in comparison:
            print(f"Comparison: {comparison['comparison'][:300]}...")

        # Test 8: Graph statistics
        print_section("8. Graph Statistics")
        stats = client.get_statistics()
        print("Node counts:")
        for node in stats["node_counts"]:
            print(f"  - {node['label']}: {node['count']}")
        print(f"\nTotal communities: {stats['community_count']}")

        # Test 9: Multi-hop reasoning
        print_section("9. Multi-hop Reasoning")
        result = client.multi_hop_reasoning(
            "What technologies are used by companies funded by top investors?",
            max_hops=3,
        )
        print(f"Answer: {result['answer'][:300]}...")

        # Test 10: Insights
        print_section("10. AI Insights")
        insights = client.get_insights("artificial intelligence")
        print(f"Insights: {insights['insights'][:300]}...")

        print("\n" + "=" * 80)
        print(" All tests completed successfully! ✅")
        print("=" * 80)

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API. Make sure the server is running:")
        print("   python api.py")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
