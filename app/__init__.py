# app/__init__.py
from flask import Flask
import threading

from app.api.challenge import challenge_bp
from app.config import Config
from app.extensions.kafka.handler import MessageHandler
from app.extensions_manager import kafka_consumer


def start_kafka_consumer(app):
    """Start Kafka consumer in a separate thread"""
    with app.app_context():
        kafka_consumer.start_consuming(MessageHandler.handle_message)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    kafka_consumer.init_app(app)

    # Register blueprints
    app.register_blueprint(challenge_bp, url_prefix='/challenges')

    # Start Kafka consumer in a separate thread
    consumer_thread = threading.Thread(
        target=start_kafka_consumer,
        args=(app,),
        daemon=True
    )
    consumer_thread.start()

    # Store the thread reference on the app
    app.consumer_thread = consumer_thread

    # Clean up Kafka consumer when app stops
    @app.teardown_appcontext
    def cleanup(exception=None):
        kafka_consumer.stop_consuming()

    return app