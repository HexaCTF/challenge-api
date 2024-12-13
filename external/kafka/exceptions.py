class KafkaLibException(Exception):
    """Base exception for kafka_lib"""
    pass

class ProducerException(KafkaLibException):
    """Raised when producer encounters an error"""
    pass

class ConsumerException(KafkaLibException):
    """Raised when consumer encounters an error"""
    pass
