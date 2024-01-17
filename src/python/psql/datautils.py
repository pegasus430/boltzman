import sys
sys.path.append('..')
import config.config as config
import json
from utils.psqlutils import PsqlUtils 
sql_utils = PsqlUtils()

class DataUtils:
    def __init__(self) -> None:
        pass
    def import_nasdaq_symbols(self):
        print ("Importing NASDAQ symbols.")
        sql_utils.begin()
        for r in sql_utils.run_select_query("DELETE FROM option"):
            print (r)
        sql_utils.commit()
        f = open('../data/nasdaq.json')
        data = json.load(f)
        sql_utils.begin()
        for i in data:
            if i["Symbol"] in config.AVAILABLE_SYMBOLS:
                sql_utils.insert("option",{
                    "parent_id" : -1,
                    "optionname" : i["Symbol"],
                    "optionclass" : "STOCK",
                    "optionexchange" : "NASDAQ"
                    })
        sql_utils.commit()
        f.close()        

