from dataclasses import dataclass

from challenge_api.objects.usrchallenge import UChallengeStatus
from challenge_api.db.repository.userchallenge_status import UserChallengeStatusRepository
from challenge_api.userchallenge.userchallenge import UserChallengeService
from challenge_api.exceptions.service import (
    ChallengeStatusNotFound,
)
class UserChallengeStatusService:
    
    def __init__(self, 
                 status_repository: UserChallengeStatusRepository,
                 userchallenge_svc: UserChallengeService
                 ):
        self.status_repository = status_repository
        self.userchallenge_svc = userchallenge_svc
    
    def create(self, id_, port=0, status="Pending"):
        status = UChallengeStatus(
            userchallenge_idx=id_,
            port=port,
            status=status
        )
        self.status_repository.create(status)
        return status
    
    def get_first(self, id_):
        status = self.status_repository.first(id_=id_)
        return UChallengeStatus(
            userchallenge_idx = status.userchallenge_idx,
            port = status.port,
            status= status.status
        )
    
    def update(self, object_):
        return self.status_repository.update(object_)
    
    def get_by_name(self,name:str) -> UChallengeStatus:
        userchallenge = self.userchallenge_svc.get_by_name(name=name)
        
        status = self.get_first(id_=userchallenge.idx)
        if not status:
            raise ChallengeStatusNotFound(message=f'status information does not found: {name}')
        return status

    
        
        
            
    
    
        
        