from prometheus_client import REGISTRY, Gauge, Counter, CONTENT_TYPE_LATEST

class ChallengeMetricsCollector:
    def __init__(self):
        # 챌린지 상태 Gauge
        self.challenge_state = Gauge(
            'challenge_state',
            'Current state of challenges',
            ['challenge_id', 'username','state']  # 1: active, 0: inactive
        )

        # API 요청 결과 카운터
        self.challenge_operations = Counter(
            'challenge_operations_total',
            'Challenge operation results',
            ['operation', 'result']  # operation: create/delete/status, result: success/error
        )

        # 레지스트리에 메트릭 등록
        # self.register_metrics()

    def register_metrics(self):
        """
        Prometheus 레지스트리에 메트릭을 등록
        """
        REGISTRY.register(self)

    def collect(self):
        """
        Prometheus Collector 인터페이스 구현 메서드
        실제 메트릭을 수집하여 반환
        """
        yield self.challenge_state
        yield self.challenge_operations
    
    def update_challenge_state(self, challenge_id: str, username: str, state: int):
        """
        챌린지 상태 업데이트
        :param challenge_id: 챌린지 ID
        :param username: 사용자 이름
        :param state: 상태 (1: active, 0: inactive)
        """
        self.challenge_state.labels(
            challenge_id=challenge_id,
            username=username
        ).set(state)

    def record_challenge_operation(self, operation: str, result: str):
        """
        챌린지 작업 결과 기록
        :param operation: 작업 유형 (create/delete/status)
        :param result: 결과 (success/error)
        """
        self.challenge_operations.labels(
            operation=operation,
            result=result
        ).inc()


challenge_metrics_collector = ChallengeMetricsCollector()
