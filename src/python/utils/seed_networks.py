from core.ainetwork import *
from genes.aigeneinputlayer import AIGeneInputLayer
from genes.aigenelayers import AIGeneLayers
from genes.aigeneoutput import AIGeneOutput
from core.ainetwork import AINetwork
from mutators.aimutator import AIMutator
from kafka import KafkaProducer
from core.aibase import *
from config import config
import sys

import json
from utils.kafkautils import KafkaUtils
from utils.psqlutils import PsqlUtils 
sql_utils = PsqlUtils()



min_dataport_count, max_dataport_count = 1, 5
min_dp_size, max_dp_size = 20, 40
min_layer_size, max_layer_size = 16, 32
min_layer_count, max_layer_count = 2, 6
mutator = AIMutator()
kafka_utils = KafkaUtils()

def seed_network():
    """Generates a baby network by using parameters defined above
    """
    n = AINetwork("FB")

    input_gene_params =[]
    for i in range (min_dataport_count, max_dataport_count):
        input_gene_params.append({
            "symbol": mutator.random_symbol(),
            "aggregation": mutator.random_aggregation(6, 7),
            "size" : mutator.random_number(min_dp_size, max_dp_size)
        })
    input_gene = AIGeneInputLayer(input_gene_params)
    layer_gene_params = []
    prev_layer_size = 0  
    for i in range (0, mutator.random_number(min_layer_count, max_layer_count)):
        layer_size = mutator.random_number(min_layer_size, max_layer_size)
        if (layer_size > prev_layer_size) and prev_layer_size > 0:
            layer_size = prev_layer_size
        layer_gene_params.append(layer_size)
        prev_layer_size = layer_size
        
    layer_gene = AIGeneLayers(layer_gene_params)
    output_gene = AIGeneOutput(mutator.random_number(2, 6), mutator.random_symbol())
    n.add_children(input_gene, layer_gene, output_gene)
    n.build_from_genes()
    n.status = AINetworkStatus.Active
    n.post()
    print (f'SCORE :{n.score}')
    return n


def reset_db ():
    """deletes networks and related monitoring data from database
       Time series are not touched.
    """    
    sql_utils.run_no_result_query("DELETE FROM network")
    sql_utils.run_no_result_query("DELETE FROM servicenotifications")
    sql_utils.run_no_result_query("DELETE FROM predictions")

def push_network_to_kafka (rec_id):
    kafka_producer = kafka_utils.get_producer()
    print ("generating network {} from db"
                .format (rec_id))
    msg = json.dumps({"rec_id" : rec_id}).encode('utf-8')
    kafka_producer.send(config.KAFKA_TOPICS["TOPIC_MODEL_NEEDS_TRAINING"], msg).get()     
    kafka_producer.flush()          

if __name__ == "__main__":
    if len (sys.argv) < 2:
        print ("command requires at least one.")
        exit(1)
    command = str(sys.argv [1]).upper()
    arg = None
    if len (sys.argv) == 3:
        arg = str(sys.argv [2]).upper()
    if command == "PUSH":
        print (command)
        push_network_to_kafka (int(arg))

    if command == "SEED":
        n = seed_network()
        n.location = config.KAFKA_TOPICS["TOPIC_MODEL_NEEDS_TRAINING"]
        n.post()
        print (n)
        push_network_to_kafka (n.record_id)
    elif command == "RESET":
        if input("are you sure to delete all networks? (y/n)") == "y":        
            reset_db()
