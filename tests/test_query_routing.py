#!/usr/bin/env python3
"""
Test script to verify query routing works correctly
"""


def classify_query_intent(query: str):
    """
    Test version of classify_query_intent - copy of the logic from rag_query.py
    """
    query_lower = query.lower()

    # Detect if this is a list query (asking for multiple entities)
    # "Which" and "What are" are strong list indicators
    # "What" alone could be singular, so check for plural indicators
    has_plural = any(
        word in query_lower
        for word in ["companies", "startups", "investors", "firms", "businesses"]
    )
    is_list_query = (
        query_lower.startswith("which ")
        or query_lower.startswith("what are ")
        or query_lower.startswith("list ")
        or query_lower.startswith("show ")
        or (query_lower.startswith("what ") and has_plural)
        or any(
            f" {word} " in f" {query_lower} "
            for word in ["which", "list", "show", "all"]
        )
    )

    # Detect temporal context
    is_recent = any(
        word in query_lower for word in ["recent", "recently", "latest", "new", "last"]
    )

    # Detect sector/category filters (use word boundaries to avoid partial matches)
    sector = None
    import re

    for sector_keyword in [
        "artificial intelligence",
        "machine learning",
        "fintech",
        "blockchain",
        "crypto",
        "saas",
        "healthcare",
        "biotech",
        "ai",
        "ml",
    ]:
        # Use word boundaries for short keywords to avoid false matches
        if len(sector_keyword) <= 2:
            pattern = r"\b" + re.escape(sector_keyword) + r"\b"
        else:
            pattern = re.escape(sector_keyword)
        if re.search(pattern, query_lower):
            sector = sector_keyword
            break

    # Check for funding-related queries first (higher priority)
    has_funding_keywords = any(
        word in query_lower
        for word in ["funding", "raised", "invested", "series", "investment"]
    )

    if has_funding_keywords:
        # Check if it's asking about investor info
        if any(
            word in query_lower
            for word in ["who funded", "which investors", "who invested"]
        ):
            return {"intent": "funding_info", "confidence": 0.9}
        # Check if it's a list query asking for multiple companies
        elif is_list_query:
            return {
                "intent": "list_funded_companies",
                "confidence": 0.9,
                "filters": {"sector": sector, "recent": is_recent},
            }
        # Single company funding query
        else:
            return {"intent": "funding_info", "confidence": 0.9}

    # Company-related queries
    has_company_keywords = any(
        word in query_lower
        for word in ["company", "companies", "startup", "startups", "firm", "business"]
    )

    # Check if it's a "tell me about X" or "about X" query (likely company info)
    is_about_query = any(
        phrase in query_lower
        for phrase in ["tell me about", "about ", "what is", "who is"]
    )

    if has_company_keywords or (
        is_about_query
        and not any(
            word in query_lower for word in ["investor", "vc", "person", "technology"]
        )
    ):
        if any(
            word in query_lower
            for word in ["competitor", "compete", "vs", "compared to"]
        ):
            return {"intent": "competitive_analysis", "confidence": 0.9}
        elif any(word in query_lower for word in ["founder", "founded", "ceo", "team"]):
            return {"intent": "company_leadership", "confidence": 0.8}
        else:
            # Check if asking for list of companies in a sector
            if is_list_query and sector:
                return {
                    "intent": "list_companies_in_sector",
                    "confidence": 0.85,
                    "filters": {"sector": sector},
                }
            return {"intent": "company_info", "confidence": 0.7}

    # Investor queries
    elif any(
        word in query_lower for word in ["investor", "vc", "venture capital", "fund"]
    ):
        if any(word in query_lower for word in ["portfolio", "invested in", "backed"]):
            return {"intent": "investor_portfolio", "confidence": 0.9}
        else:
            return {"intent": "investor_info", "confidence": 0.7}

    # Person queries
    elif any(
        word in query_lower
        for word in ["who is", "person", "founder", "ceo", "executive"]
    ):
        return {"intent": "person_info", "confidence": 0.8}

    # Technology queries
    elif any(
        word in query_lower for word in ["technology", "tech", "ai", "ml", "blockchain"]
    ):
        return {"intent": "technology_info", "confidence": 0.8}

    # Trend queries
    elif any(
        word in query_lower for word in ["trend", "popular", "growing", "emerging"]
    ):
        return {"intent": "trend_analysis", "confidence": 0.8}

    # Relationship queries
    elif any(
        word in query_lower
        for word in ["connection", "related", "link", "relationship"]
    ):
        return {"intent": "relationship_query", "confidence": 0.8}

    # General search
    else:
        return {"intent": "general_search", "confidence": 0.5}


def test_query_classification():
    """Test query classification logic"""

    # Test cases
    test_queries = [
        {
            "query": "Which AI startups raised funding recently?",
            "expected_intent": "list_funded_companies",
            "expected_filters": {"sector": "ai", "recent": True},
        },
        {
            "query": "What companies in fintech have funding?",
            "expected_intent": "list_funded_companies",
            "expected_filters": {"sector": "fintech", "recent": False},
        },
        {
            "query": "Show me all blockchain startups",
            "expected_intent": "list_companies_in_sector",
            "expected_filters": {"sector": "blockchain"},
        },
        {
            "query": "Tell me about Anthropic",
            "expected_intent": "company_info",
            "expected_filters": {},
        },
        {
            "query": "What funding did OpenAI raise?",
            "expected_intent": "funding_info",
            "expected_filters": {},
        },
    ]

    print("=" * 80)
    print("TESTING QUERY CLASSIFICATION")
    print("=" * 80)

    passed = 0
    failed = 0

    for test in test_queries:
        query = test["query"]
        expected_intent = test["expected_intent"]
        expected_filters = test["expected_filters"]

        # Classify query
        result = classify_query_intent(query)

        # Check results
        intent_match = result["intent"] == expected_intent
        filters_match = result.get("filters", {}) == expected_filters

        if intent_match and filters_match:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1

        print(f"\n{status}")
        print(f"Query: {query}")
        print(f"Expected: intent={expected_intent}, filters={expected_filters}")
        print(
            f"Got:      intent={result['intent']}, filters={result.get('filters', {})}"
        )

        if not intent_match:
            print(f"  ⚠️  Intent mismatch!")
        if not filters_match:
            print(f"  ⚠️  Filters mismatch!")

    print("\n" + "=" * 80)
    print(f"TEST COMPLETE: {passed} passed, {failed} failed")
    print("=" * 80)


if __name__ == "__main__":
    test_query_classification()
