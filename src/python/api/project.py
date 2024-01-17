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


class AIProjectSdk(object):
    def __init__(self, api) -> None:
        self.api = api
        self.sql_utils = api.sql_utils



    def create_new_project(self, name, description, data):
        unique_id = str(uuid.uuid4())
        account_id = self.api._get_account_id()

        self.sql_utils.insert("project", {
            "projectId": unique_id,
            "accountId": account_id,
            "name" : name,
            "description" : description,
            "data" : json.dumps(data)
        })
        return unique_id

    def delete_project(self, project_id):
        self.sql_utils.delete_record("project" , project_id, index_field = "projectid")
        return {
            "deleted_project" : project_id
        }

    def get_project_list(self):
        projects_to_return = []
        account_id = self.api._get_account_id()
        for rec in self.sql_utils.select ("project",{
            "accountid" : account_id
        }):
            projects_to_return.append({
                "projectId": rec[1],
                "name" : rec[3],
                "description" : rec[4],
                "data" : json.loads (rec[5].tobytes())
        })
        return projects_to_return

    def update_project(self, unique_id, name, description, data):
        self.sql_utils.update("project", {
            "name" : name,
            "description" : description,
            "data" : json.dumps(data)
        },{
            "projectId": unique_id,
        })

