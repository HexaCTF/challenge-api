from contextlib import contextmanager

from external.db.exceptions import QueryException, ConnectionException


class DatabaseConnection:
    def __init__(self, config):
        """
        Initialize database connection with configuration

        Args:
            config (DatabaseConfig): Configuration instance
        """
        self.config = config
        self._connection = None
        self._cursor = None

    def connect(self):
        """Establish database connection"""
        try:
            if not self._connection or not self._connection.is_connected():
                self._connection = mysql.connector.connect(
                    **self.config.connection_params
                )
        except Exception as e:
            raise ConnectionException(f"Failed to connect to database: {str(e)}")

    def disconnect(self):
        """Close database connection"""
        if self._cursor:
            self._cursor.close()
        if self._connection:
            self._connection.close()
        self._cursor = None
        self._connection = None

    @contextmanager
    def cursor(self, dictionary=True):
        """
        Context manager for database cursor

        Args:
            dictionary (bool): Return results as dictionaries if True
        """
        try:
            self.connect()
            cursor = self._connection.cursor(dictionary=dictionary)
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            raise QueryException(f"Database operation failed: {str(e)}")
        finally:
            cursor.close()

    def execute_query(self, query, params=None):
        """
        Execute a query and return results

        Args:
            query (str): SQL query
            params (tuple): Query parameters
        """
        with self.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()

    def execute_many(self, query, params_list):
        """
        Execute the same query with different parameters

        Args:
            query (str): SQL query
            params_list (list): List of parameter tuples
        """
        with self.cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount