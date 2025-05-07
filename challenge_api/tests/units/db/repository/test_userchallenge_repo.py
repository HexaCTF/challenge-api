import pytest
from exceptions.api_exceptions import InternalServerError
from db.models import UserChallenges
from db.repository import UserChallengesRepository

# ===============================================
# create 테스트
# ===============================================
def test_userchallenge_create_success(test_db, fake_challenge_info):
    """Test successful user challenge creation"""
    # when
    session = test_db.get_session()
    user_challenges_repo = UserChallengesRepository(session=session)
    
    # given
    challenge = user_challenges_repo.create(fake_challenge_info)
    
    # then
    assert challenge is not None
    assert challenge.user_idx == fake_challenge_info.user_id
    assert challenge.C_idx == fake_challenge_info.challenge_id
    assert challenge.userChallengeName == fake_challenge_info.name
    

# ===============================================
# is_exist 테스트
# ===============================================
def test_userchallenge_is_exist_success(test_db, fake_challenge_info):
    """Test successful user challenge existence check"""
    # when
    session = test_db.get_session()
    user_challenges_repo = UserChallengesRepository(session=session)
    
    # given
    user_challenges_repo.create(fake_challenge_info)
    
    # then
    assert user_challenges_repo.is_exist(fake_challenge_info) is True
    

    
        
        
        
        