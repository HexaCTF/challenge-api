import os
import sys

from flask import Flask
from typing import Type

from challenge_api.exceptions.http import BaseHttpException
from challenge_api.api.challenge_api import challenge_bp
from challenge_api.config import Config
from challenge_api.extensions.kafka.handler import MessageHandler
from challenge_api.extensions_manager import kafka_consumer
from challenge_api.db.db_manager import db

from challenge_api.container import Container

def start_kafka_consumer(app):
    """Start Kafka consumer in a separate thread"""
    with app.app_context():
        kafka_consumer.start_consuming(MessageHandler.handle_message)

class FlaskApp:
    def __init__(self, config_class: Type[Config] = Config):
        
        self.app = Flask(__name__)
        self.app.config.from_object(config_class)
        
        # 초기 설정
        # self._init_kafka()
        self._init_db()
        self._register_error_handlers()
        self._setup_blueprints()
        self._inject()

    def _init_kafka(self):
        """Extensions 초기화"""
        # Kafka 초기화
        kafka_consumer.init_app(self.app)
        kafka_consumer.start_consuming(MessageHandler.handle_message)
    
    def _init_db(self):
        # DB 초기화
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()

    def _inject(self):
        self.app.container = Container(db.session)
                
    
    def _register_error_handlers(self):
        """에러 핸들러 등록"""

        @self.app.errorhandler(BaseHttpException)
        def handle_challenge_error(error):
            print(f"[DEBUG] error: {error.__dict__}", file=sys.stderr)
            response = {
                'error': {
                    'message': error.message,
                }
            }
            return response, error.status_code

    def _setup_blueprints(self):
        """Blueprint 등록"""

        self.app.register_blueprint(challenge_bp, url_prefix='/v1/user-challenges')
    
    def run(self, **kwargs):
        """애플리케이션 실행"""
        self.app.run(**kwargs)

def create_app(config_class: Type[Config] = Config):
    """Factory pattern을 위한 생성 함수"""
    flask_app = FlaskApp(config_class)
    return flask_app.app
