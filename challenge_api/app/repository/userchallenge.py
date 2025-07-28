from typing import Optional

from challenge_api.db.models import UserChallenges
from challenge_api.app.schema import UserChallengeData
from challenge_api.app.repository.challenge import ChallengeRepository
from challenge_api.exceptions.service import InvalidInputValue
from sqlalchemy.orm import Session

class UserChallengesRepository():
    def __init__(self, session:Session):
        self.session:Session = session
        self.challenge_repo:ChallengeRepository = None
        
    def create(self, data:UserChallengeData) -> Optional[UserChallenges]:
        userchallenge = UserChallenges(**data.model_dump())
        
        with self.session.begin():
            challenge =self.challenge_repo.get_by_id(data.C_idx)
            
            self.session.add(userchallenge)
        return userchallenge
        
    
    def get_by_id(self, idx: int) -> Optional[UserChallenges]:
        return self.session.query(UserChallenges).filter_by(idx=idx).first()
    
    def get(self, **kwargs) -> Optional[UserChallenges]:
        return self.session.query(UserChallenges).filter_by(**kwargs).first()

    def is_exist(self, **kwargs) -> bool:
        return self.session.query(UserChallenges).filter_by(**kwargs).first() is not None

 