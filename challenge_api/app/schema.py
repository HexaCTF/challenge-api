from pydantic import BaseModel

class ChallengeRequest(BaseModel):
    challenge_id: int
    user_id: int
    
    @property
    def name(self) -> str:
        return f"challenge-{self.challenge_id}-{self.user_id}"

@dataclass
class ChallengeData:
    challenge_id: int
    user_id: int

@dataclass
class UserChallengeData:
    C_idx: int
    user_id: int
    name: str

@dataclass
class StatusData:
    idx: int 
    user_challenge_idx: int
    status: str
    port: int

@dataclass
class K8sChallengeData:
    challenge_id: int
    user_id: int
    userchallenge_name: str
    definition: str
    
