from flask import Blueprint, jsonify, request

from app.extensions.db.models import Challenge
from app.extensions.db.repository import ChallengeRepository

bp = Blueprint('challenge', __name__)
repo = ChallengeRepository(extensions.db.connection, Challenge)


@bp.route('/<int:challenge_id>', methods=['GET'])
def get_challenge(challenge_id):
    try:
        challenge = repo.find_by_id(challenge_id)
        if not challenge:
            return jsonify({'error': 'Challenge not found'}), 404

        # Send event to Kafka
        kafka_producer.producer.send_event(
            'challenge_viewed',
            {'challenge_id': challenge_id}
        )

        return jsonify(challenge.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/', methods=['POST'])
def create_challenge():
    try:
        data = request.get_json()
        challenge = Challenge(**data)

        if repo.create(challenge):
            kafka_producer.producer.send_event(
                'challenge_created',
                challenge.to_dict()
            )
            return jsonify(challenge.to_dict()), 201
        else:
            return jsonify({'error': 'Failed to create challenge'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:challenge_id>', methods=['PUT'])
def update_challenge(challenge_id):
    try:
        data = request.get_json()
        challenge = Challenge(**data)

        if repo.update(challenge_id, challenge):
            kafka_producer.producer.send_event(
                'challenge_updated',
                {'challenge_id': challenge_id, **challenge.to_dict()}
            )
            return jsonify(challenge.to_dict())
        else:
            return jsonify({'error': 'Challenge not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:challenge_id>', methods=['DELETE'])
def delete_challenge(challenge_id):
    try:
        if repo.delete(challenge_id):
            kafka_producer.producer.send_event(
                'challenge_deleted',
                {'challenge_id': challenge_id}
            )
            return '', 204
        else:
            return jsonify({'error': 'Challenge not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
