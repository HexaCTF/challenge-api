"""
UserChallenge Repository Tests - Simplified
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError

from challenge_api.app.repository import UserChallengeRepository, ChallengeRepository
from challenge_api.app.model import UserChallenges
from challenge_api.app.common.exceptions import InvalidInputValue, UserChallengeRepositoryException

from .conftest import (
    mock_session, userchallenge_repo, userchallenge_repo_no_challenge,
    mock_userchallenge, mock_challenge, mock_challenge_repo,
    valid_create_userchallenge_kwargs, valid_update_userchallenge_kwargs,
    assert_session_calls, setup_mock_session_for_query, setup_mock_session_for_error
)


# Repository Initialization Tests
def test_init_with_challenge_repo(mock_session, mock_challenge_repo):
    """Test repository initialization with challenge repo"""
    repo = UserChallengeRepository(mock_session, mock_challenge_repo)
    assert repo.session == mock_session
    assert repo.challenge_repo == mock_challenge_repo


def test_init_without_challenge_repo(mock_session):
    """Test repository initialization without challenge repo"""
    repo = UserChallengeRepository(mock_session)
    assert repo.session == mock_session
    assert repo.challenge_repo is None


# Create Method Tests
def test_create_success(userchallenge_repo, mock_session, mock_challenge, valid_create_userchallenge_kwargs):
    """Test successful userchallenge creation"""
    # Arrange
    # Set up the challenge validation to return the mock challenge
    userchallenge_repo.challenge_repo.get_by_id.return_value = mock_challenge

    # Act
    result = userchallenge_repo.create(**valid_create_userchallenge_kwargs)

    # Assert
    assert isinstance(result, UserChallenges)
    assert result.user_idx == 100
    assert result.C_idx == 200
    assert result.userChallengeName == 'test-challenge'
    userchallenge_repo.challenge_repo.get_by_id.assert_called_once_with(200)
    assert_session_calls(mock_session, add_called=True, flush_called=True, commit_called=True)


def test_create_without_challenge_validation(userchallenge_repo_no_challenge, mock_session, valid_create_userchallenge_kwargs):
    """Test creation without challenge validation"""
    # Act
    result = userchallenge_repo_no_challenge.create(**valid_create_userchallenge_kwargs)

    # Assert
    assert isinstance(result, UserChallenges)
    assert result.user_idx == 100
    assert result.C_idx == 200
    assert result.userChallengeName == 'test-challenge'
    assert_session_calls(mock_session, add_called=True, flush_called=True, commit_called=True)


def test_create_without_challenge_id(userchallenge_repo, mock_session):
    """Test creation without challenge ID"""
    # Arrange
    kwargs = {
        'user_idx': 100,
        'userChallengeName': 'test-challenge'
    }

    # Act
    result = userchallenge_repo.create(**kwargs)

    # Assert
    assert isinstance(result, UserChallenges)
    assert result.user_idx == 100
    assert result.userChallengeName == 'test-challenge'
    # Should not call challenge validation since C_idx is not provided
    userchallenge_repo.challenge_repo.get_by_id.assert_not_called()


def test_create_invalid_challenge_id(userchallenge_repo, mock_challenge):
    """Test creation with invalid challenge ID"""
    # Arrange
    kwargs = {
        'user_idx': 100,
        'C_idx': 999,
        'userChallengeName': 'test-challenge'
    }
    # Set up the challenge validation to return None (challenge not found)
    userchallenge_repo.challenge_repo.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(InvalidInputValue) as exc_info:
        userchallenge_repo.create(**kwargs)
    assert "Challenge with id 999 not found" in str(exc_info.value)


def test_create_database_error(userchallenge_repo, mock_session, valid_create_userchallenge_kwargs):
    """Test create when database error occurs"""
    # Arrange
    # Set up challenge validation to succeed
    userchallenge_repo.challenge_repo.get_by_id.return_value = mock_challenge
    # Set up database error
    mock_session.add.side_effect = SQLAlchemyError("Database connection failed")

    # Act & Assert
    with pytest.raises(UserChallengeRepositoryException) as exc_info:
        userchallenge_repo.create(**valid_create_userchallenge_kwargs)
    assert "Failed to create UserChallenge" in str(exc_info.value)
    mock_session.rollback.assert_called_once()


# GetById Method Tests
def test_get_by_id_success(userchallenge_repo, mock_session, mock_userchallenge):
    """Test successful userchallenge retrieval by ID"""
    # Arrange
    userchallenge_id = 1
    setup_mock_session_for_query(mock_session, mock_userchallenge)

    # Act
    result = userchallenge_repo.get_by_id(userchallenge_id)

    # Assert
    assert result == mock_userchallenge
    assert_session_calls(mock_session, execute_called=True)


def test_get_by_id_not_found(userchallenge_repo, mock_session):
    """Test get_by_id when userchallenge doesn't exist"""
    # Arrange
    userchallenge_id = 1
    setup_mock_session_for_query(mock_session, None)

    # Act
    result = userchallenge_repo.get_by_id(userchallenge_id)

    # Assert
    assert result is None


def test_get_by_id_database_error(userchallenge_repo, mock_session):
    """Test get_by_id when database error occurs"""
    # Arrange
    userchallenge_id = 1
    setup_mock_session_for_error(mock_session)

    # Act & Assert
    with pytest.raises(UserChallengeRepositoryException) as exc_info:
        userchallenge_repo.get_by_id(userchallenge_id)
    assert f"Failed to get UserChallenge by id {userchallenge_id}" in str(exc_info.value)


# Get Method Tests
def test_get_success_single_condition(userchallenge_repo, mock_session, mock_userchallenge):
    """Test successful userchallenge retrieval with single condition"""
    # Arrange
    kwargs = {'user_idx': 100}
    setup_mock_session_for_query(mock_session, mock_userchallenge)

    # Act
    result = userchallenge_repo.get(**kwargs)

    # Assert
    assert result == mock_userchallenge
    assert_session_calls(mock_session, execute_called=True)


def test_get_success_multiple_conditions(userchallenge_repo, mock_session, mock_userchallenge):
    """Test successful userchallenge retrieval with multiple conditions"""
    # Arrange
    kwargs = {'user_idx': 100, 'C_idx': 200}
    setup_mock_session_for_query(mock_session, mock_userchallenge)

    # Act
    result = userchallenge_repo.get(**kwargs)

    # Assert
    assert result == mock_userchallenge
    assert_session_calls(mock_session, execute_called=True)


def test_get_not_found(userchallenge_repo, mock_session):
    """Test get when userchallenge doesn't exist"""
    # Arrange
    kwargs = {'user_idx': 100}
    setup_mock_session_for_query(mock_session, None)

    # Act
    result = userchallenge_repo.get(**kwargs)

    # Assert
    assert result is None


def test_get_database_error(userchallenge_repo, mock_session):
    """Test get when database error occurs"""
    # Arrange
    kwargs = {'user_idx': 100}
    setup_mock_session_for_error(mock_session)

    # Act & Assert
    with pytest.raises(UserChallengeRepositoryException) as exc_info:
        userchallenge_repo.get(**kwargs)
    assert "Failed to get UserChallenge with" in str(exc_info.value)


# IsExist Method Tests
def test_is_exist_true(userchallenge_repo, mock_session, mock_userchallenge):
    """Test is_exist when userchallenge exists"""
    # Arrange
    kwargs = {'user_idx': 100}
    setup_mock_session_for_query(mock_session, mock_userchallenge)

    # Act
    result = userchallenge_repo.is_exist(**kwargs)

    # Assert
    assert result is True
    assert_session_calls(mock_session, execute_called=True)


def test_is_exist_false(userchallenge_repo, mock_session):
    """Test is_exist when userchallenge doesn't exist"""
    # Arrange
    kwargs = {'user_idx': 100}
    setup_mock_session_for_query(mock_session, None)

    # Act
    result = userchallenge_repo.is_exist(**kwargs)

    # Assert
    assert result is False
    assert_session_calls(mock_session, execute_called=True)


def test_is_exist_database_error(userchallenge_repo, mock_session):
    """Test is_exist when database error occurs"""
    # Arrange
    kwargs = {'user_idx': 100}
    setup_mock_session_for_error(mock_session)

    # Act & Assert
    with pytest.raises(UserChallengeRepositoryException) as exc_info:
        userchallenge_repo.is_exist(**kwargs)
    assert "Failed to check UserChallenge existence" in str(exc_info.value)


# GetByUserAndChallenge Method Tests
def test_get_by_user_and_challenge_success(userchallenge_repo, mock_session, mock_userchallenge):
    """Test successful retrieval by user and challenge"""
    # Arrange
    user_idx = 100
    challenge_idx = 200
    setup_mock_session_for_query(mock_session, mock_userchallenge)

    # Act
    result = userchallenge_repo.get_by_user_and_challenge(user_idx, challenge_idx)

    # Assert
    assert result == mock_userchallenge
    assert_session_calls(mock_session, execute_called=True)


def test_get_by_user_and_challenge_not_found(userchallenge_repo, mock_session):
    """Test get_by_user_and_challenge when not found"""
    # Arrange
    user_idx = 100
    challenge_idx = 200
    setup_mock_session_for_query(mock_session, None)

    # Act
    result = userchallenge_repo.get_by_user_and_challenge(user_idx, challenge_idx)

    # Assert
    assert result is None


# GetByName Method Tests
def test_get_by_name_success(userchallenge_repo, mock_session, mock_userchallenge):
    """Test successful retrieval by name"""
    # Arrange
    name = "test-challenge"
    setup_mock_session_for_query(mock_session, mock_userchallenge)

    # Act
    result = userchallenge_repo.get_by_name(name)

    # Assert
    assert result == mock_userchallenge
    assert_session_calls(mock_session, execute_called=True)


def test_get_by_name_not_found(userchallenge_repo, mock_session):
    """Test get_by_name when not found"""
    # Arrange
    name = "non-existent-challenge"
    setup_mock_session_for_query(mock_session, None)

    # Act
    result = userchallenge_repo.get_by_name(name)

    # Assert
    assert result is None


# Update Method Tests
def test_update_success(userchallenge_repo, mock_session, mock_userchallenge, valid_update_userchallenge_kwargs):
    """Test successful userchallenge update"""
    # Arrange
    userchallenge_id = 1
    setup_mock_session_for_query(mock_session, mock_userchallenge)

    # Act
    result = userchallenge_repo.update(userchallenge_id, **valid_update_userchallenge_kwargs)

    # Assert
    assert result == mock_userchallenge
    assert_session_calls(mock_session, execute_called=True, commit_called=True)
    # Verify the attribute was set
    assert mock_userchallenge.userChallengeName == 'updated-challenge'


def test_update_multiple_fields(userchallenge_repo, mock_session, mock_userchallenge):
    """Test update with multiple fields"""
    # Arrange
    userchallenge_id = 1
    kwargs = {
        'userChallengeName': 'updated-challenge',
        'user_idx': 101
    }
    setup_mock_session_for_query(mock_session, mock_userchallenge)

    # Act
    result = userchallenge_repo.update(userchallenge_id, **kwargs)

    # Assert
    assert result == mock_userchallenge
    assert mock_userchallenge.userChallengeName == 'updated-challenge'
    assert mock_userchallenge.user_idx == 101


def test_update_not_found(userchallenge_repo, mock_session, valid_update_userchallenge_kwargs):
    """Test update when userchallenge doesn't exist"""
    # Arrange
    userchallenge_id = 1
    setup_mock_session_for_query(mock_session, None)

    # Act & Assert
    with pytest.raises(UserChallengeRepositoryException) as exc_info:
        userchallenge_repo.update(userchallenge_id, **valid_update_userchallenge_kwargs)
    assert f"UserChallenge with id {userchallenge_id} not found for update" in str(exc_info.value)


def test_update_invalid_field(userchallenge_repo, mock_session, mock_userchallenge):
    """Test update with invalid field (should be ignored)"""
    # Arrange
    userchallenge_id = 1
    kwargs = {
        'userChallengeName': 'updated-challenge',
        'invalid_field': 'should_be_ignored'
    }
    setup_mock_session_for_query(mock_session, mock_userchallenge)

    # Act
    result = userchallenge_repo.update(userchallenge_id, **kwargs)

    # Assert
    assert result == mock_userchallenge
    assert mock_userchallenge.userChallengeName == 'updated-challenge'
    # Invalid field should not be set
    assert not hasattr(mock_userchallenge, 'invalid_field')


def test_update_database_error(userchallenge_repo, mock_session, valid_update_userchallenge_kwargs):
    """Test update when database error occurs"""
    # Arrange
    userchallenge_id = 1
    setup_mock_session_for_error(mock_session)

    # Act & Assert
    with pytest.raises(UserChallengeRepositoryException) as exc_info:
        userchallenge_repo.update(userchallenge_id, **valid_update_userchallenge_kwargs)
    assert "Failed to update UserChallenge" in str(exc_info.value)
    mock_session.rollback.assert_called_once()


# Edge Cases
def test_create_with_large_ids(userchallenge_repo, mock_session, mock_challenge):
    """Test create with very large user and challenge IDs"""
    # Arrange
    large_user_id = 999999999
    large_challenge_id = 999999998
    kwargs = {
        'user_idx': large_user_id,
        'C_idx': large_challenge_id,
        'userChallengeName': 'large-id-test'
    }
    # Set up challenge validation to succeed
    userchallenge_repo.challenge_repo.get_by_id.return_value = mock_challenge

    # Act
    result = userchallenge_repo.create(**kwargs)

    # Assert
    assert isinstance(result, UserChallenges)
    assert result.user_idx == large_user_id
    assert result.C_idx == large_challenge_id


def test_get_with_empty_conditions(userchallenge_repo, mock_session, mock_userchallenge):
    """Test get with empty conditions"""
    # Arrange
    kwargs = {}
    setup_mock_session_for_query(mock_session, mock_userchallenge)

    # Act
    result = userchallenge_repo.get(**kwargs)

    # Assert
    assert result == mock_userchallenge
    assert_session_calls(mock_session, execute_called=True)


def test_is_exist_with_empty_conditions(userchallenge_repo, mock_session):
    """Test is_exist with empty conditions"""
    # Arrange
    kwargs = {}
    setup_mock_session_for_query(mock_session, None)

    # Act
    result = userchallenge_repo.is_exist(**kwargs)

    # Assert
    assert result is False


def test_update_with_empty_fields(userchallenge_repo, mock_session, mock_userchallenge):
    """Test update with empty fields"""
    # Arrange
    userchallenge_id = 1
    kwargs = {}
    setup_mock_session_for_query(mock_session, mock_userchallenge)

    # Act
    result = userchallenge_repo.update(userchallenge_id, **kwargs)

    # Assert
    assert result == mock_userchallenge
    mock_session.commit.assert_called_once()


def test_multiple_operations_same_session(userchallenge_repo, mock_session, mock_userchallenge):
    """Test multiple operations using the same session"""
    # Arrange
    kwargs = {'user_idx': 100}
    setup_mock_session_for_query(mock_session, mock_userchallenge)

    # Act
    result1 = userchallenge_repo.get(**kwargs)
    result2 = userchallenge_repo.get_by_id(1)
    result3 = userchallenge_repo.is_exist(**kwargs)

    # Assert
    assert result1 is not None
    assert result2 is not None
    assert result3 is True
    assert mock_session.execute.call_count == 3


def test_create_with_special_characters_in_name(userchallenge_repo, mock_session, mock_challenge):
    """Test create with special characters in name"""
    # Arrange
    special_name = "test-challenge-@#$%^&*()"
    kwargs = {
        'user_idx': 100,
        'C_idx': 200,
        'userChallengeName': special_name
    }
    # Set up challenge validation to succeed
    userchallenge_repo.challenge_repo.get_by_id.return_value = mock_challenge

    # Act
    result = userchallenge_repo.create(**kwargs)

    # Assert
    assert isinstance(result, UserChallenges)
    assert result.userChallengeName == special_name


def test_update_with_none_values(userchallenge_repo, mock_session, mock_userchallenge):
    """Test update with None values"""
    # Arrange
    userchallenge_id = 1
    kwargs = {
        'userChallengeName': None,
        'user_idx': None
    }
    setup_mock_session_for_query(mock_session, mock_userchallenge)

    # Act
    result = userchallenge_repo.update(userchallenge_id, **kwargs)

    # Assert
    assert result.userChallengeName is None
    assert result.user_idx is None


# Integration Tests (skipped by default)
@pytest.mark.skip(reason="Requires test database setup")
def test_create_with_real_database(real_session):
    """Integration test: Test create with real database"""
    challenge_repo = ChallengeRepository(real_session)
    repo = UserChallengeRepository(real_session, challenge_repo)
    assert repo.session == real_session
    assert repo.challenge_repo == challenge_repo


@pytest.mark.skip(reason="Requires test database setup")
def test_get_by_id_with_real_database(real_session):
    """Integration test: Test get_by_id with real database"""
    repo = UserChallengeRepository(real_session)
    assert repo.session == real_session 