from typing import Any, Optional
from dataclasses import dataclass
from app.utils.exceptions import ApiException
from flask import jsonify
from .error_types import ErrorTypes

@dataclass
class ErrorDetail:
    """에러 상세 정보"""
    type: str
    message: str

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "message": self.message
        }

class ApiResponse:
    """API 응답 처리 클래스"""
    
    @staticmethod
    def success(data: Any = None, status_code: int = 200):
        """성공 응답 반환"""
        response = {"data": data} if data is not None else {}
        return jsonify(response), status_code

    @staticmethod
    def error(error_type: ErrorTypes, message: str, status_code: int):
        """에러 응답 반환"""
        error_detail = ErrorDetail(type=error_type, message=message)
        response = {"error": error_detail.to_dict()}
        return jsonify(response), status_code

    @classmethod
    def from_exception(cls, exception: ApiException):
        """예외로부터 에러 응답 생성"""
        return cls.error(
            error_type=exception.error_type,
            message=exception.message,
            status_code=exception.status_code
        )