import psycopg2
import os

from os.path import exists
from exceptions.exceptions import DataIntegrityCompromised, RecordNotFound
from utils.loggerfactory import logger

QUERY_ARRAY_SIZE = 20

class DoubleTransactionBegin(Exception):
    pass


class NoActiveTransaction(Exception):
    pass


class PsqlUtils:
    connection = None

    def __init__(self):
        self.transaction_active = False
        try:
            # We need to get the ip of psql container. If this code is run from a docker container
            # ip is what psql ip is otherwise we use localhost, in case it is run on host
            db_host = "127.0.0.1"
            db_port = 5432
            # no container, running from host
            if not os.getenv("RUN_TIME_ENV") == 'docker':
                db_host = "127.0.0.1"
                db_port = 5432

            if not PsqlUtils.connection:
                PsqlUtils.connection = psycopg2.connect(
                    # host="localhost",
                    host=db_host,
                    database="capitalist",
                    user="postgres",
                    password="root", port=db_port)  # AWS pass BuGala78!

            self.psqlConnection = PsqlUtils.connection

        except (Exception, psycopg2.DatabaseError) as error:
            logger().error("Error while connecting to db", error)

    def run_no_result_query(self, query_string):
        cursor = self.psqlConnection.cursor()
        cursor.execute(query_string)
        self.psqlConnection.commit()
        cursor.close()

    def run_select_query(self, query_string):
        cursor = self.psqlConnection.cursor()
        cursor.execute(query_string)
        try:
            while True:
                results = cursor.fetchmany(QUERY_ARRAY_SIZE)
                if results:
                    for result in results:
                        yield result
                else:
                    self.psqlConnection.commit()
                    cursor.close()
                    break
        except psycopg2.ProgrammingError as e:
            if 'no results to fetch in e':
                pass
            else:
                raise

    def select(self, table, where_dict, limit = None):
        whereCols = ['{}'.format(col) for col in where_dict.keys()]
        whereVals = ["'{}'".format(col) for col in where_dict.values()]

        sql_string = "SELECT * FROM " + table
        if (where_dict):
            sql_string = sql_string + " WHERE " + \
                " AND ".join(['='.join(map(str, i))
                             for i in zip(whereCols, whereVals)]).format(table)
        if limit:
            sql_string = sql_string + f" LIMIT {limit}"
        return self.run_select_query(sql_string)

    def insert(self, table, row):
        cursor = self.psqlConnection.cursor()
        cols = ', '.join('"{}"'.format(col.lower()) for col in row.keys())
        place_holders = ', '.join('%s' for col in row.keys())
        vals = tuple([row[col] for col in row.keys()])
        sql = '''INSERT INTO {0} ({1}) VALUES ({2})
            RETURNING id
            '''.format(table, cols, place_holders)
        cursor.execute(sql, vals)
        id = cursor.fetchone()[0]
        cursor.close()

        if not self.transaction_active:
            self.psqlConnection.commit()

        return id

    def update(self, table, row, where_dict):
        cursor = self.psqlConnection.cursor()
        cols = ['{}'.format(col) for col in row.keys()]
        vals = ["'{}'".format(col) for col in row.values()]
        vals = tuple([row[k] for k in row.keys()])

        whereCols = ['{}'.format(col) for col in where_dict.keys()]
        whereVals = ["'{}'".format(col) for col in where_dict.values()]

        sql_string = "UPDATE " + table + " SET " + ",".join(['=%'.join(map(str, i)) for i in zip(cols, "s" * len(
            cols))]) + " WHERE " + " AND ".join(['='.join(map(str, i)) for i in zip(whereCols, whereVals)]).format(table)
        cursor.execute(sql_string, vals)
        cursor.close()
        if not self.transaction_active:
            self.psqlConnection.commit()
        psycopg2.errors.NotNullViolation

    def delete (self, table, where_dict):
        whereCols = ['{}'.format(col) for col in where_dict.keys()]
        whereVals = ["'{}'".format(col) for col in where_dict.values()]

        sql_string = "DELETE FROM " + table
        if (where_dict):
            sql_string = sql_string + " WHERE " + \
                " AND ".join(['='.join(map(str, i))
                             for i in zip(whereCols, whereVals)]).format(table)
        return self.run_select_query(sql_string)



    def delete_record(self, table, record_id, index_field="id"):
        sql = "DELETE FROM  {0} WHERE {2} = '{1}'".format(
            table, record_id, index_field)
        cursor = self.psqlConnection.cursor()
        print(sql)
        cursor.execute(sql)
        if not self.transaction_active:
            self.psqlConnection.commit()

    def count_records(self, table_name, where_dict):
        ''' checks if given where filter applied on table returns any records
            returns the number of records matchong the filter
        '''
        whereCols = ['{}'.format(col) for col in where_dict.keys()]
        whereVals = ["'{}'".format(col) for col in where_dict.values()]

        sql_string = "SELECT COUNT (*) FROM " + table_name + " WHERE " + " AND ".join(
            ['='.join(map(str, i)) for i in zip(whereCols, whereVals)]).format(table_name)
        print(sql_string)
        cursor = self.psqlConnection.cursor()
        cursor.execute(sql_string)
        print(cursor.rowcount)
        results = cursor.fetchone()
        print(results)
        return results[0]

    def begin(self):
        if self.transaction_active:
            raise DoubleTransactionBegin()
        self.psqlConnection.cursor().execute("BEGIN TRANSACTION;")
        self.transaction_active = True

    def commit(self):
        if not self.transaction_active:
            raise NoActiveTransaction()
        self.psqlConnection.cursor().execute("COMMIT;")
        self.transaction_active = False

    def rollback(self):
        if not self.transaction_active:
            raise NoActiveTransaction()
        self.psqlConnection.cursor().execute("ROLLBACK;")
        self.transaction_active = False

    def check_if_record_exists(self, table_name, unique_id, field_name="id"):
        '''
            Utility function that returns True if given id exists in given table
        '''
        query = f"SELECT id FROM {table_name} WHERE {field_name} = '{unique_id}'"
        result_set = list(self.run_select_query(query))
        if (len(result_set)) == 0:
            return False
        return True

    def query_with_where(self, table_name, where_dict=None):
        '''
            Utility function that returns True if given id exists in given table
        '''
        query_string = "SELECT * FROM " + table_name
        if (where_dict):
            whereCols = ['{}'.format(col) for col in where_dict.keys()]
            whereVals = ["'{}'".format(col) for col in where_dict.values()]
            query_string = query_string + " WHERE " + \
                " AND ".join(['='.join(map(str, i)) for i in zip(
                    whereCols, whereVals)]).format(table_name)
        return self.run_select_query(query_string)

    def return_first_if_exists(self, table_name, unique_id, field_name="id"):
        '''
            Utility function that returns the first record if given id exists in given table
        '''
        query = f"SELECT * FROM {table_name} WHERE {field_name} = '{unique_id}'"

        for rec in self.run_select_query(query):
            return rec

        return None

    def return_first_if_exists_with_where(self, table_name, where_dict):
        '''
            Utility function that returns the first record if given id exists in given table
            by uing given where clause
        '''
        recs = self.query_with_where (table_name, where_dict)
        record_to_return = None
        for rec in recs:
            if record_to_return:
                raise DataIntegrityCompromised(
                    f" Query for table: {table_name} , filter: {str(where_dict)} returns multiple values.")
            return rec

        return None


    def return_single_if_exists(self, table_name, unique_id, field_name="id"):
        '''
            Utility function that returns the only record if given id exists in given table.
            If result set has more than single record errors out
        '''
        query = f"SELECT * FROM {table_name} WHERE {field_name} = '{unique_id}'"

        rec_to_return = None

        for rec in self.run_select_query(query):
            if (rec_to_return):
                raise DataIntegrityCompromised(
                    f" Query for table: {table_name} , unique_id: {unique_id} for field: {field_name} returns multiple values.")
            rec_to_return = rec
        if rec_to_return:
            return rec_to_return
        else:
            raise RecordNotFound(
                f" Query for table: {table_name} , unique_id: {unique_id} for field: {field_name} returns no value.")

    def __del__(self):
        if PsqlUtils.connection:
            PsqlUtils.connection.close()
