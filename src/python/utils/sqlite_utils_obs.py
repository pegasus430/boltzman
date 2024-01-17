import sqlite3
import errno
from os.path import exists

QUERY_ARRAY_SIZE = 20;
DEFAULT_SCHEMA_PATH = "/Users/arifbilgin/workspace/brain/brain/src/cpp/capitalist/schema.sql"


class DoubleTransactionBegin(Exception):
    pass

class NoActiveTransaction(Exception):
    pass

class sqlite_utils:
    def __init__ (self, path, logger):
        self.transaction_active = False
        try:
            self.logger = logger
            if not exists(path):
                raise FileNotFoundError(path)            
            self.sqliteConnection = sqlite3.connect(path)
            cursor = self.sqliteConnection.cursor()
            sqlite_select_Query = "select sqlite_version();"
            cursor.execute(sqlite_select_Query)
            record = cursor.fetchall()
            self.logger().info("SQLite Database Version is: {}".format(record[0]))
            cursor.close()
        except sqlite3.Error as error:
            self.logger().error("Error while connecting to sqlite", error)
    def run_select_query (self, query_string):
        cursor = self.sqliteConnection.cursor()
        cursor.execute(query_string)
        while True:
            results = cursor.fetchmany(QUERY_ARRAY_SIZE)
            if not results:
                break
            for result in results:
                yield result
        self.sqliteConnection.commit()
        cursor.close()

    def insert(self, table, row):
        cursor = self.sqliteConnection.cursor()
        cols = ', '.join('"{}"'.format(col) for col in row.keys())
        vals = ', '.join(':{}'.format(col) for col in row.keys())
        sql = 'INSERT INTO "{0}" ({1}) VALUES ({2})'.format(table, cols, vals)
        cursor.execute(sql, row)
        return cursor.execute('''select last_insert_rowid()''').fetchone()[0]

    def update(self, table, row, where_dict):

        cols = ['{}'.format(col) for col in row.keys()]
        vals = ["'{}'".format(col) for col in row.values()]
        vals = tuple([row[k] for k in row.keys()])

        whereCols = ['{}'.format(col) for col in where_dict.keys()]
        whereVals = ["'{}'".format(col) for col in where_dict.values()]
        zipped = zip (cols, vals) 

        sql_string = "UPDATE "+ table +" SET " + ",".join(['='.join(map(str, i)) for i in zip(cols, "?" * len(cols))]) + " WHERE " + " AND ".join(['='.join(map(str, i)) for i in zip(whereCols, whereVals)]).format(table)
        self.sqliteConnection.cursor().execute(sql_string, vals)

    @staticmethod
    def create_db (path, schemaFilePath = DEFAULT_SCHEMA_PATH):
        if exists(path):
            raise FileExistsError(
                path)          
        file = open(schemaFilePath)
        sqliteConnection = sqlite3.connect(path)
        cursor = sqliteConnection.cursor()
        cursor.executescript(file.read())
        sqliteConnection.commit()
    def begin(self):
        if self.transaction_active:
            raise DoubleTransactionBegin()
        self.sqliteConnection.cursor().execute("BEGIN TRANSACTION;")    
        self.transaction_active = True

    def commit(self):
        if not self.transaction_active:
            raise NoActiveTransaction()
        self.sqliteConnection.cursor().execute("COMMIT;")
        self.transaction_active = False

    def rollback(self):
        if not self.transaction_active:
            raise NoActiveTransaction()
        self.sqliteConnection.cursor().execute("ROLLBACK;")
        self.transaction_active = False

