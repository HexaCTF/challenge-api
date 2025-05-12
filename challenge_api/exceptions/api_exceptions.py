from challenge_api.exceptions.base_exceptions import CustomBaseException
from challenge_api.exceptions.error_types import ApiErrorTypes


class APIException(CustomBaseException):
    """API 예외 클래스"""
    def __init__(self, error_type: ApiErrorTypes, message: str, status_code: int = 500, error_msg: str = None):
        super().__init__(error_type, message, status_code, error_msg)

class InvalidRequest(APIException):
    """올바르지 않은 요청 예외"""
    def __init__(self, error_msg: str = None):
        super().__init__(
            error_type=ApiErrorTypes.INVALID_REQUEST,
            message="Invalid request format",
            status_code=400,
            error_msg=error_msg
        )

class InternalServerError(APIException):
    """서버 내부 오류 예외"""
    def __init__(self, error_msg: str = None):
        super().__init__(
            error_type=ApiErrorTypes.INTERNAL_SERVER_ERROR,
            message="Internal server error",
            status_code=500,
            error_msg=error_msg
        )

class ChallengeNotFound(APIException):
    def __init__(self, error_msg: str = None):
        super().__init__(
            error_type=ApiErrorTypes.NOT_FOUND,
            message="Challenge not found",
            status_code=404,
            error_msg=error_msg
        )