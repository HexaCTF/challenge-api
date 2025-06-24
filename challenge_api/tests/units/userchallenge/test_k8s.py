import pytest
from unittest.mock import MagicMock, patch

from challenge_api.objects.challenge import ChallengeRequest
from challenge_api.userchallenge.k8s import K8sManager
from challenge_api.exceptions.service import (
    UserChallengeCreationException,
    UserChallengeDeletionException,
)
from kubernetes.client.rest import ApiException

NAMESPACE = "challenge"

class MockUserChallenge:
    def __init__(self, idx, name):
        self.idx = idx
        self.name = name

class MockStatus:
    def __init__(self, status, port=None):
        self.status = status
        self.port = port

@pytest.fixture
def mock_services():
    # ChallengeService, UserChallengeService, UserChallengeStatusService
    challenge_service = MagicMock()
    userchallenge_service = MagicMock()
    status_service = MagicMock()
    return challenge_service, userchallenge_service, status_service

@pytest.fixture
def sample_request():
    # ChallengeRequest는 실제 구현에 맞게 수정
    return ChallengeRequest(
        name="test-challenge",
        challenge_id=123,
        user_id=456
    )

@pytest.fixture
def k8s_manager(mock_services):
    with patch('kubernetes.config.load_incluster_config'), \
         patch('kubernetes.config.load_kube_config'), \
         patch('kubernetes.client.CustomObjectsApi') as mock_custom_api, \
         patch('kubernetes.client.CoreV1Api'):
        challenge_service, userchallenge_service, status_service = mock_services
        manager = K8sManager(
            challenge_service, userchallenge_service, status_service
        )
        # 실제로 사용할 mock 객체 할당
        manager.custom_api = MagicMock()
        return manager

# =============== Test Case ==================


def test_create_new_userchallenge_success(k8s_manager, mock_services, sample_request):
    """
    if userchallenge does not exist, create new one. 
    """
    challenge_service, userchallenge_service, status_service = mock_services

    userchallenge_service.get_by_name.return_value = None
    mock_userchallenge = MockUserChallenge(idx=1, name=sample_request.name)
    userchallenge_service.create.return_value = mock_userchallenge
    status_service.create.return_value = None # create new status 
    challenge_service.get_name.return_value = "test-definition"

    # Update status: Pending     
    status_service.get_first.side_effect = [None, MockStatus(status='Pending')]

    # Watch stream: Pending → Running
    mock_watch = MagicMock()
    running_event = {
        'object': {
            'status': {
                'currentStatus': {'status': 'Running'},
                'endpoint': 8080
            }
        }
    }
    with patch('kubernetes.watch.Watch', return_value=mock_watch):
        mock_watch.stream.return_value = iter([running_event])
        result = k8s_manager.create(sample_request)

    assert result == 8080
    userchallenge_service.create.assert_called_once()
    status_service.get_first.assert_called_once()
    status_service.create.assert_called_once()
    k8s_manager.custom_api.create_namespaced_custom_object.assert_called_once()

def test_create_existing_running_userchallenge(k8s_manager, mock_services, sample_request):
    """
    If userchallenge is 'Running, return port value. 
    """
    challenge_service, userchallenge_service, status_service = mock_services

    mock_userchallenge = MockUserChallenge(idx=1, name=sample_request.name)
    userchallenge_service.get_by_name.return_value = mock_userchallenge
    mock_status = MockStatus(status='Running', port=9090)
    status_service.get_first.return_value = mock_status

    result = k8s_manager.create(sample_request)
    assert result == 9090

    userchallenge_service.create.assert_not_called()
    k8s_manager.custom_api.create_namespaced_custom_object.assert_not_called()

def test_kubernetes_api_exception(k8s_manager, mock_services, sample_request):
    challenge_service, userchallenge_service, status_service = mock_services

    userchallenge_service.get_by_name.return_value = None
    mock_userchallenge = MockUserChallenge(idx=1, name=sample_request.name)
    userchallenge_service.create.return_value = mock_userchallenge
    status_service.create.return_value = None
    challenge_service.get_name.return_value = "test-definition"
    status_service.get_first.side_effect = [None, MockStatus(status='Pending')]

    # Kubernetes API에서 예외 발생
    k8s_manager.custom_api.create_namespaced_custom_object.side_effect = ApiException(status=400, reason="Bad Request")

    with pytest.raises(ApiException):
        k8s_manager.create(sample_request)

def test_watch_timeout_or_no_endpoint(k8s_manager, mock_services, sample_request):
    challenge_service, userchallenge_service, status_service = mock_services

    userchallenge_service.get_by_name.return_value = None
    mock_userchallenge = MockUserChallenge(idx=1, name=sample_request.name)
    userchallenge_service.create.return_value = mock_userchallenge
    status_service.create.return_value = None
    challenge_service.get_name.return_value = "test-definition"
    status_service.get_first.side_effect = [None, MockStatus(status='Pending')]

    # Watch stream에서 endpoint를 얻지 못함
    mock_watch = MagicMock()
    only_pending_event = {
        'object': {
            'status': {
                'currentStatus': {'status': 'Pending'}
                # Endpoint does not exist
            }
        }
    }
    with patch('kubernetes.watch.Watch', return_value=mock_watch):
        mock_watch.stream.return_value = iter([only_pending_event])
        with pytest.raises(UserChallengeCreationException):
            k8s_manager.create(sample_request)

def test_challenge_manifest_structure(k8s_manager, mock_services, sample_request):
    challenge_service, userchallenge_service, status_service = mock_services

    userchallenge_service.get_by_name.return_value = None
    mock_userchallenge = MockUserChallenge(idx=1, name=sample_request.name)
    userchallenge_service.create.return_value = mock_userchallenge
    status_service.create.return_value = None
    challenge_service.get_name.return_value = "test-definition"
    status_service.get_first.side_effect = [None, MockStatus(status='Pending')]

    # Watch stream: Running 이벤트 발생
    mock_watch = MagicMock()
    running_event = {
        'object': {
            'status': {
                'currentStatus': {'status': 'Running'},
                'endpoint': 12345
            }
        }
    }
    with patch('kubernetes.watch.Watch', return_value=mock_watch):
        mock_watch.stream.return_value = iter([running_event])
        k8s_manager.create(sample_request)

    # 매니페스트 구조 검증
    call_args = k8s_manager.custom_api.create_namespaced_custom_object.call_args
    manifest = call_args[1]['body']
    assert manifest['apiVersion'] == "apps.hexactf.io/v2alpha1"
    assert manifest['kind'] == "Challenge"
    assert manifest['metadata']['name'] == sample_request.name
    assert manifest['metadata']['labels']['apps.hexactf.io/challengeId'] == str(sample_request.challenge_id)
    assert manifest['metadata']['labels']['apps.hexactf.io/userId'] == str(sample_request.user_id)
    assert manifest['spec']['namespace'] == NAMESPACE
    assert manifest['spec']['definition'] == "test-definition"

# delete
def test_delete_success(
    k8s_manager,
    mock_services,
    sample_request
):
    # Given 
    _, userchallenge_svc, _ = mock_services
    
    userchallenge_svc.get_by_name.return_value = MockUserChallenge(
        idx=1, name=sample_request.name
        )
    
    k8s_manager.custom_api.delete_namespaced_custom_object.return_value = {
        'status':'Success'
    }
    
    # When
    k8s_manager.delete(sample_request)
    
    # Then 
    userchallenge_svc.get_by_name.assert_called_once_with(
        name=sample_request.name
    )
    k8s_manager.custom_api.delete_namespaced_custom_object.assert_called_once_with(
                group="apps.hexactf.io",
                version="v2alpha1",
                namespace="challenge",
                plural="challenges",
                name=sample_request.name
            )

def test_delete_userchallenge_not_found(
    k8s_manager,
    mock_services,
    sample_request
):
    # Given
    _, userchallenge_svc, _ = mock_services
        
    userchallenge_svc.get_by_name.return_value = None
    
    # When
    with pytest.raises(UserChallengeDeletionException) as exc_info:
        k8s_manager.delete(sample_request)
    
    # Then
    assert "Deletion : UserChallenge not found: challenge-123-456" in str(exc_info.value)
    
    # UserChallenge 조회까지는 호출되었는지 확인
    userchallenge_svc.get_by_name.assert_called_once_with(
        name=sample_request.name
    )
    
    # Kubernetes API는 호출되지 않았는지 확인
    k8s_manager.custom_api.delete_namespaced_custom_object.assert_not_called()

def test_delete_k8s_resource_not_found_handled_gracefully(
    k8s_manager,
    mock_services,
    sample_request
):
    # Given
    _, userchallenge_svc, _ = mock_services
    
    mock_user_challenge = MockUserChallenge(idx=1, name="challenge-123-456")
    userchallenge_svc.get_by_name.return_value = mock_user_challenge
    
    api_error = ApiException(status=404, reason='Not Found')
    k8s_manager.custom_api.delete_namespaced_custom_object.side_effect = api_error
    
    # When
    with pytest.raises(ApiException) as exc_info:
        k8s_manager.delete(sample_request)
    
    # Then
    assert exc_info.value.status == 404
    assert "Not Found" in str(exc_info.value)
    
    k8s_manager.custom_api.delete_namespaced_custom_object.assert_called_once()
    
