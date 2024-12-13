class DatabaseConfig:
    def __init__(
        self,
        host='localhost',
        port=3306,
        user=None,
        password=None,
        database=None,
        **kwargs
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.additional_config = kwargs

    @property
    def connection_params(self):
        return {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': self.database,
            **self.additional_config
        }