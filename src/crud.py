from mysql.connector.cursor import MySQLCursor
from mysql.connector.connection import MySQLConnection
import json

class CrudOperation:
    def __init__(self, connection: MySQLConnection, cursor: MySQLCursor) -> None:
        self.connection = connection
        self.cursor = cursor
        
    def exec_sql(self, sql_cmd: str, *args, commit = False):
        print("command:", sql_cmd, "args:", *args)
        if len(args) < 1:
            self.cursor.execute(sql_cmd)
        else:
            self.cursor.execute(sql_cmd, args)
        if commit:
            self.connection.commit()
        return self.cursor.fetchall()
    
    @classmethod
    def construct(cls, sql_cmd, default_commit_value):
        """Preserves the scope of each crud method creation. `sql_cmd` is therefore unique for the lambda returned"""
        return lambda self, *args, commit=default_commit_value: \
            cls.exec_sql(self, sql_cmd, *args, commit=commit)


class Create(CrudOperation):
    commit = True


class Read(CrudOperation):
    commit = False


class Update(CrudOperation):
    commit = True


class Delete(CrudOperation):
    commit = True


with open("./db/commands.json", "r") as f:
    crud_commands = json.load(f)

for Operation in CrudOperation.__subclasses__():
    for op, cmd in crud_commands[Operation.__name__.lower()].items():
        setattr(Operation, op, CrudOperation.construct(cmd, Operation.commit))

if __name__ == "__main__":
    for Class in CrudOperation.__subclasses__():
        for attr in dir(Class):
            if callable(getattr(Class, attr)) and not attr.startswith("__"):
                print(Class.__name__, attr)
