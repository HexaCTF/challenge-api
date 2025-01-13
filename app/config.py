import os

class Config:
    """
    Flask 애플리케이션의 설정 클래스
    
    환경 변수를 통해 설정값을 주입받으며, 없는 경우 기본값을 사용합니다.
    주요 설정 카테고리:
    - 데이터베이스 연결 설정
    - SQLAlchemy ORM 설정
    - 보안 관련 설정
    - Kafka 메시징 설정
    """

    # =========================================================================
    # Flask 기본 설정
    # =========================================================================
    PROPAGATE_EXCEPTIONS = True  # 예외를 상위로 전파하도록 설정
    
    # =========================================================================
    # 데이터베이스 기본 연결 설정
    # =========================================================================
    DB_HOST = os.getenv('DB_HOST', 'mariadb')           # 데이터베이스 호스트
    DB_PORT = os.getenv('DB_PORT', '3306')              # 데이터베이스 포트
    DB_NAME = os.getenv('DB_NAME', 'challenge_db')      # 데이터베이스 이름
    DB_USER = os.getenv('DB_USER', 'challenge_user')    # 데이터베이스 사용자
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'challenge_password')  # 데이터베이스 비밀번호
    
    # =========================================================================
    # SQLAlchemy ORM 설정
    # =========================================================================
    # 데이터베이스 연결 문자열
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@"
        f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    
    # SQLAlchemy 동작 설정
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 수정 추적 비활성화 (성능 향상)
    
    # 커넥션 풀 설정
    SQLALCHEMY_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))        # 기본 풀 크기
    SQLALCHEMY_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10')) # 최대 초과 커넥션
    
    # =========================================================================
    # 보안 설정
    # =========================================================================
    SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')  # 암호화 키
    SESSION_COOKIE_HTTPONLY = True      # JavaScript에서 세션 쿠키 접근 방지
    SESSION_COOKIE_SAMESITE = 'Lax'     # CSRF 공격 방지를 위한 SameSite 설정
    
    # =========================================================================
    # Kafka 메시징 설정
    # =========================================================================
    # Kafka 브로커 및 토픽 설정
    KAFKA_BOOTSTRAP_SERVERS = os.getenv(
        'KAFKA_BOOTSTRAP_SERVERS', 
        'localhost:9093'
    )  # Kafka 브로커 주소
    
    KAFKA_TOPIC = os.getenv(
        'KAFKA_TOPIC', 
        'challenge-status'
    )  # 메시지 토픽명
    
    KAFKA_GROUP_ID = os.getenv(
        'KAFKA_GROUP_ID', 
        'challenge-consumer-group'
    )  # 컨슈머 그룹 ID