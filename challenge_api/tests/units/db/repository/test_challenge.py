import pytest
from unittest.mock import MagicMock, patch
from challenge_api.db.repository.challenge import ChallengeRepository
from challenge_api.exceptions.challenge import ChallengeNotFound

@pytest.fixture
def mock_challenge():
    challenge = MagicMock()
    challenge.idx = 1
    challenge.title = "test_challenge"
    return challenge

class TestChallengeRepository:
    def setup_method(self):
        self.mock_session = MagicMock()
        self.repo = ChallengeRepository(session=self.mock_session)
    
    def test_get_by_id_success(self, mock_challenge):
        self.mock_session.get.return_value = mock_challenge
                
        result = self.repo.get_by_id(1)
        assert result == mock_challenge
    
    def test_get_by_id_does_not_exist(self):
        self.mock_session.get.return_value = None
        
        result = self.repo.get_by_id(1)
        assert result is None
    
