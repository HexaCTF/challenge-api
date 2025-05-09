from challenge_api.db.models import UserChallenges
from challenge_api.objects.challenge_info import ChallengeInfo
from challenge_api.exceptions.api_exceptions import InternalServerError
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
import sys

from challenge_api.extensions_manager import db
from challenge_api.db.repository.challenge_repo import ChallengeRepository

class UserChallengesRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def create(self, challenge_info: ChallengeInfo) -> Optional[UserChallenges]:
        """새로운 사용자 챌린지 생성
        
        Args:
            challenge_name (ChallengeName): 챌린지 이름 객체
            
        Returns:
            Optional[UserChallenges]: 생성된 챌린지, 실패시 None
            
        Raises:
            InternalServerError: DB 작업 실패시
        """
        try:
            # 먼저 Challenge가 존재하는지 확인
            challenge_repo = ChallengeRepository(self.session)
            if not challenge_repo.is_exist(challenge_info.challenge_id):
                error_msg = f"Challenge with id {challenge_info.challenge_id} does not exist"
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                raise InternalServerError(error_msg=error_msg)
            
            challenge = UserChallenges(
                C_idx=challenge_info.challenge_id,
                user_idx=challenge_info.user_id,
                userChallengeName=challenge_info.name,
            )
            print(f"[DEBUG] Creating UserChallenge: {challenge.__dict__}", file=sys.stderr)
            self.session.add(challenge)
            self.session.commit()
            return challenge
            
        except SQLAlchemyError as e:
            self.session.rollback()
            error_msg = f"Error creating challenge in db: {str(e)}"
            print(f"[ERROR] {error_msg}", file=sys.stderr)
            raise InternalServerError(error_msg=error_msg) from e
        except Exception as e:
            self.session.rollback()
            error_msg = f"Unexpected error creating challenge: {str(e)}"
            print(f"[ERROR] {error_msg}", file=sys.stderr)
            raise InternalServerError(error_msg=error_msg) from e

    def get_by_user_challenge_name(self, userChallengeName: str) -> Optional[UserChallenges]:
        """
        사용자 챌린지 이름 조회
        
        Args:
            userChallengeName (str): 사용자 챌린지 이름
        
        Returns:
            UserChallenges: 사용자 챌린지
        """
        try:
            user_challenge = UserChallenges.query.filter_by(userChallengeName=userChallengeName).first()
            return user_challenge
        except SQLAlchemyError as e:
            raise InternalServerError(error_msg=f"Error getting challenge by name in db: {e}") from e
        
        
    def is_running(self, challenge: UserChallenges) -> bool:
        """
        챌린지 실행 여부 확인
        
        Args:
            challenge (UserChallenges): 사용자 챌린지
        
        Returns:
            bool: 챌린지 실행 여부
        """
        return challenge.status == 'Running'
    
    def is_exist(self, challenge_info: ChallengeInfo) -> bool:
        """챌린지 이름 존재 여부 확인
        
        Args:
            challenge_info (ChallengeInfo): 챌린지 이름 객체

        Returns:
            bool: 존재 여부
        """
        return (
            UserChallenges.query
            .filter_by(userChallengeName=challenge_info.name)
            .first() is not None
        )
    