from typing import Optional, Dict, Any
import time
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

from challenge_api.app.schema import K8sChallengeData, ChallengeRequest
from challenge_api.exceptions.service import (
    UserChallengeCreationException,
    UserChallengeDeletionException,
    K8sResourceException
)
import logging

logger = logging.getLogger(__name__)

NAMESPACE = "challenge"
DEFAULT_TIMEOUT = 300  # 5분
WATCH_TIMEOUT = 120   # 2분


class K8sManager:
    
    def __init__(self):
        """K8s 클라이언트를 초기화합니다."""
        self._initialize_k8s_clients()
    
    def _initialize_k8s_clients(self):
        """K8s 클라이언트를 초기화합니다."""
        try:
            # 클러스터 내부에서 실행 중인지 확인
            try:
                config.load_incluster_config()
                logger.info("Loaded in-cluster Kubernetes configuration")
            except config.ConfigException:
                config.load_kube_config()
                logger.info("Loaded local Kubernetes configuration")
                
            self.custom_api = client.CustomObjectsApi()
            self.core_api = client.CoreV1Api()
            
            # 클러스터 연결 테스트
            self._test_cluster_connection()
            
        except Exception as e:
            logger.error(f"Failed to initialize K8s clients: {str(e)}")
            raise K8sResourceException(f"K8s initialization failed: {str(e)}")
    
    def _test_cluster_connection(self):
        """클러스터 연결을 테스트합니다."""
        try:
            self.core_api.get_api_version()
            logger.info("K8s cluster connection successful")
        except Exception as e:
            logger.error(f"K8s cluster connection failed: {str(e)}")
            raise K8sResourceException(f"Cannot connect to K8s cluster: {str(e)}")
    
    def create(self, data: K8sChallengeData, timeout: int = DEFAULT_TIMEOUT) -> int:
        """
        Challenge Custom Resource를 생성하고 엔드포인트를 반환합니다.
        
        Args:
            data: K8s 챌린지 생성 데이터
            timeout: 생성 대기 시간 (초)
            
        Returns:
            int: 할당된 엔드포인트 포트
            
        Raises:
            UserChallengeCreationException: 챌린지 생성 실패 시
        """
        try:
            logger.info(f"Creating K8s challenge: {data.userchallenge_name}")
            
            # 1. 기존 리소스 확인 및 정리
            self._cleanup_existing_resource(data.userchallenge_name)
            
            # 2. Challenge 매니페스트 생성
            challenge_manifest = self._build_challenge_manifest(data)
            
            # 3. K8s 리소스 생성
            self._create_k8s_resource(challenge_manifest)
            
            # 4. 리소스 상태 대기 및 엔드포인트 조회
            endpoint = self._wait_for_challenge_ready(data, timeout)
            
            logger.info(f"Successfully created challenge {data.userchallenge_name} with endpoint {endpoint}")
            return endpoint
            
        except UserChallengeCreationException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating K8s challenge: {str(e)}")
            raise UserChallengeCreationException(f"Failed to create K8s challenge: {str(e)}")
    
    def _cleanup_existing_resource(self, resource_name: str):
        """기존 리소스가 있다면 정리합니다."""
        try:
            existing = self.custom_api.get_namespaced_custom_object(
                group="apps.hexactf.io",
                version="v2alpha1",
                namespace=NAMESPACE,
                plural="challenges",
                name=resource_name
            )
            
            if existing:
                logger.info(f"Found existing resource {resource_name}, deleting...")
                self._delete_resource(resource_name)
                # 삭제 완료까지 잠시 대기
                time.sleep(2)
                
        except ApiException as e:
            if e.status == 404:
                # 리소스가 없는 것은 정상
                logger.debug(f"No existing resource found: {resource_name}")
            else:
                logger.warning(f"Error checking existing resource: {str(e)}")
        except Exception as e:
            logger.warning(f"Unexpected error during cleanup: {str(e)}")
    
    def _build_challenge_manifest(self, data: K8sChallengeData) -> Dict[str, Any]:
        """Challenge 매니페스트를 구성합니다."""
        return {
            "apiVersion": "apps.hexactf.io/v2alpha1",
            "kind": "Challenge",
            "metadata": {
                "name": data.userchallenge_name,
                "namespace": NAMESPACE,
                "labels": {
                    "apps.hexactf.io/challengeId": str(data.challenge_id),
                    "apps.hexactf.io/userId": str(data.user_id),
                    "apps.hexactf.io/managed-by": "challenge-api"
                },
                "annotations": {
                    "apps.hexactf.io/created-at": str(int(time.time())),
                    "apps.hexactf.io/definition": data.definition
                }
            },
            "spec": {
                "namespace": NAMESPACE,
                "definition": data.definition,
                "challengeId": data.challenge_id,
                "userId": data.user_id
            }
        }
    
    def _create_k8s_resource(self, manifest: Dict[str, Any]):
        """K8s 리소스를 생성합니다."""
        try:
            result = self.custom_api.create_namespaced_custom_object(
                group="apps.hexactf.io",
                version="v2alpha1",
                namespace=NAMESPACE,
                plural="challenges",
                body=manifest
            )
            
            logger.info(f"Created K8s resource: {manifest['metadata']['name']}")
            return result
            
        except ApiException as e:
            logger.error(f"K8s API error creating resource: {e.status} - {e.reason}")
            raise UserChallengeCreationException(f"K8s API error: {e.reason}")
        except Exception as e:
            logger.error(f"Unexpected error creating K8s resource: {str(e)}")
            raise UserChallengeCreationException(f"Failed to create K8s resource: {str(e)}")
    
    def _wait_for_challenge_ready(self, data: K8sChallengeData, timeout: int) -> int:
        """
        Challenge가 준비될 때까지 대기하고 엔드포인트를 반환합니다.
        
        Args:
            data: K8s 챌린지 데이터
            timeout: 대기 시간 (초)
            
        Returns:
            int: 할당된 엔드포인트 포트
        """
        field_selector = f"metadata.name={data.userchallenge_name}"
        w = watch.Watch()
        
        start_time = time.time()
        
        try:
            logger.info(f"Waiting for challenge {data.userchallenge_name} to be ready...")
            
            for event in w.stream(
                self.custom_api.list_namespaced_custom_object,
                group="apps.hexactf.io",
                version="v2alpha1",
                namespace=NAMESPACE,
                plural="challenges",
                field_selector=field_selector,
                timeout_seconds=min(WATCH_TIMEOUT, timeout)
            ):
                # 타임아웃 체크
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    w.stop()
                    raise UserChallengeCreationException(
                        f"Timeout waiting for challenge {data.userchallenge_name} (elapsed: {elapsed:.1f}s)"
                    )
                
                obj = event['object']
                event_type = event['type']
                
                logger.debug(f"Received event: {event_type} for {data.userchallenge_name}")
                
                # 삭제 이벤트인 경우
                if event_type == 'DELETED':
                    w.stop()
                    raise UserChallengeCreationException(
                        f"Challenge {data.userchallenge_name} was deleted unexpectedly"
                    )
                
                # 상태 확인
                status = obj.get('status', {})
                current_status = status.get('currentStatus', {})
                
                if current_status.get('status') == 'Running':
                    endpoint = status.get('endpoint')
                    if endpoint and isinstance(endpoint, int) and endpoint > 0:
                        w.stop()
                        logger.info(f"Challenge {data.userchallenge_name} is ready with endpoint {endpoint}")
                        return endpoint
                    else:
                        logger.warning(f"Challenge running but invalid endpoint: {endpoint}")
                
                elif current_status.get('status') == 'Failed':
                    w.stop()
                    error_msg = current_status.get('message', 'Unknown error')
                    raise UserChallengeCreationException(
                        f"Challenge {data.userchallenge_name} failed: {error_msg}"
                    )
                
                # 진행 상황 로깅
                if elapsed > 0 and int(elapsed) % 30 == 0:  # 30초마다
                    logger.info(f"Still waiting for {data.userchallenge_name}... ({elapsed:.1f}s elapsed)")
            
            # watch가 종료되었지만 결과를 받지 못한 경우
            raise UserChallengeCreationException(
                f"Challenge {data.userchallenge_name} did not become ready within {timeout}s"
            )
            
        except UserChallengeCreationException:
            raise
        except Exception as e:
            logger.error(f"Error waiting for challenge ready: {str(e)}")
            raise UserChallengeCreationException(f"Error waiting for challenge: {str(e)}")
        finally:
            try:
                w.stop()
            except Exception:
                pass
    
    def delete(self, challenge_info: ChallengeRequest, namespace: str = NAMESPACE) -> bool:
        """
        Challenge Custom Resource를 삭제합니다.
        
        Args:
            challenge_info: Challenge 삭제 요청 데이터
            namespace: Challenge가 생성된 네임스페이스
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            UserChallengeDeletionException: Challenge 삭제에 실패했을 때
        """
        try:
            resource_name = challenge_info.name
            logger.info(f"Deleting challenge resource: {resource_name}")
            
            # 리소스 존재 여부 확인
            if not self._resource_exists(resource_name, namespace):
                logger.warning(f"Challenge resource {resource_name} not found")
                return True  # 이미 없으면 성공으로 간주
            
            # 리소스 삭제
            self._delete_resource(resource_name, namespace)
            
            # 삭제 완료 대기
            self._wait_for_deletion(resource_name, namespace)
            
            logger.info(f"Successfully deleted challenge resource: {resource_name}")
            return True
            
        except UserChallengeDeletionException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting challenge: {str(e)}")
            raise UserChallengeDeletionException(f"Failed to delete challenge: {str(e)}")
    
    def _resource_exists(self, resource_name: str, namespace: str = NAMESPACE) -> bool:
        """리소스가 존재하는지 확인합니다."""
        try:
            self.custom_api.get_namespaced_custom_object(
                group="apps.hexactf.io",
                version="v2alpha1",
                namespace=namespace,
                plural="challenges",
                name=resource_name
            )
            return True
        except ApiException as e:
            if e.status == 404:
                return False
            else:
                logger.error(f"Error checking resource existence: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error checking resource existence: {str(e)}")
            return False
    
    def _delete_resource(self, resource_name: str, namespace: str = NAMESPACE):
        """리소스를 삭제합니다."""
        try:
            self.custom_api.delete_namespaced_custom_object(
                group="apps.hexactf.io",
                version="v2alpha1",
                namespace=namespace,
                plural="challenges",
                name=resource_name,
                body=client.V1DeleteOptions(
                    propagation_policy="Foreground",
                    grace_period_seconds=30
                )
            )
            logger.info(f"Initiated deletion of resource: {resource_name}")
            
        except ApiException as e:
            if e.status == 404:
                logger.info(f"Resource {resource_name} already deleted")
            else:
                logger.error(f"K8s API error deleting resource: {e.status} - {e.reason}")
                raise UserChallengeDeletionException(f"K8s API error: {e.reason}")
        except Exception as e:
            logger.error(f"Unexpected error deleting resource: {str(e)}")
            raise UserChallengeDeletionException(f"Failed to delete resource: {str(e)}")
    
    def _wait_for_deletion(self, resource_name: str, namespace: str = NAMESPACE, timeout: int = 60):
        """리소스 삭제 완료를 대기합니다."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if not self._resource_exists(resource_name, namespace):
                logger.info(f"Resource {resource_name} successfully deleted")
                return
            
            time.sleep(2)  # 2초마다 확인
        
        logger.warning(f"Resource {resource_name} deletion timeout after {timeout}s")
    
    def get_challenge_status(self, resource_name: str, namespace: str = NAMESPACE) -> Optional[Dict[str, Any]]:
        """
        Challenge 리소스의 현재 상태를 조회합니다.
        
        Args:
            resource_name: 리소스 이름
            namespace: 네임스페이스
            
        Returns:
            상태 정보 딕셔너리 또는 None
        """
        try:
            resource = self.custom_api.get_namespaced_custom_object(
                group="apps.hexactf.io",
                version="v2alpha1",
                namespace=namespace,
                plural="challenges",
                name=resource_name
            )
            
            status = resource.get('status', {})
            current_status = status.get('currentStatus', {})
            
            return {
                'status': current_status.get('status', 'Unknown'),
                'endpoint': status.get('endpoint'),
                'message': current_status.get('message', ''),
                'last_updated': current_status.get('lastTransitionTime')
            }
            
        except ApiException as e:
            if e.status == 404:
                logger.debug(f"Challenge resource {resource_name} not found")
                return None
            else:
                logger.error(f"Error getting challenge status: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"Unexpected error getting challenge status: {str(e)}")
            return None
    
    def list_challenges(self, namespace: str = NAMESPACE) -> List[Dict[str, Any]]:
        """
        네임스페이스의 모든 Challenge 리소스를 조회합니다.
        
        Args:
            namespace: 네임스페이스
            
        Returns:
            Challenge 정보 리스트
        """
        try:
            resources = self.custom_api.list_namespaced_custom_object(
                group="apps.hexactf.io",
                version="v2alpha1",
                namespace=namespace,
                plural="challenges"
            )
            
            challenges = []
            for item in resources.get('items', []):
                metadata = item.get('metadata', {})
                status = item.get('status', {})
                
                challenges.append({
                    'name': metadata.get('name'),
                    'challenge_id': metadata.get('labels', {}).get('apps.hexactf.io/challengeId'),
                    'user_id': metadata.get('labels', {}).get('apps.hexactf.io/userId'),
                    'status': status.get('currentStatus', {}).get('status', 'Unknown'),
                    'endpoint': status.get('endpoint'),
                    'created_at': metadata.get('creationTimestamp')
                })
            
            logger.debug(f"Found {len(challenges)} challenges in namespace {namespace}")
            return challenges
            
        except Exception as e:
            logger.error(f"Error listing challenges: {str(e)}")
            return []
    
    def cleanup_failed_challenges(self, namespace: str = NAMESPACE, max_age_hours: int = 24) -> int:
        """
        실패한 또는 오래된 Challenge 리소스를 정리합니다.
        
        Args:
            namespace: 네임스페이스
            max_age_hours: 최대 보관 시간 (시간)
            
        Returns:
            정리된 리소스 수
        """
        try:
            challenges = self.list_challenges(namespace)
            cleaned_count = 0
            current_time = time.time()
            
            for challenge in challenges:
                should_cleanup = False
                
                # 실패한 챌린지
                if challenge['status'] in ['Failed', 'Error']:
                    should_cleanup = True
                    logger.info(f"Cleaning up failed challenge: {challenge['name']}")
                
                # 오래된 챌린지 (created_at이 있는 경우만)
                elif challenge.get('created_at'):
                    # K8s timestamp 파싱 로직 필요
                    # 여기서는 간단히 처리
                    should_cleanup = False  # 실제 구현에서는 시간 비교 로직 추가
                
                if should_cleanup:
                    try:
                        self._delete_resource(challenge['name'], namespace)
                        cleaned_count += 1
                    except Exception as e:
                        logger.error(f"Failed to cleanup challenge {challenge['name']}: {str(e)}")
            
            logger.info(f"Cleaned up {cleaned_count} challenges")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return 0