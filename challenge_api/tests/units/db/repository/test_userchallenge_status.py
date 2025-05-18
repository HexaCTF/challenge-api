import pytest
from unittest.mock import MagicMock
from challenge_api.db.repository.userchallenge import UserChallengesRepository
from challenge_api.db.repository.challenge import ChallengeRepository
from challenge_api.db.repository.userchallenge_status import UserChallengeStatusRepository
from challenge_api.exceptions.challenge_exceptions import ChallengeNotFound
from challenge_api.exceptions.userchallenge_exceptions import UserChallengeNotFound
from unittest.mock import patch

class TestBaseUserChallengeStatusRepository:
    def setup_method(self):
        self.session = MagicMock()
        self.userchallenge_repository = UserChallengesRepository(self.session)
        self.challenge_repository = ChallengeRepository(self.session)
        self.userchallenge_status_repository = UserChallengeStatusRepository(self.session)
        
class TestUserChallengeStatusRepository(TestBaseUserChallengeStatusRepository):
    def setup_method(self):
        super().setup_method()
        
    def test_create_success(self):
        pass 
    
    def test_create_userchallenge_does_not_exist(self):
        pass