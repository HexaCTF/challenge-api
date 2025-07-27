from flask import Blueprint, jsonify, request, current_app

from challenge_api.utils.api_decorators import validate_request_body
from challenge_api.objects.challenge import ChallengeRequest
from challenge_api.exceptions.service import (
    BaseServiceException,
    InvalidInputValue
)

from sqlalchemy.exc import SQLAlchemyError
from kubernetes.client.rest import ApiException

challenge_bp = Blueprint('challenge', __name__)

@challenge_bp.route('', methods=['POST'])
@validate_request_body('challenge_id', 'user_id')
def create_challenge():
    container = current_app.container
    
    try:
        """사용자 챌린지 생성"""
        res = request.get_json()
        req = ChallengeRequest(**res)
        
        challenge = container.k8s_manager.create(req)
        
        return jsonify({'data' : {'port': challenge.port}}), 200
    except InvalidInputValue as e:
        return jsonify({
            'message': 'Invalid input value'
        }), 400 
    except BaseServiceException as e:
        return jsonify({
            'message' : 'Service Unavailable'
        }), 503
    except SQLAlchemyError as e:
        return jsonify({
            'message': 'Internal server error'
        }), 500 
    except ApiException as e:
        return jsonify({
            'message': 'External service error'
            }), 502
    except Exception as e:
        return jsonify({
            'message': 'Internal server error'
            }), 500
     

@challenge_bp.route('/delete', methods=['POST'])    
@validate_request_body('challenge_id', 'user_id')
def delete():
    """사용자 챌린지 삭제"""
    try:
        container = current_app.container
        
        res = request.get_json()
        challenge_info = ChallengeRequest(**res)
        
        # 사용자 챌린지 삭제 
        container.k8s_manager.delete(challenge_info)
                
        return jsonify({'message' : 'UserChallenge deleted successfully.'}), 200

    except BaseServiceException as e:
        return jsonify({
            'message' : 'Service Unavailable'
        }), 503
    except ApiException as e:
        return jsonify({
            'message': 'External service error'
            }), 502
    except Exception as e:
        return jsonify({
            'message': 'Internal server error'
            }), 500

@challenge_bp.route('/status', methods=['POST'])
@validate_request_body('challenge_id', 'user_id')
def get_status():
    """사용자 챌린지 최근 상태 조회"""
    try:
        container = current_app.container
        
        res = request.get_json()
        req = ChallengeRequest(**res)
                
        status = container.status_service.get_by_name(name=req.name)
        
        return jsonify({'data': {'port': status.port, 'status': status.status}}), 200
    except BaseServiceException as e:
        return jsonify({
            'message' : 'Service Unavailable'
        }), 503
    except Exception as e:
        return jsonify({
            'message': 'Internal server error'
            }), 500
 