import os
from sqlite3 import Timestamp
import string
from time import sleep
from utils.aiutils import make_sure, validate
import json
from core.aibase import *
from exceptions.exceptions import *
from api.data import AIDataSdk
from functools import wraps
import uuid
import datetime
from utils.loggerfactory import logger
from core.aidataport import AIDataport

class AITimeSeriesSdk(object):
    def __init__(self, api) -> None:
        self.api = api
        self.sql_utils = api.sql_utils
        self.data_sdk = AIDataSdk(api)

    def register_new_time_series(self, name: string, parentCategoryId: string, description: string,  data: dict, status: int = 1):
        """Creates a new timeseries type
            name (string): name of the time series.
            parentCategoryId (string): parent category uuid from table application key:data_categories value: dict
            description (string): description of the time series
            data (dict): extra data in dict format
            status (int, optional): _description_. Defaults to 1.
        """
        # get data category tree
        catalog_node = self.api.get_endpoint("_find_value_recursively") (
                        self.api.get_endpoint("_get_data_categories")(), 
                        parentCategoryId)
        validate(catalog_node, f"Data Category {parentCategoryId} is not found.")
        unique_id = str(uuid.uuid4())
        self.sql_utils.insert("timeseries_definition",{
            "name" : name,
            "description" : description,
            "uniqueid" : unique_id,
            "dataCatalogId" : parentCategoryId,
            "data" : json.dumps(data),
            "status" : status
        })
        self.data_sdk.increment_time_series_count(parentCategoryId)


        return unique_id
    
    def set_time_series_active(self,time_series_id, active):
        """Activates / Deactivates a time series. 
        Note that networks already using a deactivated time series will not be affected.

        Args:
            time_series_id (string): unique time series def id
            active (Boolean): True / False , active or inactive
        """
        time_series_rec = self.sql_utils.return_single_if_exists ("timeseries_definition", time_series_id, field_name = "uniqueid")
        validate (time_series_rec, f"time series : {time_series_id} does not exist")

        self.sql_utils.update ("timeseries_definition", {
            "status" : 1 if active else 0
        }, {"uniqueid" : time_series_id})

        return time_series_id

    def subscribe_project_to_time_series(self, project_id, time_series_id, activate = False):
        """Subscribes a project to a time serious (data source).
            After subscriptions, project networks may start pulling data for time series
            if the status of the time_series is 1, otherwise it is ignored by evolution engine

        Args:
            project_id (_type_): _description_
            time_series_id (_type_): _description_
            activate: if True time series becomes active immediately otherwise it is not used
        """
        validate(
            self.sql_utils.check_if_record_exists("project", project_id, field_name = "projectId"),
            f"Project id: {project_id} does not exist")

        validate(
            self.sql_utils.check_if_record_exists("timeseries_definition", time_series_id, field_name = "uniqueid"),
            f"Project id: {project_id} does not exist")
        
        unique_id = str(uuid.uuid4())

        self.sql_utils.insert("timeseries_project", {
                "uniqueid" : unique_id,
                "projectid" : project_id,
                "timeseriesdefinitionid" : time_series_id ,
                "status":1 if activate else 0
            })
        return unique_id

    def get_project_time_series (self, project_id):
        """ Returns time series that projects subscribes

        Args:
            project_id (str): unique project id

        Returns:
            Array of time series in format:
            {
                "name":<time series name>,
                "description" : <time series description>,
                "earliest_date" : time stamp of the first data point,
                "total_records" :< number of records in as raw data>,
                "catalog_id" : <unique catalog id>,
                "catalog_name" : <catalog name>
            }

        """
    
    def get_catalog_time_series (self, datacatalogId,offset = None):
        """_summary_

        Args:
            datalogId (_type_): _description_
        """
        number_of_recs = self.sql_utils.count_records("timeseries_definition", {
            "datacatalogid": datacatalogId
        })

        if number_of_recs == 0:
            return []
        print (number_of_recs)
        query = f'''
        SELECT * FROM timeseries_definition 
        WHERE datacatalogid='{datacatalogId}' 
        ORDER BY name
        LIMIT 30
        '''
        if offset:
            query = query + f" OFFSET {offset}"
        time_series_to_return = []

        for rec in (self.sql_utils.run_select_query(query)):
            time_series_to_return.append({
                "name": rec[1],
                "description": rec[2],
                "granularity": "15 minutes",
                "category" : "Unspecified"
            })

        return {"offset" : offset,
                "total_records" : number_of_recs,
                "in_this_batch" : len (time_series_to_return),
                "data" : time_series_to_return}

    def sample_time_series(self, name):
        sample_data = []
        for rec in self.sql_utils.select("timeseries", {"timeseriesname" : name}, limit = 40):
            sample_data.append({
                "name" : rec[2],
                "timestamp" : rec[3],
                "value" : rec[5]
            })
        return sample_data



if __name__ == "__main__":
    from api.aiapi import AIApi

    m = AITimeSeriesSdk(AIApi())

    script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
    rel_path = "data/nasdaq.json"
    abs_file_path = os.path.join(script_dir, rel_path)        
    f = open(abs_file_path)
    data = json.load(f)
    for stock in data:
        m.register_new_time_series (
            stock["Symbol"], "a4534242-a75c-11ed-afa1-0242ac120001",
            stock["Company Name"],{
                        "Company Name": "iShares MSCI All Country Asia Information Technology Index Fund",
                        "Financial Status": stock["Financial Status"],
                        "Market Category": stock["Market Category"],
                        "Round Lot Size": stock["Round Lot Size"],
                        "Security Name": stock["Security Name"]
            }
        )


