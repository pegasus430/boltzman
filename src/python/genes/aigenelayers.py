from genes.aigene import AIGene
from exceptions.exceptions import *
from mutators.aimutator import AIMutator
import config.config as config



class AIGeneLayers (AIGene):
    def __init__ (self, layer_schema = []):
        '''
            gene that adds a network its hidden layers.
            provide a list of integer with layer sizes in it
            e.g : [32, 32]
            exclude output layer , it is handled by another gene
        '''
        super().__init__(name = "AIGeneLayers", class_name = "AIGeneLayers", record_id = -1, parent_id = -1)
        self.params["layer_schema"] = layer_schema

    def process_network (self, network):
        for l in self.params["layer_schema"]:
            network.add_hidden_layer(l)
        

    def mutate(self, perc):
        self.params["layer_schema"] = self.mutator.mutate_list(self.params["layer_schema"], perc, min_items = 2)
