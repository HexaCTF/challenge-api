import pytest

from db.models import UserChallenges
from objects.challenge_info import ChallengeInfo

@pytest.fixture 
def fake_challenge_info():
    return ChallengeInfo(
        challenge_id=1,
        user_id=1,
        name="challenge-1-1"
    )



@pytest.fixture
def fake_userchallenge():
    return UserChallenges(
        user_idx=1,
        C_idx=1,
        userChallengeName="challenge-1-1",
        createdAt="2021-01-01 00:00:00"
    )
