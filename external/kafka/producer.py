import json
from datetime import datetime

from kafka import KafkaProducer

from external.kafka.exceptions import ProducerException


class KafkaEventProducer:
    def __init__(self, config):
        """
        Initialize Kafka producer with configuration

        Args:
            config (KafkaConfig): Configuration instance
        """
        self.config = config
        self._producer = None

    @property
    def producer(self):
        if self._producer is None:
            try:
                self._producer = KafkaProducer(
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    **self.config.producer_config
                )
            except Exception as e:
                raise ProducerException(f"Failed to create producer: {str(e)}")
        return self._producer

    def send_event(self, event_type, payload, topic=None):
        """
        Send event to Kafka topic

        Args:
            event_type (str): Type of event
            payload (dict): Event payload
            topic (str, optional): Override default topic
        """
        try:
            message = {
                'event_type': event_type,
                'payload': payload,
                'timestamp': datetime.now().isoformat()
            }

            future = self.producer.send(
                topic or self.config.topic,
                message
            )
            future.get(timeout=10)  # Wait for sending to complete

        except Exception as e:
            raise ProducerException(f"Failed to send event: {str(e)}")

    def close(self):
        """Close the producer connection"""
        if self._producer:
            self._producer.close()
            self._producer = None
