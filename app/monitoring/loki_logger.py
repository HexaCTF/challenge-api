import datetime
import json
import logging
from typing import Any, Dict
from urllib import request

from logging_loki import LokiHandler

from app.exceptions.base import CustomBaseException


class FlaskLokiLogger:    
    def __init__(self, app_name: str, loki_url: str):
        self.app_name = app_name
        self.logger = self._setup_logger(loki_url)

    def _setup_logger(self) -> logging.Logger:
        """Loki 로거 설정"""
        handler = LokiHandler(
            url=self.app.config['LOKI_URL'],
            tags=self.app.config['LOG_TAGS'],
            version="1",
            json_fields= True
        )
        
        logger = logging.getLogger(self.app.config['APP_NAME'])
        logger.setLevel(self.app.config['LOG_LEVEL'])
        logger.addHandler(handler)
        return logger
    
    def _get_request_context(self) -> Dict[str, Any]:
        """현재 요청의 컨텍스트 정보 수집"""
        return {
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote_addr,
            "user_agent": request.user_agent.string,
            "request_id": request.headers.get('X-Request-ID', 'unknown'),
            "timestamp": datetime.utcnow().isoformat()
        }

    def log_request(self, response: Any, processing_time: float):
        """HTTP 요청 로깅"""
        context = self._get_request_context()
        context.update({
            "status_code": response.status_code,
            "processing_time_ms": round(processing_time * 1000, 2)
        })

        if request.is_json:
            context["request_body"] = request.get_json()

        self.logger.info(
            "HTTP Request",
            extra={
                "tags": {"request_id": context["request_id"]},
                "attributes": context
            }
        )

    def log_error(self, error: CustomBaseException):
        """커스텀 예외 로깅"""
        context = self._get_request_context()
        context.update({
            "error_type": error.error_type.value,
            "error_message": error.message,
            "status_code": error.status_code,
            "error_msg": error.error_msg
        })

        self.logger.error(
            "Application Error",
            extra={
                "tags": {
                    "error_type": error.error_type.value,
                    "request_id": context["request_id"]
                },
                "attributes": context
            }
        )
