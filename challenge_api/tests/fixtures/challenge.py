import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_challenge():
    """Mock challenge object"""
    challenge = Mock()
    challenge.id = 1
    challenge.title = "Test Challenge"
    return challenge
