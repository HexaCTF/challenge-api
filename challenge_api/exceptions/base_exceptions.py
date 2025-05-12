# challenge_api/exceptions/base_exceptions.py

from challenge_api.exceptions.error_types import ApiErrorTypes

class CustomBaseException(Exception):
        def __init__(self, error_type: ApiErrorTypes, message: str, status_code: int = 500, error_msg: str = None):
                super().__init__(message)
                self.error_type = error_type or ApiErrorTypes.UNEXPECTED_ERROR
                self.message = message or "An unexpected error occurred"
                self.status_code = status_code
                self.error_msg = error_msg
        
        def __str__(self):
                return f"[Error] {self.error_type}: {self.error_msg}"

        def to_dict(self):
                return {
                    "error_type": self.error_type,
                    "message": self.message,
                    "status_code": self.status_code,
                }
