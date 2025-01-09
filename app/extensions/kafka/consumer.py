import datetime
from typing import Any, Dict
from kafka import KafkaConsumer
import json
from app.extensions.kafka.exceptions import ConsumerException

class StatusMessage:
   """상태 메시지를 표현하는 클래스"""
   def __init__(self, user: str, problemId: str, newStatus: str, timestamp: str):
       # 메시지의 기본 속성들을 초기화
       self.user = user          # 사용자 ID
       self.problemId = problemId    # 문제 ID 
       self.newStatus = newStatus    # 새로운 상태
       self.timestamp = timestamp    # 타임스탬프

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
           user=data['user'],
           problemId=data['problemId'],
           newStatus=data['newStatus'],
           timestamp=data['timestamp']
       )

   def __str__(self) -> str:
       """객체를 문자열로 표현"""
       return f"StatusMessage(user={self.user}, problemId={self.problemId}, newStatus={self.newStatus}, timestamp={self.timestamp})"

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
                   # 바이트 문자열을 JSON으로 자동 변환하는 deserializer 설정
                   value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                   **self.config.consumer_config
               )
           except Exception as e:
               raise ConsumerException(f"Failed to create consumer: {str(e)}")
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
                   print(f"Error decoding message: {e}")
                   continue
               except KeyError as e:
                   # 필수 필드 누락 오류 처리
                   print(f"Missing required field in message: {e}")
                   continue
               except Exception as e:
                   # 기타 예외 처리
                   print(f"Error processing message: {e}")
                   continue
               
       except Exception as e:
           raise ConsumerException(f"Failed to consume events: {str(e)}")

   def close(self):
       """Kafka 소비자 연결 종료"""
       if self._consumer:
           self._consumer.close()
           self._consumer = None