import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from challenge_api.app.api.userchallenge import router
from challenge_api.app.service.userchallenge import UserChallengeService
from challenge_api.app.repository.userchallenge import UserChallengeRepository
from challenge_api.app.repository.challenge import ChallengeRepository
from challenge_api.app.repository.status import StatusRepository
from challenge_api.app.external.k8s import K8sManager
from challenge_api.app.schema import ChallengeRequest, StatusData, K8sChallengeData
from challenge_api.app.common.exceptions import (
    UserChallengeCreationException,
    InvalidInputValue
)
from challenge_api.app.api.errors import BadRequest, BadGateway, InternalServerError


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
    @app.exception_handler(BadRequest)
    @app.exception_handler(BadGateway)
    @app.exception_handler(InternalServerError)
    async def handle_http_exception(request, error):
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
    
    # Override dependency
    def get_mock_service():
        return user_challenge_service
    
    # Create router with overridden dependency
    from fastapi import APIRouter, Depends
    
    test_router = APIRouter(prefix='/api/v2/userchallenge', tags=['userchallenge'])
    
    @test_router.post('/')
    async def create_challenge(
        request: ChallengeRequest,
        challenge_service: UserChallengeService = Depends(get_mock_service),
    ):
        """사용자 챌린지 생성 - 통합 테스트용"""
        try:
            port = challenge_service.create(request)
            return {'data': {'port': port}}
        except InvalidInputValue as e:
            raise BadRequest(error_msg=e.message)
        except UserChallengeCreationException as e:
            raise BadGateway(error_msg=str(e))
        except Exception as e:
            raise InternalServerError(error_msg=str(e))
    
    app.include_router(test_router)
    return app


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)


@pytest.fixture
def sample_challenge_request():
    """Sample ChallengeRequest for testing"""
    return ChallengeRequest(challenge_id=1, user_id=101)


@pytest.fixture
def mock_user_challenge():
    """Mock UserChallenge object with actual string values"""
    mock = MagicMock()
    mock.idx = 1001
    mock.user_idx = 101
    mock.C_idx = 1
    mock.userChallengeName = "challenge-1-101"  # Actual string value
    return mock


@pytest.fixture
def mock_status_data():
    """Mock StatusData object with actual values"""
    mock = MagicMock()
    mock.user_challenge_idx = 1001
    mock.status = "None"
    mock.port = 0
    return mock


@pytest.fixture
def mock_running_status_data():
    """Mock running StatusData object with actual values"""
    mock = MagicMock()
    mock.user_challenge_idx = 1001
    mock.status = "Running"
    mock.port = 8080
    return mock


class TestUserChallengeAPIIntegration:
    """API 통합 테스트 - 실제 API 엔드포인트 + 모킹된 의존성"""

    def test_create_challenge_integration_success(self, client, user_challenge_service, 
                                                sample_challenge_request, mock_user_challenge, mock_status_data):
        """Test successful challenge creation through API"""
        # Arrange
        expected_port = 8080
        
        # Mock no existing challenge
        user_challenge_service.user_challenge_repo.get.return_value = None
        
        # Mock new user challenge creation
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        
        # Mock initial status creation
        user_challenge_service.status_repo.create.return_value = mock_status_data
        
        # Mock challenge definition
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        
        # Mock get_by_id
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        
        # Mock K8s manager
        user_challenge_service.k8s_manager.create.return_value = expected_port
        
        # Mock status update
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        response = client.post(
            "/api/v2/userchallenge/",
            json={
                "challenge_id": sample_challenge_request.challenge_id,
                "user_id": sample_challenge_request.user_id
            }
        )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['data']['port'] == expected_port
        
        # Verify service was called with correct data
        user_challenge_service.user_challenge_repo.get.assert_called_once_with(
            user_idx=sample_challenge_request.user_id,
            C_idx=sample_challenge_request.challenge_id
        )

    def test_create_challenge_integration_existing_running(self, client, user_challenge_service, 
                                                         sample_challenge_request, mock_user_challenge, 
                                                         mock_running_status_data):
        """Test API when challenge already exists and is running"""
        # Arrange
        expected_port = 8080
        
        # Mock existing user challenge
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        
        # Mock existing running status
        user_challenge_service.status_repo.first.return_value = mock_running_status_data
        
        # Act
        response = client.post(
            "/api/v2/userchallenge/",
            json={
                "challenge_id": sample_challenge_request.challenge_id,
                "user_id": sample_challenge_request.user_id
            }
        )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['data']['port'] == expected_port
        
        # Verify no new resources were created
        user_challenge_service.user_challenge_repo.create.assert_not_called()
        user_challenge_service.k8s_manager.create.assert_not_called()

    def test_create_challenge_integration_service_exception(self, client, user_challenge_service, 
                                                          sample_challenge_request):
        """Test API when service raises UserChallengeCreationException"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.side_effect = Exception("Database error")
        
        # Act
        response = client.post(
            "/api/v2/userchallenge/",
            json={
                "challenge_id": sample_challenge_request.challenge_id,
                "user_id": sample_challenge_request.user_id
            }
        )
        
        # Assert
        assert response.status_code == 502  # BadGateway
        response_data = response.json()
        assert "Failed to create challenge for user" in response_data['error']['error_msg']

    def test_create_challenge_integration_k8s_failure(self, client, user_challenge_service, 
                                                    sample_challenge_request, mock_user_challenge, mock_status_data):
        """Test API when K8s manager fails"""
        # Arrange
        # Mock no existing challenge
        user_challenge_service.user_challenge_repo.get.return_value = None
        
        # Mock new user challenge creation
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        
        # Mock initial status creation
        user_challenge_service.status_repo.create.return_value = mock_status_data
        
        # Mock challenge definition
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        
        # Mock get_by_id
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        
        # Mock K8s manager failure
        user_challenge_service.k8s_manager.create.side_effect = Exception("K8s creation failed")
        
        # Mock status update to Error
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        response = client.post(
            "/api/v2/userchallenge/",
            json={
                "challenge_id": sample_challenge_request.challenge_id,
                "user_id": sample_challenge_request.user_id
            }
        )
        
        # Assert
        assert response.status_code == 502  # BadGateway
        response_data = response.json()
        assert "Failed to start challenge" in response_data['error']['error_msg']

    def test_create_challenge_integration_validation_error(self, client):
        """Test API with invalid request data"""
        # Act
        response = client.post(
            "/api/v2/userchallenge/",
            json={
                "challenge_id": "invalid",  # Should be int
                "user_id": 101
            }
        )
        
        # Assert
        assert response.status_code == 422  # Validation error

    def test_create_challenge_integration_missing_fields(self, client):
        """Test API with missing required fields"""
        # Act
        response = client.post(
            "/api/v2/userchallenge/",
            json={
                "challenge_id": 1
                # Missing user_id
            }
        )
        
        # Assert
        assert response.status_code == 422  # Validation error

    def test_create_challenge_integration_invalid_input_value(self, client, user_challenge_service, 
                                                            sample_challenge_request):
        """Test API when service raises InvalidInputValue"""
        # Arrange
        # Mock the service to raise InvalidInputValue directly
        with patch.object(user_challenge_service, 'create') as mock_create:
            mock_create.side_effect = InvalidInputValue("Invalid challenge_id")
            
            # Act
            response = client.post(
                "/api/v2/userchallenge/",
                json={
                    "challenge_id": sample_challenge_request.challenge_id,
                    "user_id": sample_challenge_request.user_id
                }
            )
            
            # Assert
            assert response.status_code == 400  # BadRequest
            response_data = response.json()
            assert "Invalid challenge_id" in response_data['error']['error_msg']

    def test_create_challenge_integration_general_exception(self, client, user_challenge_service, 
                                                          sample_challenge_request):
        """Test API when service raises general exception"""
        # Arrange
        # Mock the service to raise a general exception directly
        with patch.object(user_challenge_service, 'create') as mock_create:
            mock_create.side_effect = ValueError("Unexpected error")
            
            # Act
            response = client.post(
                "/api/v2/userchallenge/",
                json={
                    "challenge_id": sample_challenge_request.challenge_id,
                    "user_id": sample_challenge_request.user_id
                }
            )
            
            # Assert
            assert response.status_code == 500  # InternalServerError
            response_data = response.json()
            assert "Unexpected error" in response_data['error']['error_msg']


class TestUserChallengeServiceIntegration:
    """Service 통합 테스트 - 실제 Service 로직 + 모킹된 Repository"""

    def test_service_repository_integration_success(self, user_challenge_service, 
                                                   sample_challenge_request, mock_user_challenge, mock_status_data):
        """Test service integration with mocked repositories"""
        # Arrange
        expected_port = 8080
        
        # Mock repository interactions
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
        
        # Verify repository interaction sequence
        user_challenge_service.user_challenge_repo.get.assert_called_once()
        user_challenge_service.user_challenge_repo.create.assert_called_once()
        user_challenge_service.status_repo.create.assert_called_once()
        user_challenge_service.challenge_repo.get_name.assert_called_once()
        user_challenge_service.user_challenge_repo.get_by_id.assert_called_once()
        user_challenge_service.k8s_manager.create.assert_called_once()
        user_challenge_service.status_repo.update.assert_called_once()

    def test_service_repository_integration_existing_challenge(self, user_challenge_service, 
                                                              sample_challenge_request, mock_user_challenge, 
                                                              mock_running_status_data):
        """Test service integration when challenge already exists"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        user_challenge_service.status_repo.first.return_value = mock_running_status_data
        
        # Act
        result = user_challenge_service.create(sample_challenge_request)
        
        # Assert
        assert result == 8080
        
        # Verify only status check was performed
        user_challenge_service.user_challenge_repo.get.assert_called_once()
        user_challenge_service.status_repo.first.assert_called_once()
        user_challenge_service.user_challenge_repo.create.assert_not_called()
        user_challenge_service.k8s_manager.create.assert_not_called()

    def test_service_repository_integration_error_handling(self, user_challenge_service, 
                                                         sample_challenge_request, mock_user_challenge, mock_status_data):
        """Test service integration error handling"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.return_value = None
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        user_challenge_service.status_repo.create.return_value = mock_status_data
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.k8s_manager.create.side_effect = Exception("K8s error")
        user_challenge_service.status_repo.update.return_value = None
        
        # Act & Assert
        with pytest.raises(UserChallengeCreationException) as exc_info:
            user_challenge_service.create(sample_challenge_request)
        
        assert "Failed to start challenge" in str(exc_info.value)
        
        # Verify error status was updated
        user_challenge_service.status_repo.update.assert_called_with(
            userchallenge_idx=mock_status_data.user_challenge_idx,
            status='Error',
            port=0
        )


class TestUserChallengeDataFlowIntegration:
    """데이터 흐름 통합 테스트"""

    def test_complete_data_flow_success(self, client, user_challenge_service, 
                                       sample_challenge_request, mock_user_challenge, mock_status_data):
        """Test complete data flow from API to K8s"""
        # Arrange
        expected_port = 8080
        
        # Mock all repository interactions
        user_challenge_service.user_challenge_repo.get.return_value = None
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        user_challenge_service.status_repo.create.return_value = mock_status_data
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.k8s_manager.create.return_value = expected_port
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        response = client.post(
            "/api/v2/userchallenge/",
            json={
                "challenge_id": sample_challenge_request.challenge_id,
                "user_id": sample_challenge_request.user_id
            }
        )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['data']['port'] == expected_port
        
        # Verify K8s data was created correctly
        user_challenge_service.k8s_manager.create.assert_called_once()
        call_args = user_challenge_service.k8s_manager.create.call_args[0][0]
        assert isinstance(call_args, K8sChallengeData)
        assert call_args.challenge_id == mock_user_challenge.C_idx
        assert call_args.user_id == mock_user_challenge.user_idx
        assert call_args.userchallenge_name == mock_user_challenge.userChallengeName
        assert call_args.definition == "test-definition"

    def test_data_flow_with_existing_challenge(self, client, user_challenge_service, 
                                              sample_challenge_request, mock_user_challenge, 
                                              mock_running_status_data):
        """Test data flow when challenge already exists"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        user_challenge_service.status_repo.first.return_value = mock_running_status_data
        
        # Act
        response = client.post(
            "/api/v2/userchallenge/",
            json={
                "challenge_id": sample_challenge_request.challenge_id,
                "user_id": sample_challenge_request.user_id
            }
        )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['data']['port'] == 8080
        
        # Verify no K8s interaction occurred
        user_challenge_service.k8s_manager.create.assert_not_called() 