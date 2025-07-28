from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from challenge_api.db.models import UserChallenges
from challenge_api.app.schema import UserChallengeData
from challenge_api.app.repository.challenge import ChallengeRepository
from challenge_api.exceptions.service import InvalidInputValue, RepositoryException
import logging

logger = logging.getLogger(__name__)


class UserChallengesRepository:
    def __init__(self, session: Session, challenge_repo: ChallengeRepository = None):
        self.session = session
        self.challenge_repo = challenge_repo
        
    def create(self, **kwargs) -> UserChallenges:
        """
        새 UserChallenge를 생성합니다.
        
        Args:
            **kwargs: UserChallenge 생성에 필요한 데이터
            
        Returns:
            UserChallenges: 생성된 UserChallenge 객체
            
        Raises:
            InvalidInputValue: 유효하지 않은 Challenge ID인 경우
            RepositoryException: 데이터베이스 오류 발생 시
        """
        try:
            # Challenge 존재 여부 검증
            challenge_id = kwargs.get('C_idx')
            if challenge_id and self.challenge_repo:
                challenge = self.challenge_repo.get_by_id(challenge_id)
                if not challenge:
                    raise InvalidInputValue(
                        message=f"Challenge with id {challenge_id} not found"
                    )
            
            # UserChallenge 생성
            userchallenge = UserChallenges(**kwargs)
            
            with self.session.begin():
                self.session.add(userchallenge)
                self.session.flush()  # ID를 얻기 위해 flush
                
            logger.info(f"Created UserChallenge with id {userchallenge.idx}")
            return userchallenge
            
        except InvalidInputValue:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error creating UserChallenge: {str(e)}")
            raise RepositoryException(f"Failed to create UserChallenge: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating UserChallenge: {str(e)}")
            raise RepositoryException(f"Unexpected error: {str(e)}")
        
    def get_by_id(self, idx: int) -> Optional[UserChallenges]:
        """
        ID로 UserChallenge를 조회합니다.
        
        Args:
            idx: UserChallenge ID
            
        Returns:
            UserChallenges 객체 또는 None
        """
        try:
            result = self.session.query(UserChallenges).filter_by(idx=idx).first()
            if result:
                logger.debug(f"Found UserChallenge with id {idx}")
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error getting UserChallenge by id {idx}: {str(e)}")
            return None
    
    def get(self, **kwargs) -> Optional[UserChallenges]:
        """
        조건에 맞는 첫 번째 UserChallenge를 조회합니다.
        
        Args:
            **kwargs: 검색 조건
            
        Returns:
            UserChallenges 객체 또는 None
        """
        try:
            result = self.session.query(UserChallenges).filter_by(**kwargs).first()
            if result:
                logger.debug(f"Found UserChallenge with conditions {kwargs}")
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error getting UserChallenge with {kwargs}: {str(e)}")
            return None

    def get_all(self, **kwargs) -> List[UserChallenges]:
        """
        조건에 맞는 모든 UserChallenge를 조회합니다.
        
        Args:
            **kwargs: 검색 조건
            
        Returns:
            List[UserChallenges]: UserChallenge 객체 리스트
        """
        try:
            results = self.session.query(UserChallenges).filter_by(**kwargs).all()
            logger.debug(f"Found {len(results)} UserChallenges with conditions {kwargs}")
            return results
        except SQLAlchemyError as e:
            logger.error(f"Database error getting all UserChallenges with {kwargs}: {str(e)}")
            return []

    def is_exist(self, **kwargs) -> bool:
        """
        조건에 맞는 UserChallenge가 존재하는지 확인합니다.
        
        Args:
            **kwargs: 검색 조건
            
        Returns:
            bool: 존재 여부
        """
        try:
            exists = self.session.query(UserChallenges).filter_by(**kwargs).first() is not None
            logger.debug(f"UserChallenge exists with conditions {kwargs}: {exists}")
            return exists
        except SQLAlchemyError as e:
            logger.error(f"Database error checking UserChallenge existence with {kwargs}: {str(e)}")
            return False
    
    def get_by_user_and_challenge(self, user_idx: int, challenge_idx: int) -> Optional[UserChallenges]:
        """
        특정 사용자의 특정 챌린지를 조회합니다.
        
        Args:
            user_idx: 사용자 ID
            challenge_idx: 챌린지 ID
            
        Returns:
            UserChallenges 객체 또는 None
        """
        return self.get(user_idx=user_idx, C_idx=challenge_idx)
    
    def get_by_name(self, name: str) -> Optional[UserChallenges]:
        """
        이름으로 UserChallenge를 조회합니다.
        
        Args:
            name: UserChallenge 이름
            
        Returns:
            UserChallenges 객체 또는 None
        """
        return self.get(userChallengeName=name)
    
    def update(self, idx: int, **kwargs) -> Optional[UserChallenges]:
        """
        UserChallenge를 업데이트합니다.
        
        Args:
            idx: UserChallenge ID
            **kwargs: 업데이트할 필드들
            
        Returns:
            업데이트된 UserChallenges 객체 또는 None
        """
        try:
            with self.session.begin():
                userchallenge = self.session.query(UserChallenges).filter_by(idx=idx).first()
                if not userchallenge:
                    logger.warning(f"UserChallenge with id {idx} not found for update")
                    return None
                
                for key, value in kwargs.items():
                    if hasattr(userchallenge, key):
                        setattr(userchallenge, key, value)
                
                self.session.flush()
                
            logger.info(f"Updated UserChallenge with id {idx}")
            return userchallenge
            
        except SQLAlchemyError as e:
            logger.error(f"Database error updating UserChallenge {idx}: {str(e)}")
            raise RepositoryException(f"Failed to update UserChallenge: {str(e)}")
    
    def delete(self, idx: int) -> bool:
        """
        UserChallenge를 삭제합니다.
        
        Args:
            idx: UserChallenge ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            with self.session.begin():
                userchallenge = self.session.query(UserChallenges).filter_by(idx=idx).first()
                if not userchallenge:
                    logger.warning(f"UserChallenge with id {idx} not found for deletion")
                    return False
                
                self.session.delete(userchallenge)
                
            logger.info(f"Deleted UserChallenge with id {idx}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting UserChallenge {idx}: {str(e)}")
            raise RepositoryException(f"Failed to delete UserChallenge: {str(e)}") 