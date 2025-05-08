import os
from flask import Flask
import pytest

from exceptions.api_exceptions import InternalServerError, InvalidRequest
from exceptions.handlers import register_error_handler
from factory import create_app

def create_app():
    app = Flask(__name__)
    register_error_handler(app)
    
    @app.route('/invalid')
    def trigger_invalid_request():
        raise InvalidRequest("Missing required field")
    
    @app.route('/internal')
    def trigger_internal_error():
        raise InternalServerError("Unexpected DB failure")
    
    return app

@pytest.fixture
def client():
    app = create_app()
    return app.test_client()
