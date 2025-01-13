
from flask import jsonify

from app.exceptions.base import CustomBaseException


def register_error_handler(app):
    """
    ApiException을 처리하는 핸들러를 등록합니다.
    ApiException를 상속받은 예외가 발생하면 아래의 핸들러를 통해 응답을 반환합니다.
    """
    @app.errorhandler(CustomBaseException)
    def handle_challenge_error(error):
        response = {
            'error': {
                'code': error.error_type.value,
                'message': error.message,
            }
        }
        return jsonify(response), error.status_code

        # 예상치 못한 예외 처리
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        response = {
            'status': 'error',
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred'
            }
        }
        return jsonify(response), 500