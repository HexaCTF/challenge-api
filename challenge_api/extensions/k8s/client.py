import os
import re
import time
from typing import Optional, Tuple

from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

from challenge_api.exceptions.challenge_exceptions import ChallengeNotFound
from challenge_api.exceptions.userchallenge_exceptions import UserChallengeCreationError, UserChallengeDeletionError
from challenge_api.db.repository import ChallengeRepository, UserChallengesRepository, UserChallengeStatusRepository
from challenge_api.objects.challenge_info import ChallengeInfo
from challenge_api.utils.namebuilder import NameBuilder

MAX_RETRIES = 3
SLEEP_INTERVAL = 2

class K8sClient:
    """
    Client class for managing Kubernetes Custom Resources
    
    Creates, deletes, and manages the state of Challenge Custom Resources.
    Automatically loads configuration to run either inside or outside the cluster.
    """
    
    def __init__(self):
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        self.custom_api = client.CustomObjectsApi()
        self.core_api = client.CoreV1Api()

    def _cleanup_existing_challenge(self, challenge_info: ChallengeInfo, namespace: str) -> None:
        """
        기존 챌린지 리소스를 정리합니다.
        
        Args:
            challenge_info (ChallengeInfo): 정리할 챌린지 정보
            namespace (str): 챌린지가 있는 네임스페이스
        """
        try:
            self.custom_api.delete_namespaced_custom_object(
                group="apps.hexactf.io",
                version="v2alpha1",
                namespace=namespace,
                plural="challenges",
                name=challenge_info.name
            )
            # 삭제 완료 대기
            time.sleep(SLEEP_INTERVAL)
        except ApiException as e:
            if e.status != 404:  # 404는 이미 삭제된 경우
                raise UserChallengeCreationError(error_msg=f"Failed to cleanup existing challenge: {str(e)}")

    def _create_challenge_cr(self, challenge_manifest: dict, namespace: str) -> dict:
        """
        Challenge Custom Resource를 생성합니다.
        
        Args:
            challenge_manifest (dict): 생성할 챌린지 매니페스트
            namespace (str): 생성할 네임스페이스
            
        Returns:
            dict: 생성된 챌린지 CR
            
        Raises:
            UserChallengeCreationError: CR 생성 실패 시
        """
        try:
            return self.custom_api.create_namespaced_custom_object(
                group="apps.hexactf.io",
                version="v2alpha1",
                namespace=namespace,
                plural="challenges",
                body=challenge_manifest
            )
        except ApiException as e:
            if e.status == 409:  # Already Exists
                raise UserChallengeCreationError(error_msg=f"Challenge already exists: {challenge_manifest['metadata']['name']}")
            raise UserChallengeCreationError(error_msg=f"Failed to create challenge CR: {str(e)}")
        except Exception as e:
            raise UserChallengeCreationError(error_msg=f"Unexpected error while creating challenge CR: {str(e)}")

    def _wait_for_challenge_status(self, challenge_id: str, user_id: str, namespace: str) -> Tuple[Optional[dict], Optional[int]]:
        """
        챌린지의 Running 상태를 기다립니다.
        
        Args:
            challenge_id (str): 챌린지 ID
            user_id (str): 사용자 ID
            namespace (str): 네임스페이스
            
        Returns:
            Tuple[Optional[dict], Optional[int]]: (상태 정보, 엔드포인트)
        """
        status = None
        endpoint = None
        field_selector = f"apps.hexactf.io/challengeId={challenge_id},apps.hexactf.io/userId={user_id}"
        w = watch.Watch()
        
        try:
            for event in w.stream(
                self.custom_api.list_namespaced_custom_object,
                group="apps.hexactf.io",
                version="v2alpha1",
                namespace=namespace,
                label_selector=field_selector,
                plural="challenges",
                timeout_seconds=300
            ):
                obj = event['object']
                current_status = obj.get('status', {}).get('currentStatus', {}).get('status', "")
                
                if current_status == 'Running':
                    status = obj['status']
                    endpoint = status.get('endpoint')
                    w.stop()
                    break
                elif current_status == 'Error':
                    raise UserChallengeCreationError(error_msg=f"Challenge failed to start: {obj.get('status', {}).get('message', 'Unknown error')}")
                    
        except Exception as e:
            raise UserChallengeCreationError(error_msg=f"Failed to watch challenge status: {str(e)}")
            
        return status, endpoint

    def _update_challenge_status(self, userchallenge, endpoint: int, status_repo: UserChallengeStatusRepository) -> None:
        """
        챌린지 상태를 업데이트합니다.
        
        Args:
            userchallenge: 업데이트할 챌린지
            endpoint (int): 엔드포인트
            status_repo (UserChallengeStatusRepository): 상태 저장소
        """
        try:
            recent_status = status_repo.get_recent_status(userchallenge.idx)
            if recent_status:
                status_repo.update_status(recent_status.idx, 'Running')
                status_repo.update_port(recent_status.idx, endpoint)
            else:
                status_repo.create(userchallenge_idx=userchallenge.idx, port=endpoint, status='Running')
        except Exception as e:
            raise UserChallengeCreationError(error_msg=f"Failed to update challenge status: {str(e)}")

    def create(self, data: ChallengeInfo, namespace="challenge") -> int:
        """
        Challenge Custom Resource를 생성하고 NodePort를 반환합니다.
        
        Args:
            data (ChallengeRequest): Challenge 생성 요청 데이터
            namespace (str): Challenge를 생성할 네임스페이스 (기본값: "default")
            
        Returns:
            int: 할당된 NodePort 번호
            
        Raises:
            ChallengeNotFound: Challenge ID에 해당하는 Challenge가 없을 때
            UserChallengeCreationError: Challenge Custom Resource 생성에 실패했을 때
        """
        userchallenge_repo = UserChallengesRepository()
        userchallenge_status_repo = UserChallengeStatusRepository()
        challenge_id, user_id = data.challenge_id, str(data.user_id)
        
        namebuilder = NameBuilder(challenge_id=challenge_id, user_id=user_id)
        challenge_info = namebuilder.build()
        
        # 1. 데이터베이스 작업
        try:
            if not userchallenge_repo.is_exist(challenge_info):
                userchallenge = userchallenge_repo.create(challenge_info)
                userchallenge_status_repo.create(userchallenge_idx=userchallenge.idx, port=0, status='Pending')
            else:
                userchallenge = userchallenge_repo.get_by_user_challenge_name(challenge_info.name)
                if not userchallenge:
                    raise UserChallengeCreationError(error_msg=f"Failed to retrieve existing challenge: {challenge_info.name}")
                
                recent = userchallenge_status_repo.get_recent_status(userchallenge.idx)
                if recent and recent.status == 'Running':
                    return recent.port
        except Exception as e:
            raise UserChallengeCreationError(error_msg=f"Database operation failed: {str(e)}")
        
        # 2. Challenge definition 조회
        challenge_definition = ChallengeRepository.get_challenge_name(challenge_id)
        if not challenge_definition:
            raise ChallengeNotFound(error_msg=f"Challenge definition not found for ID: {challenge_id}")
        
        # 3. Challenge manifest 생성
        challenge_manifest = {
            "apiVersion": "apps.hexactf.io/v2alpha1",
            "kind": "Challenge",
            "metadata": {
                "name": challenge_info.name,
                "labels": {
                    "apps.hexactf.io/challengeId": str(challenge_id),
                    "apps.hexactf.io/userId": user_id
                }
            },
            "spec": {
                "namespace": namespace,
                "definition": challenge_definition
            }
        }
        
        # 4. 기존 리소스 정리
        try:
            self._cleanup_existing_challenge(challenge_info, namespace)
        except Exception as e:
            logger.warning(f"Failed to cleanup existing challenge: {str(e)}")
        
        # 5. Challenge CR 생성
        try:
            self._create_challenge_cr(challenge_manifest, namespace)
        except UserChallengeCreationError as e:
            if "already exists" in str(e):
                self._cleanup_existing_challenge(challenge_info, namespace)
                self._create_challenge_cr(challenge_manifest, namespace)
            else:
                raise
        
        # 6. 상태 대기 및 엔드포인트 획득
        status, endpoint = self._wait_for_challenge_status(challenge_id, user_id, namespace)
        
        if not endpoint:
            # 실패 시 롤백
            try:
                self._cleanup_existing_challenge(challenge_info, namespace)
            except Exception as e:
                logger.error(f"Failed to cleanup challenge after error: {str(e)}")
            raise UserChallengeCreationError(error_msg=f"Failed to get NodePort for Challenge: {challenge_info.name}")
        
        # 7. 상태 업데이트
        self._update_challenge_status(userchallenge, endpoint, userchallenge_status_repo)
        
        return endpoint

    def delete(self, challenge_info: ChallengeInfo, namespace="challenge"):
        """
        Challenge Custom Resource를 삭제합니다.
        
        Args:
            challenge_info (ChallengeInfo): Challenge 삭제 요청 데이터
            namespace (str): Challenge가 생성된 네임스페이스 (기본값: "default")
            
        Raises:
            UserChallengeDeletionError: Challenge 삭제에 실패했을 때
        """
        
        # UserChallenge 조회
        namebuilder = NameBuilder(challenge_id=challenge_info.challenge_id, user_id=challenge_info.user_id)
        challenge_info = namebuilder.build()
        user_challenge_repo = UserChallengesRepository()
        user_challenge = user_challenge_repo.get_by_user_challenge_name(challenge_info.name)
        if not user_challenge:
            raise UserChallengeDeletionError(error_msg=f"Deletion : UserChallenge not found: {challenge_info.name}")
        
        # 사용자 챌린지(컨테이너) 삭제 
        try:
            self.custom_api.delete_namespaced_custom_object(
                group="apps.hexactf.io",
                version="v2alpha1",
                namespace=namespace,
                plural="challenges",
                name=challenge_info.name
            )
            
        except Exception as e:
            raise UserChallengeDeletionError(error_msg=str(e)) from e
 
