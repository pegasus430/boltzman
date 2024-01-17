from marshal import dumps
from sqlite3 import Timestamp
import string
from time import sleep
from utils.aiutils import validate
import json
from core.aibase import *
from exceptions.exceptions import *
from functools import wraps
import uuid
import datetime


class AIinfraSdk(object):
    def __init__(self, api) -> None:
        self.api = api
        self.sql_utils = api.sql_utils


    def _resource_class_map(self, invalidate_cache=False):
        '''
            construct a cache obj for resource tree.
        '''
        if self.resource_class_map and not invalidate_cache:
            return self.resource_class_map

        m = {}

        for class_rec in (self.sql_utils.run_select_query(
            '''
            SELECT * FROM resourceClass; 
            '''
        )):

            m[class_rec[1]] = {
                'classId': class_rec[1],
                'className': class_rec[2],
                'classDescription': class_rec[3],
                'data': class_rec[4],
                'sub_classes': {}
            }

            for rec in (self.sql_utils.run_select_query(
                f'''
                SELECT * FROM resourceSubClass WHERE classId ='{class_rec[1]}'; 
                '''
            )):
                m[class_rec[1]]['sub_classes'][rec[2]] = {
                    'classId': class_rec[1],
                    'subClassId': rec[2],
                    'subClassName': rec[3],
                    'subClassDescription': rec[4],
                    'data': json.loads(rec[5].tobytes())
                }
        return m

    def register_cluster(self, clusterType: int, data):
        cluster_id = str(uuid.uuid4())
        record = {
            'clusterId': cluster_id,
            'clusterType': clusterType,
            'registryTime': int(datetime.datetime.now().timestamp()),
            'rootAccountId': '001',
            'status': 0,
            'data': json.dumps(data)
        }
        record['clusterId'] = str(uuid.uuid4())
        self.sql_utils.insert("cluster", record)
        return record['clusterId']

    def register_resource_class(self, record):
        record['classId'] = str(uuid.uuid4())
        self.sql_utils.insert("resourceClass", record)
        self._resource_class_map(True)  # make sure to invalidate resource map
        return record['classId']

    def register_resource_sub_class(self, record):
        validate(record.get("classId", None) in self._resource_class_map().keys(),
                 f"class id: {record['classId']} is not found")

        record['subClassId'] = str(uuid.uuid4())
        self.sql_utils.insert("resourceSubClass", record)
        self._resource_class_map(True)  # make sure to invalidate resource map
        return record['subClassId']

    def attach_resource_to_cluster(self, resource_id, cluster_id):
        validate(self.sql_utils.check_if_record_exists("resource", resource_id, "resourceId"),
                 f"resource id {resource_id} does not exits")

        validate(self.sql_utils.check_if_record_exists("cluster", cluster_id, "clusterId"),
                 f"cluster id {resource_id} does not exits")

        self.sql_utils.update("resource", {
            "clusterId": cluster_id
        }, {"resourceId": resource_id})

    def register_resource(self,
                          resource_class: string,
                          resource_sub_class: string,
                          resource_type: int,
                          data: dict):

        resource_id = str(uuid.uuid4())
        validate(resource_class in self._resource_class_map().keys(),
                 f"Resource class {resource_class} not found.")
        validate(resource_sub_class in self._resource_class_map()[
                 resource_class]['sub_classes'].keys(), f"Resource sub class {resource_sub_class} not found.")

        a = self.sql_utils.insert("resource", {
            "resourceId": resource_id,
            "resourceClassId": resource_class,
            "resourceSubClassId": resource_sub_class,
            "resourceType": resource_type,
            "registryTime": int(datetime.datetime.now().timestamp()),
            "status": 0,
            "data": json.dumps(data)
        })
        return resource_id

    def __del__(self):
        print("Closing API Connection")
        
    def get_infra_details (self, account_id):
        '''
            Returns infra details for given account in following format
        '''
        {
            "cluster_id": "001",
            "cluster_details" : {}, # Filtered DB Rec.
            "resources" :[{},{}] # Filtered DB Rec.
        }
        query = f'''
                select 
                    resource_account.accountid, 
                    n2.resourceid as resourceId,
                    n2.classname as className,
                    n2.data as resourceData,
                    n2.resourceType resourceType,
                    n2.subclassname,
                    n2.subclassdescription,
                    n2.subclassdata,
                    cluster.clusterid as clusterId,
                    cluster.data as clusterData,
                    cluster.status as clusterStatus,
                    cluster.clustertype as clusterType
                from resource_account
                inner join   
                    (select 
                        resource.* ,
                        resourceclass.classname as classname,
                        rsc.subclassname as subclassname,
                        rsc.subclassdescription as subclassdescription,
                        rsc.data as subclassdata
                        from resource
                        inner join resourceclass on resource.resourceclassid=resourceclass.classid
                        inner join resourcesubclass rsc on resource.resourcesubclassid = rsc.subclassid 
                    ) n2
                    on resource_account.resourceid = n2.resourceid
                inner join cluster on n2.clusterid = cluster.clusterid
                where resource_account.accountid = '{account_id}'        
                '''
        infra ={}

        for rec in self.sql_utils.run_select_query(query):
            cluster_id = rec[8]
            cluster_data = rec[9]
            cluster_status = rec [10]

            resource_id = rec[1]
            resource_type = rec[4]
            resource_data = rec [3]
            resource_class = rec [2]
            resource_sub_class = rec [5]
            if not infra.get(cluster_id, None):
                infra[cluster_id] ={
                        "cluster_id": cluster_id,
                        "cluster_data" : json.loads(cluster_data.tobytes()),
                        "cluster_status" : cluster_status,
                        "resources" :[] 
                    }
            infra [cluster_id]['resources'].append(
                {
                    "resource_id": resource_id,
                    "resource_type" : "shared" if resource_type == 0 else "dedicated",
                    "resource_data" : json.loads(resource_data.tobytes()),
                    "resource_class" : resource_class,
                    "resource_sub_class" : resource_sub_class
                }
            )
        return infra
