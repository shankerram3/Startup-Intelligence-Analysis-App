"""
Unit tests for security utilities
Tests JWT token handling, password hashing, and security helpers
"""

from datetime import timedelta

import pytest
from fastapi import HTTPException

from utils.security import (create_access_token, decode_access_token,
                            generate_test_token, get_password_hash,
                            sanitize_error_message, validate_password_strength,
                            verify_password)


class TestPasswordHashing:
    """Test password hashing and verification"""

    def test_hash_password(self):
        """Test password hashing generates different hash"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 20

    def test_hash_long_password(self):
        """Test password hashing with password > 72 bytes (bcrypt limit)"""
        # Create a password longer than 72 bytes
        long_password = "a" * 100
        hashed = get_password_hash(long_password)
        assert hashed != long_password
        assert len(hashed) > 20
        # Should still verify correctly (truncated to 72 bytes)
        assert verify_password(long_password, hashed) is True

    def test_verify_correct_password(self):
        """Test verification succeeds for correct password"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Test verification fails for incorrect password"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert verify_password("wrong_password", hashed) is False

    def test_same_password_different_hashes(self):
        """Test same password produces different hashes (salt)"""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestJWTTokens:
    """Test JWT token creation and validation"""

    def test_create_token(self):
        """Test token creation"""
        data = {"sub": "user123", "role": "admin"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 20

    def test_decode_valid_token(self):
        """Test decoding valid token"""
        data = {"sub": "user123", "role": "admin"}
        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded["sub"] == "user123"
        assert decoded["role"] == "admin"
        assert "exp" in decoded
        assert "iat" in decoded

    def test_decode_invalid_token(self):
        """Test decoding invalid token raises exception"""
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("invalid_token")

        assert exc_info.value.status_code == 401

    def test_token_with_custom_expiration(self):
        """Test token with custom expiration time"""
        data = {"sub": "user123"}
        expires = timedelta(minutes=5)
        token = create_access_token(data, expires_delta=expires)
        decoded = decode_access_token(token)

        # Token should have expiration set
        assert "exp" in decoded

    def test_generate_test_token(self):
        """Test test token generation"""
        token = generate_test_token("test_user", "user")
        decoded = decode_access_token(token)

        assert decoded["sub"] == "test_user"
        assert decoded["role"] == "user"


class TestPasswordValidation:
    """Test password strength validation"""

    def test_valid_strong_password(self):
        """Test validation passes for strong password"""
        password = "StrongPass123"
        is_valid, message = validate_password_strength(password)
        assert is_valid is True
        assert "strong" in message.lower()

    def test_password_too_short(self):
        """Test validation fails for short password"""
        password = "Short1"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert "8 characters" in message

    def test_password_no_uppercase(self):
        """Test validation fails without uppercase letter"""
        password = "weakpass123"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert "uppercase" in message.lower()

    def test_password_no_lowercase(self):
        """Test validation fails without lowercase letter"""
        password = "WEAKPASS123"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert "lowercase" in message.lower()

    def test_password_no_digit(self):
        """Test validation fails without digit"""
        password = "WeakPassword"
        is_valid, message = validate_password_strength(password)
        assert is_valid is False
        assert "digit" in message.lower()

    def test_password_with_special_chars(self):
        """Test validation passes with special characters"""
        password = "Strong!Pass123"
        is_valid, message = validate_password_strength(password)
        assert is_valid is True


class TestErrorSanitization:
    """Test error message sanitization"""

    def test_sanitize_generic_error(self):
        """Test generic error is sanitized"""
        error = Exception("Internal server error with sensitive data")
        sanitized = sanitize_error_message(error, include_details=False)
        assert "internal error" in sanitized.lower()
        assert "sensitive data" not in sanitized

    def test_sanitize_neo4j_error(self):
        """Test Neo4j errors are sanitized"""
        error = Exception("Neo4jError: connection failed to bolt://...")
        sanitized = sanitize_error_message(error, include_details=False)
        assert "database" in sanitized.lower()
        assert "bolt://" not in sanitized
        # Test with different Neo4j error formats
        error2 = Exception("Database connection failed")
        sanitized2 = sanitize_error_message(error2, include_details=False)
        assert "database" in sanitized2.lower()

    def test_sanitize_openai_error(self):
        """Test OpenAI errors are sanitized"""
        error = Exception("OpenAI API error: Invalid API key")
        sanitized = sanitize_error_message(error, include_details=False)
        assert "service" in sanitized.lower()
        assert "API key" not in sanitized

    def test_sanitize_with_details(self):
        """Test sanitization includes details when requested"""
        error = Exception("Detailed error message")
        sanitized = sanitize_error_message(error, include_details=True)
        assert "Detailed error message" in sanitized

    def test_sanitize_validation_error(self):
        """Test validation errors are handled"""
        error = ValueError("Invalid input data")
        sanitized = sanitize_error_message(error, include_details=False)
        assert "invalid input" in sanitized.lower()
