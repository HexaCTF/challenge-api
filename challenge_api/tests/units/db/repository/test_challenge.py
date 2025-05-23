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
    
    def test_is_exist_success(self, mock_challenge):
        with patch.object(self.repo, "get_by_id", return_value=mock_challenge) as mock_get_by_id:
            result = self.repo.is_exist(1)
            assert result is True
            
            mock_get_by_id.assert_called_once_with(id_=1)
               

    def test_is_exist_does_not_exist(self):
        with patch.object(self.repo, "get_by_id", return_value=None) as mock_get_by_id:
            result = self.repo.is_exist(1)
            assert result is False
            
            mock_get_by_id.assert_called_once_with(id_=1)
            
    
        
    def test_get_name_success(self, mock_challenge):
        with patch.object(self.repo, "get_by_id", return_value=mock_challenge) as mock_get_by_id:
            result = self.repo.get_name(1)
            assert result == "test_challenge"
            
            mock_get_by_id.assert_called_once_with(id_=1)
        
        
    def test_get_name_does_not_exist(self):
        with patch.object(self.repo, "get_by_id", return_value=None) as mock_get_by_id:
            with pytest.raises(ChallengeNotFound):
                self.repo.get_name(1)

            mock_get_by_id.assert_called_once_with(id_=1)
        
