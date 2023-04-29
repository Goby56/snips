import mysql.connector, bcrypt
import json

class TableMismatch(Exception):
    """
    Raised if a table doesn't have the same columns
    specified in the 'models.json' file
    """
    def __init__(self, table_name: str) -> None:
        super().__init__(f"The table '{table_name}' does not follow 'models.json' specifications")

class Database:
    def __init__(self, name: str) -> None:
        self.name = name
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
        existing_tables = list(map(lambda x: x[0], self.cursor))
        for table_name, columns in self.models.items():
            if table_name in existing_tables:
                self.validate_table(table_name)
            else:
                self.create_table(table_name, columns)

    def create_table(self, name: str, columns: dict):
        sql_columns = ["id int NOT NULL PRIMARY KEY"]
        for col_name, sql_cmd in columns.items():
            sql_columns.append(sql_cmd % tuple(col_name.split(" ")))
        self.cursor.execute(f"CREATE TABLE {name} ({', '.join(sql_columns)})")

    def validate_table(self, name: str):
        # TODO implement robust table validation
        return
        self.cursor.execute(f"DESCRIBE {name}")
        model = self.models[name]
        for col_name, col_type, *_ in self.cursor:
            if col_name == "id": continue
            # TODO implement robust table validation
            # if name not in self.models.keys():
            #     raise TableMismatch(name)
            # if self.models[name][col_name] != col_type:
            #     raise TableMismatch(name)

    def insert_into(self, table: str, **kwargs):
        columns = ", ".join(kwargs.keys())
        values = ", ".join(kwargs.values())
        self.execute(f"INSERT INTO {table} ({columns}) VALUES ({values})")

    # def authenticate(self, username: str, password: str):
    #     if 
    #     self.execute(f"SELECT username, password FROM user WHERE username='{username}'")
    #     print(self.cursor)
        
    # def register(self, username: str, password: str):
    #     self.execute(f"INSERT INTO user ")
            