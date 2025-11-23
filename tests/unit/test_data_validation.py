"""
Unit tests for data validation utilities
Tests all validation functions without external dependencies
"""

import pytest
from utils.data_validation import (
    validate_article_structure,
    validate_article_content,
    validate_extracted_data,
    validate_entity_types,
    validate_relationship_types,
    VALID_ENTITY_TYPES,
    VALID_RELATIONSHIP_TYPES,
)


class TestArticleStructureValidation:
    """Test article structure validation"""

    def test_valid_article_structure(self, sample_article):
        """Test validation passes for valid article"""
        is_valid, message = validate_article_structure(sample_article)
        assert is_valid is True
        assert message == "Valid"

    def test_missing_title(self, sample_article):
        """Test validation fails when title is missing"""
        del sample_article["title"]
        is_valid, message = validate_article_structure(sample_article)
        assert is_valid is False
        assert "title" in message.lower()

    def test_missing_content(self, sample_article):
        """Test validation fails when content is missing"""
        del sample_article["content"]
        is_valid, message = validate_article_structure(sample_article)
        assert is_valid is False
        assert "content" in message.lower()

    def test_missing_url(self, sample_article):
        """Test validation fails when URL is missing"""
        del sample_article["url"]
        is_valid, message = validate_article_structure(sample_article)
        assert is_valid is False
        assert "url" in message.lower()

    def test_empty_title(self, sample_article):
        """Test validation fails for empty title"""
        sample_article["title"] = ""
        is_valid, message = validate_article_structure(sample_article)
        assert is_valid is False

    def test_empty_content(self, sample_article):
        """Test validation fails for empty content"""
        sample_article["content"] = ""
        is_valid, message = validate_article_structure(sample_article)
        assert is_valid is False


class TestArticleContentValidation:
    """Test article content quality validation"""

    def test_valid_content_length(self, sample_article):
        """Test validation passes for adequate content length"""
        sample_article["content"] = "A" * 200  # 200 characters
        is_valid, message = validate_article_content(sample_article)
        assert is_valid is True

    def test_content_too_short(self, sample_article):
        """Test validation fails for content that's too short"""
        sample_article["content"] = "Short"
        is_valid, message = validate_article_content(sample_article)
        assert is_valid is False
        assert "too short" in message.lower()

    def test_content_minimum_threshold(self, sample_article):
        """Test validation at minimum content length threshold"""
        sample_article["content"] = "A" * 100  # Exactly at minimum
        is_valid, message = validate_article_content(sample_article)
        assert is_valid is True


class TestExtractedDataValidation:
    """Test validation of extracted entities and relationships"""

    def test_valid_extracted_data(self):
        """Test validation passes for valid extracted data"""
        extracted = {
            "entities": [
                {"name": "OpenAI", "type": "Company", "description": "AI company"},
                {"name": "Sam Altman", "type": "Person", "description": "CEO"},
            ],
            "relationships": [
                {
                    "source": "Sam Altman",
                    "target": "OpenAI",
                    "type": "WORKS_AT",
                    "strength": 0.9,
                    "context": "CEO of OpenAI",
                }
            ],
        }
        is_valid, message = validate_extracted_data(extracted)
        assert is_valid is True

    def test_missing_entities_key(self):
        """Test validation fails when entities key is missing"""
        extracted = {"relationships": []}
        is_valid, message = validate_extracted_data(extracted)
        assert is_valid is False
        assert "entities" in message.lower()

    def test_missing_relationships_key(self):
        """Test validation fails when relationships key is missing"""
        extracted = {"entities": []}
        is_valid, message = validate_extracted_data(extracted)
        assert is_valid is False
        assert "relationships" in message.lower()

    def test_empty_extraction(self):
        """Test validation fails when both entities and relationships are empty"""
        extracted = {"entities": [], "relationships": []}
        is_valid, message = validate_extracted_data(extracted)
        assert is_valid is False
        assert "empty" in message.lower() or "no entities" in message.lower()

    def test_entity_missing_name(self):
        """Test validation fails when entity missing name"""
        extracted = {
            "entities": [{"type": "Company", "description": "AI company"}],
            "relationships": [],
        }
        is_valid, message = validate_extracted_data(extracted)
        assert is_valid is False
        assert "name" in message.lower()

    def test_entity_missing_type(self):
        """Test validation fails when entity missing type"""
        extracted = {
            "entities": [{"name": "OpenAI", "description": "AI company"}],
            "relationships": [],
        }
        is_valid, message = validate_extracted_data(extracted)
        assert is_valid is False
        assert "type" in message.lower()

    def test_relationship_missing_fields(self):
        """Test validation fails when relationship missing required fields"""
        extracted = {
            "entities": [{"name": "OpenAI", "type": "Company", "description": "AI"}],
            "relationships": [{"source": "OpenAI"}],  # Missing target, type, strength
        }
        is_valid, message = validate_extracted_data(extracted)
        assert is_valid is False

    def test_invalid_strength_value(self):
        """Test validation fails for invalid strength value"""
        extracted = {
            "entities": [{"name": "OpenAI", "type": "Company", "description": "AI"}],
            "relationships": [
                {
                    "source": "A",
                    "target": "B",
                    "type": "PARTNERS_WITH",
                    "strength": 1.5,  # Invalid: > 1.0
                }
            ],
        }
        is_valid, message = validate_extracted_data(extracted)
        assert is_valid is False
        assert "strength" in message.lower()


class TestEntityTypeValidation:
    """Test entity type validation"""

    def test_valid_entity_types(self, entity_type):
        """Test all valid entity types are accepted"""
        is_valid, message = validate_entity_types([entity_type])
        assert is_valid is True

    def test_invalid_entity_type(self):
        """Test validation fails for invalid entity type"""
        is_valid, message = validate_entity_types(["InvalidType"])
        assert is_valid is False
        assert "invalid" in message.lower()

    def test_mixed_valid_invalid(self):
        """Test validation fails when mix includes invalid types"""
        types = ["Company", "InvalidType", "Person"]
        is_valid, message = validate_entity_types(types)
        assert is_valid is False

    def test_empty_type_list(self):
        """Test validation handles empty list"""
        is_valid, message = validate_entity_types([])
        assert is_valid is True  # Empty list is technically valid


class TestRelationshipTypeValidation:
    """Test relationship type validation"""

    def test_valid_relationship_types(self, relationship_type):
        """Test all valid relationship types are accepted"""
        is_valid, message = validate_relationship_types([relationship_type])
        assert is_valid is True

    def test_invalid_relationship_type(self):
        """Test validation fails for invalid relationship type"""
        is_valid, message = validate_relationship_types(["INVALID_RELATION"])
        assert is_valid is False
        assert "invalid" in message.lower()

    def test_multiple_valid_types(self):
        """Test validation passes for multiple valid types"""
        types = ["FOUNDED_BY", "FUNDED_BY", "WORKS_AT"]
        is_valid, message = validate_relationship_types(types)
        assert is_valid is True


class TestValidConstants:
    """Test that validation constants are properly defined"""

    def test_entity_types_not_empty(self):
        """Test VALID_ENTITY_TYPES constant is not empty"""
        assert len(VALID_ENTITY_TYPES) > 0

    def test_relationship_types_not_empty(self):
        """Test VALID_RELATIONSHIP_TYPES constant is not empty"""
        assert len(VALID_RELATIONSHIP_TYPES) > 0

    def test_entity_types_are_strings(self):
        """Test all entity types are strings"""
        assert all(isinstance(t, str) for t in VALID_ENTITY_TYPES)

    def test_relationship_types_are_strings(self):
        """Test all relationship types are strings"""
        assert all(isinstance(t, str) for t in VALID_RELATIONSHIP_TYPES)

    def test_expected_entity_types_present(self):
        """Test expected entity types are in the list"""
        expected = {"Company", "Person", "Investor", "Technology", "Product"}
        assert expected.issubset(set(VALID_ENTITY_TYPES))

    def test_expected_relationship_types_present(self):
        """Test expected relationship types are in the list"""
        expected = {"FOUNDED_BY", "FUNDED_BY", "WORKS_AT", "PARTNERS_WITH"}
        assert expected.issubset(set(VALID_RELATIONSHIP_TYPES))
