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
                

            # Challenge manifest 생성
            challenge_manifest = {
                "apiVersion": "apps.hexactf.io/v1alpha1",
                "kind": "Challenge",
                "metadata": {
                    "name": challenge_name,
                    "labels": {
                        "apps.hexactf.io/problemId": str(challenge_id),
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

            endpoint = challenge['status']['endpoint']
            # NodePort update
            if endpoint:
                success = UserChallengesRepository.update_port(challenge_name, endpoint)
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
    
 
