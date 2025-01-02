from flask import Blueprint, jsonify, request

from app import extensions
from app.extensions.k8s.client import K8sClient

challenge_bp = Blueprint('challenge', __name__)


@challenge_bp.route('/<int:challenge_id>', methods=['POST'])
def create_challenge(challenge_id):
    try:
        """
        Challenge 필수사항
        - Challenge 정보 데이터베이스에 저장 
        - Challenge의 상태가 실행중이라면 실행중인 컨테이너의 정보(URL, 포트번호 등)을 반환
        """        
       
        
        # * 쿠버네티스는 추후 추가 예정 
        # Create Challenge
        # store data in Docker Controller
        # client = K8sClient()
        # response = client.create_challenge_resource(challenge_id, user)
        # print(response)

        return jsonify("Hello world"), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
