from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc

from challenge_api.app.model import UserChallengeStatus
from challenge_api.app.schema import StatusData
from challenge_api.exceptions.service import InvalidInputValue, RepositoryException
import logging

logger = logging.getLogger(__name__)


class UserChallengeStatusRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, **kwargs) -> StatusData:
        """
        새 UserChallengeStatus를 생성합니다.
        
        Args:
            **kwargs: Status 생성에 필요한 데이터
            
        Returns:
            StatusData: 생성된 상태 데이터
            
        Raises:
            RepositoryException: 데이터베이스 오류 발생 시
        """
        try:
            # 필수 필드 검증
            required_fields = ['user_challenge_idx']
            for field in required_fields:
                if field not in kwargs:
                    raise InvalidInputValue(f"Required field '{field}' is missing")
            
            # 기본값 설정
            kwargs.setdefault('status', 'None')
            kwargs.setdefault('port', 0)
            
            userchallenge_status = UserChallengeStatus(**kwargs)
            
            with self.session.begin():
                self.session.add(userchallenge_status)
                self.session.flush()  # ID를 얻기 위해 flush
                
            logger.info(f"Created UserChallengeStatus with id {userchallenge_status.idx}")
            
            # StatusData로 변환하여 반환
            return StatusData(
                idx=userchallenge_status.idx,
                user_challenge_idx=userchallenge_status.user_challenge_idx,
                status=userchallenge_status.status,
                port=userchallenge_status.port
            )
            
        except InvalidInputValue:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error creating UserChallengeStatus: {str(e)}")
            raise RepositoryException(f"Failed to create UserChallengeStatus: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating UserChallengeStatus: {str(e)}")
            raise RepositoryException(f"Unexpected error: {str(e)}")
    
    def first(self, userchallenge_idx: int) -> Optional[StatusData]:
        """
        특정 UserChallenge의 최신 상태를 조회합니다.
        
        Args:
            userchallenge_idx: UserChallenge ID
            
        Returns:
            StatusData 또는 None
        """
        try:
            status = self._first(userchallenge_idx)
            if not status:
                logger.debug(f"No status found for userchallenge_idx {userchallenge_idx}")
                return None
                
            return StatusData(
                idx=status.idx,
                user_challenge_idx=status.user_challenge_idx,
                status=status.status,
                port=status.port
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error getting first status for {userchallenge_idx}: {str(e)}")
            return None
    
    def _first(self, userchallenge_idx: int) -> Optional[UserChallengeStatus]:
        """
        특정 UserChallenge의 최신 상태를 조회합니다 (내부용).
        
        Args:
            userchallenge_idx: UserChallenge ID
            
        Returns:
            UserChallengeStatus 또는 None
        """
        try:
            return self.session.query(UserChallengeStatus) \
                .filter_by(user_challenge_idx=userchallenge_idx) \
                .order_by(desc(UserChallengeStatus.createdAt)) \
                .first()
        except SQLAlchemyError as e:
            logger.error(f"Database error in _first for {userchallenge_idx}: {str(e)}")
            return None
    
    def get_all_by_userchallenge(self, userchallenge_idx: int) -> List[StatusData]:
        """
        특정 UserChallenge의 모든 상태 기록을 조회합니다.
        
        Args:
            userchallenge_idx: UserChallenge ID
            
        Returns:
            List[StatusData]: 상태 데이터 리스트 (최신순)
        """
        try:
            statuses = self.session.query(UserChallengeStatus) \
                .filter_by(user_challenge_idx=userchallenge_idx) \
                .order_by(desc(UserChallengeStatus.createdAt)) \
                .all()
            
            result = [
                StatusData(
                    idx=status.idx,
                    user_challenge_idx=status.user_challenge_idx,
                    status=status.status,
                    port=status.port
                )
                for status in statuses
            ]
            
            logger.debug(f"Found {len(result)} statuses for userchallenge_idx {userchallenge_idx}")
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting all statuses for {userchallenge_idx}: {str(e)}")
            return []
    
    def update(self, **kwargs) -> Optional[StatusData]:
        """
        UserChallengeStatus를 업데이트합니다.
        
        Args:
            **kwargs: 업데이트 조건 및 데이터
            
        Returns:
            StatusData: 업데이트된 상태 데이터 또는 None
            
        Raises:
            InvalidInputValue: 필수 필드가 누락된 경우
            RepositoryException: 데이터베이스 오류 발생 시
        """
        try:
            userchallenge_idx = kwargs.get('userchallenge_idx')
            if not userchallenge_idx:
                raise InvalidInputValue("userchallenge_idx is required for update")
            
            with self.session.begin():
                status = self.session.query(UserChallengeStatus) \
                    .filter_by(user_challenge_idx=userchallenge_idx) \
                    .order_by(desc(UserChallengeStatus.createdAt)) \
                    .first()
                
                if not status:
                    logger.warning(f"No status found for userchallenge_idx {userchallenge_idx}")
                    return None
                
                # 업데이트 가능한 필드들
                updatable_fields = ['status', 'port']
                for field in updatable_fields:
                    if field in kwargs:
                        setattr(status, field, kwargs[field])
                
                self.session.flush()
            
            logger.info(f"Updated UserChallengeStatus for userchallenge_idx {userchallenge_idx}")
            
            return StatusData(
                idx=status.idx,
                user_challenge_idx=status.user_challenge_idx,
                status=status.status,
                port=status.port
            )
            
        except InvalidInputValue:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error updating UserChallengeStatus: {str(e)}")
            raise RepositoryException(f"Failed to update UserChallengeStatus: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error updating UserChallengeStatus: {str(e)}")
            raise RepositoryException(f"Unexpected error: {str(e)}")
    
    def get_by_id(self, idx: int) -> Optional[StatusData]:
        """
        ID로 UserChallengeStatus를 조회합니다.
        
        Args:
            idx: Status ID
            
        Returns:
            StatusData 또는 None
        """
        try:
            status = self.session.query(UserChallengeStatus).filter_by(idx=idx).first()
            if not status:
                return None
                
            return StatusData(
                idx=status.idx,
                user_challenge_idx=status.user_challenge_idx,
                status=status.status,
                port=status.port
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error getting status by id {idx}: {str(e)}")
            return None
    
    def get_running_challenges(self) -> List[StatusData]:
        """
        실행 중인 모든 챌린지의 상태를 조회합니다.
        
        Returns:
            List[StatusData]: 실행 중인 챌린지 상태 리스트
        """
        try:
            # 각 UserChallenge의 최신 상태 중 Running인 것들만 조회
            subquery = self.session.query(UserChallengeStatus.user_challenge_idx,
                                        self.session.query(UserChallengeStatus.idx)
                                        .filter(UserChallengeStatus.user_challenge_idx == 
                                               UserChallengeStatus.user_challenge_idx)
                                        .order_by(desc(UserChallengeStatus.createdAt))
                                        .limit(1)
                                        .scalar_subquery()
                                        .label('latest_idx')) \
                        .group_by(UserChallengeStatus.user_challenge_idx) \
                        .subquery()
            
            statuses = self.session.query(UserChallengeStatus) \
                .join(subquery, UserChallengeStatus.idx == subquery.c.latest_idx) \
                .filter(UserChallengeStatus.status == 'Running') \
                .all()
            
            result = [
                StatusData(
                    idx=status.idx,
                    user_challenge_idx=status.user_challenge_idx,
                    status=status.status,
                    port=status.port
                )
                for status in statuses
            ]
            
            logger.debug(f"Found {len(result)} running challenges")
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting running challenges: {str(e)}")
            return []
    
    def cleanup_old_statuses(self, userchallenge_idx: int, keep_count: int = 10) -> int:
        """
        오래된 상태 기록을 정리합니다.
        
        Args:
            userchallenge_idx: UserChallenge ID
            keep_count: 유지할 최신 기록 수
            
        Returns:
            int: 삭제된 기록 수
        """
        try:
            with self.session.begin():
                # 유지할 기록의 ID들을 조회
                keep_ids = self.session.query(UserChallengeStatus.idx) \
                    .filter_by(user_challenge_idx=userchallenge_idx) \
                    .order_by(desc(UserChallengeStatus.createdAt)) \
                    .limit(keep_count) \
                    .subquery()
                
                # 유지할 기록을 제외한 모든 기록 삭제
                deleted_count = self.session.query(UserChallengeStatus) \
                    .filter_by(user_challenge_idx=userchallenge_idx) \
                    .filter(~UserChallengeStatus.idx.in_(keep_ids)) \
                    .delete(synchronize_session=False)
            
            logger.info(f"Cleaned up {deleted_count} old status records for userchallenge_idx {userchallenge_idx}")
            return deleted_count
            
        except SQLAlchemyError as e:
            logger.error(f"Database error cleaning up old statuses: {str(e)}")
            raise RepositoryException(f"Failed to cleanup old statuses: {str(e)}")