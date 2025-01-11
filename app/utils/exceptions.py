# app/utils/exceptions.py
from app.utils.error_types import ApiErrorTypes


class ApiException(Exception):
    """기본 API 예외 클래스"""
    def __init__(self, error_type: ApiErrorTypes, message: str, status_code: int = 500):
        self.error_type = error_type
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class UnauthorizedException(ApiException):
    """인증 관련 예외"""
    def __init__(self, message: str, error_type: ApiErrorTypes = ApiErrorTypes.UNAUTHORIZED):
        super().__init__(error_type=error_type, message=message, status_code=401)

class NotFoundException(ApiException):
    """리소스를 찾을 수 없을 때의 예외"""
    def __init__(self, message: str):
        super().__init__(error_type=ApiErrorTypes.RESOURCE_NOT_FOUND, message=message, status_code=404)