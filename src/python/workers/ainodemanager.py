from time import sleep
import config.config as config
import json
import pickle

from core.ainetwork import AINetwork
from utils.kafkautils import KafkaUtils
from utils.psqlutils import PsqlUtils
from api.aiapi import AIApi
from workers.aiservice import AIService
from workers.notification_handlers.nodemanagernh import NodeManagerNotificationHandler


NOTIFICATIONS_TABLE = "notifications"
SERVICE_TABLE = "service"
sql_utils = PsqlUtils()

class AINodeManager(AIService):
    def __init__(self, node_id):
        ''' Worker class to consume node notifications.
        '''
        AIService.__init__(self, None, None, "node_id", 1 )
        self.api_client = AIApi()
        self.node_id = node_id
        AIService.__init__(self, None, kafka_consumer_group='node_id',Notifications_Handler_Class=NodeManagerNotificationHandler)

    def service_main(self):
        print (f"AINodeManager {self.node_id} is active")
        self._push_status()

if __name__ == "__main__":
    m = AINodeManager('NodeManager')
    m.process()
