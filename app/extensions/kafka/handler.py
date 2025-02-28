import logging
from typing import Any, Dict
from app.exceptions.kafka import QueueProcessingError
from app.extensions.db.repository import UserChallengesRepository

logger = logging.getLogger(__name__)

class MessageHandler:
    VALID_STATUSES = {'Creating', 'Running', 'Deleted', 'Error'}

    @staticmethod
    def validate_message(message: Dict[str, Any]) -> tuple[str, str, str, str]:
        """
        Kafka 메세지의 필수 필드를 검증하고 반환
        
        Args:
            message (Dict[str, Any]): Kafka 메세지
        
        Returns:
            tuple[str, str, str, str]: 사용자 이름, 챌린지 ID, 새로운 상태, 타임스탬프
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
            raise QueueProcessingError(error_msg=f"Kafka Error : Missing required fields in message: {message}")

        if new_status not in MessageHandler.VALID_STATUSES:
            raise QueueProcessingError(error_msg=f"Kafka Error : Invalid status in message: {new_status}")

        return username, problem_id, new_status, timestamp

    @staticmethod
    def handle_message(message: Dict[str, Any]):
        """
        Consume한 Kafka message 내용을 DB에 반영

        Args:
            message: Kafka 메세지        
        """
        try:
            username, challenge_id, new_status, _ = MessageHandler.validate_message(message)
            challenge_name = challenge_name = f"challenge-{challenge_id}-{username.lower()}"
            
            # 상태 정보 업데이트
            repo = UserChallengesRepository()
            user_challenge = repo.get_by_user_challenge_name(challenge_name)
            logger.debug(f"Found user challenge {challenge_name} : {user_challenge}")
            if user_challenge is None:
                repo.create(username, challenge_id, challenge_name, 0, new_status)
            logger.debug(f"Updating status of challenge {challenge_name} to {new_status}")
            
            success = repo.update_status(user_challenge, new_status)
            if not success:
                raise QueueProcessingError(error_msg=f"Kafka Error : Failed to update challenge status: {challenge_name}")
        
        except ValueError as e:
            raise QueueProcessingError(error_msg=f"Invalid message format {str(e)}") from e 
        except Exception as e:
            raise QueueProcessingError(error_msg=f"Kafka Error: {str(e)}") from e
