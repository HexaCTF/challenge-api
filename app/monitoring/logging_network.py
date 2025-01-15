from flask import app, request, g
import traceback
import time
from datetime import datetime
from typing import Dict, Any

from app.monitoring.logging_setup import network_logger, error_logger

class RequestFormatter:
    """요청 정보를 포맷팅하는 유틸리티 클래스"""
    @staticmethod
    def format_request() -> Dict[Any, Any]:
        return {
            "method": request.method,
            "path": request.path,
            "ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "request_id": request.headers.get("X-Request-ID", ""),
            "timestamp": datetime.utcnow().isoformat(),
            "headers": dict(request.headers),
            "query_params": dict(request.args),
            "content_type": request.content_type,
            "content_length": request.content_length or 0
        }

# 네트워크 로깅 미들웨어
@app.before_request
def log_request():
    """요청 시작 시 로깅"""
    g.start_time = time.time()
    request_info = RequestFormatter.format_request()
    
    network_logger.info(
        "Incoming request",
        extra={
            "tags": {
                "log_type": "request",
                **request_info
            }
        }
    )

@app.after_request
def log_response(response):
    """응답 시 로깅"""
    request_time = time.time() - g.start_time
    request_info = RequestFormatter.format_request()
    
    response_info = {
        "status_code": response.status_code,
        "response_time": round(request_time, 3),
        "response_size": response.content_length,
        "response_headers": dict(response.headers)
    }
    
    network_logger.info(
        "Response sent",
        extra={
            "tags": {
                "log_type": "response",
                **request_info,
                **response_info
            }
        }
    )
    return response
