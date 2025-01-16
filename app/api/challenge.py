from json import JSONDecodeError
from logging import log
from flask import Blueprint, jsonify, request

from app.exceptions.api import InvalidRequest
from app.exceptions.userchallenge import UserChallengeCreationError, UserChallengeDeletionError, UserChallengeNotFoundError
from app.extensions.db.repository import UserChallengesRepository
from app.extensions.k8s.client import K8sClient

challenge_bp = Blueprint('challenge', __name__)

@challenge_bp.route('', methods=['POST'])
def create_challenge():
    """사용자 챌린지 생성"""
    try:        
        # Challenge 관련 정보 가져오기 
        res = request.get_json()
        if not res:
           raise InvalidRequest("Request body is empty or not valid JSON")

        if 'challenge_id' not in res:
            raise InvalidRequest("Required field 'challenge_id' is missing in request")
        
        challenge_id = res['challenge_id']
        
        if 'username' not in res:
            raise InvalidRequest("Required field 'username' is missing in request")
        username = res['username']

        # 챌린지 생성 
        client = K8sClient()
        endpoint = client.create_challenge_resource(challenge_id, username)
        if endpoint:
            return jsonify({'data' : {'port': endpoint}}), 200
        return UserChallengeCreationError(f"Faile to create challenge {challenge_id} for user {username}")
    
    except Exception as e:
        raise UserChallengeCreationError(str(e)) from e 

@challenge_bp.route('/delete', methods=['POST'])    
def delete_userchallenges():
    try:
        """
        사용자 챌린지 삭제 
        """
        # Challenge 관련 정보 가져오기 
        res = request.get_json()
        if not res:
            log.error("No data provided")
            raise UserChallengeDeletionError()

        if 'challenge_id' not in res:
            log.error("No challenge_id provided")
            raise InvalidRequest()
        challenge_id = res['challenge_id']
        
        if 'username' not in res:
            log.error("No username provided")
            raise InvalidRequest()
        username = res['username']
        
        # 사용자 챌린지 삭제 
        client = K8sClient()
        client.delete_userchallenge(username, challenge_id)
        
        return jsonify({'message' : '챌린지가 정상적으로 삭제되었습니다.'}), 200
    except JSONDecodeError as e:
        log.error("Invalid request format")
        raise InvalidRequest() from e
    except Exception as e:
        raise UserChallengeDeletionError() from e

@challenge_bp.route('/status', methods=['POST'])
def get_userchallenge_status():
    """ 사용자 챌린지 상태 조회 """
    try:
        # Challenge 관련 정보 가져오기
        res = request.get_json()
        if not res:
            log.error("No data provided")
            raise UserChallengeDeletionError()

        if 'challenge_id' not in res:
            log.error("No challenge_id provided")
            raise InvalidRequest()
        challenge_id = res['challenge_id']

        if 'username' not in res:
            log.error("No username provided")
            raise InvalidRequest()
        username = res['username']

        # 사용자 챌린지 상태 조회
        repo = UserChallengesRepository()
        status = repo.get_status(challenge_id, username)
        if status is None:
            raise UserChallengeNotFoundError()
        return jsonify({'data': {'status': status}}), 200
    except Exception as e:
        raise UserChallengeNotFoundError() from e