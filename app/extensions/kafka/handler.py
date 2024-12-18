import logging

logger = logging.getLogger(__name__)


class MessageHandler:
    @staticmethod
    def handle_message(message):
        """
        Handle incoming Kafka messages

        Args:
            message (dict): Kafka message payload
        """
        try:
            event_type = message.get('event_type')
            payload = message.get('payload', {})

            if event_type == 'challenge_viewed':
                MessageHandler._handle_challenge_viewed(payload)
            elif event_type == 'challenge_created':
                MessageHandler._handle_challenge_created(payload)
            elif event_type == 'challenge_updated':
                MessageHandler._handle_challenge_updated(payload)
            elif event_type == 'challenge_deleted':
                MessageHandler._handle_challenge_deleted(payload)
            else:
                logger.warning(f"Unknown event type: {event_type}")

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            # Don't raise the exception - we want to continue processing messages

    @staticmethod
    def _handle_challenge_viewed(payload):
        challenge_id = payload.get('challenge_id')
        logger.info(f"Challenge viewed: {challenge_id}")
        # Add your business logic here

    @staticmethod
    def _handle_challenge_created(payload):
        logger.info(f"New challenge created: {payload}")
        # Add your business logic here

    @staticmethod
    def _handle_challenge_updated(payload):
        challenge_id = payload.get('challenge_id')
        logger.info(f"Challenge updated: {challenge_id}")
        # Add your business logic here

    @staticmethod
    def _handle_challenge_deleted(payload):
        challenge_id = payload.get('challenge_id')
        logger.info(f"Challenge deleted: {challenge_id}")