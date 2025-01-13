from json import JSONDecodeError
from logging import log
from flask import Blueprint, jsonify, request

from app.exceptions.api import InvalidRequest
from app.exceptions.userchallenge import UserChallengeCreationError, UserChallengeDeletionError
from app.extensions.k8s.client import K8sClient

challenge_bp = Blueprint('challenge', __name__)

# *TEST : Challenge 생성 서버의 테스트 URL  
GLOBAL_URL = 'http://127.0.0.1'

@challenge_bp.route('/', methods=['POST'])
def create_challenge():
    """사용자 챌린지 생성"""
    try:        
        # Challenge 관련 정보 가져오기 
        res = request.get_json()
        if not res:
           raise InvalidRequest()

        if 'challenge_id' not in res:
            raise InvalidRequest()
        
        challenge_id = res['challenge_id']
        
        # TODO(-) : Session을 활용한 사용자 정보 가져오기 
        if 'username' not in res:
            log.error("No username provided")
            raise InvalidRequest()
        username = res['username']

        # 챌린지 생성 
        client = K8sClient()
        endpoint = client.create_challenge_resource(challenge_id, username)
        if endpoint:
            return jsonify({'data' : {'url' : GLOBAL_URL, 'port': endpoint}}), 200
        return UserChallengeCreationError()
    
    except Exception as e:
        raise UserChallengeCreationError() from e 

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
        
        # TODO(-) : Session을 활용한 사용자 정보 가져오기 
        if 'username' not in res:
            log.error("No username provided")
            raise InvalidRequest()
        username = res['username']
        
        # 사용자의 모든 챌린지 삭제 
        client = K8sClient()
        client.delete_userchallenge(username, challenge_id)
        
        return jsonify({'message' : '챌린지가 정상적으로 삭제되었습니다.'}), 200
    except JSONDecodeError as e:
        log.error("Invalid request format")
        raise InvalidRequest() from e
    except Exception as e:
        raise UserChallengeDeletionError() from e