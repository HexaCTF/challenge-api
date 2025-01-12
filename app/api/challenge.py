from flask import Blueprint, jsonify, request

from app.extensions.k8s.client import K8sClient

challenge_bp = Blueprint('challenge', __name__)

# *TEST : Challenge 생성 서버의 테스트 URL  
GLOBAL_URL = 'http://127.0.0.1'


@challenge_bp.route('/', methods=['POST'])
def create_challenge():
    try:
        """
        Challenge 필수사항
        - Challenge 정보 데이터베이스에 저장 
        - Challenge의 상태가 실행중이라면 실행중인 컨테이너의 정보(URL, 포트번호 등)을 반환
        """
        
        # Challenge 관련 정보 가져오기 
        # TODO(-) : Session을 활용한 사용자 정보 가져오기 
        username = "test" # 테스트용 사용자 이름
        res = request.get_json()
        if not res:
           return jsonify({'error': 'No data provided'}), 400

        if 'challenge_id' not in res:
            return jsonify({'error': 'No challenge_id provided'}), 400
        
        challenge_id = res['challenge_id']
        
        # 챌린지 생성 
        client = K8sClient()
        endpoint = client.create_challenge_resource(challenge_id, username)
        if endpoint:
            return jsonify({'data' : {'url' : GLOBAL_URL, 'port': endpoint}}), 200
        return jsonify({'error': 'Failed to create challenge'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@challenge_bp.route('/delete', methods=['POST'])    
def delete_userchallenges():
    try:
        """
        사용자의 모든 챌린지 삭제 
        """
        # Challenge 관련 정보 가져오기 
        # TODO(-) : Session을 활용한 사용자 정보 가져오기 
        username = "test" # 테스트용 사용자 이름
        res = request.get_json()
        if not res:
           return jsonify({'error': 'No data provided'}), 400

        # Get Challenge_id
        if 'challenge_id' not in res:
            return jsonify({'error': 'No challenge_id provided'}), 400
        challenge_id = res['challenge_id']
        
        # 사용자의 모든 챌린지 삭제 
        client = K8sClient()
        client.delete_userchallenge(username, challenge_id)
        
        return jsonify({'message' : '챌린지가 정상적으로 삭제되었습니다.'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500