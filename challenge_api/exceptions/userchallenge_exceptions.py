
from exceptions.base_exceptions import CustomBaseException
from exceptions.error_types import ApiErrorTypes

class UserChallengeException(CustomBaseException):
    """UserChallenge 관련 기본 예외"""
    def __init__(self, error_type: ApiErrorTypes, message: str, status_code: int = 500, error_msg: str = None):
        super().__init__(error_type, message, status_code, error_msg)

class UserChallengeConflictError(UserChallengeException):
    """UserChallenge 중복 생성 시도시 발생하는 예외"""
    def __init__(self, error_msg: str = None):
        super().__init__(
            error_type=ApiErrorTypes.CHALLENGE_CONFLICT,
            message="Challenge already exists",
            status_code=409,
            error_msg=error_msg
        )

class UserChallengeCreationError(UserChallengeException):
    """UserChallenge 생성 실패시 발생하는 예외"""
    def __init__(self, error_msg: str = None):
        super().__init__(
            error_type=ApiErrorTypes.CHALLENGE_CREATION_FAILED,
            message="Unable to create challenge. Please try again later",
            status_code=500,
            error_msg=error_msg
        )

class UserChallengeDeletionError(UserChallengeException):
    """UserChallenge 삭제 실패시 발생하는 예외"""
    def __init__(self, error_msg: str = None):
        super().__init__(
            error_type=ApiErrorTypes.CHALLENGE_DELETION_FAILED,
            message="Unable to delete challenge. Please try again later",
            status_code=500,
            error_msg=error_msg
        )

class UserChallengeNotFoundError(UserChallengeException):
    """UserChallenge 조회 실패시 발생하는 예외"""
    def __init__(self, error_msg: str = None):
        super().__init__(
            error_type=ApiErrorTypes.CHALLENGE_NOT_FOUND,
            message="UserChallenge not found",
            status_code=404,
            error_msg=error_msg
       )
