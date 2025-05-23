from typing import Optional

from challenge_api.db.models import UserChallenges
from challenge_api.objects.challenge import ChallengeRequest
from challenge_api.db.repository.base import BaseRepository
from challenge_api.db.repository.challenge import ChallengeRepository
from challenge_api.exceptions.service import InvalidInputValue

class UserChallengesRepository(BaseRepository):
    def __init__(self, session=None):
        super().__init__(session)
        self.challenge_repo = ChallengeRepository(session=self.session)
        
    
    def create(self, object_) -> Optional[UserChallenges]:
        userchallenge = None
        if isinstance(object_, ChallengeRequest):
            userchallenge = UserChallenges(
                C_idx=object_.challenge_id,
                user_idx=object_.user_id,
                userChallengeName=object_.name
            )
        else:
            raise InvalidInputValue(
                message = "Invalid input error when creating userchallenge"
            )
        self.session.add(userchallenge)
        self.session.commit()
        return userchallenge
        
    
    def get_by_id(self, id_) -> Optional[UserChallenges]:
        return self.session.query(UserChallenges).filter_by(id_=id_).first()
        
    def update(self, object_):
        raise NotImplementedError("Subclasses must implement this method")

    def delete(self, object_):
        raise NotImplementedError("Subclasses must implement this method")
    
    
    
    # def create(self, challenge_info: ChallengeInfo) -> Optional[UserChallenges]:
    #     """새로운 사용자 챌린지 생성
        
    #     Args:
    #         challenge_name (ChallengeName): 챌린지 이름 객체
            
    #     Returns:
    #         Optional[UserChallenges]: 생성된 챌린지, 실패시 None
            
    #     Raises:
    #         InternalServerError: DB 작업 실패시
    #     """
    #     try:
    #         challenge = UserChallenges(
    #             C_idx=challenge_info.challenge_id,
    #             user_idx=challenge_info.user_id,
    #             userChallengeName=challenge_info.name,
    #         )
    #         self.session.add(challenge)
    #         self.session.commit()
    #         return challenge
            
    #     except SQLAlchemyError as e:
    #         self.session.rollback()
    #         raise InternalServerError(error_msg=f"Error creating challenge in db: {e}") from e

    # def get_by_user_challenge_name(self, userChallengeName: str) -> Optional[UserChallenges]:
    #     """
    #     사용자 챌린지 이름 조회
        
    #     Args:
    #         userChallengeName (str): 사용자 챌린지 이름
        
    #     Returns:
    #         UserChallenges: 사용자 챌린지
    #     """
    #     user_challenge = UserChallenges.query.filter_by(userChallengeName=userChallengeName).first()
    #     if not user_challenge:
    #         return None
    #     return user_challenge
        
    # def is_running(self, challenge: UserChallenges) -> bool:
    #     """
    #     챌린지 실행 여부 확인
        
    #     Args:
    #         challenge (UserChallenges): 사용자 챌린지
        
    #     Returns:
    #         bool: 챌린지 실행 여부
    #     """
    #     return challenge.status == 'Running'
    
    # def is_exist(self, challenge_info: ChallengeInfo) -> bool:
    #     """챌린지 이름 존재 여부 확인
        
    #     Args:
    #         challenge_info (ChallengeInfo): 챌린지 이름 객체

    #     Returns:
    #         bool: 존재 여부
    #     """
    #     return (
    #         UserChallenges.query
    #         .filter_by(userChallengeName=challenge_info.name)
    #         .first() is not None
    #     )
    