import logging
import sys
from threading import Lock, Thread, Event
from typing import Optional, Callable
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from challenge_api.extensions.kafka import KafkaConfig, KafkaEventConsumer
from kafka import KafkaConsumer
from kafka.errors import KafkaError, NoBrokersAvailable
import json
import os
import time
from challenge_api.extensions.kafka.handler import MessageHandler

logger = logging.getLogger(__name__)

class FlaskKafkaConsumer:
    """Flask 애플리케이션에서 Kafka 메시지 소비를 관리하는 클래스"""
    def __init__(self):
        self.consumer: Optional[KafkaEventConsumer] = None
        self._consumer_thread: Optional[Thread] = None
        self._running = Event()
        self._lock = Lock()
        self.app: Optional[Flask] = None
        self.handler = MessageHandler()
        self._reconnect_delay = 5  # 재연결 시도 간격 (초)
        self._max_reconnect_attempts = 3  # 최대 재연결 시도 횟수
    
    def init_app(self, app: Flask) -> None:
        """Flask 애플리케이션 초기화"""
        with self._lock:
            self.app = app
            try:
                config = KafkaConfig(
                    bootstrap_servers=[app.config['KAFKA_BOOTSTRAP_SERVERS']],
                    topic=app.config['KAFKA_TOPIC'],
                    group_id=app.config['KAFKA_GROUP_ID']
                )
                self.consumer = KafkaEventConsumer(config)
                logger.info("Kafka consumer initialized with app config")
            except Exception as e:
                logger.error(f"Failed to initialize Kafka consumer with app config: {str(e)}")
                raise

            # teardown_appcontext 핸들러 등록
            app.teardown_appcontext(self.cleanup)
    
    def cleanup(self, exception=None):
        """애플리케이션 컨텍스트 종료 시 정리"""
        self.stop_consuming()
    
    def start_consuming(self) -> None:
        """Thread-safe하게 메시지 소비 시작"""
        with self._lock:
            if self._running.is_set():
                logger.warning("Consumer already running")
                return

            try:
                self._initialize_consumer()
                self._running.set()
                self._consumer_thread = Thread(target=self._consume_messages)
                self._consumer_thread.daemon = True
                self._consumer_thread.start()
                logger.info("Kafka consumer started")
            except Exception as e:
                logger.error(f"Failed to start consumer: {str(e)}")
                self._running.clear()
                if self.consumer:
                    try:
                        self.consumer.close()
                    except Exception as close_error:
                        logger.error(f"Error closing consumer: {str(close_error)}")
                    self.consumer = None
    
    def stop_consuming(self) -> None:
        """Thread-safe하게 메시지 소비 중지"""
        with self._lock:
            if not self._running.is_set():
                logger.warning("Consumer not running")
                return
            
            self._running.clear()
            if self.consumer:
                try:
                    self.consumer.close()
                except Exception as e:
                    logger.error(f"Error closing consumer: {str(e)}")
                self.consumer = None
                
            if self._consumer_thread:
                self._consumer_thread.join(timeout=5.0)
                if self._consumer_thread.is_alive():
                    logger.error("Consumer thread did not stop gracefully")
                self._consumer_thread = None
            logger.info("Kafka consumer stopped")
    
    def _initialize_consumer(self) -> None:
        """Kafka consumer를 초기화합니다."""
        try:
            if self.app:
                # Flask 앱 설정에서 가져오기
                bootstrap_servers = self.app.config['KAFKA_BOOTSTRAP_SERVERS']
                topic = self.app.config['KAFKA_TOPIC']
                group_id = self.app.config['KAFKA_GROUP_ID']
            else:
                # 환경 변수에서 가져오기
                bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
                topic = os.getenv('KAFKA_TOPIC', 'challenge-status')
                group_id = os.getenv('KAFKA_GROUP_ID', 'challenge-status-group')

            self.consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                consumer_timeout_ms=1000,
                retry_backoff_ms=500,
                request_timeout_ms=30000,
                session_timeout_ms=10000
            )
            logger.info(f"Kafka consumer initialized with bootstrap servers: {bootstrap_servers}")
        except NoBrokersAvailable as e:
            logger.error(f"No Kafka brokers available: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {str(e)}")
            raise

    def _consume_messages(self) -> None:
        """메시지 소비를 수행하는 메인 루프"""
        logger.info("Starting message consumption loop")
        reconnect_attempts = 0

        while self._running.is_set():
            try:
                if not self.consumer:
                    logger.error("Consumer not initialized")
                    break

                for message in self.consumer:
                    if not self._running.is_set():
                        break
                    try:
                        logger.info(f"Received message: {message.value}")
                        self.handler.handle_message(message.value)
                        reconnect_attempts = 0  # 성공적인 메시지 처리 후 재시도 카운트 리셋
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
                        continue  # 개별 메시지 처리 실패는 전체 루프를 중단하지 않음

            except KafkaError as e:
                if self._running.is_set():
                    logger.error(f"Kafka error in consumer loop: {str(e)}")
                    if reconnect_attempts < self._max_reconnect_attempts:
                        reconnect_attempts += 1
                        logger.info(f"Attempting to reconnect (attempt {reconnect_attempts}/{self._max_reconnect_attempts})")
                        time.sleep(self._reconnect_delay)
                        try:
                            self._initialize_consumer()
                            continue
                        except Exception as init_error:
                            logger.error(f"Failed to reinitialize consumer: {str(init_error)}")
                    else:
                        logger.error("Max reconnection attempts reached")
                        break
            except Exception as e:
                if self._running.is_set():
                    logger.error(f"Unexpected error in consumer loop: {str(e)}")
                    break

        logger.info("Message consumption loop stopped")

    def is_running(self) -> bool:
        """consumer가 실행 중인지 확인"""
        return self._running.is_set()

# 전역 인스턴스 생성
db = SQLAlchemy()
kafka_consumer = FlaskKafkaConsumer()