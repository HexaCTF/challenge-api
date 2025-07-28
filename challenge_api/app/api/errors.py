from typing import Tuple, Optional
from datetime import datetime

from flask import jsonify, Response, current_app, request

from . import v1

class BaseHttpException(Exception):
    """
    Base HTTP exception class
    
    Args:
        message (str): Exception message
        status_code (int): HTTP status code
        details (str, optional): Additional error details
        
    NOTE:
        - All exceptions should inherit from BaseHttpException
    """
    def __init__(self, message = "An unexpected error occurred", status_code= 500, details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code 
        self.details = details

# 400 ~ 499 Client Error Exceptions
class BadRequest(BaseHttpException):
    """Bad Request - 400"""
    def __init__(self, message: str ="Bad request", details: Optional[str] = None):
        super().__init__(message, 400, details)

class Unauthorized(BaseHttpException):
    """Unauthorized - 401"""
    def __init__(self, message: str = "Authentication required", details: Optional[str] = None):
        super().__init__(message, 401, details)

class Forbidden(BaseHttpException):
    """Forbidden - 403"""
    def __init__(self, message: str = "Access denied", details: Optional[str] = None):
        super().__init__(message, 403, details)

class NotFound(BaseHttpException):
    """Not Found - 404"""
    def __init__(self, message: str = "Resource not found", details: Optional[str] = None):
        super().__init__(message, 404, details)

class MethodNotAllowed(BaseHttpException):
    """Method Not Allowed - 405"""
    def __init__(self, message: str = "Method not allowed", details: Optional[str] = None):
        super().__init__(message, 405, details)

class Conflict(BaseHttpException):
    """Conflict - 409"""
    def __init__(self, message: str = "Resource conflict", details: Optional[str] = None):
        super().__init__(message, 409, details)

class UnprocessableEntity(BaseHttpException):
    """Unprocessable Entity - 422"""
    def __init__(self, message: str = "Validation failed", details: Optional[str] = None):
        super().__init__(message, 422, details)

class TooManyRequests(BaseHttpException):
    """Too Many Requests - 429"""
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[str] = None):
        super().__init__(message, 429, details)

# 500 ~ 599 Server Error Exceptions
class InternalServerError(BaseHttpException):
    """Internal Server Error - 500"""
    def __init__(self, message: str = "Internal server error", details: Optional[str] = None):
        super().__init__(message, 500, details)

class NotImplemented(BaseHttpException):
    """Not Implemented - 501"""
    def __init__(self, message: str = "Feature not implemented", details: Optional[str] = None):
        super().__init__(message, 501, details)

class BadGateway(BaseHttpException):
    """Bad Gateway - 502"""
    def __init__(self, message: str = "Bad gateway", details: Optional[str] = None):
        super().__init__(message, 502, details)

class ServiceUnavailable(BaseHttpException):
    """Service Unavailable - 503"""
    def __init__(self, message: str = "Service temporarily unavailable", details: Optional[str] = None):
        super().__init__(message, 503, details)

class GatewayTimeout(BaseHttpException):
    """Gateway Timeout - 504"""
    def __init__(self, message: str = "Gateway timeout", details: Optional[str] = None):
        super().__init__(message, 504, details)

def create_error_response(
    message: str,
    status_code: int,
) -> Tuple[Response, int]:
    """
    Create standardized error response
    
    Args:
        message (str): Error message to display to client
        status_code (int): HTTP status code
        
    Returns:
        Tuple[Response, int]: JSON response with error message and status code
    """
    response = {
        'error': {
            'message': message,
        },
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return jsonify(response), status_code

@v1.errorhandler(BaseHttpException)
def handle_http_exception(error: BaseHttpException) -> Tuple[Response, int]:
    """
    Global error handler for all BaseHttpException instances
    
    Args:
        error (BaseHttpException): The caught exception instance
        
    Returns:
        Tuple[Response, int]: Standardized error response
    """
    
    # Create log message with context information
    log_data = {
        'error_type': type(error).__name__,
        'status_code': error.status_code,
        'endpoint': request.endpoint,
        'method': request.method,
        'url': request.url,
        'remote_addr': request.remote_addr,
    }
    
    if error.details:
        log_data['details'] = error.details
    
    current_app.logger.error(
        f"Error: {error.message}",
        extra=log_data
    )
    
    return create_error_response(
        message=error.message,
        status_code=error.status_code,
    )