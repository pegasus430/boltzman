from os.path import exists
import json
import collections
import string
import os
from kafka import KafkaConsumer, KafkaProducer, KafkaAdminClient

import config.config as config
from utils.loggerfactory import logger

class KafkaUtils:
    def __init__ (self):
        self.consumers = {}
        if os.getenv("RUN_TIME_ENV") == 'docker': # no container, running from host
            self.kafka_prokers = config.KAFKA_BROKERS_DEV_DOCKER
        else:
            self.kafka_prokers = config.KAFKA_BROKERS_DEV
        self.producer = KafkaProducer(
            bootstrap_servers=self.kafka_prokers)
        self.admin_client = KafkaAdminClient(bootstrap_servers=self.kafka_prokers, client_id='test')

    def get_consumer(self, topic:string, consumer_group:string):
        '''
        returns a kafka consume object for given topic and group id.
        Consumers are cached by topic/group_id pair is requests.
        e.g: 
        {
            "topic1" : {
                "consumer_group1": consumer_obj1,
                "consumer_group2": consumer_obj2
                ...
            }
            "topic2" : { ... }
        }
        '''
        if not topic in self.consumers.keys():
            self.consumers [topic] = {}

        if not consumer_group in self.consumers[topic]:
            self.consumers [topic][consumer_group] = KafkaConsumer(topic,
                                            group_id=consumer_group,
                                            bootstrap_servers=self.kafka_prokers,
                                            enable_auto_commit=True,
                                            value_deserializer=lambda m: json.loads(m.decode('utf-8')))
        return self.consumers[topic][consumer_group]

    def get_producer(self):
        return self.producer

    def get_admin_client(self):
        return self.admin_client
