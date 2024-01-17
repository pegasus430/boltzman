from datetime import datetime
from workers.aiservice import AIService
from core.ainetwork import AINetwork, AINetworkStatus
from exceptions.exceptions import PredictionAlreadyExists
import config.config as config
import json

from statistics import mean
from utils import aiutils
from utils.loggerfactory import logger


class AITradeTask(AIService):
    def __init__(self, capacity=1, number_of_iterations=None):
        ''' For each network in AIService.networks
            - create a predicton based on output dataport 
            - check if network is short term trainable, if so train it if not push it back to need to train topic
            - compare predictions with real data and update networks predictons score
            - if network score is less than minimum score kill network by passing to the cemetery topic
        '''
        AIService.__init__(self, config.KAFKA_TOPICS["TOPIC_MODEL_READY"], 
                            [[config.KAFKA_TOPICS["TOPIC_MODEL_NEEDS_PARTIAL_TRAINING"]],
                            [config.KAFKA_TOPICS["TOPIC_MODEL_CEMETERY"]]],
                            "AITradeTask", 
                            capacity, 
                            number_of_iterations)
        self.time_cursor = 0
        print("AITradeTask is initiated with service id: {}".format(self.uuid))

    def _dispatch_predictions(self, predictions: list):
        '''
            Sends given prediction list to kafka topic predictions
        '''
        for p in predictions:
            msg = json.dumps(p.get_details())
            self.producer.send(config.KAFKA_TOPICS["TOPIC_PREDICTIONS"], msg.encode('utf-8'))
            self.producer.flush()

    def process_predictions(self, process_time):
        '''
            Process predictions that can be matured and send predictions of each network as a chunk to kafka
        '''
        logger().info(
            f'Processing predictions for {datetime.fromtimestamp(process_time)}')

        for n in self.networks:
            self._dispatch_predictions(n.process_predictions(process_time))

    def get_stats(self):
        return {
            "predictions": self.predictions
        }

    def service_main(self):
        '''
        1- Check if the network needs training
            - if short term training needed train here
            - else dispatch to partial training topic and remove from networks
        2- Check the time if it is in working hours 
            - if off hours pass
        3- check time stamp of last prediction created 
            - if (curerent time - last_prediction) > minimum input dataport aggregation value
                - create a new prediction
            -else 
                - pass
        '''
        self._push_status()
        if config.time_generator.is_simulation():  # slow down simulation while waiting for new networks
            if len(self.networks) == 0:
                config.time_generator.delay = 5
            else:
                config.time_generator.delay = 0

        current_time = config.time_generator.get_current_time()

        # make sure not to process the same timestamp
        if (self.time_cursor < current_time):
            self.time_cursor = current_time
        else:
            logger().info(
                f'TradeTask processing canceled. Timestamp already processed  [{datetime.fromtimestamp(current_time)}]')
            return

        process_time = self.time_cursor
        networks_need_training = []
        networks_to_be_killed = []
        logger().info(f'TradeTask Network Processing =>\n'
                    f'Network count  : {len(self.networks)}\n'
                    f'Processing time: {datetime.fromtimestamp(process_time)}')
        n: AINetwork
        for n in self.networks:
            time_stamp_bucket = n.timestamp_bucket(
                process_time)
            logger().info(f'\tNetwork: {n.record_id} prediction loop'
                        f'    Bucket time : {datetime.fromtimestamp(time_stamp_bucket)}')

            # if timestamp is in the off hours for the network market skip
            market_code = self.symbols_map[n.output_dataport.params["symbol"]][4]
            if not aiutils.is_asset_active(time_stamp_bucket, market_code):
                logger().info(f'\tSkipping... Off hours.')
                continue

            # make sure to that network is up to date before creating any predictions
            if not n.short_term_trainable(process_time):
                networks_need_training.append(n)
                logger().info(
                    f'\tNetwork needs long training and will be dispatched')
            # Check if how network does , kill it if score is below threshold
            elif n.score < config.NETWORK_STATUS_THRESHOLDS[AINetworkStatus.Dead.name][1]:
                logger().info(f'\tNetwork is dead and will be sent to cemetery.')
                networks_to_be_killed.append(n)
            else:
                # make sure to short train the network
                if (n.next_training_time() <= process_time):
                    logger().info('\tNetwork needs short training. Training...')
                    ts1 = n.last_trained_time if not n.last_trained_time == 0 else n.earliest_time_stamp()
                    n.batch_train(
                        ts1 + n.minimum_aggregation_type().value, process_time)
                try:
                    p = n.new_prediction_request(process_time)
                    logger().info(f'\tTradeTask Prediction created:')
                    logger().info("\t" + str(p))
                except PredictionAlreadyExists as e:
                    logger().info('\tPrediction already exists.Skipping')

        self.process_predictions(process_time)

        for n in networks_need_training:
            self.dispatch_network(
                self, n, config.KAFKA_TOPICS["TOPIC_MODEL_NEEDS_PARTIAL_TRAINING"])
        for n in networks_to_be_killed:
            logger().info(f'Network {(n.record_id)} died.')
            self.dispatch_network(
                n, [config.KAFKA_TOPICS["TOPIC_MODEL_CEMETERY"]])

# structure of predictions collection:
# {
#   record_id_1 : {
#        time_stamp1 : AIPrediction
#        time_stamp2 : AIPrediction
#        time_stamp3 : AIPrediction
#   },
#   record_id_2 : {
#        time_stamp1 : AIPrediction
#        time_stamp2 : AIPrediction
#        time_stamp3 : AIPrediction
#   },
#   record_id_3 : {
#        time_stamp1 : AIPrediction
#        time_stamp2 : AIPrediction
#        time_stamp3 : AIPrediction
#   }
#
# }
if __name__ == '__main__':
    task  = AITradeTask()
    task.process()
