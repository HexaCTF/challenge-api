import pytest
from challenge_api.utils.namebuilder import NameBuilder
from challenge_api.objects.challenge_info import ChallengeInfo

@pytest.fixture
def fake_challengeinfo():
    return ChallengeInfo(challenge_id=1, user_id=1)

class TestNameBuilder:
    def setup_method(self):
        self.namebuilder = NameBuilder(1, 1)
        
    def test_success(self, fake_challengeinfo):
        info = self.namebuilder.build()
        
        assert info.challenge_id == 1
        assert info.user_id == 1
        assert info.name == "challenge-1-1"


        
        