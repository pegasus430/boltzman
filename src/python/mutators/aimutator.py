from core.aibase import *
from config import config
import random

class AIMutator (AIBase):
    def __init__ (self):
        AIBase.__init__(self, name = "AIMutator", class_name = "AIMutator", record_id = -1)
        self.symbols =  []
        self.symbols_map = {}
        for rec in sql_utils.run_select_query("SELECT * FROM option"):
            self.symbols.append(rec)
            self.symbols_map[rec[2]] = rec        

    def mutate_integer (self, val, perc):
        delta = round(int(val) * perc)
        rv = random.randint(val - delta, val + delta)
        if rv == val:
            neg_pos = random.randint(1, 2)
            if neg_pos == 1:
                rv += 1
            else:
                rv -= 1
        return rv

    def mutate_float (self, val, perc):
        delta = val * perc
        return random.uniform(val - delta, val + delta)
    
    def random_number (self, min_val, max_val):
        if isinstance (min_val, int):
            return random.randint(min_val, max_val)
        if isinstance (min_val, float):
            return random.uniform(min_val, max_val)
    def mutate_number (self, val, perc):
        if isinstance (val, int):
            return self.mutate_integer(val, perc)
        if isinstance (val, float):
            return self.mutate_float(val, perc)


    def mutate_list (self, l, perc, min_items = 1):
        print ("List original: {}".format(l))
        min_val = min (l)
        max_val = max (l)
        new_list_size = self.mutate_integer(len(l), perc)
        if (new_list_size < min_items):
            new_list_size = min_items
        if new_list_size == len(l):
            new_list_size +=1
        delta =  new_list_size - len (l)
        rv = l.copy()
        if delta < 0:
            return l[:delta]
        else:          
            rv = l + [self.random_number(min_val, max_val) for i in range (0, delta)]
        print ("List New: {}".format(rv))

        return rv
    def mutate_list_content(self, l, perc, count = 1):
        rv = l.copy()
        for i in range (0, count):
            index = random.randint(0, len(l) -  1)
            rv[index] = self.mutate_number(l[index], perc)
        return rv

    def random_symbol (self, exclude_symbol = None):
#[(1, None, 'TSLA', '0', '', 'XNAS'), (2, None, 'GOOGL', '0', '', 'XNAS'), (3, None, 'FB', '0', '', 'XNAS'), (4, None, 'AAPL', '0', '', 'XNAS'), (5, None, 'MSFT', '0', '', 'XNAS')]        
        symbols_without = [s[2] for s in self.symbols]
        if (exclude_symbol):
            symbols_without.remove(exclude_symbol)
        return  symbols_without[random.randint(0, len(symbols_without) -  1)]
    
    def random_aggregation (self, min_aggregation_index = 0, max_aggregation_index = len(AIAggregationType) -  1):
        member_name = AIAggregationType._member_names_[random.randint(min_aggregation_index, max_aggregation_index)]
        return AIAggregationType._member_map_[member_name]


    def mutate(self, v, mutation_percentage):
        if isinstance (v, int):
            return self.mutate_integer(v, mutation_percentage)
        if isinstance (v, float):
            return self.mutate_float(v, mutation_percentage)
        if isinstance (v, list):
            return self.mutate_list(v, mutation_percentage)                        

