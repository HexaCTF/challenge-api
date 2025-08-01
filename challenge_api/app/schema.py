from pydantic import BaseModel, Field
from typing import Optional

class ChallengeRequest(BaseModel):
    challenge_id: int = Field(..., description="Challenge ID")
    user_id: int = Field(..., description="User ID")
    
    @property
    def name(self) -> str:
        return f"challenge-{self.challenge_id}-{self.user_id}"

class ChallengeData(BaseModel):
    challenge_id: int = Field(..., description="Challenge ID")
    user_id: int = Field(..., description="User ID")

class UserChallengeData(BaseModel):
    C_idx: int = Field(..., description="Challenge index")
    user_id: int = Field(..., description="User ID")
    name: Optional[str] = Field(None, description="Challenge name")

class StatusData(BaseModel):
    idx: int = Field(..., description="Status ID")
    user_challenge_idx: int = Field(..., description="User challenge index")
    status: str = Field(..., description="Status value")
    port: int = Field(0, description="Port number")

class K8sChallengeData(BaseModel):
    challenge_id: int = Field(..., description="Challenge ID")
    user_id: int = Field(..., description="User ID")
    userchallenge_name: str = Field(..., description="User challenge name")
    definition: str = Field(..., description="Kubernetes definition")
    
