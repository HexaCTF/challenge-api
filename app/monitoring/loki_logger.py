import time
import json
import logging
import sys
import traceback

from app.monitoring.async_handler import AsyncHandler
from logging_loki import LokiHandler



class FlaskLokiLogger:
    def __init__(self, app_name,loki_url: str):
        self.app_name = app_name
        self.logger = self._setup_logger(loki_url)
    
    def _setup_logger(self, loki_url: str) -> logging.Logger:
        """Loki 로거 설정"""
        # Define static tags for Loki indexing
        tags = {
            "app": self.app_name,
        }
        
        handler = LokiHandler(
            url=loki_url,
            tags=tags,
            version="1",
        )
        
        
        handler.setFormatter(LokiJsonFormatter())
        async_handler = AsyncHandler(handler)
        logger = logging.getLogger(self.app_name)
        logger.setLevel(logging.INFO)
        logger.addHandler(async_handler)
        return logger
    
    def log_info(self, message: str, labels: dict = None, content: dict = None):
        """
        INFO 레벨 로깅 메서드

        Args:
            message (str): 로깅할 메시지
            labels (dict, optional): 로그 인덱싱을 위한 라벨
            content (dict, optional): 추가 로그 컨텍스트 정보
        """
        try:
            # 기본 labels 설정
            default_labels = {
                "app": self.app_name,
                "level": "INFO"
            }

            # 제공된 labels와 병합
            if labels:
                default_labels.update(labels)

            # 기본 content 설정
            default_content = {
                "message": message
            }

            # 제공된 content와 병합
            if content:
                default_content.update(content)

            self.logger.info(
                message,
                extra={
                    "labels": default_labels,
                    "content": default_content
                }
            )
        except Exception as e:
            print(f"Logging error: {e}", file=sys.stderr)
    

class LokiJsonFormatter(logging.Formatter):
    def format(self, record):
        try:
            # 현재 타임스탬프 (나노초 단위)
            timestamp_ns = str(int(time.time() * 1e9))
            
            # record에서 직접 labels와 content 추출
            labels = getattr(record, 'labels', {})
            content = getattr(record, 'content', {})
            
            # 기본 로그 정보 추가
            base_content = {
                "level": record.levelname,
                "message": record.getMessage(),
                "logger": record.name
            }
            
            # 예외 정보 추가 (있는 경우)
            if record.exc_info:
                base_content["exception"] = {
                    "type": str(record.exc_info[0]),
                    "message": str(record.exc_info[1]),
                    "traceback": traceback.format_exception(*record.exc_info)
                }
            
            # content에 기본 로그 정보 병합
            full_content = {**base_content, **content}
            
            # 로그 구조 생성
            log_entry = {
                "timestamp": timestamp_ns,
                "labels": labels,
                "content": full_content
            }
            
            # JSON으로 변환
            return json.dumps(log_entry, ensure_ascii=False, default=str)
        
        except Exception as e:
            # 포맷팅 중 오류 발생 시 대체 로그
            fallback_entry = {
                "timestamp": str(int(time.time() * 1e9)),
                "labels": {"error": "FORMATTING_FAILURE"},
                "content": {
                    "original_message": record.getMessage(),
                    "formatting_error": str(e),
                    "record_details": str(getattr(record, '__dict__', 'No __dict__'))
                }
            }
            return json.dumps(fallback_entry)