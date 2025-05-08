import logging
import sys
from typing import Any, Dict
from challenge_api.exceptions.kafka_exceptions import QueueProcessingError
from challenge_api.db.repository import UserChallengesRepository, UserChallengeStatusRepository
from challenge_api.objects.challenge_info import ChallengeInfo
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class MessageHandler:
    VALID_STATUSES = {'Pending', 'Running', 'Deleted', 'Error'}
    VALID_STATUS_TRANSITIONS = {
        'Pending': {'Running', 'Error', 'Deleted'},
        'Running': {'Error', 'Deleted'},
        'Error': {'Running', 'Deleted'},
        'Deleted': set()  # Deleted is a terminal state
    }

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
    def validate_status_transition(current_status: str, new_status: str) -> bool:
        """
        상태 전이가 유효한지 검증
        
        Args:
            current_status (str): 현재 상태
            new_status (str): 새로운 상태
            
        Returns:
            bool: 유효한 상태 전이인지 여부
        """
        if not current_status:
            return True  # 첫 상태는 항상 유효
        return new_status in MessageHandler.VALID_STATUS_TRANSITIONS.get(current_status, set())

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
            
            print(f"Received message: {message}", file=sys.stderr)
            
            # 상태 정보 업데이트
            userchallenge_repo = UserChallengesRepository()
            status_repo = UserChallengeStatusRepository()
            

            if userchallenge_repo.is_exist(challenge_info):
                userchallenge = userchallenge_repo.get_by_user_challenge_name(challenge_name)
                if not userchallenge:
                    logger.warning(f"Challenge {challenge_name} exists but could not be retrieved")
                    return
                
                recent_status = None
                if new_status == 'Pending':
                    recent_status = status_repo.create(userchallenge_idx=userchallenge.idx, port=0)   
                else:
                    recent_status = status_repo.get_recent_status(userchallenge.idx)
                    if new_status == 'Running' and endpoint:
                        # Running 상태이고 endpoint가 있으면 포트 업데이트
                        status_repo.update_port(recent_status.idx, int(endpoint))
                    status_repo.update_status(recent_status.idx, new_status)

                logger.info(f"Updated status for challenge {challenge_name} to {new_status} with endpoint {endpoint}")
            
        except ValueError as e:
            logger.error(f"Invalid message format: {str(e)}")
            raise QueueProcessingError(error_msg=f"Invalid message format {str(e)}") from e 
        except Exception as e:
            logger.error(f"Unexpected error while processing message: {str(e)}")
            raise QueueProcessingError(error_msg=f"Kafka Error: {str(e)}") from e
