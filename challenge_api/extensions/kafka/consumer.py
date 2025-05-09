import datetime
import logging
from typing import Any, Dict
from kafka import KafkaConsumer
import json
from challenge_api.exceptions.kafka_exceptions import QueueProcessingError

logger = logging.getLogger(__name__)
class StatusMessage:
   """상태 메시지를 표현하는 클래스"""
   def __init__(self, userId: str, problemId: str, newStatus: str, timestamp: str, endpoint: str = None):
       # 메시지의 기본 속성들을 초기화
       self.userId = userId          # 사용자 ID
       self.problemId = problemId    # 문제 ID 
       self.newStatus = newStatus    # 새로운 상태
       self.timestamp = timestamp    # 타임스탬프
       self.endpoint = endpoint      # 엔드포인트

   @classmethod
   def from_json(cls, data: Dict[str, Any]) -> 'StatusMessage':
       """
       JSON 데이터로부터 StatusMessage 객체를 생성하는 클래스 메서드
       
       Args:
           data: JSON 형식의 딕셔너리 데이터
       Returns:
           StatusMessage 인스턴스
       """
       return cls(
           userId=data['userId'],
           problemId=data['problemId'],
           newStatus=data['newStatus'],
           timestamp=data['timestamp'],
           endpoint=data.get('endpoint')  # endpoint가 없을 수 있으므로 get 사용
       )

   def __str__(self) -> str:
       """객체를 문자열로 표현"""
       return f"StatusMessage(userId={self.userId}, problemId={self.problemId}, newStatus={self.newStatus}, timestamp={self.timestamp}, endpoint={self.endpoint})"

class KafkaEventConsumer:
   """Kafka 이벤트 소비자 클래스"""
   def __init__(self, config):
       """
       Kafka 소비자 초기화
       
       Args:
           config (KafkaConfig): 설정 객체
       """
       self.config = config
       self._consumer = None  # 실제 Kafka 소비자 인스턴스

   def bootstrap_connected(self) -> bool:
       """Kafka 브로커와의 연결 상태를 확인

       Returns:
           bool: 연결 성공 여부
       """
       try:
           if not self._consumer:
               self._consumer = KafkaConsumer(
                   self.config.topic,
                   value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                   **self.config.consumer_config
               )
           
           # 브로커 연결 상태 확인
           node_info = self._consumer.cluster.brokers()
           if not node_info:
               logger.error("No brokers available")
               return False
               
           return True
       except Exception as e:
           logger.error(f"Error checking bootstrap connection: {e}")
           return False

   @property
   def consumer(self):
       """
       Kafka 소비자 인스턴스를 생성하고 반환하는 프로퍼티
       지연 초기화(lazy initialization) 패턴 사용
       """
       if self._consumer is None:
           try:
               self._consumer = KafkaConsumer(
                   self.config.topic,
                   value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                   **self.config.consumer_config
               )
           except Exception as e:
               logger.error(f"Failed to create consumer: {e}")
               raise QueueProcessingError(error_msg=f"Failed to create consumer: {e}") from e
       return self._consumer

   def consume_events(self, callback):
       """
       이벤트를 소비하고 콜백 함수로 처리
       
       Args:
           callback: 각 메시지를 처리할 콜백 함수
       """
       try:
           for message in self.consumer:
               try:
                   # 메시지 파싱
                   status_msg = StatusMessage.from_json(message.value)
                   callback(status_msg)
                   
               except json.JSONDecodeError as e:
                   # JSON 디코딩 오류 처리
                   logger.error(f"Error decoding message: {e}")
                   continue
               except KeyError as e:
                   # 필수 필드 누락 오류 처리
                   logger.error(f"Missing required field in message: {e}")
                   continue
               except Exception as e:
                   # 기타 예외 처리
                   logger.error(f"Error processing message: {e}")
                   continue
               
       except Exception as e:
           raise QueueProcessingError(error_msg=f"Kafka Error: {str(e)}") from e

   def close(self):
       """Kafka 소비자 연결 종료"""
       if self._consumer:
           self._consumer.close()
           self._consumer = None