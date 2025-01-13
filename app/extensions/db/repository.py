
import logging
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
from app.extensions_manager import db
from app.extensions.db.models import Challenges, UserChallenges

logger = logging.getLogger(__name__)

class UserChallengesRepository:
    def __init__(self, session=None):
        self.session = session or db.session

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
            self.session.add(challenge)
            self.session.commit()
            return challenge
        except SQLAlchemyError as e:
            logger.error(f"Error creating challenge: {e}")
            self.session.rollback()
            return None

    def get_by_user_challenge_name(self, userChallengeName: str) -> Optional[UserChallenges]:
        """챌린지 이름으로 조회"""
        return UserChallenges.query.filter_by(userChallengeName=userChallengeName).first()

    def update_status(self, challenge: UserChallenges, new_status: str) -> bool:
        """챌린지 상태 업데이트"""
        try:
            challenge.status = new_status
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating challenge status: {e}")
            self.session.rollback()
            return False

    def update_port(self, challenge: UserChallenges, port: int) -> bool:
        """챌린지 포트 업데이트"""
        try:
            challenge.port = port
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating challenge port: {e}")
            self.session.rollback()
            return False

    def is_running(self, challenge: UserChallenges) -> bool:
        """챌린지 실행 여부 확인"""
        return challenge.status == 'Running'

class ChallengeRepository:
    @staticmethod
    def get_challenge_name(challenge_id: int) -> Optional[str]:
        """
        Get challenge name (title) by challenge ID
        
        Args:
            challenge_id (int): The ID of the challenge to look up
            
        Returns:
            Optional[str]: The title of the challenge if found, None otherwise
        """
        challenge = Challenges.query.get(challenge_id)
        return challenge.title if challenge else None