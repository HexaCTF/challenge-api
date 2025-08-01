import pytest
from unittest.mock import MagicMock, patch, Mock
from kubernetes.client.rest import ApiException
from kubernetes import watch, config

from challenge_api.app.external.k8s.k8s import K8sManager
from challenge_api.app.schema import K8sChallengeData, ChallengeRequest
from challenge_api.app.common.exceptions import (
    K8sResourceException,
    UserChallengeCreationException,
    UserChallengeDeletionException
)


@pytest.fixture
def mock_k8s_config():
    """Mock Kubernetes configuration"""
    with patch('challenge_api.app.external.k8s.k8s.config') as mock_config:
        mock_config.load_incluster_config.return_value = None
        mock_config.load_kube_config.return_value = None
        yield mock_config


@pytest.fixture
def mock_k8s_client():
    """Mock Kubernetes client"""
    with patch('challenge_api.app.external.k8s.k8s.client') as mock_client:
        mock_client.CustomObjectsApi.return_value = MagicMock()
        mock_client.CoreV1Api.return_value = MagicMock()
        mock_client.V1DeleteOptions.return_value = MagicMock()
        yield mock_client


@pytest.fixture
def mock_watch():
    """Mock Kubernetes watch"""
    with patch('challenge_api.app.external.k8s.k8s.watch') as mock_watch:
        mock_watch.Watch.return_value = MagicMock()
        yield mock_watch


@pytest.fixture
def k8s_manager():
    """Create K8sManager instance with mocked dependencies"""
    with patch('challenge_api.app.external.k8s.k8s.config.load_incluster_config') as mock_incluster:
        with patch('challenge_api.app.external.k8s.k8s.config.load_kube_config') as mock_local:
            with patch('challenge_api.app.external.k8s.k8s.client.CustomObjectsApi') as mock_custom_api:
                with patch('challenge_api.app.external.k8s.k8s.client.CoreV1Api') as mock_core_api:
                    # Mock successful initialization
                    mock_incluster.return_value = None
                    mock_custom_api.return_value = MagicMock()
                    mock_core_api.return_value = MagicMock()
                    
                    manager = K8sManager()
                    
                    # Mock the connection test
                    manager.core_api.get_api_version.return_value = None
                    
                    return manager


@pytest.fixture
def sample_k8s_challenge_data():
    """Sample K8sChallengeData for testing"""
    return K8sChallengeData(
        challenge_id=1,
        user_id=101,
        userchallenge_name="challenge-1-101",
        definition="test-definition"
    )


@pytest.fixture
def sample_challenge_request():
    """Sample ChallengeRequest for testing"""
    return ChallengeRequest(challenge_id=1, user_id=101)


class TestK8sManagerInitialization:
    """Test K8sManager initialization"""

    def test_initialization_success_incluster(self):
        """Test successful initialization with in-cluster config"""
        # Arrange
        with patch('challenge_api.app.external.k8s.k8s.config.load_incluster_config') as mock_incluster:
            with patch('challenge_api.app.external.k8s.k8s.config.load_kube_config') as mock_local:
                with patch('challenge_api.app.external.k8s.k8s.client.CustomObjectsApi') as mock_custom_api:
                    with patch('challenge_api.app.external.k8s.k8s.client.CoreV1Api') as mock_core_api:
                        # Mock successful in-cluster config
                        mock_incluster.return_value = None
                        mock_local.side_effect = config.ConfigException("ConfigException")
                        mock_custom_api.return_value = MagicMock()
                        mock_core_api.return_value = MagicMock()
                        
                        # Act
                        manager = K8sManager()
                        
                        # Assert
                        assert manager.custom_api is not None
                        assert manager.core_api is not None
                        mock_incluster.assert_called_once()

    def test_initialization_success_local_config(self):
        """Test successful initialization with local config"""
        # Arrange
        with patch('challenge_api.app.external.k8s.k8s.config.load_incluster_config') as mock_incluster:
            with patch('challenge_api.app.external.k8s.k8s.config.load_kube_config') as mock_local:
                with patch('challenge_api.app.external.k8s.k8s.client.CustomObjectsApi') as mock_custom_api:
                    with patch('challenge_api.app.external.k8s.k8s.client.CoreV1Api') as mock_core_api:
                        # Mock successful local config
                        mock_incluster.side_effect = config.ConfigException("ConfigException")
                        mock_local.return_value = None
                        mock_custom_api.return_value = MagicMock()
                        mock_core_api.return_value = MagicMock()
                        
                        # Act
                        manager = K8sManager()
                        
                        # Assert
                        assert manager.custom_api is not None
                        assert manager.core_api is not None
                        mock_local.assert_called_once()

    def test_initialization_failure(self):
        """Test initialization failure"""
        # Arrange
        with patch('challenge_api.app.external.k8s.k8s.config.load_incluster_config') as mock_incluster:
            with patch('challenge_api.app.external.k8s.k8s.config.load_kube_config') as mock_local:
                # Mock both configs failing
                mock_incluster.side_effect = Exception("Connection failed")
                mock_local.side_effect = Exception("Config failed")
                
                # Act & Assert
                with pytest.raises(K8sResourceException) as exc_info:
                    K8sManager()
                
                assert "K8s initialization failed" in str(exc_info.value)

    def test_cluster_connection_failure(self):
        """Test cluster connection failure"""
        # Arrange
        with patch('challenge_api.app.external.k8s.k8s.config.load_incluster_config') as mock_incluster:
            with patch('challenge_api.app.external.k8s.k8s.client.CoreV1Api') as mock_core_api:
                # Mock successful config but failed connection
                mock_incluster.return_value = None
                mock_core_instance = MagicMock()
                mock_core_instance.get_api_version.side_effect = Exception("Connection failed")
                mock_core_api.return_value = mock_core_instance
                
                # Act & Assert
                with pytest.raises(K8sResourceException) as exc_info:
                    K8sManager()
                
                assert "Cannot connect to K8s cluster" in str(exc_info.value)


class TestK8sManagerCreate:
    """Test K8sManager create method"""

    def test_create_challenge_success(self, k8s_manager, sample_k8s_challenge_data):
        """Test successful challenge creation"""
        # Arrange
        expected_endpoint = 8080
        
        # Mock resource creation
        k8s_manager.custom_api.create_namespaced_custom_object.return_value = {'metadata': {'name': 'test'}}
        
        # Mock the watch stream to return a successful event
        with patch('challenge_api.app.external.k8s.k8s.watch.Watch') as mock_watch_class:
            mock_watch_instance = MagicMock()
            mock_watch_class.return_value = mock_watch_instance
            
            mock_watch_instance.stream.return_value = [
                {
                    'type': 'MODIFIED',
                    'object': {
                        'status': {
                            'currentStatus': {'status': 'Running'},
                            'endpoint': expected_endpoint
                        }
                    }
                }
            ]
            
            # Act
            result = k8s_manager.create(sample_k8s_challenge_data)
            
            # Assert
            assert result == expected_endpoint
            k8s_manager.custom_api.create_namespaced_custom_object.assert_called_once()
            # stop() is called twice: once in the logic and once in finally block
            assert mock_watch_instance.stop.call_count == 2

    def test_create_challenge_existing_resource_cleanup(self, k8s_manager, sample_k8s_challenge_data):
        """Test challenge creation with existing resource cleanup"""
        # Arrange
        expected_endpoint = 8080
        
        # Mock existing resource found
        k8s_manager.custom_api.get_namespaced_custom_object.return_value = {'metadata': {'name': 'existing'}}
        k8s_manager.custom_api.delete_namespaced_custom_object.return_value = None
        
        # Mock successful creation after cleanup
        with patch('challenge_api.app.external.k8s.k8s.watch.Watch') as mock_watch_class:
            mock_watch_instance = MagicMock()
            mock_watch_class.return_value = mock_watch_instance
            
            mock_watch_instance.stream.return_value = [
                {
                    'type': 'MODIFIED',
                    'object': {
                        'status': {
                            'currentStatus': {'status': 'Running'},
                            'endpoint': expected_endpoint
                        }
                    }
                }
            ]
            
            # Act
            result = k8s_manager.create(sample_k8s_challenge_data)
            
            # Assert
            assert result == expected_endpoint
            k8s_manager.custom_api.get_namespaced_custom_object.assert_called_once()
            k8s_manager.custom_api.delete_namespaced_custom_object.assert_called_once()

    def test_create_challenge_api_exception(self, k8s_manager, sample_k8s_challenge_data):
        """Test challenge creation with API exception"""
        # Arrange
        api_exception = ApiException(status=500, reason="Internal Server Error")
        k8s_manager.custom_api.create_namespaced_custom_object.side_effect = api_exception
        
        # Act & Assert
        with pytest.raises(UserChallengeCreationException) as exc_info:
            k8s_manager.create(sample_k8s_challenge_data)
        
        assert "K8s API error" in str(exc_info.value)

    def test_create_challenge_timeout(self, k8s_manager, sample_k8s_challenge_data):
        """Test challenge creation timeout"""
        # Arrange
        with patch('challenge_api.app.external.k8s.k8s.watch.Watch') as mock_watch_class:
            mock_watch_instance = MagicMock()
            mock_watch_class.return_value = mock_watch_instance
            
            # Mock watch stream to return events that don't indicate readiness
            mock_watch_instance.stream.return_value = [
                {
                    'type': 'MODIFIED',
                    'object': {
                        'status': {
                            'currentStatus': {'status': 'Pending'}
                        }
                    }
                }
            ]
            
            # Act & Assert
            with pytest.raises(UserChallengeCreationException) as exc_info:
                k8s_manager.create(sample_k8s_challenge_data, timeout=1)
            
            assert "did not become ready within" in str(exc_info.value)

    def test_create_challenge_failed_status(self, k8s_manager, sample_k8s_challenge_data):
        """Test challenge creation with failed status"""
        # Arrange
        with patch('challenge_api.app.external.k8s.k8s.watch.Watch') as mock_watch_class:
            mock_watch_instance = MagicMock()
            mock_watch_class.return_value = mock_watch_instance
            
            # Mock watch stream to return failed status
            mock_watch_instance.stream.return_value = [
                {
                    'type': 'MODIFIED',
                    'object': {
                        'status': {
                            'currentStatus': {
                                'status': 'Failed',
                                'message': 'Challenge failed to start'
                            }
                        }
                    }
                }
            ]
            
            # Act & Assert
            with pytest.raises(UserChallengeCreationException) as exc_info:
                k8s_manager.create(sample_k8s_challenge_data)
            
            assert "Challenge failed" in str(exc_info.value)

    def test_create_challenge_deleted_event(self, k8s_manager, sample_k8s_challenge_data):
        """Test challenge creation with unexpected deletion"""
        # Arrange
        with patch('challenge_api.app.external.k8s.k8s.watch.Watch') as mock_watch_class:
            mock_watch_instance = MagicMock()
            mock_watch_class.return_value = mock_watch_instance
            
            # Mock watch stream to return deletion event
            mock_watch_instance.stream.return_value = [
                {
                    'type': 'DELETED',
                    'object': {'metadata': {'name': 'test'}}
                }
            ]
            
            # Act & Assert
            with pytest.raises(UserChallengeCreationException) as exc_info:
                k8s_manager.create(sample_k8s_challenge_data)
            
            assert "was deleted unexpectedly" in str(exc_info.value)


class TestK8sManagerDelete:
    """Test K8sManager delete method"""

    def test_delete_challenge_success(self, k8s_manager, sample_challenge_request):
        """Test successful challenge deletion"""
        # Arrange
        k8s_manager.custom_api.get_namespaced_custom_object.return_value = {'metadata': {'name': 'test'}}
        k8s_manager.custom_api.delete_namespaced_custom_object.return_value = None
        
        # Mock _wait_for_deletion to avoid actual waiting
        with patch.object(k8s_manager, '_wait_for_deletion') as mock_wait:
            # Act
            result = k8s_manager.delete(sample_challenge_request)
            
            # Assert
            assert result is True
            k8s_manager.custom_api.get_namespaced_custom_object.assert_called_once()
            k8s_manager.custom_api.delete_namespaced_custom_object.assert_called_once()
            mock_wait.assert_called_once()

    def test_delete_challenge_not_found(self, k8s_manager, sample_challenge_request):
        """Test challenge deletion when resource not found"""
        # Arrange
        api_exception = ApiException(status=404, reason="Not Found")
        k8s_manager.custom_api.get_namespaced_custom_object.side_effect = api_exception
        
        # Act
        result = k8s_manager.delete(sample_challenge_request)
        
        # Assert
        assert result is True  # Should return True when resource doesn't exist

    def test_delete_challenge_api_exception(self, k8s_manager, sample_challenge_request):
        """Test challenge deletion with API exception"""
        # Arrange
        api_exception = ApiException(status=500, reason="Internal Server Error")
        k8s_manager.custom_api.delete_namespaced_custom_object.side_effect = api_exception
        
        # Mock resource exists
        k8s_manager.custom_api.get_namespaced_custom_object.return_value = {'metadata': {'name': 'test'}}
        
        # Act & Assert
        with pytest.raises(UserChallengeDeletionException) as exc_info:
            k8s_manager.delete(sample_challenge_request)
        
        assert "K8s API error" in str(exc_info.value)


class TestK8sManagerGetStatus:
    """Test K8sManager get_challenge_status method"""

    def test_get_challenge_status_success(self, k8s_manager):
        """Test successful status retrieval"""
        # Arrange
        mock_resource = {
            'status': {
                'currentStatus': {
                    'status': 'Running',
                    'message': 'All good',
                    'lastTransitionTime': '2024-01-01T00:00:00Z'
                },
                'endpoint': 8080
            }
        }
        k8s_manager.custom_api.get_namespaced_custom_object.return_value = mock_resource
        
        # Act
        result = k8s_manager.get_challenge_status("test-challenge")
        
        # Assert
        assert result is not None
        assert result['status'] == 'Running'
        assert result['endpoint'] == 8080
        assert result['message'] == 'All good'

    def test_get_challenge_status_not_found(self, k8s_manager):
        """Test status retrieval when resource not found"""
        # Arrange
        api_exception = ApiException(status=404, reason="Not Found")
        k8s_manager.custom_api.get_namespaced_custom_object.side_effect = api_exception
        
        # Act
        result = k8s_manager.get_challenge_status("test-challenge")
        
        # Assert
        assert result is None

    def test_get_challenge_status_api_exception(self, k8s_manager):
        """Test status retrieval with API exception"""
        # Arrange
        api_exception = ApiException(status=500, reason="Internal Server Error")
        k8s_manager.custom_api.get_namespaced_custom_object.side_effect = api_exception
        
        # Act
        result = k8s_manager.get_challenge_status("test-challenge")
        
        # Assert
        assert result is None


class TestK8sManagerListChallenges:
    """Test K8sManager list_challenges method"""

    def test_list_challenges_success(self, k8s_manager):
        """Test successful challenge listing"""
        # Arrange
        mock_resources = {
            'items': [
                {
                    'metadata': {
                        'name': 'challenge-1',
                        'labels': {
                            'apps.hexactf.io/challengeId': '1',
                            'apps.hexactf.io/userId': '101'
                        },
                        'creationTimestamp': '2024-01-01T00:00:00Z'
                    },
                    'status': {
                        'currentStatus': {'status': 'Running'},
                        'endpoint': 8080
                    }
                }
            ]
        }
        k8s_manager.custom_api.list_namespaced_custom_object.return_value = mock_resources
        
        # Act
        result = k8s_manager.list_challenges()
        
        # Assert
        assert len(result) == 1
        assert result[0]['name'] == 'challenge-1'
        assert result[0]['status'] == 'Running'
        assert result[0]['endpoint'] == 8080

    def test_list_challenges_empty(self, k8s_manager):
        """Test challenge listing when no challenges exist"""
        # Arrange
        k8s_manager.custom_api.list_namespaced_custom_object.return_value = {'items': []}
        
        # Act
        result = k8s_manager.list_challenges()
        
        # Assert
        assert len(result) == 0

    def test_list_challenges_exception(self, k8s_manager):
        """Test challenge listing with exception"""
        # Arrange
        k8s_manager.custom_api.list_namespaced_custom_object.side_effect = Exception("API Error")
        
        # Act
        result = k8s_manager.list_challenges()
        
        # Assert
        assert result == []


class TestK8sManagerCleanup:
    """Test K8sManager cleanup_failed_challenges method"""

    def test_cleanup_failed_challenges_success(self, k8s_manager):
        """Test successful cleanup of failed challenges"""
        # Arrange
        mock_challenges = [
            {
                'name': 'failed-challenge',
                'status': 'Failed'
            },
            {
                'name': 'running-challenge',
                'status': 'Running'
            }
        ]
        
        # Mock list_challenges to return failed challenges
        k8s_manager.list_challenges = MagicMock(return_value=mock_challenges)
        k8s_manager.custom_api.delete_namespaced_custom_object.return_value = None
        
        # Act
        result = k8s_manager.cleanup_failed_challenges()
        
        # Assert
        assert result == 1  # Only one failed challenge should be cleaned up
        k8s_manager.custom_api.delete_namespaced_custom_object.assert_called_once()

    def test_cleanup_failed_challenges_no_failed(self, k8s_manager):
        """Test cleanup when no failed challenges exist"""
        # Arrange
        mock_challenges = [
            {
                'name': 'running-challenge',
                'status': 'Running'
            }
        ]
        
        k8s_manager.list_challenges = MagicMock(return_value=mock_challenges)
        
        # Act
        result = k8s_manager.cleanup_failed_challenges()
        
        # Assert
        assert result == 0
        k8s_manager.custom_api.delete_namespaced_custom_object.assert_not_called()

    def test_cleanup_failed_challenges_exception(self, k8s_manager):
        """Test cleanup with exception"""
        # Arrange
        k8s_manager.list_challenges = MagicMock(side_effect=Exception("API Error"))
        
        # Act
        result = k8s_manager.cleanup_failed_challenges()
        
        # Assert
        assert result == 0


class TestK8sManagerManifestBuilding:
    """Test K8sManager manifest building functionality"""

    def test_build_challenge_manifest(self, k8s_manager, sample_k8s_challenge_data):
        """Test challenge manifest building"""
        # Arrange & Act
        manifest = k8s_manager._build_challenge_manifest(sample_k8s_challenge_data)
        
        # Assert
        assert manifest['apiVersion'] == 'apps.hexactf.io/v2alpha1'
        assert manifest['kind'] == 'Challenge'
        assert manifest['metadata']['name'] == sample_k8s_challenge_data.userchallenge_name
        assert manifest['metadata']['namespace'] == 'challenge'
        assert manifest['spec']['challengeId'] == sample_k8s_challenge_data.challenge_id
        assert manifest['spec']['userId'] == sample_k8s_challenge_data.user_id
        assert manifest['spec']['definition'] == sample_k8s_challenge_data.definition

    def test_build_challenge_manifest_with_labels(self, k8s_manager, sample_k8s_challenge_data):
        """Test challenge manifest building with proper labels"""
        # Arrange & Act
        manifest = k8s_manager._build_challenge_manifest(sample_k8s_challenge_data)
        
        # Assert
        labels = manifest['metadata']['labels']
        assert labels['apps.hexactf.io/challengeId'] == str(sample_k8s_challenge_data.challenge_id)
        assert labels['apps.hexactf.io/userId'] == str(sample_k8s_challenge_data.user_id)
        assert labels['apps.hexactf.io/managed-by'] == 'challenge-api' 