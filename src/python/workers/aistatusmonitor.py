from api.service import AIServiceSdk
import config.config as config
import json
import pickle

from core.ainetwork import AINetwork
from utils.kafkautils import KafkaUtils
from utils.psqlutils import PsqlUtils
from api.aiapi import AIApi
from workers.aiservice import AIService


NOTIFICATIONS_TABLE = "notifications"
SERVICE_TABLE = "service"
sql_utils = PsqlUtils()

class AIStatusMonitor(AIService):
    def __init__(self):
        ''' Worker class to consume status messages.
            It channels status to the db.
        '''
        AIService.__init__(self, config.KAFKA_TOPICS["TOPIC_SERVICE_STATUS"], None, "AITrainer", 1 )
        self.kafka_utils = KafkaUtils()
        self.api_client = AIServiceSdk(AIApi())
        self.message_processor = AIStatusMonitor._message_processor

    def _update_db(self, data):    
        self.api_client.update_service_status(data)

    def _message_processor (self, msg):
        self._update_db(msg.value)
        print (msg)

    def service_main(self):
        self._push_status()        

if __name__ == "__main__":
    m = AIStatusMonitor()
    m.process()
