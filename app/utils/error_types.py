from enum import Enum


class ApiErrorTypes(str, Enum):
    """API 에러 타입 정의"""
    
    # 인증 관련 에러
    SESSION_EXPIRED = "SESSION_EXPIRED"
    INVALID_TOKEN = "INVALID_TOKEN"
    UNAUTHORIZED = "UNAUTHORIZED"
    
    # 권한 관련 에러
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INSUFFICIENT_PRIVILEGES = "INSUFFICIENT_PRIVILEGES"
    
    # 리소스 관련 에러
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    
    # 유효성 검사 에러
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    
    # 서버 에러
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
