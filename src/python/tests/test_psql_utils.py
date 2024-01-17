import sys
sys.path.append('..')
import pickle
from utils.psqlutils import PsqlUtils 
import config.config as config
from utils.loggerfactory import logger


psql_conn = PsqlUtils(logger)

def test_connection ():
    for rec in psql_conn.run_select_query("select version();"):
        var = str(rec[0])[:10] 
        assert (var == "PostgreSQL")

def test_schema():
    q_str = '''SELECT table_name
        FROM information_schema.tables
        WHERE table_schema='public'
        AND table_type='BASE TABLE';'''
    reference_tables = [
            'object',
            'network',
            'timeseries',
            'option',
            'iex_symbols'
            ]
    for rec in psql_conn.run_select_query(q_str):
        assert(str(rec[0]) in reference_tables)

class MyClass:
    def __init__ (self):
        self.var1 = "var1"
        self.var2 = 10


def test_insert():
    testObj = MyClass()
    testObj.var1 = 8
    testObj.var2 = 15
    testObj2 = MyClass()
    rec = {
            "parent_id" : 100,
            "classname" : "AINetwork",
            "score" : 94.9993,
            "lasttraineddate" : 77777777,
            "data" : pickle.dumps(testObj)
    }
    psql_conn.begin()
    recID = psql_conn.insert("network", rec)
    assert(recID > 0)
    psql_conn.commit()

    
    for rec in psql_conn.run_select_query("SELECT * from network WHERE id = {}".format(recID)):
        testObj2.__dict__.update(pickle.loads(rec[5]).__dict__)
        assert (testObj2.var2 == 15)
    return recID

def test_update():
    recID = test_insert()
    psql_conn.begin()
    psql_conn.update("network", {
        "parent_id" : 200,
        "score" : "101010"
    }, {"id" : recID})
    psql_conn.commit()
    rec = list(psql_conn.run_select_query("SELECT * from network WHERE id = {}".format(recID)))[0]
    assert (rec[1] == 200)
    assert (rec[3] == 101010)
    psql_conn.run_select_query("DELETE from network WHERE id = {}".format(recID))

