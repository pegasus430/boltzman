from copyreg import dispatch_table
from datetime import datetime
import json
import sys
import time
import traceback
from api.aiapi import AIApi, AIServiceNotificationType
from config import config
import pickle
import enum
from functools import wraps
from exceptions.exceptions import *
from utils.psqlutils import PsqlUtils
from workers.notification_handlers.aiservicenotificationhandler import AIServiceNotificationHandler
sql_utils = PsqlUtils()

notifications = [
    AIServiceNotificationType.Ping,
    AIServiceNotificationType.Shutdown,
    AIServiceNotificationType.SpinService,
    AIServiceNotificationType.GetLocalServiceList
]
class NodeManagerNotificationHandler(AIServiceNotificationHandler):
    def __init__(self, service):
        AIServiceNotificationHandler.__init__(self, service)
        self.acceptted_notifications  = notifications
        self.api = AIApi() # not sure if i need it this way or import the api module
        self.api = AIApi()
    def consume(self, id, params,  notification_type:AIServiceNotificationType):
        if notification_type == AIServiceNotificationType.SpinService:
            print ("SpinService Network Request received.")
            return self.api.localSpinService(params["task_name"], params["version"])

        if notification_type == AIServiceNotificationType.GetLocalServiceList:
            print ("GetLocalServiceList Network Request received.")
            return self.api.localGetServiceList()

