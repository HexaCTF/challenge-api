# app/config.py
import os

class Config:
    """Flask 애플리케이션 설정"""
    
    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'mariadb')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'challenge_db')
    DB_USER = os.getenv('DB_USER', 'challenge_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'challenge_password')

    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = (
        f"mariadb+mariadbconnector://{DB_USER}:{DB_PASSWORD}@"
        f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))
    SQLALCHEMY_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))
    
    # Security configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Kafka configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
    KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'challenge-status')
    KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'challenge-consumer-group')