from typing import Optional
from challenge_api.app.repository.userchallenge import UserChallengeRepository
from challenge_api.app.repository.challenge import ChallengeRepository
from challenge_api.app.repository.status import StatusRepository
from challenge_api.app.external.k8s import K8sManager
from challenge_api.app.schema import ChallengeRequest, StatusData, K8sChallengeData
from challenge_api.app.common.exceptions import (
    UserChallengeCreationException,
    InvalidInputValue
)

import logging

logger = logging.getLogger(__name__)


class UserChallengeService:
    def __init__(
        self, 
        user_challenge_repo: UserChallengeRepository,
        challenge_repo: ChallengeRepository,
        status_repo: StatusRepository,
        k8s_manager: K8sManager
    ):
        self.user_challenge_repo = user_challenge_repo
        self.challenge_repo = challenge_repo
        self.status_repo = status_repo  
        self.k8s_manager = k8s_manager
    
    def create(self, data: ChallengeRequest) -> int:
        """
        사용자 챌린지를 생성하고 실행 중인 포트를 반환합니다.
        
        Args:
            data: 챌린지 생성 요청 데이터
            
        Returns:
            int: 챌린지가 실행되는 포트 번호
            
        Raises:
            InvalidInputValue: 잘못된 입력값이 제공된 경우
            UserChallengeCreationException: 챌린지 생성에 실패한 경우
        """
        try:
            # 1. 기존 챌린지 상태 확인
            existing_challenge = self._get_existing_user_challenge(data)
            
            if existing_challenge:
                logger.info(f"Found existing challenge for user {data.user_id}, challenge {data.challenge_id}")
                return self._handle_existing_challenge(existing_challenge)
            
            # 2. 새로운 챌린지 생성
            logger.info(f"Creating new challenge for user {data.user_id}, challenge {data.challenge_id}")
            return self._create_new_user_challenge(data)
            
        except Exception as e:
            logger.error(f"Failed to create user challenge: {str(e)}")
            raise UserChallengeCreationException(
                message=f"Failed to create challenge for user {data.user_id}: {str(e)}"
            )
    
    def _get_existing_user_challenge(self, data: ChallengeRequest) -> Optional[StatusData]:
        """
        기존 사용자 챌린지가 있는지 확인합니다.
        
        Args:
            data: 챌린지 요청 데이터
            
        Returns:
            StatusData 또는 None
        """
        # 사용자의 해당 챌린지에 대한 UserChallenge 조회
        user_challenge = self.user_challenge_repo.get(
            user_idx=data.user_id,
            C_idx=data.challenge_id
        )
        
        if not user_challenge:
            return None
        
        # 해당 UserChallenge의 최신 상태 조회
        try:
            return self.status_repo.first(user_challenge.idx)
        except Exception:
            # 상태가 없는 경우 None 반환
            return None
    
    def _create_new_user_challenge(self, data: ChallengeRequest) -> int:
        """
        새로운 사용자 챌린지를 생성합니다.
        
        Args:
            data: 챌린지 생성 요청 데이터
            
        Returns:
            int: 실행 중인 챌린지의 포트 번호
        """
        # 1. UserChallenge 생성
        user_challenge = self.user_challenge_repo.create(
            user_idx=data.user_id,
            C_idx=data.challenge_id,
            userChallengeName=data.name
        )
        
        # 2. 초기 상태 생성
        initial_status = self.status_repo.create(
            user_challenge_idx=user_challenge.idx,
            status='None',
            port=0
        )
        
        # 3. K8s 리소스 생성 및 상태 업데이트
        return self._start_challenge(initial_status)
    
    def _handle_existing_challenge(self, status_data: StatusData) -> int:
        """
        기존 챌린지의 상태에 따라 적절한 처리를 수행합니다.
        
        Args:
            status_data: 챌린지 상태 데이터
            
        Returns:
            int: 실행 중인 챌린지의 포트 번호
        """
        # 이미 실행 중인 경우 기존 포트 반환
        if status_data.status == 'Running' and status_data.port > 0:
            logger.info(f"Challenge already running on port {status_data.port}")
            return status_data.port
        
        # 중지되었거나 초기 상태인 경우 새로 시작
        return self._start_challenge(status_data)
    
    def _start_challenge(self, status_data: StatusData) -> int:
        """
        챌린지를 시작하고 상태를 업데이트합니다.
        
        Args:
            status_data: 챌린지 상태 데이터
            
        Returns:
            int: 할당된 포트 번호
        """
        try:
            # K8s 챌린지 리소스 생성
            endpoint = self._create_k8s_challenge(status_data)
            
            # 상태 업데이트
            self.status_repo.update(
                userchallenge_idx=status_data.user_challenge_idx,
                status='Running',
                port=endpoint
            )
            
            logger.info(f"Challenge started successfully on port {endpoint}")
            return endpoint
            
        except Exception as e:
            # 실패한 경우 상태를 Error로 업데이트
            try:
                self.status_repo.update(
                    userchallenge_idx=status_data.user_challenge_idx,
                    status='Error',
                    port=0
                )
            except Exception:
                logger.error("Failed to update status to Error")
            
            raise UserChallengeCreationException(
                message=f"Failed to start challenge: {str(e)}"
            )
    
    def _create_k8s_challenge(self, status_data: StatusData) -> int:
        """
        K8s 챌린지 리소스를 생성하고 엔드포인트를 반환합니다.
        
        Args:
            status_data: 챌린지 상태 데이터
            
        Returns:
            int: 할당된 엔드포인트 포트
            
        Raises:
            UserChallengeCreationException: K8s 리소스 생성 실패 시
        """
        try:
            # UserChallenge 정보 조회
            user_challenge = self.user_challenge_repo.get_by_id(status_data.user_challenge_idx)
            if not user_challenge:
                raise ValueError(f"UserChallenge not found: {status_data.user_challenge_idx}")
            
            # 챌린지 정의 조회
            challenge_definition = self.challenge_repo.get_name(user_challenge.C_idx)
            if not challenge_definition:
                raise ValueError(f"Challenge definition not found: {user_challenge.C_idx}")
            
            # K8s 데이터 구성
            k8s_data = K8sChallengeData(
                challenge_id=user_challenge.C_idx,  # 실제 challenge_id 사용
                user_id=user_challenge.user_idx,    # 실제 user_id 사용
                userchallenge_name=user_challenge.userChallengeName,
                definition=challenge_definition
            )
            
            # K8s 리소스 생성
            endpoint = self.k8s_manager.create(k8s_data)
            
            if not endpoint or endpoint <= 0:
                raise ValueError("Invalid endpoint received from K8s manager")
            
            return endpoint
            
        except Exception as e:
            logger.error(f"Failed to create K8s challenge: {str(e)}")
            raise UserChallengeCreationException(
                message=f"Failed to create K8s challenge: {str(e)}"
            )