from challenge_api.app.model import Challenges
from sqlalchemy.orm import Session
from typing import Optional

class ChallengeRepository:
    def __init__(self, session:Session):
        self.session = session
    
    def get_by_id(self, challenge_id: int) -> Challenges:
        return self.session.query(Challenges).filter(Challenges.idx == challenge_id).first()
    
    def get_name(self, challenge_id: int) -> str:
        return self.session.query(Challenges).filter(Challenges.idx == challenge_id).first().name
    
