from app.exceptions.base import CustomBaseException
from app.exceptions.error_types import ApiErrorTypes


class ChallengeException(CustomBaseException):
    """UserChallenge 관련 기본 예외"""
    def __init__(self, error_type: ApiErrorTypes, message: str, status_code: int = 500, error_msg:str = None):
        super().__init__(error_type, message, status_code, error_msg)

class ChallengeNotFound(ChallengeException):
    """Challenge를 찾을 수 없을 때의 예외"""
    def __init__(self, error_msg: str = None):
        super().__init__(
            error_type=ApiErrorTypes.CHALLENGE_NOT_FOUND,
            message="Challenge not found",
            status_code=404,
            error_msg=error_msg
        )