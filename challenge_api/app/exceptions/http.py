class BaseHttpException(Exception):
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
     def __init__(self, message:str, status_code:int):
        super().__init__(message)
        self.message = message or "An unexpected error occurred"
        self.status_code = status_code

"""
400 ~ 499  
"""
class BadRequest(BaseHttpException):
    """Bad Request"""
    def __init__(self, message:str):
        super().__init__("Bad Request", 400)

class NotFound(BaseHttpException):
    """Not Found"""
    def __init__(self, message:str):
        super().__init__("Not Found", 404)

"""
500 ~ 599
"""
class InternalServerError(BaseHttpException):
    """Internal Server Error"""
    def __init__(self, message:str):
        super().__init__("Internal Server Error", 500)
            
        
