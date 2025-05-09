# Kaf
class KafkaConfig:
    """Kafka 설정 클래스"""
    def __init__(
        self,
        bootstrap_servers=None, # Kafka 서버 주소 리스트
        topic=None, # Kafka Topic 이름
        group_id=None, # Kafka Consumer Group ID
        **kwargs
    ):
        """KafkaConfig 생성자"""
        self.bootstrap_servers = bootstrap_servers or ['localhost:9093']
        self.topic = topic or 'challenge-status' 
        self.group_id = group_id or 'challenge-consumer-group'
        self.additional_config = kwargs

    @property
    def consumer_config(self):
        """Kafka Consumer 설정을 반환

        Returns:
            dict: Kafka consumer configuration
        """
        config = {
            'bootstrap_servers': self.bootstrap_servers,
            'group_id': self.group_id,
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': True,
            'security_protocol': 'PLAINTEXT',  # 보안 프로토콜 명시
            'session_timeout_ms': 30000,  # 30초로 줄임
            'request_timeout_ms': 15000,  # 15초로 줄임
            'max_poll_interval_ms': 300000,
            'heartbeat_interval_ms': 1000,  # 1초로 줄임
            'max_partition_fetch_bytes': 1048576,
            'fetch_max_wait_ms': 500,
            'metadata_max_age_ms': 300000,
            'reconnect_backoff_ms': 100,  # 증가
            'reconnect_backoff_max_ms': 10000,  # 증가
            'api_version_auto_timeout_ms': 5000,  # API 버전 자동 감지 타임아웃
            'connections_max_idle_ms': 540000,  # 연결 유휴 시간
            'retry_backoff_ms': 100,  # 재시도 간격
        }
        
        if self.additional_config:
            config.update(self.additional_config)
            
        return config