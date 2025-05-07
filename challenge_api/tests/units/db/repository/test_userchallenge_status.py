from db.repository import UserChallengeStatusRepository, UserChallengesRepository
# ===============================================
# create 테스트
# ===============================================
def test_userchallenge_status_create_success(test_db, fake_challenge_info, fake_userchallenge_status):
    """Test successful user challenge status creation"""
    # when
    session = test_db.get_session()
    userchallenge_status_repo = UserChallengeStatusRepository(session=session)
    
    # given
    user_challenges_repo = UserChallengesRepository(session=session)
    user_challenges_repo.create(fake_challenge_info)
    status = userchallenge_status_repo.create(fake_userchallenge_status.userChallenge_idx, fake_userchallenge_status.port)
    
    # then
    assert status is not None
    assert status.port == fake_userchallenge_status.port
    assert status.status == "None"
    assert status.userChallenge_idx == fake_userchallenge_status.userChallenge_idx
    

    
    
    