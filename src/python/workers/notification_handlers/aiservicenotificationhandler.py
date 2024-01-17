from copyreg import dispatch_table
from datetime import datetime
import json
import sys
import time
import traceback
from api.aiapi import AIServiceNotificationType
from config import config
import pickle
import enum
from functools import wraps
from exceptions.exceptions import *
from utils.psqlutils import PsqlUtils
sql_utils = PsqlUtils()

default_notifications = [
    AIServiceNotificationType.Ping,
    AIServiceNotificationType.Shutdown,
    AIServiceNotificationType.Dispatch_Network,
    AIServiceNotificationType.ParkNetwork,
]


class AIServiceNotificationHandler(object):
    def __init__(self, service):
        self.service = service
        self.last_processing_time = 0
        self.acceptted_notifications  = default_notifications

    def consume(self, id, params,  notification_type:AIServiceNotificationType):
        if notification_type == AIServiceNotificationType.Dispatch_Network:
            print ("Dispatch Network Request received.")
            params = json.loads(params.tobytes())
            self.service.dispatch_network_by_id(params["network_id"], params["topic"])

        if notification_type == AIServiceNotificationType.ParkNetwork:
            print ("Park Network Request received.")
            self.service.dispatch_network_by_id(params["network_id"])
        
        if notification_type == AIServiceNotificationType.Shutdown:
            print ("Shutdownz Request received.")
            sql_utils.update("notifications", {"status": 2}, {"id" : id})
            time.sleep(3)
            sys.exit(0)


    def consume_base(self):
        '''
        Checks commands table for new commands and execute them
        status  0: new command
        status  1: pending
        status  2: sucessfully completed
        status -1: error, make sure to set error string as well
        '''
        now_time_stamp = int(datetime.now().timestamp())
        if  now_time_stamp - self.last_processing_time > config.SERVICE_DEFAULT_NOTIFICATION_CHECK_INTERVAL:
            for rec in sql_utils.run_select_query(f'''
                SELECT * from notifications 
                    WHERE targetserviceid = '{self.service.uuid}'
                    AND status = 0
                '''):
                try:
                    sql_utils.update("notifications", {"status": 1}, {"id" : rec[0]})
                    try:
                        notification_type = AIServiceNotificationType(int(rec[4]))
                    except:
                        raise NotificationTypeIsNotSupported(f"Integer value {rec[4]} is not a valid notification (service {self.service.uuid})")
                    if not notification_type in self.acceptted_notifications:
                        raise NotificationTypeIsNotSupported(f"Integer value {rec[4]} is not supported by service {self.service.uuid}")
                    params = rec[7]

                    self.consume(rec[0], params, notification_type)
                    sql_utils.update("notifications", {"status": 2}, {"id" : rec[0]})

                except Exception as e: # work on python 3.x
                    error_str = traceback.format_exc()
                    print (str(e))
                    sql_utils.update("notifications", {"error" : error_str, "status": -1}, {"id" : rec[0]})
            self.last_processing_time =  now_time_stamp          

