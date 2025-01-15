
# Loki 로거 설정
import logging
import logging_loki


def setup_loki_loggers():
    # 공통 Loki 설정
    loki_handler = logging_loki.LokiHandler(
        url="http://localhost:3100/loki/api/v1/push",
        tags={"service": "challenge_app"},
        version="1"
    )
    
    # 에러 로거 설정
    error_logger = logging.getLogger("error")
    error_logger.setLevel(logging.ERROR)
    error_logger.addHandler(loki_handler)
    
    # 네트워크 로거 설정
    network_logger = logging.getLogger("network")
    network_logger.setLevel(logging.INFO)
    network_logger.addHandler(loki_handler)
    
    return error_logger, network_logger

error_logger, network_logger = setup_loki_loggers()