from marshal import dumps
from sqlite3 import Timestamp
import string
from time import sleep
from genes.aigeneinputlayer import AIGeneInputLayer
from genes.aigenelayers import AIGeneLayers
from genes.aigeneoutput import AIGeneOutput
from utils.aiutils import validate
import json
from core.aibase import *
from core.ainetwork import AINetwork, AINetworkStatus
from exceptions.exceptions import *
from mutators.aimutator import AIMutator

from functools import wraps
import uuid
import datetime

from utils.kafkautils import KafkaUtils



class AINetworkSdk(object):
    def __init__(self, api) -> None:
        self.sql_utils = api.sql_utils
        self.api = api
        self.consumer = None
        self.producer = None


    def _dispatch_network(self, network: AINetwork, topic):
        """dispatches given network to given topics. 

        Args:
            network_id (int): network id
            topic (string]): topic to dispatch network
        """
        if not self.producer:
            self.kafka_utils = KafkaUtils()
            self.producer = self.kafka_utils.get_producer()
        msg = json.dumps({"rec_id": network.record_id}).encode('utf-8')
        self.producer.send(topic, msg)
        self.producer.flush()
        network.location = topic
        network.post()

    def _dispatch_network_with_id(self, network_id, topic):
        """dispatches given network to given topics. 

        Args:
            network_id (int): network id
            topic (string]): topic to dispatch network
        """
        network = AINetwork()
        print(f"Network Id: {network_id}")
        network.load(network_id)
        if not self.producer:
            self.kafka_utils = KafkaUtils()
            self.producer = self.kafka_utils.get_producer()
        msg = json.dumps({"rec_id": network.record_id}).encode('utf-8')
        self.producer.send(topic, msg)
        self.producer.flush()
        network.location = topic
        network.post()

    def getNetworks(self, locations=None):
        '''
            Returns list of networks for given locations.
            If locations are not sent , All networks are returned for the account
        '''
        query = "SELECT * FROM network"
        if (locations):
            in_clause = ",".join([f"'{x}'" for x in locations])
            query = query + f" WHERE location in ({in_clause})"

        networks_to_return = []

        for rec in (self.sql_utils.run_select_query(query)):
            networks_to_return.append({
                "id": rec[0],
                "location": rec[3],
                "score": rec[5],
                "last_trained_time": rec[6],
                "model_file": rec[7]
            })
        return networks_to_return

    def seedNetwork(self, target_topic=None):
        """Generates a baby network by using parameters defined above
        """
        n = AINetwork("FB")

        mutator = AIMutator()
        input_gene_params = []
        for i in range(config.INITIAL_NETWORK_MIN_DP_COUNT, config.INITIAL_NETWORK_MAX_DP_COUNT):
            input_gene_params.append({
                "symbol": mutator.random_symbol(),
                "aggregation": mutator.random_aggregation(6, 7),
                "size": mutator.random_number(config.INITIAL_NETWORK_MIN_DP_SIZE, config.INITIAL_NETWORK_MAX_DP_SIZE)
            })
        input_gene = AIGeneInputLayer(input_gene_params)
        layer_gene_params = []
        prev_layer_size = 0
        for i in range(0, mutator.random_number(config.INITIAL_NETWORK_MIN_LAYER_COUNT, config.INITIAL_NETWORK_MAX_LAYER_COUNT)):
            layer_size = mutator.random_number(
                config.INITIAL_NETWORK_MIN_LAYER_SIZE, config.INITIAL_NETWORK_MAX_LAYER_SIZE,)
            if (layer_size > prev_layer_size) and prev_layer_size > 0:
                layer_size = prev_layer_size
            layer_gene_params.append(layer_size)
            prev_layer_size = layer_size

        layer_gene = AIGeneLayers(layer_gene_params)
        output_gene = AIGeneOutput(
            mutator.random_number(2, 6), mutator.random_symbol())
        n.add_children(input_gene, layer_gene, output_gene)
        n.build_from_genes()
        n.status = AINetworkStatus.Active
        if target_topic:
            n.post()
            n._dispatch_network(n, target_topic)
        else:
            n.location = "IDLE"
            n.post()

        return n

    def deleteNetworks(self, networks_to_delete: list):
        '''
            Deletes given idle networks from database. 
            Networks that are not idle (either in a kafka topic or service) can not be deleted by executing this method.           
        '''
        validate(len(networks_to_delete) > 0, "No network id is specified.")
        query = "DELETE FROM network"
        in_clause = ",".join([f"'{x}'" for x in networks_to_delete])
        query = query + f" WHERE id in ({in_clause}) AND location ='IDLE'"
        self.sql_utils.run_no_result_query(query)

    def removeNetworks(self, source_service_id, network_ids, topic_to_dispatch=None):
        '''
            ## Description:
            deattach given networks from their services and pushed to the kafka topic specified.

            ## Params:
            ```
            {
                source_service_id: origin of the message being sent to service(s)
                topic <string>: kafka topic to send networks after being dettached. if None Networks are parked at IDLE
                networkIds []: array of network ids
            }
            ```

            ## Returns:
            ackknowledgement message:
            {
                ackToken: uuid
            }
        '''
        query = '''
            SELECT * FROM network INNER join service 
            on network.location = service.serviceid 
        '''
        in_clause = ",".join([f"'{x}'" for x in network_ids])
        query = query + f" WHERE network.id in ({in_clause})"
        network_map = {}

        for rec in self.sql_utils.run_select_query(query):
            network_map[rec[0]] = rec

        validate(set(network_map.keys()) == set(network_ids),
                 f"Network Ids are not all in services, requested: {network_ids}, in db: {list(network_map.keys())}")

        # generate service notifications for each network
        for id in network_map.keys():
            target_service_id = network_map[id][3]
            print(target_service_id)
            self.sendNotification(source_service_id, target_service_id, AIServiceNotificationType.Dispatch_Network,
                                   {"topic": topic_to_dispatch, "network_id": id})

    def _cloneNetwork(self, network_to_clone, target_location=None):
        new_network = network_to_clone.clone()
        new_network.post()
        if target_location:
            self._dispatch_network(new_network, target_location)

    def cloneNetworks(self, network_ids, target_location=None):
        for network_id in network_ids:
            n = AINetwork()
            n.load(network_id)
            self._cloneNetwork(n, target_location)

    def mutateNetworks(self, networks_to_mutate, target_location=None):
        '''
            ## Description:
            clone given networks. If a topic is specified, cloned networks are sent to the given topic

            ## Params:
            ```
            {
                topic <string>: kafka topic to send networks
                networkIds[]: array of networkIds to be cloned
            }
            ```

            ## Returns:
            ackknowledgement message:
            {
                networkIds[]: array of cloned networkIds in the same order as input.
            }
        '''
        pass

    def getNetworkDetails(self, network_id):
        '''
            ## Description:
            returns network details for given network_id, throws exception if not found
        '''
        print("NETWORK ID", network_id)
        validate(isinstance(network_id, int),
                 f"Given network id is not valid. Expected an integer number")
        n = AINetwork()

        # check if network exists
        validate(self.sql_utils.check_if_record_exists("network", network_id),
                 f"Given network id does not exist. {network_id}")
        n.load(network_id)
        return n.get_details()


