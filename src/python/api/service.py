from marshal import dumps
from time import sleep
from api.types import AIServiceNotificationType
from utils.aiutils import validate
from core.aibase import *
from exceptions.exceptions import *
from functools import wraps
import uuid


class AIServiceSdk(object):
    def __init__(self, api) -> None:
        if not api:
            from api.aiapi import AIApi 
            api = AIApi()

        self.api = api
        self.sql_utils = api.sql_utils

    def getServiceSummary(self, service_class=None, include_networks=False):
        '''
            ## Description:
            Returns an array service summary from database

            ## service_class<string>: Type of services to list. e.g AITrainer
            ## include_networks: if True returns network list too.
            ```

            ## Returns:
            List of services.<br>
            If includeNetworks is set to true, response object also returns an array of networks
        '''
        service_list = []
        query = "SELECT * FROM service"
        if (service_class):
            query = query + f" WHERE classname = '{service_class}'"

        for rec in (self.sql_utils.run_select_query(query)):
            data = pickle.loads(rec[8])
            val = {
                "id": rec[0],
                "service_id": rec[3],
                "service_class": rec[4],
                "network_count": len(data['networks'])
            }
            if include_networks:
                networks = []
                for n in data['networks']:
                    networks.append(n["network_id"])

                val["networks"] = networks

            service_list.append(val)

        return service_list
    def localGetServiceList(self):
        '''
            returns the list of running services locally to where api module is loaded.
            Note that this is a base function and works with docker, not the db
            If there is a mismatch between service status in db, call this function for the correct status by sending a notification to local nodemanager
        '''
        containers = self.api.docker_client.containers.list()
        service_list = []

        for c in containers:
            for t in c.image.attrs['RepoTags']:
                tag_tokens = t.split(":")
                if not (len(tag_tokens)) == 2:  # valid services should have a name and version
                    continue
                if not tag_tokens[0] in self.api.task_defs:
                    continue
                service_list.append(t)
        return service_list

    def localSpinService(self, taskName, version=None):
        '''
            Starts a local docker container with given taskName and version
            If version is not provided , an image with "latest" is looked for
            Returns container object if successfull
        '''
        if not version:
            version = "latest"
        # Check if it is a valid task class name
        if not taskName in self.api.task_defs:
            raise ServiceImageIsNotFound(
                f"Service {taskName}:{version} is not registered in task_config.json.")
        # Check if docker image is available for taskName:version
        for image in self.api.docker_client.images.list():
            for image_text in image.tags:
                if image_text == f"{taskName}:{version}":
                    service_id = str(uuid.uuid4())
                    c = self.api.docker_client.containers.run(
                        image,
                        environment=[f"SERVICE_ID={service_id}"],
                        network="boltzman",
                        labels={"service_id": service_id},
                        init=True,
                        volumes={config.MODEL_FILES_LOCATION: {
                            'bind': config.MODEL_FILES_LOCATION_IN_DOCKER, 'mode': 'rw'}},
                        name=service_id)
                    return c

        raise ServiceImageIsNotFound(
            f"Service {taskName}:{version} does not exist.")

    def localStopService(self, service_id):
        '''
            Stops the service container forcefully via docker api.
            DO NOT USE IT UNLESS YOU REALLY NEED TO USE IT
            Use it via nodemanager
        '''
        containers = self.api.docker_client.containers.list()

        for c in containers:
            if "service_id" in c.labels:
                if c.labels["service_id"] == service_id:
                    print(f"stopping container : {service_id}")
                    c.stop()
                    return
        raise ServiceContainerNotFound(
            f"Service container with id {service_id} does not exist.")

    def requestStopService(self, source, service_id):
        '''
            Asks the given service container to stop gracefully.
            The result of this call can be harvested from service_notifications by querying its status periodically
        '''
        self.api.sendNotification(source, service_id, AIServiceNotificationType.Shutdown, {
                               "service_id": service_id})

    def listServiceClasses(self):
        '''
            ## Description:
            Returns the service class decriptions

            ## Returns:
            an object wrapping service class definitions
        '''
        return self.api.task_defs

    def update_service_status(self, data):
        '''
            Update service status in service table
        '''
        SERVICE_TABLE = "service"

        self.sql_utils.begin()
        deseri_obj = pickle.dumps(data)
        record = {"timestamp": 0,
                  "serviceId": data["service_id"],
                  "className": data["class_name"],
                  "status": data["status"],
                  "upSince": data["up_since"],
                  "networkCount": data["number_of_networks"],
                  "body": deseri_obj}
        
        if not self.sql_utils.check_if_record_exists(SERVICE_TABLE, data["service_id"], "serviceid"):
            self.record_id = self.sql_utils.insert(SERVICE_TABLE, record)
        else:
            self.sql_utils.update(SERVICE_TABLE, record, {
                             "serviceId": data["service_id"]})

        self.sql_utils.commit()

if __name__ == "__main__":
    m = AIServiceSdk(None)
    m.localSpinService("trainer", "1.0.2")
