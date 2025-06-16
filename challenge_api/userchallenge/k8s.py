from kubernetes import client, config, watch
from challenge_api.userchallenge.userchallenge import UserChallengeService
from challenge_api.userchallenge.status import UserChallengeStatusService
from challenge_api.objects.challenge import ChallengeRequest
from challenge_api.exceptions.service import UserChallengeCreationException
from challenge_api.userchallenge.challenge import ChallengeService


NAMESPACE = "challenge"

class K8sManager:
    
    def __init__(
        self, 
        challenge_service: ChallengeService,
        userchallenge_service: UserChallengeService, 
        status_service: UserChallengeStatusService
        ):
        # K8S Client configurations
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
            
        self.custom_api = client.CustomObjectsApi()
        self.core_api = client.CoreV1Api()
        
        # service 
        self.challenge_service = challenge_service
        self.userchallenge_service = userchallenge_service
        self.status_service = status_service
    
    
    def create(self, request: ChallengeRequest):
        
        # 1. Create New UserChallenge if it doesn't exist
        userchallenge = self.userchallenge_service.get_by_name(request.name)
        if not userchallenge:
            userchallenge = self.userchallenge_service.create(request)
            self.status_service.create(id_=userchallenge.idx)
        else:
            recent = self.status_service.get_first(userchallenge.idx)
            if recent and recent.status == 'Running':
                return recent.port
        
        # Get definition name
        definition= self.challenge_service.get_name(request.challenge_id)
        
        # Create Kubernetes Challenge Objects 
        
        challenge_manifest = {
            "apiVersion": "apps.hexactf.io/v2alpha1",
            "kind": "Challenge",
            "metadata": {
                "name": request.name,
                "labels": {
                    "apps.hexactf.io/challengeId": str(request.challenge_id),
                    "apps.hexactf.io/userId": str(request.user_id)
                }
            },
            "spec": {
                "namespace": NAMESPACE,
                "definition": definition
            }
        }
            
        _ = self.custom_api.create_namespaced_custom_object(
            group="apps.hexactf.io",
            version="v2alpha1",
            namespace=NAMESPACE,
            plural="challenges",
            body=challenge_manifest
        )
        
        
        status = None
        endpoint = 0
        field_selector = f"apps.hexactf.io/challengeId={request.challenge_id},apps.hexactf.io/userId={request.user_id}"
        w = watch.Watch()
        for event in w.stream(self.custom_api.list_namespaced_custom_object,
                              group="apps.hexactf.io",
                              version="v2alpha1",
                              namespace=NAMESPACE,
                              label_selector=field_selector,
                              plural="challenges",
                              ):
            obj = event['object']
            
            if obj.get('status', {}).get('currentStatus', {}).get('status',"") == 'Running':
                status = event['object']['status']
                endpoint = status.get('endpoint')
                w.stop()
                break
        
        if not endpoint:
            raise UserChallengeCreationException(message=f"Failed to get NodePort for Challenge: {request.name}")
        
        recent = self.status_service.get_first(userchallenge.idx)
        if recent and recent.status == 'Pending':
            recent.status = 'Running'
            recent.port = endpoint
            self.status_service.update(recent)
        
        return endpoint

    # def delete(self, challenge_info: ChallengeInfo, namespace="challenge"):
    #     """
    #     Challenge Custom Resource를 삭제합니다.
        
    #     Args:
    #         challenge_info (ChallengeInfo): Challenge 삭제 요청 데이터
    #         namespace (str): Challenge가 생성된 네임스페이스 (기본값: "default")
            
    #     Raises:
    #         UserChallengeDeletionError: Challenge 삭제에 실패했을 때
    #     """
        
    #     # UserChallenge 조회
    #     namebuilder = NameBuilder(challenge_id=challenge_info.challenge_id, user_id=challenge_info.user_id)
    #     challenge_info = namebuilder.build()
    #     user_challenge_repo = UserChallengesRepository()
    #     user_challenge = user_challenge_repo.get_by_user_challenge_name(challenge_info.name)
    #     if not user_challenge:
    #         raise UserChallengeDeletionError(error_msg=f"Deletion : UserChallenge not found: {challenge_info.name}")
        
    #     # 사용자 챌린지(컨테이너) 삭제 
    #     try:
    #         self.custom_api.delete_namespaced_custom_object(
    #             group="apps.hexactf.io",
    #             version="v2alpha1",
    #             namespace=namespace,
    #             plural="challenges",
    #             name=challenge_info.name
    #         )
            
    #     except Exception as e:
    #         raise UserChallengeDeletionError(error_msg=str(e)) from e
 
