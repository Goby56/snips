import mysql.connector
import json, os

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
        with open("./db/models.json") as f:
            self.models = json.load(f)

        self.db_connection = mysql.connector.connect(
            host=os.getenv("MYSQLHOST", default="localhost"),
            port=os.getenv("MYSQLPORT", default=3306),
            user=os.getenv("MYSQLUSER", default="root"),
            password=os.getenv("MYSQLPASSWORD", default="")
        )
        self.cursor = self.db_connection.cursor(prepared=True)

        self.validate()
    
    def validate(self):
        self.cursor.execute("SHOW DATABASES")
        if self.name not in map(lambda x: x[0], self.cursor.fetchall()):
            self.cursor.execute(f"CREATE DATABASE {self.name}")
        self.db_connection.connect(database=os.getenv("MYSQLDATABASE", default=self.name))
        
        self.cursor.execute("SHOW TABLES")
        existing_tables = list(map(lambda x: x[0], self.cursor.fetchall()))
        for table_name, model in self.models.items():
            if table_name in existing_tables:
                self.validate_table(table_name)
            else:
                self.create_table(table_name, model["columns"], model["constraints"])

    def create_table(self, name: str, columns: dict, constraints: dict):
        sql_columns = ["id int NOT NULL PRIMARY KEY AUTO_INCREMENT"]
        for col_name, sql_cmd in columns.items():
            sql_columns.append(sql_cmd % tuple(col_name.split(" ")))
        for values, sql_cmd in constraints.items():
            sql_columns.append(sql_cmd % tuple(values.split(" ")))
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
        self.cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({values})")

   
            