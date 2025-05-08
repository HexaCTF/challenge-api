import pytest

from db.models import UserChallenges_status

@pytest.fixture
def fake_userchallenge_status():
    return UserChallenges_status(
        port=1, 
        userChallenge_idx=1
    )