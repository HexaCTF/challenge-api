import pytest
from unittest.mock import MagicMock
from flask import Flask

from challenge_api.api.challenge_api import challenge_bp
from challenge_api.exceptions.service import (
    InvalidInputValue,
    BaseServiceException,
    UserChallengeCreationException,
    ChallengeStatusNotFound,
)
from challenge_api.objects.usrchallenge import UChallengeStatus
from sqlalchemy.exc import SQLAlchemyError
from kubernetes.client.rest import ApiException


@pytest.fixture
def client():
    app = Flask(__name__)
    app.config['TESTING'] = True

    # MagicMock으로 DI 컨테이너 구성
    mock_container = MagicMock()
    app.container = mock_container

    # Blueprint 등록
    app.register_blueprint(challenge_bp, url_prefix='/challenge')

    with app.app_context():
        with app.test_client() as test_client:
            # 클라이언트와 컨테이너를 함께 리턴
            yield test_client, mock_container

"""
/create 
"""
def test_create_challenge_success(client):
    test_client, mock_container = client

    mock_response = MagicMock()
    mock_response.port = 12345
    mock_container.k8s_manager.create.return_value = mock_response

    payload = {'challenge_id': 1, 'user_id': 101}
    response = test_client.post('/challenge', json=payload)

    assert response.status_code == 200
    assert response.json['data']['port'] == 12345
    mock_container.k8s_manager.create.assert_called_once()


def test_create_challenge_service_userchallenge_exception(client):
    test_client, mock_container = client

    mock_container.k8s_manager.create.side_effect = UserChallengeCreationException(message='something happen')

    payload = {'challenge_id': 1, 'user_id': 101}
    response = test_client.post('/challenge', json=payload)

    assert response.status_code == 503
    assert response.json['message'] == 'Service Unavailable'


def test_create_challenge_service_base_service_exception(client):
    test_client, mock_container = client

    mock_container.k8s_manager.create.side_effect = BaseServiceException(message='something happen')
    payload = {'challenge_id': 1, 'user_id': 101}
    response = test_client.post('/challenge', json=payload)

    assert response.status_code == 503
    assert response.json['message'] == 'Service Unavailable'

def test_create_challenge_sqlalchemy_error(client):
    test_client, mock_container = client

    mock_container.k8s_manager.create.side_effect = SQLAlchemyError()

    payload = {'challenge_id': 1, 'user_id': 101}
    response = test_client.post('/challenge', json=payload)

    assert response.status_code == 500
    assert response.json['message'] == 'Internal server error'


def test_create_challenge_apiexception(client):
    test_client, mock_container = client

    mock_container.k8s_manager.create.side_effect = ApiException()

    payload = {'challenge_id': 1, 'user_id': 101}
    response = test_client.post('/challenge', json=payload)

    assert response.status_code == 502
    assert response.json['message'] == 'External service error'


def test_create_challenge_generic_exception(client):
    test_client, mock_container = client

    mock_container.k8s_manager.create.side_effect = Exception("Unexpected error")

    payload = {'challenge_id': 1, 'user_id': 101}
    response = test_client.post('/challenge', json=payload)

    assert response.status_code == 500
    assert response.json['message'] == 'Internal server error'


"""
/delete
"""
def test_delete_success(client):
    test_client, mock_container = client

    # success k8s manager return value 
    mock_container.k8s_manager.delete.return_value = None
    
    payload = {'challenge_id': 1, 'user_id': 101}
    response = test_client.post('/challenge/delete', json=payload)
    
    assert response.status_code == 200
    
def test_delete_invalid_input(client):
    test_client, mock_container = client

    mock_container.k8s_manager.delete.side_effect = InvalidInputValue(message='error')
    
    payload = {'challenge_id': 1, 'user_id': 101}
    response = test_client.post('/challenge/delete', json=payload)
    
    assert response.status_code == 503
    assert response.json['message'] == 'Service Unavailable'

def test_delete_k8s_delete_error(client):
    test_client, mock_container = client

    mock_container.k8s_manager.delete.side_effect = ApiException()
    
    payload = {'challenge_id': 1, 'user_id': 101}
    response = test_client.post('/challenge/delete', json=payload)
    
    assert response.status_code == 502
    assert response.json['message'] == 'External service error'

def test_delete_generic_exception(client):
    test_client, mock_container = client

    mock_container.k8s_manager.delete.side_effect = Exception("Unexpected error")

    payload = {'challenge_id': 1, 'user_id': 101}
    response = test_client.post('/challenge/delete', json=payload)

    assert response.status_code == 500
    assert response.json['message'] == 'Internal server error'

# /status

def test_get_status_success(client):
    # Given 
    test_client, mock_container = client
    
    mock_container.status_service.get_by_name.return_value = UChallengeStatus(
        userchallenge_idx = 1,
        port = 8080,
        status= 'running'
    )
    
    # When
    payload = {'challenge_id': 1, 'user_id': 101}
    response = test_client.post('/challenge/status', json=payload)
    
    assert response.status_code == 200
    assert response.json['data']['port'] == 8080
    assert response.json['data']['status'] == 'running'
    
    
def test_get_status_not_found(client):
    test_client, mock_container = client
    
    mock_container.status_service.get_by_name.side_effect = ChallengeStatusNotFound(
        message = 'Not Found'    
    )
    
    payload = {'challenge_id': 1, 'user_id': 101}
    response = test_client.post('/challenge/status', json=payload)
    
    assert response.status_code == 503
    assert response.json['message'] == 'Service Unavailable'
    

    
    
    
    
    
    
    