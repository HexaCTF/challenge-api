import logging
import sys
from threading import Lock, Thread, Event
from typing import Optional, Callable
from flask import Flask
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
            self.app = app
            config = KafkaConfig(
                bootstrap_servers=[app.config['KAFKA_BOOTSTRAP_SERVERS']],
                topic=app.config['KAFKA_TOPIC'],
                group_id=app.config['KAFKA_GROUP_ID']
            )
            self.consumer = KafkaEventConsumer(config)

            # teardown_appcontext 핸들러 등록
            app.teardown_appcontext(self.cleanup)
    
    def cleanup(self, exception=None):
        """애플리케이션 컨텍스트 종료 시 정리"""
        self.stop_consuming()
    
    def start_consuming(self, message_handler: Callable) -> None:
        """Thread-safe하게 메시지 소비 시작"""
        with self._lock:
            if self._consumer_thread is not None:
                print("Consumer thread already running", file=sys.stderr)
                return
            
            self._running.set()
            self._consumer_thread = Thread(
                target=self._consume_messages,
                args=(message_handler,),
                daemon=True
            )
            self._consumer_thread.start()
            print("Kafka consumer thread started", file=sys.stderr)
    
    def stop_consuming(self) -> None:
        """Thread-safe하게 메시지 소비 중지"""
        with self._lock:
            if not self._running.is_set():
                print("Consumer not running", file=sys.stderr)
                return
            
            self._running.clear()
            if self.consumer:
                self.consumer.close()
                
            if self._consumer_thread:
                self._consumer_thread.join(timeout=5.0)
                if self._consumer_thread.is_alive():
                    print("Consumer thread did not stop gracefully", file=sys.stderr)
                self._consumer_thread = None
            print("Kafka consumer stopped", file=sys.stderr)
    
    def _consume_messages(self, message_handler: Callable) -> None:
        """Thread-safe한 메시지 소비 루프"""
        with self.app.app_context():
            try:
                while self._running.is_set():
                    try:
                        self.consumer.consume_events(message_handler)
                    except Exception as e:
                        print(f"Error consuming messages: {e}", file=sys.stderr)
                        if self._running.is_set():
                            print("Attempting to reconnect...", file=sys.stderr)
                            self._running.wait(timeout=5.0)
            except Exception as e:
                print(f"[ERROR] Fatal error in consumer thread: {e}", file=sys.stderr)
            finally:
                print("Consumer thread ending", file=sys.stderr)
                
# 전역 인스턴스 생성
kafka_consumer = FlaskKafkaConsumer()