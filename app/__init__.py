from app.config import Config
from app.extensions import db


def create_app(config_class=Config, kafka_producer=None):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    kafka_producer.init_app(app)

    # Register blueprints
    # app.register_blueprint(challenge_bp, url_prefix='/api/challenges')

    return app