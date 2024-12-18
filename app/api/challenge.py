from flask import Blueprint, jsonify, request

from app import extensions
from app.extensions.db.models import Challenge
from app.extensions.db.repository import ChallengeRepository
from app.extensions.k8s.client import K8sClient

challenge_bp = Blueprint('challenge', __name__)
repo = ChallengeRepository(extensions.db.connection, Challenge)


@challenge_bp.route('/<int:challenge_id>', methods=['POST'])
def create_challenge(challenge_id):
    try:
        # Get Metadata
        # * Session을 활용한 사용자 인증 추후 구현 예정
        data = request.get_json()
        user = data['user']

        # Create Challenge
        # store data in Docker Controller
        client = K8sClient()
        response = client.create_challenge_resource(challenge_id, user)
        print(response)

        return jsonify(response), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

