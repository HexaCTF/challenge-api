import pytest
from unittest.mock import MagicMock, patch
from challenge_api.db.repository.userchallenge import UserChallengesRepository
from challenge_api.db.repository.challenge import ChallengeRepository
from challenge_api.db.repository.userchallenge_status import UserChallengeStatusRepository
from challenge_api.exceptions.userchallenge_exceptions import UserChallengeNotFound
from challenge_api.exceptions.api_exceptions import InternalServerError
from challenge_api.db.models import UserChallengesStatus
from sqlalchemy.exc import SQLAlchemyError

@pytest.fixture
def fake_userchallenge_status():
    return UserChallengesStatus(
        port=1234,
        status='running',
        userChallenge_idx=1
    )

class TestBaseUserChallengeStatusRepository:
    def setup_method(self):
        self.session = MagicMock()
        self.userchallenge_repository = UserChallengesRepository(self.session)
        self.challenge_repository = ChallengeRepository(self.session)
        self.userchallenge_status_repository = UserChallengeStatusRepository(self.session)

class TestUserChallengeStatusRepository(TestBaseUserChallengeStatusRepository):
    def setup_method(self):
        super().setup_method()

    def test_create_success(self, fake_userchallenge_status):
        """
        Case: 사용자 챌린지 상태 생성 성공
        """
        # Given
        with patch.object(self.userchallenge_repository, '_get_by_idx', return_value=MagicMock()):
            # When
            result = self.userchallenge_status_repository.create(
                userchallenge_idx=fake_userchallenge_status.userChallenge_idx,
                port=fake_userchallenge_status.port,
                status=fake_userchallenge_status.status
            )
            
            # Then
            assert isinstance(result, UserChallengesStatus)
            assert result.port == fake_userchallenge_status.port
            assert result.status == fake_userchallenge_status.status
            assert result.userChallenge_idx == fake_userchallenge_status.userChallenge_idx
            self.session.add.assert_called_once()
            self.session.commit.assert_called_once()

    def test_create_userchallenge_not_found(self, fake_userchallenge_status):
        """
        Case: 사용자 챌린지가 존재하지 않는 경우
        """
        # Given
        with patch.object(
            self.userchallenge_repository, 
            '_get_by_idx', 
            side_effect=UserChallengeNotFound(error_msg=f"Userchallenge with idx {fake_userchallenge_status.userChallenge_idx} does not exist")
        ):
            # When & Then
            with pytest.raises(UserChallengeNotFound) as exc_info:
                self.userchallenge_status_repository.create(
                    userchallenge_idx=fake_userchallenge_status.userChallenge_idx,
                    port=fake_userchallenge_status.port,
                    status=fake_userchallenge_status.status
                )
            
            assert f"Userchallenge with idx {fake_userchallenge_status.userChallenge_idx} does not exist" in str(exc_info.value)
            self.session.add.assert_not_called()
            self.session.commit.assert_not_called()

    def test_create_db_error(self, fake_userchallenge_status):
        """
        Case: DB 에러 발생 시
        """
        # Given
        with patch.object(self.userchallenge_repository, '_get_by_idx', return_value=MagicMock()), \
             patch.object(self.session, 'add', side_effect=SQLAlchemyError("DB Error")):
            # When & Then
            with pytest.raises(InternalServerError) as exc_info:
                self.userchallenge_status_repository.create(
                    userchallenge_idx=fake_userchallenge_status.userChallenge_idx,
                    port=fake_userchallenge_status.port,
                    status=fake_userchallenge_status.status
                )
            
            assert "Error creating challenge status in db" in str(exc_info.value)
            self.session.rollback.assert_called_once()