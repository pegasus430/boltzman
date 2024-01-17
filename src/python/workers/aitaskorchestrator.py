import config.config as config
import json
import random
import time
import enum
import importlib
from kafka import KafkaProducer
from kafka.errors import KafkaError
from multiprocessing import Process, Manager
from exceptions.exceptions import *
from utils.kafkautils import KafkaUtils
from workers.aiservice import AIServiceStatus, AIService
from workers.aitrainer import AITrainer
from core.ainetwork import AINetwork
from workers.aimutatortask import AIMutatorTask
from mutators.aimutator import AIMutator
from utils.loggerfactory import logger 
import sys
from utils.loggerfactory import logger

class CommInterface ():
    def __init__(self, shared_data):
        self.process = None
        self.shared_data = shared_data
    def get_data (self):
        return self.shared_data
    def set_task(self, task):
        self.task = task


class AIServiceStatus(enum.Enum):
    Initial = 0
    Active = 1
    Stopped = 2
    Error = 3

class AIServiceOrchestrator(object):
    def __init__(self, worker_module_name , worker_class_name, max_worker_count = config.MAX_WORKER_NUMBER):
        self.max_worker_count = max_worker_count
        self.comm_channels = []
        self.manager = Manager()
        self.kafka_utils = KafkaUtils("AIServiceOrchestrator")
        self.kafka_producer = self.kafka_utils.get_producer()
        self.kafka_consumer_shared_list = None
        self.worker_class_name = worker_class_name
        self.worker_module_name = worker_module_name
        

    def start_workers(self):
        for i in range(self.max_worker_count):
            module = importlib.import_module(self.worker_module_name)
            worker_class = getattr(module, self.worker_class_name)
            shared_data = self.manager.dict()
            shared_data ["status"] = AIServiceStatus.Initial
            shared_data ["status_string"] = "AIServiceStatus.Initial"
            comm_channel = CommInterface (shared_data)
            worker = worker_class(comm_channel)
            comm_channel.set_task(worker)
            
            p = Process(target=worker.process, args=[shared_data])
            comm_channel.process = p
            self.comm_channels.append(comm_channel)
            p.start()
            logger().info (f'process created. module: {self.worker_module_name} class: {self.worker_class_name}')


    def listen_workers (self):
        while True:
            time.sleep(1)
            for com in self.comm_channels:
                a = com.shared_data["status_string"]

    def __del__(self):
        for p in self.comm_channels:
            p.process.join()        




if __name__ == '__main__':
    if not len (sys.argv) == 2:
        print ("Please specify a task name")
        exit(1)
    f = open("../config/task_config.json")
    data = json.load(f)
    o  = AIServiceOrchestrator(data["tasks"][sys.argv[1]]["worker_module"], data["tasks"][sys.argv[1]]["worker_class"])
    o.start_workers()
    o.listen_workers()
