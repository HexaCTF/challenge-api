import datetime
import logging
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import json
from challenge_api.exceptions.kafka_exceptions import QueueProcessingError
import sys
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class StatusMessage:
    """상태 메시지를 표현하는 데이터 클래스"""
    userId: str
    problemId: str
    newStatus: str
    timestamp: str
    endpoint: Optional[str] = None

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'StatusMessage':
        """
        JSON 데이터로부터 StatusMessage 객체를 생성하는 클래스 메서드
        
        Args:
            data: JSON 형식의 딕셔너리 데이터
        Returns:
            StatusMessage 인스턴스
        Raises:
            ValueError: 필수 필드가 누락된 경우
        """
        required_fields = {'userId', 'problemId', 'newStatus', 'timestamp'}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
            
        return cls(
            userId=str(data['userId']),
            problemId=str(data['problemId']),
            newStatus=str(data['newStatus']),
            timestamp=str(data['timestamp']),
            endpoint=str(data.get('endpoint', ''))
        )

    def __str__(self) -> str:
        """객체를 문자열로 표현"""
        return (f"StatusMessage(userId={self.userId}, problemId={self.problemId}, "
                f"newStatus={self.newStatus}, timestamp={self.timestamp}, "
                f"endpoint={self.endpoint})")

class KafkaEventConsumer:
    """Kafka 이벤트 소비자 클래스"""
    def __init__(self, config):
        """
        Kafka 소비자 초기화
        
        Args:
            config (KafkaConfig): 설정 객체
        """
        self.config = config
        self._consumer = None
        self._connected = False

    @contextmanager
    def _get_consumer(self):
        """컨텍스트 매니저를 사용한 Kafka 소비자 관리"""
        try:
            if not self._consumer:
                self._consumer = self._create_consumer()
            yield self._consumer
        except KafkaError as e:
            logger.error(f"Kafka error: {e}")
            self._connected = False
            raise QueueProcessingError(error_msg=f"Kafka error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self._connected = False
            raise QueueProcessingError(error_msg=f"Unexpected error: {e}") from e

    def _create_consumer(self) -> KafkaConsumer:
        """내부 메서드: Kafka 소비자 인스턴스 생성"""
        try:
            consumer = KafkaConsumer(
                self.config.topic,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                **self.config.consumer_config
            )
            self._connected = True
            return consumer
        except Exception as e:
            logger.error(f"Failed to create consumer: {e}")
            self._connected = False
            raise QueueProcessingError(error_msg=f"Failed to create consumer: {e}") from e

    def bootstrap_connected(self) -> bool:
        """Kafka 브로커와의 연결 상태를 확인

        Returns:
            bool: 연결 성공 여부
        """
        try:
            with self._get_consumer() as consumer:
                # 브로커 연결 상태 확인
                node_info = consumer.cluster.brokers()
                if not node_info:
                    logger.error("No brokers available")
                    return False
                    
                # 토픽 존재 여부 확인
                topics = consumer.topics()
                if self.config.topic not in topics:
                    logger.error(f"Topic '{self.config.topic}' not found")
                    return False
                    
                return True
        except Exception as e:
            logger.error(f"Error checking bootstrap connection: {e}")
            return False

    def consume_events(self, callback: Callable[[StatusMessage], None]) -> None:
        """
        이벤트를 소비하고 콜백 함수로 처리
        
        Args:
            callback: 각 메시지를 처리할 콜백 함수
            
        Raises:
            QueueProcessingError: 메시지 처리 중 오류 발생시
        """
        if not self._consumer:
            logger.error("Consumer not initialized")
            raise RuntimeError("Consumer not initialized")

        try:
            logger.debug("Starting to consume messages...")
            with self._get_consumer() as consumer:
                # 토픽 구독
                consumer.subscribe([self.config.topic])
                logger.debug(f"Subscribed to topic: {self.config.topic}")
                
                for message in consumer:
                    try:
                        if message is None or message.value is None:
                            logger.warning("Received null message")
                            continue
                            
                        logger.debug(f"Received message from partition {message.partition}, "
                                   f"offset {message.offset}")
                        logger.debug(f"Message value: {message.value}")
                        
                        # 메시지 파싱
                        status_msg = StatusMessage.from_json(message.value)
                        logger.debug(f"Parsed message: {status_msg}")
                        
                        # 콜백 호출
                        logger.debug("Calling message handler...")
                        callback(status_msg)
                        logger.debug("Message handler completed successfully")
                        
                        # 오프셋 커밋
                        consumer.commit()
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error: {e}")
                        logger.error(f"Raw message content: {message.value}")
                        continue
                    except ValueError as e:
                        logger.error(f"Message validation error: {e}")
                        logger.error(f"Message content: {message.value}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        logger.error(f"Error type: {type(e)}")
                        logger.error(f"Message content: {message.value}")
                        continue
                
        except Exception as e:
            logger.error(f"Fatal error in consume_events: {e}")
            logger.error(f"Error type: {type(e)}")
            raise QueueProcessingError(error_msg=f"Kafka Error: {str(e)}") from e

    def close(self) -> None:
        """Kafka 소비자 연결 종료"""
        if self._consumer:
            try:
                self._consumer.close()
            except Exception as e:
                logger.error(f"Error closing consumer: {e}")
            finally:
                self._consumer = None
                self._connected = False