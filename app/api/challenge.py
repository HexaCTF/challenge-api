from flask import Blueprint, jsonify, request

from app import extensions
from app.extensions.db.models import Challenge
from app.extensions.db.repository import ChallengeRepository

challenge_bp = Blueprint('challenge', __name__)
repo = ChallengeRepository(extensions.db.connection, Challenge)


@challenge_bp.route('/<int:challenge_id>', methods=['POST'])
def create_challenge(challenge_id):
    try:
        # * Session을 활용한 사용자 인증 추후 구현 예정
        data = request.get_json()
        user = data['user']
        status = generate_challenge(challenge_id, user)
        return jsonify({'status':'Success'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

