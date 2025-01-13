# app/utils/exceptions.py

from app.exceptions.error_types import ApiErrorTypes


class CustomBaseException(Exception):
     """기본 예외 클래스"""
     def __init__(self, error_type: ApiErrorTypes, message: str, status_code: int = 500):
        self.error_type = error_type or ApiErrorTypes.UNEXPECTED_ERROR
        self.message = message or "An unexpected error occurred"
        self.status_code = status_code
        super().__init__(message)
