import logging
import sys
from threading import Lock, Thread, Event
from typing import Optional, Callable
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from app.extensions.db.config import MariaDBConfig
from app.extensions.kafka import KafkaConfig, KafkaEventConsumer

class FlaskKafkaConsumer:
    """Flask 애플리케이션에서 Kafka 메시지 소비를 관리하는 클래스"""
    def __init__(self):
        self.consumer: Optional[KafkaEventConsumer] = None
        self._consumer_thread: Optional[Thread] = None
        self._running = Event()
        self._lock = Lock()
        self.app: Optional[Flask] = None

    def init_app(self, app: Flask) -> None:
        """Flask 애플리케이션 초기화"""
        with self._lock:
            self.app = app
            config = KafkaConfig(
                bootstrap_servers=[app.config['KAFKA_BOOTSTRAP_SERVERS']],
                topic=app.config['KAFKA_TOPIC'],
                group_id=app.config['KAFKA_GROUP_ID']
            )
            self.consumer = KafkaEventConsumer(config)

    def start_consuming(self, message_handler: Callable) -> None:
        """Thread-safe하게 메시지 소비 시작"""
        with self._lock:
            if self._consumer_thread is not None:
                # logger.warning("Consumer thread already running")
                return

            self._running.set()
            self._consumer_thread = Thread(
                target=self._consume_messages,
                args=(message_handler,),
                daemon=True
            )
            self._consumer_thread.start()
            # logger.info("Kafka consumer thread started")

    def stop_consuming(self) -> None:
        """Thread-safe하게 메시지 소비 중지"""
        with self._lock:
            if not self._running.is_set():
                # logger.warning("Consumer not running")
                return

            self._running.clear()
            if self.consumer:
                self.consumer.close()
            
            if self._consumer_thread:
                self._consumer_thread.join(timeout=5.0)
                if self._consumer_thread.is_alive():
                    print("Consumer thread did not stop gracefully", file=sys.stderr)
                    # logger.warning("Consumer thread did not stop gracefully")
                self._consumer_thread = None
            # logger.info("Kafka consumer stopped")

    def _consume_messages(self, message_handler: Callable) -> None:
        """Thread-safe한 메시지 소비 루프"""
        with self.app.app_context():
            try:
                while self._running.is_set():
                    try:
                        self.consumer.consume_events(message_handler)
                    except Exception as e:
                        # logger.error(f"Error consuming messages: {e}")
                        if self._running.is_set():
                            # logger.info("Attempting to reconnect...")
                            self._running.wait(timeout=5.0)
            except Exception as e:
                print(f"[ERROR] Fatal error in consumer thread: {e}", file=sys.stderr)
                # logger.error(f"Fatal error in consumer thread: {e}")
            finally:
                print("Consumer thread ending", file=sys.stderr)
                # logger.info("Consumer thread ending")

# 전역 인스턴스 생성
db = SQLAlchemy()
kafka_consumer = FlaskKafkaConsumer()