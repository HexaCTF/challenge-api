from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import ForeignKey, String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from challenge_api.app.external.database.database import Base

def current_time_kst():
    return datetime.utcnow() + timedelta(hours=9)

# Users Table Model
class Users(Base):
    __tablename__ = 'Users'
    
    idx: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    homepage: Mapped[str] = mapped_column(String(255), default='', nullable=False)
    country: Mapped[str] = mapped_column(String(255), default='', nullable=False)
    lang: Mapped[str] = mapped_column(String(255), default='EN', nullable=False)
    organization: Mapped[str] = mapped_column(String(255), default='', nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    permission: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    teamName: Mapped[str] = mapped_column(String(20), default='', nullable=False)
    currentStatus: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=current_time_kst, nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False)
    tokenTime: Mapped[datetime] = mapped_column(DateTime, default=current_time_kst, nullable=False)
    passwordTime: Mapped[datetime] = mapped_column(DateTime, default=current_time_kst, nullable=False)

# Teams Table Model
class Teams(Base):
    __tablename__ = 'Teams'

    teamName: Mapped[str] = mapped_column(String(20), primary_key=True, nullable=False)
    username: Mapped[str] = mapped_column(String(20), ForeignKey('Users.username'), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    homepage: Mapped[str] = mapped_column(String(255), default='', nullable=False)
    organization: Mapped[str] = mapped_column(String(255), default='', nullable=False)
    country: Mapped[str] = mapped_column(String(255), default='', nullable=False)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    createdCode: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    currentStatus: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=current_time_kst, nullable=False)

# Notifications Table Model
class Notifications(Base):
    __tablename__ = 'Notifications'

    idx: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(20), ForeignKey('Users.username'), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    contents: Mapped[str] = mapped_column(String(1000), nullable=False)
    currentStatus: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=current_time_kst, nullable=False)
    playSound: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

# Challenges Table Model
class Challenges(Base):
    __tablename__ = 'Challenges'

    idx: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(20), ForeignKey('Users.username'), nullable=False)
    challengeType: Mapped[str] = mapped_column(String(20), nullable=False)
    author: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    initialValue: Mapped[int] = mapped_column(Integer, nullable=False)
    decayFunction: Mapped[str] = mapped_column(String(20), default='', nullable=False)
    decay: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    minimumValue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    flag: Mapped[str] = mapped_column(String(255), nullable=False)
    userFile: Mapped[str] = mapped_column(String(255), default='', nullable=False)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    solvedCount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currentStatus: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=current_time_kst, nullable=False)
    unlockScore: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unlockTime: Mapped[datetime] = mapped_column(DateTime, default=0, nullable=False)
    unlockChallenges: Mapped[str] = mapped_column(String(255), default='', nullable=False)
    isPersistence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

# UserChallenges Table Model
class UserChallenges(Base):
    __tablename__ = 'UserChallenges'

    idx: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_idx: Mapped[int] = mapped_column(Integer, ForeignKey('Users.idx'), default=0, nullable=False)
    C_idx: Mapped[int] = mapped_column(Integer, ForeignKey('Challenges.idx'), nullable=False)
    userChallengeName: Mapped[str] = mapped_column(String(255), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=current_time_kst, nullable=False)

# UserChallengeStatus Table Model
class UserChallengeStatus(Base):
    __tablename__ = 'UserChallengeStatus'

    idx: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='None')
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=current_time_kst, nullable=False)
    user_challenge_idx: Mapped[int] = mapped_column(Integer, ForeignKey('UserChallenges.idx'), nullable=False)

# Submissions Table Model
class Submissions(Base):
    __tablename__ = 'Submissions'

    idx: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    C_idx: Mapped[int] = mapped_column(Integer, ForeignKey('Challenges.idx'), nullable=False)
    username: Mapped[str] = mapped_column(String(20), ForeignKey('Users.username'), nullable=False)
    teamName: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[bool] = mapped_column(Boolean, nullable=False)
    provided: Mapped[str] = mapped_column(String(255), nullable=False)
    currentStatus: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=current_time_kst, nullable=False)
