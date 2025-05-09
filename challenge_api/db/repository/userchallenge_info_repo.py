from typing import Tuple

from challenge_api.extensions_manager import db
from challenge_api.db.models import UserChallenge_Info
from challenge_api.exceptions.challenge_info import *
from challenge_api.extensions_manager import logger

class UserChallengeInfoRepository:
    def __init__(self):
        self.db = db

    def exists(self, userChallenge_idx: int) -> bool:
        """사용자 챌린지 정보 존재 여부 확인
        
        Args:
            userChallenge_idx (int): 사용자 챌린지 인덱스
            
        Returns:
            bool: 존재 여부
        """
        return self.db.session.query(UserChallenge_Info)\
            .filter(UserChallenge_Info.userChallenge_idx == userChallenge_idx)\
            .first() is not None

    def create(self, userChallenge_idx:int, status:str, port:int):
        """사용자 챌린지 정보 생성
        
        Args:
            userChallenge_idx (int): 사용자 챌린지 인덱스
            status (str): 챌린지 상태
            port (int): 챌린지 포트

        Raises:
            UserChallengeInfoCreateError: 사용자 챌린지 정보 생성 실패
        """
        try:

            userChallenge_info = UserChallenge_Info(
                userChallenge_idx=userChallenge_idx,
                port=port if port else 0,
                status=status
            )
            self.db.session.add(userChallenge_info)
            self.db.session.commit()
            
        except Exception as e:
            err_msg = f"{UserChallengeInfoCreateError.__name__}: {userChallenge_idx} couldn't create info\n{e}"
            logger.error(err_msg)
            raise UserChallengeInfoCreateError(error_msg=err_msg) from e
    
    def update_status(self, info:UserChallenge_Info, status:str):
        """사용자 챌린지 상태 업데이트
        
        Args:
            userChallenge_idx (int): 사용자 챌린지 인덱스
            status (str): 챌린지 상태

        Raises:
            UserChallengeInfoUpdateError: 사용자 챌린지 상태 업데이트 실패
        """
        
        try:
            info.status = status
            self.db.session.commit()
        except Exception as e:
            err_msg = f"{UserChallengeInfoUpdateError.__name__}: {info.userChallenge_idx} couldn't update info\n{e}"
            logger.error(err_msg)
            raise UserChallengeInfoUpdateError(error_msg=err_msg) from e
            
    
    def update_port(self, info:UserChallenge_Info, port:int):
        """사용자 챌린지 포트 업데이트
        
        Args:
            userChallenge_idx (int): 사용자 챌린지 인덱스
            port (int): 챌린지 포트

        Raises:
            UserChallengeInfoUpdateError: 사용자 챌린지 포트 업데이트 실패
        """
        
        try:
            info.port = port
            self.db.session.commit()
            
        except Exception as e:
            err_msg = f"{UserChallengeInfoUpdateError.__name__}: {info.userChallenge_idx} couldn't update info\n{e}"
            logger.error(err_msg)
            raise UserChallengeInfoUpdateError(error_msg=err_msg) from e

    def update_all(self, userChallenge_idx:int, status:str, port:int):
        """사용자 챌린지 정보 업데이트
        
        Args:
            userChallenge_idx (int): 사용자 챌린지 인덱스
            status (str): 챌린지 상태
            port (int): 챌린지 포트

        Raises:
            UserChallengeInfoUpdateError: 사용자 챌린지 정보 업데이트 실패
        """
        
        try:
            info = self._get_first(userChallenge_idx)
            self.update_status(info, status)
            self.update_port(info, port)
            self.db.session.commit()
            
        except Exception as e:
            err_msg = f"{UserChallengeInfoUpdateError.__name__}: {userChallenge_idx} couldn't update info\n{e}"
            logger.error(err_msg)
            raise UserChallengeInfoUpdateError(error_msg=err_msg) from e

    def get_first(self, userChallenge_idx:int)->UserChallenge_Info:
        return self._get_first(userChallenge_idx=userChallenge_idx)
    
    def _get_first(self, userChallenge_idx:int)->UserChallenge_Info:
        """사용자 챌린지 정보 조회
        
        Args:
            userChallenge_idx (int): 사용자 챌린지 인덱스
        """
        try:
            userChallenge_info = self.db.session.query(UserChallenge_Info)\
                .filter(UserChallenge_Info.userChallenge_idx == userChallenge_idx)\
                .order_by(UserChallenge_Info.createdAt.desc())\
                .first()
            
            if not userChallenge_info:
                raise UserChallengeInfoNotFound(error_msg=f"{userChallenge_idx} couldn't find info")
            
            return userChallenge_info
        
        except Exception as e:
            err_msg = f"{UserChallengeInfoGetError.__name__}: {userChallenge_idx} couldn't get info\n{e}"
            logger.error(err_msg)
            raise UserChallengeInfoGetError(error_msg=err_msg) from e

    def get_status(self, userChallenge_idx:int)->Tuple[str,int]:
        """사용자 챌린지 상태 조회
        
        Args:
            userChallenge_idx (int): 사용자 챌린지 인덱스
        """
        try:
            info = self._get_first(userChallenge_idx)
            return info.status, info.port
        except Exception as e:
            err_msg = f"{UserChallengeInfoGetError.__name__}: {userChallenge_idx} couldn't get info\n{e}"
            logger.error(err_msg)
            raise UserChallengeInfoGetError(error_msg=err_msg) from e

    