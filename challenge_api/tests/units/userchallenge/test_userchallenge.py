import pytest
from unittest.mock import MagicMock
from challenge_api.userchallenge.userchallenge import UserChallengeService
from challenge_api.objects.challenge import ChallengeRequest
from challenge_api.db.models import UserChallenges
from challenge_api.exceptions.service import UserChallengeNotFound, ChallengeNotFound

@pytest.fixture
def request_stub():
    return ChallengeRequest(challenge_id=1, user_id=1)

class TestUserChallengeService:
    def setup_method(self):
        self.userchallenge_repository_mock = MagicMock()
        self.challenge_service_mock = MagicMock()
        self.userchallenge_service = UserChallengeService(self.userchallenge_repository_mock, self.challenge_service_mock)
        
    def test_is_exist_true(self, request_stub):
        self.userchallenge_repository_mock.get_by_id.return_value = True
        
        result = self.userchallenge_service.is_exist(request_stub)
        
        assert result is True
        self.userchallenge_repository_mock.get_by_id.assert_called_once_with(request_stub.challenge_id)
        
        
    def test_is_exist_false(self, request_stub):
        self.userchallenge_repository_mock.get_by_id.return_value = None
        
        result = self.userchallenge_service.is_exist(request_stub)
        
        assert result is False
        self.userchallenge_repository_mock.get_by_id.assert_called_once_with(request_stub.challenge_id)
        
        
    def test_get_by_name_success(self, request_stub):
        userchallenge = UserChallenges(
            user_idx=request_stub.user_id,
            C_idx=request_stub.challenge_id,
            userChallengeName=request_stub.name
        )
        
        self.userchallenge_repository_mock.get.return_value = userchallenge
        
        kwarg = {
            "userChallengeName": request_stub.name
        }
        self.userchallenge_repository_mock.get.return_value = userchallenge
        
        result = self.userchallenge_service.get_by_name(request_stub.name)
        
        assert result is userchallenge
        self.userchallenge_repository_mock.get.assert_called_once_with(**kwarg)
        
        
    def test_get_by_name_not_found(self, request_stub):
        self.userchallenge_repository_mock.get.return_value = None
        
        with pytest.raises(UserChallengeNotFound) as e:
            self.userchallenge_service.get_by_name(request_stub.name)
            
        assert str(e.value) == f"UserChallengeNotFound: User challenge {request_stub.name} not found"
        
        
    def test_create_success(self, request_stub):
        self.challenge_service_mock.is_exist.return_value = True
        
        userchallenge = UserChallenges(
            user_idx=request_stub.user_id,
            C_idx=request_stub.challenge_id,
            userChallengeName=request_stub.name
        )
        
        self.userchallenge_repository_mock.create.return_value = userchallenge
        
        result = self.userchallenge_service.create(request_stub)
        
        assert result is userchallenge
        self.userchallenge_repository_mock.create.assert_called_once_with(request_stub)
        
        
    def test_create_challenge_not_found(self, request_stub):
        self.challenge_service_mock.is_exist.return_value = False
        
        with pytest.raises(ChallengeNotFound) as e:
            self.userchallenge_service.create(request_stub)
            
        assert str(e.value) == f"ChallengeNotFound: Challenge {request_stub.challenge_id} not found"
        
        
    