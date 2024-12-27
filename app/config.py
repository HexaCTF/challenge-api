import os


class Config:
    # Flask configuration
    # SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

    # Database configuration
    # DB_HOST = os.getenv('DB_HOST', 'localhost')
    # DB_USER = os.getenv('DB_USER', 'your_user')
    # DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_password')
    # DB_NAME = os.getenv('DB_NAME', 'your_database')

    # Kafka configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9093')
    KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'challenge-status')
    KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'challenge-consumer-group')
