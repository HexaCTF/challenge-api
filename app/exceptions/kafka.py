from app.exceptions.base import CustomBaseException
from app.exceptions.error_types import ApiErrorTypes

class QueueException(CustomBaseException):
    """Queue(Kafka) 관련 기본 예외"""
    def __init__(self, error_type: ApiErrorTypes, message: str, status_code: int = 500):
        super().__init__(error_type, message, status_code)
        

class QueueConnectionError(QueueException):
    def __init__(self):
        super().__init__(
            error_type=ApiErrorTypes.SERVICE_UNAVAILABLE,
            message="Service is temporarily unavailable",
            status_code=503
        )

class QueueProcessingError(QueueException):
    def __init__(self):
        super().__init__(
            error_type=ApiErrorTypes.PROCESSING_ERROR,
            message="Failed to process request",
            status_code=422
        )

class QueueTimeoutError(QueueException):
    def __init__(self):
        super().__init__(
            error_type=ApiErrorTypes.REQUEST_TIMEOUT,
            message="Request processing timed out",
            status_code=408
        )

class QueueValidationError(QueueException):
    def __init__(self):
        super().__init__(
            error_type=ApiErrorTypes.INVALID_REQUEST,
            message="Invalid request format",
            status_code=400
        )
