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
            message: Dict[str, Any] - 검증할 메시지
            
        Returns:
            tuple[str, str, str, str, str] - (user_id, problem_id, new_status, timestamp, endpoint)
            
        Raises:
            QueueProcessingError: 메시지 검증 실패시
        """
        try:
            print(f"[DEBUG] Validating message: {message}", file=sys.stderr)
            
            # 메시지가 딕셔너리인지 확인
            if not isinstance(message, dict):
                error_msg = f"Message must be a dictionary, got {type(message)}"
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                raise QueueProcessingError(error_msg=error_msg)
            
            # 필수 필드 추출
            user_id = str(message.get('userId', ''))
            problem_id = str(message.get('problemId', ''))
            new_status = str(message.get('newStatus', ''))
            timestamp = str(message.get('timestamp', ''))
            endpoint = str(message.get('endpoint', ''))

            print(f"[DEBUG] Extracted values - user_id: {user_id}, problem_id: {problem_id}, new_status: {new_status}, timestamp: {timestamp}, endpoint: {endpoint}", file=sys.stderr)

            # 필수 필드 검증
            if not all([user_id, problem_id, new_status, timestamp]):
                missing_fields = [
                    field for field, value in {
                        'userId': user_id,
                        'problemId': problem_id,
                        'newStatus': new_status,
                        'timestamp': timestamp
                    }.items() if not value
                ]
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                raise QueueProcessingError(error_msg=error_msg)

            # 상태 값 검증
            if new_status not in MessageHandler.VALID_STATUSES:
                error_msg = f"Invalid status: {new_status}. Must be one of {MessageHandler.VALID_STATUSES}"
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                raise QueueProcessingError(error_msg=error_msg)

            print("[DEBUG] Message validation successful", file=sys.stderr)
            return user_id, problem_id, new_status, timestamp, endpoint
            
        except QueueProcessingError:
            raise
        except Exception as e:
            error_msg = f"Message validation failed: {str(e)}"
            print(f"[ERROR] {error_msg}", file=sys.stderr)
            print(f"[ERROR] Error type: {type(e)}", file=sys.stderr)
            raise QueueProcessingError(error_msg=error_msg) from e

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
            message: Dict[str, Any] - Kafka 메세지
            
        Raises:
            QueueProcessingError: 메시지 처리 실패시
        """
        try:
            print(f"[DEBUG] Starting to process message: {message}", file=sys.stderr)
            
            # 1. 메시지 유효성 검사
            user_id, challenge_id, new_status, _, endpoint = MessageHandler.validate_message(message)
            
            try:
                challenge_info = ChallengeInfo(challenge_id=int(challenge_id), user_id=int(user_id))
            except ValueError as e:
                error_msg = f"Invalid ID format: {str(e)}"
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                raise QueueProcessingError(error_msg=error_msg) from e
                
            challenge_name = challenge_info.name
            print(f"[INFO] Processing message for challenge {challenge_name}", file=sys.stderr)
            print(f"[DEBUG] Status update request: {new_status}, Endpoint: {endpoint}", file=sys.stderr)

            # 2. Repository 초기화
            userchallenge_repo = UserChallengesRepository()
            status_repo = UserChallengeStatusRepository()
            
            # 3. UserChallenge 존재 확인 및 조회
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
                # 첫 상태이거나 상태가 변경된 경우에만 새 레코드 생성
                if not recent_status or current_status != new_status:
                    print(f"[DEBUG] Creating new status record for {challenge_name}", file=sys.stderr)
                    
                    # endpoint가 있고 Running 상태인 경우 포트 번호 파싱
                    port = 0
                    if new_status == 'Running' and endpoint:
                        try:
                            port = int(endpoint)
                            print(f"[DEBUG] Parsed port number: {port}", file=sys.stderr)
                        except ValueError as e:
                            error_msg = f"Invalid port value: {endpoint}"
                            print(f"[ERROR] {error_msg}", file=sys.stderr)
                            raise QueueProcessingError(error_msg=error_msg) from e
                    
                    # 새 상태 레코드 생성
                    recent_status = status_repo.create(
                        userchallenge_idx=userchallenge.idx,
                        port=port,
                        status=new_status
                    )
                    print(f"[INFO] Created new status record for challenge {challenge_name}: {new_status}", file=sys.stderr)
                
            except SQLAlchemyError as e:
                error_msg = f"Database error while updating status: {str(e)}"
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                raise QueueProcessingError(error_msg=error_msg) from e

        except QueueProcessingError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error in message handling: {str(e)}"
            print(f"[ERROR] {error_msg}", file=sys.stderr)
            raise QueueProcessingError(error_msg=error_msg) from e
