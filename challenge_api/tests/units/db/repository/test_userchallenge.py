import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError

from challenge_api.db.repository.userchallenge import UserChallengesRepository
from challenge_api.objects.challenge import ChallengeRequest
from challenge_api.exceptions.userchallenge_exceptions import UserChallengeNotFound
from challenge_api.exceptions.challenge_exceptions import ChallengeNotFound
from challenge_api.db.repository.challenge import ChallengeRepository
from challenge_api.db.models import UserChallenges


@pytest.fixture
def mock_challengeInfo():
    return ChallengeRequest(
        user_id=1,
        challenge_id=1,
    )

@pytest.fixture
def mock_user_challenge():
    userchallenge = MagicMock()
    userchallenge.user_id = 1
    userchallenge.challenge_id = 1
    userchallenge.userChallengeName = "challenge-1-1"
    return userchallenge


class TestBaseUserChallengeRepository:
    def setup_method(self):
        self.mock_session = MagicMock()
        self.repository = UserChallengesRepository(self.mock_session)

class TestUserChallengeRepository(TestBaseUserChallengeRepository):
    def setup_method(self):
        super().setup_method()
        
    def test__get_by_name_success(self, mock_challengeInfo, mock_user_challenge):
        """
        Case: 챌린지 이름 존재 여부 확인
        """
        # Given
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user_challenge

        # When
        result = self.repository._get_by_name(mock_challengeInfo.name)

        # Then
        assert result == mock_user_challenge
        self.mock_session.query.return_value.filter_by.assert_called_once_with(userChallengeName=mock_challengeInfo.name)
    
    def test__get_by_name_not_found(self, mock_challengeInfo):
        """
        Case: 챌린지 이름 존재 여부 확인
        """
        # Given
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # When & Then
        with pytest.raises(UserChallengeNotFound) as exc_info:
            self.repository._get_by_name(mock_challengeInfo.name)

        assert f"Userchallenge with name {mock_challengeInfo.name} does not exist" in str(exc_info.value)
        self.mock_session.query.return_value.filter_by.assert_called_once_with(userChallengeName=mock_challengeInfo.name)
        
    
    def test_is_exist_success(self, mock_challengeInfo, mock_user_challenge):
        """
        Case: 챌린지 이름 존재 여부 확인
        """
        # Given
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user_challenge

        # When
        result = self.repository.is_exist(mock_challengeInfo)

        # Then
        assert result is True
        self.mock_session.query.return_value.filter_by.assert_called_once_with(userChallengeName=mock_challengeInfo.name)
        
    def test_is_exist_not_found(self, mock_challengeInfo):
        """
        Case: 챌린지 이름 존재 여부 확인
        """
        # Given
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # When
        result = self.repository.is_exist(mock_challengeInfo)

        # Then
        assert result is False
        self.mock_session.query.return_value.filter_by.assert_called_once_with(userChallengeName=mock_challengeInfo.name)

    def test_create_success(self, mock_challengeInfo):
        """
        Case: 새로운 사용자 챌린지 생성 성공
        """
        # Given
        mock_challenge = MagicMock()
        mock_challenge.C_idx = mock_challengeInfo.challenge_id
        mock_challenge.user_idx = mock_challengeInfo.user_id
        mock_challenge.userChallengeName = mock_challengeInfo.name

        with patch.object(ChallengeRepository, 'is_exist', return_value=True):
            # When
            result = self.repository.create(mock_challengeInfo)

            # Then
            assert result.C_idx == mock_challengeInfo.challenge_id
            assert result.user_idx == mock_challengeInfo.user_id
            assert result.userChallengeName == mock_challengeInfo.name
            self.mock_session.add.assert_called_once()
            self.mock_session.commit.assert_called_once()

    def test_create_challenge_not_found(self, mock_challengeInfo):
        """
        Case: 챌린지가 존재하지 않는 경우
        """
        # Given
        with patch.object(ChallengeRepository, 'is_exist', return_value=False):
            # When & Then
            with pytest.raises(ChallengeNotFound) as exc_info:
                self.repository.create(mock_challengeInfo)

            assert f"Challenge with id {mock_challengeInfo.challenge_id} does not exist" in str(exc_info.value)
            self.mock_session.rollback.assert_not_called()

    def test_get_by_name_success(self, mock_challengeInfo, mock_user_challenge):
        """
        Case: 사용자 챌린지 이름 조회
        """
        # Given
        with patch.object(self.repository, '_get_by_name', return_value=mock_user_challenge):
            # When
            result = self.repository.get_by_name(mock_challengeInfo.name)

            # Then
            assert result == mock_user_challenge
    
    def test_get_by_name_not_found(self, mock_challengeInfo):
        """
        Case: 사용자 챌린지 이름 조회
        """
        # Given
        with patch.object(
            self.repository, '_get_by_name',
            side_effect=UserChallengeNotFound(error_msg=f"Userchallenge with name {mock_challengeInfo.name} does not exist")
        ):
            # When & Then
            with pytest.raises(UserChallengeNotFound) as exc_info:
                self.repository.get_by_name(mock_challengeInfo.name)

            assert self.repository._get_by_name.call_count == 1
            assert f"Userchallenge with name {mock_challengeInfo.name} does not exist" in str(exc_info.value)
                
