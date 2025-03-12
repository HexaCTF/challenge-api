__version__ = '1.0.0'

__all__ = [
    'KafkaEventConsumer',
    'KafkaConfig',
]

from hexactf.extensions.kafka.config import KafkaConfig
from hexactf.extensions.kafka.consumer import KafkaEventConsumer
