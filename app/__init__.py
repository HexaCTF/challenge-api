# app/__init__.py
from flask import Flask
import threading

from app.api.challenge import challenge_bp
from app.config import Config
from app.extensions.kafka.handler import MessageHandler
from app.extensions_manager import kafka_consumer, db


def start_kafka_consumer(app):
    """Start Kafka consumer in a separate thread"""
    with app.app_context():
        kafka_consumer.start_consuming(MessageHandler.handle_message)


# Flask를 실행시키는 코드
# TODO(+) : Config에 데이터베이스 관련 환경 변수 추가하기 
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Extension 초기화 
    kafka_consumer.init_app(app)
        
    # blueprint 등록
    app.register_blueprint(challenge_bp, url_prefix='/challenges')

    # * Kafka 설정(추후 주석 제거 예정) 
    consumer_thread = threading.Thread(
        target=start_kafka_consumer,
        args=(app,),
        daemon=True
    )
    consumer_thread.start()

    app.consumer_thread = consumer_thread

    # Clean up Kafka consumer when app stops
    @app.teardown_appcontext
    def cleanup(exception=None):
        kafka_consumer.stop_consuming()

    return app