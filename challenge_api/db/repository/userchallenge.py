from challenge_api.db.models import UserChallenges
from challenge_api.objects.challenge import ChallengeRequest
from challenge_api.exceptions.api_exceptions import InternalServerError
from challenge_api.exceptions.challenge_exceptions import ChallengeNotFound
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional

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

    def _get_by_idx(self, userchallenge_idx: int) -> Optional[UserChallenges]:
        """사용자 챌린지 인덱스 조회
        
        Args:
            userchallenge_idx (int): 사용자 챌린지 인덱스
            
        Returns:
            Optional[UserChallenges]: 사용자 챌린지 객체
            
        Raises:
            UserChallengeNotFound: 사용자 챌린지가 존재하지 않을 때
        """
        challenge = self.session.query(UserChallenges).filter_by(idx=userchallenge_idx).first()
        if not challenge:
            raise UserChallengeNotFound(error_msg=f"Userchallenge with idx {userchallenge_idx} does not exist")
        return challenge

    def is_exist(self, userchallenge_idx: int) -> bool:
        """챌린지 이름 존재 여부 확인
        
        Args:
            userchallenge_idx (int): 사용자 챌린지 인덱스

        Returns:
            bool: 존재 여부
            
        Raises:
            UserChallengeNotFound: 사용자 챌린지가 존재하지 않을 때
        """
        if self._get_by_idx(userchallenge_idx) is None:
            return False 
        return True 
        
    
    def create(self, challenge_info: ChallengeRequest) -> Optional[UserChallenges]:
        """새로운 사용자 챌린지 생성
        
        Args:
            challenge_name (ChallengeName): 챌린지 이름 객체
            
        Returns:
            Optional[UserChallenges]: 생성된 챌린지, 실패시 None
            
        Raises:
            ChallengeNotFound: 챌린지가 존재하지 않을 때
            InternalServerError: DB 작업 실패시
        """
        
        # 먼저 Challenge가 존재하는지 확인
        challenge_repo = ChallengeRepository(self.session)
        if not challenge_repo.is_exist(challenge_info.challenge_id):
            error_msg = f"Challenge with id {challenge_info.challenge_id} does not exist"
            raise ChallengeNotFound(error_msg=error_msg)
        
        challenge = UserChallenges(
            C_idx=challenge_info.challenge_id,
            user_idx=challenge_info.user_id,
            userChallengeName=challenge_info.name,
        )
        self.session.add(challenge)
        self.session.commit()
        return challenge
            

    
    def get_by_name(self, userChallengeName: str) -> Optional[UserChallenges]:
        """사용자 챌린지 이름 조회
        
        Args:
            userChallengeName (str): 사용자 챌린지 이름
        """
        return self._get_by_name(userChallengeName)