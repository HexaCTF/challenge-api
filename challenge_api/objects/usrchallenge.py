
class UChallengeStatus():
    def __init__(self, userchallenge_idx: int, status: str, port: int):
        self.userchallenge_idx = userchallenge_idx
        self.status = status
        self.port = port
    
    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, value):
        if value is "":
            self._status = "None"
        self._status = value
    
    @property
    def port(self):
        return self._port
    
    @port.setter
    def port(self, value):
        if 0 <= value <= 65535:
            self._port = 0
        self._port = value
    
