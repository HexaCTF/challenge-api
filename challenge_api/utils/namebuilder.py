from typing import Optional
import re

from objects.challenge_info import ChallengeInfo

class NameBuilder:
    def __init__(self, challenge_id: int, user_id: int):
        self._challenge_id = challenge_id
        self._user_id = user_id
        
    def _is_valid_name(self, name:str) -> bool:
        """Kubernetes 리소스 이름 유효성 검사"""
        name = self.challenge_name.lower()
        if not name or len(name) > 253:
            return False
        pattern = r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
        return bool(re.match(pattern, name))
    
    def build(self) -> Optional[ChallengeInfo]:
        """
        챌린지 이름 빌더 
        
        """
        # TODO: Error Handling 추가 필요 
        challenge_info = ChallengeInfo(challenge_id=self._challenge_id, user_id=self._user_id)
        if not self._is_valid_name(challenge_info.name):
            return None
        return challenge_info
            
    
        