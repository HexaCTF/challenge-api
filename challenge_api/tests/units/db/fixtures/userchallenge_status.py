import pytest

from db.models import UserChallengesStatus

@pytest.fixture
def fake_userchallenge_status():
    return UserChallengesStatus(
        port=1, 
        userChallenge_idx=1
    )