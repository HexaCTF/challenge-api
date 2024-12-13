from app.extensions.db import DatabaseConfig, DatabaseConnection
from app.extensions.kafka import KafkaConfig, KafkaEventProducer


class FlaskDatabase:
    def __init__(self):
        self.connection = None

    def init_app(self, app):
        config = DatabaseConfig(
            host=app.config['DB_HOST'],
            user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'],
            database=app.config['DB_NAME']
        )
        self.connection = DatabaseConnection(config)

class FlaskKafkaProducer:
    def __init__(self):
        self.producer = None

    def init_app(self, app):
        config = KafkaConfig(
            bootstrap_servers=[app.config['KAFKA_BOOTSTRAP_SERVERS']],
            topic=app.config['KAFKA_TOPIC']
        )
        self.producer = KafkaEventProducer(config)

db = FlaskDatabase()
kafka_producer = FlaskKafkaProducer()