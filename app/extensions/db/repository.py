
import logging
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
from app.exceptions.api import InternalServerError
from app.extensions_manager import db
from app.extensions.db.models import Challenges, UserChallenges


class UserChallengesRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def create(self, username: str, C_idx: int, userChallengeName: str,
               port: int, status: str = 'None') -> Optional[UserChallenges]:
        """
        새로운 사용자 챌린지 생성
        
        Args:
            username (str): 사용자 이름
            C_idx (int): 챌린지 ID
            userChallengeName (str): 챌린지 이름
            port (int): 챌린지 포트
            status (str): 챌린지 상태
        
        Returns:
            UserChallenges: 생성된 챌린지
        """
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
            self.session.rollback()
            raise InternalServerError(error_msg=f"Error creating challenge in db: {e}") from e

    def get_by_user_challenge_name(self, userChallengeName: str) -> Optional[UserChallenges]:
        """
        사용자 챌린지 이름 조회
        
        Args:
            userChallengeName (str): 사용자 챌린지 이름
        
        Returns:
            UserChallenges: 사용자 챌린지
        """
        user_challenge = UserChallenges.query.filter_by(userChallengeName=userChallengeName).first()
        if not user_challenge:
            return None
        return user_challenge
        

    def update_status(self, challenge: UserChallenges, new_status: str) -> bool:
        """
        사용자 챌린지 상태 업데이트
        
        Args:
            challenge (UserChallenges): 사용자 챌린지
            new_status (str): 새로운 상태
        
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            challenge.status = new_status
            self.session.add(challenge)  # Add this line to track the object
            self.session.flush()  
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            # logger.error(f"Error updating challenge status: {e}")
            self.session.rollback()
            raise InternalServerError(error_msg=f"Error updating challenge status: {e}") from e

    def update_port(self, challenge: UserChallenges, port: int) -> bool:
        """
        챌린지 포트 업데이트
        
        Args:
            challenge (UserChallenges): 사용자 챌린지
            port (int): 새로운 포트
        
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            challenge.port = port
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise InternalServerError(error_msg=f"Error updating challenge port: {e}") from e

    def is_running(self, challenge: UserChallenges) -> bool:
        """
        챌린지 실행 여부 확인
        
        Args:
            challenge (UserChallenges): 사용자 챌린지
        
        Returns:
            bool: 챌린지 실행 여부
        """
        return challenge.status == 'Running'

    def get_status(self, challenge_id, username) -> Optional[str]:
        """
        챌린지 상태 조회
        
        Args:
            challenge_id (int): 챌린지 아이디
            username (str): 사용자 이름
        
        Returns:
            str: 챌린지 상태
        """
        challenge = UserChallenges.query.filter_by(C_idx=challenge_id, username=username).first()
        return challenge.status if challenge else None

class ChallengeRepository:
    @staticmethod
    def get_challenge_name(challenge_id: int) -> Optional[str]:
        """
        챌린지 아이디로 챌린지 조회
        
        Args:
            challenge_id (int): 챌린지 아이디  
        
        Returns:
            str: 챌린지 이름
        """
        challenge = Challenges.query.get(challenge_id)
        return challenge.title if challenge else None