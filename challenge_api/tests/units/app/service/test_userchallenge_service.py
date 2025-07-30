import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime

from challenge_api.app.service.userchallenge import UserChallengeService
from challenge_api.app.schema import ChallengeRequest, StatusData, K8sChallengeData
from challenge_api.app.common.exceptions import (
    UserChallengeCreationException,
    InvalidInputValue
)


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


class TestUserChallengeServiceCreate:
    """Test UserChallengeService create method"""

    def test_create_new_challenge_success(self, user_challenge_service, sample_challenge_request, 
                                         mock_user_challenge, mock_status_data):
        """Test successful creation of new challenge"""
        # Arrange
        expected_port = 8080
        
        # Mock no existing challenge
        user_challenge_service.user_challenge_repo.get.return_value = None
        
        # Mock new user challenge creation
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        
        # Mock initial status creation
        user_challenge_service.status_repo.create.return_value = mock_status_data
        
        # Mock challenge definition - return actual string
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        
        # Mock get_by_id to return proper user challenge object
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        
        # Mock K8s manager
        user_challenge_service.k8s_manager.create.return_value = expected_port
        
        # Mock status update
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        result = user_challenge_service.create(sample_challenge_request)
        
        # Assert
        assert result == expected_port
        
        # Verify repository calls
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
        user_challenge_service.status_repo.update.assert_called_once_with(
            userchallenge_idx=mock_status_data.user_challenge_idx,
            status='Running',
            port=expected_port
        )

    def test_create_existing_running_challenge(self, user_challenge_service, sample_challenge_request, 
                                              mock_user_challenge, mock_running_status_data):
        """Test handling of existing running challenge"""
        # Arrange
        expected_port = 8080
        
        # Mock existing user challenge
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        
        # Mock existing running status
        user_challenge_service.status_repo.first.return_value = mock_running_status_data
        
        # Act
        result = user_challenge_service.create(sample_challenge_request)
        
        # Assert
        assert result == expected_port
        
        # Verify no new resources were created
        user_challenge_service.user_challenge_repo.create.assert_not_called()
        user_challenge_service.k8s_manager.create.assert_not_called()

    def test_create_existing_stopped_challenge(self, user_challenge_service, sample_challenge_request, 
                                              mock_user_challenge, mock_status_data):
        """Test restarting existing stopped challenge"""
        # Arrange
        expected_port = 8080
        
        # Mock existing user challenge
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        
        # Mock existing stopped status
        user_challenge_service.status_repo.first.return_value = mock_status_data
        
        # Mock challenge definition - return actual string
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        
        # Mock get_by_id to return proper user challenge object
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        
        # Mock K8s manager
        user_challenge_service.k8s_manager.create.return_value = expected_port
        
        # Mock status update
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        result = user_challenge_service.create(sample_challenge_request)
        
        # Assert
        assert result == expected_port
        
        # Verify K8s challenge was created
        user_challenge_service.k8s_manager.create.assert_called_once()
        user_challenge_service.status_repo.update.assert_called_once_with(
            userchallenge_idx=mock_status_data.user_challenge_idx,
            status='Running',
            port=expected_port
        )

    def test_create_existing_challenge_no_status(self, user_challenge_service, sample_challenge_request, 
                                                mock_user_challenge):
        """Test handling of existing challenge with no status"""
        # Arrange
        expected_port = 8080
        
        # Mock existing user challenge
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        
        # Mock no status (exception or None)
        user_challenge_service.status_repo.first.side_effect = Exception("Status not found")
        
        # Mock challenge definition - return actual string
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        
        # Mock get_by_id to return proper user challenge object
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        
        # Mock K8s manager
        user_challenge_service.k8s_manager.create.return_value = expected_port
        
        # Mock status update
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        result = user_challenge_service.create(sample_challenge_request)
        
        # Assert
        assert result == expected_port
        
        # Verify new status was created
        user_challenge_service.status_repo.create.assert_called_once()

    def test_create_k8s_manager_failure(self, user_challenge_service, sample_challenge_request, 
                                       mock_user_challenge, mock_status_data):
        """Test handling of K8s manager failure"""
        # Arrange
        # Mock no existing challenge
        user_challenge_service.user_challenge_repo.get.return_value = None
        
        # Mock new user challenge creation
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        
        # Mock initial status creation
        user_challenge_service.status_repo.create.return_value = mock_status_data
        
        # Mock challenge definition - return actual string
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        
        # Mock get_by_id to return proper user challenge object
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        
        # Mock K8s manager failure
        user_challenge_service.k8s_manager.create.side_effect = Exception("K8s creation failed")
        
        # Mock status update to Error
        user_challenge_service.status_repo.update.return_value = None
        
        # Act & Assert
        with pytest.raises(UserChallengeCreationException) as exc_info:
            user_challenge_service.create(sample_challenge_request)
        
        assert "Failed to start challenge" in str(exc_info.value)
        
        # Verify status was updated to Error
        user_challenge_service.status_repo.update.assert_called_with(
            userchallenge_idx=mock_status_data.user_challenge_idx,
            status='Error',
            port=0
        )

    def test_create_invalid_endpoint_from_k8s(self, user_challenge_service, sample_challenge_request, 
                                             mock_user_challenge, mock_status_data):
        """Test handling of invalid endpoint from K8s manager"""
        # Arrange
        # Mock no existing challenge
        user_challenge_service.user_challenge_repo.get.return_value = None
        
        # Mock new user challenge creation
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        
        # Mock initial status creation
        user_challenge_service.status_repo.create.return_value = mock_status_data
        
        # Mock challenge definition - return actual string
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        
        # Mock get_by_id to return proper user challenge object
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        
        # Mock K8s manager returning invalid endpoint
        user_challenge_service.k8s_manager.create.return_value = 0
        
        # Mock status update to Error
        user_challenge_service.status_repo.update.return_value = None
        
        # Act & Assert
        with pytest.raises(UserChallengeCreationException) as exc_info:
            user_challenge_service.create(sample_challenge_request)
        
        assert "Invalid endpoint received from K8s manager" in str(exc_info.value)

    def test_create_user_challenge_not_found(self, user_challenge_service, sample_challenge_request, 
                                            mock_status_data):
        """Test handling when UserChallenge is not found during K8s creation"""
        # Arrange
        # Mock no existing challenge
        user_challenge_service.user_challenge_repo.get.return_value = None
        
        # Mock new user challenge creation
        mock_user_challenge = MagicMock()
        mock_user_challenge.idx = 1001
        mock_user_challenge.user_idx = 101
        mock_user_challenge.C_idx = 1
        mock_user_challenge.userChallengeName = "challenge-1-101"  # Actual string
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        
        # Mock initial status creation
        user_challenge_service.status_repo.create.return_value = mock_status_data
        
        # Mock challenge definition - return actual string
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        
        # Mock UserChallenge not found during K8s creation
        user_challenge_service.user_challenge_repo.get_by_id.return_value = None
        
        # Mock status update to Error
        user_challenge_service.status_repo.update.return_value = None
        
        # Act & Assert
        with pytest.raises(UserChallengeCreationException) as exc_info:
            user_challenge_service.create(sample_challenge_request)
        
        assert "UserChallenge not found" in str(exc_info.value)

    def test_create_challenge_definition_not_found(self, user_challenge_service, sample_challenge_request, 
                                                  mock_user_challenge, mock_status_data):
        """Test handling when challenge definition is not found"""
        # Arrange
        # Mock no existing challenge
        user_challenge_service.user_challenge_repo.get.return_value = None
        
        # Mock new user challenge creation
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        
        # Mock initial status creation
        user_challenge_service.status_repo.create.return_value = mock_status_data
        
        # Mock challenge definition not found
        user_challenge_service.challenge_repo.get_name.return_value = None
        
        # Mock get_by_id to return proper user challenge object
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        
        # Mock status update to Error
        user_challenge_service.status_repo.update.return_value = None
        
        # Act & Assert
        with pytest.raises(UserChallengeCreationException) as exc_info:
            user_challenge_service.create(sample_challenge_request)
        
        assert "Challenge definition not found" in str(exc_info.value)

    def test_create_status_update_failure(self, user_challenge_service, sample_challenge_request, 
                                         mock_user_challenge, mock_status_data):
        """Test handling when status update fails"""
        # Arrange
        # Mock no existing challenge
        user_challenge_service.user_challenge_repo.get.return_value = None
        
        # Mock new user challenge creation
        user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
        
        # Mock initial status creation
        user_challenge_service.status_repo.create.return_value = mock_status_data
        
        # Mock challenge definition - return actual string
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
        
        # Mock get_by_id to return proper user challenge object
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        
        # Mock K8s manager failure
        user_challenge_service.k8s_manager.create.side_effect = Exception("K8s creation failed")
        
        # Mock status update failure
        user_challenge_service.status_repo.update.side_effect = Exception("Status update failed")
        
        # Act & Assert
        with pytest.raises(UserChallengeCreationException) as exc_info:
            user_challenge_service.create(sample_challenge_request)
        
        assert "Failed to start challenge" in str(exc_info.value)

    def test_create_general_exception(self, user_challenge_service, sample_challenge_request):
        """Test handling of general exceptions during creation"""
        # Arrange
        # Mock repository failure
        user_challenge_service.user_challenge_repo.get.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(UserChallengeCreationException) as exc_info:
            user_challenge_service.create(sample_challenge_request)
        
        assert "Failed to create challenge for user" in str(exc_info.value)


class TestUserChallengeServiceHelperMethods:
    """Test UserChallengeService helper methods"""

    def test_get_existing_user_challenge_found(self, user_challenge_service, sample_challenge_request, 
                                               mock_user_challenge, mock_status_data):
        """Test _get_existing_user_challenge when challenge exists"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        user_challenge_service.status_repo.first.return_value = mock_status_data
        
        # Act
        result = user_challenge_service._get_existing_user_challenge(sample_challenge_request)
        
        # Assert
        assert result == mock_status_data
        user_challenge_service.user_challenge_repo.get.assert_called_once_with(
            user_idx=sample_challenge_request.user_id,
            C_idx=sample_challenge_request.challenge_id
        )

    def test_get_existing_user_challenge_not_found(self, user_challenge_service, sample_challenge_request):
        """Test _get_existing_user_challenge when challenge doesn't exist"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.return_value = None
        
        # Act
        result = user_challenge_service._get_existing_user_challenge(sample_challenge_request)
        
        # Assert
        assert result is None

    def test_get_existing_user_challenge_no_status(self, user_challenge_service, sample_challenge_request, 
                                                   mock_user_challenge):
        """Test _get_existing_user_challenge when challenge exists but no status"""
        # Arrange
        user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
        user_challenge_service.status_repo.first.side_effect = Exception("Status not found")
        
        # Act
        result = user_challenge_service._get_existing_user_challenge(sample_challenge_request)
        
        # Assert
        assert result is None

    def test_handle_existing_challenge_running(self, user_challenge_service, mock_running_status_data):
        """Test _handle_existing_challenge when challenge is already running"""
        # Act
        result = user_challenge_service._handle_existing_challenge(mock_running_status_data)
        
        # Assert
        assert result == 8080

    def test_handle_existing_challenge_stopped(self, user_challenge_service, mock_status_data, mock_user_challenge):
        """Test _handle_existing_challenge when challenge is stopped"""
        # Arrange
        expected_port = 8080
        
        # Mock the dependencies needed for _start_challenge
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"  # Actual string
        user_challenge_service.k8s_manager.create.return_value = expected_port
        user_challenge_service.status_repo.update.return_value = None
        
        # Act
        result = user_challenge_service._handle_existing_challenge(mock_status_data)
        
        # Assert
        assert result == expected_port

    def test_create_k8s_challenge_success(self, user_challenge_service, mock_status_data, mock_user_challenge):
        """Test _create_k8s_challenge success"""
        # Arrange
        expected_port = 8080
        
        user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
        user_challenge_service.challenge_repo.get_name.return_value = "test-definition"  # Actual string
        user_challenge_service.k8s_manager.create.return_value = expected_port
        
        # Act
        result = user_challenge_service._create_k8s_challenge(mock_status_data)
        
        # Assert
        assert result == expected_port
        
        # Verify K8s data was created correctly
        user_challenge_service.k8s_manager.create.assert_called_once()
        call_args = user_challenge_service.k8s_manager.create.call_args[0][0]
        assert isinstance(call_args, K8sChallengeData)
        assert call_args.challenge_id == mock_user_challenge.C_idx
        assert call_args.user_id == mock_user_challenge.user_idx
        assert call_args.userchallenge_name == mock_user_challenge.userChallengeName
        assert call_args.definition == "test-definition" 