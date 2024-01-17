import datetime
from workers.aiservice import AIService
from core.ainetwork import AINetwork , AINetworkTrainingStatus
import config.config as config
from  utils import aiutils
from utils.loggerfactory import logger

class AITrainer(AIService):
    def __init__(self, to_time = None, capacity = 1, source_topic = None):
        ''' For each network in AIService.networks
            - Train it from its last trained time to to_time 
            - Then dispatches it to the output topics
            - if to_time is not specified , dynamic approach is used to train the network as close as possible to now
                and dispatch once it is close enough that would be considered as up to real time
        '''
        if not source_topic:
            source_topic = config.KAFKA_TOPICS["TOPIC_MODEL_NEEDS_TRAINING"]
        AIService.__init__(self, source_topic, [[config.KAFKA_TOPICS["TOPIC_MODEL_READY"]]], "AITrainer", capacity )
        self.to_time = to_time
        print ("AITrainer is initiated with service id: {}".format(self.uuid))

    def service_main(self):
        self._push_status()
        if len(self.networks)== 0:
            return
        counter = 0 
        network = self.networks[0]
        process_step = network.minimum_aggregation_type().value
        latest_time_to_train = self.to_time if self.to_time else min (network.latest_time_stamp(), config.time_generator.current_time)
        network.training_status = AINetworkTrainingStatus.InTraining 
        time_cursor = network.next_training_time()
        
        while time_cursor <= latest_time_to_train: # and counter < DEMO_TRAINING_CAP:
            #fast forward the off hours and holidays weekends etc
            market_code = self.symbols_map[network.output_dataport.params["symbol"]][4]
            time_cursor = aiutils.fast_forward_time(time_cursor, market_code)
            network.train(time_cursor)
            if counter % 10 == 0:
                #self._log_to_orchestrator('Network ({}) is trained up to {}.'.format(network.output_dataport.params["symbol"], datetime.datetime.fromtimestamp(time_cursor)))
                print('Network ({}) is trained up to {}.'.format(network.record_id, datetime.datetime.fromtimestamp(time_cursor)))
                network.location = self.uuid
                network.post()
                self.notification_handler.consume()
                return # return so that side affects of the whatever command was executed avoided with a fresh start of main


            self._push_status()        
            time_cursor += process_step
            counter +=1

        network.training_status = AINetworkTrainingStatus.TrainingUpToDate
        print ("Training process for network [{}] has finished".format(network.output_dataport.params["symbol"]))
        network.post()
        self.dispatch_network (network, self.distribution_topic_groups[0])

    
if __name__ == '__main__':
    task  = AITrainer()
    task.process()
