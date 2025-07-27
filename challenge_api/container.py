from challenge_api.db.repository.challenge import ChallengeRepository
from challenge_api.db.repository.userchallenge import UserChallengesRepository
from challenge_api.db.repository.userchallenge_status import UserChallengeStatusRepository

from challenge_api.userchallenge.challenge import ChallengeService
from challenge_api.userchallenge.userchallenge import UserChallengeService
from challenge_api.userchallenge.status import UserChallengeStatusService
from challenge_api.userchallenge.k8s import K8sManager

class Container:
    def __init__(self, db_session):
        # Repository
        self.challenge_repo = ChallengeRepository(db_session)
        self.userchallenge_repo = UserChallengesRepository(db_session)
        self.userchallenge_status_repo = UserChallengeStatusRepository(db_session)

        # Services
        self.challenge_service = ChallengeService(self.challenge_repo)
        self.userchallenge_service = UserChallengeService(
            self.userchallenge_repo,
            self.challenge_service
        )
        self.status_service = UserChallengeStatusService(
            self.userchallenge_status_repo,
            self.userchallenge_service
        )

        # Manager
        self.k8s_manager = K8sManager(
            self.challenge_service,
            self.userchallenge_service,
            self.status_service
        )