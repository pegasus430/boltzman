import sys
sys.path.append('..')
import config.config as config
import time
from kafka.admin import KafkaAdminClient, NewTopic

WAIT_TIME = 10

retry = 0
while retry < 3:

    retry += 1
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers="localhost:9092", 
            client_id='test'
        )
        topic_list = []
        for t in config.KAFKA_TOPICS:
            topic_list.append(NewTopic(name=t, num_partitions=4, replication_factor=1))
        admin_client.create_topics(new_topics=topic_list, validate_only=False)
        quit(0)
    
    except Exception as inst:
        print ("{}".format(inst))
        print ("topic creation failed. retrying in {}...".format(WAIT_TIME))
        time.sleep(WAIT_TIME)
        pass
quit(-1)