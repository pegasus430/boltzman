import sys
sys.path.append('..')
import config.config as config



from kafka import KafkaConsumer, KafkaProducer, KafkaAdminClient
consumer = KafkaConsumer(config.KAFKA_TOPICS["TOPIC_MODEL_NEEDS_TRAINING"],
                        group_id='my-group',
                        bootstrap_servers=config.KAFKA_BROKERS_DEV,
                        enable_auto_commit=True,
                        value_deserializer=lambda m: json.loads(m.decode('utf-8')))
producer = KafkaProducer(bootstrap_servers=config.KAFKA_BROKERS_DEV)

admin_client = KafkaAdminClient(bootstrap_servers=config.KAFKA_BROKERS_DEV, client_id='test')

def test_topics():
    topics = admin_client.list_topics()
    assert (len(topics) == len (config.KAFKA_TOPICS.keys()))
    for t in topics:
        assert (t in config.KAFKA_TOPICS.values())
