from core.aibase import AIBase
from mutators.aimutator import AIMutator

class AIGene (AIBase):
    def __init__ (self, name = "", class_name = "", record_id = -1, parent_id = -1):
        '''
            Base class for all genes
        '''
        super().__init__(name = name, class_name = class_name, record_id = record_id)
        self.mutator = AIMutator()


    def print_params(self):
        print ("Gene class: {}".format(self.class_name))
        for k in self.params.keys():
            print ("  {} : {}".format(k, self.params[k]))


    def __ge__(self, other):
        return self.params == other.params
