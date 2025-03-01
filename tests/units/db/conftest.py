import os
from unittest.mock import MagicMock, patch
import pytest
from hexactf.extensions.db.repository import ChallengeRepository, UserChallengesRepository


class DBMock:
    """Manages database-related fixtures for testing"""

    def __init__(self):
        self.mock_session = MagicMock()
        self.user_challenges_repo = UserChallengesRepository(session=self.mock_session)
        self.challenge_repo = ChallengeRepository()

@pytest.fixture()
def db_mock():
    """Provides an instance of DBTestManager for database tests"""
    return DBMock()

# autouse 명시적으로 call 하지 않아도 사용할 수 있는 옵션 
@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """Automatically set TEST_MODE=true for all tests"""
    os.environ["TEST_MODE"] = "true"
    