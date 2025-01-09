
import logging
from typing import List, Optional
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from app.extensions_manager import db
from app.extensions.db.models import UserChallenges, current_time_kst

logger = logging.getLogger(__name__)

class UserChallengesRepository:
        
    def create(self, username: str, C_idx: int, userChallengeName: str, 
              port: int, status: str = 'None') -> Optional[UserChallenges]:
       """새로운 사용자 챌린지 생성"""
       
       try:
           challenge = UserChallenges(
               username=username,
               C_idx=C_idx,
               userChallengeName=userChallengeName,
               port=port,
               status=status
           )
           db.session.add(challenge)
           db.session.commit()
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
       try:
           challenge.status = new_status
           db.session.commit()
           return True
       except SQLAlchemyError as e:
           logger.error(f"Error updating challenge status: {e}")
           db.session.rollback()
           return False

    
    def update_port(self, challenge: UserChallenges, port: int) -> bool:
        """챌린지 포트 업데이트"""
        
        
        try:
            challenge.port = port
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating challenge port: {e}")
            db.session.rollback()
            return False