from typing import Optional

from challenge_api.db.repository.userchallenge import UserChallengesRepository
from challenge_api.userchallenge.challenge import ChallengeService
from challenge_api.objects.challenge import ChallengeRequest
from challenge_api.db.models import UserChallenges
from challenge_api.objects.usrchallenge import UChallengeStatus
from challenge_api.exceptions.service import UserChallengeNotFound, ChallengeNotFound

class UserChallengeService:
    
    def __init__(self, userchallenge_repository: UserChallengesRepository, challenge_service: ChallengeService):    
    
        self.userchallenge_repository = userchallenge_repository
        self.challenge_service = challenge_service
        
    def is_exist(self, request: ChallengeRequest) -> bool:
    
        return self.userchallenge_repository.get_by_id(request.challenge_id) is not None
    
    def get_by_name(self, name:str) -> Optional[UChallengeStatus]:
    
        kwarg = {
            "userChallengeName": name
        }        
        userchallenge = self.userchallenge_repository.get(**kwarg)
        if not userchallenge:
            raise UserChallengeNotFound(f"User challenge {name} not found")
        
        return userchallenge
        
    def create(self, request: ChallengeRequest) -> UserChallenges:
        
        if not self.challenge_service.is_exist(request):
            raise ChallengeNotFound(f"Challenge {request.challenge_id} not found")
        
        userchallenge = self.userchallenge_repository.create(request)
        return userchallenge

    
    
    
    