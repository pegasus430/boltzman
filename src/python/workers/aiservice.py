import datetime
import enum
import uuid
from xmlrpc.client import DateTime
from api.aiapi import AIServiceNotificationType
import config.config as config
import json
import os
from core.ainetwork import AINetwork
from exceptions.exceptions import *
from utils.aimaintenance import AIMaintenance
from utils.aiutils import make_sure

from utils.loggerfactory import logger
from utils.psqlutils import PsqlUtils
from workers.servicekiller import ServiceKiller
from workers.notification_handlers.aiservicenotificationhandler import AIServiceNotificationHandler

class AIServiceStatus(enum.Enum):
    Stopped = 0
    Running = 1
    Completed = 2
    Errored = 3

sql_utils = PsqlUtils()


class AIService(object):
    def __init__(self,
                 kafka_input_topic,
                 kafka_output_topics=None,
                 kafka_consumer_group="AIService",
                 capacity=1,
                 number_of_iterations=None,
                 Notifications_Handler_Class = AIServiceNotificationHandler):
        """Base class for all services. Common features for all task types are
            -  a collection of networks being processed
            - input topics to poll new networks to be processed
            - output topics where networks are sent after task is done with them
            - capacity: maximum number of networks being processed
            - number_of_iterations: Used in tests, 
                limits the service life time by number of itrations, then service exits, rather than running forever
            - Notifications_Handler_Class: class that handles incoming notifications.Default is AIServiceNotificationHandler.
                notification handlers should subclass AIServiceNotificationHandler and implement consume method for desired behaviour

        Args:
            kafka_input_topic (string): source topic for fresh networks
            kafka_output_topics ([[string]] ): topics to distribute networks after processed. This is a 2D array giving flexibility to task classes to channel 
                                               networks to different output topics on conditions. If not given, service doesnt produce kafka messages
            capacity (int, optional): Max number of networks being processed at any given time. Defaults to 1.
            number_of_iterations(int, optional): Max number of iterations, if not set task runs forever, usually test code shoud limit iterations to prematurly end the task
            consumer_group(string) = Kafka consumer group, usually set by derived task classes to their class name e.g : AITrainer
        """        ''''''
        if not os.getenv("SERVICE_ID"):
            raise MissingServiceIdEnvVariable(
                "SERVICE_ID is not set")

        self.uuid = os.getenv("SERVICE_ID")
        self.networks = []
        self.status = AIServiceStatus.Stopped
        self.capacity = capacity
        self.subscribed_topic = kafka_input_topic
        self.distribution_topic_groups = kafka_output_topics
        self.number_of_iterations = number_of_iterations
        self.consumer = None
        self.producer = None
        # Number of networks processed and dispatched to the next topix
        self.processed_networks = 0
        # Last time a summary update is pushed to kafka status topic
        self.last_summary_update_push_time = None
        # Last time a detailed update is pushed to kafka status topic
        self.last_detailed_update_push_time = None
        # create a maintanence object
        self.maintenance = AIMaintenance("AIService", self.uuid)
        self.maintenance.initial_test()  # fatal situations are caught here in constructor
        self.symbols = []
        self.symbols_map = {}
        for rec in sql_utils.run_select_query("SELECT * FROM option"):
            self.symbols.append(rec)
            self.symbols_map[rec[2]] = rec
        self.init_time = datetime.datetime.now()
        #self.service_killer = ServiceKiller()
        self.kafka_consumer_group = kafka_consumer_group
        self.notification_handler = Notifications_Handler_Class(self)
        self.message_processor = AIService._default_message_processor

    def _push_status(self, status_string="ONLINE"):
        '''
            Sends detailed network status to kafka
        '''
        if not self.last_detailed_update_push_time:
            self.last_detailed_update_push_time = datetime.datetime.now()
            return  # not yet
        elif (datetime.datetime.now() - self.last_detailed_update_push_time).total_seconds() > config.NETWORK_STATUS_UPDATE_INTERVAL:
            status = {
                "class_name": self.__class__.__name__,
                "service_id": str(self.uuid),
                "up_since": int(self.init_time.timestamp()),
                "status": status_string,
                "number_of_networks": len(self.networks),
                "trained_networks": self.processed_networks,
                "networks": []
            }

            self.last_detailed_update_push_time = datetime.datetime.now()
            for n in self.networks:
                status["networks"].append(n.network_details())

            self.producer.send(config.KAFKA_TOPICS["TOPIC_SERVICE_STATUS"], json.dumps(
                status).encode('utf-8'))

            #logger().log_to_kafka (status , config.KAFKA_TOPICS["TOPIC_SERVICE_STATUS"])
#        else:
#            print ((datetime.datetime.now() - self.last_detailed_update_push_time).total_seconds())

    def dispatch_network_by_id (self, network_id, topics):
        '''
            dispatches network with given id to topics
        '''
        for n in self.networks:
            if n.record_id == network_id:
                self.dispatch_network(n, topics)
                return
        raise NetworkIsNotFound(f"Nework is not found for id: {network_id}")
    
    def dispatch_network(self, network, topics:list):
        """dispatches given network to given topics. 
            Network is also deleted from networks list

        Args:
            network (AINetwork): network to be dispatched
            topics ([string]]): list of topics to dispatch network, If not given networks are parked at IDLE
        """
        msg = json.dumps({"rec_id": network.record_id}).encode('utf-8')
        self.networks.remove(network)
        if topics and len(topics) > 0:
            for topic in topics:
                self.producer.send(topic, msg)
                self.producer.flush()

            network.location = topics[0]

        else:
            network.location = "IDLE"
        network.post()

    def _default_message_processor(self, msg):
        '''
            default function called to process kafka polled networks.
            by services that process networks.
            For other type of services msg content is usually not a serialized network but other structs
            e.g AIStatusMonitor. They need to provide their own message_processor
        
        '''
        self.consumer.commit()
        n = AINetwork("")
        print ("_default_message_processor")
        print (msg)
        n.load(msg.value["rec_id"])
        n.location = self.uuid
        print(f'Network picked : {msg.value["rec_id"]}')
        self.networks.append(n)
        n.post()  # updates location in the db

    def poll_messages(self):
        """polls kafka messages from  subscribed topic
            Services do not poll more than their capacities
        """
        msg_to_pull = self.capacity - len(self.networks)
        if msg_to_pull == 0:
            return

        recs = self.consumer.poll(max_records=1)
        if recs == {}:
            return

        for tp, messages in recs.items():
            for msg in messages:
                print(msg)
                self.message_processor(self, msg)

    def get_stats(self):
        return {}

    def process(self):
        """Main process function 
           Once initial kafka setup is done (not sure why it is setup here) It does dollowing in an infinite loop:
           - run service_main()
           - poll new networks
           service_main method is not implemented in here and It should be implemented by subclasses.
           It is also sub classes' responsibility to dispatch networks that are no longer processed
           Make sure to implement this function
        """
        try:
            from utils.kafkautils import KafkaUtils
            self.kafka_utils = KafkaUtils()
            if not self.consumer and self.subscribed_topic:
                self.consumer = self.kafka_utils.get_consumer(
                    self.subscribed_topic, self.kafka_consumer_group)
            if not self.producer:
                self.producer = self.kafka_utils.get_producer()

            iteration_count = 0
            self.status = AIServiceStatus.Running
            while not self.status == AIServiceStatus.Stopped and (not self.number_of_iterations or
                                                                  iteration_count < self.number_of_iterations):  # and not self.service_killer.kill_now: #TODO this approach doent work for trainers due to long wait to training complete
                self.notification_handler.consume_base()
                self.service_main()

                if (self.number_of_iterations):
                    iteration_count += 1
                if (self.subscribed_topic and len(self.subscribed_topic) > 0):
                    self.poll_messages()

            # if self.service_killer.kill_now:
            #    raise Exception("Service got kill signal")

        finally:
            print("STOPPING SERVICE GRACEFULLY")
            self.status = AIServiceStatus.Stopped
            # self.service_cleanup()

    def service_cleanup(self):
        for n in self.networks:
            self.dispatch_network(
                n, [config.KAFKA_TOPICS["TOPIC_MODEL_NEEDS_TRAINING"]])
