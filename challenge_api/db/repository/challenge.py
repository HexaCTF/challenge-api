from sqlalchemy.exc import SQLAlchemyError
from challenge_api.db.models import Challenges
from challenge_api.exceptions.api_exceptions import InternalServerError, ChallengeNotFound

class ChallengeRepository:
    def __init__(self, session):
        self.session = session
    
    def _get_challenge(self, challenge_id: int) -> Challenges:
        """
        챌린지 아이디로 챌린지 조회
        
        Args:
            challenge_id (int): 챌린지 아이디
            
        Returns:
            Challenges: 챌린지 객체
            
        Raises:
            ChallengeNotFound: 챌린지가 존재하지 않을 때
            InternalServerError: DB 에러 발생 시
        """
        challenge = self.session.get(Challenges, challenge_id)
        if not challenge:
            raise ChallengeNotFound(error_msg=f"Challenge not found: {challenge_id}")
        
        return challenge
    
    def is_exist(self, challenge_id: int) -> bool:
        """
        챌린지 존재 여부 확인
        
        Args:
            challenge_id (int): 챌린지 아이디
            
        Returns:
            bool: 챌린지 존재 여부
            
        Raises:
            InternalServerError: DB 에러 발생 시
        """
        try:
            _  = self._get_challenge(challenge_id)
            return True
        except ChallengeNotFound:
            return False
        except SQLAlchemyError as e:
            raise InternalServerError(
                error_msg=f"Error checking challenge existence for id {challenge_id}: {str(e)}"
                ) from e
    
    def get_challenge_name(self, challenge_id: int) -> str:
        """
        챌린지 이름 조회
        
        Args:
            challenge_id (int): 챌린지 아이디
            
        Returns:
            str: 챌린지 이름
            
        Raises:
            ChallengeNotFound: 챌린지가 존재하지 않을 때
            InternalServerError: DB 에러 발생 시
        """
        try:
            challenge = self._get_challenge(challenge_id)
            return challenge.title
        except SQLAlchemyError as e:
            raise InternalServerError(
                error_msg=f"Error getting challenge name for id {challenge_id}: {str(e)}"
                ) from e
    