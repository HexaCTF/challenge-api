from pydantic import BaseModel

class ChallengeInfo(BaseModel):
    challenge_id: int
    user_id: int
    
    @property
    def name(self) -> str:
        return f"challenge-{self.challenge_id}-{self.user_id}"
    

class UserChallengeStatus:
    def __init__(self, port:int, status:str):
        self._port = port
        self._status = status

    def to_dict(self):
        return {
            'port': self._port,
            'status': self._status
        }
    
    def __str__(self):
        return f"Port: {self._port}, Status: {self._status}"
    
    def __repr__(self):
        return f"UserChallengeStatus(port={self._port}, status={self._status})"
    