__version__ = '1.0.0'

__all__ = [
    'KafkaEventConsumer',
    'KafkaConfig',
]

from challenge_api.extensions.kafka.config import KafkaConfig
from challenge_api.extensions.kafka.consumer import KafkaEventConsumer
