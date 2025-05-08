import pytest
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from extensions_manager import db

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