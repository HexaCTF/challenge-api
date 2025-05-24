
from challenge_api.objects.usrchallenge import UChallengeStatus
from challenge_api.db.repository.userchallenge_status import UserChallengeStatusRepository

class UserChallengeStatusService:
    
    def __init__(self, status_repository: UserChallengeStatusRepository):
        self.status_repository = status_repository
    
    def create(self, id_, port=0, status="Pending"):
        status = UChallengeStatus(
            userchallenge_idx=id_,
            port=port,
            status=status
        )
        self.status_repository.create(status)
        return status
    
    def get_first(self, id_):
        return self.status_repository.first(id_)
    
    def update(self, object_):
        return self.status_repository.update(object_)
    
    
        
        