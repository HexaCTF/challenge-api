from challenge_api.db.models import UserChallengesStatus, UserChallenges
from challenge_api.extensions_manager import db
from challenge_api.objects.challenge_info import ChallengeInfo
from challenge_api.exceptions.api_exceptions import InternalServerError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from typing import Optional

class UserChallengeStatusRepository:
    def __init__(self, session=None):
        """
        Repository 초기화
        
        Args:
            session: SQLAlchemy 세션 (선택사항)
        """
        self.session = session
        if not self.session:
            from flask import current_app
            if current_app:
                self.session = db.session
            else:
                # Flask context 없는 경우 새로운 세션 생성
                self.session = db.create_scoped_session()
        print(f"UserChallengeStatusRepository initialized with session: {self.session}")
    
    def create(self, userchallenge_idx: int, port: int, status: str) -> Optional[UserChallengesStatus]:
        """
        새로운 사용자 챌린지 상태 생성
        
        Args:
            userchallenge_idx (int): 사용자 챌린지 ID
            port (int): 포트
            status (str): 상태
        
        Returns:
            UserChallenges: 생성된 사용자 챌린지 상태
        """
        print(f"=== Creating UserChallengeStatus ===")
        print(f"Parameters: idx={userchallenge_idx}, port={port}, status={status}")
        
        try:
            # Check if UserChallenge exists
            user_challenge = self.session.get(UserChallenges, userchallenge_idx)
            if not user_challenge:
                print(f"UserChallenge not found with idx: {userchallenge_idx}")
                raise InternalServerError(error_msg=f"UserChallenge not found with idx: {userchallenge_idx}")

            print(f"Found UserChallenge: {user_challenge.idx}")
            
            challenge_status = UserChallengesStatus(
                port=port,
                status=status,
                userChallenge_idx=userchallenge_idx
            )
            
            print(f"Created UserChallengeStatus object")
            print(f"Adding to session...")
            self.session.add(challenge_status)
            
            print("Flushing session...")
            self.session.flush()  # ID 생성을 위해 flush

            if not challenge_status.idx:  # ID 확인
                print("No ID generated for challenge status")
                self.session.rollback()
                raise InternalServerError(error_msg="Failed to create challenge status - no ID generated")

            print(f"Generated ID: {challenge_status.idx}")
            print("Committing transaction...")
            self.session.commit()
            print(f"Successfully committed status with ID {challenge_status.idx}")

            # DB에서 다시 조회하여 반환
            print("Verifying created status...")
            created_status = self.session.get(UserChallengesStatus, challenge_status.idx)
            if not created_status:
                print("Failed to retrieve created challenge status")
                raise InternalServerError(error_msg="Failed to retrieve created challenge status")

            print(f"Successfully verified status: {created_status.idx}")
            return created_status

        except SQLAlchemyError as e:
            print(f"SQLAlchemy error while creating challenge status: {str(e)}")
            self.session.rollback()
            raise InternalServerError(error_msg=f"Error creating challenge status in db: {e}") from e
        except Exception as e:
            print(f"Unexpected error while creating challenge status: {str(e)}")
            self.session.rollback()
            raise InternalServerError(error_msg=f"Unexpected error creating challenge status: {e}") from e
    
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