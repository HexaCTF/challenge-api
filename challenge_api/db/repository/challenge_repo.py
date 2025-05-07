from db.models import Challenges
from extensions_manager import db
from objects.challenge_info import ChallengeInfo
from exceptions.api_exceptions import InternalServerError
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional

class ChallengeRepository:
    
    def __init__(self, session=None):
        self.session = session or db.session
        
    def is_exist(self, challenge_id: int) -> bool:
        """
        챌린지 아이디 존재 여부 확인
        
        Args:
            challenge_id (int): 챌린지 아이디
        
        """
        challenge = Challenges.query.get(challenge_id)
        return challenge is not None
    
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
    