class DatabaseError(Exception):
    """Base exception for database errors"""
    pass

class DBUpdateError(DatabaseError):
    """Exception raised when an update operation fails"""
    pass