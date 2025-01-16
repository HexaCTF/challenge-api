from flask import Flask, g, request
import threading
from datetime import datetime
from typing import Type
from logging_loki import LokiHandler
import logging

from app.api.challenge import challenge_bp
from app.config import Config
from app.exceptions.base import CustomBaseException
from app.exceptions.handlers import register_error_handler
from app.extensions.kafka.handler import MessageHandler
from app.extensions_manager import kafka_consumer, db

def start_kafka_consumer(app):
    """Start Kafka consumer in a separate thread"""
    with app.app_context():
        kafka_consumer.start_consuming(MessageHandler.handle_message)

class FlaskApp:
    def __init__(self, config_class: Type[Config] = Config):
        self.app = Flask(__name__)
        self.app.config.from_object(config_class)
        self.logger = self._setup_logger()

        # 초기 설정
        self._init_extensions()
        self._setup_middleware()
        self._register_error_handlers()
        self._setup_blueprints()
        self._setup_kafka()

    def _setup_logger(self) -> logging.Logger:
        """Loki 로거 설정"""
        handler = LokiHandler(
            url=self.app.config.get('LOKI_URL', 'http://loki:3100/loki/api/v1/push'),
            tags={"application": self.app.config.get('APP_NAME', 'flask-app')},
            version="1"
        )
        
        logger = logging.getLogger(self.app.config.get('APP_NAME', 'flask-app'))
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        return logger

    def _init_extensions(self):
        """Extensions 초기화"""
        # Kafka 초기화
        kafka_consumer.init_app(self.app)
        
        # DB 초기화
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()

    def _setup_middleware(self):
        """미들웨어 설정"""
        @self.app.before_request
        def start_timer():
            g.start = datetime.now()

        @self.app.after_request
        def log_request(response):
            total_time = (datetime.now() - g.start).total_seconds()
            self._log_request(response, total_time)
            return response

    def _register_error_handlers(self):
        """에러 핸들러 등록"""

        @self.app.errorhandler(CustomBaseException)
        def handle_challenge_error(error):
            self._log_error(error)
            response = {
                'error': {
                    'code': error.error_type.value,
                    'message': error.message,
                }
            }
            return response, error.status_code

    def _setup_blueprints(self):
        """Blueprint 등록"""
        self.app.register_blueprint(challenge_bp, url_prefix='/v1/user-challenges')

    def _setup_kafka(self):
        """Kafka 컨슈머 설정"""
        consumer_thread = threading.Thread(
            target=start_kafka_consumer,
            args=(self.app,),
            daemon=True
        )
        consumer_thread.start()
        self.app.consumer_thread = consumer_thread

        @self.app.teardown_appcontext
        def cleanup(exception=None):
            kafka_consumer.stop_consuming()

    def _log_request(self, response, processing_time: float):
        """HTTP 요청 로깅"""
        self.logger.info(
            "HTTP Request",
            extra={
                "tags": {
                    "request_id": request.headers.get('X-Request-ID', 'unknown')
                },
                "attributes": {
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "processing_time_ms": round(processing_time * 1000, 2),
                    "remote_addr": request.remote_addr,
                    "user_agent": request.user_agent.string,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )

    def _log_error(self, error: CustomBaseException):
        """에러 로깅"""
        self.logger.error(
            "Application Error",
            extra={
                "tags": {
                    "error_type": error.error_type.value,
                    "request_id": request.headers.get('X-Request-ID', 'unknown')
                },
                "attributes": {
                    "error_message": error.error_msg,
                    "status_code": error.status_code,
                    "path": request.path,
                    "method": request.method,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )

    def run(self, **kwargs):
        """애플리케이션 실행"""
        self.app.run(**kwargs)

def create_app(config_class: Type[Config] = Config):
    """Factory pattern을 위한 생성 함수"""
    flask_app = FlaskApp(config_class)
    return flask_app.app