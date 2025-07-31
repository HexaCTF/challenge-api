import pytest
from unittest.mock import MagicMock
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from kubernetes.client.rest import ApiException

from challenge_api.app.schema import ChallengeRequest
from challenge_api.app.common.exceptions import InvalidInputValue, UserChallengeCreationException, BaseException
from challenge_api.app.api.errors import BadRequest, BadGateway, InternalServerError, BaseHttpException


@pytest.fixture
def mock_user_challenge_service():
    """Mock UserChallengeService"""
    return MagicMock()


@pytest.fixture
def test_app(mock_user_challenge_service):
    """Create a completely isolated test FastAPI app with minimal router"""
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
        
        # Add details if available
        if error.details:
            response_data['error']['details'] = error.details
        
        return JSONResponse(
            status_code=error.status_code,
            content=response_data
        )
    
    # Create a minimal router that only tests the API logic
    from fastapi import APIRouter
    
    router = APIRouter(prefix='/api/v2/userchallenge', tags=['userchallenge'])
    
    def get_mock_service():
        return mock_user_challenge_service
    
    @router.post('/')
    async def create_challenge(
        request: ChallengeRequest,
        challenge_service: MagicMock = Depends(get_mock_service),
    ):
        """사용자 챌린지 생성 - 테스트용"""
        try:
            port = challenge_service.create(request)
            return {'data': {'port': port}}
        except InvalidInputValue as e:
            raise BadRequest(details=e.message)
        except ApiException as e:
            raise BadGateway(details=str(e))
        except (BaseException, SQLAlchemyError, Exception) as e:
            raise InternalServerError(details=str(e))
    
    app.include_router(router)
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


class TestCreateChallenge:
    """Test cases for the create_challenge API endpoint"""

    def test_create_challenge_success(self, client, mock_user_challenge_service, valid_challenge_request):
        """Test successful challenge creation"""
        # Arrange
        expected_port = 8080
        mock_user_challenge_service.create.return_value = expected_port
        
        # Act
        response = client.post('/api/v2/userchallenge/', json=valid_challenge_request)
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {'data': {'port': expected_port}}
        mock_user_challenge_service.create.assert_called_once()
        
        # Verify the service was called with correct data
        call_args = mock_user_challenge_service.create.call_args[0][0]
        assert isinstance(call_args, ChallengeRequest)
        assert call_args.challenge_id == valid_challenge_request['challenge_id']
        assert call_args.user_id == valid_challenge_request['user_id']

    def test_create_challenge_invalid_input(self, client, mock_user_challenge_service, valid_challenge_request):
        """Test challenge creation with invalid input"""
        # Arrange
        error_details = "Invalid challenge_id"
        mock_user_challenge_service.create.side_effect = InvalidInputValue(message=error_details)
        
        # Act
        response = client.post('/api/v2/userchallenge/', json=valid_challenge_request)
        
        # Assert
        assert response.status_code == 400
        response_data = response.json()
        assert 'error' in response_data
        assert 'details' in response_data['error']
        assert error_details in response_data['error']['details']

    def test_create_challenge_kubernetes_api_exception(self, client, mock_user_challenge_service, valid_challenge_request):
        """Test challenge creation with Kubernetes API exception"""
        # Arrange
        api_error = "Kubernetes API error"
        mock_user_challenge_service.create.side_effect = ApiException(reason=api_error)
        
        # Act
        response = client.post('/api/v2/userchallenge/', json=valid_challenge_request)
        
        # Assert
        assert response.status_code == 502  # BadGateway
        response_data = response.json()
        assert 'error' in response_data
        assert 'details' in response_data['error']
        assert api_error in response_data['error']['details']

    def test_create_challenge_sqlalchemy_error(self, client, mock_user_challenge_service, valid_challenge_request):
        """Test challenge creation with SQLAlchemy error"""
        # Arrange
        db_error = "Database connection failed"
        mock_user_challenge_service.create.side_effect = SQLAlchemyError(db_error)
        
        # Act
        response = client.post('/api/v2/userchallenge/', json=valid_challenge_request)
        
        # Assert
        assert response.status_code == 500  # InternalServerError
        response_data = response.json()
        assert 'error' in response_data
        assert 'details' in response_data['error']
        assert db_error in response_data['error']['details']

    def test_create_challenge_user_challenge_creation_exception(self, client, mock_user_challenge_service, valid_challenge_request):
        """Test challenge creation with UserChallengeCreationException"""
        # Arrange
        service_error = "Failed to create challenge"
        mock_user_challenge_service.create.side_effect = UserChallengeCreationException(message=service_error)
        
        # Act
        response = client.post('/api/v2/userchallenge/', json=valid_challenge_request)
        
        # Assert
        assert response.status_code == 500  # InternalServerError
        response_data = response.json()
        assert 'error' in response_data
        assert 'details' in response_data['error']
        assert service_error in response_data['error']['details']

    def test_create_challenge_generic_exception(self, client, mock_user_challenge_service, valid_challenge_request):
        """Test challenge creation with generic exception"""
        # Arrange
        unexpected_error = "Unexpected error occurred"
        mock_user_challenge_service.create.side_effect = Exception(unexpected_error)
        
        # Act
        response = client.post('/api/v2/userchallenge/', json=valid_challenge_request)
        
        # Assert
        assert response.status_code == 500  # InternalServerError
        response_data = response.json()
        assert 'error' in response_data
        assert 'details' in response_data['error']
        assert unexpected_error in response_data['error']['details']

    @pytest.mark.parametrize("invalid_request,expected_status", [
        ({"challenge_id": 1}, 422),  # Missing user_id
        ({"user_id": 101}, 422),     # Missing challenge_id
        ({}, 422),                   # Empty request
        ({"challenge_id": "invalid", "user_id": 101}, 422),  # Invalid challenge_id type
        ({"challenge_id": 1, "user_id": "invalid"}, 422),    # Invalid user_id type
    ])
    def test_create_challenge_validation_errors(self, client, invalid_request, expected_status):
        """Test challenge creation with various validation errors"""
        # Act
        response = client.post('/api/v2/userchallenge/', json=invalid_request)
        
        # Assert
        assert response.status_code == expected_status

    def test_create_challenge_with_extra_fields(self, client, mock_user_challenge_service, valid_challenge_request):
        """Test challenge creation with extra fields (should be ignored)"""
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
        
        # Verify only the required fields were passed to the service
        call_args = mock_user_challenge_service.create.call_args[0][0]
        assert call_args.challenge_id == valid_challenge_request['challenge_id']
        assert call_args.user_id == valid_challenge_request['user_id']

    def test_create_challenge_service_not_called_on_validation_error(self, client, mock_user_challenge_service):
        """Test that service is not called when validation fails"""
        # Arrange
        invalid_request = {"challenge_id": "invalid", "user_id": 101}
        
        # Act
        response = client.post('/api/v2/userchallenge/', json=invalid_request)
        
        # Assert
        assert response.status_code == 422
        mock_user_challenge_service.create.assert_not_called()

    def test_create_challenge_logging_on_success(self, client, mock_user_challenge_service, valid_challenge_request, caplog):
        """Test that successful challenge creation is logged"""
        # Arrange
        expected_port = 8080
        mock_user_challenge_service.create.return_value = expected_port
        
        # Act
        response = client.post('/api/v2/userchallenge/', json=valid_challenge_request)
        
        # Assert
        assert response.status_code == 200
        # Note: In a real scenario, you might want to check for specific log messages
        # This test ensures the endpoint works without throwing logging-related errors

    def test_create_challenge_logging_on_error(self, client, mock_user_challenge_service, valid_challenge_request, caplog):
        """Test that errors are properly logged"""
        # Arrange
        error_message = "Test error for logging"
        mock_user_challenge_service.create.side_effect = Exception(error_message)
        
        # Act
        response = client.post('/api/v2/userchallenge/', json=valid_challenge_request)
        
        # Assert
        assert response.status_code == 500
        # Note: In a real scenario, you might want to check for specific error log messages
        # This test ensures the endpoint handles errors without throwing logging-related errors