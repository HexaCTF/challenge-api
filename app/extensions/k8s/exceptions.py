class KubernetesError(Exception):
    """기본적인 예외"""
    pass 


class ChallengeRequestError(KubernetesError):
    """ChallengeDefinition 쿠버네티스 리소스 요청과 관련된 모든 예외 처리"""
    pass 
        
class UserChallengeRequestError(KubernetesError):
    """Challenge 쿠버네티스 리소스 요청과 관련된 모든 예외 처리"""
    pass
  
class ChallengeConflictError(KubernetesError):
    """리소스 충돌 예외"""
    pass     
