__version__ = '1.0.0'

__all__ = [
    'KafkaEventConsumer',
    'KafkaConfig',
]

from app.extensions.kafka.config import KafkaConfig
from app.extensions.kafka.consumer import KafkaEventConsumer
