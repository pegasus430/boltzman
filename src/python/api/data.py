import os
import re
import traceback
import jwt
from marshal import dumps
from sqlite3 import Timestamp
import string
from time import sleep
from utils.aiutils import make_sure, validate
import json
from core.aibase import *
from exceptions.exceptions import *
from functools import wraps
import uuid
import datetime
from utils.loggerfactory import logger


class AIDataSdk(object):
    def __init__(self, api) -> None:
        if not api:
            from api.aiapi import AIApi 
            api = AIApi()
        self.api = api
        self.sql_utils = api.sql_utils

    def _get_data_categories(self):
        rec = self.api._get_application_data()
        app_data = None
        try:
            app_data = json.loads(rec[2].tobytes())
            #print (app_data)

        except Exception as ex:
            logger().error(traceback.format_exc())
            make_sure(False, "Invalid JSON Format.")
        make_sure (app_data.get("data_category_tree", None), "No Data Category tree found.")
        return app_data["data_category_tree"]

    def _get_app_data(self):
        rec = self.api._get_application_data()
        app_data = None
        try:
            app_data = json.loads(rec[2].tobytes())
            #print (app_data)

        except Exception as ex:
            logger().error(traceback.format_exc())
            make_sure(False, "Invalid JSON Format.")
        make_sure (app_data.get("data_category_tree", None), "No Data Category tree found.")
        return app_data


    def recursive_lookup(k, d):
        if k in d:
            return d[k]
        for v in d.values():
            if isinstance(v, dict):
                return AIDataSdk.recursive_lookup(k, v)
        return None

    def _find_value_recursively(self, obj, key):
        """ Locate a key in given dict recursively and returns the value.
            If key is not found returns None

        Args:
            key (string): key value to lookup
            obj (dict): dict to search
        """
        return AIDataSdk.recursive_lookup(key, obj)
        if key in obj:
            return obj[key]
        for k, v in obj.items():
            if isinstance(v, dict):
                item = self._find_value_recursively(v, key)
                if item is not None:
                    return item
            elif isinstance(v, list):
                for list_item in v:
                    item = self._find_value_recursively(list_item, key)
                    if item is not None:
                        return item
            return None

    def increment_time_series_count(self, catalogId):
        data_categories = self._get_app_data()
        print (data_categories)
        print (catalogId)
        catalog = self._find_value_recursively(data_categories, catalogId)
        print (catalog)
        validate(catalog, f"{catalogId} not found in data catalog.")
        catalog["time_series_count"] = 1 if not catalog.get ("time_series_count", None) else catalog["time_series_count"] + 1
        self.sql_utils.update ("application", {
            "data": json.dumps(data_categories)
        },{ "uniqueid" : "3d7d6607-fd97-4da8-8c3c-3de3264506c0"})  

    def reset_catalog(self):
        script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
        rel_path = "data/initial_data_catalog.json"
        abs_file_path = os.path.join(script_dir, rel_path)        
        f = open(abs_file_path)
        data = json.load(f)
        print (data)
        self.sql_utils.update ("application", {
            "data": json.dumps(data)
        },{ "uniqueid" : "3d7d6607-fd97-4da8-8c3c-3de3264506c0"})      


    def get_data_catalog(self):
        return self._get_data_categories()

    def delete_data_category(self, unique_category_id):
        pass
     
    def register_new_data_category(self, name: string,  description: string, parent_category_id: string = None, status: int = 1):
        try:
            data_categories = self._get_data_categories()
            unique_id = str(uuid.uuid4())
            app_data = self.api._get_application_data()

            new_dict = {
                "name": name,
                "description": description,
            }
            
            if not parent_category_id:  # register to root
                data_categories[unique_id] = new_dict

            else:
                parent_obj = self._find_value_recursively(
                    data_categories, parent_category_id)
                validate(parent_obj, "Parent category does not exist")

                # check if name is unique
                for key, value in parent_obj.items():
                    if isinstance(value, dict):
                        existing_name = value.get("name", None)
                        if existing_name:
                            validate ( not (existing_name.lower() == name.lower()), f"category :{name} already exists")


                parent_obj[unique_id] = new_dict
            
            app_data_json = json.loads(app_data[2].tobytes())
            app_data_json["data_category_tree"] = data_categories

            self.sql_utils.update("application", {
                "data": json.dumps(app_data_json)
            }, {"uniqueid": "3d7d6607-fd97-4da8-8c3c-3de3264506c0"})

            return unique_id
        except Exception as ex:
            logger().error (ex)
            raise ex


if __name__ == "__main__":
    m = AIDataSdk(None)
