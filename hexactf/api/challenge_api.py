from json import JSONDecodeError
from logging import log
from flask import Blueprint, jsonify, request

from hexactf.exceptions.api_exceptions import InvalidRequest
from hexactf.exceptions.userchallenge_exceptions import UserChallengeCreationError, UserChallengeDeletionError, UserChallengeNotFoundError
from hexactf.extensions.db.repository import UserChallengesRepository
from hexactf.extensions.k8s.client import K8sClient

challenge_bp = Blueprint('challenge', __name__)

@challenge_bp.route('', methods=['POST'])
def create_challenge():
    """사용자 챌린지 생성"""
   # Challenge 관련 정보 가져오기 
    res = request.get_json()
    if not res:
        raise InvalidRequest(error_msg="Request body is empty or not valid JSON")
    if 'challenge_id' not in res:
        raise InvalidRequest(error_msg="Required field 'challenge_id' is missing in request")

    challenge_id = res['challenge_id']

    if 'username' not in res:
        raise InvalidRequest(error_msg="Required field 'username' is missing in request")
    username = res['username']
    # 챌린지 생성 
    client = K8sClient()
    endpoint = client.create_challenge_resource(challenge_id, username)
    if not endpoint:
        raise  UserChallengeCreationError(error_msg=f"Failed to create challenge {challenge_id} for user {username} : Endpoint did not exist")
    
    return jsonify({'data' : {'port': endpoint}}), 200

@challenge_bp.route('/delete', methods=['POST'])    
def delete_userchallenges():
    try:
        """
        사용자 챌린지 삭제 
        """
        # Challenge 관련 정보 가져오기 
        res = request.get_json()
        if not res:
            raise UserChallengeDeletionError(error_msg="Request body is empty or not valid JSON")

        if 'challenge_id' not in res:
            raise InvalidRequest(error_msg="Required field 'challenge_id' is missing in request")
        challenge_id = res['challenge_id']
        
        if 'username' not in res:
            raise InvalidRequest(error_msg="Required field 'username' is missing in request")
        username = res['username']
        
        # 사용자 챌린지 삭제 
        client = K8sClient()
        client.delete_userchallenge(username, challenge_id)
                
        return jsonify({'message' : '챌린지가 정상적으로 삭제되었습니다.'}), 200
    except JSONDecodeError as e:
        log.error("Invalid request format")
        raise InvalidRequest(error_msg=str(e)) from e

@challenge_bp.route('/status', methods=['POST'])
def get_userchallenge_status():
    """ 사용자 챌린지 상태 조회 """
    try:
        # Challenge 관련 정보 가져오기
        res = request.get_json()
        if not res:
            raise InvalidRequest(error_msg="Request body is empty or not valid JSON")

        if 'challenge_id' not in res:
            raise InvalidRequest(error_msg="Required field 'challenge_id' is missing in request")
        
        challenge_id = res['challenge_id']
        if not challenge_id:
            raise InvalidRequest(error_msg="'challenge_id' is empty or not valid")

        if 'username' not in res:
            raise InvalidRequest(error_msg="Required field 'username' is missing in request")
    
        username = res['username']
        if not username:
            raise InvalidRequest(error_msg="'username' is empty or not valid")
                
        # 사용자 챌린지 상태 조회
        repo = UserChallengesRepository()
        status_dict = repo.get_status(challenge_id, username)
        if status_dict is None:
            raise UserChallengeNotFoundError(error_msg=f"User challenge not found for {username} and {challenge_id}")
        return jsonify({'data': status_dict}), 200
    except Exception as e:
        raise UserChallengeNotFoundError(error_msg=str(e))