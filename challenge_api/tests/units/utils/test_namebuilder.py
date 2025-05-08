import pytest
from unittest.mock import Mock, patch

from utils.namebuilder import ChallengeNameSet, NameBuilder

@pytest.fixture
def mock_data():
    return {
        'challenge_id': 123,
        'user_id': 456,
        'expected_name': 'challenge-123-456'
    }

@pytest.fixture
def mock_challenge_name_set():
    with patch('utils.namebuilder.ChallengeNameSet') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock, mock_instance

def test_challenge_name_set(mock_data, mock_challenge_name_set):
    # Given
    mock_class, mock_instance = mock_challenge_name_set
    mock_instance.name = mock_data['expected_name']
    mock_instance.is_valid_name.return_value = True
    
    # When
    name_set = ChallengeNameSet(
        challenge_id=mock_data['challenge_id'], 
        user_id=mock_data['user_id']
    )
    
    # Then
    assert name_set.name == mock_data['expected_name']
    assert name_set.is_valid_name() is True
    mock_class.assert_called_once_with(
        challenge_id=mock_data['challenge_id'],
        user_id=mock_data['user_id']
    )

def test_challenge_name_set_invalid(mock_data, mock_challenge_name_set):
    # Given
    mock_class, mock_instance = mock_challenge_name_set
    mock_instance.name = mock_data['expected_name']
    mock_instance.is_valid_name.return_value = False
    
    # When
    name_set = ChallengeNameSet(
        challenge_id=mock_data['challenge_id'], 
        user_id=mock_data['user_id']
    )
    
    # Then
    assert name_set.is_valid_name() is False
    mock_class.assert_called_once_with(
        challenge_id=mock_data['challenge_id'],
        user_id=mock_data['user_id']
    )

def test_name_builder(mock_data, mock_challenge_name_set):
    # Given
    mock_class, mock_instance = mock_challenge_name_set
    mock_instance.name = mock_data['expected_name']
    mock_instance.is_valid_name.return_value = True
    
    # When
    builder = NameBuilder(
        challenge_id=mock_data['challenge_id'], 
        user_id=mock_data['user_id']
    )
    result = builder.build()
    
    # Then
    assert result is not None
    assert result.name == mock_data['expected_name']
    assert result.is_valid_name() is True
    mock_class.assert_called_once_with(
        challenge_id=mock_data['challenge_id'],
        user_id=mock_data['user_id']
    )

def test_name_builder_invalid(mock_data, mock_challenge_name_set):
    # Given
    mock_class, mock_instance = mock_challenge_name_set
    mock_instance.name = mock_data['expected_name']
    mock_instance.is_valid_name.return_value = False
    
    # When
    builder = NameBuilder(
        challenge_id=mock_data['challenge_id'], 
        user_id=mock_data['user_id']
    )
    result = builder.build()
    
    # Then
    assert result is None
    mock_class.assert_called_once_with(
        challenge_id=mock_data['challenge_id'],
        user_id=mock_data['user_id']
    )