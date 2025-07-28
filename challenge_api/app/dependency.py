# dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from challenge_api.app.service.userchallenge import UserChallengeService
from challenge_api.app.service.challenge import ChallengeService
from challenge_api.app.repository.userchallenge import UserChallengeRepository
from challenge_api.app.repository.challenge import ChallengeRepository
from challenge_api.app.manager.k8s import K8sManager
from challenge_api.app.external.database.database import SessionLocal

# Database 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Repository 의존성들
def get_challenge_repository(db: Session = Depends(get_db)):
    return ChallengeRepository(db)

def get_user_challenge_repository(db: Session = Depends(get_db)):
    return UserChallengeRepository(db)

def get_status_repository(db: Session = Depends(get_db)):
    return StatusRepository(db)

# External Service 의존성들
def get_k8s_manager():
    return K8sManager()

# Service 의존성들
def get_challenge_service(
    challenge_repo: ChallengeRepository = Depends(get_challenge_repository)
):
    return ChallengeService(challenge_repo)

def get_user_challenge_service(
    user_challenge_repo: UserChallengeRepository = Depends(get_user_challenge_repository),
    challenge_repo: ChallengeRepository = Depends(get_challenge_repository),
    status_repo: StatusRepository = Depends(get_status_repository),
    k8s_manager: K8sManager = Depends(get_k8s_manager)
):
    return UserChallengeService(
        user_challenge_repo=user_challenge_repo,
        challenge_repo=challenge_repo,
        status_repo=status_repo,
        k8s_manager=k8s_manager
    )