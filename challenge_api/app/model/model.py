from datetime import datetime, timedelta
from sqlalchemy import ForeignKey
from challenge_api.app.external.database import Base

def current_time_kst():
    return datetime.utcnow() + timedelta(hours=9)

# Users Table Model
class Users(Base):
    __tablename__ = 'Users'
    
    idx = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
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
class Teams(Base):
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
class Notifications(Base):
    __tablename__ = 'Notifications'

    idx = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), ForeignKey('Users.username'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    contents = db.Column(db.String(1000), nullable=False)
    currentStatus = db.Column(db.Boolean, default=True, nullable=False)
    createdAt = db.Column(db.DateTime, default=current_time_kst, nullable=False)  # 함수 참조
    playSound = db.Column(db.Boolean, default=True, nullable=False)  # playSound 컬럼 추가

# Challenges Table Model
class Challenges(Base):
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

# UserChallenges Table Model
class UserChallenges(Base):
    __tablename__ = 'UserChallenges'

    idx = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_idx = db.Column(db.Integer, ForeignKey('Users.idx'), default=0, nullable=False)
    C_idx = db.Column(db.Integer, db.ForeignKey('Challenges.idx'), nullable=False)
    userChallengeName = db.Column(db.String(255), nullable=False)
    createdAt = db.Column(db.DateTime, default=current_time_kst, nullable=False)


# UserChallengeStatus Table Model
class UserChallengeStatus(Base):
    __tablename__ = 'UserChallengeStatus'

    idx = db.Column(db.Integer, primary_key=True, autoincrement=True)
    port = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='None')
    createdAt = db.Column(db.DateTime, default=current_time_kst, nullable=False)
    user_challenge_idx = db.Column(db.Integer, db.ForeignKey('UserChallenges.idx'), nullable=False)

# Submissions Table Model
class Submissions(Base):
    __tablename__ = 'Submissions'

    idx = db.Column(db.Integer, primary_key=True, autoincrement=True)
    C_idx = db.Column(db.Integer, ForeignKey('Challenges.idx'), nullable=False)
    username = db.Column(db.String(20), ForeignKey('Users.username'), nullable=False)
    teamName = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    type = db.Column(db.Boolean, nullable=False)
    provided = db.Column(db.String(255), nullable=False)
    currentStatus = db.Column(db.Boolean, default=True, nullable=False)
    createdAt = db.Column(db.DateTime, default=current_time_kst, nullable=False)
