from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
import time

from challenge_api.exceptions.challenge_exceptions import ChallengeNotFound
from challenge_api.exceptions.userchallenge_exceptions import UserChallengeCreationError, UserChallengeDeletionError
from challenge_api.db.repository import ChallengeRepository, UserChallengesRepository, UserChallengeStatusRepository, UserChallengeInfoRepository
from challenge_api.objects.challenge_info import ChallengeInfo
from challenge_api.utils.namebuilder import NameBuilder
from challenge_api.extensions_manager import logger
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
        
        
        
        try:
            # Repository 
            userchallenge_repo = UserChallengesRepository()
            
            # user id를 숫자 대신에 문자로 표현 
            challenge_id, user_id = data.challenge_id, str(data.user_id)
            logger.info(f"Creating challenge", extra={
                'challenge_id': challenge_id,
                'user_id': user_id,
                'operation': 'create_challenge'
            })

            namebuilder = NameBuilder(challenge_id=challenge_id, user_id=user_id)
            challenge_info = namebuilder.build()

            # Database에 UserChallenge 생성
            userchallenge = None 
            if not userchallenge_repo.is_exist(challenge_info):
                logger.debug("Creating new userchallenge", extra={
                    'challenge_name': challenge_info.name,
                    'operation': 'create_userchallenge'
                })
                userchallenge = userchallenge_repo.create(challenge_info=challenge_info)
            else:
                logger.debug("Fetching existing userchallenge", extra={
                    'challenge_name': challenge_info.name,
                    'operation': 'get_userchallenge'
                })
                userchallenge = userchallenge_repo.get_by_user_challenge_name(challenge_info.name)

            if not userchallenge:
                raise UserChallengeCreationError(error_msg=f"Failed to create userchallenge: {challenge_info.name}")
            
            
            manifest = self._get_definition_manifest(challenge_info)
            logger.debug("Creating k8s challenge resource", extra={
                'challenge_name': challenge_info.name,
                'manifest': manifest,
                'operation': 'create_k8s_resource'
            })
            _ = self.custom_api.create_namespaced_custom_object(
                group="apps.hexactf.io",
                version="v2alpha1",
                namespace=namespace,
                plural="challenges",
                body=manifest
            )
        
            status = None
            endpoint = 0
            field_selector = f"apps.hexactf.io/challengeId={challenge_id},apps.hexactf.io/userId={user_id}"
            
            logger.debug("Waiting for challenge status", extra={
                'challenge_name': challenge_info.name,
                'field_selector': field_selector,
                'operation': 'wait_challenge_status'
            })
            
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
                    logger.info("Challenge is running", extra={
                        'challenge_name': challenge_info.name,
                        'endpoint': endpoint,
                        'operation': 'challenge_running'
                    })
                    w.stop()
                    break
            
            if not endpoint:
                logger.error("Failed to get endpoint", extra={
                    'challenge_name': challenge_info.name,
                    'operation': 'get_endpoint_failed'
                })
                raise UserChallengeCreationError(error_msg=f"Failed to get NodePort for Challenge: {challenge_info.name}")
            
            userchallenge_info_repo = UserChallengeInfoRepository()
            userchallenge_info_repo.create(userChallenge_idx=userchallenge.idx, status='Running', port=int(endpoint))
            
            logger.info("Challenge created successfully", extra={
                'challenge_name': challenge_info.name,
                'endpoint': endpoint,
                'operation': 'challenge_created'
            })
            return endpoint
        
        
        except ApiException as e:
            # conflict
            if e.status == 409:
                logger.warning("Challenge already exists, attempting deletion", extra={
                    'challenge_name': challenge_info.name,
                    'error': str(e),
                    'operation': 'handle_conflict'
                })
                self.delete(challenge_info=challenge_info)
                
            logger.error("Kubernetes API error", extra={
                'challenge_name': challenge_info.name if 'challenge_info' in locals() else None,
                'error': str(e),
                'status_code': e.status if hasattr(e, 'status') else None,
                'operation': 'k8s_api_error'
            })
            raise UserChallengeCreationError(error_msg=str(e)) from e
        except Exception as e:
            logger.error("Unexpected error during challenge creation", extra={
                'challenge_name': challenge_info.name if 'challenge_info' in locals() else None,
                'error': str(e),
                'error_type': type(e).__name__,
                'operation': 'unexpected_error'
            })
            raise UserChallengeCreationError(error_msg=str(e)) from e
        
        

    def _get_definition_manifest(self, challenge_info:ChallengeInfo) -> dict:
        challenge_id, user_id, challenge_name = challenge_info.challenge_id, challenge_info.user_id, challenge_info.name
        
        # Definition 조회 
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
                "name": challenge_name,
                "labels": {
                    "apps.hexactf.io/challengeId": str(challenge_id),
                    "apps.hexactf.io/userId": str(user_id)
                }
            },
            "spec": {
                "namespace": "challenge",
                "definition": challenge_definition
            }
        }
        return challenge_manifest
    
    def _is_deleted(self, challenge_info: ChallengeInfo, namespace="challenge"):
        field_selector = f"apps.hexactf.io/challengeId={challenge_info.challenge_id},apps.hexactf.io/userId={challenge_info.user_id}"
        w = watch.Watch()
        try:
            for event in w.stream(self.custom_api.list_namespaced_custom_object,
                                  group="apps.hexactf.io",
                                  version="v2alpha1",
                                  namespace=namespace,
                                  label_selector=field_selector,
                                  plural="challenges",
                                  timeout_seconds=30):
                if event['type'] == 'Deleted':
                    w.stop()
                    return True
        except ApiException as e:
            raise UserChallengeDeletionError(error_msg=str(e)) from e
        except Exception as e:
            raise UserChallengeDeletionError(error_msg=str(e)) from e
        finally:
            w.stop()
            return False
    
    def delete(self, challenge_info: ChallengeInfo, namespace="challenge"):
        """
        Challenge Custom Resource를 삭제합니다.
        
        Args:
            challenge_info (ChallengeInfo): Challenge 삭제 요청 데이터
            namespace (str): Challenge가 생성된 네임스페이스 (기본값: "default")
            
        Raises:
            UserChallengeDeletionError: Challenge 삭제에 실패했을 때
        """
        
        
        # 사용자 챌린지(컨테이너) 삭제 
        try:
            namebuilder = NameBuilder(challenge_id=challenge_info.challenge_id, user_id=challenge_info.user_id)
            challenge_info = namebuilder.build()

            # UserChallenge 조회
            user_challenge_repo = UserChallengesRepository()
            if not user_challenge_repo.is_exist(challenge_info):
                raise UserChallengeDeletionError(error_msg=f"Deletion : UserChallenge not found: {challenge_info.name}")
            
            user_challenge = user_challenge_repo.get_by_user_challenge_name(challenge_info.name)
            if not user_challenge:
                raise UserChallengeDeletionError(error_msg=f"Deletion : UserChallenge not found: {challenge_info.name}")
            
            # Delete Kubernetes Resources
            self.custom_api.delete_namespaced_custom_object(
                group="apps.hexactf.io",
                version="v2alpha1",
                namespace=namespace,
                plural="challenges",
                name=challenge_info.name
            )
            
            # isDeleted = self._is_deleted(challenge_info)
            # if not isDeleted:
            #     raise UserChallengeDeletionError(error_msg=f"Deletion : Failed to delete challenge: {challenge_info.name}")
            time.sleep(3)
            # Update the status in database
            userchallenge_info_repo = UserChallengeInfoRepository()
            info = userchallenge_info_repo.get_first(userChallenge_idx=user_challenge.idx)
            userchallenge_info_repo.update_status(info, 'Deleted')
            
        except ApiException as e:            
            # Kubernetes API 에러 
            raise UserChallengeDeletionError(error_msg=str(e)) from e
        except Exception as e:
            raise UserChallengeDeletionError(error_msg=str(e)) from e
 
