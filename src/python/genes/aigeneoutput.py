from core.aibase import AIAggregationType
from genes.aigene import AIGene
from exceptions.exceptions import *
import config.config as config
from mutators.aimutator import AIMutator

class AIGeneOutput (AIGene):
    def __init__ (self, size = 0, symbol = "", aggregation = AIAggregationType.OneHour):
        '''
            gene that adds the output layer to the network for given symbol and and layer size
        '''
        super().__init__(name = "AIGeneOutput", class_name = "AIGeneOutput", record_id = -1)
        self.params["output_size"] = size
        self.params["symbol"] = symbol
        self.params["aggregation"] = aggregation

    def process_network (self, network):
        network.set_output_symbol(self.params["symbol"], self.params["aggregation"], self.params["output_size"])
        
    def mutate(self, perc):
        action = self.mutator.random_number(0, 2)
        print ("action :{}".format(action))
        if action == 0:
            self.params["symbol"] = self.mutator.random_symbol(self.params["symbol"])
        elif action ==1:
            self.params["output_size"] = self.mutator.mutate_integer(self.params["output_size"], perc)
        elif action ==2: 
            self.params["aggregation"] = self.mutator.random_aggregation()

    