# db_lib/exceptions.py
class DatabaseException(Exception):
    """Base exception for database operations"""
    pass

class ConnectionException(DatabaseException):
    """Raised when database connection fails"""
    pass

class QueryException(DatabaseException):
    """Raised when query execution fails"""
    pass
