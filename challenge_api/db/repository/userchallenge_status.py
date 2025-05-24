from challenge_api.db.models import UserChallengeStatus
from challenge_api.objects.usrchallenge import UChallengeStatus
from challenge_api.db.repository.base import BaseRepository
from challenge_api.exceptions.service import InvalidInputValue

class UserChallengeStatusRepository(BaseRepository):
    def __init__(self, session=None):
        super().__init__(session)
    
    def create(self, object_):
        if isinstance(object_, UChallengeStatus):
            userchallenge_status = UserChallengeStatus(
                userChallenge_idx=object_.userchallenge_idx,
                port=object_.port,
                status=object_.status
            )
            self.session.add(userchallenge_status)
            self.session.commit()
            return userchallenge_status
        else:
            raise InvalidInputValue(
                message = "Invalid input error when creating userchallenge status"
            )

    def get(self, **kwargs):
        return self.session.query(UserChallengeStatus).filter_by(**kwargs).first()
    
    def get_by_id(self, id_):
        return self.session.query(UserChallengeStatus).filter_by(idx=id_).first()
    
    def first(self, id_):
        return self.session.query(UserChallengeStatus) \
            .filter_by(id_=id_) \
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

    
