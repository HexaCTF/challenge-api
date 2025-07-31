import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime

from challenge_api.app.service.userchallenge import UserChallengeService
from challenge_api.app.schema import ChallengeRequest, StatusData, K8sChallengeData
from challenge_api.app.common.exceptions import (
    UserChallengeCreationException,
    UserChallengeDeletionException,
    UserChallengeNotFound,
    InvalidInputValue
)

# Service를 구성하는 의존성 객체 생성 
@pytest.fixture
def mock_user_challenge_repo():
    return MagicMock()

@pytest.fixture
def mock_challenge_repo():
    return MagicMock()

@pytest.fixture
def mock_status_repo():
    return MagicMock()

@pytest.fixture
def mock_k8s_manager():
    return MagicMock()

@pytest.fixture
def user_challenge_service(mock_user_challenge_repo, mock_challenge_repo, mock_status_repo, mock_k8s_manager):
    """mock 객체를 사용하여 UserChallengeService 인스턴스 생성"""
    return UserChallengeService(
        user_challenge_repo=mock_user_challenge_repo,
        challenge_repo=mock_challenge_repo,
        status_repo=mock_status_repo,
        k8s_manager=mock_k8s_manager
    )

@pytest.fixture
def sample_challenge_request():
    """테스트용 ChallengeRequest 생성"""
    return ChallengeRequest(challenge_id=1, user_id=101)


@pytest.fixture
def mock_user_challenge():
    """실제 문자열 값을 가진 UserChallenge 객체 생성"""
    mock = MagicMock()
    mock.idx = 1001
    mock.user_idx = 101
    mock.C_idx = 1
    mock.userChallengeName = "challenge-1-101"  # Actual string value
    return mock

@pytest.fixture
def mock_status_data():
    """실제 문자열 값을 가진 StatusData 객체 생성"""
    mock = MagicMock()
    mock.user_challenge_idx = 1001
    mock.status = "None"
    mock.port = 0
    return mock


@pytest.fixture
def mock_running_status_data():
    """실제 문자열 값을 가진 Running StatusData 객체 생성"""
    mock = MagicMock()
    mock.user_challenge_idx = 1001
    mock.status = "Running"
    mock.port = 8080
    return mock


def test_create_new_challenge_success(
    user_challenge_service, 
    sample_challenge_request, 
    mock_user_challenge, 
    mock_status_data
):
    """챌린지 생성 성공 시 할당된 포트 반환 """
    # Arrange
    expected_port = 8080
    
    # 존재하지 않는 챌린지 조회
    user_challenge_service.user_challenge_repo.get.return_value = None
    
    # 새로운 챌린지 생성
    user_challenge_service.user_challenge_repo.create.return_value = mock_user_challenge
    
    # 초기 상태 생성
    user_challenge_service.status_repo.create.return_value = mock_status_data
    
    # 챌린지 정의 조회
    user_challenge_service.challenge_repo.get_name.return_value = "test-definition"
    
    # 사용자 챌린지 조회
    user_challenge_service.user_challenge_repo.get_by_id.return_value = mock_user_challenge
    
    # K8s 매니저 생성
    user_challenge_service.k8s_manager.create.return_value = expected_port

    # 상태 업데이트
    user_challenge_service.status_repo.update.return_value = None
    
    # Act
    result = user_challenge_service.create(sample_challenge_request)
    
    # Assert
    assert result == expected_port
    
    # 저장소 호출 확인
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

def test_create_existing_running_challenge(
    user_challenge_service, 
    sample_challenge_request, 
    mock_user_challenge, 
    mock_running_status_data
):
    """실행 중인 챌린지 생성 시 테스트"""
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

def test_create_existing_stopped_challenge(
    user_challenge_service, 
    sample_challenge_request, 
    mock_user_challenge, 
    mock_status_data
):
    """중지된 챌린지 재시작 시 테스트"""
    # Arrange
    expected_port = 8080
    
    # 존재하는 사용자 챌린지 조회
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

def test_create_existing_challenge_no_status(
    user_challenge_service, 
    sample_challenge_request, 
    mock_user_challenge
):
    """상태가 없는 챌린지 생성 시 테스트"""
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

def test_create_k8s_manager_failure(
    user_challenge_service, 
    sample_challenge_request, 
    mock_user_challenge, 
    mock_status_data
):
    """K8s 매니저 실패 시 테스트"""
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

def test_create_invalid_endpoint_from_k8s(
    user_challenge_service, 
    sample_challenge_request, 
    mock_user_challenge, 
    mock_status_data
):
    """K8s 매니저에서 유효하지 않은 엔드포인트 발생 시 테스트"""
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

def test_create_user_challenge_not_found(
    user_challenge_service, 
    sample_challenge_request, 
    mock_status_data
):
    """UserChallenge 조회 실패 시 테스트"""
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

def test_create_challenge_definition_not_found(
    user_challenge_service, 
    sample_challenge_request, 
    mock_user_challenge, 
    mock_status_data
):
    """챌린지 정의 조회 실패 시 테스트"""
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

def test_create_status_update_failure(
    user_challenge_service, 
    sample_challenge_request, 
    mock_user_challenge, 
    mock_status_data
):
    """상태 업데이트 실패 시 테스트"""
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

def test_create_general_exception(
    user_challenge_service, 
    sample_challenge_request
):
    """일반적인 예외 발생 시 테스트"""
    # Arrange
    # Mock repository failure
    user_challenge_service.user_challenge_repo.get.side_effect = Exception("Database error")
    
    # Act & Assert
    with pytest.raises(UserChallengeCreationException) as exc_info:
        user_challenge_service.create(sample_challenge_request)
    
    assert "Failed to create challenge for user" in str(exc_info.value)


def test_get_existing_user_challenge_found(
    user_challenge_service, 
    sample_challenge_request, 
    mock_user_challenge, 
    mock_status_data
):
    """챌린지 존재 시 _get_existing_user_challenge 테스트"""
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

def test_get_existing_user_challenge_not_found(
    user_challenge_service, 
    sample_challenge_request
):
    """챌린지 존재하지 않을 때 _get_existing_user_challenge 테스트"""
    # Arrange
    user_challenge_service.user_challenge_repo.get.return_value = None
    
    # Act
    result = user_challenge_service._get_existing_user_challenge(sample_challenge_request)
    
    # Assert
    assert result is None

def test_get_existing_user_challenge_no_status(
    user_challenge_service, 
    sample_challenge_request, 
    mock_user_challenge
):
    """챌린지 존재 시 상태가 없을 때 _get_existing_user_challenge 테스트"""
    # Arrange
    user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
    user_challenge_service.status_repo.first.side_effect = Exception("Status not found")
    
    # Act
    result = user_challenge_service._get_existing_user_challenge(sample_challenge_request)
    
    # Assert
    assert result is None

def test_handle_existing_challenge_running(
    user_challenge_service, 
    mock_running_status_data
):
    """실행 중인 챌린지 존재 시 _handle_existing_challenge 테스트"""
    # Act
    result = user_challenge_service._handle_existing_challenge(mock_running_status_data)
    
    # Assert
    assert result == 8080

def test_handle_existing_challenge_stopped(
    user_challenge_service, 
    mock_status_data, 
    mock_user_challenge
):
    """중지된 챌린지 존재 시 _handle_existing_challenge 테스트"""
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

def test_create_k8s_challenge_success(
    user_challenge_service, 
    mock_status_data, 
    mock_user_challenge
):
    """K8s 챌린지 생성 성공 시 테스트"""
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


# Delete 함수 테스트들
def test_delete_challenge_success(
    user_challenge_service, 
    sample_challenge_request, 
    mock_user_challenge, 
    mock_status_data
):
    """챌린지 삭제 성공 시 테스트"""
    # Arrange
    # Mock existing user challenge with proper idx
    mock_user_challenge.idx = 1001
    user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
    
    # Mock existing status with proper user_challenge_idx
    mock_status_data.user_challenge_idx = 1001
    user_challenge_service.status_repo.first.return_value = mock_status_data
    
    # Mock successful deletion operations
    user_challenge_service.user_challenge_repo.delete.return_value = None
    user_challenge_service.k8s_manager.delete.return_value = None
    user_challenge_service.status_repo.update.return_value = None
    
    # Act
    user_challenge_service.delete(sample_challenge_request)
    
    # Assert
    # Verify user challenge was deleted
    user_challenge_service.user_challenge_repo.delete.assert_called_once_with(1001)
    
    # Verify K8s resources were deleted
    user_challenge_service.k8s_manager.delete.assert_called_once_with(1001)
    
    # Verify status was updated to Deleted
    user_challenge_service.status_repo.update.assert_called_once_with(
        user_challenge_idx=1001,
        status='Deleted',
        port=0
    )


def test_delete_challenge_not_found(
    user_challenge_service, 
    sample_challenge_request
):
    """존재하지 않는 챌린지 삭제 시 테스트"""
    # Arrange
    # Mock no existing challenge
    user_challenge_service.user_challenge_repo.get.return_value = None
    
    # Act & Assert
    with pytest.raises(UserChallengeDeletionException) as exc_info:
        user_challenge_service.delete(sample_challenge_request)
    
    assert "Failed to delete challenge for user" in str(exc_info.value)
    assert "No existing challenge found for user" in str(exc_info.value)
    
    # Verify no deletion operations were performed
    user_challenge_service.user_challenge_repo.delete.assert_not_called()
    user_challenge_service.k8s_manager.delete.assert_not_called()
    user_challenge_service.status_repo.update.assert_not_called()


def test_delete_challenge_no_status(
    user_challenge_service, 
    sample_challenge_request, 
    mock_user_challenge
):
    """상태가 없는 챌린지 삭제 시 테스트"""
    # Arrange
    # Mock existing user challenge
    user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
    
    # Mock no status (exception)
    user_challenge_service.status_repo.first.side_effect = Exception("Status not found")
    
    # Act & Assert
    with pytest.raises(UserChallengeDeletionException) as exc_info:
        user_challenge_service.delete(sample_challenge_request)
    
    assert "Failed to delete challenge for user" in str(exc_info.value)
    assert "No existing challenge found for user" in str(exc_info.value)


def test_delete_challenge_repository_failure(
    user_challenge_service, 
    sample_challenge_request, 
    mock_user_challenge, 
    mock_status_data
):
    """저장소 삭제 실패 시 테스트"""
    # Arrange
    # Mock existing user challenge with proper idx
    mock_user_challenge.idx = 1001
    user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
    
    # Mock existing status with proper user_challenge_idx
    mock_status_data.user_challenge_idx = 1001
    user_challenge_service.status_repo.first.return_value = mock_status_data
    
    # Mock repository deletion failure
    user_challenge_service.user_challenge_repo.delete.side_effect = Exception("Database deletion failed")
    
    # Act & Assert
    with pytest.raises(UserChallengeDeletionException) as exc_info:
        user_challenge_service.delete(sample_challenge_request)
    
    assert "Failed to delete challenge for user" in str(exc_info.value)
    assert "Database deletion failed" in str(exc_info.value)


def test_delete_challenge_k8s_failure(
    user_challenge_service, 
    sample_challenge_request, 
    mock_user_challenge, 
    mock_status_data
):
    """K8s 리소스 삭제 실패 시 테스트"""
    # Arrange
    # Mock existing user challenge with proper idx
    mock_user_challenge.idx = 1001
    user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
    
    # Mock existing status with proper user_challenge_idx
    mock_status_data.user_challenge_idx = 1001
    user_challenge_service.status_repo.first.return_value = mock_status_data
    
    # Mock successful repository deletion
    user_challenge_service.user_challenge_repo.delete.return_value = None
    
    # Mock K8s deletion failure
    user_challenge_service.k8s_manager.delete.side_effect = Exception("K8s deletion failed")
    
    # Act & Assert
    with pytest.raises(UserChallengeDeletionException) as exc_info:
        user_challenge_service.delete(sample_challenge_request)
    
    assert "Failed to delete challenge for user" in str(exc_info.value)
    assert "K8s deletion failed" in str(exc_info.value)


def test_delete_challenge_status_update_failure(
    user_challenge_service, 
    sample_challenge_request, 
    mock_user_challenge, 
    mock_status_data
):
    """상태 업데이트 실패 시 테스트"""
    # Arrange
    # Mock existing user challenge with proper idx
    mock_user_challenge.idx = 1001
    user_challenge_service.user_challenge_repo.get.return_value = mock_user_challenge
    
    # Mock existing status with proper user_challenge_idx
    mock_status_data.user_challenge_idx = 1001
    user_challenge_service.status_repo.first.return_value = mock_status_data
    
    # Mock successful repository and K8s deletion
    user_challenge_service.user_challenge_repo.delete.return_value = None
    user_challenge_service.k8s_manager.delete.return_value = None
    
    # Mock status update failure
    user_challenge_service.status_repo.update.side_effect = Exception("Status update failed")
    
    # Act & Assert
    with pytest.raises(UserChallengeDeletionException) as exc_info:
        user_challenge_service.delete(sample_challenge_request)
    
    assert "Failed to delete challenge for user" in str(exc_info.value)
    assert "Status update failed" in str(exc_info.value)


def test_delete_challenge_general_exception(
    user_challenge_service, 
    sample_challenge_request
):
    """일반적인 예외 발생 시 테스트"""
    # Arrange
    # Mock repository failure during initial check
    user_challenge_service.user_challenge_repo.get.side_effect = Exception("General database error")
    
    # Act & Assert
    with pytest.raises(UserChallengeDeletionException) as exc_info:
        user_challenge_service.delete(sample_challenge_request)
    
    assert "Failed to delete challenge for user" in str(exc_info.value)
    assert "General database error" in str(exc_info.value)