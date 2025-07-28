
import pytest
import json
from datetime import datetime
from unittest.mock import Mock

from flask import Flask, Blueprint, request

from challenge_api.app.api.errors import (
    BaseHttpException,
    BadRequest,
    create_error_response,
    handle_http_exception
)

def test_base_http_exception():
    # arrange
    message = "test error message"
    status_code = 500
    details = "test details"
    
    # act
    exception = BaseHttpException(
        message=message,
        status_code=status_code,
        details=details
    )
    
    # assert
    assert exception.message == message
    assert exception.status_code == status_code
    assert exception.details == details

def test_base_http_exception_without_message():
    # arrange
    status_code = 500
    details = "test details"
    
    # act
    exception = BaseHttpException(
        status_code=status_code,
        details=details
    )
    
    # assert
    assert exception.message == "An unexpected error occurred"
    assert exception.status_code == status_code
    assert exception.details is details

def test_base_http_exception_without_status_code():
    # arrange
    message = "test message"
    details = "test details"
    
    # act
    exception = BaseHttpException(
        message=message,
        details=details
    )
    
    # assert
    assert exception.message == message
    assert exception.status_code == 500
    assert exception.details is details 

def test_base_http_exception_without_details():
    # arrange
    message = "test error message"
    status_code = 500
    
    # act
    exception = BaseHttpException(
        message=message,
        status_code=status_code,
    )
    
    # assert
    assert exception.message == message
    assert exception.status_code == status_code
    assert exception.details is None 

def test_bad_request():
    # arrange
    message = "Invalid input"
    details = "Field validation failed"
    
    #act
    exception = BadRequest(message, details)
    
    # assert
    assert exception.message == message
    assert exception.status_code == 400
    assert exception.details == details

def test_bad_request_without_message():
    # arrange
    details = "Field validation failed"
    
    # act
    exception = BadRequest(details=details)
    
    # assert
    assert exception.message == "Bad request"
    assert exception.status_code == 400
    assert exception.details == details

@pytest.fixture
def app():
    app = Flask(__name__)
    v1 = Blueprint('v1', __name__)
    
    # 에러 핸들러 등록
    @v1.errorhandler(BaseHttpException)
    def error_handler(error):
        return handle_http_exception(error)
    
    app.register_blueprint(v1)
    return app

def test_create_error_response(app):
    with app.app_context():
        # arrange
        message = "Test error"
        status_code = 400
        
        # act & assert    
        response, code = create_error_response(message, status_code)    
        assert code == status_code
        
        data = json.loads(response.get_data(as_text=True))
        assert data['error']['message'] == message
        assert 'timestamp' in data
        
        timestamp = datetime.fromisoformat(data['timestamp'])
        assert isinstance(timestamp, datetime)

def test_handle_http_exception(mocker,app):
    with app.test_request_context('/api/users/123', method='GET'):
        # arrange
        mock_current_app = mocker.patch('challenge_api.app.api.errors.current_app') # module level patch
        mock_create_error_response = mocker.patch('challenge_api.app.api.errors.create_error_response')
        
        mock_logger = Mock()
        mock_current_app.logger = mock_logger
        
        mock_create_error_response.return_value = ("mocked_response", 400)
        
        # act
        error = BadRequest(message = "Invalid user ID", details = "ID does not exist")
        result = handle_http_exception(error)
        
        # assert
        mock_logger.error.assert_called_once_with(
            "Error: Invalid user ID",
            extra={
                'error_type': 'BadRequest',
                'status_code': 400,
                'endpoint': None,  # test_request_context에서는 endpoint가 None
                'method': 'GET',
                'url': 'http://localhost/api/users/123',
                'remote_addr': None , # test context에서는 remote_addr이 None
                'details': 'ID does not exist'
            }
        )
        
        mock_create_error_response.assert_called_once_with(
            message="Invalid user ID",
            status_code=400
        )
        
        assert result == ("mocked_response", 400)
        
def test_handle_http_exception_without_details(mocker, app):
    """HTTP 예외 처리 테스트"""
    with app.test_request_context('/api/users/123', method='GET'):
        # arrange
        mock_current_app = mocker.patch('challenge_api.app.api.errors.current_app') # module level patch
        mock_create_error_response = mocker.patch('challenge_api.app.api.errors.create_error_response')
        
        mock_logger = Mock()
        mock_current_app.logger = mock_logger
        
        mock_create_error_response.return_value = ("mocked_response", 400)
        
        # act
        error = BadRequest("Invalid user ID")
        result = handle_http_exception(error)
        
        # assert
        mock_logger.error.assert_called_once_with(
            "Error: Invalid user ID",
            extra={
                'error_type': 'BadRequest',
                'status_code': 400,
                'endpoint': None,  # test_request_context에서는 endpoint가 None
                'method': 'GET',
                'url': 'http://localhost/api/users/123',
                'remote_addr': None  # test context에서는 remote_addr이 None
            }
        )
        
        mock_create_error_response.assert_called_once_with(
            message="Invalid user ID",
            status_code=400
        )
        
        assert result == ("mocked_response", 400)
