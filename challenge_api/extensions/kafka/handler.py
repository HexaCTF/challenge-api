import logging
from typing import Any, Dict
from challenge_api.exceptions.kafka_exceptions import QueueProcessingError
from challenge_api.db.repository import UserChallengesRepository, UserChallengeStatusRepository
from challenge_api.objects.challenge_info import ChallengeInfo

logger = logging.getLogger(__name__)

class MessageHandler:
    VALID_STATUSES = {'Pending', 'Running', 'Deleted', 'Error'}

    @staticmethod
    def validate_message(message: Dict[str, Any]) -> tuple[str, str, str, str, str]:
        """
        Kafka 메세지의 필수 필드를 검증하고 반환
        
        Args:
            message (Dict[str, Any]): Kafka 메세지
        
        Returns:
            tuple[str, str, str, str, str]: 사용자 이름, 챌린지 ID, 새로운 상태, 타임스탬프, 엔드포인트
        """
        try:
            user_id = message.userId
            problem_id = message.problemId
            new_status = message.newStatus
            endpoint = message.endpoint
            timestamp = message.timestamp
        except AttributeError:
            user_id = message['userId']
            problem_id = message['problemId']
            new_status = message['newStatus']
            timestamp = message['timestamp']
            endpoint = message.get('endpoint')  # endpoint가 없을 수 있으므로 get 사용

        if not all([user_id, problem_id, new_status, timestamp]):
            raise QueueProcessingError(error_msg=f"Kafka Error : Missing required fields in message: {message}")

        if new_status not in MessageHandler.VALID_STATUSES:
            raise QueueProcessingError(error_msg=f"Kafka Error : Invalid status in message: {new_status}")

        return user_id, problem_id, new_status, timestamp, endpoint

    @staticmethod
    def handle_message(message: Dict[str, Any]):
        """
        Consume한 Kafka message 내용을 DB에 반영

        Args:
            message: Kafka 메세지        
        """
        try:
            user_id, challenge_id, new_status, _, endpoint = MessageHandler.validate_message(message)
            challenge_info = ChallengeInfo(challenge_id=int(challenge_id), user_id=int(user_id))
            challenge_name = challenge_info.name
            
            # 상태 정보 업데이트
            userchallenge_repo = UserChallengesRepository()
            status_repo = UserChallengeStatusRepository()
            
            if userchallenge_repo.is_exist(challenge_info):
                userchallenge = userchallenge_repo.get_by_user_challenge_name(challenge_name)
                if not userchallenge:
                    logger.warning(f"Challenge {challenge_name} exists but could not be retrieved")
                    return
                    
                recent_status = status_repo.get_recent_status(userchallenge.idx)
                if not recent_status:
                    logger.warning(f"No status found for challenge {challenge_name}, creating new status")
                    recent_status = status_repo.create(userchallenge_idx=userchallenge.idx, port=0)
                
                try:
                    port = int(endpoint) if endpoint else 0
                except (ValueError, TypeError):
                    logger.warning(f"Invalid endpoint value: {endpoint}, using 0 as default")
                    port = 0
                
                if new_status == 'Running' and endpoint:
                    # Running 상태이고 endpoint가 있으면 포트 업데이트
                    status_repo.update_port(recent_status.idx, port)
                
                status_repo.update_status(recent_status.idx, new_status)
                logger.info(f"Updated status for challenge {challenge_name} to {new_status} with endpoint {endpoint}")
            else:
                logger.warning(f"Challenge {challenge_name} does not exist")
            
        except ValueError as e:
            raise QueueProcessingError(error_msg=f"Invalid message format {str(e)}") from e 
        except Exception as e:
            raise QueueProcessingError(error_msg=f"Kafka Error: {str(e)}") from e
