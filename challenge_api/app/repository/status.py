from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func
from sqlalchemy.exc import SQLAlchemyError

from challenge_api.app.model.model import UserChallengeStatus
from challenge_api.app.schema import StatusData
from challenge_api.app.common.exceptions import InvalidInputValue, StatusRepositoryException
import logging

logger = logging.getLogger(__name__)


class StatusRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, **kwargs) -> StatusData:
        """
        create user challenge status.
        
        Args:
            **kwargs: Status creation required data
            
        Returns:
            StatusData: created status data
            
        Raises:
            StatusRepositoryException: database error occurred
        """
        try:
            # validate required fields
            # TODO: convert to pydantic model
            required_fields = ['user_challenge_idx']
            for field in required_fields:
                if field not in kwargs:
                    raise InvalidInputValue(f"Required field '{field}' is missing")
            
            # set default values
            kwargs.setdefault('status', 'None')
            kwargs.setdefault('port', 0)
            # ------------------------------------------------------------
            
            userchallenge_status = UserChallengeStatus(**kwargs)
            
            # commit
            self.session.add(userchallenge_status)
            self.session.flush()  # to get id 
            self.session.commit()
                
            # convert to StatusData and return
            return StatusData(
                idx=userchallenge_status.idx,
                user_challenge_idx=userchallenge_status.user_challenge_idx,
                status=userchallenge_status.status,
                port=userchallenge_status.port
            )
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise StatusRepositoryException(f"Failed to create UserChallengeStatus: {str(e)}")
    
    def first(self, userchallenge_idx: int) -> Optional[StatusData]:
        """
        get latest status of specific UserChallenge.
        
        Args:
            userchallenge_idx: UserChallenge ID
            
        Returns:
            StatusData or None
        """
        try:
            # get first status
            status = self._first(userchallenge_idx)
            if not status:
                raise StatusRepositoryException(f"No status found for userchallenge_idx {userchallenge_idx}")
            
            # convert to StatusData and return
            return StatusData(
                idx=status.idx,
                user_challenge_idx=status.user_challenge_idx,
                status=status.status,
                port=status.port
            )
        except SQLAlchemyError as e:
            raise StatusRepositoryException(f"Failed to get first status for userchallenge_idx {userchallenge_idx}: {str(e)}")
    
    def _first(self, userchallenge_idx: int) -> Optional[UserChallengeStatus]:
        """
        get first status of specific UserChallenge.(Internal use)
        
        Args:
            userchallenge_idx: UserChallenge ID
            
        Returns:
            UserChallengeStatus or None
        """
        try:
            stmt = select(UserChallengeStatus).where(
                UserChallengeStatus.user_challenge_idx == userchallenge_idx
            ).order_by(desc(UserChallengeStatus.createdAt)).limit(1)
            
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            raise StatusRepositoryException(f"Failed to get first status for userchallenge_idx {userchallenge_idx}: {str(e)}")
    
    
    def update(self, **kwargs) -> Optional[StatusData]:
        """
        update UserChallengeStatus.
        
        Args:
            **kwargs: update condition and data
            
        Returns:
            StatusData: updated status data or None
            
        Raises:
            InvalidInputValue: required field is missing
            StatusRepositoryException: database error occurred
        """
        try:
            # validate required fields
            # TODO: convert to pydantic model
            required_fields = ['user_challenge_idx']
            for field in required_fields:
                if field not in kwargs:
                    raise InvalidInputValue(f"Required field '{field}' is missing")
            
            stmt = select(UserChallengeStatus).where(
                UserChallengeStatus.user_challenge_idx == kwargs['user_challenge_idx']
            ).order_by(desc(UserChallengeStatus.createdAt)).limit(1)
            
            status = self.session.execute(stmt).scalar_one_or_none()
            
            if not status:
                raise StatusRepositoryException(f"No status found for userchallenge_idx {kwargs['user_challenge_idx']}")
            
            # validate updatable fields
            updatable_fields = ['status', 'port']
            for field in updatable_fields:
                if field in kwargs:
                    value = kwargs[field]
                    if value is None:
                        # None 값이 들어오면 기본값 설정
                        if field == 'status':
                            value = 'None'
                        elif field == 'port':
                            value = 0
                    setattr(status, field, value)
            
            self.session.commit()
            
            return StatusData(
                idx=status.idx,
                user_challenge_idx=status.user_challenge_idx,
                status=status.status,
                port=status.port
            )
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise StatusRepositoryException(f"Failed to update UserChallengeStatus: {str(e)}")
    
    def get_by_id(self, idx: int) -> Optional[StatusData]:
        """
        ID로 UserChallengeStatus를 조회합니다.
        
        Args:
            idx: Status ID
            
        Returns:
            StatusData 또는 None
        """
        try:
            stmt = select(UserChallengeStatus).where(UserChallengeStatus.idx == idx)
            status = self.session.execute(stmt).scalar_one_or_none()
            
            if not status:
                raise StatusRepositoryException(f"No status found for idx {idx}")
                
            return StatusData(
                idx=status.idx,
                user_challenge_idx=status.user_challenge_idx,
                status=status.status,
                port=status.port
            )
        except SQLAlchemyError as e:
            raise StatusRepositoryException(f"Failed to get status by id {idx}: {str(e)}")
    
    