__version__ = '1.0.0'

__all__ = [
    'KafkaEventConsumer',
    'KafkaConfig',
]

from extensions.kafka.config import KafkaConfig
from extensions.kafka.consumer import KafkaEventConsumer
