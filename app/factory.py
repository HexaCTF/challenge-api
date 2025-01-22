import json
import sys

from requests import Response
from app.monitoring.ctf_metrics_collector import ChallengeMetricsCollector
from app.monitoring.loki_logger import FlaskLokiLogger
from app.monitoring.system_metrics_collector import SystemMetricsCollector
from flask import Flask, g, request
import threading
from datetime import datetime
from typing import Any, Dict, Type
from prometheus_client import REGISTRY, generate_latest, CONTENT_TYPE_LATEST

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
        self._init_metrics_collector()
   
    def _init_extensions(self):
        """Extensions 초기화"""
        # Kafka 초기화
        kafka_consumer.init_app(self.app)
        kafka_consumer.start_consuming(MessageHandler.handle_message)
        
        # DB 초기화
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()

    def _init_metrics_collector(self):

        # System 메트릭 수집기 초기화
        system_collector = SystemMetricsCollector(self.app)
        system_collector.start_collecting()
        
        
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
                "request_id": context.get("request_id", "unknown"),
                "status_code": str(getattr(response, 'status_code', 'unknown')),
                "method": context.get("method", "UNKNOWN"),
            }
    
            # Prepare log content
            log_content = {
                "processing_time_ms": round(processing_time * 1000, 2),
                "remote_addr": context.get("remote_addr", ""),
                "user_agent": context.get("user_agent", ""),
                "path": context.get("path", ""),
            }

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
            # error_msg가 JSON 형태라면 파싱
            parsed_error_msg = {}
            if error.error_msg:
                try:
                    parsed_error_msg = json.loads(error.error_msg.split("HTTP response body: ", 1)[-1])
                except (json.JSONDecodeError, IndexError):
                    parsed_error_msg = {"raw_error_msg": error.error_msg}

            # 중요한 정보만 추출
            simplified_error_msg = {
                "status": parsed_error_msg.get("status", "Unknown"),
                "message": parsed_error_msg.get("message", "No message provided"),
                "reason": parsed_error_msg.get("reason", "Unknown"),
                "code": parsed_error_msg.get("code", "Unknown"),
                "details": parsed_error_msg.get("details", {}),
            }

            # 로깅
            self.logger.error(
                "Application Error",
                extra={
                    "tags": {
                        "error_type": str(error.error_type.value),
                        "status_code": error.status_code,
                        "request_id": request.headers.get('X-Request-ID', 'unknown') if request else 'unknown'
                    },
                    "content": {
                        "error_type": str(error.error_type.value),
                        "error_message": str(error.message),
                        "error_details": simplified_error_msg,
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