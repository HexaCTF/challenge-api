"""
Status Repository Tests - Simplified
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError

from challenge_api.app.repository import StatusRepository
from challenge_api.app.model import UserChallengeStatus
from challenge_api.app.schema import StatusData
from challenge_api.app.common.exceptions import InvalidInputValue, StatusRepositoryException

from .conftest import (
    mock_session, status_repo, mock_status, valid_create_status_kwargs,
    valid_update_status_kwargs, valid_status_id, valid_userchallenge_idx,
    assert_session_calls, setup_mock_session_for_query, setup_mock_session_for_error,
    setup_mock_for_create_with_flush
)


# Repository Initialization Tests
def test_init(mock_session):
    """Test repository initialization"""
    repo = StatusRepository(mock_session)
    assert repo.session == mock_session


# Create Method Tests
def test_create_success(status_repo, mock_session, valid_create_status_kwargs):
    """Test successful status creation"""
    # Arrange
    mock_status_instance = MagicMock()
    mock_status_instance.idx = None  # Will be set by flush
    mock_status_instance.user_challenge_idx = 100
    mock_status_instance.status = 'Running'
    mock_status_instance.port = 8080
    
    # Mock flush to set the idx
    def mock_flush():
        mock_status_instance.idx = 1
    mock_session.flush.side_effect = mock_flush
    
    with patch('challenge_api.app.repository.status.UserChallengeStatus') as mock_status_class:
        mock_status_class.return_value = mock_status_instance

        # Act
        result = status_repo.create(**valid_create_status_kwargs)

        # Assert
        assert isinstance(result, StatusData)
        assert result.idx == 1
        assert result.user_challenge_idx == 100
        assert result.status == 'Running'
        assert result.port == 8080
        
        mock_session.add.assert_called_once_with(mock_status_instance)
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_called_once()


def test_create_with_defaults(status_repo, mock_session):
    """Test status creation with default values"""
    # Arrange
    kwargs = {'user_challenge_idx': 100}
    
    mock_status_instance = MagicMock()
    mock_status_instance.idx = None  # Will be set by flush
    mock_status_instance.user_challenge_idx = 100
    mock_status_instance.status = 'None'
    mock_status_instance.port = 0
    
    # Mock flush to set the idx
    def mock_flush():
        mock_status_instance.idx = 1
    mock_session.flush.side_effect = mock_flush
    
    with patch('challenge_api.app.repository.status.UserChallengeStatus') as mock_status_class:
        mock_status_class.return_value = mock_status_instance

        # Act
        result = status_repo.create(**kwargs)

        # Assert
        assert result.status == 'None'
        assert result.port == 0


def test_create_missing_required_field(status_repo):
    """Test create with missing required field"""
    # Arrange
    kwargs = {'status': 'Running'}  # Missing user_challenge_idx

    # Act & Assert
    with pytest.raises(InvalidInputValue) as exc_info:
        status_repo.create(**kwargs)
    assert "Required field 'user_challenge_idx' is missing" in str(exc_info.value)


def test_create_database_error(status_repo, mock_session, valid_create_status_kwargs):
    """Test create when database error occurs"""
    # Arrange
    mock_session.add.side_effect = SQLAlchemyError("Database connection failed")

    # Act & Assert
    with pytest.raises(StatusRepositoryException) as exc_info:
        status_repo.create(**valid_create_status_kwargs)
    assert "Failed to create UserChallengeStatus" in str(exc_info.value)
    mock_session.rollback.assert_called_once()


# First Method Tests
def test_first_success(status_repo, mock_session, mock_status, valid_userchallenge_idx):
    """Test successful status retrieval"""
    # Arrange
    setup_mock_session_for_query(mock_session, mock_status)

    # Act
    result = status_repo.first(valid_userchallenge_idx)

    # Assert
    assert isinstance(result, StatusData)
    assert result.idx == 1
    assert result.user_challenge_idx == 100
    assert result.status == "Running"
    assert result.port == 8080
    
    assert_session_calls(mock_session, execute_called=True)


def test_first_not_found(status_repo, mock_session, valid_userchallenge_idx):
    """Test first when status doesn't exist"""
    # Arrange
    setup_mock_session_for_query(mock_session, None)

    # Act & Assert
    with pytest.raises(StatusRepositoryException) as exc_info:
        status_repo.first(valid_userchallenge_idx)
    assert f"No status found for userchallenge_idx {valid_userchallenge_idx}" in str(exc_info.value)


def test_first_database_error(status_repo, mock_session, valid_userchallenge_idx):
    """Test first when database error occurs"""
    # Arrange
    setup_mock_session_for_error(mock_session)

    # Act & Assert
    with pytest.raises(StatusRepositoryException) as exc_info:
        status_repo.first(valid_userchallenge_idx)
    assert f"Failed to get first status for userchallenge_idx {valid_userchallenge_idx}" in str(exc_info.value)


# Update Method Tests
def test_update_success(status_repo, mock_session, mock_status, valid_update_status_kwargs):
    """Test successful status update"""
    # Arrange
    setup_mock_session_for_query(mock_session, mock_status)

    # Act
    result = status_repo.update(**valid_update_status_kwargs)

    # Assert
    assert isinstance(result, StatusData)
    assert result.idx == 1
    assert result.user_challenge_idx == 100
    assert result.status == "Stopped"
    assert result.port == 9090
    
    mock_session.commit.assert_called_once()


def test_update_status_only(status_repo, mock_session, mock_status):
    """Test update with status only"""
    # Arrange
    kwargs = {
        'user_challenge_idx': 100,
        'status': 'Stopped'
    }
    setup_mock_session_for_query(mock_session, mock_status)

    # Act
    result = status_repo.update(**kwargs)

    # Assert
    assert result.status == "Stopped"
    # Port should remain unchanged
    assert result.port == 8080


def test_update_port_only(status_repo, mock_session, mock_status):
    """Test update with port only"""
    # Arrange
    kwargs = {
        'user_challenge_idx': 100,
        'port': 9090
    }
    setup_mock_session_for_query(mock_session, mock_status)

    # Act
    result = status_repo.update(**kwargs)

    # Assert
    assert result.port == 9090
    # Status should remain unchanged
    assert result.status == "Running"


def test_update_missing_required_field(status_repo):
    """Test update with missing required field"""
    # Arrange
    kwargs = {'status': 'Stopped'}  # Missing user_challenge_idx

    # Act & Assert
    with pytest.raises(InvalidInputValue) as exc_info:
        status_repo.update(**kwargs)
    assert "Required field 'user_challenge_idx' is missing" in str(exc_info.value)


def test_update_not_found(status_repo, mock_session):
    """Test update when status doesn't exist"""
    # Arrange
    kwargs = {'user_challenge_idx': 100, 'status': 'Stopped'}
    setup_mock_session_for_query(mock_session, None)

    # Act & Assert
    with pytest.raises(StatusRepositoryException) as exc_info:
        status_repo.update(**kwargs)
    assert "No status found for userchallenge_idx 100" in str(exc_info.value)


def test_update_database_error(status_repo, mock_session, valid_update_status_kwargs):
    """Test update when database error occurs"""
    # Arrange
    setup_mock_session_for_error(mock_session)

    # Act & Assert
    with pytest.raises(StatusRepositoryException) as exc_info:
        status_repo.update(**valid_update_status_kwargs)
    assert "Failed to update UserChallengeStatus" in str(exc_info.value)
    mock_session.rollback.assert_called_once()


# GetById Method Tests
def test_get_by_id_success(status_repo, mock_session, mock_status, valid_status_id):
    """Test successful status retrieval by ID"""
    # Arrange
    setup_mock_session_for_query(mock_session, mock_status)

    # Act
    result = status_repo.get_by_id(valid_status_id)

    # Assert
    assert isinstance(result, StatusData)
    assert result.idx == 1
    assert result.user_challenge_idx == 100
    assert result.status == "Running"
    assert result.port == 8080
    
    assert_session_calls(mock_session, execute_called=True)


def test_get_by_id_not_found(status_repo, mock_session, valid_status_id):
    """Test get_by_id when status doesn't exist"""
    # Arrange
    setup_mock_session_for_query(mock_session, None)

    # Act & Assert
    with pytest.raises(StatusRepositoryException) as exc_info:
        status_repo.get_by_id(valid_status_id)
    assert f"No status found for idx {valid_status_id}" in str(exc_info.value)


def test_get_by_id_database_error(status_repo, mock_session, valid_status_id):
    """Test get_by_id when database error occurs"""
    # Arrange
    setup_mock_session_for_error(mock_session)

    # Act & Assert
    with pytest.raises(StatusRepositoryException) as exc_info:
        status_repo.get_by_id(valid_status_id)
    assert f"Failed to get status by id {valid_status_id}" in str(exc_info.value)


# Edge Cases
def test_create_with_large_userchallenge_idx(status_repo, mock_session):
    """Test create with a very large user_challenge_idx"""
    # Arrange
    large_idx = 999999999
    kwargs = {'user_challenge_idx': large_idx}
    
    mock_status_instance = MagicMock()
    mock_status_instance.idx = None  # Will be set by flush
    mock_status_instance.user_challenge_idx = large_idx
    mock_status_instance.status = 'None'
    mock_status_instance.port = 0
    
    # Mock flush to set the idx
    def mock_flush():
        mock_status_instance.idx = 1
    mock_session.flush.side_effect = mock_flush
    
    with patch('challenge_api.app.repository.status.UserChallengeStatus') as mock_status_class:
        mock_status_class.return_value = mock_status_instance

        # Act
        result = status_repo.create(**kwargs)

        # Assert
        assert result.user_challenge_idx == large_idx


def test_update_with_invalid_fields(status_repo, mock_session, mock_status):
    """Test update with invalid fields (should be ignored)"""
    # Arrange
    kwargs = {
        'user_challenge_idx': 100,
        'status': 'Stopped',
        'invalid_field': 'should_be_ignored'
    }
    setup_mock_session_for_query(mock_session, mock_status)

    # Act
    result = status_repo.update(**kwargs)

    # Assert
    assert result.status == "Stopped"
    # Invalid field should not affect the result


def test_multiple_query_operations_same_session(status_repo, mock_session, mock_status):
    """Test multiple query operations using the same session"""
    # Arrange
    setup_mock_session_for_query(mock_session, mock_status)
    
    # Test query operations (these don't need the UserChallengeStatus patch)
    result1 = status_repo.first(100)
    result2 = status_repo.get_by_id(1)

    # Assert
    assert result1 is not None
    assert result2 is not None
    assert mock_session.execute.call_count == 2  # first() and get_by_id()





def test_create_with_zero_port(status_repo, mock_session):
    """Test create with zero port value"""
    # Arrange
    kwargs = {'user_challenge_idx': 100, 'port': 0}
    
    mock_status_instance = MagicMock()
    mock_status_instance.idx = None  # Will be set by flush
    mock_status_instance.user_challenge_idx = 100
    mock_status_instance.status = 'None'
    mock_status_instance.port = 0
    
    # Mock flush to set the idx
    def mock_flush():
        mock_status_instance.idx = 1
    mock_session.flush.side_effect = mock_flush
    
    with patch('challenge_api.app.repository.status.UserChallengeStatus') as mock_status_class:
        mock_status_class.return_value = mock_status_instance

        # Act
        result = status_repo.create(**kwargs)

        # Assert
        assert result.port == 0


def test_update_with_none_values(status_repo, mock_session, mock_status):
    """Test update with None values"""
    # Arrange
    kwargs = {
        'user_challenge_idx': 100,
        'status': None,
        'port': None
    }
    setup_mock_session_for_query(mock_session, mock_status)

    # Act
    result = status_repo.update(**kwargs)

    # Assert
    assert result.status == 'None'  # None 값이 들어오면 기본값 'None'으로 설정
    assert result.port == 0  # None 값이 들어오면 기본값 0으로 설정


# Integration Tests (skipped by default)
@pytest.mark.skip(reason="Requires test database setup")
def test_create_with_real_database(real_session):
    """Integration test: Test create with real database"""
    repo = StatusRepository(real_session)
    assert repo.session == real_session


@pytest.mark.skip(reason="Requires test database setup")
def test_first_with_real_database(real_session):
    """Integration test: Test first with real database"""
    repo = StatusRepository(real_session)
    assert repo.session == real_session 