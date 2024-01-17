import json
import sys
import config.config as config
from utils.psqlutils import PsqlUtils 
sql_utils = PsqlUtils()

def insert_symbol (data):
    sql_utils.begin()
    record = {
        "symbol": data["symbol"],
        "exchange": data["exchange"],
        "exchangeSuffix": data["exchangeSuffix"],
        "exchangeName": data["exchangeName"],
        "exchangeSegment": data["exchangeSegment"],
        "exchangeSegmentName": data["exchangeSegmentName"],
        "name": data["name"],
        "date": data["date"],
        "type": data["type"],
        "iexId": data["iexId"],
        "region": data["region"],
        "currency": data["currency"],
        "isEnabled": data["isEnabled"],
        "figi": data["figi"],
        "cik": data["cik"],
        "lei": data["lei"]        
    }
    sql_utils.insert("symbols", record)
    sql_utils.commit()



def ingest_symbol_meta (file_path):
    '''
        inserts iex supported stock meta to database.
        file is the output of iex https://iexcloud.io/docs/api/#symbols api call
        Make sure to empty symbols table before running this script to avoid multiple entirees.
        ****** THIS SHOULD NOT BE RUN FREQUENTLY OR YET NEVER!!!!
    '''
    with open(file_path) as json_file:
        data = json.load(json_file)
        for stock_block in data:
            print (stock_block)
            insert_symbol(stock_block, {})

def activate_stocks(number_of_stocks):
    sql_utils.run_no_result_query(
    '''
    WITH x AS (
        SELECT *
            FROM symbols
            WHERE active=0
            ORDER BY random()
            LIMIT %1
    )
    update symbols set active = 1 from x
    WHERE symbols.id = x.id;    
    '''.format(number_of_stocks))

activate_stocks(10000)