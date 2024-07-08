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

    def create_tables(self):
        create_page_table_query = """
        CREATE TABLE IF NOT EXISTS page (
            id INT AUTO_INCREMENT PRIMARY KEY,
            website_id INT,
            title VARCHAR(255),
            meta_description TEXT,
            language VARCHAR(10),
            top_headline TEXT,
            word_count INT,
            image_count INT,
            page_type VARCHAR(50),
            external_link_count INT,
            internal_link_count INT,
            url VARCHAR(2048) NOT NULL,
            date_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (website_id) REFERENCES google_results(id)
        );
        """
        self.execute_query(create_page_table_query)
        create_image_table_query = """
        CREATE TABLE IF NOT EXISTS image (
            id INT AUTO_INCREMENT PRIMARY KEY,
            page_id INT,
            hash VARCHAR(100) NOT NULL,
            image_url VARCHAR(2048) NOT NULL,
            src VARCHAR(2048),
            file_name VARCHAR(255),
            alt_text TEXT,
            image_title TEXT,
            image_caption TEXT,
            width INT,
            height INT,
            contains_transparency BOOLEAN,
            headline_above_image TEXT,
            wrapped_element VARCHAR(50),
            semantic_context VARCHAR(50),
            file_size INT,
            file_format VARCHAR(30),
            frequency_on_website INT,
            extracted_text TEXT,
            is_decorative BOOLEAN,
            date_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (page_id) REFERENCES page(id)
        );
        """
        self.execute_query(create_image_table_query)
        print("Tables created")

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

    def execute_query(self, query, params=None, fetch=None):
        try:
            self.connect()
            cursor = self._connection.cursor(buffered=True)
            cursor.execute(query, params)
            self._connection.commit()
            if fetch == 'all':
                result = cursor.fetchall()
            elif fetch == 'one':
                result = cursor.fetchone()
            else:
                result = None
            print("Query executed successfully")
            return result
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    def image_exists(self, img_hash):
        query = "SELECT COUNT(*) FROM image WHERE hash = %s"
        self.execute_query(query, img_hash)
        result = self._connection.cursor.fetchone()
        return result[0] > 0

    def insert_page(self, page_data):
        query = """
        INSERT INTO page (title, meta_description, language, top_headline, word_count, image_count, external_link_count, internal_link_count, url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (page_data['title'], page_data['meta_description'], page_data['language'], page_data['top_headline'], page_data['word_count'],
                  page_data['image_count'], page_data['external_link_count'],
                  page_data['internal_link_count'], page_data['url'])
        self.connect()
        cursor = self._connection.cursor()
        cursor.execute(query, params)
        last_row_id = self._connection.cursor().lastrowid
        self._connection.commit()
        return last_row_id

    def insert_image(self, image_data):
        query = """
        INSERT INTO image (page_id, hash, image_url, src, file_name, alt_text, image_title, image_caption, width, height, contains_transparency, headline_above_image, wrapped_element, semantic_context, file_size, file_format)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            image_data['page_id'], image_data['hash'], image_data['image_url'], image_data['src'],
            image_data['file_name'], image_data['alt_text'], image_data['image_title'], image_data['image_caption'],
            image_data['width'], image_data['height'], image_data['contains_transparency'], image_data['headline_above_image'], image_data['wrapped_element'], image_data['semantic_context'],
            image_data['file_size'], image_data['file_format'])
        self.execute_query(query, params)
