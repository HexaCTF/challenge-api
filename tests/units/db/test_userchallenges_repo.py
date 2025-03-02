import pytest
from hexactf.exceptions.api_exceptions import InternalServerError
from hexactf.extensions.db.models import UserChallenges
from hexactf.extensions.db.repository import UserChallengesRepository

# ============================
# create_challenge 
# ============================

def test_create_challenge_success(test_db):
    """Test successful challenge creation"""
    session = test_db.get_session()
    user_challenges_repo = UserChallengesRepository(session=session)
    
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

def test_create_challenge_None_value_failed(test_db):
    """Test challenge creation failure due to database error"""
    
    session = test_db.get_session()
    user_challenges_repo = UserChallengesRepository(session=session)
        
    with pytest.raises(InternalServerError):
        user_challenges_repo.create(
            username=None,
            C_idx=1,
            userChallengeName="test_challenge",
            port=30000
        )

# ============================
# get_by_user_challenge_name
# ============================

def test_get_by_user_challenge_name_success(test_db):
    """Test retrieving a challenge by name"""
    session = test_db.get_session()
    user_challenges_repo = UserChallengesRepository(session=session)
    
    challenge = UserChallenges(
        username="test_user",
        C_idx=1,
        userChallengeName="test_challenge",
        port=30000
    )
    session.add(challenge)
    session.commit()
    
    result = user_challenges_repo.get_by_user_challenge_name("test_challenge")
    assert result == challenge, "Challenge should be retrieved by name"
    
def test_get_by_user_challenge_name_Invalid_name_failed(test_db):
    """Test retrieving a challenge by name"""
    session = test_db.get_session()
    user_challenges_repo = UserChallengesRepository(session=session)
    
    challenge = UserChallenges(
        username="test_user",
        C_idx=1,
        userChallengeName="test_challenge",
        port=30000
    )
    session.add(challenge)
    session.commit()
    
    result = user_challenges_repo.get_by_user_challenge_name("invalid_challenge")
    assert result is None, "Invalid challenge name should return None"


# ============================
# get_by_user_challenge_name
# ============================

def test_update_status_success(test_db):
    """Test updating challenge status"""
    session = test_db.get_session()
    user_challenges_repo = UserChallengesRepository(session=session)
    
    challenge = UserChallenges(
        username="test_user",
        C_idx=1,
        userChallengeName="test_challenge",
        port=30000,
        status="Running"
    )
    session.add(challenge)
    session.commit()
    
    success = user_challenges_repo.update_status(challenge, "Deleted")
    assert success
    assert challenge.status == "Deleted"
   
# ============================
# is_running
# ============================ 

def test_is_running_success(test_db):
    """Test checking if challenge is running"""
    session = test_db.get_session()
    user_challenges_repo = UserChallengesRepository(session=session)
    
    challenge = UserChallenges(
        username="test_user",
        C_idx=1,
        userChallengeName="test_challenge",
        port=30000,
        status="Running"
    )
    
    assert user_challenges_repo.is_running(challenge)
    challenge.status = "Stopped"
    assert not user_challenges_repo.is_running(challenge)

# ============================
# get_status
# ============================

def test_get_status_success(test_db):
    """Test retrieving challenge status"""
    session = test_db.get_session()
    user_challenges_repo = UserChallengesRepository(session=session)
    
    challenge = UserChallenges(
        username="test_user",
        C_idx=1,
        userChallengeName="test_challenge",
        port=30000,
        status="Running"
    )
    session.add(challenge)
    session.commit()
    
    result = user_challenges_repo.get_status(1, "test_user")
    assert result == {"status": "Running", "port": 30000}
    
    challenge.status = "Deleted"
    session.commit()
    result = user_challenges_repo.get_status(1, "test_user")
    assert result == {"status": "Deleted"}

def test_get_status_invalid_challenge_failed(test_db):
    """Test retrieving challenge status"""
    session = test_db.get_session()
    user_challenges_repo = UserChallengesRepository(session=session)
    
    challenge = UserChallenges(
        username="test_user",
        C_idx=1,
        userChallengeName="test_challenge",
        port=30000,
        status="Running"
    )
    session.add(challenge)
    session.commit()
    
    # 잘못된 challenge id 
    result = user_challenges_repo.get_status(2, "test_user")
    assert result is None
    
    # 잘못된 username
    result2 = user_challenges_repo.get_status(1, "wrong_user")
    assert result2 is None