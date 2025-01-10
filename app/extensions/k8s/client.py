import time

from kubernetes import client, config

import logging

from app.extensions.db.exceptions import DBUpdateError
from app.extensions.db.repository import ChallengeRepository, UserChallengesRepository
from app.extensions.k8s.exceptions import ChallengeConflictError, ChallengeRequestError, OperatorRequestError, UserChallengeRequestError
from app.utils.exceptions import ApiException

MAX_RETRIES = 5
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

    
    def create_challenge_resource(self, challenge_id, username, namespace="default"):
        """
        Challenge CR를 생성한 후 NodePort를 확인한다.
        TODO - 코드 정리 필요 
        1. ChallengeDefinition 조회 및 필요 정보 추출
        2. Challenge 생성
        3. NodePort 확인, 없다면 재시도 
        4. NodePort 업데이트
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
            
            retry_count = 0
            endpoint = None 
            while retry_count < MAX_RETRIES:
                try:
                    # Challenge CR 생성
                    challenge = self.custom_api.create_namespaced_custom_object(
                        group="apps.hexactf.io",
                        version="v1alpha1",
                        namespace=namespace,
                        plural="challenges",
                        body=challenge_manifest
                    )
                    
                    # Challenge status 확인
                    if not challenge['status']:
                        retry_count +=1
                        time.sleep(SLEEP_INTERVAL)
                        continue
                        
                    
                    if not challenge['status']['endpoint']:
                        retry_count +=1
                        time.sleep(SLEEP_INTERVAL)
                        continue
                    
                    endpoint = challenge['status']['endpoint']
                    # NodePort update
                    if endpoint:
                        success = UserChallengesRepository.update_port(challenge_name, endpoint)
                        if not success:
                            raise DBUpdateError(f"Failed to update UserChallenge with NodePort: {endpoint}")
                    
                except ApiException as e:
                    if e.status == 409:
                        # TODO - 
                        pass 
                    else:
                        retry_count += 1
                        time.sleep(SLEEP_INTERVAL)

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
    
    def _get_service_nodeport(self, user, challenge_id, namespace="default"):
        """Get NodePort from the service using the correct service name pattern"""
        try:
            service_name = f"svc-{user}-{challenge_id}"

            service = self.core_api.read_namespaced_service(
                name=service_name,
                namespace=namespace
            )

            if service.spec.ports:
                nodeport = service.spec.ports[0].node_port
                return nodeport

            logger.warning(f"No ports found for service {service_name}")
            return None

        except client.rest.ApiException as e:
            if e.status == 404:
                logger.warning(f"Service {service_name} not found")
                return None
            else:
                raise UserChallengeRequestError(
                    f"NodePort error: {e.reason}",
                )
 
