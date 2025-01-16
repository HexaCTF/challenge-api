import sys
from app.monitoring.loki_logger import FlaskLokiLogger
from flask import Flask, g, request
import threading
from datetime import datetime
from typing import Any, Dict, Type

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
        self.logger = FlaskLokiLogger(app_name="challenge-api", loki_url=self.app.config['LOKI_URL']).logger

        # 초기 설정
        self._init_extensions()
        self._setup_middleware()
        self._register_error_handlers()
        self._setup_blueprints()
        self._setup_kafka()

    # def _setup_logger(self) -> logging.Logger:
    #     """Loki 로거 설정"""
    #     # 기본 로거 생성
    #     loki_logger = FlaskLokiLogger(app_name=self.app.name, loki_url=self.app.config['LOKI_URL'])

    #     return loki_logger.logger
    
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
            print(f"[DEBUG] error: {error.__dict__}", file=sys.stderr)
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
    
    def _get_request_context(self) -> Dict[str, Any]:
       """현재 요청의 컨텍스트 정보 수집"""
       try:
           return {
               "method": request.method,
               "path": request.path,
               "remote_addr": request.remote_addr,
               "user_agent": request.user_agent.string,
               "request_id": request.headers.get('X-Request-ID', 'unknown'),
               "timestamp": datetime.utcnow().isoformat()
           }
       except Exception as e:
           # 요청 컨텍스트 추출 실패 시 기본값
           return {
               "method": "UNKNOWN",
               "path": "/",
               "remote_addr": "",
               "user_agent": "",
               "request_id": "unknown",
               "context_error": str(e)
            }
           
    def _log_request(self, response, processing_time: float):
        """HTTP 요청 로깅"""
        try:
            context = self._get_request_context()

            # Prepare labels (these will be indexed by Loki)
            labels = {
                "request_id": context.get("request_id", "unknown"),
                "status_code": str(getattr(response, 'status_code', 'unknown')),
                "method": context.get("method", "UNKNOWN"),
                "path": context.get("path", "/")
            }
    
            # Prepare log content
            log_content = {
                "processing_time_ms": round(processing_time * 1000, 2),
                "remote_addr": context.get("remote_addr", ""),
                "user_agent": context.get("user_agent", ""),
                "method": context.get("method", ""),
                "path": context.get("path", ""),
                "status_code": str(getattr(response, 'status_code', 'unknown')),
                "timestamp": context.get("timestamp", datetime.utcnow().isoformat())
            }
    
            # 추가 정보 안전하게 포함
            try:
                if request.is_json:
                    log_content["request_body"] = request.get_json()
            except Exception as e:
                log_content["request_body_error"] = str(e)
    
            self.logger.info(
                "HTTP Request",
                extra={
                    "labels": labels,
                    "content": log_content
                }
            )
        except Exception as e:
            # 로깅 중 오류 발생 시 기본 로깅
            self.logger.error(f"Logging error: {str(e)}")
        

    def _log_error(self, error: CustomBaseException):
        """에러 로깅"""
        try:
            # 요청 컨텍스트 안전하게 추출
            context = {
                "method": getattr(request, 'method', 'UNKNOWN'),
                "path": getattr(request, 'path', '/'),
                "remote_addr": getattr(request, 'remote_addr', ''),
                "user_agent": str(getattr(request, 'user_agent', '')),
                "request_id": request.headers.get('X-Request-ID', 'unknown') if request else 'unknown'
            }

            # 로깅
            self.logger.error(
                "Application Error",
                extra={
                    "labels": {
                        "error_type": str(error.error_type.value),
                        "request_id": context.get('request_id', 'unknown')
                    },
                    "content": {
                        **context,
                        "error_type": str(error.error_type.value),
                        "error_message": str(error.message),
                        "error_msg": str(error.error_msg or ''),
                        "status_code": error.status_code,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )

        except Exception as log_error:
            # 로깅 중 오류 발생 시 기본 로깅
            print(f"[DEBUG] Logging error: {log_error}", file=sys.stderr)
            self.logger.error(f"Error logging failed: {str(log_error)}")

    def run(self, **kwargs):
        """애플리케이션 실행"""
        self.app.run(**kwargs)

def create_app(config_class: Type[Config] = Config):
    """Factory pattern을 위한 생성 함수"""
    flask_app = FlaskApp(config_class)
    return flask_app.app