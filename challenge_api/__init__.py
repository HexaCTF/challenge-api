import sys

from flask import Flask
from typing import Type

from .config import Config
from .model.db_manager import db
from .container import Container

class FlaskApp:
    def __init__(self, config_class: Type[Config] = Config):
        
        self.app = Flask(__name__)
        self.app.config.from_object(config_class)
        
        self._init_db()
        self._setup_blueprints()
        self._inject()

    
    def _init_db(self):
        # DB 초기화
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()

    def _inject(self):
        self.app.container = Container(db.session)

    def _setup_blueprints(self):
        """Blueprint 등록"""
        from challenge_api.api import v1
        from challenge_api.app.api.userchallenge import userchallenge_bp
        
        v1.register_blueprint(userchallenge_bp, url_prefix='/userchallenges')   
        self.app.register_blueprint(v1)
    
    def run(self, **kwargs):
        """애플리케이션 실행"""
        self.app.run(**kwargs)

def create_app(config_class: Type[Config] = Config):
    flask_app = FlaskApp(config_class)
    return flask_app.app
