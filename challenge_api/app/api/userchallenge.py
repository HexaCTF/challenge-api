from flask import Blueprint, jsonify, request, current_app

from sqlalchemy.exc import SQLAlchemyError
from kubernetes.client.rest import ApiException

from challenge_api.utils.decorators import validate_request_body
from challenge_api.api.errors import (
    BadRequest,
    BadGateway,
    ServiceUnavailable,
    InternalServerError
)

userchallenge_bp = Blueprint('userchallenge', __name__)

@userchallenge_bp.route('', methods=['POST'])
@validate_request_body('challenge_id', 'user_id')
def create_challenge():

    try:
        """사용자 챌린지 생성"""
        res = request.get_json()
        req = ChallengeRequest(**res)
        
        # service 
        
        return jsonify({'data' : {'port': challenge.port}}), 200
    except InvalidInputValue as e:
        raise BadRequest(
            details = e.message
        )
    except BaseServiceException as e:
        raise ServiceUnavailable(
            details = e.message
        )
    except SQLAlchemyError as e:
        raise InternalServerError(
            details = e.message
        )
    except ApiException as e:
        raise BadGateway(
            details = e.message
        )
    except Exception as e:
        raise InternalServerError(
            details = e.message
        )
     

# @challenge_bp.route('/delete', methods=['POST'])    
# @validate_request_body('challenge_id', 'user_id')
# def delete():
#     """사용자 챌린지 삭제"""
#     try:
#         container = current_app.container
        
#         res = request.get_json()
#         challenge_info = ChallengeRequest(**res)
        
#         # 사용자 챌린지 삭제 
#         container.k8s_manager.delete(challenge_info)
                
#         return jsonify({'message' : 'UserChallenge deleted successfully.'}), 200

#     except BaseServiceException as e:
#         return jsonify({
#             'message' : 'Service Unavailable'
#         }), 503
#     except ApiException as e:
#         return jsonify({
#             'message': 'External service error'
#             }), 502
#     except Exception as e:
#         return jsonify({
#             'message': 'Internal server error'
#             }), 500

# @challenge_bp.route('/status', methods=['POST'])
# @validate_request_body('challenge_id', 'user_id')
# def get_status():
#     """사용자 챌린지 최근 상태 조회"""
#     try:
#         container = current_app.container
        
#         res = request.get_json()
#         req = ChallengeRequest(**res)
                
#         status = container.status_service.get_by_name(name=req.name)
        
#         return jsonify({'data': {'port': status.port, 'status': status.status}}), 200
#     except BaseServiceException as e:
#         return jsonify({
#             'message' : 'Service Unavailable'
#         }), 503
#     except Exception as e:
#         return jsonify({
#             'message': 'Internal server error'
#             }), 500
 