from challenge_api.db.models import Challenges
from challenge_api.extensions_manager import db
from challenge_api.objects.challenge_info import ChallengeInfo
from challenge_api.exceptions.api_exceptions import InternalServerError
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from challenge_api.db.repository.base import BaseRepository

class ChallengeRepository(BaseRepository):
    def __init__(self, session=None):
        super().__init__(session)
        
    def create(self, **kwargs):
        pass 
    
    def get_by_id(self, id_: int) -> Optional[Challenges]:
        return Challenges.query.get(idx=id_)
        
    def update(self, **kwargs):
        pass 
    
    def delete(self, **kwargs):
        pass 
    
    def is_exist(self, challenge_id: int) -> bool:
        """
        챌린지 아이디 존재 여부 확인
        
        Args:
            challenge_id (int): 챌린지 아이디
        
        """
        return self.get_by_id(id_=challenge_id) is not None 
        
    
    def get_name(self, challenge_id: int) -> Optional[str]:
        """
        챌린지 아이디로 챌린지 조회
        
        Args:
            challenge_id (int): 챌린지 아이디  
        
        Returns:
            str: 챌린지 이름
        """
        challenge = self.get_by_id(id_=challenge_id)
        return challenge.title if challenge else None
    