import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError
from kubernetes.client.rest import ApiException

from challenge_api.app.api.userchallenge import router
from challenge_api.app.service.userchallenge import UserChallengeService
from challenge_api.app.repository.userchallenge import UserChallengeRepository
from challenge_api.app.repository.challenge import ChallengeRepository
from challenge_api.app.repository.status import StatusRepository
from challenge_api.app.external.k8s import K8sManager
from challenge_api.app.schema import ChallengeRequest, StatusData, K8sChallengeData
from challenge_api.app.common.exceptions import (
    UserChallengeCreationException,
    UserChallengeDeletionException,
    UserChallengeNotFound,
    ChallengeStatusNotFound,
    InvalidInputValue,
    BaseException
)
from challenge_api.app.api.errors import BadRequest, BadGateway, InternalServerError, BaseHttpException


@pytest.fixture
def mock_user_challenge_repo():
    """Mock UserChallengeRepository"""
    return MagicMock()


@pytest.fixture
def mock_challenge_repo():
    """Mock ChallengeRepository"""
    return MagicMock()


@pytest.fixture
def mock_status_repo():
    """Mock StatusRepository"""
    return MagicMock()


@pytest.fixture
def mock_k8s_manager():
    """Mock K8sManager"""
    return MagicMock()


@pytest.fixture
def user_challenge_service(mock_user_challenge_repo, mock_challenge_repo, mock_status_repo, mock_k8s_manager):
    """Create UserChallengeService instance with mocked dependencies"""
    return UserChallengeService(
        user_challenge_repo=mock_user_challenge_repo,
        challenge_repo=mock_challenge_repo,
        status_repo=mock_status_repo,
        k8s_manager=mock_k8s_manager
    )


@pytest.fixture
def test_app(user_challenge_service):
    """Create FastAPI test app with mocked dependencies"""
    app = FastAPI()
    
    # Add exception handlers for custom exceptions (same as main app)
    @app.exception_handler(BaseHttpException)
    async def handle_http_exception(request, error: BaseHttpException):
        """Global error handler for all BaseHttpException instances"""
        response_data = {
            'error': {
                'message': error.message,
            },
            'timestamp': '2024-01-01T00:00:00'  # Fixed timestamp for testing
        }
        
        # Add error_msg if available
        if error.error_msg:
            response_data['error']['error_msg'] = error.error_msg
        
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=error.status_code,
            content=response_data
        )
    
    # Include the actual router
    app.include_router(router)
    
    # Override dependency
    def get_mock_service():
        return user_challenge_service
    
    # Override the dependency
    from challenge_api.app.dependency import get_user_challenge_service
    app.dependency_overrides[get_user_challenge_service] = get_mock_service
    
    return app


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)


@pytest.fixture
def sample_challenge_request():
    """Sample challenge request data"""
    return ChallengeRequest(challenge_id=1, user_id=101)


def to_dict(request: ChallengeRequest) -> dict:
    """ChallengeRequest를 딕셔너리로 변환하는 헬퍼 함수"""
    return {
        "challenge_id": request.challenge_id,
        "user_id": request.user_id
    }


@pytest.fixture
def mock_user_challenge():
    """Mock UserChallenge object"""
    mock = MagicMock()
    mock.idx = 1001
    mock.user_idx = 101
    mock.C_idx = 1
    mock.userChallengeName = "challenge-1-101"
    return mock


@pytest.fixture
def mock_status_data():
    """Mock StatusData object"""
    mock = MagicMock()
    mock.idx = 1
    mock.user_challenge_idx = 1001
    mock.status = "None"
    mock.port = 0
    return mock


@pytest.fixture
def mock_running_status_data():
    """Mock running StatusData object"""
    mock = MagicMock()
    mock.idx = 1
    mock.user_challenge_idx = 1001
    mock.status = "Running"
    mock.port = 8080
    return mock


# ============================================================================
# API 통합 테스트 - 모든 엔드포인트
# ============================================================================

class TestUserChallengeAPIIntegration:
    """API 레벨 통합 테스트"""

    def test_create_challenge_integration_success(self, client, user_challenge_service, 
                                                sample_challenge_request, mock_user_challenge, mock_status_data):
        """챌린지 생성 API 통합 테스트 - 성공 케이스"""
        # Arrange
        expected_port = 8080
        
        # Mock service dependencies
        user_challenge_service.user_challenge_repo.get.return_value = None
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        user_challenge_service.status_repo.create.return_value = mock_status_data
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.k8s_manager.create.return_value = expected_port
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        response = client.post('/api/v2/userchallenge/', json=to_dict(sample_challenge_request))
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {'data': {'port': expected_port}}
        
        # Verify service was called correctly
        user_challenge_service.user_challenge_repo.get.assert_called_once_with(
            user_idx=sample_challenge_request.user_id,
            C_idx=sample_challenge_request.challenge_id
        )

    def test_create_challenge_integration_existing_running(self, client, user_challenge_service, 
                                                         sample_challenge_request, mock_user_challenge, 
                                                         mock_running_status_data):
        """기존 실행 중인 챌린지 생성 API 통합 테스트"""
        # Arrange
        expected_port = 8080
        
        # Mock existing running challenge
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        user_challenge_service.status_repo.first.return_value = mock_running_status_data
        
        # Act
        response = client.post('/api/v2/userchallenge/', json=to_dict(sample_challenge_request))
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {'data': {'port': expected_port}}

    def test_create_challenge_integration_service_exception(self, client, user_challenge_service, 
                                                          sample_challenge_request):
        """서비스 예외 발생 시 API 통합 테스트"""
        # Arrange
        # Mock the service method to raise exception
        with patch.object(user_challenge_service, 'create') as mock_create:
            mock_create.side_effect = UserChallengeCreationException(
                message="Failed to create challenge"
            )
            
            # Act
            response = client.post('/api/v2/userchallenge/', json=to_dict(sample_challenge_request))
            
            # Assert
            assert response.status_code == 500
            response_data = response.json()
            assert 'error' in response_data
            assert 'error_msg' in response_data['error']
            assert "Failed to create challenge" in response_data['error']['error_msg']

    def test_create_challenge_integration_k8s_failure(self, client, user_challenge_service, 
                                                    sample_challenge_request, mock_user_challenge, mock_status_data):
        """K8s 실패 시 API 통합 테스트"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.return_value = None
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        user_challenge_service.status_repo.create.return_value = mock_status_data
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.k8s_manager.create.side_effect = ApiException(reason="K8s API error")
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        response = client.post('/api/v2/userchallenge/', json=to_dict(sample_challenge_request))
        
        # Assert
        assert response.status_code == 500  # UserChallengeCreationException은 500으로 처리됨
        response_data = response.json()
        assert 'error' in response_data
        assert 'error_msg' in response_data['error']
        assert "Failed to start challenge" in response_data['error']['error_msg']

    def test_create_challenge_integration_validation_error(self, client):
        """입력값 검증 오류 API 통합 테스트"""
        # Act
        response = client.post('/api/v2/userchallenge/', json={"challenge_id": 1})  # Missing user_id
        
        # Assert
        assert response.status_code == 422

    def test_create_challenge_integration_missing_fields(self, client):
        """필수 필드 누락 API 통합 테스트"""
        # Act
        response = client.post('/api/v2/userchallenge/', json={})  # Empty request
        
        # Assert
        assert response.status_code == 422

    def test_create_challenge_integration_invalid_input_value(self, client, user_challenge_service, 
                                                            sample_challenge_request):
        """InvalidInputValue 예외 API 통합 테스트"""
        # Arrange
        # Mock the service method to raise exception
        with patch.object(user_challenge_service, 'create') as mock_create:
            mock_create.side_effect = InvalidInputValue(message="Invalid challenge_id")
            
            # Act
            response = client.post('/api/v2/userchallenge/', json=to_dict(sample_challenge_request))
            
            # Assert
            assert response.status_code == 400
            response_data = response.json()
            assert 'error' in response_data
            assert 'error_msg' in response_data['error']
            assert "Invalid challenge_id" in response_data['error']['error_msg']

    def test_create_challenge_integration_general_exception(self, client, user_challenge_service, 
                                                          sample_challenge_request):
        """일반 예외 API 통합 테스트"""
        # Arrange
        # Mock the service method to raise exception
        with patch.object(user_challenge_service, 'create') as mock_create:
            mock_create.side_effect = Exception("Database connection failed")
            
            # Act
            response = client.post('/api/v2/userchallenge/', json=to_dict(sample_challenge_request))
            
            # Assert
            assert response.status_code == 500
            response_data = response.json()
            assert 'error' in response_data
            assert 'error_msg' in response_data['error']
            assert "Database connection failed" in response_data['error']['error_msg']

    # ============================================================================
    # DELETE 엔드포인트 통합 테스트
    # ============================================================================

    def test_delete_challenge_integration_success(self, client, user_challenge_service, 
                                                sample_challenge_request, mock_user_challenge, mock_status_data):
        """챌린지 삭제 API 통합 테스트 - 성공 케이스"""
        # Arrange
        mock_user_challenge.idx = 1001
        mock_status_data.user_challenge_idx = 1001
        
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        user_challenge_service.status_repo.first.return_value = mock_status_data
        user_challenge_service.user_challenge_repo.delete.return_value = None
        user_challenge_service.k8s_manager.delete.return_value = None
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        response = client.post('/api/v2/userchallenge/delete', json=to_dict(sample_challenge_request))
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {'message': 'UserChallenge deleted successfully.'}

    def test_delete_challenge_integration_not_found(self, client, user_challenge_service, 
                                                  sample_challenge_request):
        """존재하지 않는 챌린지 삭제 API 통합 테스트"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.return_value = None
        
        # Act
        response = client.post('/api/v2/userchallenge/delete', json=to_dict(sample_challenge_request))
        
        # Assert
        assert response.status_code == 500
        response_data = response.json()
        assert 'error' in response_data
        assert 'error_msg' in response_data['error']
        assert "No existing challenge found" in response_data['error']['error_msg']

    def test_delete_challenge_integration_k8s_failure(self, client, user_challenge_service, 
                                                    sample_challenge_request, mock_user_challenge, mock_status_data):
        """K8s 삭제 실패 API 통합 테스트"""
        # Arrange
        mock_user_challenge.idx = 1001
        mock_status_data.user_challenge_idx = 1001
        
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        user_challenge_service.status_repo.first.return_value = mock_status_data
        user_challenge_service.user_challenge_repo.delete.return_value = None
        user_challenge_service.k8s_manager.delete.side_effect = ApiException(reason="K8s deletion failed")
        
        # Act
        response = client.post('/api/v2/userchallenge/delete', json=to_dict(sample_challenge_request))
        
        # Assert
        assert response.status_code == 500  # UserChallengeDeletionException은 500으로 처리됨
        response_data = response.json()
        assert 'error' in response_data
        assert 'error_msg' in response_data['error']
        assert "Failed to delete challenge for user" in response_data['error']['error_msg']

    # ============================================================================
    # GET STATUS 엔드포인트 통합 테스트
    # ============================================================================

    def test_get_status_integration_success(self, client, user_challenge_service, 
                                          sample_challenge_request, mock_user_challenge, mock_running_status_data):
        """챌린지 상태 조회 API 통합 테스트 - 성공 케이스"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        user_challenge_service.status_repo.first.return_value = mock_running_status_data
        
        # Act
        response = client.post('/api/v2/userchallenge/status', json=to_dict(sample_challenge_request))
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {
            'data': {
                'port': mock_running_status_data.port,
                'status': mock_running_status_data.status
            }
        }

    def test_get_status_integration_not_found(self, client, user_challenge_service, 
                                            sample_challenge_request):
        """존재하지 않는 챌린지 상태 조회 API 통합 테스트"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.return_value = None
        
        # Act
        response = client.post('/api/v2/userchallenge/status', json=to_dict(sample_challenge_request))
        
        # Assert
        assert response.status_code == 503
        response_data = response.json()
        assert 'error' in response_data
        assert response_data['error']['message'] == "No existing challenge found for user 101, challenge 1"

    def test_get_status_integration_base_exception(self, client, user_challenge_service, 
                                                 sample_challenge_request):
        """BaseException 발생 시 상태 조회 API 통합 테스트"""
        # Arrange
        # Mock the service method to raise exception
        with patch.object(user_challenge_service, 'get_status') as mock_get_status:
            mock_get_status.side_effect = ChallengeStatusNotFound(message="Failed to get status")
            
            # Act
            response = client.post('/api/v2/userchallenge/status', json=to_dict(sample_challenge_request))
            
            # Assert
            assert response.status_code == 503
            response_data = response.json()
            assert 'error' in response_data
            assert response_data['error']['message'] == "Failed to get status"

    def test_get_status_integration_general_exception(self, client, user_challenge_service, 
                                                    sample_challenge_request):
        """일반 예외 발생 시 상태 조회 API 통합 테스트"""
        # Arrange
        # Mock the service method to raise exception
        with patch.object(user_challenge_service, 'get_status') as mock_get_status:
            mock_get_status.side_effect = Exception("Database error")
            
            # Act
            response = client.post('/api/v2/userchallenge/status', json=to_dict(sample_challenge_request))
            
            # Assert
            assert response.status_code == 500
            response_data = response.json()
            assert 'error' in response_data
            assert response_data['error']['message'] == "Internal server error"
            assert 'error_msg' in response_data['error']
            assert "Database error" in response_data['error']['error_msg']


# ============================================================================
# 서비스 통합 테스트
# ============================================================================

class TestUserChallengeServiceIntegration:
    """서비스 레벨 통합 테스트"""

    def test_service_repository_integration_success(self, user_challenge_service, 
                                                   sample_challenge_request, mock_user_challenge, mock_status_data):
        """서비스-저장소 통합 테스트 - 성공 케이스"""
        # Arrange
        expected_port = 8080
        
        # Mock repository calls
        user_challenge_service.user_challenge_repo.get.return_value = None
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        user_challenge_service.status_repo.create.return_value = mock_status_data
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.k8s_manager.create.return_value = expected_port
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        result = user_challenge_service.create(sample_challenge_request)
        
        # Assert
        assert result == expected_port
        
        # Verify repository interactions
        user_challenge_service.user_challenge_repo.get.assert_called_once()
        user_challenge_service.user_challenge_repo.create.assert_called_once()
        user_challenge_service.status_repo.create.assert_called_once()
        user_challenge_service.k8s_manager.create.assert_called_once()
        user_challenge_service.status_repo.update.assert_called_once()

    def test_service_repository_integration_existing_challenge(self, user_challenge_service, 
                                                              sample_challenge_request, mock_user_challenge, 
                                                              mock_running_status_data):
        """기존 챌린지 서비스-저장소 통합 테스트"""
        # Arrange
        expected_port = 8080
        
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        user_challenge_service.status_repo.first.return_value = mock_running_status_data
        
        # Act
        result = user_challenge_service.create(sample_challenge_request)
        
        # Assert
        assert result == expected_port
        
        # Verify no new resources were created
        user_challenge_service.user_challenge_repo.create.assert_not_called()
        user_challenge_service.k8s_manager.create.assert_not_called()

    def test_service_repository_integration_error_handling(self, user_challenge_service, 
                                                         sample_challenge_request, mock_user_challenge, mock_status_data):
        """서비스-저장소 통합 테스트 - 오류 처리"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.return_value = None
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        user_challenge_service.status_repo.create.return_value = mock_status_data
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.k8s_manager.create.side_effect = Exception("K8s creation failed")
        user_challenge_service.status_repo.update.return_value = None
        
        # Act & Assert
        with pytest.raises(UserChallengeCreationException) as exc_info:
            user_challenge_service.create(sample_challenge_request)
        
        assert "Failed to start challenge" in str(exc_info.value)
        
        # Verify error status was set
        user_challenge_service.status_repo.update.assert_called_with(
            userchallenge_idx=mock_status_data.user_challenge_idx,
            status='Error',
            port=0
        )

    def test_service_get_status_integration_success(self, user_challenge_service, 
                                                  sample_challenge_request, mock_user_challenge, mock_running_status_data):
        """서비스 get_status 통합 테스트 - 성공 케이스"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        user_challenge_service.status_repo.first.return_value = mock_running_status_data
        
        # Act
        result = user_challenge_service.get_status(sample_challenge_request)
        
        # Assert
        assert result == mock_running_status_data
        user_challenge_service.user_challenge_repo.get.assert_called_once_with(
            user_idx=sample_challenge_request.user_id,
            C_idx=sample_challenge_request.challenge_id
        )
        user_challenge_service.status_repo.first.assert_called_once_with(mock_user_challenge.idx)

    def test_service_get_status_integration_not_found(self, user_challenge_service, 
                                                    sample_challenge_request):
        """서비스 get_status 통합 테스트 - 찾을 수 없음"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.return_value = None
        
        # Act & Assert
        with pytest.raises(ChallengeStatusNotFound) as exc_info:
            user_challenge_service.get_status(sample_challenge_request)
        
        assert "No existing challenge found for user" in str(exc_info.value)

    def test_service_delete_integration_success(self, user_challenge_service, 
                                              sample_challenge_request, mock_user_challenge, mock_status_data):
        """서비스 delete 통합 테스트 - 성공 케이스"""
        # Arrange
        mock_user_challenge.idx = 1001
        mock_status_data.user_challenge_idx = 1001
        
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        user_challenge_service.status_repo.first.return_value = mock_status_data
        user_challenge_service.user_challenge_repo.delete.return_value = None
        user_challenge_service.k8s_manager.delete.return_value = None
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        user_challenge_service.delete(sample_challenge_request)
        
        # Assert
        user_challenge_service.user_challenge_repo.delete.assert_called_once_with(1001)
        user_challenge_service.k8s_manager.delete.assert_called_once_with(1001)
        user_challenge_service.status_repo.update.assert_called_once_with(
            user_challenge_idx=1001,
            status='Deleted',
            port=0
        )


# ============================================================================
# 데이터 플로우 통합 테스트
# ============================================================================

class TestUserChallengeDataFlowIntegration:
    """전체 데이터 플로우 통합 테스트"""

    def test_complete_data_flow_success(self, client, user_challenge_service, 
                                       sample_challenge_request, mock_user_challenge, mock_status_data):
        """완전한 데이터 플로우 통합 테스트 - 성공 케이스"""
        # Arrange
        expected_port = 8080
        
        # Mock all dependencies
        user_challenge_service.user_challenge_repo.get.return_value = None
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        user_challenge_service.status_repo.create.return_value = mock_status_data
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.k8s_manager.create.return_value = expected_port
        user_challenge_service.status_repo.update.return_value = None
        
        # Act - Create challenge
        create_response = client.post('/api/v2/userchallenge/', json=to_dict(sample_challenge_request))
        
        # Assert - Create success
        assert create_response.status_code == 200
        assert create_response.json() == {'data': {'port': expected_port}}
        
        # Arrange for status check
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        user_challenge_service.status_repo.first.return_value = mock_status_data
        mock_status_data.status = "Running"
        mock_status_data.port = expected_port
        
        # Act - Get status
        status_response = client.post('/api/v2/userchallenge/status', json=to_dict(sample_challenge_request))
        
        # Assert - Status success
        assert status_response.status_code == 200
        assert status_response.json() == {
            'data': {
                'port': expected_port,
                'status': "Running"
            }
        }
        
        # Arrange for deletion
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        user_challenge_service.status_repo.first.return_value = mock_status_data
        user_challenge_service.user_challenge_repo.delete.return_value = None
        user_challenge_service.k8s_manager.delete.return_value = None
        user_challenge_service.status_repo.update.return_value = None
        
        # Act - Delete challenge
        delete_response = client.post('/api/v2/userchallenge/delete', json=to_dict(sample_challenge_request))
        
        # Assert - Delete success
        assert delete_response.status_code == 200
        assert delete_response.json() == {'message': 'UserChallenge deleted successfully.'}

    def test_data_flow_with_existing_challenge(self, client, user_challenge_service, 
                                              sample_challenge_request, mock_user_challenge, 
                                              mock_running_status_data):
        """기존 챌린지가 있는 데이터 플로우 통합 테스트"""
        # Arrange
        expected_port = 8080
        
        # Mock existing running challenge
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        user_challenge_service.status_repo.first.return_value = mock_running_status_data
        
        # Act - Create challenge (should return existing)
        create_response = client.post('/api/v2/userchallenge/', json=to_dict(sample_challenge_request))
        
        # Assert - Should return existing port
        assert create_response.status_code == 200
        assert create_response.json() == {'data': {'port': expected_port}}
        
        # Act - Get status
        status_response = client.post('/api/v2/userchallenge/status', json=to_dict(sample_challenge_request))
        
        # Assert - Status should match
        assert status_response.status_code == 200
        assert status_response.json() == {
            'data': {
                'port': expected_port,
                'status': "Running"
            }
        }

    def test_data_flow_error_recovery(self, client, user_challenge_service, 
                                    sample_challenge_request, mock_user_challenge, mock_status_data):
        """오류 복구 데이터 플로우 통합 테스트"""
        # Arrange - First create fails
        user_challenge_service.user_challenge_repo.get.return_value = None
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        user_challenge_service.status_repo.create.return_value = mock_status_data
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.k8s_manager.create.side_effect = Exception("K8s creation failed")
        user_challenge_service.status_repo.update.return_value = None
        
        # Act - Create challenge (should fail)
        create_response = client.post('/api/v2/userchallenge/', json=to_dict(sample_challenge_request))
        
        # Assert - Should return 500 error
        assert create_response.status_code == 500
        
        # Arrange - Retry with success
        user_challenge_service.k8s_manager.create.side_effect = None
        user_challenge_service.k8s_manager.create.return_value = 8080
        
        # Act - Retry create
        retry_response = client.post('/api/v2/userchallenge/', json=to_dict(sample_challenge_request))
        
        # Assert - Should succeed on retry
        assert retry_response.status_code == 200
        assert retry_response.json() == {'data': {'port': 8080}}


# ============================================================================
# 외부 의존성 통합 테스트
# ============================================================================

class TestExternalDependenciesIntegration:
    """외부 의존성 통합 테스트"""

    def test_k8s_manager_integration_success(self, user_challenge_service, 
                                           sample_challenge_request, mock_user_challenge, mock_status_data):
        """K8s 매니저 통합 테스트 - 성공 케이스"""
        # Arrange
        expected_port = 8080
        
        user_challenge_service.user_challenge_repo.get.return_value = None
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        user_challenge_service.status_repo.create.return_value = mock_status_data
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.k8s_manager.create.return_value = expected_port
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        result = user_challenge_service.create(sample_challenge_request)
        
        # Assert
        assert result == expected_port
        
        # Verify K8s manager was called with correct data
        user_challenge_service.k8s_manager.create.assert_called_once()
        call_args = user_challenge_service.k8s_manager.create.call_args[0][0]
        assert isinstance(call_args, K8sChallengeData)
        assert call_args.challenge_id == sample_challenge_request.challenge_id
        assert call_args.user_id == sample_challenge_request.user_id
        assert call_args.userchallenge_name == sample_challenge_request.name
        assert call_args.definition == "test-definition"

    def test_k8s_manager_integration_failure(self, user_challenge_service, 
                                           sample_challenge_request, mock_user_challenge, mock_status_data):
        """K8s 매니저 통합 테스트 - 실패 케이스"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.return_value = None
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        user_challenge_service.status_repo.create.return_value = mock_status_data
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.k8s_manager.create.side_effect = Exception("K8s resource creation failed")
        user_challenge_service.status_repo.update.return_value = None
        
        # Act & Assert
        with pytest.raises(UserChallengeCreationException) as exc_info:
            user_challenge_service.create(sample_challenge_request)
        
        assert "Failed to start challenge" in str(exc_info.value)
        assert "K8s resource creation failed" in str(exc_info.value)

    def test_repository_integration_success(self, user_challenge_service, 
                                          sample_challenge_request, mock_user_challenge, mock_status_data):
        """저장소 통합 테스트 - 성공 케이스"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.return_value = None
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        user_challenge_service.status_repo.create.return_value = mock_status_data
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.k8s_manager.create.return_value = 8080
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        result = user_challenge_service.create(sample_challenge_request)
        
        # Assert
        assert result == 8080
        
        # Verify repository interactions
        user_challenge_service.user_challenge_repo.get.assert_called_once_with(
            user_idx=sample_challenge_request.user_id,
            C_idx=sample_challenge_request.challenge_id
        )
        user_challenge_service.user_challenge_repo.create.assert_called_once_with(
            user_idx=sample_challenge_request.user_id,
            C_idx=sample_challenge_request.challenge_id,
            userChallengeName=sample_challenge_request.name
        )
        user_challenge_service.status_repo.create.assert_called_once_with(
            user_challenge_idx=mock_user_challenge.idx,
            status='None',
            port=0
        )

    def test_repository_integration_failure(self, user_challenge_service, 
                                          sample_challenge_request):
        """저장소 통합 테스트 - 실패 케이스"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.side_effect = SQLAlchemyError("Database connection failed")
        
        # Act & Assert
        with pytest.raises(UserChallengeCreationException) as exc_info:
            user_challenge_service.create(sample_challenge_request)
        
        assert "Failed to create challenge for user" in str(exc_info.value)
        assert "Database connection failed" in str(exc_info.value)


# ============================================================================
# 성능 및 부하 테스트 시뮬레이션
# ============================================================================

class TestPerformanceIntegration:
    """성능 및 부하 테스트 시뮬레이션"""

    def test_multiple_concurrent_requests(self, client, user_challenge_service, 
                                        sample_challenge_request, mock_user_challenge, mock_status_data):
        """여러 동시 요청 시뮬레이션 테스트"""
        # Arrange
        expected_port = 8080
        
        user_challenge_service.user_challenge_repo.get.return_value = None
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        user_challenge_service.status_repo.create.return_value = mock_status_data
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.k8s_manager.create.return_value = expected_port
        user_challenge_service.status_repo.update.return_value = None
        
        # Act - Send multiple requests
        responses = []
        for i in range(5):
            response = client.post('/api/v2/userchallenge/', json=to_dict(sample_challenge_request))
            responses.append(response)
        
        # Assert - All should succeed
        for response in responses:
            assert response.status_code == 200
            assert response.json() == {'data': {'port': expected_port}}
        
        # Verify service was called correct number of times
        assert user_challenge_service.user_challenge_repo.get.call_count == 5

    def test_mixed_endpoint_requests(self, client, user_challenge_service, 
                                   sample_challenge_request, mock_user_challenge, mock_status_data):
        """여러 엔드포인트 혼합 요청 테스트"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        user_challenge_service.status_repo.first.return_value = mock_status_data
        user_challenge_service.user_challenge_repo.delete.return_value = None
        user_challenge_service.k8s_manager.delete.return_value = None
        user_challenge_service.status_repo.update.return_value = None
        
        # Act - Mixed requests
        create_response = client.post('/api/v2/userchallenge/', json=to_dict(sample_challenge_request))
        status_response = client.post('/api/v2/userchallenge/status', json=to_dict(sample_challenge_request))
        delete_response = client.post('/api/v2/userchallenge/delete', json=to_dict(sample_challenge_request))
        
        # Assert - All should succeed
        assert create_response.status_code == 200
        assert status_response.status_code == 200
        assert delete_response.status_code == 200


# ============================================================================
# 엣지 케이스 통합 테스트
# ============================================================================

class TestEdgeCasesIntegration:
    """엣지 케이스 통합 테스트"""

    def test_large_numbers_integration(self, client, user_challenge_service, 
                                     mock_user_challenge, mock_status_data):
        """큰 숫자 값 통합 테스트"""
        # Arrange
        large_request = ChallengeRequest(challenge_id=999999999, user_id=999999999)
        
        user_challenge_service.user_challenge_repo.get.return_value = None
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        user_challenge_service.status_repo.create.return_value = mock_status_data
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.k8s_manager.create.return_value = 8080
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        response = client.post('/api/v2/userchallenge/', json=to_dict(large_request))
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {'data': {'port': 8080}}

    def test_zero_values_integration(self, client, user_challenge_service, 
                                   mock_user_challenge, mock_status_data):
        """0 값 통합 테스트"""
        # Arrange
        zero_request = ChallengeRequest(challenge_id=0, user_id=0)
        
        user_challenge_service.user_challenge_repo.get.return_value = None
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        user_challenge_service.status_repo.create.return_value = mock_status_data
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.k8s_manager.create.return_value = 8080
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        response = client.post('/api/v2/userchallenge/', json=to_dict(zero_request))
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {'data': {'port': 8080}}

    def test_extra_fields_integration(self, client, user_challenge_service, 
                                    sample_challenge_request, mock_user_challenge, mock_status_data):
        """추가 필드 포함 통합 테스트"""
        # Arrange
        request_with_extra = to_dict(sample_challenge_request)
        request_with_extra.update({
            "extra_field": "extra_value",
            "another_field": 123
        })
        
        user_challenge_service.user_challenge_repo.get.return_value = None
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        user_challenge_service.status_repo.create.return_value = mock_status_data
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.k8s_manager.create.return_value = 8080
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        response = client.post('/api/v2/userchallenge/', json=request_with_extra)
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {'data': {'port': 8080}} 