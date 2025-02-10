from enum import Enum

from enum import Enum


class ApiErrorTypes(str, Enum):
    """API 에러 타입을 정의하는 열거형 클래스"""

    # =========================================================================
    # 기본 에러
    # =========================================================================
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"  # 예상치 못한 에러

    # =========================================================================
    # 인증/권한 에러
    # =========================================================================
    # 인증 관련
    SESSION_EXPIRED = "SESSION_EXPIRED"          # 세션 만료
    INVALID_TOKEN = "INVALID_TOKEN"              # 유효하지 않은 토큰
    UNAUTHORIZED = "UNAUTHORIZED"                 # 인증되지 않은 요청
    
    # 권한 관련
    PERMISSION_DENIED = "PERMISSION_DENIED"           # 권한 없음
    INSUFFICIENT_PRIVILEGES = "INSUFFICIENT_PRIVILEGES"  # 불충분한 권한

    # =========================================================================
    # Challenge 관련 에러
    # =========================================================================
    CHALLENGE_NOT_FOUND = "CHALLENGE_NOT_FOUND"           # Challenge를 찾을 수 없음
    CHALLENGE_CONFLICT = "CHALLENGE_CONFLICT"             # Challenge 충돌
    CHALLENGE_CREATION_FAILED = "CHALLENGE_CREATION_FAILED"  # Challenge 생성 실패
    CHALLENGE_DELETION_FAILED = "CHALLENGE_DELETION_FAILED"  # Challenge 삭제 실패

    # =========================================================================
    # 리소스 관련 에러
    # =========================================================================
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"               # 리소스를 찾을 수 없음
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"     # 리소스가 이미 존재함
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"             # 서비스 이용 불가
    PROCESSING_ERROR = "PROCESSING_ERROR"                   # 처리 중 에러 발생
    REQUEST_TIMEOUT = "REQUEST_TIMEOUT"                     # 요청 시간 초과

    # =========================================================================
    # 유효성 검사 에러
    # =========================================================================
    INVALID_REQUEST = "INVALID_REQUEST"      # 잘못된 요청
    INVALID_PARAMETER = "INVALID_PARAMETER"  # 잘못된 파라미터

    # =========================================================================
    # 시스템 에러
    # =========================================================================
    INTERNAL_ERROR = "INTERNAL_ERROR"                 # 내부 서버 에러
    DATABASE_ERROR = "DATABASE_ERROR"                 # 데이터베이스 에러
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR" # 외부 서비스 에러
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"   # 서버 내부 에러
