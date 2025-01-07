class DatabaseError(Exception):
    """Base exception for database errors"""
    pass

class ConnectionError(DatabaseError):
    """Raised when database connection fails"""
    pass

class InitializationError(DatabaseError):
    """Raised when database initialization fails"""
    pass

class SessionError(DatabaseError):
    """Raised when session operations fail"""
    pass

class QueryError(DatabaseError):
    """Raised when database query fails"""
    pass

class ConfigurationError(DatabaseError):
    """Raised when configuration is invalid"""
    pass