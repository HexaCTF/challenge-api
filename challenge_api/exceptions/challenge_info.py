from challenge_api.exceptions.base_exceptions import CustomBaseException
from challenge_api.exceptions.error_types import ApiErrorTypes

class UserChallengeInfoException(CustomBaseException):
    """UserChallenge 관련 기본 예외"""
    def __init__(self, error_type: ApiErrorTypes, message: str, status_code: int = 500, error_msg:str = None):
        super().__init__(error_type, message, status_code, error_msg)

class UserChallengeInfoNotFound(UserChallengeInfoException):
    """Challenge를 찾을 수 없을 때의 예외"""
    def __init__(self, error_msg: str = None):
        super().__init__(
            error_type=ApiErrorTypes.CHALLENGE_INFO_NOT_FOUND,
            message="Challenge Info not found",
            status_code=500,
            error_msg=error_msg
        )

class UserChallengeInfoCreateError(UserChallengeInfoException):
    """Challenge Info 생성 실패"""
    def __init__(self, error_msg: str = None):
        super().__init__(
            error_type=ApiErrorTypes.CHALLENGE_INFO_CREATE_ERROR,
            message="Challenge Info create failed",
            status_code=500,
            error_msg=error_msg
        )

class UserChallengeInfoUpdateError(UserChallengeInfoException):
    """Challenge Info 업데이트 실패"""
    def __init__(self, error_msg: str = None):
        super().__init__(
            error_type=ApiErrorTypes.CHALLENGE_INFO_UPDATE_ERROR,
            message="Challenge Info update failed",
            status_code=500,
            error_msg=error_msg
        )

class UserChallengeInfoGetError(UserChallengeInfoException):
    """Challenge Info 조회 실패"""
    def __init__(self, error_msg: str = None):
        super().__init__(
            error_type=ApiErrorTypes.CHALLENGE_INFO_GET_ERROR,
            message="Challenge Info get failed",
            status_code=500,
            error_msg=error_msg
        )
