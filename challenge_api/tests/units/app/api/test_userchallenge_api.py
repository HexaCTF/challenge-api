import pytest
from unittest.mock import MagicMock
from fastapi import FastAPI  
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from kubernetes.client.rest import ApiException

from challenge_api.app.schema import ChallengeRequest
from challenge_api.app.common.exceptions import (
    InvalidInputValue, 
    UserChallengeCreationException, 
    UserChallengeDeletionException,
    BaseException
)
from challenge_api.app.api.errors import BadRequest, BadGateway, InternalServerError, BaseHttpException
from challenge_api.app.api.userchallenge import router
from challenge_api.app.dependency import get_user_challenge_service


@pytest.fixture
def mock_user_challenge_service():
    return MagicMock()

@pytest.fixture
def test_app(mock_user_challenge_service):
    app = FastAPI()
    
    # BaseHttpException 예외 핸들러 추가(기존의 핸들러와 동일)
    # 테스트 환경에서는 고정된 타임스탬프를 사용
    @app.exception_handler(BaseHttpException)
    async def handle_http_exception(request, error: BaseHttpException):
        response_data = {
            'error': {
                'message': error.message,
            },
            'timestamp': '2024-01-01T00:00:00' 
        }
        
        if error.error_msg:
            response_data['error']['error_msg'] = error.error_msg
        
        return JSONResponse(
            status_code=error.status_code,
            content=response_data
        )
    
    # 실제 라우터를 포함
    app.include_router(router)
    
    # Dependency override 설정
    # api 계층에서는 실제 서비스 대신 모의 서비스로 의존성을 주입
    # 의존성 주입 시 함수 형태로 주입해야 함(lambda)
    app.dependency_overrides[get_user_challenge_service] = lambda: mock_user_challenge_service
    
    return app


@pytest.fixture
def client(test_app):
    """Create a test client for the FastAPI app"""
    return TestClient(test_app)


@pytest.fixture
def valid_challenge_request():
    """Valid challenge request data"""
    return {
        "challenge_id": 1,
        "user_id": 101
    }


@pytest.fixture
def challenge_request_object():
    """ChallengeRequest object for testing"""
    return ChallengeRequest(challenge_id=1, user_id=101)



def test_create_challenge_success(client, mock_user_challenge_service, valid_challenge_request):
    """챌린지 생성 요청 성공 시 200 응답 및 챌린지 정보 반환"""
    
    # Arrange
    expected_port = 8080
    mock_user_challenge_service.create.return_value = expected_port
    
    # Act
    response = client.post('/api/v2/userchallenge/', json=valid_challenge_request)

    
    # Assert
    assert response.status_code == 200
    assert response.json() == {'data': {'port': expected_port}}
    mock_user_challenge_service.create.assert_called_once()
    
    # 서비스가 올바르게 호출되었는지 확인 
    call_args = mock_user_challenge_service.create.call_args[0][0]
    assert isinstance(call_args, ChallengeRequest)
    assert call_args.challenge_id == valid_challenge_request['challenge_id']
    assert call_args.user_id == valid_challenge_request['user_id']

def test_create_challenge_invalid_input(client, mock_user_challenge_service, valid_challenge_request):
    """입력 값이 유효하지 않을 때 400 응답 및 오류 메시지 반환"""
    
    # Arrange
    error_error_msg = "Invalid challenge_id"
    mock_user_challenge_service.create.side_effect = InvalidInputValue(message=error_error_msg)
    
    # Act
    response = client.post('/api/v2/userchallenge/', json=valid_challenge_request)
    
    # Assert
    assert response.status_code == 400
    response_data = response.json()
    assert 'error' in response_data
    assert 'error_msg' in response_data['error']
    assert error_error_msg in response_data['error']['error_msg']

def test_create_challenge_kubernetes_api_exception(client, mock_user_challenge_service, valid_challenge_request):
    """Kubernetes API 예외 발생 시 502 응답 및 오류 메시지 반환"""
    # Arrange
    api_error = "Kubernetes API error"
    mock_user_challenge_service.create.side_effect = ApiException(reason=api_error)
    
    # Act
    response = client.post('/api/v2/userchallenge/', json=valid_challenge_request)
    
    # Assert
    assert response.status_code == 502  # BadGateway

    response_data = response.json()
    assert 'error' in response_data
    assert 'error_msg' in response_data['error']
    assert api_error in response_data['error']['error_msg']

def test_create_challenge_sqlalchemy_error(client, mock_user_challenge_service, valid_challenge_request):
    """SQLAlchemy 예외 발생 시 500 응답 및 오류 메시지 반환"""
    # Arrange
    db_error = "Database connection failed"
    mock_user_challenge_service.create.side_effect = SQLAlchemyError(db_error)
    
    # Act
    response = client.post('/api/v2/userchallenge/', json=valid_challenge_request)
    
    # Assert
    assert response.status_code == 500  # InternalServerError
    
    response_data = response.json()
    assert 'error' in response_data
    assert 'error_msg' in response_data['error']
    assert db_error in response_data['error']['error_msg']

def test_create_challenge_user_challenge_creation_exception(client, mock_user_challenge_service, valid_challenge_request):
    """UserChallengeCreationException(서비스 로직 에러) 발생 시 500 응답 및 오류 메시지 반환"""
    # Arrange
    service_error = "Failed to create challenge"
    mock_user_challenge_service.create.side_effect = UserChallengeCreationException(message=service_error)
    
    # Act
    response = client.post('/api/v2/userchallenge/', json=valid_challenge_request)

    # Assert
    assert response.status_code == 500  # InternalServerError

    response_data = response.json()
    assert 'error' in response_data
    assert 'error_msg' in response_data['error']
    assert service_error in response_data['error']['error_msg']

def test_create_challenge_generic_exception(client, mock_user_challenge_service, valid_challenge_request):
    """일반적인 예외 발생 시 500 응답 및 오류 메시지 반환"""
    
    # Arrange
    unexpected_error = "Unexpected error occurred"
    mock_user_challenge_service.create.side_effect = Exception(unexpected_error)
    
    # Act
    response = client.post('/api/v2/userchallenge/', json=valid_challenge_request)
    
    # Assert
    assert response.status_code == 500  # InternalServerError

    response_data = response.json()
    assert 'error' in response_data
    assert 'error_msg' in response_data['error']
    assert unexpected_error in response_data['error']['error_msg']

@pytest.mark.parametrize("invalid_request,expected_status", [
    ({"challenge_id": 1}, 422),  # Missing user_id
    ({"user_id": 101}, 422),     # Missing challenge_id
    ({}, 422),                   # Empty request
    ({"challenge_id": "invalid", "user_id": 101}, 422),  # Invalid challenge_id type
    ({"challenge_id": 1, "user_id": "invalid"}, 422),    # Invalid user_id type
])
def test_create_challenge_validation_errors(client, invalid_request, expected_status):
    """입력 값이 유효하지 않을 때 422 응답 및 오류 메시지 반환"""
    # Act
    response = client.post('/api/v2/userchallenge/', json=invalid_request)
    
    # Assert
    assert response.status_code == expected_status

def test_create_challenge_with_extra_fields(client, mock_user_challenge_service, valid_challenge_request):
    """추가 필드가 있을 때 무시되고 200 응답 및 챌린지 정보 반환"""
    # Arrange
    request_with_extra = {
        **valid_challenge_request,
        "extra_field": "should_be_ignored",
        "another_field": 123
    }
    expected_port = 8080
    mock_user_challenge_service.create.return_value = expected_port
    
    # Act
    response = client.post('/api/v2/userchallenge/', json=request_with_extra)
    
    # Assert
    assert response.status_code == 200
    assert response.json() == {'data': {'port': expected_port}}
    mock_user_challenge_service.create.assert_called_once()
    
    # 필수 필드만 서비스에 전달되었는지 확인
    call_args = mock_user_challenge_service.create.call_args[0][0]
    assert call_args.challenge_id == valid_challenge_request['challenge_id']
    assert call_args.user_id == valid_challenge_request['user_id']

def test_create_challenge_service_not_called_on_validation_error(client, mock_user_challenge_service):
    """요청 검증 실패 시 서비스가 호출되지 않고 422 응답 반환"""
    # Arrange
    invalid_request = {"challenge_id": "invalid", "user_id": 101}
    
    # Act
    response = client.post('/api/v2/userchallenge/', json=invalid_request)
    
    # Assert
    assert response.status_code == 422
    mock_user_challenge_service.create.assert_not_called()


def test_delete_challenge_success(client, mock_user_challenge_service, valid_challenge_request):
    """챌린지 삭제 요청 성공 시 200 응답 및 성공 메세지 반환"""
    
    # Arrange
    mock_user_challenge_service.delete.return_value = None
    
    # Act
    response = client.post('/api/v2/userchallenge/delete', json=valid_challenge_request)
    
    # Assert
    assert response.status_code == 200
    assert response.json() == {'message': 'UserChallenge deleted successfully.'}
    mock_user_challenge_service.delete.assert_called_once()

def test_delete_challenge_invalid_input(client, mock_user_challenge_service, valid_challenge_request):
    """입력 값이 유효하지 않을 때 400 응답 및 오류 메시지 반환"""
    # Arrange
    error_error_msg = "Invalid challenge_id"
    mock_user_challenge_service.delete.side_effect = InvalidInputValue(message=error_error_msg)

    # Act
    response = client.post('/api/v2/userchallenge/delete', json=valid_challenge_request)
    
    # Assert
    assert response.status_code == 400

    response_data = response.json()
    assert 'error' in response_data
    assert 'error_msg' in response_data['error']
    assert error_error_msg in response_data['error']['error_msg']

def test_delete_challenge_does_not_exist_challenge(client, mock_user_challenge_service, valid_challenge_request):
    """존재하지 않는 챌린지 삭제 요청 시 400 응답 및 오류 메시지 반환"""
    # Arrange
    error_error_msg = "No existing challenge found for user 101, challenge 1"
    mock_user_challenge_service.delete.side_effect = InvalidInputValue(message=error_error_msg)

    # Act
    response = client.post('/api/v2/userchallenge/delete', json=valid_challenge_request)
    
    # Assert
    assert response.status_code == 400

    response_data = response.json()
    assert 'error' in response_data
    assert 'error_msg' in response_data['error']
    assert error_error_msg in response_data['error']['error_msg']

def test_delete_challenge_user_challenge_deletion_exception(client, mock_user_challenge_service, valid_challenge_request):
    """UserChallengeDeletionException 발생 시 500 응답 및 오류 메시지 반환"""
    # Arrange
    service_error = "Failed to delete challenge"
    mock_user_challenge_service.delete.side_effect = UserChallengeDeletionException(message=service_error)

    # Act
    response = client.post('/api/v2/userchallenge/delete', json=valid_challenge_request)
    
    # Assert
    assert response.status_code == 500

    response_data = response.json()
    assert 'error' in response_data
    assert 'error_msg' in response_data['error']
    assert service_error in response_data['error']['error_msg']

@pytest.mark.parametrize("invalid_request,expected_status", [
    ({"challenge_id": 1}, 422),  # Missing user_id
    ({"user_id": 101}, 422),     # Missing challenge_id
    ({}, 422),                   # Empty request
    ({"challenge_id": "invalid", "user_id": 101}, 422),  # Invalid challenge_id type
    ({"challenge_id": 1, "user_id": "invalid"}, 422),    # Invalid user_id type
])
def test_delete_challenge_validation_errors(client, invalid_request, expected_status):
    """입력 값이 유효하지 않을 때 422 응답 및 오류 메시지 반환"""
    # Act
    response = client.post('/api/v2/userchallenge/delete', json=invalid_request)
    
    # Assert
    assert response.status_code == expected_status

def test_delete_challenge_api_exception(client, mock_user_challenge_service, valid_challenge_request):
    """쿠버네티스 API 예외 발생 시 502 응답 및 오류 메시지 반환"""
    # Arrange
    api_error = "API error"
    mock_user_challenge_service.delete.side_effect = ApiException(reason=api_error)

    # Act
    response = client.post('/api/v2/userchallenge/delete', json=valid_challenge_request)

    # Assert
    assert response.status_code == 502

    response_data = response.json()
    assert 'error' in response_data
    assert 'error_msg' in response_data['error']
    assert api_error in response_data['error']['error_msg']

