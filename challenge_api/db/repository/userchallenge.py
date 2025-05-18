from challenge_api.db.models import UserChallenges
from challenge_api.objects.challenge_info import ChallengeInfo
from challenge_api.exceptions.api_exceptions import InternalServerError
from challenge_api.exceptions.challenge_exceptions import ChallengeNotFound
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
import sys

from challenge_api.db.repository.challenge import ChallengeRepository
from challenge_api.exceptions.userchallenge_exceptions import UserChallengeNotFound

class UserChallengesRepository: 
    def __init__(self, session=None):
        self.session = session 

    def _get_by_name(self, userChallengeName: str) -> Optional[UserChallenges]:
        """사용자 챌린지 이름 조회
        
        Args:
            userChallengeName (str): 사용자 챌린지 이름
        """
        challenge = self.session.query(UserChallenges).filter_by(userChallengeName=userChallengeName).first()
        if not challenge:
            raise UserChallengeNotFound(error_msg=f"Userchallenge with name {userChallengeName} does not exist")
        return challenge

    def is_exist(self, challenge_info: ChallengeInfo) -> bool:
        """챌린지 이름 존재 여부 확인
        
        Args:
            challenge_info (ChallengeInfo): 챌린지 이름 객체

        Returns:
            bool: 존재 여부
        """
        try:
            self._get_by_name(challenge_info.name)
            return True
        except UserChallengeNotFound:
            return False
    
    def create(self, challenge_info: ChallengeInfo) -> Optional[UserChallenges]:
        """새로운 사용자 챌린지 생성
        
        Args:
            challenge_name (ChallengeName): 챌린지 이름 객체
            
        Returns:
            Optional[UserChallenges]: 생성된 챌린지, 실패시 None
            
        Raises:
            ChallengeNotFound: 챌린지가 존재하지 않을 때
            InternalServerError: DB 작업 실패시
        """
        try:
            # 먼저 Challenge가 존재하는지 확인
            challenge_repo = ChallengeRepository(self.session)
            if not challenge_repo.is_exist(challenge_info.name):
                error_msg = f"Challenge with name {challenge_info.name} does not exist"
                raise ChallengeNotFound(error_msg=error_msg)
            
            challenge = UserChallenges(
                C_idx=challenge_info.challenge_id,
                user_idx=challenge_info.user_id,
                userChallengeName=challenge_info.name,
            )
            self.session.add(challenge)
            self.session.commit()
            return challenge
            
        except SQLAlchemyError as e:
            self.session.rollback()
            error_msg = f"Error creating challenge in db: {str(e)}"
            raise InternalServerError(error_msg=error_msg) from e
        except ChallengeNotFound as e:
            raise e
        except Exception as e:
            self.session.rollback()
            error_msg = f"Unexpected error creating challenge: {str(e)}"
            raise InternalServerError(error_msg=error_msg) from e

    
    def get_by_name(self, userChallengeName: str) -> Optional[UserChallenges]:
        """사용자 챌린지 이름 조회
        
        Args:
            userChallengeName (str): 사용자 챌린지 이름
        """
        return self._get_by_name(userChallengeName)
    # def get_by_user_challenge_name(self, userChallengeName: str) -> Optional[UserChallenges]:
    #     """
    #     사용자 챌린지 이름 조회
        
    #     Args:
    #         userChallengeName (str): 사용자 챌린지 이름
        
    #     Returns:
    #         UserChallenges: 사용자 챌린지
    #     """
    #     try:
    #         user_challenge = self.session.query(UserChallenges).filter_by(userChallengeName=userChallengeName).first()
    #         return user_challenge
    #     except SQLAlchemyError as e:
    #         raise InternalServerError(error_msg=f"Error getting challenge by name in db: {e}") from e
        
        
    # def is_running(self, challenge: UserChallenges) -> bool:
    #     """
    #     챌린지 실행 여부 확인
        
    #     Args:
    #         challenge (UserChallenges): 사용자 챌린지
        
    #     Returns:
    #         bool: 챌린지 실행 여부
    #     """
    #     return challenge.status == 'Running'
    
