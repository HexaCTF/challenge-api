
from dataclasses import dataclass


class UserChallengeInputData:
    def __init__(self, user_id: str, challenge_id: str, input_data: str):
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.input_data = input_data

    
    def __repr__(self):
        return f"UserChallengeInputData(user_id={self.user_id}, challenge_id={self.challenge_id}, input_data={self.input_data})"


class UserChallengeStatusData:
    def __init__(self, user_id: str, challenge_id: str, status: str, port: int):
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.port = port 
        self.status = status
    
    def __repr__(self):
        return f"UserChallengeStatusData(user_id={self.user_id}, challenge_id={self.challenge_id}, status={self.status})"