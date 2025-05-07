from unittest.mock import MagicMock, patch

import pytest

from exceptions.kafka_exceptions import QueueProcessingError
from extensions.kafka.consumer import KafkaEventConsumer


def test_consumer_initialization(kafka_event_consumer, kafka_mock):
    """Test Kafka consumer initialization"""
    assert kafka_event_consumer.consumer is not None
    kafka_mock.assert_called_once()  

def test_consume_valid_message(kafka_event_consumer, kafka_mock, sample_json):
    """Test consuming valid Kafka messages"""
    mock_callback = MagicMock()

    mock_message = MagicMock()
    mock_message.value = sample_json  
    
    kafka_mock.return_value.__iter__.return_value = [mock_message]
    kafka_event_consumer.consume_events(mock_callback)
    mock_callback.assert_called_once()

    status_msg = mock_callback.call_args[0][0]
    assert status_msg.user == "test_user"
    assert status_msg.problemId == "1234"


def test_consumer_creation_failure():
    """Test handling when Kafka consumer fails to initialize"""
    with patch("hexactf.extensions.kafka.consumer.KafkaConsumer", side_effect=Exception("Failed to process request")):
        with pytest.raises(QueueProcessingError, match="Failed to process request"):
            consumer = KafkaEventConsumer(MagicMock())
            _ = consumer.consumer  
            
def test_close_consumer(kafka_event_consumer, kafka_mock):
    """Test consumer closing"""
    _ = kafka_event_consumer.consumer  # Ensure the consumer is initialized
    kafka_event_consumer.close()
    kafka_mock.return_value.close.assert_called_once()  # Check that close was called
    assert kafka_event_consumer._consumer is None
