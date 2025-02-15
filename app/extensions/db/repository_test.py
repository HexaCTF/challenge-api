import pytest
from unittest.mock import MagicMock
from app.repositories.user_challenges_repository import UserChallengesRepository
from app.extensions.db.models import UserChallenges

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def user_challenges_repo(mock_session):
    return UserChallengesRepository(session=mock_session)

@pytest.fixture
def mock_challenge():
    return UserChallenges(C_idx=1, username="test_user", status="Running", port=8080)

def test_get_status_running(user_challenges_repo, mock_session, mock_challenge):
    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_challenge
    result = user_challenges_repo.get_status(challenge_id=1, username="test_user")
    assert result == {'status': 'Running', 'port': 8080}

def test_get_status_not_running(user_challenges_repo, mock_session):
    mock_challenge = UserChallenges(C_idx=1, username="test_user", status="Stopped", port=8080)
    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_challenge
    result = user_challenges_repo.get_status(challenge_id=1, username="test_user")
    assert result == {'status': 'Stopped'}

def test_get_status_not_found(user_challenges_repo, mock_session):
    mock_session.query.return_value.filter_by.return_value.first.return_value = None
    result = user_challenges_repo.get_status(challenge_id=1, username="nonexistent_user")
    assert result is None
