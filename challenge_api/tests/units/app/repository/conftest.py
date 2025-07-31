"""
Common fixtures and utilities for repository tests
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from challenge_api.app.model.model import Challenges, UserChallenges, UserChallengeStatus
from challenge_api.app.repository.challenge import ChallengeRepository
from challenge_api.app.repository.userchallenge import UserChallengesRepository
from challenge_api.app.repository.status import UserChallengeStatusRepository
from challenge_api.app.common.exceptions import (
    RepositoryException, 
    ChallengeRepositoryException, 
    UserChallengeRepositoryException, 
    StatusRepositoryException,
    InvalidInputValue
)


# ============================================================================
# Session Fixtures
# ============================================================================

@pytest.fixture
def mock_session():
    """Create a mock database session"""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.flush = MagicMock()
    session.execute = MagicMock()
    session.close = MagicMock()
    return session


@pytest.fixture
def real_session():
    """Create a real database session for integration tests"""
    # This would be configured with a test database
    # For now, return None to indicate it's not implemented
    return None


# ============================================================================
# Mock Object Factory
# ============================================================================

class MockObjectFactory:
    """Factory for creating mock objects"""
    
    @staticmethod
    def create_mock_challenge():
        """Create a mock Challenge object"""
        challenge = MagicMock(spec=Challenges)
        challenge.idx = 1
        challenge.title = "Test Challenge"
        challenge.description = "Test challenge description"
        challenge.currentStatus = True
        challenge.createdAt = datetime.now()
        challenge.updatedAt = datetime.now()
        return challenge
    
    @staticmethod
    def create_mock_userchallenge():
        """Create a mock UserChallenges object"""
        userchallenge = MagicMock(spec=UserChallenges)
        userchallenge.idx = 1
        userchallenge.user_idx = 100
        userchallenge.C_idx = 200
        userchallenge.userChallengeName = "test-challenge"
        userchallenge.createdAt = datetime.now()
        userchallenge.updatedAt = datetime.now()
        return userchallenge
    
    @staticmethod
    def create_mock_status():
        """Create a mock UserChallengeStatus object"""
        status = MagicMock(spec=UserChallengeStatus)
        status.idx = 1
        status.user_challenge_idx = 100
        status.status = "Running"
        status.port = 8080
        status.createdAt = datetime.now()
        status.updatedAt = datetime.now()
        return status
    
    @staticmethod
    def create_mock_challenge_repo():
        """Create a mock ChallengeRepository"""
        return MagicMock(spec=ChallengeRepository)


# ============================================================================
# Repository Fixtures
# ============================================================================

@pytest.fixture
def challenge_repo(mock_session):
    """Create a ChallengeRepository instance with mock session"""
    return ChallengeRepository(session=mock_session)


@pytest.fixture
def userchallenge_repo(mock_session):
    """Create a UserChallengesRepository instance with mock session"""
    mock_challenge_repo = MockObjectFactory.create_mock_challenge_repo()
    return UserChallengesRepository(session=mock_session, challenge_repo=mock_challenge_repo)


@pytest.fixture
def userchallenge_repo_no_challenge(mock_session):
    """Create a UserChallengesRepository instance without challenge repo"""
    return UserChallengesRepository(session=mock_session)


@pytest.fixture
def status_repo(mock_session):
    """Create a UserChallengeStatusRepository instance with mock session"""
    return UserChallengeStatusRepository(session=mock_session)


# ============================================================================
# Mock Object Fixtures
# ============================================================================

@pytest.fixture
def mock_challenge():
    """Create a mock Challenge object"""
    return MockObjectFactory.create_mock_challenge()


@pytest.fixture
def mock_userchallenge():
    """Create a mock UserChallenges object"""
    return MockObjectFactory.create_mock_userchallenge()


@pytest.fixture
def mock_status():
    """Create a mock UserChallengeStatus object"""
    return MockObjectFactory.create_mock_status()


@pytest.fixture
def mock_challenge_repo():
    """Create a mock ChallengeRepository"""
    return MockObjectFactory.create_mock_challenge_repo()


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def valid_challenge_id():
    """Valid challenge ID for testing"""
    return 1


@pytest.fixture
def valid_userchallenge_id():
    """Valid userchallenge ID for testing"""
    return 1


@pytest.fixture
def valid_status_id():
    """Valid status ID for testing"""
    return 1


@pytest.fixture
def valid_userchallenge_idx():
    """Valid user challenge index for testing"""
    return 100


@pytest.fixture
def invalid_ids():
    """Invalid IDs for testing"""
    return [0, -1, None]


@pytest.fixture
def valid_create_challenge_kwargs():
    """Valid kwargs for challenge create method"""
    return {
        'title': 'Test Challenge',
        'description': 'Test challenge description'
    }


@pytest.fixture
def valid_create_userchallenge_kwargs():
    """Valid kwargs for userchallenge create method"""
    return {
        'user_idx': 100,
        'C_idx': 200,
        'userChallengeName': 'test-challenge'
    }


@pytest.fixture
def valid_create_status_kwargs():
    """Valid kwargs for status create method"""
    return {
        'user_challenge_idx': 100,
        'status': 'Running',
        'port': 8080
    }


@pytest.fixture
def valid_update_userchallenge_kwargs():
    """Valid kwargs for userchallenge update method"""
    return {
        'userChallengeName': 'updated-challenge'
    }


@pytest.fixture
def valid_update_status_kwargs():
    """Valid kwargs for status update method"""
    return {
        'user_challenge_idx': 100,
        'status': 'Stopped',
        'port': 9090
    }


# ============================================================================
# Helper Functions
# ============================================================================

def assert_session_calls(mock_session, add_called=False, commit_called=False, 
                        flush_called=False, execute_called=False, rollback_called=False):
    """Assert that session methods were called as expected"""
    if add_called:
        mock_session.add.assert_called_once()
    if commit_called:
        mock_session.commit.assert_called_once()
    if flush_called:
        mock_session.flush.assert_called_once()
    if execute_called:
        mock_session.execute.assert_called_once()
    if rollback_called:
        mock_session.rollback.assert_called_once()


def assert_session_execute_conditions(mock_session, expected_conditions):
    """Assert that session.execute was called with expected conditions"""
    mock_session.execute.assert_called_once()
    call_args = mock_session.execute.call_args[0][0]
    assert call_args is not None
    
    call_args_str = str(call_args)
    for condition in expected_conditions:
        assert condition in call_args_str


def create_mock_flush_effect(mock_instance, idx_value=1):
    """Create a mock flush effect that sets the idx attribute"""
    def mock_flush():
        mock_instance.idx = idx_value
    return mock_flush


def setup_mock_session_for_create(mock_session, mock_instance, idx_value=1):
    """Setup mock session for create operations"""
    def mock_flush():
        mock_instance.idx = idx_value
    mock_session.flush.side_effect = mock_flush


def setup_mock_session_for_query(mock_session, return_value):
    """Setup mock session for query operations"""
    mock_session.execute.return_value.scalar_one_or_none.return_value = return_value


def setup_mock_session_for_error(mock_session, error_type=SQLAlchemyError, error_message="Database connection failed"):
    """Setup mock session to raise an error"""
    mock_session.execute.side_effect = error_type(error_message)


# ============================================================================
# Test Pattern Functions
# ============================================================================

def test_get_by_id_success_pattern(repo, mock_session, mock_obj, obj_id, model_class, repo_name):
    """Common pattern for testing successful get_by_id operations"""
    # Arrange
    setup_mock_session_for_query(mock_session, mock_obj)
    
    # Act
    result = repo.get_by_id(obj_id)
    
    # Assert
    assert result == mock_obj
    assert_session_calls(mock_session, execute_called=True)
    assert_session_execute_conditions(mock_session, [f"{model_class.__name__}.idx == {obj_id}"])


def test_get_by_id_not_found_pattern(repo, mock_session, obj_id):
    """Common pattern for testing get_by_id when object doesn't exist"""
    # Arrange
    setup_mock_session_for_query(mock_session, None)
    
    # Act
    result = repo.get_by_id(obj_id)
    
    # Assert
    assert result is None
    assert_session_calls(mock_session, execute_called=True)


def test_get_by_id_database_error_pattern(repo, mock_session, obj_id, exception_class, repo_name):
    """Common pattern for testing get_by_id database errors"""
    # Arrange
    setup_mock_session_for_error(mock_session)
    
    # Act & Assert
    with pytest.raises(exception_class) as exc_info:
        repo.get_by_id(obj_id)
    assert f"Failed to get {repo_name} by id" in str(exc_info.value)


def test_create_database_error_pattern(repo, mock_session, create_kwargs, exception_class, repo_name):
    """Common pattern for testing create database errors"""
    # Arrange
    mock_session.add.side_effect = SQLAlchemyError("Database connection failed")
    
    # Act & Assert
    with pytest.raises(exception_class) as exc_info:
        repo.create(**create_kwargs)
    assert f"Failed to create {repo_name}" in str(exc_info.value)
    assert_session_calls(mock_session, rollback_called=True)


def test_update_database_error_pattern(repo, mock_session, update_kwargs, exception_class, repo_name):
    """Common pattern for testing update database errors"""
    # Arrange
    setup_mock_session_for_error(mock_session)
    
    # Act & Assert
    with pytest.raises(exception_class) as exc_info:
        repo.update(**update_kwargs)
    assert f"Failed to update {repo_name}" in str(exc_info.value)
    assert_session_calls(mock_session, rollback_called=True)


# ============================================================================
# Edge Case Test Functions
# ============================================================================

def test_with_large_id_pattern(repo, mock_session, mock_obj, large_id, method_name):
    """Common pattern for testing with very large IDs"""
    # Arrange
    setup_mock_session_for_query(mock_session, mock_obj)
    
    # Act
    if method_name == "get_by_id":
        result = repo.get_by_id(large_id)
    elif method_name == "exists":
        result = repo.exists(large_id)
    else:
        raise ValueError(f"Unknown method: {method_name}")
    
    # Assert
    assert result is not None
    assert_session_calls(mock_session, execute_called=True)


def test_multiple_operations_same_session_pattern(repo, mock_session, mock_obj, test_data):
    """Common pattern for testing multiple operations using the same session"""
    # Arrange
    setup_mock_session_for_query(mock_session, mock_obj)
    
    # Act
    results = []
    for operation in test_data:
        if operation['method'] == 'get_by_id':
            result = repo.get_by_id(operation['args'])
        elif operation['method'] == 'get':
            result = repo.get(**operation['args'])
        elif operation['method'] == 'exists':
            result = repo.exists(operation['args'])
        else:
            raise ValueError(f"Unknown operation: {operation['method']}")
        results.append(result)
    
    # Assert
    for result in results:
        assert result is not None
    assert mock_session.execute.call_count == len(test_data)


# ============================================================================
# Integration Test Helpers
# ============================================================================

def skip_if_no_real_session(real_session):
    """Skip test if real session is not available"""
    if real_session is None:
        pytest.skip("Real database session not configured")


def create_integration_test_repo(repo_class, real_session, **kwargs):
    """Create a repository instance for integration tests"""
    skip_if_no_real_session(real_session)
    return repo_class(real_session, **kwargs)


# ============================================================================
# Validation Helper Functions
# ============================================================================

def assert_repository_initialization(repo_class, mock_session, **kwargs):
    """Assert that repository is properly initialized"""
    repo = repo_class(mock_session, **kwargs)
    assert repo.session == mock_session
    for key, value in kwargs.items():
        assert getattr(repo, key) == value
    return repo


def assert_invalid_input_exception(func, *args, **kwargs):
    """Assert that InvalidInputValue exception is raised"""
    with pytest.raises(InvalidInputValue) as exc_info:
        func(*args, **kwargs)
    return exc_info.value


def assert_repository_exception(func, exception_class, *args, **kwargs):
    """Assert that repository exception is raised"""
    with pytest.raises(exception_class) as exc_info:
        func(*args, **kwargs)
    return exc_info.value


# ============================================================================
# Mock Setup Helpers
# ============================================================================

def setup_mock_for_create_with_flush(mock_session, mock_class_path, mock_instance, idx_value=1):
    """Setup mock for create operations that need flush to set idx"""
    with patch(mock_class_path) as mock_class:
        mock_class.return_value = mock_instance
        setup_mock_session_for_create(mock_session, mock_instance, idx_value)
        return mock_class


def setup_mock_challenge_validation(mock_challenge_repo, mock_challenge):
    """Setup mock challenge validation"""
    mock_challenge_repo.get_by_id.return_value = mock_challenge


def setup_mock_challenge_validation_failure(mock_challenge_repo, challenge_id):
    """Setup mock challenge validation failure"""
    mock_challenge_repo.get_by_id.return_value = None 