from abc import ABC, abstractmethod

class BaseRepository(ABC):
    def __init__(self, session=None):
        self.session = session

    def create(self, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_by_id(self, id_):
        raise NotImplementedError("Subclasses must implement this method")
    
    def update(self, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")

    def delete(self, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")
    
    
    