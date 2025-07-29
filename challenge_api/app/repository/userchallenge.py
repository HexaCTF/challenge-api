from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from challenge_api.app.model.model import UserChallenges
from challenge_api.app.schema import UserChallengeData
from challenge_api.app.repository.challenge import ChallengeRepository
from challenge_api.app.common.exceptions import InvalidInputValue, UserChallengeRepositoryException
import logging

logger = logging.getLogger(__name__)


class UserChallengesRepository:
    def __init__(self, session: Session, challenge_repo: ChallengeRepository = None):
        self.session = session
        self.challenge_repo = challenge_repo
        
    def create(self, **kwargs) -> UserChallenges:
        """
        create new UserChallenge.
        
        Args:
            **kwargs: UserChallenge creation required data
            
        Returns:
            UserChallenges: created UserChallenge object
            
        Raises:
            InvalidInputValue: invalid Challenge ID
            UserChallengeRepositoryException: database error occurred
        """
        try:
            # validate challenge existence
            challenge_id = kwargs.get('C_idx')
            if challenge_id and self.challenge_repo:
                challenge = self.challenge_repo.get_by_id(challenge_id)
                if not challenge:
                    raise InvalidInputValue(
                        message=f"Challenge with id {challenge_id} not found"
                    )
            
            # create UserChallenge
            userchallenge = UserChallenges(**kwargs)
            
            self.session.add(userchallenge)
            self.session.flush()  # to get id
            self.session.commit()
                
            return userchallenge
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise UserChallengeRepositoryException(f"Failed to create UserChallenge: {str(e)}")
        
    def get_by_id(self, idx: int) -> Optional[UserChallenges]:
        """
        get UserChallenge by id.
        
        Args:
            idx: UserChallenge ID
            
        Returns:
            UserChallenges object or None
        """
        try:
            stmt = select(UserChallenges).where(UserChallenges.idx == idx)
            result = self.session.execute(stmt).scalar_one_or_none()
            return result
        except SQLAlchemyError as e:
            raise UserChallengeRepositoryException(f"Failed to get UserChallenge by id {idx}: {str(e)}")
    
    def get(self, **kwargs) -> Optional[UserChallenges]:
        """
        get first UserChallenge by conditions.
        
        Args:
            **kwargs: search conditions
            
        Returns:
            UserChallenges object or None
        """
        try:
            stmt = select(UserChallenges)
            for key, value in kwargs.items():
                stmt = stmt.where(getattr(UserChallenges, key) == value)
            result = self.session.execute(stmt).scalar_one_or_none()
            return result
        except SQLAlchemyError as e:
            raise UserChallengeRepositoryException(f"Failed to get UserChallenge with {kwargs}: {str(e)}")

    
    def is_exist(self, **kwargs) -> bool:
        """
        check if UserChallenge exists by conditions.
        
        Args:
            **kwargs: 검색 조건
            
        Returns:
            bool: exists or not
        """
        try:
            stmt = select(UserChallenges)
            for key, value in kwargs.items():
                stmt = stmt.where(getattr(UserChallenges, key) == value)
            exists = self.session.execute(stmt).scalar_one_or_none() is not None
            return exists
        except SQLAlchemyError as e:
            raise UserChallengeRepositoryException(f"Failed to check UserChallenge existence with {kwargs}: {str(e)}")
    
    def get_by_user_and_challenge(self, user_idx: int, challenge_idx: int) -> Optional[UserChallenges]:
        """
        get UserChallenge by user_idx and challenge_idx.
        
        Args:
            user_idx: user ID
            challenge_idx: challenge ID
            
        Returns:
            UserChallenges 객체 또는 None
        """
        return self.get(user_idx=user_idx, C_idx=challenge_idx)
    
    def get_by_name(self, name: str) -> Optional[UserChallenges]:
        """
        get UserChallenge by name.
        
        Args:
            name: UserChallenge name
            
        Returns:
            UserChallenges object or None
        """
        return self.get(userChallengeName=name)
    
    def update(self, idx: int, **kwargs) -> Optional[UserChallenges]:
        """
        update UserChallenge.
        
        Args:
            idx: UserChallenge ID
            **kwargs: update fields
            
        Returns:
            updated UserChallenges object or None
        """
        try:
            stmt = select(UserChallenges).where(UserChallenges.idx == idx)
            userchallenge = self.session.execute(stmt).scalar_one_or_none()
            
            if not userchallenge:
                raise UserChallengeRepositoryException(f"UserChallenge with id {idx} not found for update")
            
            for key, value in kwargs.items():
                if hasattr(userchallenge, key):
                    setattr(userchallenge, key, value)
            
            self.session.commit()
                
            return userchallenge
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise UserChallengeRepositoryException(f"Failed to update UserChallenge: {str(e)}")
    