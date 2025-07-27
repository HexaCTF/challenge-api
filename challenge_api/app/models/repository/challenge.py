from challenge_api.db.models import Challenges
from typing import Optional
from challenge_api.db.repository.base import BaseRepository


class ChallengeRepository(BaseRepository):
    def __init__(self, session=None):
        super().__init__(session)
    
    def get(self, **kwargs):
        pass 
    
    def create(self, object_):
        pass 
    
    def get_by_id(self, id_: int) -> Challenges:
        return self.session.get(Challenges, id_)
        
    def update(self, object_):
        if isinstance(object_, Challenges):
            self.session.update(object_)
            self.session.commit()
            return object_
        return None
    
    def delete(self, object_):
        pass 
    
