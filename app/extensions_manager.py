import logging
from threading import Thread

from app.extensions.kafka import KafkaConfig, KafkaEventConsumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

 # FlaskKafkaConsumer는 Kafka를 Consume할때 사용됩니다.
class FlaskKafkaConsumer:
    def __init__(self):
        self.consumer = None
        self._consumer_thread = None
        self.is_running = False

    def init_app(self, app):
        config = KafkaConfig(
            bootstrap_servers=[app.config['KAFKA_BOOTSTRAP_SERVERS']],
            topic=app.config['KAFKA_TOPIC'],
            group_id=app.config['KAFKA_GROUP_ID']
        )
        self.consumer = KafkaEventConsumer(config)

    def start_consuming(self, message_handler):
        """Start consuming messages in a separate thread"""
        if self._consumer_thread is not None:
            logger.warning("Consumer thread already running")
            return

        self.is_running = True
        self._consumer_thread = Thread(
            target=self._consume_messages,
            args=(message_handler,),
            daemon=True
        )
        self._consumer_thread.start()
        logger.info("Kafka consumer thread started")

    def stop_consuming(self):
        """Stop the consumer thread"""
        self.is_running = False
        if self.consumer:
            self.consumer.close()
        if self._consumer_thread:
            self._consumer_thread.join(timeout=5.0)
            self._consumer_thread = None
        logger.info("Kafka consumer stopped")

    def _consume_messages(self, message_handler):
        """Consumer loop"""
        try:
            while self.is_running:
                try:
                    self.consumer.consume_events(message_handler)
                except Exception as e:
                    logger.error(f"Error consuming messages: {e}")
                    if self.is_running:
                        logger.info("Attempting to reconnect...")
        except Exception as e:
            logger.error(f"Fatal error in consumer thread: {e}")
        finally:
            logger.info("Consumer thread ending")

kafka_consumer = FlaskKafkaConsumer()
