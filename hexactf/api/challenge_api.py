from json import JSONDecodeError
from logging import log
from flask import Blueprint, jsonify, request
import yaml

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

def modify_k8s_yaml(yaml_content, username, challenge_id):
    """Modify the Kubernetes YAML content to include unique identifiers."""
    resources = yaml.safe_load(yaml_content)
    
    if not isinstance(resources, list):
        resources = [resources]
    
    modified_resources = []
    
    for resource in resources:
        if 'metadata' in resource:
            # Modify name to include username and challenge_id
            if 'name' in resource['metadata']:
                resource['metadata']['name'] = f"{resource['metadata']['name']}-{username}-{challenge_id}"
            
            # Add labels
            if 'labels' not in resource['metadata']:
                resource['metadata']['labels'] = {}
            resource['metadata']['labels'].update({
                'username': username,
                'challenge_id': challenge_id
            })
        
        modified_resources.append(resource)
    
    return yaml.safe_dump_all(modified_resources)

@challenge_bp.route('/generate', methods=['POST'])
def generate_yaml():
    """API endpoint to modify and return Kubernetes YAML with user-specific values."""
    try:
        data = request.json
        username = data.get('username')
        challenge_id = data.get('challenge_id')
        yaml_file = data.get('yaml_file')
        
        if not all([username, challenge_id, yaml_file]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        modified_yaml = modify_k8s_yaml(yaml_file, username, challenge_id)
        
        return jsonify({'modified_yaml': modified_yaml})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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