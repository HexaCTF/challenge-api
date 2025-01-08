
import logging
from typing import List, Optional
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.extensions.db.models import UserChallenges, current_time_kst

logger = logging.getLogger(__name__)

class UserChallengesRepository:
    def __init__(self, session=None):
        self._session = session

    def get_session(self):
        if self._session is not None:
            return self._session
        
        # current_app을 통해 세션 획득
        try:
            return db.session
        except Exception as e:
            raise RuntimeError("Unable to get database session. Ensure you are within an application context.") from e
        
    def create(self, username: str, C_idx: int, userChallengeName: str, 
              port: int, status: str = 'None') -> Optional[UserChallenges]:
       """새로운 사용자 챌린지 생성"""
       session = self.get_session()
       
       try:
           challenge = UserChallenges(
               username=username,
               C_idx=C_idx,
               userChallengeName=userChallengeName,
               port=port,
               status=status
           )
           session.add(challenge)
           session.commit()
           return challenge
       except SQLAlchemyError as e:
           logger.error(f"Error creating challenge: {e}")
           db.session.rollback()
           return None

    def get_by_user_challenge_name(self, userChallengeName: str) -> Optional[UserChallenges]:
       """챌린지 이름으로 조회"""

       return UserChallenges.query.filter_by(userChallengeName=userChallengeName).first()

    def update_status(self, challenge: UserChallenges, new_status: str) -> bool:
       """챌린지 상태 업데이트"""
       session = self.get_session()
       try:
           challenge.status = new_status
           session.commit()
           return True
       except SQLAlchemyError as e:
           logger.error(f"Error updating challenge status: {e}")
           session.rollback()
           return False

    
    def update_port(self, challenge: UserChallenges, port: int) -> bool:
        """챌린지 포트 업데이트"""
        
        session = self.get_session()
        
        try:
            challenge.port = port
            session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating challenge port: {e}")
            session.rollback()
            return False