import os
import time

from kubernetes import client, config

from app.exceptions.challenge import ChallengeNotFound
from app.exceptions.userchallenge import UserChallengeCreationError, UserChallengeDeletionError
from app.extensions.db.repository import ChallengeRepository, UserChallengesRepository
from app.monitoring.loki_logger import FlaskLokiLogger


MAX_RETRIES = 3
SLEEP_INTERVAL = 2


class K8sClient:
    """
    Kubernetes Custom Resource 관리를 위한 클라이언트 클래스
    
    Challenge Custom Resource를 생성, 삭제하고 상태를 관리합니다.
    클러스터 내부 또는 외부에서 실행될 수 있도록 설정을 자동으로 로드합니다.
    """
    
    def __init__(self):
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        self.custom_api = client.CustomObjectsApi()
        self.core_api = client.CoreV1Api()

    
    def create_challenge_resource(self, challenge_id, username, namespace="default") -> int:
        """
        Challenge Custom Resource를 생성하고 NodePort를 반환합니다.
        
        Args:
            challenge_id (str): 생성할 Challenge의 ID
            username (str): Challenge를 생성하는 사용자 이름
            namespace (str): Challenge를 생성할 네임스페이스 (기본값: "default")
            
        Returns:
            int: 할당된 NodePort 번호
            
        Raises:
            ChallengeNotFound: Challenge ID에 해당하는 Challenge가 없을 때
            ChallengeCreationError: Challenge Custom Resource 생성에 실패했을 때

        """
        
        user_challenge_repo = UserChallengesRepository()
            
        # Challenge definition 조회
        challenge_definition = ChallengeRepository.get_challenge_name(challenge_id)
        if not challenge_definition:
            raise ChallengeNotFound(error_msg=f"Challenge definition not found for ID: {challenge_id}")

        # Challenge name 생성 및 검증
        challenge_name = f"challenge-{challenge_id}-{username}"
        if not self._is_valid_k8s_name(challenge_name):
            raise UserChallengeCreationError(error_msg=f"Invalid challenge name: {challenge_name}")

        # Namespace 존재 여부 확인
        try:
            self.core_api.read_namespace(namespace)
        except Exception as e:
            raise UserChallengeCreationError(error_msg=str(e))
            
        # Database에 UserChallenge 생성 
        user_challenge = user_challenge_repo.get_by_user_challenge_name(challenge_name)
        if not user_challenge:
            user_challenge = user_challenge_repo.create(username, challenge_id, challenge_name, 0)
        else:
            # 이미 실행 중인 Challenge가 있으면 데이터베이스에 저장된 포트 번호 반환
            if user_challenge.status == 'Running':
                return user_challenge.port
        
        # 공백의 경우 하이픈으로 변환
        challenge_definition = self._normalize_k8s_name(challenge_definition)
        
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

        # status 값 가져오기
        status = challenge.get('status', {})
        endpoint = status.get('endpoint')

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
        
        # NodePort 업데이트
        if not endpoint:
            raise UserChallengeCreationError(error_msg=f"Failed to get NodePort for Challenge: {challenge_name}")
        
        success = user_challenge_repo.update_port(user_challenge, int(endpoint))
        if not success:
            raise UserChallengeCreationError(error_msg=f"Failed to update UserChallenge with NodePort: {endpoint}")
    
        return endpoint
        
        
    def _normalize_k8s_name(name: str) -> str:
        """
        Kubernetes 리소스 이름을 유효한 형식으로 변환 (소문자 + 공백을 하이픈으로 변경)

        Args:
            name (str): 원본 이름

        Returns:
            str: 변환된 Kubernetes 리소스 이름
        """
        if not name or len(name) > 253:
            raise ValueError("이름이 비어있거나 길이가 253자를 초과함")

        # 1. 소문자로 변환
        name = name.lower()

        # 2. 공백 및 비허용 문자 (`[^a-z0-9-]`)를 `-`로 변환
        name = re.sub(r'[^a-z0-9-]+', '-', name)

        # 3. 하이픈(-)이 연속적으로 나오면 하나로 줄이기
        name = re.sub(r'-+', '-', name)

        # 4. 앞뒤의 하이픈 제거
        name = name.strip('-')

        # 5. 최종 길이 검사 (1~253자)
        if not name or len(name) > 253:
            raise ValueError(f"변환 후에도 유효하지 않은 Kubernetes 리소스 이름: {name}")

        return name

    def _is_valid_k8s_name(self, name: str) -> bool:
        """
        Kubernetes 리소스 이름 유효성 검사
        
        Args:
            name (str): 검사할 이름
            
        Returns:
            bool: 유효한 이름인지 여부
        """
        
        # 소문자로 변환 
        name = name.lower()
        
        # Kubernetes naming convention 검사
        if not name or len(name) > 253:
            return False
        
        # DNS-1123 label 규칙 검사
        import re
        pattern = r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
        return bool(re.match(pattern, name))
    
    def delete_userchallenge(self, username, challenge_id, namespace="default"):
        """
        Challenge Custom Resource를 삭제합니다.
        
        Args:
            username (str): Challenge를 생성한 사용자 이름
            challenge_id (str): 삭제할 Challenge의 ID
            namespace (str): Challenge가 생성된 네임스페이스 (기본값: "default")
            
        Raises:
            UserChallengeDeletionError: Challenge 삭제에 실패했을 때
        """
        
        # UserChallenge 조회 
        username = username.lower() # 소문자로 변환
        challenge_name = f"challenge-{challenge_id}-{username}"
        user_challenge_repo = UserChallengesRepository()
        user_challenge = user_challenge_repo.get_by_user_challenge_name(challenge_name)
        if not user_challenge:
            raise UserChallengeDeletionError(error_msg=f"Deletion : UserChallenge not found: {challenge_name}")
        
        # 사용자 챌린지(컨테이너) 삭제 
        try:
            self.custom_api.delete_namespaced_custom_object(
                group="apps.hexactf.io",
                version="v1alpha1",
                namespace=namespace,
                plural="challenges",
                name=challenge_name
            )
            
        except Exception as e:
            raise UserChallengeDeletionError(error_msg=str(e)) from e
 
