import json
import os
import config.config as config
import logging
from logging import DEBUG, INFO, ERROR
from time import sleep
from kafka import KafkaProducer

from utils.kafkautils import KafkaUtils

class AILogger(logging.RootLogger):
    ''' Overriding base logging class to add status pushes
    '''    
    def __init__(self, name: str=os.path.basename(__file__)) -> None:
        logging.RootLogger.__init__(self, name=name)
        self.producer = None
        self.kafka_utils = KafkaUtils("AILogger")


    def log_to_kafka(self, msg, topic):        
        if not self.producer:
            self.producer = self.kafka_utils.get_producer()

        msg = json.dumps(msg).encode('utf-8')
        self.producer.send(topic, msg)
        self.producer.flush()
        ##self.producer.close()
        
    def __exit__(self,ext_type,exc_value,traceback):
        self.procuer.close()

    def __del__(self):
        self.producer.flush()
        self.procuer.close()



