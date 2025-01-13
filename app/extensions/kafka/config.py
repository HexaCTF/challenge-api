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
            bootstrap_servers (list): Kafka 서버 주소 리스트
            group_id (str): Kafka Consumer Group ID
            auto_offset_reset (str): Consumer가 메세지를 읽을 위치 
            enable_auto_commit (bool): 자동 커밋 여부
        """
        return {
            'bootstrap_servers': self.bootstrap_servers, # Kafka 서버 주소 리스트
            'group_id': self.group_id, # Kafka Consumer Group ID
            'auto_offset_reset': 'earliest', # Consumer가 메세지를 읽을 위치, 데이터 손실 방지를 위해 earliest로 설정
            'enable_auto_commit': True, # 자동 커밋 여부
            **self.additional_config
        }