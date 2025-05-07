import os
import sys

# from hexactf.monitoring.system_metrics_collector import SystemMetricsCollector
from flask import Flask, g, request
from datetime import datetime
from typing import Any, Dict, Type

from api.challenge_api import challenge_bp
from config import Config
from exceptions.base_exceptions import CustomBaseException
from extensions.kafka.handler import MessageHandler
from extensions_manager import kafka_consumer, db
from monitoring.loki_logger import FlaskLokiLogger

def start_kafka_consumer(app):
    """Start Kafka consumer in a separate thread"""
    with app.app_context():
        kafka_consumer.start_consuming(MessageHandler.handle_message)

class FlaskApp:
    def __init__(self, config_class: Type[Config] = Config):
        self.app = Flask(__name__)
        self.app.config.from_object(config_class)
               
        # self.logger = FlaskLokiLogger(app_name="challenge-api", loki_url=self.app.config['LOKI_URL']).logger

        # if os.getenv("TEST_MODE") != "true":
        #     from hexactf.monitoring.loki_logger import FlaskLokiLogger
        #     self.logger = FlaskLokiLogger(app_name="challenge-api", loki_url=self.app.config['LOKI_URL']).logger
        # else:
        #     self.logger = self.app.logger  # Use Flask default logger
        
        # 초기 설정
        self._init_extensions()
        # self._setup_middleware()
        self._register_error_handlers()
        self._setup_blueprints()
        # self._init_metrics_collector()
    
    def _init_extensions(self):
        """Extensions 초기화"""
        # Kafka 초기화
        kafka_consumer.init_app(self.app)
        kafka_consumer.start_consuming(MessageHandler.handle_message)
        
        # DB 초기화
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()

    # @NOTE : 추후 제거 예정 
    # def _init_metrics_collector(self):

    #     # System 메트릭 수집기 초기화
    #     system_collector = SystemMetricsCollector(self.app)
    #     system_collector.start_collecting()
        
        
    def _setup_middleware(self):
        """미들웨어 설정"""
        @self.app.before_request
        def start_timer():
            g.start = datetime.now()

        @self.app.after_request
        def log_request(response):
            total_time = (datetime.now() - g.start).total_seconds()
            # self._log_request(response, total_time)
            return response

    def _register_error_handlers(self):
        """에러 핸들러 등록"""

        @self.app.errorhandler(CustomBaseException)
        def handle_challenge_error(error):
            print(f"[DEBUG] error: {error.__dict__}", file=sys.stderr)
            # self._log_error(error)
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
    
    def _get_request_context(self) -> Dict[str, Any]:
       """현재 요청의 컨텍스트 정보 수집"""
       try:
           return {
               "method": request.method,
               "path": request.path,
               "remote_addr": request.remote_addr,
               "user_agent": request.user_agent.string,
               "request_id": request.headers.get('X-Request-ID', 'unknown'),
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
            tags = {
                "request_id": str(context.get("request_id", "unknown")),
                "status_code": str(response.status_code),
                "method": str(context.get("method", "UNKNOWN")),
            }
    
            # Prepare log content
            log_content = {
                "remote_addr": context.get("remote_addr", ""),
                "user_agent": context.get("user_agent", ""),
                "path": context.get("path", ""),
            }
    
            if response.status_code >= 500:
                self.logger.error(
                    "HTTP Request",
                    extra={
                        "tags": tags,
                        "content": log_content
                    }
                )
            elif response.status_code >= 400:
                self.logger.warning(
                    "HTTP Request",
                    extra={
                        "tags": tags,
                        "content": log_content
                    }
                )
            else:    
                self.logger.info(
                    "HTTP Request",
                    extra={
                        "tags": tags,
                        "content": log_content
                    }
                )
        except Exception as e:
            # 로깅 중 오류 발생 시 기본 로깅
            self.logger.error(f"Logging error: {str(e)}")
        

    def _log_error(self, error: CustomBaseException):
        """에러 로깅"""
        try:
            # 로깅
            self.logger.error(
                "Application Error",
                extra={
                    "tags": {
                        "error_type": str(error.error_type.value),
                        "request_id": request.headers.get('X-Request-ID', 'unknown') if request else 'unknown'
                    },
                    "content": {
                        "error_type": str(error.error_type.value),
                        "error_message": str(error.message),
                        "error_msg": str(error.error_msg or ''),
                        "status_code": error.status_code,
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