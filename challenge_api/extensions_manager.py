import logging
import sys
import traceback
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

        print("[INFO] FlaskKafkaConsumer initialized", file=sys.stderr)

    
    def init_app(self, app: Flask) -> None:
        """Flask 애플리케이션 초기화"""
        with self._lock:

            try:
                self.app = app
                print(f"[INFO] Initializing Kafka consumer with bootstrap servers: {app.config['KAFKA_BOOTSTRAP_SERVERS']}", file=sys.stderr)
                print(f"[INFO] Topic: {app.config['KAFKA_TOPIC']}, Group ID: {app.config['KAFKA_GROUP_ID']}", file=sys.stderr)
                
                config = KafkaConfig(
                    bootstrap_servers=[app.config['KAFKA_BOOTSTRAP_SERVERS']],
                    topic=app.config['KAFKA_TOPIC'],
                    group_id=app.config['KAFKA_GROUP_ID']
                )
                self.consumer = KafkaEventConsumer(config)
                print("[INFO] KafkaEventConsumer created successfully", file=sys.stderr)

                # teardown_appcontext 핸들러 등록
                app.teardown_appcontext(self.cleanup)
                print("[INFO] Teardown handler registered", file=sys.stderr)
            except Exception as e:
                print(f"[ERROR] Failed to initialize Kafka consumer: {str(e)}", file=sys.stderr)
                print(f"[ERROR] Traceback: {traceback.format_exc()}", file=sys.stderr)
                raise

    
    def cleanup(self, exception=None):
        """애플리케이션 컨텍스트 종료 시 정리"""
        print("[INFO] Starting cleanup process", file=sys.stderr)
        if exception:
            print(f"[WARNING] Cleanup triggered by exception: {str(exception)}", file=sys.stderr)
        self.stop_consuming()
    
    def start_consuming(self, message_handler: Callable) -> None:
        """Thread-safe하게 메시지 소비 시작"""
        with self._lock:

            try:
                if self._consumer_thread is not None:
                    print("[WARNING] Consumer thread already running", file=sys.stderr)
                    return
                
                print("[INFO] Starting Kafka consumer thread", file=sys.stderr)
                self._running.set()
                self._consumer_thread = Thread(
                    target=self._consume_messages,
                    args=(message_handler,),
                    daemon=True
                )
                self._consumer_thread.start()
                print("[INFO] Kafka consumer thread started successfully", file=sys.stderr)
            except Exception as e:
                print(f"[ERROR] Failed to start consumer thread: {str(e)}", file=sys.stderr)
                print(f"[ERROR] Traceback: {traceback.format_exc()}", file=sys.stderr)
                raise

    
    def stop_consuming(self) -> None:
        """Thread-safe하게 메시지 소비 중지"""
        with self._lock:

            try:
                if not self._running.is_set():
                    print("[INFO] Consumer not running", file=sys.stderr)
                    return
                
                print("[INFO] Stopping Kafka consumer...", file=sys.stderr)
                self._running.clear()
                
                if self.consumer:
                    try:
                        print("[INFO] Closing Kafka consumer connection...", file=sys.stderr)
                        self.consumer.close()
                        print("[INFO] Kafka consumer connection closed", file=sys.stderr)
                    except Exception as e:
                        print(f"[ERROR] Error closing consumer: {str(e)}", file=sys.stderr)
                        print(f"[ERROR] Traceback: {traceback.format_exc()}", file=sys.stderr)
                
                if self._consumer_thread:
                    print("[INFO] Waiting for consumer thread to stop...", file=sys.stderr)
                    self._consumer_thread.join(timeout=5.0)
                    if self._consumer_thread.is_alive():
                        print("[ERROR] Consumer thread did not stop gracefully", file=sys.stderr)
                    else:
                        print("[INFO] Consumer thread stopped successfully", file=sys.stderr)
                    self._consumer_thread = None
                
                print("[INFO] Kafka consumer stopped completely", file=sys.stderr)
            except Exception as e:
                print(f"[ERROR] Error during consumer shutdown: {str(e)}", file=sys.stderr)
                print(f"[ERROR] Traceback: {traceback.format_exc()}", file=sys.stderr)
                raise

    
    def _consume_messages(self, message_handler: Callable) -> None:
        """Thread-safe한 메시지 소비 루프"""
        with self.app.app_context():
            try:

                print("[INFO] Starting message consumption loop", file=sys.stderr)
                while self._running.is_set():
                    try:
                        print("[DEBUG] Attempting to consume messages...", file=sys.stderr)
                        self.consumer.consume_events(message_handler)
                    except Exception as e:
                        print(f"[ERROR] Error consuming messages: {str(e)}", file=sys.stderr)
                        print(f"[ERROR] Traceback: {traceback.format_exc()}", file=sys.stderr)
                        if self._running.is_set():
                            print("[INFO] Attempting to reconnect...", file=sys.stderr)
                            self._running.wait(timeout=5.0)
            except Exception as e:
                print(f"[ERROR] Fatal error in consumer thread: {str(e)}", file=sys.stderr)
                print(f"[ERROR] Traceback: {traceback.format_exc()}", file=sys.stderr)
            finally:
                print("[INFO] Consumer thread ending", file=sys.stderr)

                
# 전역 인스턴스 생성
db = SQLAlchemy()
kafka_consumer = FlaskKafkaConsumer()