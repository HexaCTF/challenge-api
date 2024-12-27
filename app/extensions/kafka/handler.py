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
            # Extract data from the Go-produced StatusMessage
            user_id = message.get('userId')
            problem_id = message.get('problemId')
            new_status = message.get('newStatus')
            timestamp = message.get('timestamp')

            if not all([user_id, problem_id, new_status, timestamp]):
                logger.warning(f"Missing required fields in message: {message}")
                return

            # Log the received message
            logger.info(f"Received status update - User: {user_id}, Problem: {problem_id}, Status: {new_status}")

            # Handle different status types
            if new_status == "Created":
                MessageHandler._handle_created_status(user_id, problem_id, timestamp)
            elif new_status == "Deleted":
                MessageHandler._handle_deleted_status(user_id, problem_id, timestamp)
            else:
                logger.warning(f"Unknown status type: {new_status}")

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            # Don't raise the exception - we want to continue processing messages

    @staticmethod
    def _handle_created_status(user_id, problem_id, timestamp):
        """Handle Created status"""
        logger.info(f"Challenge {problem_id} has been created for user {user_id}")
        print("\n=== Challenge Created ===")
        print(f"User: {user_id}")
        print(f"Problem: {problem_id}")
        print(f"Time: {timestamp}")
        print("=======================\n")

    @staticmethod
    def _handle_deleted_status(user_id, problem_id, timestamp):
        """Handle Deleted status"""
        logger.info(f"Challenge {problem_id} has been deleted for user {user_id}")
        print("\n=== Challenge Deleted ===")
        print(f"User: {user_id}")
        print(f"Problem: {problem_id}")
        print(f"Time: {timestamp}")
        print("=======================\n")