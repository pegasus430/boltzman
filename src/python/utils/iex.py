import requests
import datetime
import json
import config.config as config
from os.path import exists
from utils.loggerfactory import logger 
import psycopg2
import os
from exceptions.exceptions import *
from utils.psqlutils import PsqlUtils 
sql_utils = PsqlUtils()

class IEX:
    def __init__ (self, api_url = config.API_URL, token = config.TOKEN):
        self.api_url = api_url
        self.token = token

    def _get_symbol_id (self, symbol):
        l = list(sql_utils.run_select_query("SELECT ID from symbols WHERE symbol = '{}'".format(symbol)))
        if not l:
            raise IndexError("Symbol {} not registered".format(symbol))
        return l[0][0]

    def pull_real_time_data (self, symbol):
        parentID = self._get_symbol_id(symbol)
        sql_utils.begin()
        data = self._pull_iex_real_time_data (symbol)

        record = {
            "parent_id" : parentID,
            "timeSeriesName" : symbol,
            "timeSeriesStamp" : int(data["latestUpdate"] / 1000),
            "timeSeriesClass" : 0,
            "timeSeriesCurrentValue" : data["latestPrice"]
        }
        try:
            sql_utils.insert("timeSeries", record)
            self._cache_real_time_data_chunk(symbol, data)
        except psycopg2.IntegrityError:
            logger().warning("symbol {} for {} already exists.".format(symbol, data["iexLastUpdated"])) 
        sql_utils.commit()

    def construct_cache_file_name (self, symbol, date_str):
        directory = config.CACHE_ROOT_DIRECTORY + "{}/{}/{}/".format(symbol, date_str[0:4], date_str[4:6])
        if (not exists(directory)):
            os.makedirs(directory)
        return "{}{}.{}.hist".format(directory, symbol, date_str)



    def pull_historical_data(self, symbol, date, use_cached = True):
        '''
            symbol: any stock symbol e.g FB , GOOGL, AAL
            date: date as string in format (YYYYMMDD)
            returns a tuple of data source and the cached file, if data is pulled from cahced they d both be same
        '''
        parentID = self._get_symbol_id(symbol)

        sql_utils.begin()
        file_name = self.construct_cache_file_name(symbol, date)
        data_iterator = None
        source = "remote"
        if use_cached and exists(file_name):
            data_iterator = self._pull_cached_historical_data (symbol, date)
            source = file_name
        else:
            data_iterator = self._pull_iex_historical_data(symbol , date)
            use_cached = False

        count = 0
        for data in data_iterator:
            if data ["average"] and data ["average"] >=0:
                count +=1
                dateTokens = data["date"].split("-")
                timeTokens = data ["minute"].split(":")
                time_stamp = datetime.datetime(int(dateTokens[0]), int(dateTokens[1]), int(dateTokens[2]), int(timeTokens[0]), int(timeTokens[1])).timestamp()
                record = {
                    "parent_id" : parentID,
                    "timeseriesname" : symbol,
                    "timeseriesstamp" : time_stamp,
                    "timeseriesclass" : 0,
                    "timeseriescurrentValue" : data["average"]
                }
                try:
                    sql_utils.insert("timeseries", record)
                    if not use_cached:
                        self._cache_historical_data_chunk(symbol, data, date)
                except psycopg2.IntegrityError:
                    logger().warning ("symbol {} for {} already exists.".format(symbol, data["date"]))
                    sql_utils.rollback()
                    return (source, file_name, "Tick Point Already exists")
        if count == 0:
            sql_utils.rollback()
            return (source, file_name, "No Data Available for symbol {} on {}".format(symbol, date))
        sql_utils.commit()
        return (source , file_name, None)

    def _cache_real_time_data_chunk (self, symbol, data):
        date_today = datetime.datetime.now()
        file_name = "./cached_data/{}.{}.real".format(symbol, date_today.strftime("%Y%m%d"))
        file = open(file_name, "a")  # append mode
        file.write(json.dumps(data))
        file.write("\n")
        file.close()
        
    def _cache_historical_data_chunk (self, symbol, data, dateStr):
        file_name = self.construct_cache_file_name(symbol, dateStr)
        file = open(file_name, "a")  # append mode
        file.write(json.dumps(data))
        file.write("\n")
        file.close()

    def _pull_iex_historical_data (self, symbol , date):
        url = self.api_url + "stable/stock/{}/chart/date/{}?token={}".format(symbol, date, self.token)
        if config.DISABLE_IEX_CALLS:
            logger().info("IEX historical data pull for symbol {} for date {} is aborted due to DISABLE_IEX_CALLS setting".format(
                symbol, date
            ))
            return
        resp = requests.get(url)
        if resp.status_code != 200:
            raise ApiError('GET /tasks/ {}'.format(resp.status_code))
        data = resp.json()
        if data:
            for chunk in data:
                yield chunk
        else:
            logger().warning("No data for {} on date {}". format(symbol, date))

    def _pull_cached_historical_data (self, symbol , dateStr):
        file_name = self.construct_cache_file_name(symbol, dateStr)
        logger().info ("Pulling historical data for {} from {}".format(symbol, file_name))
        file = open(file_name , 'r')
        count = 0
        while True:
            count += 1
            line = file.readline()
            if not line:
                break
            yield json.loads(line)                
        file.close()

    def _pull_iex_real_time_data (self, symbol):
        url = self.api_url + "stable/stock/{}/quote?token={}".format(symbol, self.token)
        resp = requests.get(url)
        if resp.status_code != 200:
            raise ApiError('GET /tasks/ {}'.format(resp.status_code))
        data = resp.json()

        if data:
            return data
        else:
            raise RuntimeError("No real time data for {}". format(symbol))
    def pull_iex_symbols (self):
        logger().info("Pulling symbol list");
        url = self.api_url + "beta/ref-data/symbols?token={}".format(self.token)
        resp = requests.get(url)
        if resp.status_code != 200:
            raise ApiError('GET /tasks/ {}'.format(resp.status_code))
        data = resp.json()
        if data:
            for chunk in data:
                yield chunk
        else:
            raise RuntimeError("No data returned from iex symbol reference call");
    
if __name__ == "__main__":
    iex = IEX()
    iex.pull_historical_data ("FB", "20220701")