"""Password hashing service tests."""

import pytest
from src.services.auth import Hash


def test_password_hashing():
    """Test password hashing functionality."""
    password = "test_password_123"
    hash_service = Hash()
    
    # Test hashing
    hashed_password = hash_service.get_password_hash(password)
    assert hashed_password != password
    assert len(hashed_password) > 10  # Hash should be longer than original
    
    # Test verification
    assert hash_service.verify_password(password, hashed_password) is True
    
    # Test wrong password
    assert hash_service.verify_password("wrong_password", hashed_password) is False
