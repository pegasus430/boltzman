# PILLAR SERVICE
import datetime
from time import sleep
import traceback
from workers.aiservice import AIService
from core.ainetwork import AINetwork , AINetworkTrainingStatus
import config.config as config
from  utils import aiutils

from utils.loggerfactory import logger
from api.aiapi import AIApi
class ZombieHunter:
    def __init__(self, interval = None):
        '''
            Check zombie networks and services.
            Update their status, dispatch zombie networks to appropriate Kafka topic
            
        '''
        self.interval = interval if interval else config.ZOMBIE_HUNTER_INTERVAL
        self.api_client = AIApi()
        self.last_processed_time = 0

    def process(self):
        print ("running zombie collector")
        while (True):
            now = datetime.datetime.now().timestamp()
            if (now - self.last_processed_time) > self.interval:
                self.last_processed_time = now
                try:
                    self.api_client.fix_zombies()
                except Exception as e:
                    print(traceback.format_exc())                
            
            else:
                sleep(self.interval)
            
if __name__ == "__main__":
    hunter = ZombieHunter()
    hunter.process()

