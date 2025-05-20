class ChallengeRequest():
    def __init__(self, challenge_id: int, user_id: int):
        self._challenge_id = challenge_id
        self._user_id = user_id
    
    @property
    def challenge_id(self) -> int:
        return self._challenge_id
    
    @property
    def user_id(self) -> int:
        return self._user_id
    @property
    def name(self) -> str:
        return f"challenge-{self.challenge_id}-{self.user_id}"
    
    @challenge_id.setter
    def challenge_id(self, value: int):
        self._challenge_id = value
    
    @user_id.setter
    def user_id(self, value: int):
        self._user_id = value
        
    
    