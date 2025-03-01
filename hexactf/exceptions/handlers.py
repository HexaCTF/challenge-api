from flask import jsonify

from hexactf.exceptions.base_exceptions import CustomBaseException

def register_error_handler(app):
    """CustomBaseException을 처리하는 에러 핸들러"""
    @app.errorhandler(CustomBaseException)
    def handle_challenge_error(error):
        response = {
            'error': {
                'code': error.error_type.value,
                'message': error.message,
            }
        }
        return jsonify(response), error.status_code
