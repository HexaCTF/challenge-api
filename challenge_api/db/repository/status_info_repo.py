from collections import Optional


from challenge_api.db.models import UserChallengesStatusInfo
from challenge_api.db import db
from challenge_api.exceptions.api_exceptions import InternalServerError

class StatusInfoRepository:
    def __init__(self, session=None):
        self.session = session or db.session
    
    def create(self, userchallenge_name: str, port: int, status: str) -> Optional[UserChallengesStatusInfo]:
        try:
            status_info = UserChallengesStatusInfo(
                userchallenge_name=userchallenge_name,
                port=port,
                status=status
            )
            self.session.add(status_info)
            self.session.flush()
            self.session.commit()
            
            return status_info
        except Exception as e:
            self.session.rollback()
            raise InternalServerError(error_msg=f"Error creating status info: {e}") from e
    
    def get_recent_status(self, userchallenge_name: str) -> Optional[UserChallengesStatusInfo]:
        try:
            return UserChallengesStatusInfo.query \
                .filter_by(userchallenge_name=userchallenge_name) \
                .order_by(UserChallengesStatusInfo.createdAt.desc()) \
                .first()
        except Exception as e:
            self.session.rollback()
            raise InternalServerError(error_msg=f"Error getting recent status info: {e}") from e

    def update_status(self, status_idx: int, new_status: str) -> bool:
        try:
            status_info = self.session.get(UserChallengesStatusInfo, status_idx)
            if not status_info:
                return False

            status_info.status = new_status
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise InternalServerError(error_msg=f"Error updating status info: {e}") from e
    
    