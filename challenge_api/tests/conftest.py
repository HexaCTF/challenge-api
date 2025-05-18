import pytest
from challenge_api import create_app

@pytest.fixture
def app():
    app = create_app()
    return app

@pytest.fixture
def app_context(app):
    with app.app_context():
        yield
