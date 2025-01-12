import logging
from typing import Any, Dict
from app.extensions.db.repository import UserChallengesRepository

logger = logging.getLogger(__name__)

class MessageHandler:
    VALID_STATUSES = {'Creating', 'Running', 'Deleted', 'Error'}

    @staticmethod
    def validate_message(message: Dict[str, Any]) -> tuple[str, str, str, str]:
        """
        Validate message and extract fields

        Args:
            message: Kafka message

        Returns:
            Tuple of (username, problem_id, new_status, timestamp)
        """
        try:
            username = message.user
            problem_id = message.problemId
            new_status = message.newStatus
            timestamp = message.timestamp
        except AttributeError:
            username = message['user']
            problem_id = message['problemId']
            new_status = message['newStatus']
            timestamp = message['timestamp']

        if not all([username, problem_id, new_status, timestamp]):
            raise ValueError(f"Missing required fields in message: {message}")

        if new_status not in MessageHandler.VALID_STATUSES:
            raise ValueError(f"Invalid status type: {new_status}")

        return username, problem_id, new_status, timestamp

    @staticmethod
    def handle_message(message: Dict[str, Any]):
        """
        Handle consumed Kafka message
        Args:
            message: Kafka message
        """
        try:
            username, challenge_id, new_status, _ = MessageHandler.validate_message(message)
            
            # Create repository with current session
            repo = UserChallengesRepository()
            
            challenge_name = challenge_name = f"challenge-{challenge_id}-{username}"
            
            challenge = repo.get_by_user_challenge_name(challenge_name)
            
            success = repo.update_status(challenge, new_status)
            if not success:
                raise ValueError(f"Failed to update challenge status: {challenge_name}")
        
        except ValueError as e:
            logger.warning(f"Invalid message format: {str(e)}")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}", exc_info=True)
            # Optionally re-raise if you want the error to propagate
            raise
