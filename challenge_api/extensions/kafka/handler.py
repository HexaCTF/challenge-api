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
        """
        try:
            print(f"[DEBUG] Validating message: {message}", file=sys.stderr)
            try:
                user_id = message.userId
                problem_id = message.problemId
                new_status = message.newStatus
                endpoint = message.endpoint
                timestamp = message.timestamp
                print("[DEBUG] Message accessed as object", file=sys.stderr)
            except AttributeError:
                print("[DEBUG] Message accessed as dictionary", file=sys.stderr)
                user_id = message['userId']
                problem_id = message['problemId']
                new_status = message['newStatus']
                timestamp = message['timestamp']
                endpoint = message.get('endpoint')

            print(f"[DEBUG] Extracted values - user_id: {user_id}, problem_id: {problem_id}, new_status: {new_status}, timestamp: {timestamp}, endpoint: {endpoint}", file=sys.stderr)

            if not all([user_id, problem_id, new_status, timestamp]):
                error_msg = f"Kafka Error : Missing required fields in message: {message}"
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                raise QueueProcessingError(error_msg=error_msg)

            if new_status not in MessageHandler.VALID_STATUSES:
                error_msg = f"Kafka Error : Invalid status in message: {new_status}"
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                raise QueueProcessingError(error_msg=error_msg)

            print("[DEBUG] Message validation successful", file=sys.stderr)
            return user_id, problem_id, new_status, timestamp, endpoint
        except Exception as e:
            print(f"[ERROR] Message validation failed: {e}", file=sys.stderr)
            print(f"[ERROR] Error type: {type(e)}", file=sys.stderr)
            raise

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
            print(f"[DEBUG] Starting to process message: {message}", file=sys.stderr)
            
            # 1. 메시지 유효성 검사
            user_id, challenge_id, new_status, _, endpoint = MessageHandler.validate_message(message)
            challenge_info = ChallengeInfo(challenge_id=int(challenge_id), user_id=int(user_id))
            challenge_name = challenge_info.name
            
            print(f"[INFO] Processing message for challenge {challenge_name}", file=sys.stderr)
            print(f"[DEBUG] Status update request: {new_status}, Endpoint: {endpoint}", file=sys.stderr)

            # 2. Repository 초기화
            userchallenge_repo = UserChallengesRepository()
            status_repo = UserChallengeStatusRepository()
            
            # 3. UserChallenge 존재 확인
            if not userchallenge_repo.is_exist(challenge_info):
                error_msg = f"Challenge {challenge_name} not found"
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                raise QueueProcessingError(error_msg=error_msg)
                
            userchallenge = userchallenge_repo.get_by_user_challenge_name(challenge_name)
            if not userchallenge:
                error_msg = f"Failed to retrieve challenge {challenge_name}"
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                raise QueueProcessingError(error_msg=error_msg)
            
            print(f"[DEBUG] Found UserChallenge with ID: {userchallenge.idx}", file=sys.stderr)
            
            # 4. 현재 상태 확인
            recent_status = status_repo.get_recent_status(userchallenge.idx)
            current_status = recent_status.status if recent_status else None
            
            # 5. 상태 전이 검증
            if not MessageHandler.validate_status_transition(current_status, new_status):
                error_msg = f"Invalid status transition from {current_status} to {new_status}"
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                raise QueueProcessingError(error_msg=error_msg)
            
            # 6. 상태 업데이트
            try:
                if not recent_status or new_status == 'Pending':
                    print(f"[DEBUG] Creating new status record for {challenge_name}", file=sys.stderr)
                    recent_status = status_repo.create(
                        userchallenge_idx=userchallenge.idx,
                        port=0,
                        status=new_status
                    )
                    print(f"[INFO] Created initial status for challenge {challenge_name}", file=sys.stderr)
                
                if recent_status:
                    if new_status == 'Running' and endpoint:
                        try:
                            port = int(endpoint)
                            print(f"[DEBUG] Updating port to {port}", file=sys.stderr)
                            status_repo.update_port(recent_status.idx, port)
                            print(f"[INFO] Updated port to {port} for challenge {challenge_name}", file=sys.stderr)
                        except ValueError as e:
                            error_msg = f"Invalid port value: {endpoint}"
                            print(f"[ERROR] {error_msg}", file=sys.stderr)
                            raise QueueProcessingError(error_msg=error_msg) from e
                    
                    print(f"[DEBUG] Updating status to {new_status}", file=sys.stderr)
                    status_repo.update_status(recent_status.idx, new_status)
                    print(f"[INFO] Updated status to {new_status} for challenge {challenge_name}", file=sys.stderr)
                
            except SQLAlchemyError as e:
                error_msg = f"Database error: {str(e)}"
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                raise QueueProcessingError(error_msg=error_msg) from e

        except ValueError as e:
            error_msg = f"Invalid message format: {str(e)}"
            print(f"[ERROR] {error_msg}", file=sys.stderr)
            raise QueueProcessingError(error_msg=error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"[ERROR] {error_msg}", file=sys.stderr)
            raise QueueProcessingError(error_msg=error_msg) from e
