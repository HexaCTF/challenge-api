import os
from flask import Flask
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from hexactf.extensions.db.models import UserChallenges
from hexactf.extensions_manager import db

class TestDB:
    """Test database setup for integration testing"""
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        self.engine = create_engine(self.app.config['SQLALCHEMY_DATABASE_URI'])
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
        
        with self.app.app_context():
            db.init_app(self.app)
            db.create_all()  
            db.session.commit()

    def get_session(self):
        with self.app.app_context():
            return db.session
    
    def close(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

@pytest.fixture()
def test_db():
    """Provides an instance of TestDB for database tests inside a Flask app context"""
    test_db_instance = TestDB()
    with test_db_instance.app.app_context():        
        yield test_db_instance
    test_db_instance.close()
    
# autouse 명시적으로 call 하지 않아도 사용할 수 있는 옵션 
@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """Automatically set TEST_MODE=true for all tests"""
    os.environ["TEST_MODE"] = "true"
    