from challenge_api.db.models import UserChallengesStatus, UserChallenges
from challenge_api.extensions_manager import db
from challenge_api.exceptions.api_exceptions import InternalServerError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from typing import Optional
from challenge_api.db.repository.userchallenge import UserChallengesRepository
from challenge_api.db.repository.challenge import ChallengeRepository
from challenge_api.exceptions.userchallenge_exceptions import UserChallengeNotFound

class UserChallengeStatusRepository:
    def __init__(self, session=None):
        self.session = session or db.session
        self.userchallenge_repository = UserChallengesRepository(self.session)
        self.challenge_repository = ChallengeRepository(self.session)
    
    def create(self, userchallenge_idx: int, port: int, status: str):
        """
        새로운 사용자 챌린지 상태 생성
        
        Args:
            port (int): 포트
            status (str): 상태
        
        Returns:
            UserChallenges: 생성된 사용자 챌린지 상태
            
        Raises:
            UserChallengeNotFound: 사용자 챌린지가 존재하지 않을 때
            InternalServerError: DB 에러 발생 시
        """
        try:
            # Check if UserChallenge exists
            try:
                self.userchallenge_repository.is_exist(userchallenge_idx)
            except UserChallengeNotFound as e:
                raise UserChallengeNotFound(error_msg=f"UserChallenge with idx {userchallenge_idx} does not exist") from e
            
            challenge_status = UserChallengesStatus(
                port=port,
                status=status,
                userChallenge_idx=userchallenge_idx
            )
            self.session.add(challenge_status)
            self.session.commit()
            return challenge_status
        except SQLAlchemyError as e:
            self.session.rollback()
            raise InternalServerError(error_msg=f"Error creating challenge status in db: {e}") from e
    
    def get_recent_status(self, userchallenge_idx: int) -> Optional[UserChallengesStatus]:
        """
        최근 사용자 챌린지 상태 조회
        
        Args:
            name (ChallengeName): 챌린지 이름 객체
            
        Returns:
            Optional[UserChallengesStatus]: 가장 최근 상태, 없으면 None
        """
        try:
            return UserChallengesStatus.query \
                .filter_by(userChallenge_idx=userchallenge_idx) \
                .order_by(UserChallengesStatus.createdAt.desc()) \
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
            
            status = self.session.get(UserChallengesStatus, status_idx)
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
            status = self.session.get(UserChallengesStatus, status_idx)
            if not status:
                raise InternalServerError(error_msg=f"UserChallengeStatus not found with idx: {status_idx}")
            status.port = port
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise InternalServerError(error_msg=f"Error updating challenge port: {e}") from e