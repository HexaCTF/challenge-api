from pydantic import BaseModel

class ChallengeInfo(BaseModel):
    challenge_id: int
    user_id: int
    
    @property
    def name(self) -> str:
        return f"challenge-{self.challenge_id}-{self.user_id}"
    
    