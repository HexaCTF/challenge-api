from dataclasses import dataclass


@dataclass
class MariaDBConfig:
    """
    MariaDB 데이터베이스 연결 설정을 관리하는 데이터 클래스
    
    각 필드는 데이터베이스 연결에 필요한 설정값들을 저장합니다.
    기본값이 설정된 필드들은 명시적으로 지정하지 않아도 됩니다.
    """
    
    # 필수 설정값들
    host: str        # 데이터베이스 서버 호스트 주소
    port: int        # 데이터베이스 서버 포트 번호
    database: str    # 사용할 데이터베이스 이름
    username: str    # 데이터베이스 접속 사용자 이름
    password: str    # 데이터베이스 접속 비밀번호
    
    # 선택적 설정값들 (기본값 제공)
    charset: str = 'utf8mb4'      # 문자 인코딩 설정 (기본값: utf8mb4)
    pool_size: int = 5            # 커넥션 풀의 기본 크기
    max_overflow: int = 10        # 커넥션 풀의 최대 초과 허용 개수
    pool_timeout: int = 30        # 커넥션 풀에서 연결을 대기하는 최대 시간(초)
    pool_recycle: int = 3600      # 커넥션 재사용 주기(초)
    connect_timeout: int = 10     # 데이터베이스 연결 시도 제한 시간(초)

    @property
    def connection_string(self) -> str:
        """
        SQLAlchemy에서 사용할 수 있는 데이터베이스 연결 문자열을 생성합니다.
        
        Returns:
            str: MariaDB 연결을 위한 SQLAlchemy 형식의 연결 문자열
                 예시: mysql+mysqlconnector://user:pass@host:port/dbname?charset=utf8mb4
        """
        return (f"mariadb+mariadbconnector://{self.username}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}?"
                f"charset={self.charset}")

    @classmethod
    def from_flask_config(cls, config: dict) -> 'MariaDBConfig':
        """
        Flask 애플리케이션의 설정 딕셔너리로부터 MariaDB 설정을 생성합니다.
        
        Args:
            config (dict): Flask 애플리케이션의 설정 딕셔너리
                         필수 키: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD
                         선택 키: DB_PORT, DB_CHARSET, DB_POOL_SIZE 등
        
        Returns:
            MariaDBConfig: 설정값이 적용된 MariaDB 설정 객체
        
        사용 예시:
            app_config = {
                'DB_HOST': 'localhost',
                'DB_PORT': 3306,
                'DB_NAME': 'myapp',
                'DB_USER': 'user',
                'DB_PASSWORD': 'pass'
            }
            db_config = MariaDBConfig.from_flask_config(app_config)
        """
        return cls(
            host=config['DB_HOST'],
            port=config.get('DB_PORT', 3306),
            database=config['DB_NAME'],
            username=config['DB_USER'],
            password=config['DB_PASSWORD'],
            charset=config.get('DB_CHARSET', 'utf8mb4'),
            pool_size=config.get('DB_POOL_SIZE', 5),
            max_overflow=config.get('DB_MAX_OVERFLOW', 10),
            pool_timeout=config.get('DB_POOL_TIMEOUT', 30),
            pool_recycle=config.get('DB_POOL_RECYCLE', 3600),
            connect_timeout=config.get('DB_CONNECT_TIMEOUT', 10)
        )