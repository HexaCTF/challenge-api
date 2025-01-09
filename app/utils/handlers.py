from app.utils.error_types import ApiErrorTypes
from app.utils.exceptions import ApiException
from app.utils.response import ApiResponse


def register_error_handlers(app):
    @app.errorhandler(ApiException)
    def handle_api_exception(e):
        return ApiResponse.from_exception(e)

    @app.errorhandler(404)
    def handle_404(e):
        return ApiResponse.error(
            error_type=ApiErrorTypes.RESOURCE_NOT_FOUND,
            message="요청한 리소스를 찾을 수 없습니다.",
            status_code=404
        )

    @app.errorhandler(500)
    def handle_500(e):
        return ApiResponse.error(
            error_type=ApiErrorTypes.INTERNAL_ERROR,
            message="서버 내부 오류가 발생했습니다.",
            status_code=500
        )