from unittest.mock import MagicMock
import pytest
from challenge_api.userchallenge.status import UserChallengeStatusService
from challenge_api.objects.usrchallenge import UChallengeStatus
from challenge_api.db.models import UserChallengeStatus
from challenge_api.exceptions.service import InvalidInputValue

class TestUserChallengeStatusService:
    def setup_method(self):
        self.mock_repo = MagicMock()
        self.status_service = UserChallengeStatusService(self.mock_repo)
    
    def test_create(self):
        status = UserChallengeStatus(
            userChallenge_idx=1,
            port=8080,
            status="running"
        )
        self.mock_repo.create.return_value = status
        
        self.status_service.create(1, 8080, "running")
        
        assert self.mock_repo.create.call_count == 1
        
        actual_arg = self.mock_repo.create.call_args[0][0]
        assert isinstance(actual_arg, UChallengeStatus)
        assert actual_arg.userchallenge_idx == 1
        assert actual_arg.port == 8080
        assert actual_arg.status == "running"
        

    def test_get_first_success(self):
        status = UserChallengeStatus(
            userChallenge_idx=1,
            port=8080,
            status="running"
        )
        self.mock_repo.first.return_value = status 
        
        result = self.status_service.get_first(1)
        assert result == status
        assert self.mock_repo.first.call_count == 1
        assert self.mock_repo.first.call_args[0][0] == 1
        
    def test_get_first_not_found(self):
        self.mock_repo.first.return_value = None
        
        result = self.status_service.get_first(1)
        
        assert result is None
        assert self.mock_repo.first.call_count == 1
        assert self.mock_repo.first.call_args[0][0] == 1
        
    def test_update_UChallengeStatus(self):
        status = UserChallengeStatus(
            userChallenge_idx=1,
            port=8080,
            status="running"
        )
        self.mock_repo.update.return_value = status
        
        result = self.status_service.update(status)
        assert result == status
        assert self.mock_repo.update.call_count == 1
        assert self.mock_repo.update.call_args[0][0] == status
    
    def test_update_UserChallengeStatus(self):
        status = UserChallengeStatus(
            userChallenge_idx=1,
            port=8080,
            status="running"
        )
        self.mock_repo.update.return_value = status
        
        result = self.status_service.update(status)
        assert result == status
        assert self.mock_repo.update.call_count == 1
        assert self.mock_repo.update.call_args[0][0] == status
        
        
        
        