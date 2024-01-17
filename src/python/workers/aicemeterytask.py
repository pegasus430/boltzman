import time
from core.aibase import AIAggregationType
from aiservice import AIService, AIServiceStatus
from core.ainetwork import AINetwork, AINetworkTrainingStatus, AINetworkStatus
from exceptions.exceptions import TrainerBeginTimeError, TrainerDispatcherError
import config.config as config
import math
from mutators.aimutator import AIMutator
from statistics import mean
from core.aiprediction import AIPrediction


class AICemetery(AIService):
    def __init__(self,  capacity=1, number_of_iterations=None):
        ''' Worker class to handle dead networks. In initial implementation
                Dead networks are deleted from db and saved to a file
        '''
        AIService.__init__(self, config.KAFKA_TOPICS["TOPIC_MODEL_CEMETERY"], [], capacity, number_of_iterations)
        self.predictions = {}


    def get_stats(self):
        return {}

    def service_main(self):
        n: AINetwork
        for n in self.networks:
            n.delete_from_db()
            self.networks.remove(n)

