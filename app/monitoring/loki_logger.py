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
            version="1"
        )
        
        handler.setFormatter(JSONFormatter())
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

        # 평평한(flat) 구조로 변경
        self.logger.info(
            "HTTP Request",
            extra={
                **context,  # context의 모든 필드를 최상위 레벨로
                "request_id": context["request_id"]
            }
        )

    def log_error(self, error: CustomBaseException):
        """커스텀 예외 로깅"""
        context = self._get_request_context()

        # 모든 필드를 최상위 레벨로 올림
        log_data = {
            "error_type": error.error_type.value,
            "error_message": error.message,
            "status_code": error.status_code,
            "error_msg": error.error_msg,
            "request_id": context["request_id"],
            "path": context["path"],
            "method": context["method"],
            "timestamp": context["timestamp"]
        }

        self.logger.error(
            "Application Error",
            extra=log_data  # 중첩 구조 제거
        )

class JSONFormatter(logging.Formatter):
    def format(self, record):
        # 기본 로그 데이터를 flatten하게 구성
        if hasattr(record, 'extra'):
            # extra의 데이터를 최상위 레벨로 복사
            extra = record.extra
            if 'attributes' in extra:
                # attributes의 모든 필드를 최상위로
                record.extra.update(extra['attributes'])
                del record.extra['attributes']
            if 'tags' in extra:
                # tags의 모든 필드를 tag_ 접두사를 붙여서 최상위로
                for key, value in extra['tags'].items():
                    record.extra[f'tag_{key}'] = value
                del record.extra['tags']

        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.msg,
            "logger": record.name
        }

        # extra 데이터 추가
        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        # JSON으로 직렬화할 때 오류 방지
        return json.dumps(log_data, default=str)