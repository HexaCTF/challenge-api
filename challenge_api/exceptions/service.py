
class BaseServiceException(Exception):
    def __init__(self, message:str):
        super().__init__(message)
        self.message = message or "An unexpected error occurred"

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


"""
Etc.. 
"""
class InvalidInputValue(BaseServiceException):
    """Invalid Input Value"""
    def __init__(self, message:str):
        super().__init__(message)
        

"""
Challenge 
"""
class ChallengeException(BaseServiceException):
    """Challenge 관련 기본 예외"""
    def __init__(self, message:str):
        super().__init__(message)

class ChallengeNotFound(ChallengeException):
    """Challenge를 찾을 수 없을 때의 예외"""
    def __init__(self, message:str):
        super().__init__(message)
