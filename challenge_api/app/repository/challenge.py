from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from challenge_api.app.model.model import Challenges
from challenge_api.app.common.exceptions import RepositoryException, ChallengeRepositoryException
import logging

logger = logging.getLogger(__name__)

class ChallengeRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, challenge_id: int) -> Optional[Challenges]:
        """
        get challenge by id.
        
        Args:
            challenge_id: Challenge ID
            
        Returns:
            Challenges object or None
        """
        if not challenge_id or challenge_id <= 0:
            raise ChallengeRepositoryException(f"Invalid challenge_id: {challenge_id} provided")
            
        try:
            stmt = select(Challenges).where(Challenges.idx == challenge_id)
            result = self.session.execute(stmt).scalar_one_or_none()
            
            return result
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to get challenge by id {challenge_id}: {str(e)}")
    
    def get_name_by_id(self, challenge_id: int) -> Optional[str]:
        """
        get challenge name by id.
        
        Args:
            challenge_id: Challenge ID
            
        Returns:
            Challenge name or None
        """
        if not challenge_id or challenge_id <= 0:
            raise ChallengeRepositoryException(f"Invalid challenge_id: {challenge_id} provided")
            
        try:
            stmt = select(Challenges).where(Challenges.idx == challenge_id)
            challenge = self.session.execute(stmt).scalar_one_or_none()
            
            return challenge.title if challenge else None
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to get challenge name by id {challenge_id}: {str(e)}")
    
    def exists(self, challenge_id: int) -> bool:
        """
        check if challenge exists.
        
        Args:
            challenge_id: Challenge ID
            
        Returns:
            bool: exists or not
        """
        if not challenge_id or challenge_id <= 0:
            raise ChallengeRepositoryException(f"Invalid challenge_id: {challenge_id} provided")
            
        try:
            stmt = select(Challenges).where(
                Challenges.idx == challenge_id,
                Challenges.currentStatus == True
            )
            return self.session.execute(stmt).scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to check challenge existence for id {challenge_id}: {str(e)}")
    