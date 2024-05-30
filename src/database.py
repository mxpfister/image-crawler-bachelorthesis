import mysql.connector


class Database:
    _instance = None

    def __new__(cls, host, username, password, database, port):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._connection = None
            cls._instance.host = host
            cls._instance.username = username
            cls._instance.password = password
            cls._instance.database = database
            cls._instance.port = port
        return cls._instance


    def connect(self):
        try:
            if self._connection is not None:
                return
            self._connection = mysql.connector.connect(
                host=self.host,
                user=self.username,
                password=self.password,
                database=self.database,
                port=self.port
            )
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    def disconnect(self):
        if self._connection.is_connected():
            self._connection.close()
            self._connection = None
            print("Disconnected from MySQL database")

    def execute_query(self, query, params=None):
        try:
            self.connect()
            cursor = self._connection.cursor()
            cursor.execute(query, params)
            self._connection.commit()
            print("Query executed successfully")
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    def image_exists(self, img_hash):
        query = "SELECT COUNT(*) FROM image WHERE hash = %s"
        self.execute_query(query, img_hash)
        result = self._connection.cursor.fetchone()
        return result[0] > 0
