import logging
from sqlite3 import OperationalError
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, load_only
from sqlalchemy.sql import text
from contextlib import contextmanager
from app.exceptions.api import InternalServerError
from app.extensions_manager import db
from app.extensions.db.models import Challenges, UserChallenges

class UserChallengesRepository:
    def __init__(self):
        """세션을 직접 관리하는 Repository"""
        self.db_session = db.session  # Flask-SQLAlchemy Scoped Session

    @contextmanager
    def get_session(self) -> Session:
        """독립적인 세션을 생성하고 자동 종료하는 컨텍스트 매니저"""
        session = db.session()  # 새로운 세션 생성
        try:
            yield session  # 세션 제공
            session.commit()  # 성공하면 커밋
        except SQLAlchemyError as e:
            session.rollback()  # 예외 발생 시 롤백
            raise InternalServerError(error_msg=f"Database transaction failed: {e}") from e
        finally:
            session.close()  # 세션 종료

    def create(self, username: str, C_idx: int, userChallengeName: str,
               port: int, status: str = 'None') -> Optional[UserChallenges]:
        """새로운 사용자 챌린지 생성"""
        try:
            challenge = UserChallenges(
                username=username,
                C_idx=C_idx,
                userChallengeName=userChallengeName,
                port=port,
                status=status
            )
            with self.get_session() as session:
                session.add(challenge)
            return challenge
        except SQLAlchemyError as e:
            raise InternalServerError(error_msg=f"Error creating challenge in db: {e}") from e

    def get_by_user_challenge_name(self, userChallengeName: str) -> Optional[UserChallenges]:
        """사용자 챌린지 이름으로 조회 (DetachedInstanceError 방지)"""
        with self.get_session() as session:
            return session.query(UserChallenges) \
                .options(load_only("status", "port")) \
                .filter_by(userChallengeName=userChallengeName).first()

    def update_status(self, challenge: UserChallenges, new_status: str) -> bool:
        """사용자 챌린지 상태 업데이트"""
        try:
            with self.get_session() as session:
                fresh_challenge = session.query(UserChallenges).filter_by(userChallengeName=challenge.userChallengeName).first()
                if fresh_challenge:
                    fresh_challenge.status = new_status
                else:
                    raise InternalServerError(error_msg=f"Challenge not found: {challenge.userChallengeName}")
            return True
        except SQLAlchemyError as e:
            raise InternalServerError(error_msg=f"Error updating challenge status: {e}") from e

    def update_port(self, challenge: UserChallenges, port: int, max_retries: int = 3) -> bool:
        """챌린지 포트 업데이트 (트랜잭션 충돌 시 재시도)"""
        retries = 0
        while retries < max_retries:
            try:
                with self.get_session() as session:
                    session.execute(text("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED"))
                    
                    # `.with_for_update()`를 적용하여 동시 수정 방지
                    fresh_challenge = session.query(UserChallenges).with_for_update().filter_by(userChallengeName=challenge.userChallengeName).one()
                    fresh_challenge.port = port
                return True
            except OperationalError as e:
                if "Record has changed since last read" in str(e):
                    retries += 1
                    continue  # 재시도
                raise InternalServerError(error_msg=f"Error updating challenge port: {e}") from e
        raise InternalServerError(error_msg="Error updating challenge port after multiple retries")

    def is_running(self, challenge: UserChallenges) -> bool:
        """챌린지가 실행 중인지 확인 (DetachedInstanceError 방지)"""
        with self.get_session() as session:
            fresh_challenge = session.merge(challenge)  # 세션에 다시 연결
            return fresh_challenge.status == 'Running'

    def get_status(self, challenge_id: int, username: str) -> Optional[dict]:
        """챌린지 상태 조회"""
        with self.get_session() as session:
            challenge = session.query(UserChallenges) \
                .options(load_only("status", "port")) \
                .filter_by(C_idx=challenge_id, username=username).first()
            if not challenge:
                return None
            return {'status': challenge.status, 'port': int(challenge.port)} if challenge.status == 'Running' else {'status': challenge.status}



    
# class ChallengeRepository:
#     def __init__(self):
#         self.db_session = db.session

#     def get_challenge_name(self, challenge_id: int) -> Optional[str]:
#         """챌린지 ID로 챌린지 조회"""
#         with self.get_session() as session:
#             challenge = session.query(Challenges).get(challenge_id)
#             return challenge.title if challenge else None

        

class ChallengeRepository:
    @staticmethod
    def get_challenge_name(challenge_id: int) -> Optional[str]:
        """
        챌린지 아이디로 챌린지 조회
        
        Args:
            challenge_id (int): 챌린지 아이디  
        
        Returns:
            str: 챌린지 이름
        """
        challenge = Challenges.query.get(challenge_id)
        return challenge.title if challenge else None