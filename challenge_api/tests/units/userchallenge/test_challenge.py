import pytest
from unittest.mock import MagicMock, patch
from challenge_api.objects.challenge import ChallengeRequest
from challenge_api.userchallenge.challenge import ChallengeService

@pytest.fixture
def request_stub():
    return ChallengeRequest(challenge_id=1, user_id=1)

class TestChallengeService:
    def setup_method(self):
        self.challenge_repository_mock = MagicMock()
        self.challenge_service = ChallengeService(self.challenge_repository_mock)
    
    def test_is_exist(self, request_stub):
        # Given
        self.challenge_repository_mock.get_by_id.return_value = True
        
        # When
        result = self.challenge_service.is_exist(request_stub)
        
        # Then
        assert result is True
        self.challenge_repository_mock.get_by_id.assert_called_once_with(request_stub.challenge_id)
    
    def test_is_exist_false(self, request_stub):
        # Given
        self.challenge_repository_mock.get_by_id.return_value = None
        
        # When
        result = self.challenge_service.is_exist(request_stub)
        
        # Then
        assert result is False
        self.challenge_repository_mock.get_by_id.assert_called_once_with(request_stub.challenge_id)