from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from kubernetes.client.rest import ApiException
import logging

from challenge_api.app.schema import ChallengeRequest
from challenge_api.app.service.userchallenge import UserChallengeService
from challenge_api.app.dependency import get_user_challenge_service
from challenge_api.app.common.exceptions import InvalidInputValue, BaseException
from challenge_api.app.api.errors import BadRequest, BadGateway, InternalServerError, BaseHttpException

router = APIRouter(prefix='/api/v2/userchallenge', tags=['userchallenge'])
logger = logging.getLogger(__name__)

@router.post('/')
async def create_challenge(
    request: ChallengeRequest,
    challenge_service: UserChallengeService = Depends(get_user_challenge_service),
):
    """Create userchallenge"""
    try:
        port = challenge_service.create(request)
        return {'data': {'port': port}}
    except InvalidInputValue as e:
        raise BadRequest(error_msg=e.message)
    except ApiException as e:
        raise BadGateway(error_msg=str(e))
    except (BaseException, SQLAlchemyError, Exception) as e:
        raise InternalServerError(error_msg=str(e))


@router.post('/delete')
async def delete_challenge(
    request: ChallengeRequest,
    challenge_service: UserChallengeService = Depends(get_user_challenge_service),
):
    """사용자 챌린지 삭제"""
    try:
        # TODO: delete 메서드를 UserChallengeService에 추가해야 함
        # challenge_service.delete(request)
        return {'message': 'UserChallenge deleted successfully.'}
    
    except BaseServiceException as e:
        raise BaseHttpException(
            message=str(e),
            status_code=503
        )
    except ApiException as e:
        raise BaseHttpException(
            message="External service error",
            status_code=502,
            error_msg=str(e)
        )
    except Exception as e:
        raise BaseHttpException(
            message="Internal server error",
            status_code=500,
            error_msg=str(e)
        )


@router.post('/status')
async def get_challenge_status(
    request: ChallengeRequest,
    challenge_service: UserChallengeService = Depends(get_user_challenge_service),
):
    """사용자 챌린지 최근 상태 조회"""
    try:
        # TODO: get_status 메서드를 UserChallengeService에 추가해야 함
        # status = challenge_service.get_status(request)
        # return {'data': {'port': status.port, 'status': status.status}}
        return {'data': {'port': 0, 'status': 'None'}}
    
    except BaseServiceException as e:
        raise BaseHttpException(
            message=e.message,
            status_code=503
        )
    except Exception as e:
        raise BaseHttpException(
            message="Internal server error",
            status_code=500,
            error_msg=str(e)
        )