import logging
import sys
from threading import Lock, Thread, Event
from typing import Optional, Callable
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from challenge_api.extensions.kafka import KafkaConfig, KafkaEventConsumer
from kafka import KafkaConsumer
from kafka.errors import KafkaError, NoBrokersAvailable, ConnectionError, TimeoutError
import json
import os
import time
import traceback
from challenge_api.extensions.kafka.handler import MessageHandler

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def log_and_print(message: str, level: str = 'info'):
    """로그를 남기고 동시에 print로 출력"""
    print(f"[{level.upper()}] {message}")
    if level == 'info':
        logger.info(message)
    elif level == 'error':
        logger.error(message)
    elif level == 'warning':
        logger.warning(message)
    elif level == 'debug':
        logger.debug(message)

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
        self._last_error = None  # 마지막 에러 저장
        log_and_print("FlaskKafkaConsumer initialized", 'info')
    
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
                log_and_print("Kafka consumer initialized with app config", 'info')
            except Exception as e:
                self._last_error = str(e)
                error_msg = f"Failed to initialize Kafka consumer with app config: {str(e)}"
                log_and_print(error_msg, 'error')
                log_and_print(f"Stack trace: {traceback.format_exc()}", 'error')
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
                log_and_print("Consumer already running", 'warning')
                return

            try:
                self._initialize_consumer()
                self._running.set()
                self._consumer_thread = Thread(target=self._consume_messages)
                self._consumer_thread.daemon = True
                self._consumer_thread.start()
                log_and_print("Kafka consumer started successfully", 'info')
            except Exception as e:
                self._last_error = str(e)
                error_msg = f"Failed to start consumer: {str(e)}"
                log_and_print(error_msg, 'error')
                log_and_print(f"Stack trace: {traceback.format_exc()}", 'error')
                self._running.clear()
                if self.consumer:
                    try:
                        self.consumer.close()
                    except Exception as close_error:
                        log_and_print(f"Error closing consumer: {str(close_error)}", 'error')
                    self.consumer = None
    
    def stop_consuming(self) -> None:
        """Thread-safe하게 메시지 소비 중지"""
        with self._lock:
            if not self._running.is_set():
                log_and_print("Consumer not running", 'warning')
                return
            
            self._running.clear()
            if self.consumer:
                try:
                    self.consumer.close()
                except Exception as e:
                    log_and_print(f"Error closing consumer: {str(e)}", 'error')
                self.consumer = None
                
            if self._consumer_thread:
                self._consumer_thread.join(timeout=5.0)
                if self._consumer_thread.is_alive():
                    log_and_print("Consumer thread did not stop gracefully", 'error')
                self._consumer_thread = None
            log_and_print("Kafka consumer stopped", 'info')
    
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

            init_msg = f"Initializing Kafka consumer with bootstrap_servers={bootstrap_servers}, topic={topic}, group_id={group_id}"
            log_and_print(init_msg, 'info')

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
                session_timeout_ms=10000,
                max_poll_interval_ms=300000,  # 5분
                max_poll_records=500  # 한 번에 최대 500개 메시지 처리
            )
            log_and_print(f"Kafka consumer initialized successfully with bootstrap servers: {bootstrap_servers}", 'info')
        except NoBrokersAvailable as e:
            self._last_error = f"No Kafka brokers available: {str(e)}"
            log_and_print(self._last_error, 'error')
            raise
        except ConnectionError as e:
            self._last_error = f"Failed to connect to Kafka: {str(e)}"
            log_and_print(self._last_error, 'error')
            raise
        except TimeoutError as e:
            self._last_error = f"Kafka connection timeout: {str(e)}"
            log_and_print(self._last_error, 'error')
            raise
        except Exception as e:
            self._last_error = f"Failed to initialize Kafka consumer: {str(e)}"
            log_and_print(self._last_error, 'error')
            log_and_print(f"Stack trace: {traceback.format_exc()}", 'error')
            raise

    def _consume_messages(self) -> None:
        """메시지 소비를 수행하는 메인 루프"""
        log_and_print("Starting message consumption loop", 'info')
        reconnect_attempts = 0

        while self._running.is_set():
            try:
                if not self.consumer:
                    log_and_print("Consumer not initialized", 'error')
                    break

                for message in self.consumer:
                    if not self._running.is_set():
                        break
                    try:
                        log_and_print(f"Received message: {message.value}", 'info')
                        self.handler.handle_message(message.value)
                        reconnect_attempts = 0  # 성공적인 메시지 처리 후 재시도 카운트 리셋
                    except Exception as e:
                        self._last_error = f"Error processing message: {str(e)}"
                        log_and_print(self._last_error, 'error')
                        log_and_print(f"Stack trace: {traceback.format_exc()}", 'error')
                        continue  # 개별 메시지 처리 실패는 전체 루프를 중단하지 않음

            except KafkaError as e:
                if self._running.is_set():
                    self._last_error = f"Kafka error in consumer loop: {str(e)}"
                    log_and_print(self._last_error, 'error')
                    if reconnect_attempts < self._max_reconnect_attempts:
                        reconnect_attempts += 1
                        retry_msg = f"Attempting to reconnect (attempt {reconnect_attempts}/{self._max_reconnect_attempts})"
                        log_and_print(retry_msg, 'info')
                        time.sleep(self._reconnect_delay)
                        try:
                            self._initialize_consumer()
                            continue
                        except Exception as init_error:
                            self._last_error = f"Failed to reinitialize consumer: {str(init_error)}"
                            log_and_print(self._last_error, 'error')
                            log_and_print(f"Stack trace: {traceback.format_exc()}", 'error')
                    else:
                        log_and_print("Max reconnection attempts reached", 'error')
                        break
            except Exception as e:
                if self._running.is_set():
                    self._last_error = f"Unexpected error in consumer loop: {str(e)}"
                    log_and_print(self._last_error, 'error')
                    log_and_print(f"Stack trace: {traceback.format_exc()}", 'error')
                    break

        log_and_print("Message consumption loop stopped", 'info')

    def is_running(self) -> bool:
        """consumer가 실행 중인지 확인"""
        return self._running.is_set()

    def get_last_error(self) -> Optional[str]:
        """마지막 에러 메시지를 반환"""
        return self._last_error

# 전역 인스턴스 생성
db = SQLAlchemy()
kafka_consumer = FlaskKafkaConsumer()