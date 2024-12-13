from datetime import datetime


class BaseModel:
    """Base class for database models"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def from_db_row(cls, row):
        """Create instance from database row"""
        if row is None:
            return None
        return cls(**row)

    def to_dict(self):
        """Convert instance to dictionary"""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }


class Challenge(BaseModel):
    """Example model for challenges"""

    def __init__(
            self,
            id=None,
            title=None,
            description=None,
            created_at=None,
            **kwargs
    ):
        self.id = id
        self.title = title
        self.description = description
        self.created_at = created_at or datetime.now()
        super().__init__(**kwargs)
