from prometheus_client import Gauge, Counter

class ChallengeMetricsCollector:
    def __init__(self):
        # 챌린지 상태 Gauge
        self.challenge_state = Gauge(
            'challenge_state',
            'Current state of challenges',
            ['challenge_id', 'username']  # 1: active, 0: inactive
        )
        
        # API 요청 결과 카운터
        self.challenge_operations = Counter(
            'challenge_operations_total',
            'Challenge operation results',
            ['operation', 'result']  # operation: create/delete/status, result: success/error
        )
