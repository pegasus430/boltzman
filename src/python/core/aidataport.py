import sys
from lib2to3.pygram import Symbols
import string
from sys import intern
from xml.dom.minidom import AttributeList
from xmlrpc.client import Boolean

from pytest import mark
from core.aibase import AIAggregationType, AIBase
from exceptions.exceptions import *
from config import config
import datetime
import math
import utils.aiutils as aiutils
from utils.psqlutils import PsqlUtils
from utils.loggerfactory import logger


sql_utils = PsqlUtils()

class AIDataport (AIBase):
    def __init__ (self, symbol, size, aggregation_type, is_input_port = True):
        AIBase.__init__(self, name = "AIDataport", class_name = "AIDataport", record_id = -1)
        if not symbol in self.symbols_map.keys():
            raise SymbolNotFound(symbol)
        self.params["symbol"] = symbol
        self.params["size"] = size
        self.params["aggregation_type"] = aggregation_type

        self.params["value_magnifier"] = 100.00
        
        self.is_input_port = is_input_port
        self._last_query = "" #for debugging puporses we keep the last run query
        self.temp_flag = None
    
    def __eq__(self, other):
        if (super().__eq__(other) and
            self.params["symbol"] == other.params["symbol"] and
            self.params["size"] == other.params["size"] and
            self.params["aggregation_type"] == other.params["aggregation_type"] and 
            self.params["value_magnifier"] == other.params["value_magnifier"] and
            self.is_input_port == other.is_input_port):
            return True
        return False
    def __str__(self):
        return (f'Symbol        : {self.params["symbol"]}\n'
            f'Aggregation : [ {self.params["aggregation_type"]}]\n')

    def set_symbol (self, symbol):
        self.params["symbol"] = symbol

    def earliest_time_stamp (self):
        '''
            calculates the earliest time stamp for symbol aggregation and dp size combination tha twould succesfully return 
            enough records for training
        '''
        if not self.is_input_port:
            raise DataportInputOutputTypeMismatch("earliest_time_stamp can not be appied to output dataports")

        query ='''SELECT AVG (timeSeriesCurrentValue) as value, 
                        timeSeriesClass as class, 
                        timeSeriesName as name, 
                        (timeSeriesStamp / {0} * {0}) as timeStamp 

            FROM  timeSeries 
            WHERE timeSeriesStamp > 0 
            AND timeSeriesName = '{1}' 
            GROUP BY timeSeriesName , timeSeriesClass, timeStamp \
            Order By timeStamp \
            LIMIT {2}'''.format(self.params["aggregation_type"].value,
                                    self.params["symbol"],
                                    self.params["size"] + 1)                                    

        rv = None
        count = 0
        for rec in sql_utils.run_select_query(query):
            rv = rec[3]
            count += 1
        return rv
        
    def latest_time_stamp (self):
        '''
            calculates the latest time stamp for symbol aggregation and dp size combination that twould succesfully return 
            enough records for training output tensor
        '''
        sort_type = "DESC"
        if self.is_input_port:
            raise DataportInputOutputTypeMismatch("latest_time_stamp can not be appied to input dataports")
        query ='''SELECT AVG (timeSeriesCurrentValue) as value, 
                        timeSeriesClass as class, 
                        timeSeriesName as name, 
                        (timeSeriesStamp / {0} * {0}) as timeStamp 

            FROM  timeSeries 
            WHERE timeSeriesStamp > 0 
            AND timeSeriesName = '{1}' 
            GROUP BY timeSeriesName , timeSeriesClass, timeStamp \
            Order By timeStamp DESC\
            LIMIT {2}'''.format(self.params["aggregation_type"].value,
                                    self.params["symbol"],
                                    self.params["size"])                                    
        rv = None
        for rec in sql_utils.run_select_query(query):
            rv = rec[3]
        return rv


    def predicton_matured_time (self, prediction_time) -> int:
        """returns a future time_stamp for given prediction time. returned time_stamp guarantees to return enough data points
            to satisfy prediction check

        Args:
            prediction_time (int): prediction time stamp to be checked

        Returns:
            int: rreturns the earliest time stamp in the future that would return enough data points
            for eg. if dataport aggregation is hourly and and size is 5 for predictions made at 13:00 would return 18:00
            to generate 5 records, before 18:00 there would be not enough data to check the prediction result
        """
        cursor = self.time_stamp_bucket(prediction_time)
        ts_bucket = cursor
        count = 0
        market_code = self.symbols_map[self.params["symbol"]][4]
        while count < self.params["size"]:
            logger().info (f'Prediction fast forward [{count}] cursor time: {datetime.datetime.fromtimestamp(cursor)}')
            cursor = aiutils.fast_forward_time(cursor, market_code)
            count += 1
            cursor += self.params["aggregation_type"].value
        rv = self.calc_time_stamp_bucket(self.params["aggregation_type"], cursor)
        logger().info (f'Prediction bucket time: {datetime.datetime.fromtimestamp(ts_bucket)} prediction time: {datetime.datetime.fromtimestamp(prediction_time)} mature time: {datetime.datetime.fromtimestamp(rv)}')
        return rv


    def _construct_custom_query (self, time_stamp, bucket_size_in_seconds) -> string:
        '''
            construct time series query for given buxket size (in seconds)
            values are aggragates as average
        '''
        if not self.is_input_port:
            time_stamp += self.params["aggregation_type"].value
        greater_or_less = "<="
        sort_type = "DESC"
        if not self.is_input_port:
            greater_or_less = ">="
            sort_type = ""
        query ='''SELECT AVG (timeSeriesCurrentValue) as value, 
                        timeSeriesClass as class, 
                        timeSeriesName as name, 
                        (timeSeriesStamp / {0} * {0}) as timeStamp 

            FROM  timeSeries 
            WHERE timeSeriesStamp > 0 
            AND timeSeriesStamp {1} {2} 
            AND timeSeriesName = '{3}' 

            GROUP BY timeSeriesName , timeSeriesClass, timeStamp \
            Order By timeStamp {4} \
            LIMIT {5}'''.format(bucket_size_in_seconds, greater_or_less, time_stamp, 
                                    self.params["symbol"],
                                    sort_type, self.params["size"])
        if self.is_input_port:
            query = "SELECT * FROM ({}) as sq ORDER BY timeStamp".format(query)
        return query

    @classmethod
    def calc_time_stamp_bucket(cls, aggregation:AIAggregationType, ts:int ):
        return math.floor (ts / aggregation.value ) * aggregation.value

    def time_stamp_bucket (self, ts) -> int:
        """Calculates timestamp bucket beginning time for given time stamp

        Args:
            ts (timestamp): time that needs to be aligned to the bucket

        Returns:
            returns the beginning of time bucket where ts fits in
        """
        rv = math.floor (ts / self.params["aggregation_type"].value ) * self.params["aggregation_type"].value
        return AIDataport.calc_time_stamp_bucket(self.params["aggregation_type"], ts)

    def _default_normalizer(self, rec, last_rec):
        '''
            Each record that is pulled from time series is first sent in this function 
            where option values are converted to percentages (0 - 1.0) by using last rec
            There is a risk that perc values might be too small, e.g 5% would be 0.05 
            function magnifies the values by a dp parameter value_magnifier.
        '''
        if not self.temp_flag: # remove once you are done with this debug flag
            self.temp_flag = True

        rec_list = list(rec)
        magnifier = self.params["value_magnifier"] if self.params["value_magnifier"] else 1.00
        if (last_rec):
            rec_list[0] = (rec_list[0] - last_rec[0]) / last_rec[0] * magnifier
        else:
            rec_list[0] = 0.00
        return tuple(rec_list)


    def pull_data(self, time_stamp, normalizer_function = None):
        query = self._construct_custom_query(time_stamp, self.params["aggregation_type"].value)
        self._last_query = query
        record_count = 0
        last_record = None
        for rec in sql_utils.run_select_query(query):
            rv = None
            if (normalizer_function):
                rv = (normalizer_function (rec, last_record))
            else:
                rv =  self._default_normalizer (rec, last_record)
                
            record_count += 1
            last_record = rec
            yield rv

        if (record_count != self.params["size"]):
            logger().info (f'Dataport record count mismatch. Expected: {self.params["size"]},  pulled: {record_count}')
            logger().info (f'query :\n{self._last_query}')
            

    def is_active (self, time_stamp):
        """checks if the dataport is able generate fresh data. e.g stock symbols for nasdaq after 4pm are closed
        and pulling data for after hours would repeteadly return the same data set until next day 9:30
        Args:
            time_stamp (int): unix time stamp
        returns (Boolean) : true if stock symbol is within market open hours false if market is closed
            Note that crypto assets never become inactive 

        """        