import pytest
from unittest.mock import MagicMock, patch
from challenge_api.db.models import Challenges

from challenge_api.db.repository.challenge import ChallengeRepository
from challenge_api.exceptions.api_exceptions import InternalServerError, ChallengeNotFound

@pytest.fixture
def mock_challenge():
    """Mock challenge object"""
    challenge = MagicMock()
    challenge.id = 1
    challenge.title = "Test Challenge"
    return challenge


class TestBaseChallengeRepository:
    def setup_method(self):
        self.mock_session = MagicMock()
        self.repository = ChallengeRepository(self.mock_session)
        
class TestChallengeRepository(TestBaseChallengeRepository):
    def setup_method(self):
        """각 테스트 메서드 실행 전에 호출되는 설정"""
        super().setup_method()
    
    # _get_challenge
    def test_get_challenge_success(self, mock_challenge):
        """
        Case: 챌린지가 존재하는 경우
        """
        # Given
        self.mock_session.get.return_value = mock_challenge

        # When
        result = self.repository._get_challenge(1)

        # Then
        assert result == mock_challenge
        self.mock_session.get.assert_called_once_with(Challenges, 1)

    def test_get_challenge_not_found(self):
        """
        Case: 챌린지가 존재하지 않는 경우
        """
        # Given
        self.mock_session.get.return_value = None

        # When & Then
        with pytest.raises(ChallengeNotFound) as exc_info:
            self.repository._get_challenge(999)

        assert "Challenge not found: 999" in str(exc_info.value)
        self.mock_session.get.assert_called_once_with(Challenges, 999)

    # is_exist
    def test_is_exist_success(self, mock_challenge):
        """
        Case: 챌린지가 존재하는 경우
        """
        # Given
        with patch.object(self.repository, '_get_challenge', return_value=mock_challenge):
            # When
            result = self.repository.is_exist(1)

            # Then
            assert result is True
            self.repository._get_challenge.assert_called_once_with(1)
    
    def test_is_exist_not_found(self):
        """
        Case: 챌린지가 존재하지 않는 경우
        """
        # Given
        with patch.object(self.repository, '_get_challenge', side_effect=ChallengeNotFound(error_msg="Challenge not found: 999")):
            # When
            result = self.repository.is_exist(999)

            # Then
            assert result is False
            self.repository._get_challenge.assert_called_once_with(999)
    
    # get_challenge_name
    def test_get_challenge_name_success(self, mock_challenge):
        """
        Case: 챌린지가 존재하는 경우
        """
        # Given
        with patch.object(self.repository, '_get_challenge', return_value=mock_challenge):
            # When
            result = self.repository.get_challenge_name(1)

            # Then
            assert result == mock_challenge.title
            self.repository._get_challenge.assert_called_once_with(1)
        
    def test_get_challenge_name_not_found(self):
        """
        Case: 챌린지가 존재하지 않는 경우
        """
        # Given
        with patch.object(self.repository, '_get_challenge', side_effect=ChallengeNotFound(error_msg="Challenge not found: 999")):
            # When & Then
            with pytest.raises(ChallengeNotFound) as exc_info:
                self.repository.get_challenge_name(999)

            assert "Challenge not found: 999" in str(exc_info.value)
            self.repository._get_challenge.assert_called_once_with(999)
        
