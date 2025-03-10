import pytest
import json
from unittest.mock import MagicMock, patch
from hexactf.exceptions.kafka_exceptions import QueueProcessingError
from kafka import KafkaConsumer
from hexactf.extensions.kafka.consumer import KafkaEventConsumer  # Ensure it's patched correctly

@pytest.fixture
def sample_json():
    """Fixture for a sample status message JSON"""
    return {
        "user": "test_user",
        "problemId": "1234",
        "newStatus": "solved",
        "timestamp": "2025-03-10T12:00:00"
    }

@pytest.fixture
def kafka_mock():
    """Mock KafkaConsumer globally to prevent real connection attempts"""
    with patch("hexactf.extensions.kafka.consumer.KafkaConsumer") as mock_kafka_consumer:
        mock_kafka_consumer.return_value.__iter__.return_value = []  # No messages by default
        yield mock_kafka_consumer  

@pytest.fixture
def kafka_event_consumer(kafka_mock):
    """Fixture for KafkaEventConsumer with mocked KafkaConsumer"""
    mock_config = MagicMock()
    mock_config.topic = "test_topic"
    mock_config.consumer_config = {"bootstrap_servers": "localhost:9092"}
    return KafkaEventConsumer(mock_config)


@pytest.fixture
def repo_mock():
    """Fixture for mocking the UserChallengesRepository"""
    with patch("hexactf.extensions.db.UserChallengesRepository") as mock_repo:
        yield mock_repo.return_value
