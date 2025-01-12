import time

from kubernetes import client, config

import logging

from app.extensions.db.exceptions import DBUpdateError
from app.extensions.db.repository import ChallengeRepository, UserChallengesRepository
from app.extensions.k8s.exceptions import ChallengeConflictError, UserChallengeRequestError
from app.utils.exceptions import ApiException


MAX_RETRIES = 3
SLEEP_INTERVAL = 2

logger = logging.getLogger(__name__)

class K8sClient:
    def __init__(self):
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        self.custom_api = client.CustomObjectsApi()
        self.core_api = client.CoreV1Api()

    
    def create_challenge_resource(self, challenge_id, username, namespace="default") -> int:
        """
        Challenge CR를 생성한 후 NodePort를 확인한다.
        
        return: endpoint(NodePort) 
        """
        try:
            
            user_challenge_repo = UserChallengesRepository()
            
            # Challenge definition 조회
            challenge_definition = ChallengeRepository.get_challenge_name(challenge_id)
            if not challenge_definition:
                raise UserChallengeRequestError(f"Challenge definition not found for ID: {challenge_id}")

            # Challenge name 생성 및 검증
            challenge_name = f"challenge-{challenge_id}-{username}"
            if not self._is_valid_k8s_name(challenge_name):
                raise UserChallengeRequestError(f"Invalid challenge name: {challenge_name}")

            # Namespace 존재 여부 확인
            try:
                self.core_api.read_namespace(namespace)
            except ApiException as e:
                if e.status == 404:
                    raise UserChallengeRequestError(f"Namespace not found: {namespace}")
            
            # Database에 UserChallenge 생성 
            user_challenge = user_challenge_repo.get_by_user_challenge_name(challenge_name)
            if not user_challenge:
                user_challenge = user_challenge_repo.create(username, challenge_id, challenge_name, 0)

            # Challenge manifest 생성
            challenge_manifest = {
                "apiVersion": "apps.hexactf.io/v1alpha1",
                "kind": "Challenge",
                "metadata": {
                    "name": challenge_name,
                    "labels": {
                        "apps.hexactf.io/challengeId": str(challenge_id),
                        "apps.hexactf.io/user": username
                    }
                },
                "spec": {
                    "namespace": namespace,
                    "definition": challenge_definition
                }
            }
            
            challenge = self.custom_api.create_namespaced_custom_object(
                group="apps.hexactf.io",
                version="v1alpha1",
                namespace=namespace,
                plural="challenges",
                body=challenge_manifest
            )
            logger.info(f"Created Challenge: {challenge}")

            # status 값 가져오기
            status = challenge.get('status', {})
            endpoint = status.get('endpoint')
            logger.info(f"Challenge Status: {status}")
            logger.info(f"Challenge Endpoint: {endpoint}")

            # status가 아직 설정되지 않았을 수 있으므로, 필요한 경우 다시 조회
            if not status:
                time.sleep(3)  
                challenge = self.custom_api.get_namespaced_custom_object(
                    group="apps.hexactf.io",
                    version="v1alpha1",
                    namespace=namespace,
                    plural="challenges",
                    name=challenge['metadata']['name']
                )
                status = challenge.get('status', {})
                endpoint = status.get('endpoint')
                logger.info(f"Updated Challenge Status: {status}")
                logger.info(f"Updated Challenge Endpoint: {endpoint}")
            
            
            if endpoint:
                success = user_challenge_repo.update_port(user_challenge, int(endpoint))
                if not success:
                    raise DBUpdateError(f"Failed to update UserChallenge with NodePort: {endpoint}")

            return endpoint
        except ApiException as e:
            if e.status == 409:
                raise ChallengeConflictError(
                    f"Challenge already exists: {challenge_name}"
                )
            else:
                raise UserChallengeRequestError(
                    f"Kubernetes API error: {e.reason}",
                    e.status
                )
        

    def _is_valid_k8s_name(self, name: str) -> bool:
        """
        Kubernetes 리소스 이름 유효성 검사
        """
        # Kubernetes naming convention 검사
        if not name or len(name) > 253:
            return False
        
        # DNS-1123 label 규칙 검사
        import re
        pattern = r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
        return bool(re.match(pattern, name))
    
 
