import datetime
import logging
import sys
from typing import Any, Dict
from kafka import KafkaConsumer
import json
from app.exceptions.kafka import QueueProcessingError


class StatusMessage:
    """상태 메시지를 표현하는 클래스"""
    def __init__(self, user: str, problemId: str, newStatus: str, timestamp: str):
        self.user = user
        self.problemId = problemId
        self.newStatus = newStatus
        self.timestamp = timestamp

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'StatusMessage':
        return cls(
            user=data['user'],
            problemId=data['problemId'],
            newStatus=data['newStatus'],
            timestamp=data['timestamp']
        )

    def __str__(self) -> str:
        return f"StatusMessage(user={self.user}, problemId={self.problemId}, newStatus={self.newStatus}, timestamp={self.timestamp})"

class KafkaEventConsumer:
    """Kafka 이벤트 소비자 클래스"""
    def __init__(self, config):
        self.config = config
        self._consumer = None
        self.reconnect_attempts = 3  # 최대 재연결 횟수

    @property
    def consumer(self):
        """Kafka 소비자 인스턴스를 생성하고 반환 (지연 초기화)"""
        if self._consumer is None:
            self._initialize_consumer()
        return self._consumer

    def _initialize_consumer(self):
        """KafkaConsumer 인스턴스를 생성하고 예외 발생 시 재시도"""
        attempt = 0
        while attempt < self.reconnect_attempts:
            try:
                self._consumer = KafkaConsumer(
                    self.config.topic,
                    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                    **self.config.consumer_config
                )
                print("Kafka consumer successfully initialized.",file=sys.stderr)
                return
            except Exception as e:
                print(f"Kafka consumer connection failed (Attempt {attempt+1}): {e}")
                datetime.time.sleep(2 ** attempt)  # 지수 백오프 적용
                attempt += 1
        raise QueueProcessingError(error_msg="Failed to initialize Kafka consumer after retries")

    def consume_events(self, callback):
        """이벤트를 소비하고 콜백 함수로 처리"""
        try:
            for message in self.consumer:
                try:
                    status_msg = StatusMessage.from_json(message.value)
                    callback(status_msg)
                except json.JSONDecodeError as e:
                    print(f"JSON decoding error: {e}",file=sys.stderr)
                    continue
                except KeyError as e:
                    print(f"Missing required field: {e}",file=sys.stderr)
                    continue
                except Exception as e:
                    print(f"Unexpected error processing message: {e}",file=sys.stderr)
                    continue
        except Exception as e:
            print(f"Kafka consumer error: {e}",file=sys.stderr)
            self._reconnect_consumer()

    def _reconnect_consumer(self):
        """Kafka 소비자 재연결"""
        print("Reconnecting Kafka consumer...",file=sys.stderr)
        self.close()
        self._initialize_consumer()

    def close(self):
        """Kafka 소비자 종료 및 연결 해제"""
        if self._consumer:
            self._consumer.close()
            self._consumer = None
        print("Kafka consumer closed.",file=sys.stderr)