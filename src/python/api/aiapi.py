from api.account import AIAccountSdk
from api.data import AIDataSdk
from api.infra import AIinfraSdk
from api.network import AINetworkSdk
from api.project import AIProjectSdk
from api.service import AIServiceSdk
from api.time_series import AITimeSeriesSdk
from api.types import AIServiceNotificationType
from utils.aiutils import make_sure
import json
import docker
from utils.psqlutils import PsqlUtils
from exceptions.exceptions import *
from config import config
import uuid
import datetime

class AIApi(object):
    def __init__(self):
        self.class_name = "AIApi"
        # load service class descriptions
        f = open("./config/task_config.json")
        self.task_defs = json.load(f)['tasks']
        f.close()
        self.resource_class_map = None
        self.sql_utils = PsqlUtils()
        self.docker_client = docker.from_env()

        self._sdk_references = [
            self,
            AIinfraSdk(self),
            AIServiceSdk(self),
            AIAccountSdk(self),
            AIProjectSdk(self),
            AINetworkSdk(self),
            AIDataSdk(self),
            AITimeSeriesSdk(self)
        ]

    def __del__(self):
        print("Closing API Connection")

    def add_sdk_plugin (self, plugin_obj):
        self._sdk_references.append(plugin_obj)

    def get_plugins (self):
        return self._sdk_references

    def get_endpoint (self, function_name):
        print ("getting endpoint", function_name)
        print (self.get_plugins())
        api_func = None
        for sdk in self.get_plugins():
            try:
                api_func = getattr(sdk, function_name)
                print (api_func)
                if not callable(api_func):
                    continue
            except AttributeError as ex:
                print (ex)
                continue
        return api_func

    def login (self, user, password):
        return {
            "user" : "Arif Bilgin",
            "auth_token" : "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        }

    def _register_application_data(self, data, status, description = ""):

        return self.sql_utils.insert ("application", {
            "data": json.dumps(data),
            "uniqueid": str(uuid.uuid4()),
            "status" : status,
            "description" : description
        })

    def _get_application_data(self):
        app_data = self.sql_utils.return_first_if_exists("application", "3d7d6607-fd97-4da8-8c3c-3de3264506c0", "uniqueid")
        make_sure(app_data, "Failed to load application data")
        return app_data

    def _get_account_id(self):
        return "d890367e-96de-11ed-a8fc-0242ac120002"


    def purgeServiceCommands(self, service_id):
        '''
            removes all commands associated for given service_id
            It should only be used if service crashed to cleanup
            zombie commands have no affect on anything except cluttering the database
        '''
        self.sql_utils.begin()
        self.sql_utils.update("commands", {"status": -1}, {"serviceId": service_id})
        self.sql_utils.commit()

    def localFixZombies(self):
        container_names = []
        for container in self.docker_client.containers.list():
            container_names.append(container.name)
        # Clean up networks
        for rec in (self.sql_utils.run_select_query(
            '''
            SELECT * FROM network;
            '''
        )):
            current_location = rec[3]
            if not current_location in container_names and not current_location in config.KAFKA_TOPICS.keys():  # zombie
                self.network_sdk._dispatch_network_with_id(
                    rec[0], config.KAFKA_TOPICS["TOPIC_MODEL_NEEDS_TRAINING"])
        # Clean up networks
        for rec in (self.sql_utils.run_select_query(
            '''
            SELECT * FROM service;
            '''
        )):
            service_id = rec[3]
            if not service_id in container_names:
                self.sql_utils.delete_record("service", rec[0])

    def sendNotification(self, source_service_id, target_service_id, notification_type: AIServiceNotificationType, params):
        '''
        CREATE TABLE commands (
        id SERIAL PRIMARY KEY,
        serviceId text, -- target service for the command
        timestamp int,
        command text , -- command to send to the service
        status int DEFAULT 0, -- status of the command 0: initial 1:pending 2: executed 3:failed
        error text, -- error message returned from service if status is 3 (failed)
        body  BYTEA -- reserved for extra parameters
        );
        '''
        self.sql_utils.begin()
        self.sql_utils.insert('notifications', {
            "sourceServiceId": source_service_id,
            "targetServiceId": target_service_id,
            "timestamp": int(datetime.datetime.now().timestamp()),
            "notification": notification_type.value,
            "status": 0,
            "body": json.dumps(params)
        })
        self.sql_utils.commit()
