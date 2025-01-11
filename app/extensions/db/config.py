from dataclasses import dataclass

@dataclass
class MariaDBConfig:
    """MariaDB configuration class"""
    host: str
    port: int
    database: str
    username: str
    password: str
    charset: str = 'utf8mb4'
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    connect_timeout: int = 10

    @property
    def connection_string(self) -> str:
        """Generate SQLAlchemy connection string for MariaDB"""
        return (f"mysql+mysqlconnector://{self.username}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}?"
                f"charset={self.charset}")

    @classmethod
    def from_flask_config(cls, config: dict) -> 'MariaDBConfig':
        """Create configuration from Flask config dictionary"""
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