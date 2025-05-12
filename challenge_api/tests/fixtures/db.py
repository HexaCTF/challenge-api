import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_session():
    """Mock database session for repository tests"""
    session = Mock()
    return session
