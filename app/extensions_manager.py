import logging
from threading import Lock, Thread
from app.extensions.db.config import MariaDBConfig
from app.extensions.db.exceptions import InitializationError, SessionError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError


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



class MariaDBManager:
    """Flask extension for managing MariaDB connections"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.Session = None
        self._lock = Lock()
        self.is_initialized = False

    def init_app(self, app):
        """Initialize database with Flask application"""
        with self._lock:
            if self.is_initialized:
                logger.warning("Database manager already initialized")
                return

            try:
                config = MariaDBConfig.from_flask_config(app.config)
                self._initialize_engine(config)
                self.is_initialized = True
                logger.info("MariaDB manager initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize MariaDB: {e}")
                raise InitializationError("Failed to initialize database") from e

    def _initialize_engine(self, config: MariaDBConfig):
        """Initialize database engine with MariaDB-specific configuration"""
        try:
            self.engine = create_engine(
                config.connection_string,
                pool_size=config.pool_size,
                max_overflow=config.max_overflow,
                pool_timeout=config.pool_timeout,
                pool_pre_ping=True,
                pool_recycle=config.pool_recycle,
                connect_args={
                    'connect_timeout': config.connect_timeout,
                    'use_pure': True,
                    'auth_plugin': 'mysql_native_password'
                }
            )
            
            self.session_factory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(self.session_factory)
            
        except Exception as e:
            logger.error(f"Error initializing engine: {e}")
            raise InitializationError("Failed to initialize database engine") from e

    def get_session(self):
        """Get a new database session"""
        if not self.is_initialized:
            raise SessionError("Database manager not initialized")
        return self.Session()

    def close_session(self, session):
        """Safely close a database session"""
        try:
            if session:
                session.close()
        except Exception as e:
            logger.error(f"Error closing session: {e}")
            raise SessionError("Failed to close database session") from e

    def shutdown(self):
        """Shutdown the database manager"""
        with self._lock:
            if self.engine:
                try:
                    self.Session.remove()
                    self.engine.dispose()
                    self.is_initialized = False
                    logger.info("Database manager shutdown completed")
                except Exception as e:
                    logger.error(f"Error during database shutdown: {e}")
                    raise ConnectionError("Failed to shutdown database") from e

    def check_connection(self) -> bool:
        """Check if database connection is healthy"""
        if not self.is_initialized:
            return False

        try:
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    # Context Manager를 통해 세션을 자동으로 관리
    def __enter__(self):
        """Context manager entry"""
        return self.get_session()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.Session.remove()

db = MariaDBManager()
kafka_consumer = FlaskKafkaConsumer()
