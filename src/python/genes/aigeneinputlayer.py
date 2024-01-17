from genes.aigene import AIGene
from core.aidataport import AIDataport
class AIGeneInputLayer (AIGene):
    def __init__ (self, symbols = []):
        '''
            gene that adds a network defined dataports.
            symbols should be the array of following format
            symbol = {
                symbol: "GOOGL",
                aggregation : AIAggregationType.OneMinute,
                size = 32
            }
        '''
        AIGene.__init__(self, name = "AIGeneInputLayer", class_name = "AIGeneInputLayer", record_id = -1)
        self.params["symbols"] = symbols

    def set_symbols(self, symbols):
        self.params["symbols"] = symbols

    def add_symbol(self, symbol):
        self.params["symbols"].append(symbol)

    def process_network (self, network):
        for s in self.params["symbols"]:
            dp = AIDataport(s["symbol"], s["size"],s["aggregation"])
            dp.is_input_port = True
            network.add_child(dp)

    def mutate (self, perc):
        new_list_size = self.mutator.mutate_integer(len(self.params["symbols"]), perc)
        if (new_list_size < 1):
            new_list_size = 1
        delta =  new_list_size - len (self.params["symbols"])
        if delta < 0:
            self.params["symbols"] =  self.params["symbols"][:delta]
        else:
            for i in range (0, delta):
                new_symbol = {
                    "symbol" : self.mutator.random_symbol(),
                    "aggregation": self.mutator.random_aggregation(),
                    "size": self.mutator.random_number(4, 30)
                }
                self.params["symbols"].append(new_symbol)
