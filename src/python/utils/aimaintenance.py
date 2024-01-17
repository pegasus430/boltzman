import json
import os
from time import sleep
import config.config as config
import logging
from logging import DEBUG, INFO, ERROR

from utils.kafkautils import KafkaUtils
from exceptions.exceptions import MaintananceTestFailure

MINIMUM_TOPIC_COUNT = 5

class AIMaintenance(object):
    ''' Overriding base logging class to add status pushes
    '''
    def __init__(self, service_class, service_id):
        self.servide_class = service_class
        self.service_id = service_id
        self.kafka_utils = KafkaUtils()
        print ("in AILogger AIMaintenance")

    def _test_kafka_status(self):
        admin_client = self.kafka_utils.get_admin_client()
        topics = admin_client.list_topics()
        if (len(topics) < MINIMUM_TOPIC_COUNT): # number of topics may change in time, just testing that topics are created
            raise MaintananceTestFailure("Expected topics are not detected. Needed at least {}".format(MINIMUM_TOPIC_COUNT))


    def initial_test(self):
        self._test_kafka_status()





