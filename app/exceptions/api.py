
from app.exceptions.base import CustomBaseException
from app.exceptions.error_types import ApiErrorTypes


class APIException(CustomBaseException):
    """API 예외 클래스"""
    def __init__(self, error_type: ApiErrorTypes, message: str, status_code: int = 500):
        super().__init__(error_type, message, status_code)

class InvalidRequest(APIException):
    """올바르지 않은 요청 예외"""
    def __init__(self):
        super().__init(
            error_type=ApiErrorTypes.INVALID_REQUEST,
            message="Invalid request format",
            status_code=400
        )

class InternalServerError(APIException):
    """서버 내부 오류 예외"""
    def __init__(self):
        super().__init(
            error_type=ApiErrorTypes.INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
            status_code=500
        )