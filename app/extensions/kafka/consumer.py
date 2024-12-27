import datetime
from typing import Any, Dict
from kafka import KafkaConsumer
import json

from app.extensions.kafka.exceptions import ConsumerException


class StatusMessage:
    def __init__(self, userId: str, problemId: str, newStatus: str, timestamp: str):
        self.userId = userId
        self.problemId = problemId
        self.newStatus = newStatus
        self.timestamp = timestamp

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'StatusMessage':
        return cls(
            userId=data['userId'],
            problemId=data['problemId'],
            newStatus=data['newStatus'],
            timestamp=data['timestamp']
        )

    def __str__(self) -> str:
        return f"StatusMessage(userId={self.userId}, problemId={self.problemId}, newStatus={self.newStatus}, timestamp={self.timestamp})"


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
                try:                 # Parse the message
                    status_msg = StatusMessage.from_json(message.value)
                    
                    # Print the message in a formatted way
                    print("\n=== New Status Message ===")
                    print(f"User ID: {status_msg.userId}")
                    print(f"Problem ID: {status_msg.problemId}")
                    print(f"New Status: {status_msg.newStatus}")
                    print(f"Timestamp: {status_msg.timestamp}")
                    print("=========================\n")
                    
                except json.JSONDecodeError as e:
                    print(f"Error decoding message: {e}")
                    continue
                except KeyError as e:
                    print(f"Missing required field in message: {e}")
                    continue
                except Exception as e:
                    print(f"Error processing message: {e}")
                    continue

        except Exception as e:
            raise ConsumerException(f"Failed to consume events: {str(e)}")

    def close(self):
        if self._consumer:
            self._consumer.close()
            self._consumer = None
