from challenge_api.db.models import Challenges
from typing import Optional
from challenge_api.db.repository.base import BaseRepository


class ChallengeRepository(BaseRepository):
    def __init__(self, session=None):
        super().__init__(session)
        
    def create(self, object_):
        pass 
    
    def get_by_id(self, id_: int) -> Challenges:
        return self.session.get(Challenges, id_)
        
    def update(self, object_):
        pass 
    
    def delete(self, object_):
        pass 
    
