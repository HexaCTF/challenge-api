import logging
from datetime import datetime
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.extensions import db
from app.extensions.db.repository import UserChallengesRepository

logger = logging.getLogger(__name__)

class MessageHandler:
   VALID_STATUSES = {'Creating', 'Running', 'Deleted', 'Error'} 

   @staticmethod
   def validate_message(message: Dict[str, Any]) -> tuple[str, str, str, str]:
       """
       메시지 유효성 검사 및 필드 추출

       Args:
           message: Kafka 메시지

       Returns:
           username, problem_id, new_status, timestamp 튜플
       """
       username = message.user
       problem_id = message.problemId
       new_status = message.newStatus
       timestamp = message.timestamp

       if not all([username, problem_id, new_status, timestamp]):
           raise ValueError(f"Missing required fields in message: {message}")

       if new_status not in MessageHandler.VALID_STATUSES:
           raise ValueError(f"Invalid status type: {new_status}")

       return username, problem_id, new_status, timestamp
   
   @staticmethod
   def handle_message(message: Dict[str, Any]):
        """
        메시지를 consume하고 처리하는 메소드
        Args:
            message: Kafka 메시지
        """
        try:
            username, problem_id, new_status, _ = MessageHandler.validate_message(message)
            
            repo = UserChallengesRepository()
            
            challenge_name = f"{username}_{problem_id}"
            
            if new_status == "Creating":
                # 새로운 챌린지 생성
                challenge = repo.create(
                    username=username,
                    C_idx=problem_id,
                    userChallengeName=challenge_name,
                    port=0,  # 초기 포트값
                    status=new_status
                )
            else:
                # 기존 챌린지 상태 업데이트
                challenge = repo.get_by_user_challenge_name(challenge_name)
                if not challenge:
                    raise ValueError(f"Challenge not found: {challenge_name}")
                
                repo.update_status(challenge, new_status)
        
        except ValueError as e:
            logger.warning(f"Invalid message format: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
