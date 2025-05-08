from challenge_api.db.models import UserChallenges_status, UserChallenges
from challenge_api.extensions_manager import db
from challenge_api.objects.challenge_info import ChallengeInfo
from challenge_api.exceptions.api_exceptions import InternalServerError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from typing import Optional

class UserChallengeStatusRepository:
    def __init__(self, session=None):
        self.session = session or db.session
    
    def create(self, userchallenge_idx: int, port: int) -> Optional[UserChallenges_status]:
        """
        새로운 사용자 챌린지 상태 생성
        
        Args:
            port (int): 포트
            status (str): 상태
        
        Returns:
            UserChallenges: 생성된 사용자 챌린지 상태
        """
        try:
            # Check if UserChallenge exists
            user_challenge = self.session.get(UserChallenges, userchallenge_idx)
            if not user_challenge:
                raise InternalServerError(error_msg=f"UserChallenge not found with idx: {userchallenge_idx}")

            challenge_status = UserChallenges_status(
                port=port,
                status="None",
                userChallenge_idx=userchallenge_idx
            )
            self.session.add(challenge_status)
            self.session.commit()
            return challenge_status
        except SQLAlchemyError as e:
            self.session.rollback()
            raise InternalServerError(error_msg=f"Error creating challenge status in db: {e}") from e
    
    def get_recent_status(self, userchallenge_idx: int) -> Optional[UserChallenges_status]:
        """
        최근 사용자 챌린지 상태 조회
        
        Args:
            name (ChallengeName): 챌린지 이름 객체
            
        Returns:
            Optional[UserChallenges_status]: 가장 최근 상태, 없으면 None
        """
        try:
            return UserChallenges_status.query \
                .filter_by(userChallenge_idx=userchallenge_idx) \
                .order_by(UserChallenges_status.createdAt.desc()) \
                .first()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise InternalServerError(error_msg=f"Error getting recent challenge status in db: {e}") from e
    
       
        
    def update_status(self,status_idx:int, new_status: str) -> bool:
        """
        사용자 챌린지 상태 업데이트
        
        Args:
            challenge (UserChallenges): 사용자 챌린지
            new_status (str): 새로운 상태
        
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            
            status = self.session.get(UserChallenges_status, status_idx)
            if not status:
                raise InternalServerError(error_msg=f"UserChallengeStatus not found with idx: {status_idx}")
            status.status = new_status
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise InternalServerError(error_msg=f"Error updating challenge status: {e}") from e


    def update_port(self, status_idx:int, port: int) -> bool:
        """
        챌린지 포트 업데이트
        
        Args:
            challenge (UserChallenges): 사용자 챌린지
            port (int): 새로운 포트
        
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            status = self.session.get(UserChallenges_status, status_idx)
            if not status:
                raise InternalServerError(error_msg=f"UserChallengeStatus not found with idx: {status_idx}")
            status.port = port
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise InternalServerError(error_msg=f"Error updating challenge port: {e}") from e