from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from kubernetes.client.rest import ApiException
from datetime import datetime
import logging

from challenge_api.app.schema import ChallengeRequest
from challenge_api.app.service.userchallenge import UserChallengeService
from challenge_api.app.dependencies import get_user_challenge_service
from challenge_api.exceptions.service import InvalidInputValue, BaseServiceException
from challenge_api.api.errors import BaseHttpException

router = APIRouter(prefix='/api/v2/userchallenge', tags=['userchallenge'])
logger = logging.getLogger(__name__)


@router.post('/')
async def create_challenge(
    request: ChallengeRequest,
    challenge_service: UserChallengeService = Depends(get_user_challenge_service),
):
    """사용자 챌린지 생성"""
    try:
        port = challenge_service.create(request)
        return {'data': {'port': port}}
    
    except InvalidInputValue as e:
        raise BaseHttpException(
            message=e.message,
            status_code=400
        )
    except BaseServiceException as e:
        raise BaseHttpException(
            message=e.message,
            status_code=503
        )
    except SQLAlchemyError as e:
        raise BaseHttpException(
            message="Database error occurred",
            status_code=500,
            details=str(e)
        )
    except ApiException as e:
        raise BaseHttpException(
            message="External service error",
            status_code=502,
            details=str(e)
        )
    except Exception as e:
        raise BaseHttpException(
            message="Internal server error",
            status_code=500,
            details=str(e)
        )


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
            message=e.message,
            status_code=503
        )
    except ApiException as e:
        raise BaseHttpException(
            message="External service error",
            status_code=502,
            details=str(e)
        )
    except Exception as e:
        raise BaseHttpException(
            message="Internal server error",
            status_code=500,
            details=str(e)
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
            details=str(e)
        )