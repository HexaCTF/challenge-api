from functools import wraps
from flask import request
from challenge_api.exceptions.service import InvalidInputValue

def validate_request_body(*required_fields):
    """
    Request body의 유효성을 검사하는 데코레이터
    
    Args:
        required_fields: 필수로 존재해야 하는 필드명들
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            res = request.get_json()
            if not res:
                raise InvalidInputValue(error_msg="Request body is empty or not valid JSON")
            
            for field in required_fields:
                if field not in res:
                    raise InvalidInputValue(error_msg=f"Required field '{field}' is missing in request")
                if not res[field]:
                    raise InvalidInputValue(error_msg=f"'{field}' is empty or not valid")
                    
            return f(*args, **kwargs)
        return decorated_function
    return decorator 