import logging
import os
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text
from hexactf.exceptions.api_exceptions import InternalServerError
from hexactf.extensions_manager import db
from hexactf.extensions.db.models import Challenges, UserChallenges, UserChallenges_status


class UserChallengesRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def create(self, u_idx: int, C_idx: int, userChallengeName: str,
               port: int, status: str = 'None') -> Optional[UserChallenges]:
        """
        새로운 사용자 챌린지 생성
        
        Args:
            u_idx (int): 사용자 아이디
            C_idx (int): 챌린지 ID
            userChallengeName (str): 챌린지 이름
            port (int): 챌린지 포트
            status (str): 챌린지 상태
        
        Returns:
            UserChallenges: 생성된 챌린지
        """
        try:
            challenge = UserChallenges(
                u_idx=u_idx,
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
        
    def is_running(self, challenge: UserChallenges) -> bool:
        """
        챌린지 실행 여부 확인
        
        Args:
            challenge (UserChallenges): 사용자 챌린지
        
        Returns:
            bool: 챌린지 실행 여부
        """
        return challenge.status == 'Running'

    def get_status(self, challenge_id, u_idx)  -> Optional[dict]:
        """
        챌린지 상태 조회
        
        Args:
            challenge_id (int): 챌린지 아이디
            u_idx (str): 사용자 이름
        
        Returns:
            str: 챌린지 상태
        """
        challenge = UserChallenges.query.filter_by(C_idx=challenge_id, u_idx=u_idx).first()
        if not challenge:
            return None
    
        if challenge.status == 'Running':
            return {'status': challenge.status, 'port': int(challenge.port)}
        return {'status': challenge.status}
    
        
class ChallengeRepository:
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
    

class UserChallengeStatusRepository:
    def __init__(self, session=None):
        self.session = session or db.session
    
    def create(self, port: int, status: str) -> Optional[UserChallenges]:
        """
        새로운 사용자 챌린지 상태 생성
        
        Args:
            port (int): 포트
            status (str): 상태
        
        Returns:
            UserChallenges: 생성된 사용자 챌린지 상태
        """
        try:
            challenge_status = UserChallenges_status(
                port=port,
                status=status
                createdAt=current_time_kst()
            )
            self.session.add(challenge_status)
            self.session.commit()
            return challenge_status
        except SQLAlchemyError as e:
            self.session.rollback()
            raise InternalServerError(error_msg=f"Error creating challenge status in db: {e}") from e
    
    def update_status(self,userchallenge_id:int, new_status: str) -> bool:
        """
        사용자 챌린지 상태 업데이트
        
        Args:
            challenge (UserChallenges): 사용자 챌린지
            new_status (str): 새로운 상태
        
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            
            db.session.execute(text("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED"))
            status = UserChallenges_status(
                idx=userchallenge_id,
                status=new_status
            )
            self.session.commit()
            return True
        except SQLAlchemyError as e:
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
            db.session.execute(text("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED"))
            fresh_challenge = self.session.merge(challenge)
            self.session.refresh(fresh_challenge) 
            fresh_challenge.port = port
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise InternalServerError(error_msg=f"Error updating challenge port: {e}") from e