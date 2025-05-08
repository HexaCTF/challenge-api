import os
import re
import time

from kubernetes import client, config, watch

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

    
    def create(self, data:ChallengeInfo, namespace="challenge") -> int:
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
        
        # Repository 
        userchallenge_repo = UserChallengesRepository()
        userchallenge_status_repo = UserChallengeStatusRepository()
        
        # user id를 숫자 대신에 문자로 표현 
        challenge_id, user_id = data.challenge_id, str(data.user_id)
        
        namebuilder = NameBuilder(challenge_id=challenge_id, user_id=user_id)
        challenge_info= namebuilder.build()
        
        # Database에 UserChallenge 생성
         
        if not userchallenge_repo.is_exist(challenge_info):
            userchallenge = userchallenge_repo.create(challenge_info)
            # Create initial status with Pending state
            userchallenge_status_repo.create(userchallenge_idx=userchallenge.idx, port=0)
        else:
            userchallenge = userchallenge_repo.get_by_user_challenge_name(challenge_info.name)
            recent = userchallenge_status_repo.get_recent_status(userchallenge.idx)
            # 이미 실행 중인 Challenge가 있으면 데이터베이스에 저장된 포트 번호 반환
            if recent and recent.status == 'Running':
                return recent.port
        
            
        # Challenge definition 조회
        challenge_definition = ChallengeRepository.get_challenge_name(challenge_id)
        if not challenge_definition:
            raise ChallengeNotFound(error_msg=f"Challenge definition not found for ID: {challenge_id}")
        # Challenge name 생성 및 검증

        # Namespace 존재 여부 확인
        # TODO: 환경 체크 로직 분리 
        # try:
        #     self.core_api.read_namespace(namespace)
        # except Exception as e:
        #     raise UserChallengeCreationError(error_msg=str(e))

        # 공백의 경우 하이픈으로 변환
        # TODO: Definition 이름에 따른 정규화 로직 추가
        # challenge_definition = self._normalize_k8s_name(challenge_definition)
        # valid_username = self._normalize_k8s_name(username)
        # Challenge manifest 생성
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
            
        challenge = self.custom_api.create_namespaced_custom_object(
            group="apps.hexactf.io",
            version="v2alpha1",
            namespace=namespace,
            plural="challenges",
            body=challenge_manifest
        )
        
        status = None
        endpoint = 0
        field_selector = f"apps.hexactf.io/challengeId={challenge_id},apps.hexactf.io/userId={user_id}"
        w = watch.Watch()
        for event in w.stream(self.custom_api.list_namespaced_custom_object,
                              group="apps.hexactf.io",
                              version="v2alpha1",
                              namespace=namespace,
                              label_selector=field_selector,
                              plural="challenges",
                              ):
            obj = event['object']
            
            if obj.get('status', {}).get('currentStatus', {}).get('status',"") == 'Running':
                status = event['object']['status']
                endpoint = status.get('endpoint')
                w.stop()
                break


        # status가 아직 설정되지 않았을 수 있으므로, 필요한 경우 다시 조회
        # if not status:
        #     time.sleep(3)  
        #     challenge = self.custom_api.get_namespaced_custom_object(
        #         group="apps.hexactf.io",
        #         version="v1alpha1",
        #         namespace=namespace,
        #         plural="challenges",
        #         name=challenge['metadata']['name']
        #     )
        #     status = challenge.get('status', {})
        #     endpoint = status.get('endpoint')
        
        # NodePort 업데이트
        if not endpoint:
            raise UserChallengeCreationError(error_msg=f"Failed to get NodePort for Challenge: {challenge_info.name}")
        
        return endpoint
        

    # TODO: 별도의 Validator로 분리 
    # def _normalize_k8s_name(self, name: str) -> str:
    #     """
    #     Kubernetes 리소스 이름을 유효한 형식으로 변환 (소문자 + 공백을 하이픈으로 변경)

    #     Args:
    #         name (str): 원본 이름

    #     Returns:
    #         str: 변환된 Kubernetes 리소스 이름
    #     """
    #     if not name or len(name) > 253:
    #         raise ValueError("이름이 비어있거나 길이가 253자를 초과함")

    #     name = name.lower()
    #     name = re.sub(r'[^a-z0-9-]+', '-', name)
    #     name = re.sub(r'-+', '-', name)
    #     name = name.strip('-')

    #     # 최종 길이 검사 (1~253자)
    #     if not name or len(name) > 253:
    #         raise ValueError(f"변환 후에도 유효하지 않은 Kubernetes 리소스 이름: {name}")

    #     return name

    # def _is_valid_k8s_name(self, name: str) -> bool:
    #     """
    #     Kubernetes 리소스 이름 유효성 검사
        
    #     Args:
    #         name (str): 검사할 이름
            
    #     Returns:
    #         bool: 유효한 이름인지 여부
    #     """
        
    #     # 소문자로 변환 
    #     name = name.lower()
        
    #     # Kubernetes naming convention 검사
    #     if not name or len(name) > 253:
    #         return False
        
    #     # DNS-1123 label 규칙 검사
    #     import re
    #     pattern = r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
    #     return bool(re.match(pattern, name))
    
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
 
