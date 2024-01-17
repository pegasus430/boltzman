from datetime import datetime
from datetime import timezone
from datetime import timedelta, date
from functools import cache
import time
import enum
import time
import uuid
from xmlrpc.client import DateTime
from numpy import source
import config.config as config
from utils.loggerfactory import logger
from core.aibase import AIAggregationType
from utils.iex import IEX
API_URL = "https://cloud.iexapis.com/"
TOKEN = 'pk_5eec2e7eb99945c588d1bf1b84346a93'
from utils.iex import IEX

iex = IEX (API_URL, TOKEN)
from utils.psqlutils import PsqlUtils 
sql_utils = PsqlUtils()


class AIIntakeStatus(enum.Enum):
    InProgress = 0 
    Completed = 1
    Failed = 2


def insert_market_calendar():
    calendar = [
            ("XNAS" , datetime(2022, 1, 17), "Martin Luther King, Jr. Day",0,"US"),
            ("XNAS" , datetime(2022, 2, 21), "President's Day",0,"US"),
            ("XNAS" , datetime(2022, 4, 15), "Good Friday",0,"US"),
            ("XNAS" , datetime(2022, 5, 30), "Memorial Day",0,"US"),
            ("XNAS" , datetime(2022, 6, 20), "Juneteenth Holiday",0,"US"),
            ("XNAS" , datetime(2022, 7, 4), "Independence Day",0,"US"),
            ("XNAS" , datetime(2022, 9, 5), "Labor Day",0,"US"),
            ("XNAS" , datetime(2022, 11, 24), "Thanksgiving Day",0,"US"),
            ("XNAS" , datetime(2022, 12, 25), "Early Close",1,"US"),
            ("XNAS" , datetime(2022, 12, 26), "Christmas Holiday",0,"US"),

            ("XNYS" , datetime(2022, 1, 17), "Martin Luther King, Jr. Day",0,"US"),
            ("XNYS" , datetime(2022, 2, 21), "President's Day",0,"US"),
            ("XNYS" , datetime(2022, 4, 15), "Good Friday",0,"US"),
            ("XNYS" , datetime(2022, 5, 30), "Memorial Day",0,"US"),
            ("XNYS" , datetime(2022, 6, 20), "Juneteenth Holiday",0,"US"),
            ("XNYS" , datetime(2022, 7, 4), "Independence Day",0,"US"),
            ("XNYS" , datetime(2022, 9, 5), "Labor Day",0,"US"),
            ("XNYS" , datetime(2022, 11, 24), "Thanksgiving Day",0,"US"),
            ("XNYS" , datetime(2022, 12, 25), "Early Close",1,"US"),
            ("XNYS" , datetime(2022, 12, 26), "Christmas Holiday",0,"US"),

            ("ARCX" , datetime(2022, 1, 17), "Martin Luther King, Jr. Day",0,"US"),
            ("ARCX" , datetime(2022, 2, 21), "President's Day",0,"US"),
            ("ARCX" , datetime(2022, 4, 15), "Good Friday",0,"US"),
            ("ARCX" , datetime(2022, 5, 30), "Memorial Day",0,"US"),
          #  ("ARCX" , datetime(2022, 6, 20), "Juneteenth Holiday",0,"US"),
          #  ("ARCX" , datetime(2022, 7, 4), "Independence Day",0,"US"),
            ("ARCX" , datetime(2022, 9, 5), "Labor Day",0,"US"),
            ("ARCX" , datetime(2022, 11, 24), "Thanksgiving Day",1,"US"),
            ("ARCX" , datetime(2022, 12, 26), "Christmas Holiday",0,"US"),



    ]



    sql_utils.begin()

    for day in calendar:
        sql_utils.insert("marketcalendar", {
            "marketCode" : day[0] ,
            "timestamp" : day [1].timestamp(),
            "description" : day [2],
            "marketStatus" : day [3],
            "countryCode" : day [4]
        })
    sql_utils.commit()


def get_active_symbols():
    for rec in sql_utils.run_select_query("select * from symbols WHERE active =1"):
        yield rec

def get_intake_logs(symbol_id):
    for rec in sql_utils.run_select_query("select * from intakelog WHERE symbol_id = " + str(symbol_id)):
        yield rec

def insert_intake_log(symbol_id, identifier):
    record = {
        "symbol_id" : symbol_id,
        "pull_id" : str(uuid.uuid4()),
        "status" : int(AIIntakeStatus.InProgress.value), 
        "startTimeStamp": int(time.time()),
        "uniqueIdentifier": identifier
    }
    return sql_utils.insert("intakeLog", record)

def update_intake_log(id, status, source, cache_file = None, error_str = None):
    record = {
        "status" : int(status.value), 
        "endTimeStamp": int(time.time()),
        "source" : source

    }
    if (cache_file):
        record ["filePath"] = cache_file
    if (error_str):
        record ["error"] = error_str
    sql_utils.update("intakeLog", record, {"id" : id})

def ingest_stock_data (symbol, date):
    date_str = date.strftime("%Y%m%d")
    job_exists = False
    rec_id = None
    # get symbol id
    for rec in sql_utils.run_select_query("select id, active from symbols where symbol = '{}'".format(symbol)):
        rec_id =  rec[0]
    if not rec_id:
        print ("symbol {} is not found for intake task".format(symbol))
        return

    # skip the task if same pull is already in intake logs and it is successfull
    for rec in sql_utils.run_select_query("select status from intakelog where uniqueidentifier='{}' and symbol_id = {} and status = 1".format(date_str, rec_id)):
        job_exists = True

    if (job_exists):
        print ("intake task for symbol {} for identifier {} already completed".format(symbol, date_str))
        return

    if rec_id:
        sql_utils.begin()
        log_id = insert_intake_log(rec_id, date_str)
        sql_utils.commit()
        pull_stats = iex.pull_historical_data (symbol, date_str)
        if pull_stats[2]:
            update_intake_log(log_id, AIIntakeStatus.Failed, pull_stats[0] , pull_stats[1] , pull_stats[2])
        else:
            update_intake_log(log_id, AIIntakeStatus.Completed, pull_stats[0] , pull_stats[1])

def pull_symbol_data (symbol, begin_date, end_date):
    print ("    {} Intake for symbol {} starts for dates {} - {}".format(datetime.now(), symbol, begin_date, end_date))
    oneday_delta = timedelta(days = 1) 
    while begin_date <= end_date:
        ingest_stock_data (symbol, begin_date)
        begin_date = begin_date + oneday_delta
    print ("    {} Intake for symbol {} ends for dates {} - {}".format(datetime.now(), symbol, begin_date, end_date))

def analyze_data_quality (symbol, exchange, begin_date: DateTime, end_date: DateTime, aggregation:AIAggregationType):
    '''
    check if the given symbol has enough data for given range also identify empty days
    '''
    # get symbol details
    symbol_data = None
    for rec in sql_utils.run_select_query('''SELECT * from symbols WHERE symbol='{}' AND exchange = '{}'
    '''.format(symbol, exchange)):
        symbol_data = rec
    if not symbol_data:
        print ("    {} Symbol {} / {} is not found!".format(datetime.now(), symbol, exchange))
        return

    print ("    {} Checking data sufficiency for symbol {} starts for dates {} - {}".format(datetime.now(), symbol, begin_date, end_date))
    oneday_delta = timedelta(days = 1) 
    date_map = construct_date_map(begin_date, end_date)
    print (date_map)
    market_holiday_map = construct_market_holidays_map(symbol_data[2])
    print (market_holiday_map)
    q = '''
    select (timeSeriesStamp / {0} * {0}) as datetime,
                        COUNT (symbols.id), symbols.symbol
    FROM symbols, timeseries 
    WHERE symbols.id = timeseries.parent_id 
    and symbols.symbol =  '{1}' AND timeSeriesStamp >= {2} AND timeSeriesStamp <= {3}
    group by datetime , symbols.symbol
    order by datetime , symbols.symbol
    '''.format (aggregation.value, symbol, int(begin_date.timestamp()), int(end_date.timestamp()))

    # timestamps are in utc , converting to local will give -4 difference , hence we need to change tz for datetime object
    for rec in sql_utils.run_select_query(q):
        a = datetime.fromtimestamp(rec[0],tz=timezone.utc).date()
        date_map [a] = rec[1]
    for key in date_map:
        if date_map[key] < 300 and key.weekday() < 5 and not market_holiday_map.get(key, None):
            print (key, date_map[key])
    return date_map

def construct_date_map (begin, end):
    date_map = {}
    oneday_delta = timedelta(days = 1) 
    while begin <= end:
        date_map[begin.date()] = 0
        begin = begin + oneday_delta
    return date_map

def construct_market_holidays_map (market_code):
    q = '''SELECT to_timestamp(timestamp) as day, marketstatus
    FROM marketcalendar
    WHERE  marketcode = '{}'
    '''.format(market_code)
    print (q)
    holiday_map = {}
    for rec in sql_utils.run_select_query(q):
        holiday_map [rec[0].date()] = rec[1] + 1
    return holiday_map
def intake_job ():
    begin_date = date(2022, 1, 1)
    oneday_delta = timedelta(days = 1)
    end_date = datetime.now().date() - oneday_delta

    symbols = []
    for rec in sql_utils.run_select_query ("SELECT symbol FROM symbols ORDER BY random() LIMIT 100"):
        symbols.append (rec[0])
    print (symbols)
    print ("{} - Batch Intake starts for dates {} - {}".format(datetime.now(), begin_date, end_date))
    for symbol in symbols:
        pull_symbol_data (symbol, begin_date, end_date)
    print ("{} - Batch Intake ends for dates {} - {}".format(datetime.now(), begin_date, end_date))


begin_date = datetime(2022, 1, 1)
end_date = datetime.now()

analyze_data_quality("GNE", "XNYS", begin_date, end_date, AIAggregationType.Daily)
#insert_market_calendar()