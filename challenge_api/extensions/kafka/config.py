import os
from typing import List, Dict, Any, Optional

class KafkaConfig:
    """Kafka 설정 클래스"""
    def __init__(
        self,
        bootstrap_servers: Optional[List[str]] = None,
        topic: Optional[str] = None,
        group_id: Optional[str] = None,
        **kwargs: Any
    ):
        """KafkaConfig 생성자
        
        Args:
            bootstrap_servers: Kafka 서버 주소 리스트
            topic: Kafka Topic 이름
            group_id: Kafka Consumer Group ID
            kwargs: 추가 설정값
        """
        self.bootstrap_servers = bootstrap_servers or \
            os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9093').split(',')
        self.topic = topic or os.environ.get('KAFKA_TOPIC', 'challenge-status')
        self.group_id = group_id or os.environ.get('KAFKA_GROUP_ID', 'challenge-consumer-group')
        self.additional_config = kwargs

    @property
    def consumer_config(self) -> Dict[str, Any]:
        """Kafka Consumer 설정을 반환

        Returns:
            dict: Kafka consumer configuration
        """
        config = {
            'bootstrap_servers': self.bootstrap_servers,
            'group_id': self.group_id,
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': True,
            'security_protocol': os.environ.get('KAFKA_SECURITY_PROTOCOL', 'PLAINTEXT'),
            'session_timeout_ms': int(os.environ.get('KAFKA_SESSION_TIMEOUT_MS', '30000')),
            'request_timeout_ms': int(os.environ.get('KAFKA_REQUEST_TIMEOUT_MS', '15000')),
            'max_poll_interval_ms': int(os.environ.get('KAFKA_MAX_POLL_INTERVAL_MS', '300000')),
            'heartbeat_interval_ms': int(os.environ.get('KAFKA_HEARTBEAT_INTERVAL_MS', '1000')),
            'max_partition_fetch_bytes': int(os.environ.get('KAFKA_MAX_PARTITION_FETCH_BYTES', '1048576')),
            'fetch_max_wait_ms': int(os.environ.get('KAFKA_FETCH_MAX_WAIT_MS', '500')),
            'metadata_max_age_ms': int(os.environ.get('KAFKA_METADATA_MAX_AGE_MS', '300000')),
            'reconnect_backoff_ms': int(os.environ.get('KAFKA_RECONNECT_BACKOFF_MS', '100')),
            'reconnect_backoff_max_ms': int(os.environ.get('KAFKA_RECONNECT_BACKOFF_MAX_MS', '10000')),
            'api_version_auto_timeout_ms': int(os.environ.get('KAFKA_API_VERSION_AUTO_TIMEOUT_MS', '5000')),
            'connections_max_idle_ms': int(os.environ.get('KAFKA_CONNECTIONS_MAX_IDLE_MS', '540000')),
            'retry_backoff_ms': int(os.environ.get('KAFKA_RETRY_BACKOFF_MS', '100')),
        }
        
        # SSL 설정이 필요한 경우 추가
        if os.environ.get('KAFKA_SSL_ENABLED', 'false').lower() == 'true':
            ssl_config = {
                'security_protocol': 'SSL',
                'ssl_cafile': os.environ.get('KAFKA_SSL_CA_FILE'),
                'ssl_certfile': os.environ.get('KAFKA_SSL_CERT_FILE'),
                'ssl_keyfile': os.environ.get('KAFKA_SSL_KEY_FILE'),
            }
            config.update(ssl_config)
        
        if self.additional_config:
            config.update(self.additional_config)
            
        return config