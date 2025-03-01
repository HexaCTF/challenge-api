import pytest
from hexactf.exceptions.api_exceptions import InternalServerError

def test_create_challenge_success(db_mock):
    """Test successful challenge creation"""
    mock_session = db_mock.mock_session
    user_challenges_repo = db_mock.user_challenges_repo

    mock_session.commit.return_value = None  
    challenge = user_challenges_repo.create(
        username="test_user",
        C_idx=1,
        userChallengeName="test_challenge",
        port=30000
    )

    assert challenge is not None
    assert challenge.username == "test_user"
    assert challenge.C_idx == 1
    assert challenge.userChallengeName == "test_challenge"
    assert challenge.port == 30000

def test_create_challenge_db_error(db_mock):
    """Test challenge creation failure due to database error"""
    mock_session = db_mock.mock_session
    user_challenges_repo = db_mock.user_challenges_repo

    mock_session.commit.side_effect = InternalServerError("Database error")

    with pytest.raises(InternalServerError):
        user_challenges_repo.create(
            username="test_user",
            C_idx=1,
            userChallengeName="test_challenge",
            port=30000
        )
