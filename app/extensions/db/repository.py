from app.extensions.db.exceptions import QueryException


class BaseRepository:
    def __init__(self, db_connection, model_class):
        """
        Initialize repository

        Args:
            db_connection (DatabaseConnection): Database connection instance
            model_class (class): Model class to use for results
        """
        self.db = db_connection
        self.model_class = model_class

    def find_by_id(self, id):
        """Find single record by ID"""
        query = f"SELECT * FROM {self.get_table_name()} WHERE id = %s"
        results = self.db.execute_query(query, (id,))
        return self.model_class.from_db_row(results[0] if results else None)

    def find_all(self, conditions=None, params=None):
        """Find all records matching conditions"""
        query = f"SELECT * FROM {self.get_table_name()}"
        if conditions:
            query += f" WHERE {conditions}"
        results = self.db.execute_query(query, params)
        return [self.model_class.from_db_row(row) for row in results]

    def create(self, model):
        """Create new record"""
        data = model.to_dict()
        fields = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {self.get_table_name()} ({fields}) VALUES ({placeholders})"

        try:
            self.db.execute_query(query, tuple(data.values()))
            return True
        except QueryException:
            return False

    def update(self, id, model):
        """Update existing record"""
        data = model.to_dict()
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        query = f"UPDATE {self.get_table_name()} SET {set_clause} WHERE id = %s"

        try:
            self.db.execute_query(query, (*data.values(), id))
            return True
        except QueryException:
            return False

    def delete(self, id):
        """Delete record by ID"""
        query = f"DELETE FROM {self.get_table_name()} WHERE id = %s"
        try:
            self.db.execute_query(query, (id,))
            return True
        except QueryException:
            return False

    @classmethod
    def get_table_name(cls):
        """Get table name for repository"""
        raise NotImplementedError("Subclasses must implement get_table_name()")


class ChallengeRepository(BaseRepository):
    """Example repository for challenges"""

    @classmethod
    def get_table_name(cls):
        return 'challenges'