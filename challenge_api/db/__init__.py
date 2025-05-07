__version__ = '1.0.0'

__all__ = ['MariaDBConfig']

from flask_sqlalchemy import SQLAlchemy
from challenge_api.extensions.db.config import MariaDBConfig
