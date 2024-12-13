from kafka import KafkaConsumer
import json

from external.kafka.exceptions import ConsumerException


class KafkaEventConsumer:
    def __init__(self, config):
        """
        Initialize Kafka consumer with configuration

        Args:
            config (KafkaConfig): Configuration instance
        """
        self.config = config
        self._consumer = None

    @property
    def consumer(self):
        if self._consumer is None:
            try:
                self._consumer = KafkaConsumer(
                    self.config.topic,
                    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                    **self.config.consumer_config
                )
            except Exception as e:
                raise ConsumerException(f"Failed to create consumer: {str(e)}")
        return self._consumer

    def consume_events(self, callback):
        """
        Consume events and process them using callback

        Args:
            callback (callable): Function to process each message
        """
        try:
            for message in self.consumer:
                try:
                    callback(message.value)
                except Exception as e:
                    print(f"Error processing message: {str(e)}")
                    continue

        except Exception as e:
            raise ConsumerException(f"Failed to consume events: {str(e)}")

    def close(self):
        """Close the consumer connection"""
        if self._consumer:
            self._consumer.close()
            self._consumer = None
