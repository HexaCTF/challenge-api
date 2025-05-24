from challenge_api.db.repository.challenge import ChallengeRepository
from challenge_api.objects.challenge import ChallengeRequest

class ChallengeService:
    def __init__(self, challenge_repository: ChallengeRepository):
        self.challenge_repository = challenge_repository
    
    def is_exist(self, request:ChallengeRequest) -> bool:
        return self.challenge_repository.get_by_id(request.challenge_id) is not None
    