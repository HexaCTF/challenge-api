from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from challenge_api.app.model import Challenges
from challenge_api.exceptions.service import RepositoryException
import logging

logger = logging.getLogger(__name__)

class ChallengeRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, challenge_id: int) -> Optional[Challenges]:
        """
        ID로 Challenge를 조회합니다.
        
        Args:
            challenge_id: Challenge ID
            
        Returns:
            Challenges 객체 또는 None
        """
        if not challenge_id or challenge_id <= 0:
            logger.warning(f"Invalid challenge_id provided: {challenge_id}")
            return None
            
        try:
            result = self.session.query(Challenges).filter(Challenges.idx == challenge_id).first()
            if result:
                logger.debug(f"Found challenge with id {challenge_id}")
            else:
                logger.debug(f"No challenge found with id {challenge_id}")
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error getting challenge by id {challenge_id}: {str(e)}")
            return None
    
    def get_name(self, challenge_id: int) -> Optional[str]:
        """
        Challenge ID로 이름을 조회합니다.
        
        Args:
            challenge_id: Challenge ID
            
        Returns:
            Challenge 이름 또는 None
        """
        if not challenge_id or challenge_id <= 0:
            logger.warning(f"Invalid challenge_id provided: {challenge_id}")
            return None
            
        try:
            challenge = self.session.query(Challenges).filter(Challenges.idx == challenge_id).first()
            if challenge:
                logger.debug(f"Found challenge name for id {challenge_id}: {challenge.title}")
                return challenge.title
            else:
                logger.debug(f"No challenge found with id {challenge_id}")
                return None
        except SQLAlchemyError as e:
            logger.error(f"Database error getting challenge name for id {challenge_id}: {str(e)}")
            return None
    
    def get_all(self, include_hidden: bool = False) -> List[Challenges]:
        """
        모든 Challenge를 조회합니다.
        
        Args:
            include_hidden: 숨겨진 챌린지 포함 여부
            
        Returns:
            List[Challenges]: Challenge 객체 리스트
        """
        try:
            query = self.session.query(Challenges)
            
            if not include_hidden:
                query = query.filter(Challenges.hidden == False)
            
            # 활성 상태인 챌린지만 조회
            query = query.filter(Challenges.currentStatus == True)
            
            results = query.all()
            logger.debug(f"Found {len(results)} challenges (include_hidden={include_hidden})")
            return results
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting all challenges: {str(e)}")
            return []
    
    def get_by_category(self, category: str, include_hidden: bool = False) -> List[Challenges]:
        """
        카테고리별로 Challenge를 조회합니다.
        
        Args:
            category: 챌린지 카테고리
            include_hidden: 숨겨진 챌린지 포함 여부
            
        Returns:
            List[Challenges]: Challenge 객체 리스트
        """
        if not category:
            logger.warning("Empty category provided")
            return []
            
        try:
            query = self.session.query(Challenges).filter(Challenges.category == category)
            
            if not include_hidden:
                query = query.filter(Challenges.hidden == False)
            
            query = query.filter(Challenges.currentStatus == True)
            
            results = query.all()
            logger.debug(f"Found {len(results)} challenges in category '{category}'")
            return results
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting challenges by category '{category}': {str(e)}")
            return []
    
    def get_by_author(self, author: str) -> List[Challenges]:
        """
        작성자별로 Challenge를 조회합니다.
        
        Args:
            author: 챌린지 작성자
            
        Returns:
            List[Challenges]: Challenge 객체 리스트
        """
        if not author:
            logger.warning("Empty author provided")
            return []
            
        try:
            results = self.session.query(Challenges) \
                .filter(Challenges.author == author) \
                .filter(Challenges.currentStatus == True) \
                .all()
            
            logger.debug(f"Found {len(results)} challenges by author '{author}'")
            return results
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting challenges by author '{author}': {str(e)}")
            return []
    
    def exists(self, challenge_id: int) -> bool:
        """
        Challenge가 존재하는지 확인합니다.
        
        Args:
            challenge_id: Challenge ID
            
        Returns:
            bool: 존재 여부
        """
        if not challenge_id or challenge_id <= 0:
            return False
            
        try:
            exists = self.session.query(Challenges) \
                .filter(Challenges.idx == challenge_id) \
                .filter(Challenges.currentStatus == True) \
                .first() is not None
            
            logger.debug(f"Challenge {challenge_id} exists: {exists}")
            return exists
            
        except SQLAlchemyError as e:
            logger.error(f"Database error checking challenge existence for id {challenge_id}: {str(e)}")
            return False
    
    def is_persistent(self, challenge_id: int) -> bool:
        """
        Challenge가 지속형인지 확인합니다.
        
        Args:
            challenge_id: Challenge ID
            
        Returns:
            bool: 지속형 여부
        """
        try:
            challenge = self.get_by_id(challenge_id)
            if challenge:
                return getattr(challenge, 'isPersistence', False)
            return False
        except Exception as e:
            logger.error(f"Error checking if challenge {challenge_id} is persistent: {str(e)}")
            return False
    
    def get_challenge_definition(self, challenge_id: int) -> Optional[str]:
        """
        Challenge의 정의(definition)를 조회합니다.
        이는 K8s 리소스 생성에 사용됩니다.
        
        Args:
            challenge_id: Challenge ID
            
        Returns:
            Challenge 정의 문자열 또는 None
        """
        try:
            challenge = self.get_by_id(challenge_id)
            if challenge:
                # 실제 모델에 definition 필드가 있다고 가정
                # 없다면 title이나 다른 적절한 필드를 사용
                definition = getattr(challenge, 'definition', None)
                if not definition:
                    # definition 필드가 없다면 title을 사용
                    definition = challenge.title
                
                logger.debug(f"Retrieved definition for challenge {challenge_id}")
                return definition
            else:
                logger.warning(f"No challenge found with id {challenge_id} for definition")
                return None
                
        except Exception as e:
            logger.error(f"Error getting challenge definition for id {challenge_id}: {str(e)}")
            return None
    
    def get_categories(self) -> List[str]:
        """
        모든 활성 챌린지의 카테고리 목록을 조회합니다.
        
        Returns:
            List[str]: 유니크한 카테고리 리스트
        """
        try:
            categories = self.session.query(Challenges.category) \
                .filter(Challenges.currentStatus == True) \
                .filter(Challenges.hidden == False) \
                .distinct() \
                .all()
            
            result = [category[0] for category in categories if category[0]]
            logger.debug(f"Found {len(result)} unique categories")
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting categories: {str(e)}")
            return []
    
    def update_solve_count(self, challenge_id: int, increment: int = 1) -> bool:
        """
        Challenge의 해결 횟수를 업데이트합니다.
        
        Args:
            challenge_id: Challenge ID
            increment: 증가시킬 값 (기본값: 1)
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            with self.session.begin():
                challenge = self.session.query(Challenges).filter(Challenges.idx == challenge_id).first()
                if not challenge:
                    logger.warning(f"Challenge {challenge_id} not found for solve count update")
                    return False
                
                challenge.solvedCount = (challenge.solvedCount or 0) + increment
                self.session.flush()
            
            logger.info(f"Updated solve count for challenge {challenge_id} by {increment}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error updating solve count for challenge {challenge_id}: {str(e)}")
            raise RepositoryException(f"Failed to update solve count: {str(e)}")
    
    def get_by_difficulty_range(self, min_score: int = 0, max_score: int = None) -> List[Challenges]:
        """
        점수 범위로 Challenge를 조회합니다.
        
        Args:
            min_score: 최소 점수
            max_score: 최대 점수 (None이면 제한 없음)
            
        Returns:
            List[Challenges]: Challenge 객체 리스트
        """
        try:
            query = self.session.query(Challenges) \
                .filter(Challenges.currentStatus == True) \
                .filter(Challenges.hidden == False) \
                .filter(Challenges.initialValue >= min_score)
            
            if max_score is not None:
                query = query.filter(Challenges.initialValue <= max_score)
            
            results = query.order_by(Challenges.initialValue).all()
            logger.debug(f"Found {len(results)} challenges in score range {min_score}-{max_score}")
            return results
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting challenges by difficulty range: {str(e)}")
            return []