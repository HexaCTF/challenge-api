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
            logger.error(f"Missing required fields in message: {message}")
            raise QueueProcessingError()

        if new_status not in MessageHandler.VALID_STATUSES:
            logger.error(f"Invalid status type: {new_status}")
            raise QueueProcessingError()

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
            
            challenge_name = challenge_name = f"challenge-{challenge_id}-{username}"
            
            # 상태 정보 업데이트
            repo = UserChallengesRepository()
            challenge = repo.get_by_user_challenge_name(challenge_name)
            success = repo.update_status(challenge, new_status)
            if not success:
                logger.error(f"Failed to update challenge status: {challenge_name}")
                raise QueueProcessingError()
        
        except ValueError as e:
            logger.warning(f"Invalid message format: {str(e)}")
            raise QueueProcessingError() from e 
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}", exc_info=True)
            raise QueueProcessingError() from e
