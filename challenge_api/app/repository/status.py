from challenge_api.app.model import UserChallengeStatus
from challenge_api.app.schema import UChallengeStatus
from challenge_api.exceptions.service import InvalidInputValue
from sqlalchemy.orm import Session

class UserChallengeStatusRepository:
    def __init__(self, session:Session):
        self.session = session
    
    def create(self, **kwargs):
        userchallenge_status = UserChallengeStatus(**kwargs)
        with self.session.begin():
            self.session.add(userchallenge_status)
                    
        return data
    
    def first(self, userchallenge_idx: int) -> StatusData:
        status = self._first(userchallenge_idx)
        return StatusData(
            idx=status.idx,
            user_challenge_idx=status.user_challenge_idx,
            status=status.status,
            port=status.port
        )
    
    def _first(self, userchallenge_idx: int) -> UserChallengeStatus:
        return self.session.query(UserChallengeStatus) \
            .filter_by(userchallenge_idx=userchallenge_idx) \
            .order_by(UserChallengeStatus.createdAt.desc()) \
            .first()
    
    def update(self, object_):
        if isinstance(object_, UChallengeStatus):
            status = self.get_by_id(id_=object_.userchallenge_idx)

            if status.status != "None":
                status.status = object_.status
            if object_.port != 0:  # port가 0이 아닐 때 업데이트
                status.port = object_.port
            
            self.session.update(status)
            self.session.commit()
            return status
        
        elif isinstance(object_, UserChallengeStatus):
            self.session.update(object_)
            self.session.commit()
            return object_
        
        else:
            raise InvalidInputValue(
                message = "Invalid input error when updating userchallenge status"
            )

    
