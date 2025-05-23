import pytest
from unittest.mock import MagicMock
from challenge_api.db.repository.userchallenge import UserChallengesRepository
from challenge_api.objects.challenge import ChallengeRequest
from challenge_api.exceptions.service import InvalidInputValue

@pytest.fixture
def fake_challenge_request():
    return ChallengeRequest(
        challenge_id=1,
        user_id=1,
        name="test_userchallenge"
    )

@pytest.fixture
def mock_userchallenge():
    userchallenge = MagicMock()
    userchallenge.idx = 1
    userchallenge.user_idx = 1
    userchallenge.C_idx = 1
    userchallenge.userChallengeName = "test_userchallenge"
    return userchallenge

class TestUserChallengeRepository:
    def setup_method(self):
        self.mock_session = MagicMock()
        self.repo = UserChallengesRepository(session=self.mock_session)
    
    def test_create_success(self, fake_challenge_request):
        
        userchallenge = self.repo.create(fake_challenge_request)
        
        assert userchallenge is not None
        assert userchallenge.user_idx == fake_challenge_request.user_id
        assert userchallenge.C_idx == fake_challenge_request.challenge_id
        assert userchallenge.userChallengeName == fake_challenge_request.name
    
    def test_create_invalid_input(self):
        with pytest.raises(InvalidInputValue) as e:
            self.repo.create(1)
            
        assert "Invalid input error when creating userchallenge" in str(e)
                    
    def test_get_by_id_success(self, mock_userchallenge):
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = mock_userchallenge
        
        userchallenge = self.repo.get_by_id(1)
        
        assert userchallenge is not None
        assert userchallenge.user_idx == 1
        assert userchallenge.C_idx == 1
        assert userchallenge.userChallengeName == "test_userchallenge"
    
    def test_get_by_id_does_not_exist(self):
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        userchallenge = self.repo.get_by_id(1)
        
        assert userchallenge is None
        
        
        
        
        
        
        
        
        