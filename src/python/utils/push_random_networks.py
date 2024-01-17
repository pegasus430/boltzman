
import config.config as config
import json
import random

from utils.kafkautils import KafkaUtils





def gen_test_network (rec_count = 1):
    kafka_utils = KafkaUtils("gen_test_network")

    kafka_producer = kafka_utils.get_producer()
    counter = 0
    while counter < rec_count:
        sleep_time = random.randint(1,12 )
        rec_id = random.randint(1350, 1400)
        print ("generating network {} from db"
                    .format (rec_id))
        msg = json.dumps({"rec_id" : rec_id}).encode('utf-8')
        kafka_producer.send(config.KAFKA_TOPICS["TOPIC_MODEL_NEEDS_TRAINING"], msg).get()     
        counter += 1
    kafka_producer.flush()          

if __name__ == '__main__':
    gen_test_network(300)