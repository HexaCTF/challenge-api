import sys
import json
from threading import Lock, Thread, Event
from typing import Optional, Callable
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from challenge_api.extensions.kafka import KafkaConfig, KafkaEventConsumer

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
            try:
                self.app = app
                print(f"Initializing Kafka consumer with bootstrap servers: {app.config['KAFKA_BOOTSTRAP_SERVERS']}", file=sys.stderr)
                
                config = KafkaConfig(
                    bootstrap_servers=[app.config['KAFKA_BOOTSTRAP_SERVERS']],
                    topic=app.config['KAFKA_TOPIC'],
                    group_id=app.config['KAFKA_GROUP_ID'],
                    
                )
                self.consumer = KafkaEventConsumer(config)
                print("Kafka consumer initialized", file=sys.stderr)

                # teardown_appcontext 핸들러 등록
                app.teardown_appcontext(self.cleanup)
            except Exception as e:
                print(f"Failed to initialize Kafka consumer: {e}", file=sys.stderr)
                raise
    
    def cleanup(self, exception=None) -> None:
        """애플리케이션 컨텍스트 종료 시 정리"""
        self.stop_consuming()
    
    def start_consuming(self, message_handler: Callable) -> None:
        """Thread-safe하게 메시지 소비 시작"""
        with self._lock:
            try:
                if not self.consumer:
                    print("Consumer not initialized", file=sys.stderr)
                    return
                    
                if self._consumer_thread is not None:
                    print("Consumer thread already running", file=sys.stderr)
                    return
                
                print("Starting Kafka consumer thread", file=sys.stderr)
                self._running.set()
                self._consumer_thread = Thread(
                    target=self._consume_messages,
                    args=(message_handler,),
                    daemon=True
                )
                self._consumer_thread.start()
                print("Kafka consumer thread started", file=sys.stderr)
            except Exception as e:
                print(f"Error starting consumer: {e}", file=sys.stderr)
                self._running.clear()
                self._consumer_thread = None
    

    def stop_consuming(self) -> None:
        """Thread-safe하게 메시지 소비 중지"""
        """메시지 소비 중지"""
        with self._lock:

            if self.consumer:
                self._running.clear()
                self.consumer.close()
                self._consumer_thread = None
                print("Kafka consumer stopped", file=sys.stderr)

    
    def _consume_messages(self, message_handler: Callable) -> None:
        """Thread-safe한 메시지 소비 루프"""
        with self.app.app_context():
            try:
                print(f"Trying to connect to Kafka at {self.consumer.config.bootstrap_servers}", file=sys.stderr)
                # 연결 상태 확인
                if not self.consumer.bootstrap_connected():
                    print("Failed to connect to Kafka brokers", file=sys.stderr)
                    return
                print("Successfully connected to Kafka", file=sys.stderr)
                
                reconnect_delay = 5.0  # 초기 재연결 대기 시간
                max_reconnect_delay = 60.0  # 최대 재연결 대기 시간

                while self._running.is_set():
                    try:
                        self.consumer.consume_events(message_handler)
                    except Exception as e:
                        print(f"Error consuming messages: {e}", file=sys.stderr)
                        if self._running.is_set():
                            print(f"Attempting to reconnect in {reconnect_delay} seconds...", file=sys.stderr)
                            self._running.wait(timeout=reconnect_delay)
                            # 지수 백오프로 재연결 대기 시간 증가
                            reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
                            # 재연결 시도
                            if not self.consumer.bootstrap_connected():
                                print("Failed to reconnect to Kafka brokers", file=sys.stderr)
                                continue
                            print("Successfully reconnected to Kafka", file=sys.stderr)
                            reconnect_delay = 5.0  # 성공하면 대기 시간 초기화
            except Exception as e:
                print(f"[ERROR] Fatal error in consumer thread: {e}", file=sys.stderr)
            finally:
                print("Consumer thread ending", file=sys.stderr)

                
# 전역 인스턴스 생성
db = SQLAlchemy()
kafka_consumer = FlaskKafkaConsumer()