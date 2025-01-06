import os

# Config flask app에 저장할 환경 변수를 보관하는 클래스 
class Config:
    pass 
    # Database configuration
    # DB_HOST = os.getenv('DB_HOST', 'localhost')
    # DB_USER = os.getenv('DB_USER', 'your_user')
    # DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_password')
    # DB_NAME = os.getenv('DB_NAME', 'your_database')

    # Kafka configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9093')
    KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'challenge-status')
    KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'challenge-consumer-group')
