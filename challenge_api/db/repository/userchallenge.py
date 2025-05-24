from typing import Optional

from challenge_api.db.models import UserChallenges
from challenge_api.objects.challenge import ChallengeRequest
from challenge_api.db.repository.base import BaseRepository
from challenge_api.db.repository.challenge import ChallengeRepository
from challenge_api.exceptions.service import InvalidInputValue

class UserChallengesRepository(BaseRepository):
    def __init__(self, session=None):
        super().__init__(session)
        self.challenge_repo = ChallengeRepository(session=self.session)
        
    
    def create(self, object_) -> Optional[UserChallenges]:
        userchallenge = None
        if isinstance(object_, ChallengeRequest):
            userchallenge = UserChallenges(
                C_idx=object_.challenge_id,
                user_idx=object_.user_id,
                userChallengeName=object_.name
            )
        else:
            raise InvalidInputValue(
                message = "Invalid input error when creating userchallenge"
            )
        self.session.add(userchallenge)
        self.session.commit()
        return userchallenge
        
    
    def get_by_id(self, id_) -> Optional[UserChallenges]:
        return self.session.query(UserChallenges).filter_by(id_=id_).first()
    
    def get(self, **kwargs) -> Optional[UserChallenges]:
        return self.session.query(UserChallenges).filter_by(**kwargs).first()
    
    def update(self, object_):
        raise NotImplementedError("Subclasses must implement this method")

    def delete(self, object_):
        raise NotImplementedError("Subclasses must implement this method")
    
 