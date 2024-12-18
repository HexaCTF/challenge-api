from flask import Flask

from app.api.challenge import challenge_bp
from app.config import Config
from app.extensions.kafka.handler import MessageHandler
from app.extensions_manager import kafka_consumer


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    from app.extensions_manager import db
    db.init_app(app)
    kafka_consumer.init_app(app)

    # Register blueprints
    app.register_blueprint(challenge_bp, url_prefix='/challenges')

    # Start Kafka consumer when app starts
    @app.before_first_request
    def start_kafka_consumer():
        kafka_consumer.start_consuming(MessageHandler.handle_message)

    # Clean up Kafka consumer when app stops
    @app.teardown_appcontext
    def cleanup(exception=None):
        kafka_consumer.stop_consuming()

    return app