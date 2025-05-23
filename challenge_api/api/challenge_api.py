from json import JSONDecodeError
from logging import log
from flask import Blueprint, jsonify, request

from challenge_api.db.repository import UserChallengesRepository, UserChallengeStatusRepository
from challenge_api.extensions.k8s.client import K8sClient
from challenge_api.utils.api_decorators import validate_request_body
from challenge_api.objects.challenge import ChallengeRequest

challenge_bp = Blueprint('challenge', __name__)

@challenge_bp.route('', methods=['POST'])
@validate_request_body('challenge_id', 'user_id')
def create_challenge():
    """사용자 챌린지 생성"""
    # Challenge 관련 정보 가져오기 
    res = request.get_json()
    body = ChallengeRequest(**res)
    
    # 챌린지 생성 
    client = K8sClient()
    endpoint = client.create(data=body)
    if not endpoint:
        raise UserChallengeCreationError(error_msg=f"Failed to create challenge {challenge_info.challenge_id} for user {challenge_info.name} : Endpoint did not exist")
    
    return jsonify({'data' : {'port': endpoint}}), 200

@challenge_bp.route('/delete', methods=['POST'])    
@validate_request_body('challenge_id', 'user_id')
def delete_userchallenges():
    """사용자 챌린지 삭제"""
    try:
        res = request.get_json()
        challenge_info = ChallengeInfo(**res)
        
        # 사용자 챌린지 삭제 
        client = K8sClient()
        client.delete(challenge_info)
                
        return jsonify({'message' : '챌린지가 정상적으로 삭제되었습니다.'}), 200
    except JSONDecodeError as e:
        log.error("Invalid request format")
        raise InvalidRequest(error_msg=str(e)) from e

@challenge_bp.route('/status', methods=['POST'])
@validate_request_body('challenge_id', 'user_id')
def get_userchallenge_status():
    """사용자 챌린지 최근 상태 조회"""
    try:
        res = request.get_json()
        challenge_info = ChallengeInfo(**res)
                
        # 사용자 챌린지 상태 조회
        userchallenge_repo = UserChallengesRepository()
        userchallenge = userchallenge_repo.get_by_user_challenge_name(challenge_info.name)
        
        repo = UserChallengeStatusRepository()
        status = repo.get_recent_status(userchallenge.idx)
        return jsonify({'data': {'port': status.port, 'status': status.status}}), 200
    except Exception as e:
        raise UserChallengeNotFoundError(error_msg=str(e))