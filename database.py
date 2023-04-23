import mysql.connector
import json

class TableMismatch(Exception):
    """
    Raised if a table doesn't have the same columns
    specified in the 'models.json' file
    """

class Database:
    def __init__(self) -> None:
        self.name = "snips"
        with open("models.json") as f:
            self.models = json.load(f)

        self.db_connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        self.cursor = self.db_connection.cursor()

        self.validate()

    def execute(self, sql: str):
        self.cursor.execute(sql)
    
    def validate(self):
        self.cursor.execute("SHOW DATABASES")
        if self.name not in map(lambda x: x[0], self.cursor):
            self.cursor.execute(f"CREATE DATABASE {self.name}")
        self.db_connection.connect(database=self.name)

        self.cursor.execute("SHOW TABLES")
        existing_tables = map(lambda x: x[0], self.cursor)
        for table_name, columns in self.models.items():
            if table_name in existing_tables:
                self.validate_table(table_name)
            else:
                self.create_table(table_name, columns)

    def create_table(self, name: str, columns: list):
        self.cursor.execute(f"CREATE TABLE {name} (id int NOT NULL PRIMARY KEY, {', '.join(columns)})")

    def validate_table(self, name: str):
        self.cursor.execute(f"DESCRIBE {name}")
        for col_name, col_type, *_ in self.cursor:
            if self.models[name][col_name] != col_type:
                raise TableMismatch(f"The table '{name}' does not follow 'models.json' specifications")
            
db = Database()