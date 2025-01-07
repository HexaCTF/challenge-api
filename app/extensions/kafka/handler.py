import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageHandler:
    @staticmethod
    def handle_message(message):
        """
        Handle incoming Kafka messages from Go producer

        Args:
            message (dict): Message with userId, problemId, newStatus, timestamp
        """
        try:
            # 데이터 필드 추출 
            user_id = message.get('userId')
            problem_id = message.get('problemId')
            new_status = message.get('newStatus')
            timestamp = message.get('timestamp')

            if not all([user_id, problem_id, new_status, timestamp]):
                logger.warning(f"Missing required fields in message: {message}")
                return

            # 상태값을 저장하는 메서드 호출
            if new_status == "Created" or new_status == "Running" or new_status == "Completed" or new_status == "Error":
                MessageHandler._handle_save_status(user_id, problem_id, new_status, timestamp)
            else:
                logger.warning(f"Unknown status type: {new_status}")

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            # Don't raise the exception - we want to continue processing messages

    @staticmethod
    def _handle_save_status(user_id, problem_id, new_status, timestamp):
        """상태값을 데이터베이스에 저장하는 메소드"""
        # TODO - Create a new userChallenge Object to save the status
        
        pass 
