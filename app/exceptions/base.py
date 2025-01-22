# app/utils/exceptions.py

from app.exceptions.error_types import ApiErrorTypes

class CustomBaseException(Exception):
     """
     기본 예외 클래스
        Args:
                error_type (ApiErrorTypes): 예외 타입
                message (str): 예외 메시지
                status_code (int): HTTP Status Code
        NOTE:
                - 모든 예외는 CustomBaseException을 상속받아야 합니다.
                - 예외 발생시 handler(handler.py)에서 에러를 반환(response)하도록 구현되어 있습니다.
     """
     def __init__(self, error_type: ApiErrorTypes, message: str, status_code: int = 500, error_msg: str = None):
        super().__init__(message)
        self.error_type = error_type or ApiErrorTypes.UNEXPECTED_ERROR
        self.message = message or "An unexpected error occurred"
        self.status_code = status_code
        self.error_msg = error_msg
        
           
        
