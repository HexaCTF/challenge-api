"""
Challenge Repository Tests - Simplified
"""

import pytest
from sqlalchemy.exc import SQLAlchemyError

from challenge_api.app.repository.challenge import ChallengeRepository
from challenge_api.app.model.model import Challenges
from challenge_api.app.common.exceptions import RepositoryException, ChallengeRepositoryException

from .conftest import (
    mock_session, challenge_repo, mock_challenge, valid_challenge_id,
    assert_session_calls, setup_mock_session_for_query, setup_mock_session_for_error
)


# Repository Initialization Tests
def test_init(mock_session):
    """Test repository initialization"""
    repo = ChallengeRepository(mock_session)
    assert repo.session == mock_session


# GetById Method Tests
def test_get_by_id_success(challenge_repo, mock_session, mock_challenge, valid_challenge_id):
    """Test successful challenge retrieval by ID"""
    # Arrange
    setup_mock_session_for_query(mock_session, mock_challenge)

    # Act
    result = challenge_repo.get_by_id(valid_challenge_id)

    # Assert
    assert result == mock_challenge
    assert_session_calls(mock_session, execute_called=True)


def test_get_by_id_not_found(challenge_repo, mock_session, valid_challenge_id):
    """Test challenge retrieval when challenge doesn't exist"""
    # Arrange
    setup_mock_session_for_query(mock_session, None)

    # Act
    result = challenge_repo.get_by_id(valid_challenge_id)

    # Assert
    assert result is None
    assert_session_calls(mock_session, execute_called=True)


@pytest.mark.parametrize("invalid_id", [0, -1, None])
def test_get_by_id_invalid_id(challenge_repo, invalid_id):
    """Test get_by_id with invalid IDs"""
    with pytest.raises(ChallengeRepositoryException) as exc_info:
        challenge_repo.get_by_id(invalid_id)
    assert f"Invalid challenge_id: {invalid_id} provided" in str(exc_info.value)


def test_get_by_id_database_error(challenge_repo, mock_session, valid_challenge_id):
    """Test get_by_id when database error occurs"""
    # Arrange
    setup_mock_session_for_error(mock_session)

    # Act & Assert
    with pytest.raises(RepositoryException) as exc_info:
        challenge_repo.get_by_id(valid_challenge_id)
    assert "Failed to get challenge by id" in str(exc_info.value)


# GetNameById Method Tests
def test_get_name_by_id_success(challenge_repo, mock_session, mock_challenge, valid_challenge_id):
    """Test successful name retrieval by ID"""
    # Arrange
    setup_mock_session_for_query(mock_session, mock_challenge)

    # Act
    result = challenge_repo.get_name_by_id(valid_challenge_id)

    # Assert
    assert result == "Test Challenge"
    assert_session_calls(mock_session, execute_called=True)


def test_get_name_by_id_not_found(challenge_repo, mock_session, valid_challenge_id):
    """Test name retrieval when challenge doesn't exist"""
    # Arrange
    setup_mock_session_for_query(mock_session, None)

    # Act
    result = challenge_repo.get_name_by_id(valid_challenge_id)

    # Assert
    assert result is None
    assert_session_calls(mock_session, execute_called=True)


@pytest.mark.parametrize("invalid_id", [0, -1, None])
def test_get_name_by_id_invalid_id(challenge_repo, invalid_id):
    """Test get_name_by_id with invalid IDs"""
    with pytest.raises(ChallengeRepositoryException) as exc_info:
        challenge_repo.get_name_by_id(invalid_id)
    assert f"Invalid challenge_id: {invalid_id} provided" in str(exc_info.value)


def test_get_name_by_id_database_error(challenge_repo, mock_session, valid_challenge_id):
    """Test get_name_by_id when database error occurs"""
    # Arrange
    setup_mock_session_for_error(mock_session)

    # Act & Assert
    with pytest.raises(RepositoryException) as exc_info:
        challenge_repo.get_name_by_id(valid_challenge_id)
    assert "Failed to get challenge name" in str(exc_info.value)


def test_get_name_by_id_challenge_without_title(challenge_repo, mock_session, valid_challenge_id):
    """Test get_name_by_id when challenge has no title"""
    # Arrange
    from .conftest import MockObjectFactory
    mock_challenge = MockObjectFactory.create_mock_challenge()
    mock_challenge.title = None
    setup_mock_session_for_query(mock_session, mock_challenge)

    # Act
    result = challenge_repo.get_name_by_id(valid_challenge_id)

    # Assert
    assert result is None


# Exists Method Tests
def test_exists_true(challenge_repo, mock_session, mock_challenge, valid_challenge_id):
    """Test exists when challenge exists"""
    # Arrange
    setup_mock_session_for_query(mock_session, mock_challenge)

    # Act
    result = challenge_repo.exists(valid_challenge_id)

    # Assert
    assert result is True
    assert_session_calls(mock_session, execute_called=True)


def test_exists_false(challenge_repo, mock_session, valid_challenge_id):
    """Test exists when challenge doesn't exist"""
    # Arrange
    setup_mock_session_for_query(mock_session, None)

    # Act
    result = challenge_repo.exists(valid_challenge_id)

    # Assert
    assert result is False
    assert_session_calls(mock_session, execute_called=True)


@pytest.mark.parametrize("invalid_id", [0, -1, None])
def test_exists_invalid_id(challenge_repo, invalid_id):
    """Test exists with invalid IDs"""
    with pytest.raises(ChallengeRepositoryException) as exc_info:
        challenge_repo.exists(invalid_id)
    assert f"Invalid challenge_id: {invalid_id} provided" in str(exc_info.value)


def test_exists_database_error(challenge_repo, mock_session, valid_challenge_id):
    """Test exists when database error occurs"""
    # Arrange
    setup_mock_session_for_error(mock_session)

    # Act & Assert
    with pytest.raises(RepositoryException) as exc_info:
        challenge_repo.exists(valid_challenge_id)
    assert "Failed to check challenge existence" in str(exc_info.value)


# Edge Cases
def test_get_by_id_with_large_id(challenge_repo, mock_session, mock_challenge):
    """Test get_by_id with very large ID"""
    # Arrange
    large_id = 999999999
    setup_mock_session_for_query(mock_session, mock_challenge)

    # Act
    result = challenge_repo.get_by_id(large_id)

    # Assert
    assert result == mock_challenge
    assert_session_calls(mock_session, execute_called=True)


def test_get_name_by_id_with_large_id(challenge_repo, mock_session, mock_challenge):
    """Test get_name_by_id with very large ID"""
    # Arrange
    large_id = 999999999
    setup_mock_session_for_query(mock_session, mock_challenge)

    # Act
    result = challenge_repo.get_name_by_id(large_id)

    # Assert
    assert result == "Test Challenge"
    assert_session_calls(mock_session, execute_called=True)


def test_exists_with_large_id(challenge_repo, mock_session):
    """Test exists with very large ID"""
    # Arrange
    large_id = 999999999
    setup_mock_session_for_query(mock_session, None)

    # Act
    result = challenge_repo.exists(large_id)

    # Assert
    assert result is False
    assert_session_calls(mock_session, execute_called=True)


def test_multiple_calls_same_session(challenge_repo, mock_session, mock_challenge, valid_challenge_id):
    """Test multiple calls using the same session"""
    # Arrange
    setup_mock_session_for_query(mock_session, mock_challenge)

    # Act
    result1 = challenge_repo.get_by_id(valid_challenge_id)
    result2 = challenge_repo.get_name_by_id(valid_challenge_id)
    result3 = challenge_repo.exists(valid_challenge_id)

    # Assert
    assert result1 == mock_challenge
    assert result2 == "Test Challenge"
    assert result3 is True
    assert mock_session.execute.call_count == 3


# Integration Tests (skipped by default)
@pytest.mark.skip(reason="Requires test database setup")
def test_get_by_id_with_real_database(real_session):
    """Integration test: Test get_by_id with real database"""
    repo = ChallengeRepository(real_session)
    assert repo.session == real_session


@pytest.mark.skip(reason="Requires test database setup")
def test_exists_with_real_database(real_session):
    """Integration test: Test exists with real database"""
    repo = ChallengeRepository(real_session)
    assert repo.session == real_session 