from typing import Optional
class BaseException(Exception):
    def __init__(self, message:str):
        super().__init__(message)
        self.message = message or "An unexpected error occurred"
    
    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


"""
Repository
"""
class RepositoryException(BaseException):
    """Repository 관련 예외"""
    def __init__(self, message:str):
        super().__init__(message)

class ChallengeRepositoryException(RepositoryException):
    """Challenge Repository 관련 예외"""
    def __init__(self, message:str):
        super().__init__(message)

class UserChallengeRepositoryException(RepositoryException):
    """UserChallenge Repository 관련 예외"""
    def __init__(self, message:str):
        super().__init__(message)

class StatusRepositoryException(RepositoryException):
    """Status Repository 관련 예외"""
    def __init__(self, message:str):
        super().__init__(message)

"""
Etc.. 
"""
class InvalidInputValue(BaseException):
    """Invalid Input Value"""
    def __init__(self, message:str):
        super().__init__(message)
        

"""
Challenge 
"""
class ChallengeException(BaseException):
    """Challenge 관련 기본 예외"""
    def __init__(self, message:str):
        super().__init__(message)

class ChallengeNotFound(ChallengeException):
    """Challenge를 찾을 수 없을 때의 예외"""
    def __init__(self, message:str):
        super().__init__(message)

"""
UserChallenge
"""
class UserChallengeException(BaseException):
    """UserChallenge 관련 기본 예외"""
    def __init__(self, message:str):
        super().__init__(message)
        
class UserChallengeNotFound(UserChallengeException):
    """UserChallenge를 찾을 수 없을 때의 예외"""
    def __init__(self, message:str):
        super().__init__(message)

class UserChallengeCreationException(UserChallengeException):
    """UserChallenge 생성 중 예외"""
    def __init__(self, message:str):
        super().__init__(message)

class UserChallengeDeletionException(UserChallengeException):
    """UserChallenge 삭제 중 예외"""
    def __init__(self, message:str):
        super().__init__(message)

# Status
class ChallengeStatusException(BaseException):
    def __init__(self, message:str):
        super().__init__(message)
        
class ChallengeStatusNotFound(ChallengeStatusException):
    def __init__(self, message:str):
        super().__init__(message)


class K8sResourceException(BaseException):
    def __init__(self, message:str):
        super().__init__(message)

class K8sResourceNotFound(K8sResourceException):
    def __init__(self, message:str):
        super().__init__(message)
