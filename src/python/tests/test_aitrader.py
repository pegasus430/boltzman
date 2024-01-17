from cgi import test
from config import config
import workers.aitradetask as aitradetask
from core.aibase import AIAggregationType
from genes.aigeneinputlayer import AIGeneInputLayer
from genes.aigenelayers import AIGeneLayers
from genes.aigeneoutput import AIGeneOutput
from mutators.aimutator import AIMutator
from core.ainetwork import AINetwork
from unittest.mock import patch
mutator = AIMutator()
import time
from tests.test_utils import generate_dummy_network


test_data =[[AIAggregationType.Daily, AIAggregationType.ThirtySeconds],
[AIAggregationType.FiveSeconds, AIAggregationType.ThirtySeconds],
[AIAggregationType.ThirtySeconds, AIAggregationType.FifteenSeconds],
[AIAggregationType.OneHour, AIAggregationType.OneMinute],
]

class FakeMessage(object):
    pass


class FakeKafka:
    def __init__ (self, in_networks):
        self.in_networks = in_networks
        self.topics = {}
        for k in config.KAFKA_TOPICS:
            self.topics[k] = []
        self.offset = 0
    def poll (self, max_records = None):
        cnt = 0;
        recs ={"topic_1" : []}
        while (cnt < max_records and self.offset < len(self.in_networks)):
            n = self.in_networks[self.offset]
            msg = FakeMessage()
            msg.value = {"rec_id" : n.record_id}
            recs["topic_1"].append(msg)
            self.offset +=1
        if (len(recs["topic_1"]) == 0):
            recs = {}
        return recs

    def send(self, topic , msg):
        if not self.topics.get(topic, None):
            self.topics[topic] = []
        #print (topic, msg)
        self.topics[topic].append(msg)

    def flush(self):
        pass


def generate_input_networks (test_data):
    mutator = AIMutator()
    rv =[]
    for aggregations in test_data:
        symbols = []
        for aggregation in aggregations:
            input_gene_symbol = {
                        "symbol":mutator.random_symbol(),
                        "aggregation": aggregation,
                        "size" : mutator.random_number(2, 32)}
            symbols.append(input_gene_symbol)
            print (input_gene_symbol)
        
        rv.append(generate_dummy_network(symbols))
    
    return rv            
initial_ts = 1619197227
def time_generator():
    global initial_ts
    initial_ts +=100
    return initial_ts

def negative_score(a, b):
    print ("returning fake score")
    return -10

def positive_score(a, b):
    print ("returning fake score")
    return 10


def test_trader_task ():
    begin_time = time.time_ns()
    number_iteration = 22
    number_of_networks = len(test_data)
    with patch("workers.aitradetask.config.current_time", wraps=time_generator) as mock_obj:    
        with patch("workers.aitradetask.AIPrediction.calculate_score", wraps=negative_score) as mock_obj2:    
            td = aitradetask.AITradeTask (capacity=2, number_of_iterations = number_iteration)
            mocked_kafka = FakeKafka(generate_input_networks(test_data)) 
            td.consumer = mocked_kafka
            td.producer = mocked_kafka
            stats = td.process(None)
            for n in td.networks:
                print (n.score, n.status)
            # all should be dead
            print (config.KAFKA_TOPICS)
            assert (len(mocked_kafka.topics[config.KAFKA_TOPICS["TOPIC_MODEL_CEMETERY"]]) == len(test_data))
            assert (len (td.networks) == 0)
        
        with patch("workers.aitradetask.AIPrediction.calculate_score", wraps=positive_score) as mock_obj2:    
            td = aitradetask.AITradeTask (capacity=2, number_of_iterations = number_iteration)
            mocked_kafka = FakeKafka(generate_input_networks(test_data)) 
            td.consumer = mocked_kafka
            td.producer = mocked_kafka
            stats = td.process(None)
            for n in td.networks:
                print (n.score, n.status)
            # all alive
            print (config.KAFKA_TOPICS)
            assert (not mocked_kafka.topics.get(config.KAFKA_TOPICS["TOPIC_MODEL_CEMETERY"],None))
            assert (len (td.networks) == len(test_data))


    delta = time.time_ns() - begin_time
    print ("Number of networks :{}". format(number_of_networks))
    print ("Duration: {} secs".format ((delta) / 1000000 / 1000))
    print ("Duration / cycle: {} secs".format ((delta) / 1000000 / 1000 / 100))
    print(mocked_kafka.topics)

test_trader_task()