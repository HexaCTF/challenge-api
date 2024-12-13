
class KafkaConfig:
    def __init__(
        self,
        bootstrap_servers=None,
        topic=None,
        group_id=None,
        **kwargs
    ):
        self.bootstrap_servers = bootstrap_servers or ['localhost:9092']
        self.topic = topic or 'default_topic'
        self.group_id = group_id or 'default_group'
        self.additional_config = kwargs

    @property
    def producer_config(self):
        return {
            'bootstrap_servers': self.bootstrap_servers,
            'acks': 'all',
            'retries': 3,
            'retry_backoff_ms': 100,
            **self.additional_config
        }

    @property
    def consumer_config(self):
        return {
            'bootstrap_servers': self.bootstrap_servers,
            'group_id': self.group_id,
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': True,
            **self.additional_config
        }