from datetime import datetime, timedelta
from app.extensions_manager import db
from sqlalchemy import func, Enum, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

def current_time_kst():
    return datetime.utcnow() + timedelta(hours=9)

# Users Table Model
class Users(db.Model):
    __tablename__ = 'Users'

    email = db.Column(db.String(255), primary_key=True, nullable=False, unique=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    homepage = db.Column(db.String(255), default='', nullable=False)
    country = db.Column(db.String(255), default='', nullable=False)
    lang = db.Column(db.String(255), default='EN', nullable=False)
    organization = db.Column(db.String(255), default='', nullable=False)
    verified = db.Column(db.Boolean, default=False, nullable=False)
    hidden = db.Column(db.Boolean, default=False, nullable=False)
    banned = db.Column(db.Boolean, default=False, nullable=False)
    permission = db.Column(db.Boolean, default=False, nullable=False)
    teamName = db.Column(db.String(20), default='', nullable=False)
    currentStatus = db.Column(db.Boolean, default=True, nullable=False)
    createdAt = db.Column(db.DateTime, default=current_time_kst, nullable=False)  # 함수 참조
    token = db.Column(db.String(255), nullable=False)
    tokenTime = db.Column(db.DateTime, default=current_time_kst, nullable=False)  # 함수 참조
    passwordTime = db.Column(db.DateTime, default=current_time_kst, nullable=False)  # 함수 참조

# Teams Table Model
class Teams(db.Model):
    __tablename__ = 'Teams'

    teamName = db.Column(db.String(20), primary_key=True, nullable=False)
    username = db.Column(db.String(20), ForeignKey('Users.username'), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    homepage = db.Column(db.String(255), default='', nullable=False)
    organization = db.Column(db.String(255), default='', nullable=False)
    country = db.Column(db.String(255), default='', nullable=False)
    hidden = db.Column(db.Boolean, default=False, nullable=False)
    banned = db.Column(db.Boolean, default=False, nullable=False)
    createdCode = db.Column(db.String(20), nullable=False, unique=True)
    currentStatus = db.Column(db.Boolean, default=True, nullable=False)
    createdAt = db.Column(db.DateTime, default=current_time_kst, nullable=False)  # 함수 참조

# Notifications Table Model
class Notifications(db.Model):
    __tablename__ = 'Notifications'

    idx = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), ForeignKey('Users.username'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    contents = db.Column(db.String(1000), nullable=False)
    currentStatus = db.Column(db.Boolean, default=True, nullable=False)
    createdAt = db.Column(db.DateTime, default=current_time_kst, nullable=False)  # 함수 참조
    playSound = db.Column(db.Boolean, default=True, nullable=False)  # playSound 컬럼 추가

# Challenges Table Model
class Challenges(db.Model):
    __tablename__ = 'Challenges'

    idx = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), ForeignKey('Users.username'), nullable=False)
    challengeType = db.Column(db.String(20), nullable=False)
    author = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(1000), nullable=False)
    initialValue = db.Column(db.Integer, nullable=False)
    decayFunction = db.Column(db.String(20), default='', nullable=False)
    decay = db.Column(db.Integer, default=0, nullable=False)
    minimumValue = db.Column(db.Integer, default=0, nullable=False)
    flag = db.Column(db.String(255), nullable=False)
    userFile = db.Column(db.String(255), default='', nullable=False)
    hidden = db.Column(db.Boolean, default=False, nullable=False)
    score = db.Column(db.Integer, default=0, nullable=False)
    solvedCount = db.Column(db.Integer, default=0, nullable=False)
    currentStatus = db.Column(db.Boolean, default=True, nullable=False)
    createdAt = db.Column(db.DateTime, default=current_time_kst, nullable=False)  # 함수 참조
    unlockScore = db.Column(db.Integer, default=0, nullable=False)
    unlockTime = db.Column(db.DateTime, default=0, nullable=False)
    unlockChallenges = db.Column(db.String(255), default='', nullable=False)
    isPersistence = db.Column(db.Boolean, default=False, nullable=False)


class UserChallenges(db.Model):
    """사용자 챌린지 모델"""
    __tablename__ = 'UserChallenges'

    idx = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), ForeignKey('Users.username'), nullable=False)
    C_idx = db.Column(db.Integer, ForeignKey('Challenges.idx'), nullable=False)
    userChallengeName = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='None', nullable=False)
    createdAt = db.Column(db.DateTime, default=current_time_kst, nullable=False)

    # 관계 설정
    user = relationship('Users', backref='challenges')
    challenge = relationship('Challenges', backref='user_challenges')

    __table_args__ = (
        CheckConstraint('port >= 15000 AND port <= 30000', name='checkPort'),
    )

    def __init__(self, username: str, C_idx: int, userChallengeName: str, port: int, status: str = 'None'):
        self.username = username
        self.C_idx = C_idx
        self.userChallengeName = userChallengeName
        self.port = port
        self.status = status

    def to_dict(self) -> dict:
        """모델을 딕셔너리로 변환"""
        return {
            'idx': self.idx,
            'username': self.username,
            'C_idx': self.C_idx,
            'userChallengeName': self.userChallengeName,
            'port': self.port,
            'status': self.status,
            'createdAt': self.createdAt.isoformat()
        }


    
