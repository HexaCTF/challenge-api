import logging
import sys
from typing import Any, Dict, Set, Optional
from enum import Enum, auto
from challenge_api.exceptions.kafka_exceptions import QueueProcessingError
from challenge_api.db.repository import UserChallengesRepository, UserChallengeStatusRepository
from challenge_api.objects.challenge_info import ChallengeInfo
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

logger = logging.getLogger(__name__)

class ChallengeStatus(Enum):
    """챌린지 상태를 나타내는 열거형"""
    PENDING = auto()
    RUNNING = auto()
    ERROR = auto()
    DELETED = auto()

    @classmethod
    def from_str(cls, status: str) -> 'ChallengeStatus':
        """문자열로부터 상태 열거형 생성"""
        try:
            return cls[status.upper()]
        except KeyError:
            raise ValueError(f"Invalid status: {status}")

    def __str__(self) -> str:
        return self.name.capitalize()

class MessageHandler:
    """Kafka 메시지 처리기"""
    
    # 상태 전이 정의
    _STATUS_TRANSITIONS: Dict[ChallengeStatus, Set[ChallengeStatus]] = {
        ChallengeStatus.PENDING: {ChallengeStatus.RUNNING, ChallengeStatus.ERROR, ChallengeStatus.DELETED},
        ChallengeStatus.RUNNING: {ChallengeStatus.ERROR, ChallengeStatus.DELETED},
        ChallengeStatus.ERROR: {ChallengeStatus.RUNNING, ChallengeStatus.DELETED},
        ChallengeStatus.DELETED: set()  # 종료 상태
    }

    @staticmethod
    def validate_message(message: Dict[str, Any]) -> tuple[str, str, ChallengeStatus, str, str]:
        """
        Kafka 메세지의 필수 필드를 검증하고 반환
        
        Args:
            message: Dict[str, Any] - 검증할 메시지
            
        Returns:
            tuple[str, str, ChallengeStatus, str, str] - (user_id, problem_id, status, timestamp, endpoint)
            
        Raises:
            QueueProcessingError: 메시지 검증 실패시
        """
        try:
            logger.debug(f"Validating message: {message}")
            
            # 메시지가 딕셔너리인지 확인
            if not isinstance(message, dict):
                error_msg = f"Message must be a dictionary, got {type(message)}"
                logger.error(error_msg)
                raise QueueProcessingError(error_msg=error_msg)
            
            # 필수 필드 추출
            user_id = str(message.get('userId', ''))
            problem_id = str(message.get('problemId', ''))
            new_status_str = str(message.get('newStatus', ''))
            timestamp = str(message.get('timestamp', ''))
            endpoint = str(message.get('endpoint', ''))

            logger.debug(
                f"Extracted values - user_id: {user_id}, problem_id: {problem_id}, "
                f"new_status: {new_status_str}, timestamp: {timestamp}, endpoint: {endpoint}"
            )

            # 필수 필드 검증
            if not all([user_id, problem_id, new_status_str, timestamp]):
                missing_fields = [
                    field for field, value in {
                        'userId': user_id,
                        'problemId': problem_id,
                        'newStatus': new_status_str,
                        'timestamp': timestamp
                    }.items() if not value
                ]
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                logger.error(error_msg)
                raise QueueProcessingError(error_msg=error_msg)

            # 상태값을 열거형으로 변환
            try:
                new_status = ChallengeStatus.from_str(new_status_str)
            except ValueError as e:
                logger.error(f"Invalid status value: {e}")
                raise QueueProcessingError(error_msg=str(e)) from e

            # 타임스탬프 검증
            try:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError as e:
                error_msg = f"Invalid timestamp format: {timestamp}"
                logger.error(error_msg)
                raise QueueProcessingError(error_msg=error_msg) from e

            logger.debug("Message validation successful")
            return user_id, problem_id, new_status, timestamp, endpoint
            
        except QueueProcessingError:
            raise
        except Exception as e:
            error_msg = f"Message validation failed: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Error type: {type(e)}")
            raise QueueProcessingError(error_msg=error_msg) from e

    @staticmethod
    def validate_status_transition(current_status: Optional[ChallengeStatus], 
                                 new_status: ChallengeStatus) -> bool:
        """
        상태 전이가 유효한지 검증
        
        Args:
            current_status: 현재 상태
            new_status: 새로운 상태
            
        Returns:
            bool: 유효한 상태 전이인지 여부
        """
        if current_status is None:
            return True  # 첫 상태는 항상 유효
        return new_status in MessageHandler._STATUS_TRANSITIONS.get(current_status, set())

    @staticmethod
    def handle_message(message: Dict[str, Any]) -> None:
        """
        Consume한 Kafka message 내용을 DB에 반영

        Args:
            message: Dict[str, Any] - Kafka 메세지
            
        Raises:
            QueueProcessingError: 메시지 처리 실패시
        """
        try:
            logger.debug(f"Starting to process message: {message}")
            
            # 1. 메시지 유효성 검사
            user_id, challenge_id, new_status, _, endpoint = MessageHandler.validate_message(message)
            
            try:
                challenge_info = ChallengeInfo(challenge_id=int(challenge_id), user_id=int(user_id))
            except ValueError as e:
                error_msg = f"Invalid ID format: {str(e)}"
                logger.error(error_msg)
                raise QueueProcessingError(error_msg=error_msg) from e
                
            challenge_name = challenge_info.name
            logger.info(f"Processing message for challenge {challenge_name}")
            logger.debug(f"Status update request: {new_status}, Endpoint: {endpoint}")

            # 2. Repository 초기화
            userchallenge_repo = UserChallengesRepository()
            status_repo = UserChallengeStatusRepository()
            
            # 3. UserChallenge 존재 확인 및 조회
            if not userchallenge_repo.is_exist(challenge_info):
                error_msg = f"Challenge {challenge_name} not found"
                logger.error(error_msg)
                raise QueueProcessingError(error_msg=error_msg)
                
            userchallenge = userchallenge_repo.get_by_user_challenge_name(challenge_name)
            if not userchallenge:
                error_msg = f"Failed to retrieve challenge {challenge_name}"
                logger.error(error_msg)
                raise QueueProcessingError(error_msg=error_msg)
            
            logger.debug(f"Found UserChallenge with ID: {userchallenge.idx}")
            
            # 4. 현재 상태 확인
            recent_status = status_repo.get_recent_status(userchallenge.idx)
            current_status = ChallengeStatus.from_str(recent_status.status) if recent_status else None
            
            # 5. 상태 전이 검증
            if not MessageHandler.validate_status_transition(current_status, new_status):
                error_msg = f"Invalid status transition from {current_status} to {new_status}"
                logger.error(error_msg)
                raise QueueProcessingError(error_msg=error_msg)
            
            # 6. 상태 업데이트
            try:
                # 첫 상태이거나 상태가 변경된 경우에만 새 레코드 생성
                if not recent_status or current_status != new_status:
                    logger.debug(f"Creating new status record for {challenge_name}")
                    
                    # endpoint가 있고 Running 상태인 경우 포트 번호 파싱
                    port = 0
                    if new_status == ChallengeStatus.RUNNING and endpoint:
                        try:
                            port = int(endpoint)
                            logger.debug(f"Parsed port number: {port}")
                        except ValueError as e:
                            error_msg = f"Invalid port value: {endpoint}"
                            logger.error(error_msg)
                            raise QueueProcessingError(error_msg=error_msg) from e
                    
                    # 새 상태 레코드 생성
                    recent_status = status_repo.create(
                        userchallenge_idx=userchallenge.idx,
                        port=port,
                        status=str(new_status)
                    )
                    logger.info(f"Created new status record for challenge {challenge_name}: {new_status}")
                
            except SQLAlchemyError as e:
                error_msg = f"Database error while updating status: {str(e)}"
                logger.error(error_msg)
                raise QueueProcessingError(error_msg=error_msg) from e

        except QueueProcessingError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error in message handling: {str(e)}"
            logger.error(error_msg)
            raise QueueProcessingError(error_msg=error_msg) from e
