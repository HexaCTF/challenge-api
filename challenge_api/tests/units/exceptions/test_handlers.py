from exceptions.error_types import ApiErrorTypes


def test_invalid_request_handler(client):
    response = client.get('/invalid')
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data == {
        'error': {
            'code': ApiErrorTypes.INVALID_REQUEST,
            'message': "Invalid request format",
        }
    }

def test_internal_server_error_handler(client):
    response = client.get('/internal')
    assert response.status_code == 500
    json_data = response.get_json()
    assert json_data == {
        'error': {
            'code': ApiErrorTypes.INTERNAL_SERVER_ERROR,
            'message': "An unexpected error occurred",
        }
    }