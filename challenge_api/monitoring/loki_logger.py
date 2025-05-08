# import time
# import json
# import logging
# import traceback

# from monitoring.async_handler import AsyncHandler
# from logging_loki import LokiHandler

# class FlaskLokiLogger:
#     def __init__(self, app_name,loki_url: str):
#         self.app_name = app_name
#         self.logger = self._setup_logger(loki_url)
    
#     def _setup_logger(self, loki_url: str) -> logging.Logger:
#         """Loki 로거 설정"""
#         tags = {
#             "app": self.app_name
#         }
        
#         handler = LokiHandler(
#             url=loki_url,
#             tags=tags,
#             version="1",
#         )
        
#         handler.setFormatter(LokiJsonFormatter())
#         async_handler = AsyncHandler(handler)
#         logger = logging.getLogger(self.app_name)
#         logger.setLevel(logging.DEBUG)
#         logger.addHandler(async_handler)
#         return logger
    
    

# class LokiJsonFormatter(logging.Formatter):
#     def format(self, record):
#         try:
#             # 현재 타임스탬프 (나노초 단위)
#             timestamp_ns = str(int(time.time() * 1e9))
            
#             # record에서 직접 labels와 content 추출
#             # tags = getattr(record, 'tags', {})
#             content = getattr(record, 'content', {})
            
#             # 기본 로그 정보 추가
#             base_content = {
#                 "message": record.getMessage(),
#                 "level": record.levelname,
#             }
            
#             # 예외 정보 추가 (있는 경우)
#             if record.exc_info:
#                 base_content["exception"] = {
#                     "type": str(record.exc_info[0]),
#                     "message": str(record.exc_info[1]),
#                     "traceback": traceback.format_exception(*record.exc_info)
#                 }
                
            
#             # content에 기본 로그 정보 병합
#             full_content = {**base_content, **content}
            
#             # 로그 구조 생성
#             log_entry = {
#                 "timestamp": timestamp_ns,
#                 "content": full_content
#             }
            
#             # JSON으로 변환
#             return json.dumps(log_entry, ensure_ascii=False, default=str)
        
#         except Exception as e:
#             # 포맷팅 중 오류 발생 시 대체 로그
#             fallback_entry = {
#                 "timestamp": str(int(time.time() * 1e9)),
#                 "labels": {"error": "FORMATTING_FAILURE"},
#                 "content": {
#                     "original_message": record.getMessage(),
#                     "formatting_error": str(e),
#                     "record_details": str(getattr(record, '__dict__', 'No __dict__'))
#                 }
#             }
#             return json.dumps(fallback_entry)
    
#     def _serialize_dict(self, data, max_depth=3, current_depth=0):
#         """재귀적으로 dict을 직렬화"""
#         if current_depth >= max_depth:
#             return "<Max depth reached>"
#         if isinstance(data, dict):
#             return {
#                 key: self._serialize_dict(value, max_depth, current_depth + 1)
#                 for key, value in data.items()
#             }
#         elif isinstance(data, (list, tuple, set)):
#             return [
#                 self._serialize_dict(item, max_depth, current_depth + 1)
#                 for item in data
#             ]
#         elif hasattr(data, "__dict__"):
#             return self._serialize_dict(data.__dict__, max_depth, current_depth + 1)
#         else:
#             return data