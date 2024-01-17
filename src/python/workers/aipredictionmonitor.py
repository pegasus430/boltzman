import config.config as config
import json
import pickle

from core.ainetwork import AINetwork
from utils.kafkautils import KafkaUtils
from utils.psqlutils import PsqlUtils



sql_utils = PsqlUtils()

class AIPredictionMonitor(object):
    def __init__(self):
        ''' Worker class to consume predictions messages.
            It channels predictions to the db.
        '''
        self.subscribed_topic = config.KAFKA_TOPICS["TOPIC_PREDICTIONS"]
        self.kafka_utils = KafkaUtils("AIPredictionMonitor")
    
    def _check_if_record_exists(self, u_id):
        query = "SELECT id FROM serviceNotifications WHERE uniqueId = '{}'".format(u_id)
        result_set = list(sql_utils.run_select_query(query))
        if (len(result_set)) == 0:
            return False
        
        return True


    def _update_db(self, data):
        '''
            Persist matured (used) predictions to db
        '''
        sql_utils.begin()
        raw_dict = data
        record = {
            "source_network_id" : raw_dict['network_id'],
            "output_symbol" : raw_dict['symbol'],
            "prediction_time" : raw_dict['prediction_time'],
            "next_prediction_time" : raw_dict['next_prediction_time'],
            "matured_time"  : raw_dict['matured_time'],
            "score" : raw_dict['network_score'],
            "prediction_points" : raw_dict['prediction'],
            "real_values" : raw_dict['real_values'],
            "serviceId" : "N/A" ,
            "className" : "AIPredictionMonitor"
        };
        sql_utils.insert("predictions", record)
        sql_utils.commit()


    def run(self):
        from kafka import KafkaConsumer
        consumer = self.kafka_utils.get_consumer(config.KAFKA_TOPICS["TOPIC_PREDICTIONS"])
        print ("Prediction Monitoring Started.")
        for msg in consumer:
            self._update_db(msg.value)
            print (msg)

if __name__ == "__main__":
    m = AIPredictionMonitor()
    m.run()
