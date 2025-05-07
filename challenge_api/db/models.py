from datetime import datetime, timedelta
from enum import Enum
from challenge_api.extensions_manager import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

def current_time_kst():
    return datetime.utcnow() + timedelta(hours=9)

def get_user_score(username):
    # Subquery: 맞은 문제의 점수를 가져옴
    total_score = db.session.query(
        func.sum(Challenges.score)  # Challenges 테이블에서 점수 합산
    ).join(
        Submissions, Challenges.idx == Submissions.C_idx  # Submissions와 Challenges 연결
    ).join(
        Users, Submissions.username == Users.username
    ).filter(
        Users.hidden == False,
        Submissions.username == username,  # 특정 유저의 제출만 필터링
        Submissions.type == True,  # 맞은 문제만 포함
        Submissions.currentStatus == True
    ).scalar()  # 단일 값 반환
    return total_score or 0  # 점수가 None이면 0 반환

def get_team_score(team_name):
    # Subquery: 특정 팀의 점수를 합산
    total_score = db.session.query(
        func.sum(Challenges.score)  # Challenges 테이블에서 점수 합산
    ).join(
        Submissions, Challenges.idx == Submissions.C_idx  # Submissions와 Challenges 연결
    ).join(
        Users, Submissions.username == Users.username  # Submissions와 Users 연결
    ).join(
        Teams, Users.teamName == Teams.teamName
    ).filter(
        Users.teamName == team_name,  # 특정 팀의 팀원만 필터링
        Teams.hidden == False,
        Users.hidden == False,
        Submissions.type == True,  # 맞은 문제만 포함
        Submissions.currentStatus == True
    ).scalar()  # 단일 값 반
    return total_score or 0  # 점수가 None이면 0 반환

def get_all_user_scores_desc():
    user_scores = db.session.query(
        Submissions.username,  # 사용자 이름
        func.sum(Challenges.score).label('total_score')  # 각 사용자의 총 점수
    ).join(
        Challenges, Challenges.idx == Submissions.C_idx  # Submissions와 Challenges 연결
    ).join(
        Users, Submissions.username == Users.username  # Submissions와 Users 연결
    ).filter(
        Submissions.currentStatus == True,
        Submissions.type == True,  # 맞은 문제만 포함
        Users.verified == True,
        Users.hidden == False,  # Users.hidden이 False인지 확인
        Users.banned == False  # Users.banned가 False인지 확인
    ).group_by(
        Submissions.username  # 사용자 이름으로 그룹화
    ).order_by(
        func.sum(Challenges.score).desc()  # 총 점수 기준으로 내림차순 정렬
    ).all()  # 모든 결과 반환

    # 결과를 리스트로 반환
    return [{'username': username, 'total_score': total_score or 0} for username, total_score in user_scores]


def get_all_team_scores_desc():
    team_scores = db.session.query(
        Users.teamName,  # 팀 이름
        func.sum(Challenges.score).label('total_score')  # 각 팀의 총 점수
    ).join(
        Submissions, Challenges.idx == Submissions.C_idx  # Submissions와 Challenges 연결
    ).join(
        Users, Submissions.username == Users.username  # Submissions와 Users 연결
    ).join(
        Teams, Users.teamName == Teams.teamName  # Users와 Teams 연결
    ).filter(
        Submissions.currentStatus == True,
        Submissions.type == True,  # 맞은 문제만 포함
        Teams.hidden == False,  # Teams.hidden이 False인지 확인
        Teams.banned == False  # Teams.banned가 False인지 확인
    ).group_by(
        Users.teamName  # 팀 이름으로 그룹화
    ).order_by(
        func.sum(Challenges.score).desc()  # 총 점수 기준으로 내림차순 정렬
    ).all()  # 모든 결과 반환

    # 결과를 리스트로 반환
    return [{'teamName': teamName, 'total_score': total_score or 0} for teamName, total_score in team_scores]

def get_team_submission_scores(team_name):
    submissions = db.session.query(
        func.group_concat(Challenges.title),  # 풀린 문제 제목 (쉼표로 구분)
        Submissions.username,
        func.sum(Challenges.score),  # 점수
        Submissions.createdAt  # 제출 시간
    ).join(
        Challenges, Challenges.idx == Submissions.C_idx
    ).join(
        Users, Submissions.username == Users.username
    ).filter(
        Users.teamName == team_name,  # 특정 팀만 필터링
        Submissions.currentStatus == True,
        Submissions.type == True  # 맞춘 플래그만 포함
    ).group_by(
        Submissions.createdAt  # 제출 시간 기준 그룹화
    ).order_by(
        Submissions.createdAt.asc()  # 제출 시간 기준 오름차순 정렬
    ).all()

    scores = []
    cumulative_score = 0
    for challenge_titles, username, score, submission_time in submissions:
        cumulative_score += score
        scores.append({
            "challenge": challenge_titles.split(",") if challenge_titles else [],  # 쉼표로 분리된 문제 이름 목록
            "username": username,
            "score": score,
            "cumulative_score": cumulative_score,
            "time": submission_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    return scores


def get_user_submission_scores(username):
    submissions = db.session.query(
        Submissions.createdAt,  # 제출 시간
        func.sum(Challenges.score),  # 점수
        func.group_concat(Challenges.title)  # 풀린 문제 제목 (쉼표로 구분)
    ).join(
        Challenges, Challenges.idx == Submissions.C_idx
    ).filter(
        Submissions.username == username,  # 특정 사용자만 필터링
        Submissions.type == True,  # 맞춘 플래그만 포함
        Submissions.currentStatus == True
    ).group_by(
        Submissions.createdAt  # 제출 시간 기준 그룹화
    ).order_by(
        Submissions.createdAt.asc()  # 제출 시간 기준 오름차순 정렬
    ).all()

    scores = []
    cumulative_score = 0
    for submission_time, score, challenge_titles in submissions:
        cumulative_score += score
        scores.append({
            "challenge": challenge_titles.split(",") if challenge_titles else [],  # 쉼표로 분리된 문제 이름 목록
            "score": score,
            "cumulative_score": cumulative_score,
            "time": submission_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    return scores

def get_team_ranking(team_name):
    # 모든 팀의 점수를 가져옴
    team_scores = db.session.query(
        Teams.teamName,
        func.sum(Challenges.score).label('total_score')
    ).join(
        Submissions, Teams.teamName == Submissions.teamName
    ).join(
        Challenges, Challenges.idx == Submissions.C_idx
    ).filter(
        Teams.hidden == False,  # 숨겨진 팀 제외
        Teams.banned == False,  # 차단된 팀 제외
        Submissions.currentStatus == True,
        Submissions.type == True  # 맞춘 문제만 포함
    ).group_by(
        Teams.teamName
    ).order_by(
        func.sum(Challenges.score).desc()  # 점수 내림차순 정렬
    ).all()

    # 점수 데이터를 리스트로 변환
    ranked_teams = [{'teamName': t.teamName, 'total_score': t.total_score or 0} for t in team_scores]

    # 팀 순위 계산
    for rank, team in enumerate(ranked_teams, start=1):  # 1부터 시작
        if team['teamName'] == team_name:
            return rank

    return None  # 팀이 랭킹에 없는 경우

def get_team_correct_challenges(team_name):
    correct_challenges = db.session.query(
        Submissions
    ).join(
        Users, Submissions.username == Users.username
    ).filter(
        Users.teamName == team_name,
        Submissions.currentStatus == True,
        Submissions.type == True
    ).all()

    return [{'challenge_id': submission.C_idx} for submission in correct_challenges]


# Users Table Model
class Users(db.Model):
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

# UserChallenges Table Model
class UserChallenges(db.Model):
    __tablename__ = 'UserChallenges'

    idx = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_idx = db.Column(db.Integer, ForeignKey('Users.idx'), default=0, nullable=False)
    C_idx = db.Column(db.Integer, db.ForeignKey('Challenges.idx'), nullable=False)
    userChallengeName = db.Column(db.String(255), nullable=False)
    createdAt = db.Column(db.DateTime, default=current_time_kst, nullable=False)


# UserChallenges_status Table Model
class UserChallenges_status(db.Model):
    __tablename__ = 'UserChallenges_status'

    idx = db.Column(db.Integer, primary_key=True, autoincrement=True)
    port = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='None')
    createdAt = db.Column(db.DateTime, default=current_time_kst, nullable=False)
    userChallenge_idx = db.Column(db.Integer, db.ForeignKey('UserChallenges.idx'), nullable=False, default=0)

# Submissions Table Model
class Submissions(db.Model):
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

class Configs(db.Model):
    __tablename__ = 'Configs'

    idx = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), ForeignKey('Users.username'), nullable=False)
    teamMode = db.Column(db.Boolean, default=True, nullable=False)
    teamLimit = db.Column(db.Integer, default=0, nullable=False)
    challengeVisibility = db.Column(Enum('Public', 'Private', 'Admins Only', name='visibility_enum'), default='Admins Only', nullable=False)
    accountVisibility = db.Column(Enum('Public', 'Private', 'Admins Only', name='visibility_enum'), default='Admins Only', nullable=False)
    scoreVisibility = db.Column(Enum('Public', 'Private', 'Hidden', 'Admins Only', name='visibility_enum'), default='Admins Only', nullable=False)
    registrationVisibility = db.Column(Enum('Public', 'Private', name='visibility_enum'), default='Private', nullable=False)
    startTime = db.Column(db.DateTime, nullable=False)
    endTime = db.Column(db.DateTime, nullable=False)
    freezeTime = db.Column(db.DateTime, nullable=False)
    updatedAt = db.Column(db.DateTime, default=current_time_kst, nullable=False)
