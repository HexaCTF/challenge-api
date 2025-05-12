import pytest
from unittest.mock import MagicMock
from sqlalchemy.exc import SQLAlchemyError

from challenge_api.db.repository.challenge_repo import ChallengeRepository
from challenge_api.exceptions.api_exceptions import InternalServerError
from challenge_api.exceptions.challenge_exceptions import ChallengeNotFound

class TestChallengeRepositoryGetChallenge:
    def setup_method(self):
        self.mock_session = MagicMock()
        self.repository = ChallengeRepository(self.mock_session)

    def test_success(self, mock_challenge):
        self.mock_session.query().get.return_value = mock_challenge

        result = self.repository._get_challenge(1)

        assert result == mock_challenge

    def test_challenge_does_not_exist(self):
        self.mock_session.query().get.side_effect = ChallengeNotFound("Challenge not found")

        with pytest.raises(ChallengeNotFound) as exc_info:
            self.repository._get_challenge(1)

        assert "Challenge not found" in str(exc_info.value)

    def raise_internal_server_error(self):
        self.mock_session.query().get.side_effect = SQLAlchemyError("DB error")

        with pytest.raises(InternalServerError) as exc_info:
            self.repository._get_challenge(1)

        assert "Error getting challenge by id 1" in str(exc_info.value)

class TestChallengeRepositoryIsExist:
    
    # 클래스 내부에서만 적용 
    def setup_method(self):
        self.mock_session = MagicMock()
        self.repository = ChallengeRepository(self.mock_session)

    
    def test_returns_true(self):
        """
        Case: Challenge가 존재하는 경우 
        """
        mock_challenge = MagicMock()
        self.mock_session.query().get.return_value = mock_challenge

        result = self.repository.is_exist(1)

        assert result is True
        self.mock_session.query().get.assert_called_once_with(1)


    def test_returns_false(self):
        """
        Case: Challenge가 존재하지 않는 경우 
        """
        self.mock_session.query().get.return_value = None

        result = self.repository.is_exist(999)

        assert result is False
        self.mock_session.query().get.assert_called_once_with(999)

    def raise_internal_server_error(self):
        """
        Case: Challenge name이 존재하지 않는 경우 
        """
        self.mock_session.query().get.side_effect = SQLAlchemyError("DB error")

        with pytest.raises(InternalServerError) as exc_info:
            self.repository.is_exist(1)

        assert "Error checking if challenge exists" in str(exc_info.value)

class TestChallengeRepositoryGetChallengeName:
    def setup_method(self):
        self.mock_session = MagicMock()
        self.repository = ChallengeRepository(self.mock_session)
    
    def test_success(self,mock_challenge):
        self.mock_session.query().get.return_value = mock_challenge

        result = self.repository.get_challenge_name(1)

        assert result == mock_challenge.title

    def test_challenge_name_does_not_exist(self):
        self.mock_session.query().get.side_effect = ChallengeNotFound("Challenge not found")

        with pytest.raises(ChallengeNotFound) as exc_info:
            self.repository.get_challenge_name(1)

        assert "Challenge not found" in str(exc_info.value)
