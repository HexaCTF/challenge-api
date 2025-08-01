from typing import Optional
from datetime import datetime

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.logger import logger

class BaseHttpException(Exception):
    """
    Base HTTP exception class
    
    Args:
        message (str): Exception message
        status_code (int): HTTP status code
        error_msg (str, optional): Additional error error_msg
        
    NOTE:
        - All exceptions should inherit from BaseHttpException
    """
    def __init__(self, message = "An unexpected error occurred", status_code= 500, error_msg: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code 
        self.error_msg = error_msg

# 400 ~ 499 Client Error Exceptions
class BadRequest(BaseHttpException):
    """Bad Request - 400"""
    def __init__(self, message: str ="Bad request", error_msg: Optional[str] = None):
        super().__init__(message, 400, error_msg)

class Unauthorized(BaseHttpException):
    """Unauthorized - 401"""
    def __init__(self, message: str = "Authentication required", error_msg: Optional[str] = None):
        super().__init__(message, 401, error_msg)

class Forbidden(BaseHttpException):
    """Forbidden - 403"""
    def __init__(self, message: str = "Access denied", error_msg: Optional[str] = None):
        super().__init__(message, 403, error_msg)

class NotFound(BaseHttpException):
    """Not Found - 404"""
    def __init__(self, message: str = "Resource not found", error_msg: Optional[str] = None):
        super().__init__(message, 404, error_msg)

class MethodNotAllowed(BaseHttpException):
    """Method Not Allowed - 405"""
    def __init__(self, message: str = "Method not allowed", error_msg: Optional[str] = None):
        super().__init__(message, 405, error_msg)

class Conflict(BaseHttpException):
    """Conflict - 409"""
    def __init__(self, message: str = "Resource conflict", error_msg: Optional[str] = None):
        super().__init__(message, 409, error_msg)

class UnprocessableEntity(BaseHttpException):
    """Unprocessable Entity - 422"""
    def __init__(self, message: str = "Validation failed", error_msg: Optional[str] = None):
        super().__init__(message, 422, error_msg)

class TooManyRequests(BaseHttpException):
    """Too Many Requests - 429"""
    def __init__(self, message: str = "Rate limit exceeded", error_msg: Optional[str] = None):
        super().__init__(message, 429, error_msg)

# 500 ~ 599 Server Error Exceptions
class InternalServerError(BaseHttpException):
    """Internal Server Error - 500"""
    def __init__(self, message: str = "Internal server error", error_msg: Optional[str] = None):
        super().__init__(message, 500, error_msg)

class BadGateway(BaseHttpException):
    """Bad Gateway - 502"""
    def __init__(self, message: str = "Bad gateway", error_msg: Optional[str] = None):
        super().__init__(message, 502, error_msg)

class ServiceUnavailable(BaseHttpException):
    """Service Unavailable - 503"""
    def __init__(self, message: str = "Service temporarily unavailable", error_msg: Optional[str] = None):
        super().__init__(message, 503, error_msg)

class GatewayTimeout(BaseHttpException):
    """Gateway Timeout - 504"""
    def __init__(self, message: str = "Gateway timeout", error_msg: Optional[str] = None):
        super().__init__(message, 504, error_msg)

def create_error_response(
    message: str,
    status_code: int,
) -> JSONResponse:
    """
    Create standardized error response
    
    Args:
        message (str): Error message to display to client
        status_code (int): HTTP status code
        
    Returns:
        JSONResponse: JSON response with error message and status code
    """
    response = {
        'error': {
            'message': message,
        },
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        status_code=status_code,
        content=response
    )
