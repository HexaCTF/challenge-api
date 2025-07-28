from challenge_api.app.repository.userchallenge import UserChallengesRepository
from challenge_api.app.repository.challenge import ChallengeRepository
from challenge_api.app.external.k8s import K8sManager
from challenge_api.app.schema import ChallengeRequest

class UserChallengeService:
    def __init__(
        self, 
        user_challenge_repo:UserChallengesRepository,
        challenge_repo:ChallengeRepository,
        status_repo:UserChallengeStatusRepository,
        k8s_manager:K8sManager
        ):
        
        self.user_challenge_repo = user_challenge_repo
        self.challenge_repo = challenge_repo
        self.k8s_manager = k8s_manager
    
    
    def create(self, data:ChallengeRequest):
        recent = self.status_repo.first(userchallenge_idx=data.user_id)
        if recent:
            return self._handle_existing_challenge(recent)
        
        return self._create_new_user_challenge(data)
    
    def _create_new_user_challenge(self, data:ChallengeRequest):
        self.user_challenge_repo.create(data)
        recent = self.status_repo.create(StatusData(userchallenge_idx=data.user_id))
        return self._handle_existing_challenge(recent)
    
    def _handle_existing_challenge(self, status_data:StatusData) -> int:
        if status_data.status == 'Running':
            return status_data.port
        
        k8s_data = K8sChallengeData(
            challenge_id=status_data.userchallenge_idx,
            user_id=status_data.userchallenge_idx,
            userchallenge_name=status_data.name,
            definition=self.challenge_repo.get_name(status_data.userchallenge_idx)
        )
        endpoint = self.k8s_manager.create(data)  
        if not endpoint:
            raise UserChallengeCreationException(message=f"Failed to get NodePort for Challenge: {request.name}")
        
        status_data.status = 'Running'
        status_data.port = endpoint
        self.status_repo.update(status_data)
        
        return status_data.port    
    